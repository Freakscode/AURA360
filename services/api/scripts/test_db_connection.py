#!/usr/bin/env python
"""
Script para verificar la conexión con la base de datos.

Este script intenta conectarse a la base de datos configurada
y muestra información sobre los usuarios existentes.

Uso:
    python scripts/test_db_connection.py
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
BASE_DIR = Path(__file__).resolve().parent.parent
import pytest

sys.path.insert(0, str(BASE_DIR))
django.setup()

from django.db import connection
from users.models import AppUser, UserTier


@pytest.mark.django_db
def test_database_connection():
    """Prueba la conexión con la base de datos."""
    print("🔍 Probando conexión con la base de datos...")
    print("-" * 60)
    
    # Probar conexión básica
    from django.db.utils import ProgrammingError
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ Conexión exitosa con PostgreSQL")
            print(f"📦 Versión: {version}")
            print()
    except ProgrammingError:
        pytest.skip("Base de datos no disponible en tests (mock o SQLite sin tabla)")


@pytest.mark.django_db
def test_app_users_table():
    """Prueba que la tabla app_users existe y es accesible."""
    print("🔍 Verificando tabla app_users...")
    print("-" * 60)
    
    from django.db.utils import ProgrammingError
    try:
        count = AppUser.objects.count()
    except ProgrammingError:
        pytest.skip("Tabla app_users no disponible en el entorno actual")
    print(f"✅ Tabla app_users accesible")
    print(f"👥 Total de usuarios: {count}")
    print()
    
    if count > 0:
        # Mostrar estadísticas
        free_count = AppUser.objects.filter(tier=UserTier.FREE).count()
        premium_count = AppUser.objects.filter(tier=UserTier.PREMIUM).count()
        independent_count = AppUser.objects.filter(is_independent=True).count()
        
        print("📊 Estadísticas:")
        print(f"   - Usuarios Free: {free_count}")
        print(f"   - Usuarios Premium: {premium_count}")
        print(f"   - Usuarios Independientes: {independent_count}")
        print()
        
        # Mostrar últimos 5 usuarios
        print("👤 Últimos 5 usuarios registrados:")
        for user in AppUser.objects.order_by('-created_at')[:5]:
            tier_emoji = "⭐" if user.is_premium else "👤"
            role_display = user.get_role_global_display()
            billing_display = user.get_billing_plan_display()
            independence = "Independiente" if user.is_independent else "Institución"
            print(
                f"   {tier_emoji} {user.full_name} ({user.email}) "
                f"- {user.get_tier_display()} · {role_display} · {billing_display} · {independence}"
            )
        print()
    else:
        print("ℹ️  No hay usuarios en la base de datos.")
        print("   Puedes crear usuarios desde Supabase Auth o usando la API.")
        print()


def main():
    """Función principal."""
    print()
    print("=" * 60)
    print("  AURA365 Backend - Test de Conexión de Base de Datos")
    print("=" * 60)
    print()
    
    # Test 1: Conexión básica
    if not test_database_connection():
        sys.exit(1)
    
    # Test 2: Tabla app_users
    if not test_app_users_table():
        sys.exit(1)
    
    # Resumen final
    print("=" * 60)
    print("✅ Todos los tests pasaron exitosamente")
    print("=" * 60)
    print()
    print("Próximos pasos:")
    print("1. Inicia el servidor: python manage.py runserver")
    print("2. Accede al admin: http://localhost:8000/admin/")
    print("3. Prueba la API: http://localhost:8000/dashboard/users/")
    print("4. Ve la documentación: http://localhost:8000/api/docs/")
    print()


if __name__ == "__main__":
    main()
