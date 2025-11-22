
import os
import django

# Configurar entorno Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from users.models import AppUser
from body.models import NutritionPlan

def run():
    user = AppUser.objects.get(email='gacardona@aura.com')
    print(f"Usuario: {user.full_name}")

    # Obtener todos los planes activos
    plans = NutritionPlan.objects.filter(auth_user_id=user.auth_user_id, is_active=True)
    print(f"Planes activos encontrados: {plans.count()}")

    target_plan_id = "3abe8715-18ac-46b4-996a-288380bb5437" # El que actualicé

    for plan in plans:
        if str(plan.id) == target_plan_id:
            print(f"Plan TARGET ({plan.id}) - MANTENIENDO ACTIVO. Title: {plan.title}")
            # Asegurar titulo correcto
            if "Correcto" not in plan.title:
                plan.title = "Plan de Alimentación - Octubre 2025 (Correcto)"
                plan.save()
        else:
            print(f"Plan {plan.id} ({plan.title}) - DESACTIVANDO")
            plan.is_active = False
            plan.save()

if __name__ == '__main__':
    run()
