"""Модульные тесты работы с записями пациентов (процесс А5)."""
from datetime import timedelta

from django.test import TestCase

from appointments import services
from appointments.models import Appointment, SmsNotification
from appointments.sms import ConsoleGateway
from schedule import services as schedule_services
from schedule.models import Slot
from tests.factories import future_day, make_doctor, make_patient, make_room, make_shift


class PhoneTests(TestCase):
    def test_normalize_variants(self):
        for raw in ['89140001122', '+7 (914) 000-11-22', '9140001122']:
            self.assertEqual(services.normalize_phone(raw), '+79140001122')


class AppointmentServiceTests(TestCase):
    def setUp(self):
        ConsoleGateway.outbox.clear()
        self.day = future_day()
        self.petrov = make_doctor()
        self.smirnova = make_doctor('Смирнова Ольга Викторовна')
        self.kuznetsov = make_doctor('Кузнецов Дмитрий Павлович', spec='Травматолог-ортопед')
        self.s1 = make_shift(self.petrov, make_room('101'), self.day)
        self.s2 = make_shift(self.smirnova, make_room('102'), self.day)
        self.s3 = make_shift(self.kuznetsov, make_room('205'), self.day)
        self.patient = make_patient()
        self.app = services.book(self.patient, self.s1.slots.first().pk)

    def test_book_marks_slot_busy(self):
        self.assertEqual(self.app.status, Appointment.Status.ACTIVE)
        self.assertEqual(Slot.objects.get(pk=self.app.slot_id).status, Slot.Status.BUSY)

    def test_cannot_book_busy_slot(self):
        with self.assertRaises(services.AppointmentError):
            services.book(make_patient('+79140003344', 'Белова Дарья'), self.app.slot_id)

    def test_proposals_same_specialization_only(self):
        doctors = {s.shift.doctor_specialization.doctor_id for s in services.propose_slots(self.app, limit=50)}
        self.assertNotIn(self.kuznetsov.pk, doctors)
        self.assertIn(self.smirnova.pk, doctors)

    def test_proposals_exclude_unavailable_doctor(self):
        schedule_services.set_unavailability(self.petrov, 'illness', self.day, self.day)
        schedule_services.set_unavailability(self.smirnova, 'vacation', self.day, self.day + timedelta(days=1))
        self.assertEqual(services.propose_slots(self.app), [])

    def test_affected_after_unavailability(self):
        schedule_services.set_unavailability(self.petrov, 'illness', self.day, self.day)
        self.assertEqual(list(services.affected_appointments()), [self.app])

    def test_reschedule_moves_same_appointment_and_sends_sms(self):
        schedule_services.set_unavailability(self.petrov, 'illness', self.day, self.day)
        old_slot_id = self.app.slot_id
        target = services.propose_slots(self.app)[0]
        moved = services.reschedule(self.app.pk, target.pk)
        self.assertEqual(moved.pk, self.app.pk)
        self.assertEqual(Appointment.objects.count(), 1)
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, Appointment.Status.ACTIVE)
        self.assertEqual(self.app.slot_id, target.pk)
        self.assertEqual(Slot.objects.get(pk=target.pk).status, Slot.Status.BUSY)
        # исходный слот остаётся заблокированным: врач недоступен
        self.assertEqual(Slot.objects.get(pk=old_slot_id).status, Slot.Status.BLOCKED)
        self.assertEqual(SmsNotification.objects.filter(appointment=self.app, status='sent').count(), 1)
        self.assertEqual(ConsoleGateway.outbox[-1][0], self.patient.phone)
        self.assertEqual(list(services.affected_appointments()), [])

    def test_reschedule_to_busy_slot_fails(self):
        other = services.book(make_patient('+79140003344', 'Белова Дарья'), self.s2.slots.first().pk)
        with self.assertRaises(services.AppointmentError):
            services.reschedule(self.app.pk, other.slot_id)
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, Appointment.Status.ACTIVE)

    def test_reschedule_to_other_specialization_fails(self):
        with self.assertRaises(services.AppointmentError):
            services.reschedule(self.app.pk, self.s3.slots.first().pk)
        self.app.refresh_from_db()
        self.assertEqual(self.app.slot.shift_id, self.s1.pk)

    def test_cancel_frees_slot_and_notifies(self):
        services.cancel(self.app.pk)
        self.assertEqual(Slot.objects.get(pk=self.app.slot_id).status, Slot.Status.FREE)
        self.assertTrue(SmsNotification.objects.filter(appointment=self.app).exists())

    def test_cancel_twice_fails(self):
        services.cancel(self.app.pk)
        with self.assertRaises(services.AppointmentError):
            services.cancel(self.app.pk)
