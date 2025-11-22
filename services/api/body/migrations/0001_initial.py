import uuid

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='BodyActivity',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Timestamp de creación.')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Timestamp de última actualización.')),
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                    help_text='Identificador único de la sesión de actividad.'
                )),
                ('auth_user_id', models.UUIDField(db_index=True, help_text='ID del usuario en Supabase (auth.users.id).')),
                ('activity_type', models.CharField(max_length=32, choices=[
                    ('cardio', 'Cardio'),
                    ('strength', 'Fuerza'),
                    ('flexibility', 'Flexibilidad'),
                    ('mindfulness', 'Mindfulness'),
                ], help_text='Tipo de actividad realizada.')),
                ('intensity', models.CharField(
                    max_length=16,
                    choices=[
                        ('low', 'Baja'),
                        ('moderate', 'Moderada'),
                        ('high', 'Alta'),
                    ],
                    default='moderate',
                    help_text='Intensidad percibida de la actividad.'
                )),
                ('duration_minutes', models.PositiveIntegerField(help_text='Duración de la sesión en minutos.')),
                ('session_date', models.DateField(default=django.utils.timezone.now, help_text='Fecha en la que se realizó la actividad.')),
                ('notes', models.TextField(blank=True, help_text='Notas opcionales o contexto adicional.', null=True)),
            ],
            options={
                'verbose_name': 'Actividad Física',
                'verbose_name_plural': 'Actividades Físicas',
                'ordering': ['-session_date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='NutritionLog',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Timestamp de creación.')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Timestamp de última actualización.')),
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                    help_text='Identificador del registro nutricional.'
                )),
                ('auth_user_id', models.UUIDField(db_index=True, help_text='ID del usuario en Supabase (auth.users.id).')),
                ('meal_type', models.CharField(
                    max_length=16,
                    choices=[
                        ('breakfast', 'Desayuno'),
                        ('lunch', 'Comida'),
                        ('dinner', 'Cena'),
                        ('snack', 'Snack'),
                    ],
                    help_text='Momento del día al que pertenece la comida.'
                )),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, help_text='Fecha y hora en la que se consumió la comida.')),
                ('items', models.JSONField(blank=True, default=list, help_text='Lista de alimentos incluidos en la comida.')),
                ('calories', models.PositiveIntegerField(blank=True, help_text='Calorías estimadas de la comida.', null=True)),
                ('protein', models.DecimalField(blank=True, decimal_places=2, help_text='Proteínas (g).', max_digits=6, null=True)),
                ('carbs', models.DecimalField(blank=True, decimal_places=2, help_text='Carbohidratos (g).', max_digits=6, null=True)),
                ('fats', models.DecimalField(blank=True, decimal_places=2, help_text='Grasas (g).', max_digits=6, null=True)),
                ('notes', models.TextField(blank=True, help_text='Notas adicionales relacionadas a la comida.', null=True)),
            ],
            options={
                'verbose_name': 'Registro Nutricional',
                'verbose_name_plural': 'Registros Nutricionales',
                'ordering': ['-timestamp', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SleepLog',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Timestamp de creación.')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Timestamp de última actualización.')),
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                    help_text='Identificador del registro de sueño.'
                )),
                ('auth_user_id', models.UUIDField(db_index=True, help_text='ID del usuario en Supabase (auth.users.id).')),
                ('bedtime', models.DateTimeField(help_text='Hora de irse a dormir.')),
                ('wake_time', models.DateTimeField(help_text='Hora de despertar.')),
                ('duration_hours', models.DecimalField(decimal_places=1, help_text='Duración total del sueño en horas.', max_digits=4)),
                ('quality', models.CharField(
                    max_length=16,
                    choices=[
                        ('poor', 'Deficiente'),
                        ('fair', 'Regular'),
                        ('good', 'Buena'),
                        ('excellent', 'Excelente'),
                    ],
                    default='good',
                    help_text='Calidad del sueño reportada.'
                )),
                ('notes', models.TextField(blank=True, help_text='Notas adicionales sobre el sueño.', null=True)),
            ],
            options={
                'verbose_name': 'Registro de Sueño',
                'verbose_name_plural': 'Registros de Sueño',
                'ordering': ['-wake_time', '-created_at'],
            },
        ),
    ]
