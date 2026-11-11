"""UI-тесты: браузер Chromium (Playwright) работает с собранным клиентом Vue.js,
который обслуживает тестовый сервер Django. Перед запуском: cd frontend && npm run build."""
import os
from datetime import timedelta

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import expect, sync_playwright

from appointments.models import Appointment
from appointments import services as app_services
from tests.factories import future_day, make_admin, make_doctor, make_patient, make_room, make_shift

os.environ.setdefault('DJANGO_ALLOW_ASYNC_UNSAFE', 'true')
CHROMIUM = os.environ.get('CHROMIUM_PATH')


class UiTestCase(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(executable_path=CHROMIUM, args=['--no-sandbox'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        super().tearDownClass()

    def setUp(self):
        make_admin()
        self.day = future_day()
        self.page = self.browser.new_page(viewport={'width': 1366, 'height': 800})
        self.page.set_default_timeout(10000)

    def tearDown(self):
        self.page.close()

    def login(self, password='admin12345'):
        self.page.goto(self.live_server_url + '/login')
        self.page.fill('input[name=login]', 'admin')
        self.page.fill('input[name=password]', password)
        self.page.click('button[type=submit]')


class LoginUiTests(UiTestCase):
    def test_wrong_password_shows_error(self):
        self.login('wrong-password')
        expect(self.page.locator('[data-test=login-error]')).to_have_text('Неверный логин или пароль.')

    def test_successful_login_opens_schedule(self):
        self.login()
        self.page.wait_for_url('**/schedule')
        expect(self.page.locator('h1')).to_have_text('Расписание')

    def test_logout(self):
        self.login()
        self.page.wait_for_url('**/schedule')
        self.page.click('nav >> text=Выйти')
        self.page.wait_for_url('**/login')


class ScheduleUiTests(UiTestCase):
    def setUp(self):
        super().setUp()
        self.doctor, self.room = make_doctor(), make_room()
        self.login()
        self.page.wait_for_url('**/schedule')

    def fill_shift(self, start, end):
        self.page.click('text=Создать смену')
        d = self.page.locator('.dialog')
        d.locator('select').nth(0).select_option(label=self.doctor.full_name)
        # у врача одна специализация – она выбирается в форме автоматически (select nth(1))
        expect(d.locator('select').nth(1)).to_have_value(str(self.doctor.specializations.get().pk))
        d.locator('select').nth(2).select_option(index=0)
        d.locator('input[type=date]').fill(str(self.day))
        d.locator('input[type=time]').nth(0).fill(start)
        d.locator('input[type=time]').nth(1).fill(end)
        d.locator('button[type=submit]').click()

    def test_create_shift_shows_slots(self):
        self.fill_shift('09:00', '10:00')
        expect(self.page.locator('.dialog')).to_have_count(0)
        expect(self.page.locator('td.slots .badge')).to_have_count(2)

    def test_conflict_message(self):
        make_shift(self.doctor, self.room, self.day, 9, 12)
        self.fill_shift('11:00', '13:00')
        expect(self.page.locator('[data-test=conflict]').first).to_contain_text('Врач уже работает')


class RescheduleUiTests(UiTestCase):
    def setUp(self):
        super().setUp()
        self.petrov = make_doctor()
        self.smirnova = make_doctor('Смирнова Ольга Викторовна')
        make_shift(self.petrov, make_room('101'), self.day)
        make_shift(self.smirnova, make_room('102'), self.day)
        self.patient = make_patient()
        self.app = app_services.book(self.patient, self.petrov.shifts.first().slots.first().pk)
        self.login()
        self.page.wait_for_url('**/schedule')

    def test_unavailability_leads_to_reschedule(self):
        self.page.click('nav >> text=Доступность врачей')
        self.page.click('text=Установить период')
        d = self.page.locator('.dialog')
        expect(d.locator('select').nth(0).locator('option')).to_have_count(2)
        d.locator('select').nth(0).select_option(label=self.petrov.full_name)
        d.locator('input[type=date]').nth(0).fill(str(self.day))
        d.locator('input[type=date]').nth(1).fill(str(self.day + timedelta(days=3)))
        d.locator('button[type=submit]').click()
        self.page.wait_for_url('**/reschedule')
        expect(self.page.locator('tr.selected')).to_contain_text(self.patient.full_name)
        self.page.locator('text=Перенести').first.click()
        expect(self.page.locator('[data-test=move-result]')).to_contain_text('SMS-уведомление отправлено')
        old_slot_id = self.app.slot_id
        self.app.refresh_from_db()
        # перенесена та же запись: она осталась активной и получила новый слот
        self.assertEqual(self.app.status, Appointment.Status.ACTIVE)
        self.assertNotEqual(self.app.slot_id, old_slot_id)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_cancel_from_appointments(self):
        self.page.click('nav >> text=Записи пациентов')
        self.page.locator('button:has-text("Отменить")').first.click()
        self.page.click('[data-test=confirm]')
        expect(self.page.locator('.info')).to_contain_text('Запись отменена')
        self.app.refresh_from_db()
        self.assertEqual(self.app.status, Appointment.Status.CANCELLED)


class AppointmentUiTests(UiTestCase):
    def test_book_new_patient(self):
        doctor = make_doctor('Кузнецов Дмитрий Павлович', spec='Травматолог-ортопед')
        make_shift(doctor, make_room(), self.day)
        self.login()
        self.page.wait_for_url('**/schedule')
        self.page.click('nav >> text=Записи пациентов')
        self.page.click('text=Новая запись')
        self.page.fill('input[name=phone]', '89145556677')
        self.page.click('.dialog >> text=Найти')
        self.page.fill('input[name=full_name]', 'Дмитриев Артём Ильич')
        self.page.locator('.dialog select').nth(0).select_option(label='Травматолог-ортопед')
        self.page.locator('.dialog .pick').first.click()
        self.page.click('.dialog >> text=Записать')
        expect(self.page.locator('.info')).to_contain_text('Дмитриев Артём Ильич записан')
        self.assertEqual(Appointment.objects.get().patient.phone, '+79145556677')


class AccountsUiTests(UiTestCase):
    def test_create_account(self):
        self.login()
        self.page.wait_for_url('**/schedule')
        self.page.click('nav >> text=Учётные записи')
        self.page.click('text=Создать')
        d = self.page.locator('.dialog')
        d.locator('input').nth(0).fill('Соколова Анна Николаевна')
        d.locator('input').nth(1).fill('sokolova')
        d.locator('input').nth(2).fill('temp12345')
        d.locator('button[type=submit]').click()
        expect(self.page.locator('table')).to_contain_text('sokolova')
