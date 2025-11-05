#!/usr/bin/env python
"""
Script de verificación para el módulo Body.

Verifica que las tablas de Supabase están correctamente configuradas
y que Django puede acceder a ellas.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from body.models import BodyActivity, NutritionLog, SleepLog


def check_table_exists(table_name: str) -> bool:
    """Verifica si una tabla existe en la base de datos."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %s
            );
            """,
            [table_name]
        )
        return cursor.fetchone()[0]


def get_table_count(model_class) -> int:
    """Obtiene el conteo de registros de un modelo."""
    try:
        return model_class.objects.count()
    except Exception as e:
        print(f"  ⚠️  Error al contar registros: {e}")
        return -1


def main():
    print("=" * 70)
    print("🔍 VERIFICACIÓN DEL MÓDULO BODY")
    print("=" * 70)
    print()

    # Verificar tablas
    print("📊 Verificando existencia de tablas en Supabase...")
    print()

    tables = {
        'body_activities': BodyActivity,
        'body_nutrition_logs': NutritionLog,
        'body_sleep_logs': SleepLog,
    }

    all_exist = True

    for table_name, model_class in tables.items():
        exists = check_table_exists(table_name)
        status = "✅" if exists else "❌"
        print(f"  {status} {table_name}: {'Existe' if exists else 'NO EXISTE'}")

        if exists:
            count = get_table_count(model_class)
            if count >= 0:
                print(f"     └─ {count} registros encontrados")
        else:
            all_exist = False

    print()

    # Verificar políticas RLS
    print("🔒 Verificando políticas RLS...")
    print()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                tablename,
                policyname
            FROM pg_policies
            WHERE schemaname = 'public'
              AND tablename IN ('body_activities', 'body_nutrition_logs', 'body_sleep_logs')
            ORDER BY tablename, policyname;
            """
        )
        policies = cursor.fetchall()

        if policies:
            current_table = None
            for table, policy in policies:
                if table != current_table:
                    print(f"  📋 {table}:")
                    current_table = table
                print(f"     ├─ {policy}")
        else:
            print("  ⚠️  No se encontraron políticas RLS")

    print()

    # Verificar índices
    print("🔍 Verificando índices...")
    print()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                tablename,
                indexname
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename IN ('body_activities', 'body_nutrition_logs', 'body_sleep_logs')
              AND indexname NOT LIKE '%_pkey'
            ORDER BY tablename, indexname;
            """
        )
        indexes = cursor.fetchall()

        if indexes:
            current_table = None
            for table, index in indexes:
                if table != current_table:
                    print(f"  📊 {table}:")
                    current_table = table
                print(f"     ├─ {index}")
        else:
            print("  ⚠️  No se encontraron índices personalizados")

    print()
    print("=" * 70)

    if all_exist:
        print("✅ VERIFICACIÓN EXITOSA")
        print()
        print("El módulo Body está correctamente configurado.")
        print("Puedes proceder a:")
        print("  1. Iniciar el servidor: uv run python manage.py runserver")
        print("  2. Ejecutar tests: uv run python manage.py test body")
        print("  3. Conectar desde la app mobile configurando BASE_URL en env/local.env")
    else:
        print("❌ VERIFICACIÓN FALLIDA")
        print()
        print("Algunas tablas no existen. Asegúrate de:")
        print("  1. Haber aplicado las migraciones de Supabase:")
        print("     cd aura_mobile && supabase db push --local")
        print("  2. Verificar la configuración de DATABASE_URL en backend/.env")

    print("=" * 70)


if __name__ == '__main__':
    main()

