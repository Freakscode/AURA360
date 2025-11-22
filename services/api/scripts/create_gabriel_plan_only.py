#!/usr/bin/env python
"""
Script simplificado para crear solo el plan nutricional de Gabriel.
Asume que el usuario ya fue creado.

Uso:
    uv run python scripts/create_gabriel_plan_only.py
"""

import os
import sys
import django
from datetime import date, datetime

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from body.models import NutritionPlan


# UUID del usuario Gabriel Cardona
GABRIEL_USER_ID = "49826733-1d96-4c2f-b122-18831bcc503e"


def create_gabriel_nutrition_plan():
    """Crea el plan nutricional para Gabriel Cardona."""
    
    print("=" * 60)
    print("🚀 Creando plan nutricional para Gabriel Cardona")
    print("=" * 60)
    print(f"Usuario ID: {GABRIEL_USER_ID}")
    print()
    
    # Datos del plan transformados al esquema
    plan_data = {
        "plan": {
            "title": "Plan Nutricional - GABRIEL CARDONA",
            "version": "1.0",
            "issued_at": "2025-10-22",
            "valid_until": "2026-04-22",
            "language": "es",
            "units": {
                "mass": "kg",
                "volume": "ml",
                "energy": "kcal"
            },
            "source": {
                "kind": "text",
                "uri": None,
                "extracted_at": datetime.now().isoformat(),
                "extractor": "manual_script_v1"
            }
        },
        "subject": {
            "user_id": GABRIEL_USER_ID,
            "name": "GABRIEL CARDONA",
            "demographics": {
                "sex": "Masculino",
                "age_years": 24,
                "height_cm": None,
                "weight_kg": None
            }
        },
        "assessment": {
            "timeseries": [
                {
                    "date": "2025-08-08",
                    "metrics": {
                        "fat_percent": 30.6,
                        "muscle_mass_kg": 38.1,
                        "bone_mass_kg": 13.3,
                        "residual_mass_kg": 27.4
                    },
                    "method_notes": "Evaluación por bioimpedancia"
                },
                {
                    "date": "2025-10-22",
                    "metrics": {
                        "fat_percent": 31.5,
                        "muscle_mass_kg": 40.1,
                        "bone_mass_kg": 13.3,
                        "residual_mass_kg": 29.0
                    },
                    "method_notes": "Evaluación por bioimpedancia"
                }
            ],
            "diagnoses": [
                {
                    "label": "Obesidad Grado II",
                    "severity": "alto",
                    "notes": "Paciente masculino de 24 años con diagnóstico de Obesidad Grado II (IMC 36 kg/m²). Presenta un porcentaje de grasa actual del 31.5%, lo que representa un aumento del 1.5% respecto a la valoración anterior. Se observa una disminución en la masa muscular de 2 kg."
                }
            ],
            "goals": [
                {
                    "target": "reduccion_grasa_corporal",
                    "value": 25,
                    "unit": "%",
                    "due_date": "2026-04-22"
                },
                {
                    "target": "imc",
                    "value": 30,
                    "unit": "kg/m²",
                    "due_date": "2026-04-22"
                }
            ]
        },
        "directives": {
            "weekly_frequency": {
                "min_days_per_week": 5,
                "notes": "El plan debe consumirse al menos 5 veces por semana. Los 2 días restantes, aumentar una porción de harina."
            },
            "conditional_allowances": [
                {
                    "name": "comida_trampa",
                    "allowed": True,
                    "frequency": "1 por semana",
                    "conditions": "Si se cumple con el plan de alimentación y la actividad física"
                }
            ],
            "restrictions": [
                {
                    "target": "azúcares",
                    "rule": "forbidden",
                    "details": "Los azúcares no están permitidos en el consumo diario"
                }
            ],
            "meals": [
                {
                    "name": "Desayuno",
                    "time_window": "7:00-9:00",
                    "components": [
                        {
                            "group": "Harinas",
                            "quantity": {"portions": 1},
                            "must_present": True
                        },
                        {
                            "group": "Lácteo Semidescremado",
                            "quantity": {"portions": 1},
                            "must_present": True
                        },
                        {
                            "group": "Quesos y Sustitutos",
                            "quantity": {"portions": 4},
                            "must_present": True
                        }
                    ],
                    "notes": "Primera comida del día"
                },
                {
                    "name": "Media Mañana",
                    "time_window": "10:00-11:00",
                    "components": [
                        {
                            "group": "Frutas",
                            "quantity": {"portions": 2},
                            "must_present": True
                        },
                        {
                            "group": "Nueces y Semillas",
                            "quantity": {"portions": 1, "notes": "Únicamente 2 veces por semana"},
                            "must_present": False
                        }
                    ],
                    "notes": "Snack de media mañana"
                },
                {
                    "name": "Almuerzo",
                    "time_window": "12:00-14:00",
                    "components": [
                        {
                            "group": "Carnes",
                            "quantity": {"portions": 2},
                            "must_present": True
                        },
                        {
                            "group": "Harina",
                            "quantity": {"portions": 1},
                            "must_present": True
                        },
                        {
                            "group": "Verduras",
                            "quantity": {"value": 2, "unit": "tazas"},
                            "must_present": True
                        },
                        {
                            "group": "Grasa",
                            "quantity": {"portions": 1},
                            "must_present": True
                        }
                    ],
                    "notes": "Comida principal. Las verduras deben ocupar mínimo la mitad del plato."
                },
                {
                    "name": "Media Tarde",
                    "time_window": "16:00-17:00",
                    "components": [
                        {
                            "group": "Frutas",
                            "quantity": {"portions": 1},
                            "must_present": True
                        },
                        {
                            "group": "Lácteo Semidescremado",
                            "quantity": {"portions": 1},
                            "must_present": True
                        }
                    ],
                    "notes": "Snack de media tarde"
                },
                {
                    "name": "Cena",
                    "time_window": "19:00-21:00",
                    "components": [
                        {
                            "group": "Harinas",
                            "quantity": {"portions": 1},
                            "must_present": True
                        },
                        {
                            "group": "Lácteo Semidescremado",
                            "quantity": {"portions": 1},
                            "must_present": True
                        },
                        {
                            "group": "Quesos y Sustitutos",
                            "quantity": {"portions": 4},
                            "must_present": True
                        }
                    ],
                    "notes": "Última comida del día"
                }
            ],
            "substitutions": [
                {
                    "group": "Harinas",
                    "items": [
                        {"name": "ARROZ BLANCO", "grams": 90, "portion_equiv": 1},
                        {"name": "PAPA COMÚN", "grams": 50, "portion_equiv": 1},
                        {"name": "AVENA EN HOJUELAS", "grams": 35, "portion_equiv": 1},
                        {"name": "PLATANO", "grams": 60, "portion_equiv": 1}
                    ]
                },
                {
                    "group": "Carnes",
                    "items": [
                        {"name": "CARNE DE RES MAGRA", "grams": 150, "portion_equiv": 1},
                        {"name": "PECHUGA DE POLLO", "grams": 150, "portion_equiv": 1},
                        {"name": "SALMON", "grams": 220, "portion_equiv": 1},
                        {"name": "PESCADO DE MAR", "grams": 200, "portion_equiv": 1}
                    ]
                },
                {
                    "group": "Grasa",
                    "items": [
                        {"name": "AGUACATE PULPA", "grams": 60, "portion_equiv": 1},
                        {"name": "MANTEQUILLA SIN SAL", "grams": 10, "portion_equiv": 1},
                        {"name": "ACEITE DE CANOLA", "grams": 10, "portion_equiv": 1}
                    ]
                },
                {
                    "group": "Quesos y Sustitutos",
                    "items": [
                        {"name": "HUEVO DE GALLINA ENTERO", "grams": 150, "portion_equiv": 1},
                        {"name": "CUAJADA LIGHT", "grams": 120, "portion_equiv": 1},
                        {"name": "MOZZARELLA BAJO EN GRASA", "grams": 70, "portion_equiv": 1}
                    ]
                },
                {
                    "group": "Frutas",
                    "items": [
                        {"name": "FRESAS", "grams": 220, "portion_equiv": 1},
                        {"name": "BANANO COMÚN", "grams": 65, "portion_equiv": 1},
                        {"name": "MANZANA", "grams": 90, "portion_equiv": 1},
                        {"name": "SANDIA", "grams": 200, "portion_equiv": 1}
                    ]
                },
                {
                    "group": "Nueces y Semillas",
                    "items": [
                        {"name": "ALMENDRAS", "grams": 10, "portion_equiv": 1},
                        {"name": "MANÍ CON SAL", "grams": 10, "portion_equiv": 1},
                        {"name": "MARAÑON", "grams": 12, "portion_equiv": 1}
                    ]
                },
                {
                    "group": "Lácteo Semidescremado",
                    "items": [
                        {"name": "LECHE DE VACA DESCREMADA", "grams": 250, "portion_equiv": 1},
                        {"name": "YOGUR GRIEGO PROMEDIO", "grams": 200, "portion_equiv": 1},
                        {"name": "KUMIS", "grams": 250, "portion_equiv": 1}
                    ]
                }
            ]
        },
        "supplements": [
            {
                "name": "Creatina",
                "dose": "2 porciones en el día",
                "timing": None,
                "notes": "Puedes consumirla en cualquier momento."
            }
        ],
        "recommendations": [
            "Para cocinar, preferir aceite de girasol, soja o canola; para preparaciones en frío, usar aceite de oliva.",
            "Las verduras no tienen restricción de cantidad.",
            "Para controlar la ansiedad: verduras picadas, gelatina sin azúcar o 1 porción de nueces.",
            "Mantener un consumo de agua de 8-10 vasos diarios (mínimo 6).",
            "Realizar actividad física según las indicaciones."
        ],
        "activity_guidance": "Realizar actividad física según las indicaciones del nutricionista.",
        "free_text": {
            "diagnosis_raw": "Paciente masculino de 24 años con diagnóstico de Obesidad Grado II (IMC 36 kg/m²). Presenta un porcentaje de grasa actual del 31.5%, lo que representa un aumento del 1.5% respecto a la valoración anterior. Se observa una disminución en la masa muscular de 2 kg.",
            "instructions_raw": "El plan debe consumirse al menos 5 veces por semana.\nLos 2 días restantes de la semana, se debe aumentar una porción de harina durante el día.\nLos azúcares no están permitidos en el consumo diario.\nSe permite una 'comida trampa' si se cumple con el plan de alimentación y la actividad física.",
            "notes_raw": "Nutricionista: Angie Martinez\nInstagram: @angiem_nutricionista"
        }
    }
    
    # Crear instancia del modelo
    try:
        nutrition_plan = NutritionPlan(
            auth_user_id=GABRIEL_USER_ID,
            title=plan_data["plan"]["title"],
            language=plan_data["plan"]["language"],
            issued_at=date.fromisoformat(plan_data["plan"]["issued_at"]),
            valid_until=date.fromisoformat(plan_data["plan"]["valid_until"]),
            is_active=True,
            plan_data=plan_data,
            source_kind=plan_data["plan"]["source"]["kind"],
            source_uri=plan_data["plan"]["source"]["uri"],
            extracted_at=datetime.fromisoformat(plan_data["plan"]["source"]["extracted_at"]),
            extractor=plan_data["plan"]["source"]["extractor"]
        )
        
        nutrition_plan.save()
        
        print("✅ Plan nutricional creado exitosamente!")
        print()
        print(f"📋 Plan ID: {nutrition_plan.id}")
        print(f"   - Título: {nutrition_plan.title}")
        print(f"   - Comidas: {len(nutrition_plan.get_meals())}")
        print(f"   - Grupos de sustitución: {len(nutrition_plan.get_substitutions())}")
        print(f"   - Suplementos: {len(nutrition_plan.get_supplements())}")
        print(f"   - Vigente hasta: {nutrition_plan.valid_until}")
        print()
        print("🔍 Puedes verificar el plan con:")
        print(f"   GET /dashboard/body/nutrition-plans/{nutrition_plan.id}/")
        print()
        print("=" * 60)
        
        return nutrition_plan
        
    except Exception as e:
        print(f"❌ Error al crear plan: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    create_gabriel_nutrition_plan()

