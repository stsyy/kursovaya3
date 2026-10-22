"""Вспомогательные функции для создания тестовых данных."""
from datetime import time, timedelta

from django.utils import timezone

from accounts.models import User
from appointments.models import Patient
from directory.models import Doctor, Room, Specialization
from schedule import services


def future_day(days=2):
    return timezone.localdate() + timedelta(days=days)


def make_admin(login='admin', password='admin12345'):
    user = User(username=login, full_name='Иванова Мария Сергеевна', role=User.Role.ADMIN)
    user.set_password(password)
    user.save()
    return user


def make_doctor(name='Петров Алексей Иванович', spec='Спортивный врач'):
    specialization, _ = Specialization.objects.get_or_create(name=spec)
    return Doctor.objects.create(full_name=name, specialization=specialization)


def make_room(number='101'):
    return Room.objects.create(number=number, floor=1, building='Главный')


def make_shift(doctor, room, day=None, start=9, end=11, minutes=30):
    return services.create_shift(doctor, room, day or future_day(), time(start), time(end), minutes)


def make_patient(phone='+79140001122', name='Андреев Кирилл Олегович'):
    return Patient.objects.create(full_name=name, phone=phone, sport='хоккей')
