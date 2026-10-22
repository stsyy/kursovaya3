"""Бизнес-логика расписания: процессы А3 «Формировать сетку расписания»,
А4 «Корректировать расписание» и А5 «Управлять статусом доступности врача»."""
from datetime import datetime, timedelta

from django.db import transaction

from .models import Shift, Slot, UnavailabilityPeriod


class ScheduleError(Exception):
    def __init__(self, messages):
        self.messages = messages if isinstance(messages, list) else [messages]
        super().__init__('; '.join(self.messages))


def _overlap(qs, start, end):
    return qs.filter(start_time__lt=end, end_time__gt=start)


def check_conflicts(doctor, room, date, start, end, exclude=None):
    """Проверка конфликтов смен (вариант использования «Проверить конфликты расписания»)."""
    errors = []
    if start >= end:
        errors.append('Время начала смены должно быть раньше времени окончания.')
        return errors
    same_day = Shift.objects.filter(date=date)
    if exclude is not None:
        same_day = same_day.exclude(pk=exclude.pk)
    for s in _overlap(same_day.filter(doctor=doctor), start, end):
        errors.append(f'Врач уже работает {s.date:%d.%m.%Y} с {s.start_time:%H:%M} до {s.end_time:%H:%M} '
                      f'в кабинете {s.room.number}.')
    for s in _overlap(same_day.filter(room=room), start, end):
        errors.append(f'Кабинет {room.number} занят врачом {s.doctor} с {s.start_time:%H:%M} до {s.end_time:%H:%M}.')
    if UnavailabilityPeriod.objects.filter(doctor=doctor, date_from__lte=date, date_to__gte=date).exists():
        errors.append('На эту дату у врача установлен период недоступности.')
    return errors


def slot_bounds(date, start, end, minutes):
    """Разбиение интервала смены на слоты заданной длительности; неполный хвост отбрасывается."""
    cur = datetime.combine(date, start)
    stop = datetime.combine(date, end)
    step = timedelta(minutes=minutes)
    while cur + step <= stop:
        yield cur.time(), (cur + step).time()
        cur += step


@transaction.atomic
def create_shift(doctor, room, date, start_time, end_time, slot_minutes):
    """Создаёт смену и формирует её слоты со статусом «свободен»."""
    if slot_minutes <= 0:
        raise ScheduleError('Длительность слота должна быть больше нуля.')
    errors = check_conflicts(doctor, room, date, start_time, end_time)
    if errors:
        raise ScheduleError(errors)
    shift = Shift.objects.create(doctor=doctor, room=room, date=date, start_time=start_time,
                                 end_time=end_time, slot_minutes=slot_minutes)
    Slot.objects.bulk_create(Slot(shift=shift, start_time=a, end_time=b)
                             for a, b in slot_bounds(date, start_time, end_time, slot_minutes))
    return shift


def _active_on(slots):
    from appointments.models import Appointment
    return Appointment.objects.filter(slot__in=slots, status__in=Appointment.ACTUAL).select_related(
        'patient', 'slot__shift__doctor')


@transaction.atomic
def update_shift(shift, room, start_time, end_time):
    """Изменяет кабинет и время смены. Свободные слоты формируются заново, занятые слоты,
    не попавшие в новый интервал, блокируются. Возвращает записи, которые нужно перенести."""
    errors = check_conflicts(shift.doctor, room, shift.date, start_time, end_time, exclude=shift)
    if errors:
        raise ScheduleError(errors)
    shift.room, shift.start_time, shift.end_time = room, start_time, end_time
    shift.save()
    shift.slots.filter(status=Slot.Status.FREE).delete()
    kept = list(shift.slots.all())
    outside = [s for s in kept if s.start_time < start_time or s.end_time > end_time]
    Slot.objects.filter(pk__in=[s.pk for s in outside]).update(status=Slot.Status.BLOCKED)
    taken = {s.start_time for s in kept}
    Slot.objects.bulk_create(Slot(shift=shift, start_time=a, end_time=b)
                             for a, b in slot_bounds(shift.date, start_time, end_time, shift.slot_minutes)
                             if a not in taken)
    return list(_active_on(outside))


@transaction.atomic
def delete_shift(shift):
    """Удаляет смену без записей. Если записи есть, слоты смены блокируются, а записи
    возвращаются для переноса; смену можно удалить после переноса."""
    affected = list(_active_on(shift.slots.all()))
    if affected:
        shift.slots.update(status=Slot.Status.BLOCKED)
        return affected
    shift.delete()
    return []


@transaction.atomic
def block_slot(slot):
    slot.status = Slot.Status.BLOCKED
    slot.save(update_fields=['status'])
    return list(_active_on([slot]))


def doctor_slots(doctor, date_from, date_to):
    return Slot.objects.filter(shift__doctor=doctor, shift__date__gte=date_from, shift__date__lte=date_to)


@transaction.atomic
def set_unavailability(doctor, reason, date_from, date_to):
    """Устанавливает период недоступности, блокирует слоты врача внутри периода и
    возвращает (период, список затронутых записей)."""
    errors = []
    if date_from > date_to:
        errors.append('Дата начала периода не может быть позже даты окончания.')
    elif UnavailabilityPeriod.objects.filter(doctor=doctor, date_from__lte=date_to, date_to__gte=date_from).exists():
        errors.append('Период пересекается с уже установленным периодом недоступности врача.')
    if errors:
        raise ScheduleError(errors)
    period = UnavailabilityPeriod.objects.create(doctor=doctor, reason=reason, date_from=date_from, date_to=date_to)
    slots = doctor_slots(doctor, date_from, date_to)
    affected = list(_active_on(slots))
    slots.update(status=Slot.Status.BLOCKED)
    return period, affected


def _release(slots):
    """Разблокирует слоты: занятые записью становятся «занят», остальные – «свободен»."""
    from appointments.models import Appointment
    busy_ids = set(Appointment.objects.filter(slot__in=slots, status__in=Appointment.ACTUAL)
                   .values_list('slot_id', flat=True))
    for slot in slots.filter(status=Slot.Status.BLOCKED):
        slot.status = Slot.Status.BUSY if slot.pk in busy_ids else Slot.Status.FREE
        slot.save(update_fields=['status'])


@transaction.atomic
def change_unavailability_end(period, new_date_to):
    """Досрочный выход врача: дата окончания переносится, слоты после неё разблокируются."""
    if new_date_to < period.date_from:
        raise ScheduleError('Дата окончания не может быть раньше даты начала периода.')
    old_to = period.date_to
    period.date_to = new_date_to
    period.save(update_fields=['date_to'])
    if new_date_to < old_to:
        _release(doctor_slots(period.doctor, new_date_to + timedelta(days=1), old_to))
        return []
    slots = doctor_slots(period.doctor, old_to + timedelta(days=1), new_date_to)
    affected = list(_active_on(slots))
    slots.update(status=Slot.Status.BLOCKED)
    return affected


@transaction.atomic
def remove_unavailability(period):
    _release(doctor_slots(period.doctor, period.date_from, period.date_to))
    period.delete()
