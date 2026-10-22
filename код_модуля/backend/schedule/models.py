from django.db import models

from directory.models import Doctor, Room


class Shift(models.Model):
    """Рабочая смена врача в кабинете в определённый день."""

    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name='shifts', verbose_name='Врач')
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='shifts', verbose_name='Кабинет')
    date = models.DateField('Дата')
    start_time = models.TimeField('Время начала')
    end_time = models.TimeField('Время окончания')
    slot_minutes = models.PositiveSmallIntegerField('Длительность слота, мин')

    class Meta:
        verbose_name = 'рабочая смена'
        verbose_name_plural = 'рабочие смены'
        ordering = ['date', 'start_time']
        constraints = [
            models.CheckConstraint(condition=models.Q(start_time__lt=models.F('end_time')), name='shift_start_before_end'),
        ]

    def __str__(self):
        return f'{self.doctor} {self.date:%d.%m.%Y} {self.start_time:%H:%M}–{self.end_time:%H:%M}'


class Slot(models.Model):
    """Временной слот приёма внутри смены."""

    class Status(models.TextChoices):
        FREE = 'free', 'свободен'
        BUSY = 'busy', 'занят'
        BLOCKED = 'blocked', 'заблокирован'

    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='slots', verbose_name='Смена')
    start_time = models.TimeField('Время начала')
    end_time = models.TimeField('Время окончания')
    status = models.CharField('Статус', max_length=10, choices=Status.choices, default=Status.FREE)

    class Meta:
        verbose_name = 'временной слот'
        verbose_name_plural = 'временные слоты'
        ordering = ['shift__date', 'start_time']
        constraints = [models.UniqueConstraint(fields=['shift', 'start_time'], name='uniq_slot_in_shift')]

    def __str__(self):
        return f'{self.shift.date:%d.%m.%Y} {self.start_time:%H:%M} ({self.get_status_display()})'

    @property
    def date(self):
        return self.shift.date

    @property
    def doctor(self):
        return self.shift.doctor


class UnavailabilityPeriod(models.Model):
    """Период недоступности врача (болезнь, отпуск и т. п.)."""

    class Reason(models.TextChoices):
        ILLNESS = 'illness', 'болезнь'
        VACATION = 'vacation', 'отпуск'
        OTHER = 'other', 'иное'

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='unavailability_periods',
                               verbose_name='Врач')
    reason = models.CharField('Причина', max_length=10, choices=Reason.choices)
    date_from = models.DateField('Дата начала')
    date_to = models.DateField('Дата окончания')

    class Meta:
        verbose_name = 'период недоступности'
        verbose_name_plural = 'периоды недоступности'
        ordering = ['-date_from']
        constraints = [
            models.CheckConstraint(condition=models.Q(date_from__lte=models.F('date_to')), name='period_from_before_to'),
        ]

    def __str__(self):
        return f'{self.doctor}: {self.get_reason_display()} {self.date_from:%d.%m.%Y}–{self.date_to:%d.%m.%Y}'
