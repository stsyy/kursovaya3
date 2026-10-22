"""Модульные тесты аутентификации (процесс А1, требования 3.1–3.2)."""
from django.test import TestCase, override_settings

from accounts import services
from accounts.models import User
from tests.factories import make_admin


class LoginTests(TestCase):
    def setUp(self):
        self.user = make_admin()

    def test_successful_login_resets_counter(self):
        self.user.failed_attempts = 2
        self.user.save()
        user = services.login('admin', 'admin12345')
        self.assertEqual(user.pk, self.user.pk)
        user.refresh_from_db()
        self.assertEqual(user.failed_attempts, 0)

    def test_wrong_password_increments_counter(self):
        with self.assertRaises(services.AuthError):
            services.login('admin', 'wrong-password')
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_attempts, 1)

    @override_settings(LOGIN_MAX_ATTEMPTS=3, LOGIN_LOCK_MINUTES=15)
    def test_three_failures_lock_account_for_15_minutes(self):
        for _ in range(3):
            with self.assertRaises(services.AuthError):
                services.login('admin', 'wrong-password')
        with self.assertRaises(services.AuthError) as ctx:
            services.login('admin', 'admin12345')  # даже верный пароль не принимается
        self.assertEqual(ctx.exception.code, 'locked')

    def test_blocked_account_cannot_login(self):
        self.user.state = User.State.BLOCKED
        self.user.save()
        with self.assertRaises(services.AuthError) as ctx:
            services.login('admin', 'admin12345')
        self.assertEqual(ctx.exception.code, 'blocked')

    def test_unknown_login(self):
        with self.assertRaises(services.AuthError):
            services.login('nobody', 'whatever1')

    def test_temp_password_length(self):
        self.assertGreaterEqual(len(services.generate_temp_password()), 8)

    def test_password_is_stored_as_hash(self):
        self.assertNotEqual(self.user.password, 'admin12345')
        self.assertTrue(self.user.check_password('admin12345'))
