#!/usr/bin/env python
"""
Script para verificar registros recientes en las tablas del módulo Body.
"""
import os
import sys
from datetime import datetime, timezone

import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from body.models import BodyActivity, NutritionLog, SleepLog


def print_section(title):
    """Imprime un separador de sección."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def check_activities():
    """Verifica registros de actividades físicas."""
    print_section("ACTIVIDADES FÍSICAS (body_activities)")
    
    activities = BodyActivity.objects.all().order_by('-created_at')[:5]
    
    if not activities:
        print("❌ No hay actividades registradas")
        return
    
    print(f"✅ Total de actividades: {BodyActivity.objects.count()}")
    print(f"\n📋 Últimas {len(activities)} actividades:\n")
    
    for idx, activity in enumerate(activities, 1):
        print(f"{idx}. ID: {activity.id}")
        print(f"   Usuario: {activity.auth_user_id}")
        print(f"   Tipo: {activity.activity_type} | Intensidad: {activity.intensity}")
        print(f"   Duración: {activity.duration_minutes} min")
        print(f"   Fecha sesión: {activity.session_date}")
        print(f"   Creado: {activity.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        if activity.notes:
            print(f"   Notas: {activity.notes}")
        print()


def check_nutrition():
    """Verifica registros de alimentación."""
    print_section("REGISTROS NUTRICIONALES (body_nutrition_logs)")
    
    nutrition = NutritionLog.objects.all().order_by('-created_at')[:5]
    
    if not nutrition:
        print("❌ No hay registros nutricionales")
        return
    
    print(f"✅ Total de registros: {NutritionLog.objects.count()}")
    print(f"\n📋 Últimos {len(nutrition)} registros:\n")
    
    for idx, log in enumerate(nutrition, 1):
        print(f"{idx}. ID: {log.id}")
        print(f"   Usuario: {log.auth_user_id}")
        print(f"   Comida: {log.meal_name} ({log.meal_type})")
        print(f"   Calorías: {log.calories_kcal} kcal")
        print(f"   Fecha: {log.meal_date}")
        print(f"   Creado: {log.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        if log.notes:
            print(f"   Notas: {log.notes}")
        print()


def check_sleep():
    """Verifica registros de sueño."""
    print_section("REGISTROS DE SUEÑO (body_sleep_logs)")
    
    sleep = SleepLog.objects.all().order_by('-created_at')[:5]
    
    if not sleep:
        print("❌ No hay registros de sueño")
        return
    
    print(f"✅ Total de registros: {SleepLog.objects.count()}")
    print(f"\n📋 Últimos {len(sleep)} registros:\n")
    
    for idx, log in enumerate(sleep, 1):
        print(f"{idx}. ID: {log.id}")
        print(f"   Usuario: {log.auth_user_id}")
        print(f"   Horas dormidas: {log.hours_slept}")
        print(f"   Calidad: {log.sleep_quality}")
        print(f"   Fecha: {log.sleep_date}")
        print(f"   Hora acostarse: {log.bedtime.strftime('%H:%M') if log.bedtime else 'N/A'}")
        print(f"   Hora despertar: {log.wake_time.strftime('%H:%M') if log.wake_time else 'N/A'}")
        print(f"   Creado: {log.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        if log.notes:
            print(f"   Notas: {log.notes}")
        print()


def check_raw_tables():
    """Verifica directamente las tablas con SQL."""
    print_section("VERIFICACIÓN DIRECTA CON SQL")
    
    with connection.cursor() as cursor:
        # Verificar body_activities
        cursor.execute("SELECT COUNT(*) FROM body_activities")
        activities_count = cursor.fetchone()[0]
        print(f"body_activities: {activities_count} registros")
        
        # Verificar body_nutrition_logs
        cursor.execute("SELECT COUNT(*) FROM body_nutrition_logs")
        nutrition_count = cursor.fetchone()[0]
        print(f"body_nutrition_logs: {nutrition_count} registros")
        
        # Verificar body_sleep_logs
        cursor.execute("SELECT COUNT(*) FROM body_sleep_logs")
        sleep_count = cursor.fetchone()[0]
        print(f"body_sleep_logs: {sleep_count} registros")


def main():
    """Función principal."""
    print("\n" + "🔍 VERIFICACIÓN DE REGISTROS - MÓDULO BODY".center(80, "="))
    print(f"Fecha/Hora: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    try:
        check_raw_tables()
        check_activities()
        check_nutrition()
        check_sleep()
        
        print_section("✅ VERIFICACIÓN COMPLETADA")
        
    except Exception as e:
        print(f"\n❌ Error durante la verificación: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

