from django.conf import settings
from django.db.models import ProtectedError
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from . import services
from .models import User
from .serializers import AccountSerializer, LoginSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    data = LoginSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    try:
        user = services.login(data.validated_data['login'], data.validated_data['password'])
    except services.AuthError as e:
        code = status.HTTP_423_LOCKED if e.code == 'locked' else (
            status.HTTP_403_FORBIDDEN if e.code == 'blocked' else status.HTTP_400_BAD_REQUEST)
        return Response({'detail': e.message, 'code': e.code}, status=code)
    token, _ = Token.objects.get_or_create(user=user)
    body = {'token': token.key, 'full_name': user.full_name, 'role': user.role}
    if user.role == User.Role.DOCTOR:
        # врач работает в модуле ведения приёма (подраздел 2.2)
        body['redirect'] = settings.DOCTOR_MODULE_URL
    return Response(body)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    Token.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class AccountViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_superuser=False)
    serializer_class = AccountSerializer

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            return Response({'detail': 'Нельзя удалить собственную учётную запись.'}, status=status.HTTP_409_CONFLICT)
        if services.account_has_active_appointments(user):
            return Response({'detail': 'У врача есть активные записи пациентов. Перенесите или отмените их.'},
                            status=status.HTTP_409_CONFLICT)
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            # вместе с учётной записью удаляется врач; врача со сменами в расписании удалить нельзя
            return Response({'detail': 'У врача есть смены в расписании. Сначала удалите их.'},
                            status=status.HTTP_409_CONFLICT)

    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        user = self.get_object()
        user.state = User.State.BLOCKED
        user.save(update_fields=['state'])
        Token.objects.filter(user=user).delete()
        return Response(AccountSerializer(user).data)

    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        user = self.get_object()
        user.state = User.State.ACTIVE
        user.failed_attempts = 0
        user.locked_until = None
        user.save(update_fields=['state', 'failed_attempts', 'locked_until'])
        return Response(AccountSerializer(user).data)

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        user = self.get_object()
        password = services.generate_temp_password()
        user.set_password(password)
        user.save(update_fields=['password'])
        return Response({'temp_password': password})
