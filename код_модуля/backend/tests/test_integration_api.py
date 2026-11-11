"""Интеграционные тесты: REST API, сервисы и база данных PostgreSQL вместе."""
from datetime import timedelta

from rest_framework.test import APITestCase

from accounts.models import User
from appointments.models import Appointment, SmsNotification
from directory.models import Specialization
from schedule.models import Slot
from tests.factories import future_day, make_admin, make_doctor, make_patient, make_room


class ApiTestCase(APITestCase):
    def setUp(self):
        make_admin()
        r = self.client.post('/api/auth/login/', {'login': 'admin', 'password': 'admin12345'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + r.data['token'])
        self.day = future_day()


class AuthApiTests(APITestCase):
    def test_login_returns_token_and_role(self):
        make_admin()
        r = self.client.post('/api/auth/login/', {'login': 'admin', 'password': 'admin12345'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['role'], 'admin')

    def test_lock_after_three_failures(self):
        make_admin()
        for _ in range(3):
            self.client.post('/api/auth/login/', {'login': 'admin', 'password': 'bad'}, format='json')
        r = self.client.post('/api/auth/login/', {'login': 'admin', 'password': 'admin12345'}, format='json')
        self.assertEqual(r.status_code, 423)

    def test_doctor_gets_redirect_and_no_admin_access(self):
        doc = User(username='petrov', full_name='Петров А. И.', role=User.Role.DOCTOR)
        doc.set_password('doctor12345')
        doc.save()
        r = self.client.post('/api/auth/login/', {'login': 'petrov', 'password': 'doctor12345'}, format='json')
        self.assertIn('redirect', r.data)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + r.data['token'])
        self.assertEqual(self.client.get('/api/doctors/').status_code, 403)

    def test_anonymous_has_no_access(self):
        self.assertEqual(self.client.get('/api/shifts/').status_code, 401)


class AccountsApiTests(ApiTestCase):
    def test_create_block_and_reset(self):
        r = self.client.post('/api/accounts/', {'full_name': 'Смирнова О. В.', 'login': 'smirnova',
                                                'password': 'temp12345', 'role': 'doctor'}, format='json')
        self.assertEqual(r.status_code, 201)
        uid = r.data['id']
        self.assertEqual(self.client.post(f'/api/accounts/{uid}/block/').data['state'], 'blocked')
        self.assertEqual(len(self.client.post(f'/api/accounts/{uid}/reset-password/').data['temp_password']), 10)

    def test_duplicate_login_rejected(self):
        r = self.client.post('/api/accounts/', {'full_name': 'X', 'login': 'admin', 'password': 'temp12345',
                                                'role': 'admin'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_short_password_rejected(self):
        r = self.client.post('/api/accounts/', {'full_name': 'X', 'login': 'x', 'password': '123', 'role': 'admin'},
                             format='json')
        self.assertEqual(r.status_code, 400)


class DirectoryApiTests(ApiTestCase):
    def test_doctor_with_shift_cannot_be_deleted(self):
        doctor, room = make_doctor(), make_room()
        self.client.post('/api/shifts/', {'doctor': doctor.pk, 'room': room.pk, 'date': self.day,
                                          'start_time': '09:00', 'end_time': '10:00', 'slot_minutes': 30}, format='json')
        self.assertEqual(self.client.delete(f'/api/doctors/{doctor.pk}/').status_code, 409)
        self.assertEqual(self.client.delete(f'/api/rooms/{room.pk}/').status_code, 409)


    def test_doctor_from_account_with_several_specializations(self):
        acc = User.objects.create(username='sokolova', full_name='Соколова Анна Николаевна', role=User.Role.DOCTOR)
        specs = [Specialization.objects.create(name=n).pk for n in ('Кардиолог', 'Спортивный врач')]
        r = self.client.post('/api/doctors/', {'account': acc.pk, 'specializations': specs}, format='json')
        self.assertEqual(r.status_code, 201)
        # ФИО врача берётся из учётной записи
        self.assertEqual(r.data['full_name'], 'Соколова Анна Николаевна')
        self.assertEqual(sorted(r.data['specialization_names']), ['Кардиолог', 'Спортивный врач'])
        r = self.client.post('/api/doctors/', {'account': acc.pk, 'specializations': specs[:1]}, format='json')
        self.assertEqual(r.status_code, 400)


class ScheduleApiTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.doctor, self.room = make_doctor(), make_room()

    def shift(self, start='09:00', end='11:00', doctor=None, room=None):
        return self.client.post('/api/shifts/', {'doctor': (doctor or self.doctor).pk, 'room': (room or self.room).pk,
                                                 'date': self.day, 'start_time': start, 'end_time': end,
                                                 'slot_minutes': 30}, format='json')

    def test_create_shift_returns_slots(self):
        r = self.shift()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(len(r.data['slots']), 4)

    def test_conflicting_shift_returns_409(self):
        self.shift()
        r = self.shift('10:00', '12:00', room=make_room('102'))
        self.assertEqual(r.status_code, 409)
        self.assertIn('Врач уже работает', r.data['detail'])

    def test_shift_requires_existing_doctor_specialization(self):
        doctor = make_doctor('Смирнова Ольга Викторовна', spec=['Спортивный врач', 'Кардиолог'])
        cardio = Specialization.objects.get(name='Кардиолог')
        base = {'doctor': doctor.pk, 'room': self.room.pk, 'date': self.day, 'start_time': '09:00',
                'end_time': '10:00', 'slot_minutes': 30}
        # у врача две специализации – без указания специализации смена не создаётся
        self.assertEqual(self.client.post('/api/shifts/', base, format='json').status_code, 400)
        # пара «врач – специализация» должна существовать
        r = self.client.post('/api/shifts/', {**base, 'doctor': self.doctor.pk, 'specialization': cardio.pk},
                             format='json')
        self.assertEqual(r.status_code, 400)
        r = self.client.post('/api/shifts/', {**base, 'specialization': cardio.pk}, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual((r.data['doctor'], r.data['specialization']), (doctor.pk, cardio.pk))

    def test_filter_by_doctor_and_dates(self):
        self.shift()
        r = self.client.get('/api/shifts/', {'doctor': self.doctor.pk, 'date_from': self.day, 'date_to': self.day})
        self.assertEqual(len(r.data), 1)


class DoctorUnavailabilityFlowTests(ApiTestCase):
    """Сквозной сценарий из подраздела 2.3: недоступность врача → перенос записей → SMS."""

    def test_full_flow(self):
        petrov, smirnova = make_doctor(), make_doctor('Смирнова Ольга Викторовна')
        r1, r2 = make_room('101'), make_room('102')
        for doc, room in [(petrov, r1), (smirnova, r2)]:
            self.client.post('/api/shifts/', {'doctor': doc.pk, 'room': room.pk, 'date': self.day, 'start_time': '09:00',
                                              'end_time': '11:00', 'slot_minutes': 30}, format='json')
        patient = make_patient()
        slot = Slot.objects.filter(shift__doctor_specialization__doctor=petrov).first()
        r = self.client.post('/api/appointments/', {'patient': patient.pk, 'slot': slot.pk}, format='json')
        self.assertEqual(r.status_code, 201)
        app_id = r.data['id']

        r = self.client.post('/api/unavailability/', {'doctor': petrov.pk, 'reason': 'illness', 'date_from': self.day,
                                                      'date_to': self.day + timedelta(days=2)}, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual([a['id'] for a in r.data['affected']], [app_id])
        self.assertEqual([a['id'] for a in self.client.get('/api/appointments/affected/').data], [app_id])

        proposals = self.client.get(f'/api/appointments/{app_id}/proposals/').data
        self.assertTrue(proposals)
        self.assertTrue(all(p['doctor'] == smirnova.pk for p in proposals))

        r = self.client.post(f'/api/appointments/{app_id}/reschedule/', {'slot': proposals[0]['id']}, format='json')
        self.assertEqual(r.status_code, 200)
        # переносится та же запись: меняется только слот, новая запись не создаётся
        self.assertEqual(r.data['id'], app_id)
        self.assertEqual(r.data['status'], 'active')
        self.assertEqual(r.data['slot'], proposals[0]['id'])
        self.assertEqual(Appointment.objects.count(), 1)
        self.assertEqual(SmsNotification.objects.count(), 1)
        self.assertEqual(self.client.get('/api/appointments/affected/').data, [])

        # повторный перенос в занятый ею же слот отклоняется, в другой свободный – выполняется
        r = self.client.post(f'/api/appointments/{app_id}/reschedule/', {'slot': proposals[0]['id']}, format='json')
        self.assertEqual(r.status_code, 409)
        r = self.client.post(f'/api/appointments/{app_id}/reschedule/', {'slot': proposals[1]['id']}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Slot.objects.get(pk=proposals[0]['id']).status, 'free')

    def test_new_patient_booking_and_cancel(self):
        doctor, room = make_doctor(), make_room()
        self.client.post('/api/shifts/', {'doctor': doctor.pk, 'room': room.pk, 'date': self.day, 'start_time': '09:00',
                                          'end_time': '10:00', 'slot_minutes': 30}, format='json')
        self.assertEqual(self.client.get('/api/patients/', {'phone': '8 914 555-66-77'}).data, [])
        p = self.client.post('/api/patients/', {'full_name': 'Волков Егор', 'phone': '8 914 555-66-77',
                                                'sport': 'бокс'}, format='json')
        self.assertEqual(p.data['phone'], '+79145556677')
        slot = Slot.objects.first()
        a = self.client.post('/api/appointments/', {'patient': p.data['id'], 'slot': slot.pk}, format='json')
        self.assertEqual(self.client.post('/api/appointments/', {'patient': p.data['id'], 'slot': slot.pk},
                                          format='json').status_code, 409)
        r = self.client.post(f'/api/appointments/{a.data["id"]}/cancel/')
        self.assertEqual(r.data['status'], 'cancelled')
        self.assertEqual(Slot.objects.get(pk=slot.pk).status, 'free')
