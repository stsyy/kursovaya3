"""Модульные тесты расписания (процессы А3–А5)."""
from datetime import time, timedelta

from django.test import TestCase

from schedule import services
from schedule.models import Slot
from appointments import services as app_services
from tests.factories import future_day, make_doctor, make_patient, make_room, make_shift


class SlotGenerationTests(TestCase):
    def test_slot_bounds_split_interval(self):
        day = future_day()
        bounds = list(services.slot_bounds(day, time(9), time(11), 30))
        self.assertEqual(bounds, [(time(9), time(9, 30)), (time(9, 30), time(10)),
                                  (time(10), time(10, 30)), (time(10, 30), time(11))])

    def test_incomplete_tail_is_dropped(self):
        bounds = list(services.slot_bounds(future_day(), time(9), time(10, 10), 20))
        self.assertEqual(len(bounds), 3)

    def test_create_shift_generates_free_slots(self):
        shift = make_shift(make_doctor(), make_room())
        self.assertEqual(shift.slots.count(), 4)
        self.assertFalse(shift.slots.exclude(status=Slot.Status.FREE).exists())


class ConflictTests(TestCase):
    def setUp(self):
        self.doctor, self.room = make_doctor(), make_room()
        self.day = future_day()
        make_shift(self.doctor, self.room, self.day, 9, 13)

    def test_doctor_overlap_is_conflict(self):
        errors = services.check_conflicts(self.doctor, make_room('102'), self.day, time(12), time(15))
        self.assertTrue(any('Врач уже работает' in e for e in errors))

    def test_room_overlap_is_conflict(self):
        other = make_doctor('Смирнова Ольга Викторовна')
        errors = services.check_conflicts(other, self.room, self.day, time(10), time(11))
        self.assertTrue(any('Кабинет 101 занят' in e for e in errors))

    def test_adjacent_shift_is_not_conflict(self):
        other = make_doctor('Смирнова Ольга Викторовна')
        self.assertEqual(services.check_conflicts(other, self.room, self.day, time(13), time(17)), [])

    def test_start_after_end(self):
        errors = services.check_conflicts(self.doctor, self.room, self.day + timedelta(days=1), time(12), time(9))
        self.assertEqual(len(errors), 1)

    def test_create_shift_raises_on_conflict(self):
        with self.assertRaises(services.ScheduleError):
            services.create_shift(self.doctor, self.room, self.day, time(11), time(12), 30)


class UnavailabilityTests(TestCase):
    def setUp(self):
        self.doctor, self.room = make_doctor(), make_room()
        self.day = future_day()
        self.shift = make_shift(self.doctor, self.room, self.day)
        self.patient = make_patient()
        self.booked = app_services.book(self.patient, self.shift.slots.first().pk)

    def test_period_blocks_slots_and_returns_affected(self):
        period, affected = services.set_unavailability(self.doctor, 'illness', self.day, self.day)
        self.assertEqual([a.pk for a in affected], [self.booked.pk])
        self.assertFalse(self.shift.slots.exclude(status=Slot.Status.BLOCKED).exists())
        self.assertFalse(self.doctor.is_available(self.day))

    def test_period_dates_validated(self):
        with self.assertRaises(services.ScheduleError):
            services.set_unavailability(self.doctor, 'illness', self.day, self.day - timedelta(days=1))

    def test_overlapping_period_rejected(self):
        services.set_unavailability(self.doctor, 'illness', self.day, self.day + timedelta(days=3))
        with self.assertRaises(services.ScheduleError):
            services.set_unavailability(self.doctor, 'vacation', self.day + timedelta(days=2), self.day + timedelta(days=5))

    def test_remove_period_restores_statuses(self):
        period, _ = services.set_unavailability(self.doctor, 'illness', self.day, self.day)
        services.remove_unavailability(period)
        statuses = dict(self.shift.slots.values_list('pk', 'status'))
        self.assertEqual(statuses[self.booked.slot_id], Slot.Status.BUSY)
        self.assertEqual(list(statuses.values()).count(Slot.Status.FREE), 3)

    def test_early_return_unblocks_later_days(self):
        later = make_shift(self.doctor, self.room, self.day + timedelta(days=1))
        period, _ = services.set_unavailability(self.doctor, 'illness', self.day, self.day + timedelta(days=1))
        services.change_unavailability_end(period, self.day)
        self.assertFalse(later.slots.exclude(status=Slot.Status.FREE).exists())

    def test_delete_shift_with_appointments_blocks_slots(self):
        affected = services.delete_shift(self.shift)
        self.assertEqual(len(affected), 1)
        self.assertTrue(type(self.shift).objects.filter(pk=self.shift.pk).exists())

    def test_update_shift_blocks_busy_slots_outside_new_time(self):
        affected = services.update_shift(self.shift, self.room, time(10), time(11))
        self.assertEqual([a.pk for a in affected], [self.booked.pk])
        self.assertEqual(self.shift.slots.filter(status=Slot.Status.FREE).count(), 2)
