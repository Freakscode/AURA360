import os
import django
from datetime import date, datetime
from decimal import Decimal

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

    # 2. Medición Corporal (Ya actualizada, no cambiar para evitar re-escritura innecesaria si ya está bien)
    
    # 3. Construir Plan Nutricional Detallado (ADAPTADO AL FRONTEND)
    
    # Listas de Intercambio (Substitutions) - Mantengo estructura, el frontend es 'any[]'
    exchange_lists = [
        {
            "category": "Harinas y Cereales",
            "portion": "1 Porción",
            "items": [
                {"name": "Arroz Blanco", "amount": "90 g"},
                {"name": "Arroz Integral", "amount": "100 g"},
                {"name": "Espaguetis cocidos", "amount": "80 g"},
                {"name": "Pastas", "amount": "30 g"},
                {"name": "Papa común", "amount": "50 g"},
                {"name": "Papa criolla", "amount": "80 g"},
                {"name": "Yuca", "amount": "50 g"},
                {"name": "Plátano", "amount": "60 g"},
                {"name": "Arepa de maíz blanco", "amount": "55 g"},
                {"name": "Maíz amarillo", "amount": "25 g"},
                {"name": "Tortilla de maíz", "amount": "45 g"},
                {"name": "Avena en hojuelas", "amount": "35 g"},
                {"name": "Quinua", "amount": "30 g"},
                {"name": "Pan (Blanco/Integral)", "amount": "30 g"},
                {"name": "Tostada", "amount": "28 g"},
                {"name": "Galletas (Integrales/Soda)", "amount": "25 g"}
            ]
        },
        {
            "category": "Carnes",
            "portion": "1 Porción",
            "items": [
                {"name": "Carne de Res (Magra)", "amount": "150 g"},
                {"name": "Lomo/Cañón de Cerdo", "amount": "150 g"},
                {"name": "Pecha de Pollo", "amount": "150 g"},
                {"name": "Pierna de Cerdo", "amount": "200 g"},
                {"name": "Salmón", "amount": "220 g"},
                {"name": "Camarón", "amount": "210 g"},
                {"name": "Pescado de Mar/Río", "amount": "200 g"}
            ]
        },
        {
            "category": "Quesos y Sustitutos",
            "portion": "1 Porción",
            "items": [
                {"name": "Huevo entero", "amount": "150 g"},
                {"name": "Clara de huevo", "amount": "150 g"},
                {"name": "Cuajada Light", "amount": "120 g"},
                {"name": "Quesito bajo en grasa", "amount": "100 g"},
                {"name": "Mozzarella bajo en grasa", "amount": "70 g"},
                {"name": "Parmesano rallado", "amount": "22 g"}
            ]
        },
        {
            "category": "Grasas",
            "portion": "1 Porción",
            "items": [
                {"name": "Aguacate (Pulpa)", "amount": "60 g"},
                {"name": "Aceite de Canola", "amount": "10 g"},
                {"name": "Mantequilla sin sal", "amount": "10 g"},
                {"name": "Margarina suave", "amount": "10 g"},
                {"name": "Mantequilla de maní", "amount": "10 g"}
            ]
        },
        {
            "category": "Frutas",
            "portion": "1 Porción",
            "items": [
                {"name": "Fresas", "amount": "220 g"},
                {"name": "Sandía", "amount": "200 g"},
                {"name": "Mandarina/Granada", "amount": "150 g"},
                {"name": "Guayaba/Naranja/Piña", "amount": "120 g"},
                {"name": "Kiwi", "amount": "100 g"},
                {"name": "Pera", "amount": "95 g"},
                {"name": "Manzana", "amount": "90 g"},
                {"name": "Mango", "amount": "85 g"},
                {"name": "Banano", "amount": "65 g"}
            ]
        },
        {
            "category": "Nueces y Semillas",
            "portion": "1 Porción",
            "items": [
                {"name": "Marañón/Ajonjolí", "amount": "12 g"},
                {"name": "Almendras/Maní/Girasol", "amount": "10 g"}
            ]
        },
        {
            "category": "Lácteos",
            "portion": "1 Porción",
            "items": [
                {"name": "Leche de vaca", "amount": "250 ml"},
                {"name": "Kumis", "amount": "250 ml"},
                {"name": "Yogur Griego", "amount": "200 g"}
            ]
        }
    ]

    plan_data = {
        "plan": {
            "title": "Plan de Alimentación - Octubre 2025 (Corregido)",
            "version": "2.0",
            "language": "es",
            "issued_at": "2025-10-01",
            "valid_until": "2025-12-01",
            "units": {
                "mass": "kg",
                "volume": "ml",
                "energy": "kcal"
            },
            "source": {
                "kind": "pdf",
                "uri": "analisis_gabriel.pdf",
                "extractor": "gemini-v2-correction"
            }
        },
        "subject": {
            "name": "Gabriel Cardona",
            "demographics": {
                "sex": "M",
                "age_years": 24,
                "weight_kg": 120.3,
                "height_cm": 183
            }
        },
        "assessment": {
            "diagnoses": [
                {"label": "Obesidad Grado II", "severity": "high", "notes": "IMC 36.0"}
            ],
            "goals": [
                {"target": "Grasa Corporal", "value": 30.0, "unit": "%", "notes": "Reducir del 31.5% (37.9kg)"},
                {"target": "Masa Muscular", "value": 42.0, "unit": "kg", "notes": "Recuperar pérdida de 2kg (Actual: 40.1kg)"}
            ]
        },
        "directives": {
            "weekly_frequency": {
                "min_days_per_week": 5,
                "notes": "El plan debe seguirse al menos 5 días. Los otros 2 se permite aumentar una harina."
            },
            "meals": [
                {
                    "name": "Desayuno",
                    "components": [
                        {"group": "Harinas y Cereales", "quantity": {"portions": 1, "notes": "Ver lista"}},
                        {"group": "Lácteo", "quantity": {"portions": 1, "notes": "Semidescremado"}},
                        {"group": "Quesos y Sustitutos", "quantity": {"portions": 4, "notes": "Ver lista"}}
                    ]
                },
                {
                    "name": "Media Mañana",
                    "components": [
                        {"group": "Frutas", "quantity": {"portions": 2, "notes": "Ver lista"}},
                        {"group": "Nueces y Semillas", "quantity": {"portions": 1, "notes": "Solo 2 veces/sem"}}
                    ]
                },
                {
                    "name": "Almuerzo",
                    "components": [
                        {"group": "Carnes", "quantity": {"portions": 2, "notes": "Ver lista"}},
                        {"group": "Harinas y Cereales", "quantity": {"portions": 1, "notes": "Ver lista"}},
                        {"group": "Verduras", "quantity": {"notes": "Libre (min 1/2 plato)"}},
                        {"group": "Grasas", "quantity": {"portions": 1, "notes": "Ver lista"}}
                    ]
                },
                {
                    "name": "Algo (Tarde)",
                    "components": [
                        {"group": "Frutas", "quantity": {"portions": 1, "notes": "Ver lista"}},
                        {"group": "Lácteo", "quantity": {"portions": 1, "notes": "Semidescremado"}}
                    ]
                },
                {
                    "name": "Cena",
                    "components": [
                        {"group": "Harinas y Cereales", "quantity": {"portions": 1, "notes": "Ver lista"}},
                        {"group": "Lácteo", "quantity": {"portions": 1, "notes": "Semidescremado"}},
                        {"group": "Quesos y Sustitutos", "quantity": {"portions": 4, "notes": "Ver lista"}}
                    ],
                    "notes": "Alternativa: Igual al almuerzo"
                }
            ],
            "substitutions": exchange_lists,
            "restrictions": [
                {"target": "Azúcares", "rule": "forbidden", "details": "Totalmente restringidos"},
                {"target": "Cantidades", "rule": "limited", "details": "No aumentar ni disminuir aportes"},
                {"target": "Comida Trampa", "rule": "limited", "details": "1 vez/semana SOLO si se cumple dieta y ejercicio"}
            ]
        },
        "supplements": [
            {"name": "Creatina", "dose": "2 porciones/día", "timing": "Cualquier momento", "notes": "Pure Pharma Grade"}
        ],
        "recommendations": [
            "Hidratación: 8-10 vasos de agua diarios (mínimo 6).",
            "Cocción: Aceite de girasol/soja/canola para calor. Oliva para frío.",
            "Ansiedad: Verduras picadas, gelatina sin azúcar o 1 puñado de nueces.",
            "Productos 0 calorías: Permitidos sin excederse."
        ]
    }

    # Buscar plan activo existente y actualizar
    plan = NutritionPlan.objects.filter(
        auth_user_id=user.auth_user_id, 
        is_active=True,
        title__contains="Octubre 2025"
    ).first()

    if not plan:
        # Si no existe el específico, buscar cualquiera activo
        plan = NutritionPlan.objects.filter(auth_user_id=user.auth_user_id, is_active=True).first()
    
    if not plan:
        print("Error: No se encontró plan activo para actualizar.")
        return

    print(f"Actualizando plan existente: {plan.id}")

    plan.title = "Plan de Alimentación - Octubre 2025 (Correcto)"
    plan.plan_data = plan_data
    plan.save()
    
    print(f"Plan Nutricional guardado correctamente: {plan.id}")

if __name__ == '__main__':
    run()