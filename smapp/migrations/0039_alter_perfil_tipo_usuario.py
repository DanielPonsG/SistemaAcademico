# Generated by Django 4.2.7 on 2025-07-06 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smapp', '0038_relacionapoderadoestudiante_alter_apoderado_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='perfil',
            name='tipo_usuario',
            field=models.CharField(choices=[('director', 'Director'), ('profesor', 'Profesor'), ('alumno', 'Alumno')], max_length=10),
        ),
    ]
