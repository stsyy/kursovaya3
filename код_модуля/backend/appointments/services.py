"""Бизнес-логика процесса А5 «Управлять записями пациентов»."""
from datetime import datetime

from django.conf import settings
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from schedule.models import Slot, UnavailabilityPeriod
from .models import Appointment, Patient, SmsNotification
from .sms import get_gateway


class AppointmentError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def find_patient(phone):
    return Patient.objects.filter(phone=normalize_phone(phone)).first()


def normalize_phone(phone):
    digits = ''.join(ch for ch in phone if ch.isdigit())
    if len(digits) == 11 and digits[0] in '78':
        digits = '7' + digits[1:]
    elif len(digits) == 10:
        digits = '7' + digits
    return '+' + digits


def _slot_in_future(slot):
    start = timezone.make_aware(datetime.combine(slot.shift.date, slot.start_time))
    return start > timezone.now()


def _take_free_slot(slot_id):
    slot = Slot.objects.select_for_update().select_related('shift__doctor_specialization').get(pk=slot_id)
    if slot.status != Slot.Status.FREE:
        raise AppointmentError('Слот уже занят. Выберите другой слот.')
    if not _slot_in_future(slot):
        raise AppointmentError('Нельзя записать пациента на прошедшее время.')
    slot.status = Slot.Status.BUSY
    slot.save(update_fields=['status'])
    return slot


@transaction.atomic
def book(patient, slot_id):
    """Запись пациента по обращению. Запись сразу получает статус «активна»."""
    slot = _take_free_slot(slot_id)
    return Appointment.objects.create(patient=patient, slot=slot, status=Appointment.Status.ACTIVE)


def affected_appointments():
    """Действующие записи на заблокированных слотах – их нужно перенести."""
    return (Appointment.objects.filter(status__in=Appointment.ACTUAL, slot__status=Slot.Status.BLOCKED)
            .select_related('patient', 'slot__shift__doctor_specialization__doctor__account',
                            'slot__shift__doctor_specialization__specialization', 'slot__shift__room'))


def propose_slots(appointment, limit=10):
    """Свободные будущие слоты смен с той же специализацией, что и специализация исходной смены,
    ближайшие к исходному времени."""
    original = appointment.slot
    spec = original.shift.doctor_specialization.specialization_id
    today = timezone.localdate()
    candidates = (Slot.objects.filter(status=Slot.Status.FREE,
                                      shift__doctor_specialization__specialization_id=spec,
                                      shift__date__gte=today)
                  .select_related('shift__doctor_specialization__doctor__account', 'shift__room'))
    # исключаем слоты, на которые приходится период недоступности врача (целый день или часы внутри дня)
    unavailable = (UnavailabilityPeriod.objects
                   .filter(doctor=OuterRef('shift__doctor_specialization__doctor'),
                           date_from__lte=OuterRef('shift__date'), date_to__gte=OuterRef('shift__date'))
                   .filter(Q(time_from__isnull=True)
                           | Q(time_from__lt=OuterRef('end_time'), time_to__gt=OuterRef('start_time'))))
    candidates = candidates.exclude(Exists(unavailable))
    target = datetime.combine(original.shift.date, original.start_time)
    result = [s for s in candidates if _slot_in_future(s)]
    result.sort(key=lambda s: abs((datetime.combine(s.shift.date, s.start_time) - target).total_seconds()))
    return result[:limit]


def notify(appointment, text):
    # в каждое SMS добавляется телефон регистратуры: отменить или перенести запись пациент может только через неё
    text = f'{text} Регистратура: {settings.REGISTRY_PHONE}.'
    ok = get_gateway().send(appointment.patient.phone, text)
    return SmsNotification.objects.create(appointment=appointment, phone=appointment.patient.phone, text=text,
                                          status=SmsNotification.Status.SENT if ok else SmsNotification.Status.FAILED)


def _when(slot):
    return f'{slot.shift.date:%d.%m.%Y} в {slot.start_time:%H:%M}'


def _release_slot(slot):
    """Освобождает слот; заблокированный слот (недоступность врача, блокировка) остаётся заблокированным."""
    if slot.status == Slot.Status.BUSY:
        slot.status = Slot.Status.FREE
        slot.save(update_fields=['status'])


@transaction.atomic
def reschedule(appointment_id, new_slot_id):
    """Перенос записи: та же запись переводится на новый слот, история переносов
    не хранится. Строки записи, исходного и нового слотов блокируются до конца транзакции.
    Пациенту отправляется SMS-уведомление."""
    try:
        new_slot_id = int(new_slot_id)
    except (TypeError, ValueError):
        raise AppointmentError('Укажите слот для переноса.') from None
    app = Appointment.objects.select_for_update().select_related('patient').get(pk=appointment_id)
    if app.status not in Appointment.ACTUAL:
        raise AppointmentError('Запись отменена, перенести её нельзя.')
    if app.slot_id == new_slot_id:
        raise AppointmentError('Запись уже находится в этом слоте.')
    # оба слота блокируются в порядке возрастания ключа, чтобы параллельные переносы не взаимоблокировались
    slots = {s.pk: s for s in Slot.objects.select_for_update(of=('self',)).filter(pk__in=[app.slot_id, new_slot_id])
             .select_related('shift__doctor_specialization__doctor__account', 'shift__room').order_by('pk')}
    old_slot, new_slot = slots[app.slot_id], slots.get(new_slot_id)
    if new_slot is None:
        raise AppointmentError('Слот не найден.')
    if new_slot.status != Slot.Status.FREE:
        raise AppointmentError('Слот уже занят. Выберите другой слот.')
    if not _slot_in_future(new_slot):
        raise AppointmentError('Нельзя перенести запись на прошедшее время.')
    if new_slot.shift.doctor_specialization.specialization_id != old_slot.shift.doctor_specialization.specialization_id:
        raise AppointmentError('Запись можно перенести только к врачу той же специализации.')
    _release_slot(old_slot)
    new_slot.status = Slot.Status.BUSY
    new_slot.save(update_fields=['status'])
    app.slot = new_slot
    app.save(update_fields=['slot'])
    notify(app, f'Ваша запись к врачу перенесена на {_when(new_slot)}, врач {new_slot.shift.doctor}, '
                f'кабинет {new_slot.shift.room.number}.')
    return app


@transaction.atomic
def cancel(appointment_id):
    """Отмена записи с SMS-уведомлением пациента."""
    app = Appointment.objects.select_for_update().select_related('patient', 'slot__shift').get(pk=appointment_id)
    if app.status not in Appointment.ACTUAL:
        raise AppointmentError('Запись уже отменена.')
    app.status = Appointment.Status.CANCELLED
    app.save(update_fields=['status'])
    _release_slot(app.slot)
    notify(app, f'Ваша запись на {_when(app.slot)} отменена. Записаться снова можно через форму онлайн-записи на сайте диспансера или в регистратуре.')
    return app
