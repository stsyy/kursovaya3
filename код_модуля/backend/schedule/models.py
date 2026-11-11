from django.db import models

from directory.models import Doctor, DoctorSpecialization, Room


class Shift(models.Model):
    """Рабочая смена врача в кабинете в определённый день. Смена ссылается на специализацию врача:
    в смене врач ведёт приём по одной из своих специализаций."""

    doctor_specialization = models.ForeignKey(DoctorSpecialization, on_delete=models.PROTECT, related_name='shifts',
                                              verbose_name='Специализация врача')
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

    @property
    def doctor(self):
        return self.doctor_specialization.doctor

    @property
    def specialization(self):
        return self.doctor_specialization.specialization


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
    """Период недоступности врача (болезнь, отпуск и т. п.).

    Если время начала и окончания не заданы, врач недоступен целые дни с date_from по date_to.
    Если заданы, врач недоступен в каждый из этих дней только с time_from до time_to."""

    class Reason(models.TextChoices):
        ILLNESS = 'illness', 'болезнь'
        VACATION = 'vacation', 'отпуск'
        OTHER = 'other', 'иное'

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='unavailability_periods',
                               verbose_name='Врач')
    reason = models.CharField('Причина', max_length=10, choices=Reason.choices)
    date_from = models.DateField('Дата начала')
    date_to = models.DateField('Дата окончания')
    time_from = models.TimeField('Время начала', null=True, blank=True)
    time_to = models.TimeField('Время окончания', null=True, blank=True)

    class Meta:
        verbose_name = 'период недоступности'
        verbose_name_plural = 'периоды недоступности'
        ordering = ['-date_from']
        constraints = [
            models.CheckConstraint(condition=models.Q(date_from__lte=models.F('date_to')), name='period_from_before_to'),
            # время либо не задано совсем (целые дни), либо задано полностью и начало раньше окончания
            models.CheckConstraint(
                condition=(models.Q(time_from__isnull=True, time_to__isnull=True)
                           | models.Q(time_from__isnull=False, time_to__isnull=False,
                                      time_from__lt=models.F('time_to'))),
                name='period_time_both_or_none'),
        ]

    def __str__(self):
        text = f'{self.doctor}: {self.get_reason_display()} {self.date_from:%d.%m.%Y}–{self.date_to:%d.%m.%Y}'
        if self.is_whole_day:
            return text
        return f'{text}, {self.time_from:%H:%M}–{self.time_to:%H:%M}'

    @property
    def is_whole_day(self):
        return self.time_from is None
