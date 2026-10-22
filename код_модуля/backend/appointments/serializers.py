from rest_framework import serializers

from .models import Appointment, Patient, SmsNotification
from .services import normalize_phone


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'full_name', 'phone', 'sport']

    def validate_phone(self, value):
        phone = normalize_phone(value)
        if len(phone) != 12:
            raise serializers.ValidationError('Введите номер телефона в формате +7XXXXXXXXXX.')
        return phone


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_phone = serializers.CharField(source='patient.phone', read_only=True)
    date = serializers.DateField(source='slot.shift.date', read_only=True)
    start_time = serializers.TimeField(source='slot.start_time', read_only=True)
    doctor_name = serializers.CharField(source='slot.shift.doctor.full_name', read_only=True)
    specialization = serializers.CharField(source='slot.shift.doctor.specialization.name', read_only=True)
    room_number = serializers.CharField(source='slot.shift.room.number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'patient_name', 'patient_phone', 'slot', 'date', 'start_time', 'doctor_name',
                  'specialization', 'room_number', 'status', 'status_display', 'channel', 'channel_display', 'created_at', 'source']
        read_only_fields = ['status', 'channel', 'created_at', 'source']
        # занятость слота проверяет сервис book() с блокировкой строки слота
        validators = []


class SmsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmsNotification
        fields = ['id', 'appointment', 'phone', 'text', 'sent_at', 'status']
