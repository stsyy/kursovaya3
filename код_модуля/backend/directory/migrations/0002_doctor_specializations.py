"""Врач может иметь несколько специализаций (таблица directory_doctorspecialization),
ФИО врача хранится только в учётной записи сотрудника."""
import django.db.models.deletion
from django.db import migrations, models


def forwards(apps, schema_editor):
    Doctor = apps.get_model('directory', 'Doctor')
    DoctorSpecialization = apps.get_model('directory', 'DoctorSpecialization')
    User = apps.get_model('accounts', 'User')
    for doctor in Doctor.objects.all():
        # прежняя единственная специализация становится первой записью таблицы специализаций врача
        DoctorSpecialization.objects.get_or_create(doctor=doctor, specialization_id=doctor.specialization_id)
        if doctor.account_id is None:
            # у врача без учётной записи ФИО переносится в новую учётную запись (без пароля, вход невозможен)
            username = f'doctor{doctor.pk}'
            while User.objects.filter(username=username).exists():
                username += '_'
            doctor.account = User.objects.create(username=username, full_name=doctor.full_name, role='doctor',
                                                 password='!')
            doctor.save(update_fields=['account'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('directory', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DoctorSpecialization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name='doctor_specializations', to='directory.doctor',
                                             verbose_name='Врач')),
                ('specialization', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                                     related_name='doctor_specializations',
                                                     to='directory.specialization', verbose_name='Специализация')),
            ],
            options={
                'verbose_name': 'специализация врача',
                'verbose_name_plural': 'специализации врачей',
                'ordering': ['doctor__account__full_name', 'specialization__name'],
                'constraints': [models.UniqueConstraint(fields=('doctor', 'specialization'),
                                                        name='uniq_doctor_specialization')],
            },
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
