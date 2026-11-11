from django.conf import settings
from django.db import models
from django.utils import timezone


class Specialization(models.Model):
    name = models.CharField('Название', max_length=100, unique=True)

    class Meta:
        verbose_name = 'специализация'
        verbose_name_plural = 'специализации'
        ordering = ['name']

    def __str__(self):
        return self.name


class Doctor(models.Model):
    """Врач. Персональные данные (ФИО, телефон) хранятся в учётной записи сотрудника,
    врач может иметь несколько специализаций (через таблицу DoctorSpecialization)."""

    account = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor',
                                   verbose_name='Учётная запись')
    specializations = models.ManyToManyField(Specialization, through='DoctorSpecialization', related_name='doctors',
                                             verbose_name='Специализации')

    class Meta:
        verbose_name = 'врач'
        verbose_name_plural = 'врачи'
        ordering = ['account__full_name']

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        """ФИО берётся из учётной записи врача и в таблице врачей не дублируется."""
        return self.account.full_name

    @property
    def shifts(self):
        """Смены врача по всем его специализациям."""
        from schedule.models import Shift
        return Shift.objects.filter(doctor_specialization__doctor=self)

    def is_available(self, day=None):
        """Статус доступности вычисляется по периодам недоступности (не хранится).
        Врач недоступен в день, на который приходится период недоступности на целый день."""
        day = day or timezone.localdate()
        return not self.unavailability_periods.filter(date_from__lte=day, date_to__gte=day,
                                                      time_from__isnull=True).exists()

    @property
    def availability_status(self):
        day = timezone.localdate()
        if not self.is_available(day):
            return 'недоступен'
        if self.unavailability_periods.filter(date_from__lte=day, date_to__gte=day).exists():
            return 'недоступен в часть дня'
        return 'доступен'


class DoctorSpecialization(models.Model):
    """Специализация врача (связь «многие ко многим» между врачами и специализациями).
    На запись этой таблицы ссылаются рабочие смены: смена задаёт, по какой специализации ведёт приём врач."""

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='doctor_specializations',
                               verbose_name='Врач')
    specialization = models.ForeignKey(Specialization, on_delete=models.PROTECT, related_name='doctor_specializations',
                                       verbose_name='Специализация')

    class Meta:
        verbose_name = 'специализация врача'
        verbose_name_plural = 'специализации врачей'
        ordering = ['doctor__account__full_name', 'specialization__name']
        constraints = [models.UniqueConstraint(fields=['doctor', 'specialization'],
                                               name='uniq_doctor_specialization')]

    def __str__(self):
        return f'{self.doctor} – {self.specialization}'


class Room(models.Model):
    number = models.CharField('Номер', max_length=10)
    floor = models.PositiveSmallIntegerField('Этаж')
    building = models.CharField('Корпус', max_length=50)

    class Meta:
        verbose_name = 'кабинет'
        verbose_name_plural = 'кабинеты'
        ordering = ['building', 'number']
        constraints = [models.UniqueConstraint(fields=['building', 'number'], name='uniq_room_in_building')]

    def __str__(self):
        return f'каб. {self.number} ({self.building})'
