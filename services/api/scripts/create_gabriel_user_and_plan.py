#!/usr/bin/env python
"""
Script para crear el usuario Gabriel Cardona y su plan nutricional.

Este script:
1. Crea el usuario en Supabase Auth
2. Transforma el plan nutricional proporcionado al esquema implementado
3. Crea el plan en la base de datos

Uso:
    uv run python scripts/create_gabriel_user_and_plan.py
"""

import os
import sys
import django
from datetime import date, datetime

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.services.supabase_admin import get_supabase_admin_client
from body.models import NutritionPlan


def create_user():
    """Crea el usuario Gabriel Cardona en Supabase Auth."""
    print("🔹 Creando usuario Gabriel Cardona...")
    
    admin_client = get_supabase_admin_client()
    
    user_data = {
        "email": "gacardona@aura.com",
        "password": "Aura123!",
        "email_confirm": True,
        "user_metadata": {
            "full_name": "GABRIEL CARDONA",
            "age": 24,
            "gender": "Masculino",
        }
    }
    
    try:
        result = admin_client.create_user(**user_data)
        user_id = result.get('id')
        print(f"✅ Usuario creado exitosamente. ID: {user_id}")
        return user_id
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error al crear usuario: {error_msg}")
        
        # Si el usuario ya existe, pedimos el UUID manualmente
        if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
            print("⚠️  El usuario ya existe en Supabase.")
        
        print("🔹 Por favor, proporciona el UUID del usuario manualmente")
        print("   (Puedes obtenerlo desde Supabase Dashboard → Authentication → Users)")
        return None


def transform_to_schema(gabriel_plan_data, user_id):
    """
    Transforma el plan de Gabriel al esquema implementado.
    
    Args:
        gabriel_plan_data: Diccionario con el plan en formato original
        user_id: UUID del usuario en Supabase
    
    Returns:
        Diccionario con el plan en el formato del esquema implementado
    """
    print("🔹 Transformando plan al esquema implementado...")
    
    nutrition_plan = gabriel_plan_data.get("nutritionPlan", {})
    
    # Construir el plan según nuestro esquema
    plan_data = {
        "plan": {
            "title": f"Plan Nutricional - {nutrition_plan['patientInfo']['name']}",
            "version": "1.0",
            "issued_at": "2025-10-22",
            "valid_until": "2026-04-22",  # 6 meses de vigencia
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
            "user_id": user_id,
            "name": nutrition_plan["patientInfo"]["name"],
            "demographics": {
                "sex": nutrition_plan["anthropometricAssessment"]["diagnosis"]["details"]["gender"],
                "age_years": nutrition_plan["anthropometricAssessment"]["diagnosis"]["details"]["age"],
                "height_cm": None,  # No proporcionado
                "weight_kg": None   # Calculable desde IMC si tuviéramos altura
            }
        },
        "assessment": {
            "timeseries": [],
            "diagnoses": [
                {
                    "label": nutrition_plan["anthropometricAssessment"]["diagnosis"]["details"]["bmiClassification"],
                    "severity": "alto",
                    "notes": nutrition_plan["anthropometricAssessment"]["diagnosis"]["summary"]
                }
            ],
            "goals": [
                {
                    "target": "reduccion_grasa_corporal",
                    "value": 25,  # Objetivo estimado
                    "unit": "%",
                    "due_date": "2026-04-22"
                },
                {
                    "target": "imc",
                    "value": 30,  # Bajar de obesidad grado II a grado I
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
            "meals": [],
            "substitutions": []
        },
        "supplements": [],
        "recommendations": nutrition_plan.get("generalRecommendations", []),
        "activity_guidance": "Realizar actividad física según las indicaciones del nutricionista.",
        "free_text": {
            "diagnosis_raw": nutrition_plan["anthropometricAssessment"]["diagnosis"]["summary"],
            "instructions_raw": "\n".join(nutrition_plan["mealPlan"]["generalInstructions"]),
            "notes_raw": f"Nutricionista: {nutrition_plan['nutritionistInfo']['name']}\nInstagram: {nutrition_plan['nutritionistInfo']['socialMedia']['instagram']}"
        }
    }
    
    # Agregar series temporales de composición corporal
    for entry in nutrition_plan["anthropometricAssessment"]["bodyCompositionHistory"]:
        plan_data["assessment"]["timeseries"].append({
            "date": entry["date"],
            "metrics": {
                "fat_percent": entry["bodyFatPercentage"],
                "muscle_mass_kg": entry["muscleMassKg"],
                "bone_mass_kg": entry["boneMassKg"],
                "residual_mass_kg": entry["residualMassKg"]
            },
            "method_notes": "Evaluación por bioimpedancia"
        })
    
    # Transformar estructura de comidas
    meal_structure = nutrition_plan["mealPlan"]["dailyMealStructure"]
    
    # Desayuno
    plan_data["directives"]["meals"].append({
        "name": "Desayuno",
        "time_window": "7:00-9:00",
        "components": [
            {
                "group": comp["group"],
                "quantity": {
                    "portions": comp["portions"] if isinstance(comp.get("portions"), (int, float)) else 0,
                    "notes": comp.get("notes")
                },
                "must_present": True
            }
            for comp in meal_structure["breakfast"]
        ],
        "notes": "Primera comida del día"
    })
    
    # Media mañana
    plan_data["directives"]["meals"].append({
        "name": "Media Mañana",
        "time_window": "10:00-11:00",
        "components": [
            {
                "group": comp["group"],
                "quantity": {
                    "portions": comp["portions"] if isinstance(comp.get("portions"), (int, float)) else 0,
                    "notes": comp.get("notes")
                },
                "must_present": comp["group"] == "Frutas"
            }
            for comp in meal_structure["midMorningSnack"]
        ],
        "notes": "Snack de media mañana"
    })
    
    # Almuerzo
    lunch_components = []
    for comp in meal_structure["lunch"]:
        portions = comp.get("portions")
        if isinstance(portions, str):
            # Caso especial para verduras
            lunch_components.append({
                "group": comp["group"],
                "quantity": {
                    "value": 2,
                    "unit": "tazas"
                },
                "must_present": True
            })
        else:
            lunch_components.append({
                "group": comp["group"],
                "quantity": {
                    "portions": portions,
                    "notes": comp.get("notes")
                },
                "must_present": True
            })
    
    plan_data["directives"]["meals"].append({
        "name": "Almuerzo",
        "time_window": "12:00-14:00",
        "components": lunch_components,
        "notes": "Comida principal. Las verduras deben ocupar mínimo la mitad del plato."
    })
    
    # Media tarde
    plan_data["directives"]["meals"].append({
        "name": "Media Tarde",
        "time_window": "16:00-17:00",
        "components": [
            {
                "group": comp["group"],
                "quantity": {
                    "portions": comp["portions"] if isinstance(comp.get("portions"), (int, float)) else 0
                },
                "must_present": True
            }
            for comp in meal_structure["afternoonSnack"]
        ],
        "notes": "Snack de media tarde"
    })
    
    # Cena
    plan_data["directives"]["meals"].append({
        "name": "Cena",
        "time_window": "19:00-21:00",
        "components": [
            {
                "group": comp["group"],
                "quantity": {
                    "portions": comp["portions"] if isinstance(comp.get("portions"), (int, float)) else 0,
                    "notes": comp.get("notes")
                },
                "must_present": True
            }
            for comp in meal_structure["dinner"]
        ],
        "notes": "Última comida del día"
    })
    
    # Transformar listas de intercambio
    exchange_list = nutrition_plan["mealPlan"]["foodExchangeList"]
    
    # Mapeo de nombres
    group_mapping = {
        "harinasYCereales": "Harinas",
        "carnes": "Carnes",
        "grasas": "Grasa",
        "quesosYSustitutos": "Quesos y Sustitutos",
        "frutas": "Frutas",
        "nuecesYSemillas": "Nueces y Semillas",
        "lacteos": "Lácteo Semidescremado"
    }
    
    for key, group_name in group_mapping.items():
        if key in exchange_list:
            items = []
            for item in exchange_list[key]:
                items.append({
                    "name": item["food"],
                    "grams": item["grams"],
                    "portion_equiv": 1,
                    "notes": None
                })
            
            plan_data["directives"]["substitutions"].append({
                "group": group_name,
                "items": items
            })
    
    # Agregar suplementos
    for supp in nutrition_plan.get("supplementRecommendations", []):
        plan_data["supplements"].append({
            "name": supp["supplement"],
            "dose": supp["dosage"],
            "timing": None,
            "notes": supp["instructions"]
        })
    
    print("✅ Plan transformado exitosamente")
    return plan_data


def create_nutrition_plan(user_id, gabriel_plan_data):
    """
    Crea el plan nutricional en la base de datos.
    
    Args:
        user_id: UUID del usuario
        gabriel_plan_data: Datos del plan en formato original
    """
    print("🔹 Creando plan nutricional en base de datos...")
    
    # Transformar plan
    plan_data = transform_to_schema(gabriel_plan_data, user_id)
    
    # Crear instancia del modelo
    nutrition_plan = NutritionPlan(
        auth_user_id=user_id,
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
    
    # Guardar en base de datos
    nutrition_plan.save()
    
    print(f"✅ Plan nutricional creado exitosamente. ID: {nutrition_plan.id}")
    print(f"   - Título: {nutrition_plan.title}")
    print(f"   - Comidas: {len(nutrition_plan.get_meals())}")
    print(f"   - Grupos de sustitución: {len(nutrition_plan.get_substitutions())}")
    print(f"   - Suplementos: {len(nutrition_plan.get_supplements())}")
    
    return nutrition_plan


def main():
    """Función principal."""
    print("=" * 60)
    print("🚀 Creando usuario Gabriel Cardona y su plan nutricional")
    print("=" * 60)
    
    # Datos del plan de Gabriel
    gabriel_plan_data = {
        "nutritionPlan": {
            "patientInfo": {
                "name": "GABRIEL CARDONA"
            },
            "nutritionistInfo": {
                "name": "Angie Martinez",
                "socialMedia": {
                    "instagram": "@angiem_nutricionista"
                }
            },
            "anthropometricAssessment": {
                "assessmentDate": "2025-10-22",
                "diagnosis": {
                    "summary": "Paciente masculino de 24 años con diagnóstico de Obesidad Grado II (IMC 36 kg/m²). Presenta un porcentaje de grasa actual del 31.5%, lo que representa un aumento del 1.5% respecto a la valoración anterior. Se observa una disminución en la masa muscular de 2 kg.",
                    "details": {
                        "age": 24,
                        "gender": "Masculino",
                        "bmi": 36,
                        "bmiClassification": "Obesidad Grado II",
                        "bodyFatPercentage": 31.5
                    }
                },
                "bodyCompositionHistory": [
                    {
                        "date": "2025-08-08",
                        "bodyFatPercentage": 30.6,
                        "fatMassKg": 34.8,
                        "muscleMassKg": 38.1,
                        "boneMassKg": 13.3,
                        "residualMassKg": 27.4
                    },
                    {
                        "date": "2025-10-22",
                        "bodyFatPercentage": 31.5,
                        "fatMassKg": 37.9,
                        "muscleMassKg": 40.1,
                        "boneMassKg": 13.3,
                        "residualMassKg": 29.0
                    }
                ],
                "skinfoldHistory": [
                    {"date": "2023-07-25", "sum_mm": 204},
                    {"date": "2023-09-19", "sum_mm": 185},
                    {"date": "2023-12-04", "sum_mm": 238},
                    {"date": "2024-02-10", "sum_mm": 215},
                    {"date": "2024-04-26", "sum_mm": 185},
                    {"date": "2024-07-25", "sum_mm": 167},
                    {"date": "2024-12-14", "sum_mm": 210},
                    {"date": "2025-05-25", "sum_mm": 241},
                    {"date": "2025-08-08", "sum_mm": 253},
                    {"date": "2025-10-22", "sum_mm": 276}
                ]
            },
            "mealPlan": {
                "generalInstructions": [
                    "El plan debe consumirse al menos 5 veces por semana.",
                    "Los 2 días restantes de la semana, se debe aumentar una porción de harina durante el día.",
                    "Los azúcares no están permitidos en el consumo diario.",
                    "Se permite una 'comida trampa' si se cumple con el plan de alimentación y la actividad física."
                ],
                "dailyMealStructure": {
                    "breakfast": [
                        {"group": "Harinas", "portions": 1},
                        {"group": "Lácteo Semidescremado", "portions": 1},
                        {"group": "Quesos y Sustitutos", "portions": 4}
                    ],
                    "lunch": [
                        {"group": "Carnes", "portions": 2},
                        {"group": "Harina", "portions": 1},
                        {"group": "Verduras", "portions": "A preferencia (mínimo la mitad del plato)"},
                        {"group": "Grasa", "portions": 1}
                    ],
                    "dinner": [
                        {"group": "Harinas", "portions": 1},
                        {"group": "Lácteo Semidescremado", "portions": 1},
                        {"group": "Quesos y Sustitutos", "portions": 4}
                    ],
                    "midMorningSnack": [
                        {"group": "Frutas", "portions": 2},
                        {"group": "Nueces y Semillas", "portions": 1, "notes": "Únicamente 2 veces por semana"}
                    ],
                    "afternoonSnack": [
                        {"group": "Frutas", "portions": 1},
                        {"group": "Lácteo Semidescremado", "portions": 1}
                    ]
                },
                "foodExchangeList": {
                    "harinasYCereales": [
                        {"food": "ARROZ BLANCO", "grams": 90},
                        {"food": "PAPA COMÚN", "grams": 50},
                        {"food": "AVENA EN HOJUELAS", "grams": 35},
                        {"food": "PLATANO", "grams": 60}
                    ],
                    "carnes": [
                        {"food": "CARNE DE RES MAGRA", "grams": 150},
                        {"food": "PECHUGA DE POLLO", "grams": 150},
                        {"food": "SALMON", "grams": 220},
                        {"food": "PESCADO DE MAR", "grams": 200}
                    ],
                    "grasas": [
                        {"food": "AGUACATE PULPA", "grams": 60},
                        {"food": "MANTEQUILLA SIN SAL", "grams": 10},
                        {"food": "ACEITE DE CANOLA", "grams": 10}
                    ],
                    "quesosYSustitutos": [
                        {"food": "HUEVO DE GALLINA ENTERO", "grams": 150},
                        {"food": "CUAJADA LIGHT", "grams": 120},
                        {"food": "MOZZARELLA BAJO EN GRASA", "grams": 70}
                    ],
                    "frutas": [
                        {"food": "FRESAS", "grams": 220},
                        {"food": "BANANO COMÚN", "grams": 65},
                        {"food": "MANZANA", "grams": 90},
                        {"food": "SANDIA", "grams": 200}
                    ],
                    "nuecesYSemillas": [
                        {"food": "ALMENDRAS", "grams": 10},
                        {"food": "MANÍ CON SAL", "grams": 10},
                        {"food": "MARAÑON", "grams": 12}
                    ],
                    "lacteos": [
                        {"food": "LECHE DE VACA DESCREMADA", "grams": 250},
                        {"food": "YOGUR GRIEGO PROMEDIO", "grams": 200},
                        {"food": "KUMIS", "grams": 250}
                    ]
                }
            },
            "supplementRecommendations": [
                {
                    "supplement": "Creatina",
                    "dosage": "2 porciones en el día",
                    "instructions": "Puedes consumirla en cualquier momento."
                }
            ],
            "generalRecommendations": [
                "Para cocinar, preferir aceite de girasol, soja o canola; para preparaciones en frío, usar aceite de oliva.",
                "Las verduras no tienen restricción de cantidad.",
                "Para controlar la ansiedad: verduras picadas, gelatina sin azúcar o 1 porción de nueces.",
                "Mantener un consumo de agua de 8-10 vasos diarios (mínimo 6).",
                "Realizar actividad física según las indicaciones."
            ]
        }
    }
    
    # Paso 1: Crear usuario
    user_id = create_user()
    
    if not user_id:
        print("\n⚠️  No se pudo crear el usuario automáticamente.")
        print("Por favor, proporciona el UUID del usuario manualmente:")
        user_id = input("UUID: ").strip()
        
        if not user_id:
            print("❌ UUID no proporcionado. Abortando.")
            return
    
    print()
    
    # Paso 2: Crear plan nutricional
    try:
        nutrition_plan = create_nutrition_plan(user_id, gabriel_plan_data)
        
        print()
        print("=" * 60)
        print("✅ ¡Proceso completado exitosamente!")
        print("=" * 60)
        print(f"\n📧 Email: gacardona@aura.com")
        print(f"🔑 Password: Aura123!")
        print(f"👤 Usuario ID: {user_id}")
        print(f"📋 Plan ID: {nutrition_plan.id}")
        print()
        print("🔍 Puedes verificar el plan con:")
        print(f"   GET /dashboard/body/nutrition-plans/{nutrition_plan.id}/")
        print()
        
    except Exception as e:
        print(f"\n❌ Error al crear plan nutricional: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

