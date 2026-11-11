"""Перенос записи меняет слот у той же записи: статус «перенесена» и ссылка на исходную запись удаляются."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0004_delete_moved_appointments'),
    ]

    operations = [
        migrations.RemoveField(model_name='appointment', name='source'),
        migrations.AlterField(
            model_name='appointment',
            name='status',
            field=models.CharField(
                choices=[('pending', 'ожидает кода из SMS'), ('active', 'активна'), ('cancelled', 'отменена')],
                default='active', max_length=10, verbose_name='Статус'),
        ),
    ]
