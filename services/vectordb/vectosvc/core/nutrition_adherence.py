"""
Análisis de Adherencia a Planes Nutricionales

Módulo para evaluar qué tan bien un usuario sigue su plan nutricional asignado.

Funcionalidades:
- Comparación entre plan prescrito y consumo real
- Cálculo de tasas de adherencia por macronutriente
- Detección de patrones de incumplimiento
- Generación de insights y recomendaciones

Referencias:
- Burke, L.E. et al. (2011) - "Self-Monitoring in Weight Loss: A Systematic Review"
- Painter, S.L. et al. (2002) - "Dietary Adherence and Weight Loss Success"
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger


# ============================================================================
# CONSTANTES Y UMBRALES
# ============================================================================

# Umbrales de adherencia (%)
EXCELLENT_ADHERENCE = 90.0  # ≥90% = excelente
GOOD_ADHERENCE = 75.0       # 75-89% = buena
MODERATE_ADHERENCE = 60.0   # 60-74% = moderada
# <60% = pobre

# Tolerancia para cumplimiento (%)
TOLERANCE_CALORIES = 10.0    # ±10% en calorías se considera cumplido
TOLERANCE_PROTEIN = 15.0     # ±15% en proteína
TOLERANCE_CARBS = 15.0       # ±15% en carbohidratos
TOLERANCE_FATS = 15.0        # ±15% en grasas

# Mínimo de registros para análisis confiable
MIN_LOGS_FOR_ANALYSIS = 3
MIN_DAYS_FOR_WEEKLY_ANALYSIS = 5


# ============================================================================
# TIPOS Y ESTRUCTURAS
# ============================================================================

class AdherenceLevel:
    """Niveles de adherencia."""
    EXCELLENT = "excellent"      # ≥90%
    GOOD = "good"               # 75-89%
    MODERATE = "moderate"       # 60-74%
    POOR = "poor"               # <60%
    INSUFFICIENT_DATA = "insufficient_data"


class AdherenceIssue:
    """Tipos de problemas de adherencia."""
    UNDER_EATING = "under_eating"          # Consumo < objetivo
    OVER_EATING = "over_eating"            # Consumo > objetivo
    PROTEIN_DEFICIT = "protein_deficit"    # Proteína baja
    CARB_EXCESS = "carb_excess"           # Carbohidratos altos
    FAT_EXCESS = "fat_excess"             # Grasas altas
    INCONSISTENT = "inconsistent"          # Gran variabilidad
    MISSING_LOGS = "missing_logs"          # Días sin registrar


# ============================================================================
# FUNCIONES PRINCIPALES
# ============================================================================

def analyze_nutrition_adherence(
    nutrition_plan: Dict[str, Any],
    nutrition_logs: List[Dict[str, Any]],
    time_range_days: Optional[int] = 7
) -> Dict[str, Any]:
    """
    Analiza la adherencia de un usuario a su plan nutricional.

    Args:
        nutrition_plan: Plan nutricional asignado con objetivos diarios
            {
                'daily_calories': float,
                'daily_protein_g': float,
                'daily_carbs_g': float,
                'daily_fats_g': float,
                'plan_data': {...}
            }
        nutrition_logs: Registros de consumo del usuario
            [
                {
                    'logged_at': str (ISO date),
                    'total_calories': float,
                    'total_protein_g': float,
                    'total_carbs_g': float,
                    'total_fats_g': float,
                    'meal_type': str
                },
                ...
            ]
        time_range_days: Días a analizar (default: última semana)

    Returns:
        Dict con análisis completo:
        {
            'period': {'start': str, 'end': str, 'days': int},
            'logs_count': int,
            'coverage': float,  # % de días con registros
            'adherence_rates': {
                'overall': float,
                'calories': float,
                'protein': float,
                'carbs': float,
                'fats': float
            },
            'adherence_level': str,
            'daily_analysis': [
                {
                    'date': str,
                    'logged': bool,
                    'target': {...},
                    'actual': {...},
                    'adherence': {...}
                }
            ],
            'issues': [
                {
                    'type': str,
                    'severity': str,
                    'description': str,
                    'recommendation': str
                }
            ],
            'trends': {
                'improving': bool,
                'consistency_score': float
            },
            'summary': str
        }
    """
    if not nutrition_plan or not nutrition_logs:
        return _create_empty_result("No hay plan nutricional o registros disponibles.")

    # Filtrar logs por rango temporal
    cutoff_date = datetime.now() - timedelta(days=time_range_days)
    logs_filtered = [
        log for log in nutrition_logs
        if _parse_date(log.get('logged_at')) >= cutoff_date
    ]

    if len(logs_filtered) < MIN_LOGS_FOR_ANALYSIS:
        return _create_empty_result(
            f"Se necesitan al menos {MIN_LOGS_FOR_ANALYSIS} registros para análisis."
        )

    # Extraer objetivos del plan
    targets = _extract_targets(nutrition_plan)

    # Agrupar logs por día
    daily_logs = _group_logs_by_day(logs_filtered)

    # Analizar cada día
    daily_analysis = []
    for date in _get_date_range(time_range_days):
        date_str = date.strftime('%Y-%m-%d')
        day_logs = daily_logs.get(date_str, [])

        day_result = _analyze_day(date_str, day_logs, targets)
        daily_analysis.append(day_result)

    # Calcular tasas de adherencia
    adherence_rates = _calculate_adherence_rates(daily_analysis)

    # Determinar nivel de adherencia
    adherence_level = _determine_adherence_level(adherence_rates['overall'])

    # Detectar problemas
    issues = _detect_adherence_issues(daily_analysis, adherence_rates, targets)

    # Analizar tendencias
    trends = _analyze_adherence_trends(daily_analysis)

    # Calcular cobertura (% de días con registros)
    days_with_logs = sum(1 for day in daily_analysis if day['logged'])
    coverage = (days_with_logs / len(daily_analysis) * 100) if daily_analysis else 0

    # Calcular período
    period = _calculate_period_from_days(daily_analysis)

    # Generar resumen
    summary = _generate_adherence_summary(
        adherence_level, adherence_rates, coverage, len(issues)
    )

    return {
        'period': period,
        'logs_count': len(logs_filtered),
        'coverage': round(coverage, 1),
        'adherence_rates': adherence_rates,
        'adherence_level': adherence_level,
        'daily_analysis': daily_analysis,
        'issues': issues,
        'trends': trends,
        'summary': summary
    }


def _extract_targets(nutrition_plan: Dict[str, Any]) -> Dict[str, float]:
    """Extrae los objetivos nutricionales del plan."""
    plan_data = nutrition_plan.get('plan_data', {})

    # Intentar obtener de múltiples ubicaciones
    targets = {
        'calories': None,
        'protein_g': None,
        'carbs_g': None,
        'fats_g': None
    }

    # Opción 1: Campos directos
    targets['calories'] = (
        nutrition_plan.get('daily_calories') or
        plan_data.get('daily_calories') or
        plan_data.get('nutrition', {}).get('daily_calories')
    )
    targets['protein_g'] = (
        nutrition_plan.get('daily_protein_g') or
        plan_data.get('daily_protein_g') or
        plan_data.get('nutrition', {}).get('daily_protein_g')
    )
    targets['carbs_g'] = (
        nutrition_plan.get('daily_carbs_g') or
        plan_data.get('daily_carbs_g') or
        plan_data.get('nutrition', {}).get('daily_carbs_g')
    )
    targets['fats_g'] = (
        nutrition_plan.get('daily_fats_g') or
        plan_data.get('daily_fats_g') or
        plan_data.get('nutrition', {}).get('daily_fats_g')
    )

    # Convertir a float
    for key in targets:
        if targets[key] is not None:
            targets[key] = float(targets[key])

    return targets


def _group_logs_by_day(logs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Agrupa los logs por día."""
    daily_logs = {}

    for log in logs:
        date = _parse_date(log.get('logged_at'))
        if date:
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in daily_logs:
                daily_logs[date_str] = []
            daily_logs[date_str].append(log)

    return daily_logs


def _analyze_day(
    date_str: str,
    day_logs: List[Dict[str, Any]],
    targets: Dict[str, float]
) -> Dict[str, Any]:
    """Analiza la adherencia de un día específico."""
    if not day_logs:
        return {
            'date': date_str,
            'logged': False,
            'target': targets,
            'actual': None,
            'adherence': None,
            'compliant': False
        }

    # Sumar todos los logs del día
    actual = {
        'calories': sum(float(log.get('total_calories', 0)) for log in day_logs),
        'protein_g': sum(float(log.get('total_protein_g', 0)) for log in day_logs),
        'carbs_g': sum(float(log.get('total_carbs_g', 0)) for log in day_logs),
        'fats_g': sum(float(log.get('total_fats_g', 0)) for log in day_logs)
    }

    # Calcular adherencia por nutriente
    adherence = {}
    compliant_count = 0
    total_nutrients = 0

    for nutrient in ['calories', 'protein_g', 'carbs_g', 'fats_g']:
        target_value = targets.get(nutrient)
        actual_value = actual.get(nutrient)

        if target_value and target_value > 0:
            total_nutrients += 1
            adherence_pct = (actual_value / target_value) * 100
            adherence[nutrient] = round(adherence_pct, 1)

            # Verificar si cumple con la tolerancia
            tolerance = _get_tolerance(nutrient)
            if abs(adherence_pct - 100) <= tolerance:
                compliant_count += 1

    # Determinar si el día fue compliant
    compliant = (compliant_count / total_nutrients) >= 0.5 if total_nutrients > 0 else False

    return {
        'date': date_str,
        'logged': True,
        'target': targets,
        'actual': actual,
        'adherence': adherence,
        'compliant': compliant
    }


def _calculate_adherence_rates(daily_analysis: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calcula las tasas promedio de adherencia."""
    # Filtrar solo días con logs
    logged_days = [day for day in daily_analysis if day['logged']]

    if not logged_days:
        return {
            'overall': 0.0,
            'calories': 0.0,
            'protein': 0.0,
            'carbs': 0.0,
            'fats': 0.0
        }

    # Promediar adherencia por nutriente
    adherence_sums = {'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fats_g': 0}
    counts = {'calories': 0, 'protein_g': 0, 'carbs_g': 0, 'fats_g': 0}

    for day in logged_days:
        if day['adherence']:
            for nutrient in adherence_sums:
                if nutrient in day['adherence']:
                    adherence_sums[nutrient] += day['adherence'][nutrient]
                    counts[nutrient] += 1

    rates = {}
    for nutrient in adherence_sums:
        if counts[nutrient] > 0:
            rates[nutrient] = round(adherence_sums[nutrient] / counts[nutrient], 1)
        else:
            rates[nutrient] = 0.0

    # Calcular adherencia overall (promedio de todos los nutrientes)
    overall = sum(rates.values()) / len(rates) if rates else 0.0

    return {
        'overall': round(overall, 1),
        'calories': rates.get('calories', 0.0),
        'protein': rates.get('protein_g', 0.0),
        'carbs': rates.get('carbs_g', 0.0),
        'fats': rates.get('fats_g', 0.0)
    }


def _determine_adherence_level(overall_rate: float) -> str:
    """Determina el nivel de adherencia basado en la tasa overall."""
    if overall_rate >= EXCELLENT_ADHERENCE:
        return AdherenceLevel.EXCELLENT
    elif overall_rate >= GOOD_ADHERENCE:
        return AdherenceLevel.GOOD
    elif overall_rate >= MODERATE_ADHERENCE:
        return AdherenceLevel.MODERATE
    else:
        return AdherenceLevel.POOR


def _detect_adherence_issues(
    daily_analysis: List[Dict[str, Any]],
    adherence_rates: Dict[str, float],
    targets: Dict[str, float]
) -> List[Dict[str, Any]]:
    """Detecta problemas específicos de adherencia."""
    issues = []

    # Issue 1: Días sin registrar
    missing_days = sum(1 for day in daily_analysis if not day['logged'])
    if missing_days > 0:
        severity = "high" if missing_days > 3 else "medium"
        issues.append({
            'type': AdherenceIssue.MISSING_LOGS,
            'severity': severity,
            'description': f'{missing_days} días sin registros nutricionales',
            'recommendation': 'Registra tus comidas diariamente para un mejor seguimiento.'
        })

    # Issue 2: Calorías bajo objetivo
    if adherence_rates['calories'] < 85:
        issues.append({
            'type': AdherenceIssue.UNDER_EATING,
            'severity': 'high' if adherence_rates['calories'] < 70 else 'medium',
            'description': f'Consumo calórico bajo: {adherence_rates["calories"]}% del objetivo',
            'recommendation': 'Aumenta las porciones o agrega snacks saludables para alcanzar tu meta calórica.'
        })

    # Issue 3: Calorías sobre objetivo
    elif adherence_rates['calories'] > 115:
        issues.append({
            'type': AdherenceIssue.OVER_EATING,
            'severity': 'high' if adherence_rates['calories'] > 130 else 'medium',
            'description': f'Consumo calórico alto: {adherence_rates["calories"]}% del objetivo',
            'recommendation': 'Reduce las porciones o elige alimentos menos calóricos.'
        })

    # Issue 4: Déficit de proteína
    if adherence_rates['protein'] < 80:
        issues.append({
            'type': AdherenceIssue.PROTEIN_DEFICIT,
            'severity': 'high',
            'description': f'Proteína baja: {adherence_rates["protein"]}% del objetivo',
            'recommendation': 'Aumenta el consumo de carnes magras, pescado, huevos o legumbres.'
        })

    # Issue 5: Exceso de carbohidratos
    if adherence_rates['carbs'] > 120:
        issues.append({
            'type': AdherenceIssue.CARB_EXCESS,
            'severity': 'medium',
            'description': f'Carbohidratos altos: {adherence_rates["carbs"]}% del objetivo',
            'recommendation': 'Reduce harinas refinadas y azúcares. Prefiere carbohidratos complejos.'
        })

    # Issue 6: Exceso de grasas
    if adherence_rates['fats'] > 120:
        issues.append({
            'type': AdherenceIssue.FAT_EXCESS,
            'severity': 'medium',
            'description': f'Grasas altas: {adherence_rates["fats"]}% del objetivo',
            'recommendation': 'Reduce frituras y alimentos procesados. Prefiere grasas saludables (aguacate, nueces).'
        })

    # Issue 7: Inconsistencia
    logged_days = [day for day in daily_analysis if day['logged']]
    if logged_days:
        calorie_values = [day['actual']['calories'] for day in logged_days]
        if len(calorie_values) >= 3:
            std_dev = np.std(calorie_values)
            mean_calories = np.mean(calorie_values)
            cv = (std_dev / mean_calories * 100) if mean_calories > 0 else 0

            if cv > 30:  # Coeficiente de variación > 30%
                issues.append({
                    'type': AdherenceIssue.INCONSISTENT,
                    'severity': 'medium',
                    'description': 'Alta variabilidad en el consumo diario',
                    'recommendation': 'Mantén una rutina alimentaria más consistente.'
                })

    return issues


def _analyze_adherence_trends(daily_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analiza tendencias de adherencia a lo largo del tiempo."""
    logged_days = [day for day in daily_analysis if day['logged'] and day['adherence']]

    if len(logged_days) < 3:
        return {
            'improving': None,
            'consistency_score': 0.0
        }

    # Calcular adherencia overall por día
    daily_overall = []
    for day in logged_days:
        adherence_values = list(day['adherence'].values())
        overall = sum(adherence_values) / len(adherence_values) if adherence_values else 0
        daily_overall.append(overall)

    # Detectar si está mejorando (comparar primera mitad vs segunda mitad)
    mid = len(daily_overall) // 2
    first_half_avg = np.mean(daily_overall[:mid]) if mid > 0 else 0
    second_half_avg = np.mean(daily_overall[mid:])
    improving = second_half_avg > first_half_avg

    # Calcular consistency score (inversa del coeficiente de variación)
    std_dev = np.std(daily_overall)
    mean_adherence = np.mean(daily_overall)
    cv = (std_dev / mean_adherence * 100) if mean_adherence > 0 else 100
    consistency_score = max(0, 100 - cv)  # 100% = perfectamente consistente

    return {
        'improving': improving,
        'consistency_score': round(consistency_score, 1)
    }


def _get_tolerance(nutrient: str) -> float:
    """Obtiene la tolerancia para un nutriente específico."""
    tolerances = {
        'calories': TOLERANCE_CALORIES,
        'protein_g': TOLERANCE_PROTEIN,
        'carbs_g': TOLERANCE_CARBS,
        'fats_g': TOLERANCE_FATS
    }
    return tolerances.get(nutrient, 10.0)


def _get_date_range(days: int) -> List[datetime]:
    """Genera una lista de fechas para el rango especificado."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return [today - timedelta(days=i) for i in range(days - 1, -1, -1)]


def _parse_date(date_value: Any) -> Optional[datetime]:
    """Parsea una fecha en múltiples formatos."""
    if isinstance(date_value, datetime):
        return date_value

    if isinstance(date_value, str):
        try:
            return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass

        try:
            return datetime.strptime(date_value, '%Y-%m-%d')
        except ValueError:
            pass

    return None


def _calculate_period_from_days(daily_analysis: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Calcula el período basado en el análisis diario."""
    if not daily_analysis:
        return None

    dates = [day['date'] for day in daily_analysis]
    start_date = min(dates)
    end_date = max(dates)

    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    days = (end_dt - start_dt).days + 1

    return {
        'start': start_date,
        'end': end_date,
        'days': days
    }


def _generate_adherence_summary(
    adherence_level: str,
    adherence_rates: Dict[str, float],
    coverage: float,
    issues_count: int
) -> str:
    """Genera un resumen textual de la adherencia."""
    level_text = {
        AdherenceLevel.EXCELLENT: "excelente",
        AdherenceLevel.GOOD: "buena",
        AdherenceLevel.MODERATE: "moderada",
        AdherenceLevel.POOR: "pobre"
    }.get(adherence_level, "desconocida")

    summary_parts = [
        f"Adherencia {level_text} ({adherence_rates['overall']:.1f}%).",
        f"Cobertura de registros: {coverage:.1f}%."
    ]

    if adherence_rates['calories'] < 90:
        summary_parts.append(f"Calorías: {adherence_rates['calories']:.1f}% del objetivo.")

    if adherence_rates['protein'] < 85:
        summary_parts.append(f"Proteína baja: {adherence_rates['protein']:.1f}%.")

    if issues_count > 0:
        summary_parts.append(f"{issues_count} área(s) de mejora detectadas.")

    return " ".join(summary_parts)


def _create_empty_result(message: str) -> Dict[str, Any]:
    """Crea un resultado vacío con mensaje."""
    return {
        'period': None,
        'logs_count': 0,
        'coverage': 0.0,
        'adherence_rates': {
            'overall': 0.0,
            'calories': 0.0,
            'protein': 0.0,
            'carbs': 0.0,
            'fats': 0.0
        },
        'adherence_level': AdherenceLevel.INSUFFICIENT_DATA,
        'daily_analysis': [],
        'issues': [],
        'trends': {
            'improving': None,
            'consistency_score': 0.0
        },
        'summary': message
    }
