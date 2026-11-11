"""Вспомогательные функции для создания тестовых данных."""
from datetime import time, timedelta

from django.utils import timezone

from accounts.models import User
from appointments.models import Patient
from directory.models import Doctor, DoctorSpecialization, Room, Specialization
from schedule import services


def future_day(days=2):
    return timezone.localdate() + timedelta(days=days)


def make_admin(login='admin', password='admin12345'):
    user = User(username=login, full_name='Иванова Мария Сергеевна', role=User.Role.ADMIN)
    user.set_password(password)
    user.save()
    return user


def make_doctor(name='Петров Алексей Иванович', spec='Спортивный врач'):
    """Создаёт учётную запись врача (в ней хранится ФИО), врача и его специализации.
    spec – название специализации или список названий."""
    account = User.objects.create(username=f'doctor{User.objects.count() + 1}', full_name=name,
                                  role=User.Role.DOCTOR)
    doctor = Doctor.objects.create(account=account)
    for spec_name in [spec] if isinstance(spec, str) else spec:
        specialization, _ = Specialization.objects.get_or_create(name=spec_name)
        DoctorSpecialization.objects.create(doctor=doctor, specialization=specialization)
    return doctor


def make_room(number='101'):
    return Room.objects.create(number=number, floor=1, building='Главный')


def doctor_specialization(doctor, spec=None):
    """Специализация врача: указанная по названию или первая из специализаций врача."""
    pairs = doctor.doctor_specializations.select_related('specialization').order_by('pk')
    return pairs.get(specialization__name=spec) if spec else pairs.first()


def make_shift(doctor, room, day=None, start=9, end=11, minutes=30, spec=None):
    return services.create_shift(doctor_specialization(doctor, spec), room, day or future_day(), time(start),
                                 time(end), minutes)


def make_patient(phone='+79140001122', name='Андреев Кирилл Олегович'):
    return Patient.objects.create(full_name=name, phone=phone, sport='хоккей')
