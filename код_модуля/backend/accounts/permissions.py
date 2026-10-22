from rest_framework.permissions import BasePermission


class IsAdministrator(BasePermission):
    """Функции модуля доступны только роли «Администратор» (требование 2.2)."""

    message = 'Функция доступна только администратору.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_administrator and user.state == 'active')
