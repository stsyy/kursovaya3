from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from appointments.serializers import AppointmentSerializer
from . import services
from .models import Shift, Slot, UnavailabilityPeriod
from .serializers import PeriodSerializer, ShiftSerializer, SlotSerializer


def conflict(e):
    return Response({'detail': e.messages[0], 'errors': e.messages}, status=status.HTTP_409_CONFLICT)


def with_affected(data, affected):
    return {**data, 'affected': AppointmentSerializer(affected, many=True).data}


def filter_by_period(qs, params, prefix=''):
    for param, field in (('doctor', 'doctor_specialization__doctor_id'),
                         ('specialization', 'doctor_specialization__specialization_id'), ('room', 'room_id'),
                         ('date_from', 'date__gte'), ('date_to', 'date__lte')):
        if params.get(param):
            qs = qs.filter(**{prefix + field: params[param]})
    return qs


class ShiftViewSet(viewsets.ModelViewSet):
    serializer_class = ShiftSerializer

    def get_queryset(self):
        qs = (Shift.objects.select_related('doctor_specialization__doctor__account',
                                           'doctor_specialization__specialization', 'room')
              .prefetch_related('slots__shift__doctor_specialization__doctor__account',
                                'slots__shift__doctor_specialization__specialization', 'slots__shift__room'))
        return filter_by_period(qs, self.request.query_params)

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            shift = services.create_shift(**ser.validated_data)
        except services.ScheduleError as e:
            return conflict(e)
        return Response(ShiftSerializer(shift).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        shift = self.get_object()
        ser = self.get_serializer(shift, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        try:
            affected = services.update_shift(shift, d.get('room', shift.room), d.get('start_time', shift.start_time),
                                             d.get('end_time', shift.end_time))
        except services.ScheduleError as e:
            return conflict(e)
        shift.refresh_from_db()
        return Response(with_affected(ShiftSerializer(shift).data, affected))

    def destroy(self, request, *args, **kwargs):
        affected = services.delete_shift(self.get_object())
        if affected:
            return Response(with_affected({'detail': 'В смене есть записи пациентов. Слоты смены заблокированы, '
                                                     'перенесите записи.'}, affected), status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SlotViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SlotSerializer

    def get_queryset(self):
        qs = Slot.objects.select_related('shift__doctor_specialization__doctor__account',
                                         'shift__doctor_specialization__specialization', 'shift__room')
        qs = filter_by_period(qs, self.request.query_params, prefix='shift__')
        if self.request.query_params.get('status'):
            qs = qs.filter(status=self.request.query_params['status'])
        return qs

    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        slot = self.get_object()
        affected = services.block_slot(slot)
        return Response(with_affected(SlotSerializer(slot).data, affected))


class PeriodViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                    mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = PeriodSerializer

    def get_queryset(self):
        qs = UnavailabilityPeriod.objects.select_related('doctor__account')
        doctor = self.request.query_params.get('doctor')
        return qs.filter(doctor_id=doctor) if doctor else qs

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            period, affected = services.set_unavailability(**ser.validated_data)
        except services.ScheduleError as e:
            return conflict(e)
        return Response(with_affected(PeriodSerializer(period).data, affected), status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        period = self.get_object()
        ser = self.get_serializer(period, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        try:
            affected = services.change_unavailability_end(period, ser.validated_data.get('date_to', period.date_to))
        except services.ScheduleError as e:
            return conflict(e)
        return Response(with_affected(PeriodSerializer(period).data, affected))

    def destroy(self, request, *args, **kwargs):
        services.remove_unavailability(self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)
