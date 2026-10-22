"""Бизнес-логика процесса А6 «Управлять записями пациентов»."""
from datetime import datetime

from django.conf import settings
from django.db import transaction
from django.db.models import Exists, OuterRef
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
    slot = Slot.objects.select_for_update().select_related('shift__doctor').get(pk=slot_id)
    if slot.status != Slot.Status.FREE:
        raise AppointmentError('Слот уже занят. Выберите другой слот.')
    if not _slot_in_future(slot):
        raise AppointmentError('Нельзя записать пациента на прошедшее время.')
    slot.status = Slot.Status.BUSY
    slot.save(update_fields=['status'])
    return slot


@transaction.atomic
def book(patient, slot_id):
    """Запись пациента по обращению (процесс 6.1). Запись сразу получает статус «активна»."""
    slot = _take_free_slot(slot_id)
    return Appointment.objects.create(patient=patient, slot=slot, status=Appointment.Status.ACTIVE)


def affected_appointments():
    """Действующие записи на заблокированных слотах – их нужно перенести (процесс 5.3)."""
    return (Appointment.objects.filter(status__in=Appointment.ACTUAL, slot__status=Slot.Status.BLOCKED)
            .select_related('patient', 'slot__shift__doctor__specialization', 'slot__shift__room'))


def propose_slots(appointment, limit=10):
    """Свободные будущие слоты врачей той же специализации (процесс 6.2), ближайшие к исходному времени."""
    original = appointment.slot
    spec = original.shift.doctor.specialization_id
    today = timezone.localdate()
    candidates = (Slot.objects.filter(status=Slot.Status.FREE, shift__doctor__specialization_id=spec,
                                      shift__date__gte=today)
                  .select_related('shift__doctor', 'shift__room'))
    # исключаем врачей, недоступных в день слота
    unavailable = UnavailabilityPeriod.objects.filter(doctor=OuterRef('shift__doctor'),
                                                      date_from__lte=OuterRef('shift__date'),
                                                      date_to__gte=OuterRef('shift__date'))
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
    if slot.status == Slot.Status.BUSY:
        slot.status = Slot.Status.FREE
        slot.save(update_fields=['status'])


@transaction.atomic
def reschedule(appointment_id, new_slot_id):
    """Перенос записи (процесс 6.3): новая запись «активна», исходная – «перенесена»,
    пациенту отправляется SMS-уведомление (процесс 6.5)."""
    old = Appointment.objects.select_for_update().select_related('patient', 'slot__shift').get(pk=appointment_id)
    if old.status not in Appointment.ACTUAL:
        raise AppointmentError('Запись уже перенесена или отменена.')
    new_slot = _take_free_slot(new_slot_id)
    old.status = Appointment.Status.MOVED
    old.save(update_fields=['status'])
    _release_slot(old.slot)
    new = Appointment.objects.create(patient=old.patient, slot=new_slot, status=Appointment.Status.ACTIVE,
                                     channel=old.channel, source=old)
    doctor = new_slot.shift.doctor
    notify(new, f'Ваша запись к врачу перенесена на {_when(new_slot)}, врач {doctor}, '
                f'кабинет {new_slot.shift.room.number}.')
    return new


@transaction.atomic
def cancel(appointment_id):
    """Отмена записи (процесс 6.4) с SMS-уведомлением пациента."""
    app = Appointment.objects.select_for_update().select_related('patient', 'slot__shift').get(pk=appointment_id)
    if app.status not in Appointment.ACTUAL:
        raise AppointmentError('Запись уже перенесена или отменена.')
    app.status = Appointment.Status.CANCELLED
    app.save(update_fields=['status'])
    _release_slot(app.slot)
    notify(app, f'Ваша запись на {_when(app.slot)} отменена. Записаться снова можно через форму онлайн-записи на сайте диспансера или в регистратуре.')
    return app
