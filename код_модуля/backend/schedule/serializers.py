from rest_framework import serializers

from directory.models import Doctor, DoctorSpecialization, Specialization
from .models import Shift, Slot, UnavailabilityPeriod


class SlotSerializer(serializers.ModelSerializer):
    date = serializers.DateField(source='shift.date', read_only=True)
    doctor = serializers.IntegerField(source='shift.doctor_specialization.doctor_id', read_only=True)
    doctor_name = serializers.CharField(source='shift.doctor.full_name', read_only=True)
    specialization = serializers.IntegerField(source='shift.doctor_specialization.specialization_id', read_only=True)
    specialization_name = serializers.CharField(source='shift.specialization.name', read_only=True)
    room_number = serializers.CharField(source='shift.room.number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Slot
        fields = ['id', 'shift', 'date', 'start_time', 'end_time', 'status', 'status_display',
                  'doctor', 'doctor_name', 'specialization', 'specialization_name', 'room_number']


class ShiftSerializer(serializers.ModelSerializer):
    """Смена. При создании передаются врач и специализация, по ним находится запись
    «специализация врача»; если у врача одна специализация, её можно не указывать."""

    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all(), write_only=True, required=False)
    specialization = serializers.PrimaryKeyRelatedField(queryset=Specialization.objects.all(), write_only=True,
                                                        required=False)
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    specialization_name = serializers.CharField(source='specialization.name', read_only=True)
    room_number = serializers.CharField(source='room.number', read_only=True)
    slots = SlotSerializer(many=True, read_only=True)

    class Meta:
        model = Shift
        fields = ['id', 'doctor', 'doctor_name', 'specialization', 'specialization_name', 'doctor_specialization',
                  'room', 'room_number', 'date', 'start_time', 'end_time', 'slot_minutes', 'slots']
        read_only_fields = ['doctor_specialization']

    def validate(self, attrs):
        doctor = attrs.pop('doctor', None)
        specialization = attrs.pop('specialization', None)
        if self.instance is not None:
            # врач, специализация и дата существующей смены не меняются
            return attrs
        if doctor is None:
            raise serializers.ValidationError({'doctor': 'Выберите врача.'})
        options = DoctorSpecialization.objects.filter(doctor=doctor)
        if specialization is not None:
            options = options.filter(specialization=specialization)
        elif options.count() > 1:
            raise serializers.ValidationError({'specialization': 'Выберите специализацию, по которой врач '
                                                                 'ведёт приём в смене.'})
        pair = options.first()
        if pair is None:
            raise serializers.ValidationError({'specialization': 'У выбранного врача нет такой специализации.'})
        attrs['doctor_specialization'] = pair
        return attrs

    def to_representation(self, shift):
        data = super().to_representation(shift)
        data['doctor'] = shift.doctor_specialization.doctor_id
        data['specialization'] = shift.doctor_specialization.specialization_id
        return data


class PeriodSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    time_from = serializers.TimeField(required=False, allow_null=True)
    time_to = serializers.TimeField(required=False, allow_null=True)

    class Meta:
        model = UnavailabilityPeriod
        fields = ['id', 'doctor', 'doctor_name', 'reason', 'reason_display', 'date_from', 'date_to',
                  'time_from', 'time_to']
