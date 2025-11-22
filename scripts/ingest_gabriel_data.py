
import os
import django
from datetime import date, datetime

# Configurar entorno Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from users.models import AppUser
from body.models import BodyMeasurement, NutritionPlan, MeasurementProtocol
from django.utils import timezone

def run():
    # 1. Obtener Usuario
    try:
        user = AppUser.objects.get(email='gacardona@aura.com')
        print(f"Usuario encontrado: {user.full_name} ({user.id})")
    except AppUser.DoesNotExist:
        print("Usuario Gabriel Cardona no encontrado.")
        return

    # 2. Crear Medición Corporal (Octubre 2025)
    # Datos del PDF: IMC 36, Grasa 31.5%, -2kg músculo
    # Estimación para cumplir constraints: Talla 1.75m -> Peso = 36 * (1.75^2) = 110.25 kg
    
    measurement_date = datetime(2025, 10, 1, 10, 0, 0, tzinfo=timezone.get_current_timezone())
    
    # Verificar si ya existe para no duplicar
    if not BodyMeasurement.objects.filter(auth_user_id=user.auth_user_id, recorded_at__year=2025, recorded_at__month=10).exists():
        measurement = BodyMeasurement.objects.create(
            auth_user_id=user.auth_user_id,
            recorded_at=measurement_date,
            protocol=MeasurementProtocol.CLINICAL_BASIC,
            weight_kg=110.25, # Estimado por IMC
            height_cm=175.0,  # Estimado estándar
            bmi=36.0,
            body_fat_percentage=31.5,
            notes="Datos extraídos de valoración nutricional (PDF). IMC 36 kg/m2. Obesidad Grado II. Disminución masa muscular 2kg vs control anterior."
        )
        print(f"Medición creada: {measurement.id}")
    else:
        print("Medición de Octubre 2025 ya existe.")

    # 3. Crear Plan Nutricional
    plan_data = {
        "plan": {
            "title": "Plan de Alimentación - Octubre 2025",
            "language": "es",
            "source": {
                "kind": "pdf",
                "uri": "analisis_gabriel.pdf",
                "extractor": "gemini-pdf-analysis"
            },
            "issued_at": "2025-10-01",
            "valid_until": "2025-12-01"
        },
        "subject": {
            "name": "Gabriel Cardona",
            "age": 24,
            "gender": "male"
        },
        "assessment": {
            "diagnoses": ["Obesidad Grado II"],
            "goals": [
                {"target": "Grasa Corporal", "action": "reduce", "notes": "Reducir del 31.5%"},
                {"target": "Masa Muscular", "action": "increase", "notes": "Recuperar pérdida reciente"}
            ]
        },
        "directives": {
            "meals": [
                {
                    "name": "Desayuno",
                    "components": [
                        {"item": "Harina", "portion_size": "1 porción"},
                        {"item": "Lácteo Semidescremado", "portion_size": "1 porción"},
                        {"item": "Quesos y Sustitutos", "portion_size": "4 porciones"}
                    ]
                },
                {
                    "name": "Media Mañana",
                    "components": [
                        {"item": "Frutas", "portion_size": "2 porciones"},
                        {"item": "Nueces y Semillas", "portion_size": "1 porción (2 veces/sem)"}
                    ]
                },
                {
                    "name": "Almuerzo",
                    "components": [
                        {"item": "Carnes", "portion_size": "2 porciones"},
                        {"item": "Harina", "portion_size": "1 porción"},
                        {"item": "Verduras", "portion_size": "Al gusto (mínimo mitad plato)"},
                        {"item": "Grasa", "portion_size": "1 porción"}
                    ]
                },
                {
                    "name": "Algo (Tarde)",
                    "components": [
                        {"item": "Frutas", "portion_size": "1 porción"},
                        {"item": "Lácteo Semidescremado", "portion_size": "1 porción"}
                    ]
                },
                {
                    "name": "Cena",
                    "components": [
                        {"item": "Harina", "portion_size": "1 porción"},
                        {"item": "Lácteo Semidescremado", "portion_size": "1 porción"},
                        {"item": "Quesos y Sustitutos", "portion_size": "4 porciones"}
                    ],
                    "notes": "Alternativa: Igual al almuerzo"
                }
            ],
            "restrictions": ["Azúcares"],
            "hydration": "8-10 vasos de agua diarios"
        },
        "supplements": [
            {"item": "Creatina", "dosage": "2 porciones/día", "timing": "Cualquier momento"}
        ]
    }

    # Verificar si ya existe plan activo similar
    if not NutritionPlan.objects.filter(auth_user_id=user.auth_user_id, title="Plan de Alimentación - Octubre 2025").exists():
        plan = NutritionPlan.objects.create(
            auth_user_id=user.auth_user_id,
            title="Plan de Alimentación - Octubre 2025",
            language="es",
            issued_at=date(2025, 10, 1),
            valid_until=date(2025, 12, 1),
            is_active=True,
            plan_data=plan_data,
            source_kind="pdf",
            extractor="gemini-script"
        )
        print(f"Plan Nutricional creado: {plan.id}")
    else:
        print("Plan Nutricional ya existe.")

if __name__ == '__main__':
    run()
