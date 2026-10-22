from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from schedule.serializers import SlotSerializer
from . import services
from .models import Appointment, Patient, SmsNotification
from .serializers import AppointmentSerializer, PatientSerializer, SmsSerializer


def error(e):
    return Response({'detail': e.message}, status=status.HTTP_409_CONFLICT)


class PatientViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                     mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = PatientSerializer

    def get_queryset(self):
        phone = self.request.query_params.get('phone')
        qs = Patient.objects.all()
        return qs.filter(phone=services.normalize_phone(phone)) if phone else qs


class AppointmentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                         viewsets.GenericViewSet):
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        qs = Appointment.objects.select_related('patient', 'slot__shift__doctor__specialization', 'slot__shift__room')
        p = self.request.query_params
        filters = {'doctor': 'slot__shift__doctor_id', 'date': 'slot__shift__date', 'status': 'status', 'channel': 'channel',
                   'date_from': 'slot__shift__date__gte', 'date_to': 'slot__shift__date__lte'}
        for param, field in filters.items():
            if p.get(param):
                qs = qs.filter(**{field: p[param]})
        if p.get('phone'):
            qs = qs.filter(patient__phone=services.normalize_phone(p['phone']))
        return qs

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            app = services.book(ser.validated_data['patient'], ser.validated_data['slot'].pk)
        except services.AppointmentError as e:
            return error(e)
        return Response(AppointmentSerializer(app).data, status=status.HTTP_201_CREATED)

    @action(detail=False)
    def affected(self, request):
        return Response(AppointmentSerializer(services.affected_appointments(), many=True).data)

    @action(detail=True)
    def proposals(self, request, pk=None):
        return Response(SlotSerializer(services.propose_slots(self.get_object()), many=True).data)

    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        try:
            new = services.reschedule(self.get_object().pk, request.data.get('slot'))
        except services.AppointmentError as e:
            return error(e)
        return Response(AppointmentSerializer(new).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        try:
            app = services.cancel(self.get_object().pk)
        except services.AppointmentError as e:
            return error(e)
        return Response(AppointmentSerializer(app).data)


class SmsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SmsNotification.objects.select_related('appointment')
    serializer_class = SmsSerializer
