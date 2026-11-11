"""Удаление прежней ссылки смены на врача; период недоступности может задаваться в часах внутри дней."""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0002_shift_doctor_specialization'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shift',
            name='doctor_specialization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='shifts',
                                    to='directory.doctorspecialization', verbose_name='Специализация врача'),
        ),
        migrations.RemoveField(model_name='shift', name='doctor'),
        migrations.AddField(
            model_name='unavailabilityperiod',
            name='time_from',
            field=models.TimeField(blank=True, null=True, verbose_name='Время начала'),
        ),
        migrations.AddField(
            model_name='unavailabilityperiod',
            name='time_to',
            field=models.TimeField(blank=True, null=True, verbose_name='Время окончания'),
        ),
        migrations.AddConstraint(
            model_name='unavailabilityperiod',
            constraint=models.CheckConstraint(
                condition=models.Q(models.Q(('time_from__isnull', True), ('time_to__isnull', True)),
                                   models.Q(('time_from__isnull', False), ('time_from__lt', models.F('time_to')),
                                            ('time_to__isnull', False)), _connector='OR'),
                name='period_time_both_or_none'),
        ),
    ]
