"""Удаление записей со статусом «перенесена»: история переносов больше не хранится."""
from django.db import migrations


def forwards(apps, schema_editor):
    Appointment = apps.get_model('appointments', 'Appointment')
    # записи со статусом «перенесена» – это история переносов, действующая запись у пациента уже есть
    Appointment.objects.filter(source__isnull=False).update(source=None)
    Appointment.objects.filter(status='moved').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0003_pending_status_label'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
