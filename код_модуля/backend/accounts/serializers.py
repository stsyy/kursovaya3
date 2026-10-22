from rest_framework import serializers

from .models import User


class AccountSerializer(serializers.ModelSerializer):
    login = serializers.CharField(source='username')
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'full_name', 'login', 'password', 'role', 'phone', 'state']
        read_only_fields = ['state']

    def validate_login(self, value):
        qs = User.objects.filter(username=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Логин уже занят.')
        return value

    def create(self, validated):
        password = validated.pop('password', None)
        if not password:
            raise serializers.ValidationError({'password': 'Укажите временный пароль.'})
        user = User(**validated)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated):
        password = validated.pop('password', None)
        for k, v in validated.items():
            setattr(instance, k, v)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField()
    password = serializers.CharField()
