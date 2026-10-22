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
    full_name = models.CharField('ФИО', max_length=150)
    specialization = models.ForeignKey(Specialization, on_delete=models.PROTECT, related_name='doctors',
                                       verbose_name='Специализация')
    account = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='doctor', verbose_name='Учётная запись')

    class Meta:
        verbose_name = 'врач'
        verbose_name_plural = 'врачи'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

    def is_available(self, day=None):
        """Статус доступности вычисляется по периодам недоступности (не хранится)."""
        day = day or timezone.localdate()
        return not self.unavailability_periods.filter(date_from__lte=day, date_to__gte=day).exists()

    @property
    def availability_status(self):
        return 'доступен' if self.is_available() else 'недоступен'


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
