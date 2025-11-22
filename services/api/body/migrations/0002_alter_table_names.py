# Migration to set correct table names matching Supabase schema

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('body', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='bodyactivity',
            table='body_activities',
        ),
        migrations.AlterModelTable(
            name='nutritionlog',
            table='body_nutrition_logs',
        ),
        migrations.AlterModelTable(
            name='sleeplog',
            table='body_sleep_logs',
        ),
    ]

