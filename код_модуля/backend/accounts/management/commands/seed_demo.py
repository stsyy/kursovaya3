"""Демонстрационные данные: python manage.py seed_demo"""
from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from appointments import services as app_services
from appointments.models import Appointment, Patient
from directory.models import Doctor, DoctorSpecialization, Room, Specialization
from schedule import services


class Command(BaseCommand):
    help = 'Заполняет базу демонстрационными данными'

    def handle(self, *args, **opts):
        admin, _ = User.objects.get_or_create(username='admin', defaults={
            'full_name': 'Иванова Мария Сергеевна', 'role': User.Role.ADMIN, 'phone': '+79140000001'})
        admin.set_password('admin12345')
        admin.save()
        specs = {n: Specialization.objects.get_or_create(name=n)[0]
                 for n in ['Спортивный врач', 'Травматолог-ортопед', 'Кардиолог']}
        doctors = []
        # первая специализация врача – та, по которой он ведёт приём в демонстрационных сменах
        for login, name, spec_names in [('petrov', 'Петров Алексей Иванович', ['Спортивный врач']),
                                        ('smirnova', 'Смирнова Ольга Викторовна', ['Спортивный врач', 'Кардиолог']),
                                        ('kuznetsov', 'Кузнецов Дмитрий Павлович', ['Травматолог-ортопед']),
                                        ('sokolova', 'Соколова Анна Николаевна', ['Кардиолог'])]:
            acc, _ = User.objects.get_or_create(username=login, defaults={'full_name': name, 'role': User.Role.DOCTOR})
            acc.set_password('doctor12345')
            acc.save()
            doctor, _ = Doctor.objects.get_or_create(account=acc)
            pairs = [DoctorSpecialization.objects.get_or_create(doctor=doctor, specialization=specs[n])[0]
                     for n in spec_names]
            doctors.append((doctor, pairs[0]))
        rooms = [Room.objects.get_or_create(number=n, building='Главный', defaults={'floor': f})[0]
                 for n, f in [('101', 1), ('102', 1), ('205', 2), ('207', 2)]]
        today = timezone.localdate()
        for d in range(1, 8):
            day = today + timedelta(days=d)
            if day.weekday() >= 5:
                continue
            for (doc, pair), room, (a, b) in zip(doctors, rooms, [(9, 13), (13, 17), (9, 15), (10, 14)]):
                if not doc.shifts.filter(date=day).exists():
                    services.create_shift(pair, room, day, time(a), time(b), 30)
        patients = []
        for name, phone, sport in [('Андреев Кирилл Олегович', '+79140001122', 'хоккей'),
                                   ('Белова Дарья Игоревна', '+79140003344', 'плавание'),
                                   ('Волков Егор Сергеевич', '+79140005566', 'бокс'),
                                   ('Григорьева Полина Андреевна', '+79140007788', 'лёгкая атлетика')]:
            patients.append(Patient.objects.get_or_create(phone=phone, defaults={'full_name': name, 'sport': sport})[0])
        first = doctors[0][0].shifts.order_by('date').first()
        if first and not first.slots.filter(status='busy').exists():
            for i, (p, slot) in enumerate(zip(patients, first.slots.order_by('start_time')[::2])):
                app = app_services.book(p, slot.pk)
                if i >= 2:
                    # записи, созданные пациентами через форму онлайн-записи (вторая ещё не подтверждена кодом из SMS)
                    app.channel = Appointment.Channel.ONLINE
                    app.status = Appointment.Status.ACTIVE if i == 2 else Appointment.Status.PENDING
                    app.save(update_fields=['channel', 'status'])
        self.stdout.write(self.style.SUCCESS('Демонстрационные данные созданы. Вход: admin / admin12345'))
