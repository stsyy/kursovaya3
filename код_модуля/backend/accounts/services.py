"""Аутентификация и управление учётными записями (процесс А1)."""
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone

from .models import User


class AuthError(Exception):
    def __init__(self, message, code='invalid'):
        super().__init__(message)
        self.message = message
        self.code = code


def login(username, password):
    """Проверяет логин и пароль с учётом блокировки после неудачных попыток.

    Возвращает пользователя при успехе, иначе выбрасывает AuthError.
    """
    user = User.objects.filter(username=username).first()
    now = timezone.now()
    if user is not None:
        if user.state == User.State.BLOCKED:
            raise AuthError('Учётная запись заблокирована администратором.', 'blocked')
        if user.locked_until and user.locked_until > now:
            minutes = int((user.locked_until - now).total_seconds() // 60) + 1
            raise AuthError(f'Вход временно заблокирован. Повторите попытку через {minutes} мин.', 'locked')

    checked = authenticate(username=username, password=password)
    if checked is None:
        if user is not None:
            user.failed_attempts += 1
            if user.failed_attempts >= settings.LOGIN_MAX_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=settings.LOGIN_LOCK_MINUTES)
                user.failed_attempts = 0
            user.save(update_fields=['failed_attempts', 'locked_until'])
        raise AuthError('Неверный логин или пароль.')

    checked.failed_attempts = 0
    checked.locked_until = None
    checked.last_login = now
    checked.save(update_fields=['failed_attempts', 'locked_until', 'last_login'])
    return checked


def generate_temp_password():
    """Временный пароль из 10 символов (не короче 8 по требованию 1.1)."""
    alphabet = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789'
    return ''.join(secrets.choice(alphabet) for _ in range(10))


def account_has_active_appointments(user):
    """Учётную запись врача нельзя удалить, пока у врача есть активные записи пациентов."""
    from appointments.models import Appointment

    doctor = getattr(user, 'doctor', None)
    if doctor is None:
        return False
    return Appointment.objects.filter(
        slot__shift__doctor=doctor,
        status__in=[Appointment.Status.ACTIVE, Appointment.Status.PENDING],
        slot__shift__date__gte=timezone.localdate(),
    ).exists()
