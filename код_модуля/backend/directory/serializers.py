from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from accounts.models import User
from .models import Doctor, DoctorSpecialization, Room, Specialization


class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = ['id', 'name']


class DoctorSerializer(serializers.ModelSerializer):
    """Врач: ФИО только для чтения (берётся из учётной записи), специализаций может быть несколько."""

    full_name = serializers.CharField(read_only=True)
    account = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.DOCTOR),
        validators=[UniqueValidator(queryset=Doctor.objects.all(),
                                    message='Учётная запись уже привязана к другому врачу.')])
    specializations = serializers.PrimaryKeyRelatedField(queryset=Specialization.objects.all(), many=True,
                                                         allow_empty=False)
    specialization_names = serializers.SerializerMethodField()
    availability_status = serializers.CharField(read_only=True)

    class Meta:
        model = Doctor
        fields = ['id', 'full_name', 'account', 'specializations', 'specialization_names', 'availability_status']

    def get_specialization_names(self, doctor):
        return [s.name for s in doctor.specializations.all()]

    def validate_specializations(self, value):
        if self.instance is not None:
            removed = set(self.instance.specializations.all()) - set(value)
            used = DoctorSpecialization.objects.filter(doctor=self.instance, specialization__in=removed,
                                                       shifts__isnull=False).distinct()
            if used.exists():
                names = ', '.join(ds.specialization.name for ds in used)
                raise serializers.ValidationError(f'По специализации «{names}» у врача есть смены, '
                                                  f'удалить её нельзя.')
        return value

    @transaction.atomic
    def create(self, validated):
        specializations = validated.pop('specializations')
        doctor = Doctor.objects.create(**validated)
        doctor.specializations.set(specializations)
        return doctor

    @transaction.atomic
    def update(self, instance, validated):
        specializations = validated.pop('specializations', None)
        for k, v in validated.items():
            setattr(instance, k, v)
        instance.save()
        if specializations is not None:
            instance.specializations.set(specializations)
        return instance


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'number', 'floor', 'building']
