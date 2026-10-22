from rest_framework import serializers

from .models import Doctor, Room, Specialization


class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = ['id', 'name']


class DoctorSerializer(serializers.ModelSerializer):
    specialization_name = serializers.CharField(source='specialization.name', read_only=True)
    availability_status = serializers.CharField(read_only=True)

    class Meta:
        model = Doctor
        fields = ['id', 'full_name', 'specialization', 'specialization_name', 'account', 'availability_status']


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'number', 'floor', 'building']
