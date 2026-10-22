from django.db.models import ProtectedError
from rest_framework import status, viewsets
from rest_framework.response import Response

from .models import Doctor, Room, Specialization
from .serializers import DoctorSerializer, RoomSerializer, SpecializationSerializer


class ProtectedDeleteMixin:
    """Удаление запрещено, если на объект ссылаются смены расписания."""

    protected_message = 'Объект используется в расписании и не может быть удалён.'

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response({'detail': self.protected_message}, status=status.HTTP_409_CONFLICT)


class SpecializationViewSet(viewsets.ModelViewSet):
    queryset = Specialization.objects.all()
    serializer_class = SpecializationSerializer


class DoctorViewSet(ProtectedDeleteMixin, viewsets.ModelViewSet):
    queryset = Doctor.objects.select_related('specialization')
    serializer_class = DoctorSerializer
    protected_message = 'У врача есть смены в расписании. Сначала удалите или перенесите их.'

    def get_queryset(self):
        qs = super().get_queryset()
        spec = self.request.query_params.get('specialization')
        return qs.filter(specialization_id=spec) if spec else qs


class RoomViewSet(ProtectedDeleteMixin, viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    protected_message = 'Кабинет используется в расписании и не может быть удалён.'
