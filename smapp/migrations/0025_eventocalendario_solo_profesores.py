# Generated by Django 4.2.7 on 2025-06-29 18:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smapp', '0024_alter_asistenciaalumno_fecha_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventocalendario',
            name='solo_profesores',
            field=models.BooleanField(default=False, verbose_name='Solo para profesores'),
        ),
    ]
