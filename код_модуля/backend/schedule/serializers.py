from rest_framework import serializers

from .models import Shift, Slot, UnavailabilityPeriod


class SlotSerializer(serializers.ModelSerializer):
    date = serializers.DateField(source='shift.date', read_only=True)
    doctor = serializers.IntegerField(source='shift.doctor_id', read_only=True)
    doctor_name = serializers.CharField(source='shift.doctor.full_name', read_only=True)
    room_number = serializers.CharField(source='shift.room.number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Slot
        fields = ['id', 'shift', 'date', 'start_time', 'end_time', 'status', 'status_display',
                  'doctor', 'doctor_name', 'room_number']


class ShiftSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    room_number = serializers.CharField(source='room.number', read_only=True)
    slots = SlotSerializer(many=True, read_only=True)

    class Meta:
        model = Shift
        fields = ['id', 'doctor', 'doctor_name', 'room', 'room_number', 'date', 'start_time', 'end_time',
                  'slot_minutes', 'slots']


class PeriodSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)

    class Meta:
        model = UnavailabilityPeriod
        fields = ['id', 'doctor', 'doctor_name', 'reason', 'reason_display', 'date_from', 'date_to']
