"""Смена ссылается на специализацию врача: добавление столбца и заполнение его по прежнему врачу смены."""
import django.db.models.deletion
from django.db import migrations, models


def forwards(apps, schema_editor):
    Shift = apps.get_model('schedule', 'Shift')
    DoctorSpecialization = apps.get_model('directory', 'DoctorSpecialization')
    for shift in Shift.objects.all():
        # до изменения у врача была одна специализация – она и становится специализацией смены
        shift.doctor_specialization = DoctorSpecialization.objects.filter(doctor_id=shift.doctor_id).first()
        shift.save(update_fields=['doctor_specialization'])


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0003_doctor_remove_specialization_full_name'),
        ('schedule', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='shift',
            name='doctor_specialization',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='shifts',
                                    to='directory.doctorspecialization', verbose_name='Специализация врача'),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
