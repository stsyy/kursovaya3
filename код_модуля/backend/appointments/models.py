from django.db import models

from schedule.models import Slot


class Patient(models.Model):
    full_name = models.CharField('ФИО', max_length=150)
    phone = models.CharField('Номер телефона', max_length=20, unique=True)
    sport = models.CharField('Вид спорта', max_length=100, blank=True)

    class Meta:
        verbose_name = 'пациент'
        verbose_name_plural = 'пациенты'
        ordering = ['full_name']

    def __str__(self):
        return f'{self.full_name} ({self.phone})'


class Appointment(models.Model):
    """Запись пациента на временной слот."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'ожидает кода из SMS'
        ACTIVE = 'active', 'активна'
        MOVED = 'moved', 'перенесена'
        CANCELLED = 'cancelled', 'отменена'

    class Channel(models.TextChoices):
        REGISTRY = 'registry', 'регистратура'
        ONLINE = 'online', 'форма онлайн-записи'

    # статусы, при которых запись занимает слот
    ACTUAL = [Status.PENDING, Status.ACTIVE]

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='appointments', verbose_name='Пациент')
    slot = models.ForeignKey(Slot, on_delete=models.PROTECT, related_name='appointments', verbose_name='Слот')
    status = models.CharField('Статус', max_length=10, choices=Status.choices, default=Status.ACTIVE)
    channel = models.CharField('Способ записи', max_length=10, choices=Channel.choices, default=Channel.REGISTRY)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    source = models.OneToOneField('self', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='rescheduled_to', verbose_name='Исходная запись')

    class Meta:
        verbose_name = 'запись пациента'
        verbose_name_plural = 'записи пациентов'
        ordering = ['slot__shift__date', 'slot__start_time']
        constraints = [
            # на один слот может приходиться только одна действующая запись
            models.UniqueConstraint(fields=['slot'], condition=models.Q(status__in=['pending', 'active']),
                                    name='one_actual_appointment_per_slot'),
        ]

    def __str__(self):
        return f'{self.patient} → {self.slot}'


class SmsNotification(models.Model):
    class Status(models.TextChoices):
        SENT = 'sent', 'отправлено'
        FAILED = 'failed', 'ошибка отправки'

    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='notifications',
                                    verbose_name='Запись')
    phone = models.CharField('Номер телефона', max_length=20)
    text = models.TextField('Текст')
    sent_at = models.DateTimeField('Время отправки', auto_now_add=True)
    status = models.CharField('Статус отправки', max_length=10, choices=Status.choices)

    class Meta:
        verbose_name = 'SMS-уведомление'
        verbose_name_plural = 'SMS-уведомления'
        ordering = ['-sent_at']
