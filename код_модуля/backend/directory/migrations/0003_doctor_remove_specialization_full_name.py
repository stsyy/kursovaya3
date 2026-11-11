"""Удаление столбцов specialization и full_name из таблицы врачей (данные перенесены миграцией 0002)."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('directory', '0002_doctor_specializations'),
    ]

    operations = [
        migrations.RemoveField(model_name='doctor', name='specialization'),
        migrations.RemoveField(model_name='doctor', name='full_name'),
        migrations.AlterField(
            model_name='doctor',
            name='account',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='doctor',
                                       to=settings.AUTH_USER_MODEL, verbose_name='Учётная запись'),
        ),
        migrations.AddField(
            model_name='doctor',
            name='specializations',
            field=models.ManyToManyField(related_name='doctors', through='directory.DoctorSpecialization',
                                         to='directory.specialization', verbose_name='Специализации'),
        ),
        migrations.AlterModelOptions(
            name='doctor',
            options={'ordering': ['account__full_name'], 'verbose_name': 'врач', 'verbose_name_plural': 'врачи'},
        ),
    ]
