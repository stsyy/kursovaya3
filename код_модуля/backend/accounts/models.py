from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Учётная запись сотрудника. Логин хранится в поле username, пароль – в виде хеша."""

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Администратор'
        DOCTOR = 'doctor', 'Врач'

    class State(models.TextChoices):
        ACTIVE = 'active', 'активна'
        BLOCKED = 'blocked', 'заблокирована'

    full_name = models.CharField('ФИО', max_length=150)
    role = models.CharField('Роль', max_length=10, choices=Role.choices)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    state = models.CharField('Состояние', max_length=10, choices=State.choices, default=State.ACTIVE)
    failed_attempts = models.PositiveSmallIntegerField('Число неудачных попыток входа', default=0)
    locked_until = models.DateTimeField('Заблокирована до', null=True, blank=True)

    class Meta:
        verbose_name = 'учётная запись сотрудника'
        verbose_name_plural = 'учётные записи сотрудников'
        ordering = ['full_name']

    def __str__(self):
        return f'{self.full_name} ({self.username})'

    @property
    def is_administrator(self):
        return self.role == self.Role.ADMIN
