"""
Análisis de Tendencias para Mediciones Corporales

Módulo para análisis de series temporales, detección de patrones y proyecciones.

Funcionalidades:
- Análisis de tendencias lineales (peso, grasa, músculo)
- Regresión lineal para proyecciones
- Detección de cambios significativos
- Cálculo de velocidades de cambio
- Generación de alertas y recomendaciones

Referencias:
- Box, G.E.P. & Jenkins, G.M. (1976) - Time Series Analysis
- Cleveland, W.S. (1979) - LOWESS regression
- Montgomery, D.C. (2009) - Statistical Quality Control
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger
from scipy import stats


# ============================================================================
# CONSTANTES Y UMBRALES
# ============================================================================

# Umbrales para detección de cambios significativos
SIGNIFICANT_WEIGHT_CHANGE_KG_PER_WEEK = 0.5  # kg/semana
SIGNIFICANT_BF_CHANGE_PCT_PER_MONTH = 1.0    # %/mes
SIGNIFICANT_MUSCLE_CHANGE_KG_PER_MONTH = 0.5  # kg/mes

# Mínimo de mediciones para análisis confiable
MIN_MEASUREMENTS_FOR_TREND = 3
MIN_MEASUREMENTS_FOR_REGRESSION = 5

# Nivel de confianza para regresiones
REGRESSION_CONFIDENCE_LEVEL = 0.95


# ============================================================================
# TIPOS Y ESTRUCTURAS
# ============================================================================

class TrendDirection:
    """Dirección de la tendencia."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


class TrendSignificance:
    """Significancia estadística de la tendencia."""
    HIGHLY_SIGNIFICANT = "highly_significant"  # p < 0.01
    SIGNIFICANT = "significant"                # p < 0.05
    MARGINALLY_SIGNIFICANT = "marginally_significant"  # p < 0.10
    NOT_SIGNIFICANT = "not_significant"        # p >= 0.10


class AlertLevel:
    """Nivel de alerta para cambios."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ============================================================================
# FUNCIONES PRINCIPALES
# ============================================================================

def analyze_measurement_trends(
    measurements: List[Dict[str, Any]],
    time_range_days: Optional[int] = None,
    target_metrics: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Analiza tendencias en series temporales de mediciones corporales.

    Args:
        measurements: Lista de mediciones ordenadas por fecha (más reciente primero)
        time_range_days: Rango temporal en días (None = todas las mediciones)
        target_metrics: Métricas a analizar (None = todas disponibles)

    Returns:
        Dict con análisis completo:
        {
            'period': {'start': '2025-01-01', 'end': '2025-11-20', 'days': 90},
            'measurement_count': int,
            'trends': {
                'weight_kg': {
                    'direction': str,
                    'slope': float,  # unidad/día
                    'change_total': float,
                    'change_percent': float,
                    'velocity': float,  # unidad/semana o unidad/mes
                    'significance': str,
                    'p_value': float,
                    'r_squared': float,
                    'projection_30d': float
                },
                ...
            },
            'alerts': [
                {
                    'metric': str,
                    'level': str,
                    'message': str,
                    'recommendation': str
                }
            ],
            'summary': str
        }
    """
    if not measurements:
        return {
            'period': None,
            'measurement_count': 0,
            'trends': {},
            'alerts': [],
            'summary': 'No hay mediciones disponibles para análisis.'
        }

    # Filtrar por rango temporal si se especifica
    if time_range_days:
        cutoff_date = datetime.now() - timedelta(days=time_range_days)
        measurements = [
            m for m in measurements
            if _parse_date(m.get('recorded_at')) >= cutoff_date
        ]

    if len(measurements) < MIN_MEASUREMENTS_FOR_TREND:
        return {
            'period': _calculate_period(measurements),
            'measurement_count': len(measurements),
            'trends': {},
            'alerts': [{
                'metric': 'general',
                'level': AlertLevel.INFO,
                'message': f'Se necesitan al menos {MIN_MEASUREMENTS_FOR_TREND} mediciones para análisis de tendencias.',
                'recommendation': 'Continúa registrando mediciones regularmente.'
            }],
            'summary': 'Datos insuficientes para análisis de tendencias.'
        }

    # Definir métricas a analizar
    if target_metrics is None:
        target_metrics = [
            'weight_kg',
            'bmi',
            'body_fat_percentage',
            'fat_mass_kg',
            'muscle_mass_kg',
            'waist_circumference_cm',
            'waist_hip_ratio'
        ]

    # Analizar cada métrica
    trends = {}
    alerts = []

    for metric in target_metrics:
        trend_result = _analyze_metric_trend(measurements, metric)
        if trend_result:
            trends[metric] = trend_result

            # Generar alertas si es necesario
            metric_alerts = _generate_alerts_for_metric(metric, trend_result)
            alerts.extend(metric_alerts)

    # Calcular período
    period = _calculate_period(measurements)

    # Generar resumen
    summary = _generate_summary(trends, len(measurements), period)

    return {
        'period': period,
        'measurement_count': len(measurements),
        'trends': trends,
        'alerts': alerts,
        'summary': summary
    }


def _analyze_metric_trend(
    measurements: List[Dict[str, Any]],
    metric: str
) -> Optional[Dict[str, Any]]:
    """
    Analiza la tendencia de una métrica específica.

    Args:
        measurements: Lista de mediciones
        metric: Nombre de la métrica (ej: 'weight_kg')

    Returns:
        Dict con análisis de la tendencia o None si no hay datos suficientes
    """
    # Extraer datos de la métrica
    data_points = []
    for m in measurements:
        value = m.get(metric)
        date = _parse_date(m.get('recorded_at'))
        if value is not None and date is not None:
            data_points.append((date, float(value)))

    if len(data_points) < MIN_MEASUREMENTS_FOR_TREND:
        return None

    # Ordenar por fecha
    data_points.sort(key=lambda x: x[0])

    # Extraer arrays para análisis
    dates = [dp[0] for dp in data_points]
    values = np.array([dp[1] for dp in data_points])

    # Convertir fechas a días desde la primera medición
    days_from_start = np.array([
        (date - dates[0]).days for date in dates
    ])

    # Si todas las mediciones son del mismo día, no se puede calcular tendencia
    if days_from_start.max() == 0:
        # Todas las mediciones del mismo día
        mean_value = values.mean()
        return {
            'direction': TrendDirection.STABLE,
            'slope': 0.0,
            'change_total': 0.0,
            'change_percent': 0.0,
            'velocity_per_week': 0.0,
            'velocity_per_month': 0.0,
            'significance': TrendSignificance.NOT_SIGNIFICANT,
            'p_value': 1.0,
            'r_squared': 0.0,
            'projection_30d': round(mean_value, 2),
            'current_value': round(values[-1], 2),
            'initial_value': round(values[0], 2)
        }

    # Regresión lineal
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        days_from_start, values
    )

    # Calcular cambios
    initial_value = values[0]
    final_value = values[-1]
    change_total = final_value - initial_value
    change_percent = (change_total / initial_value * 100) if initial_value != 0 else 0

    # Determinar dirección
    # Umbral más realista: 0.01 unidades/día = ~0.07 unidades/semana
    if abs(slope) < 0.01:
        direction = TrendDirection.STABLE
    elif slope > 0:
        direction = TrendDirection.INCREASING
    else:
        direction = TrendDirection.DECREASING

    # Determinar significancia
    if p_value < 0.01:
        significance = TrendSignificance.HIGHLY_SIGNIFICANT
    elif p_value < 0.05:
        significance = TrendSignificance.SIGNIFICANT
    elif p_value < 0.10:
        significance = TrendSignificance.MARGINALLY_SIGNIFICANT
    else:
        significance = TrendSignificance.NOT_SIGNIFICANT

    # Calcular velocidad de cambio
    total_days = (dates[-1] - dates[0]).days
    if total_days == 0:
        velocity_per_week = 0
        velocity_per_month = 0
    else:
        velocity_per_week = (change_total / total_days) * 7
        velocity_per_month = (change_total / total_days) * 30

    # Proyección a 30 días
    projection_30d = None
    if len(data_points) >= MIN_MEASUREMENTS_FOR_REGRESSION:
        last_day = days_from_start[-1]
        projection_30d = slope * (last_day + 30) + intercept

    return {
        'direction': direction,
        'slope': round(slope, 4),
        'change_total': round(change_total, 2),
        'change_percent': round(change_percent, 2),
        'velocity_per_week': round(velocity_per_week, 3),
        'velocity_per_month': round(velocity_per_month, 3),
        'significance': significance,
        'p_value': round(p_value, 4),
        'r_squared': round(r_value ** 2, 4),
        'projection_30d': round(projection_30d, 2) if projection_30d else None,
        'current_value': round(final_value, 2),
        'initial_value': round(initial_value, 2)
    }


def _generate_alerts_for_metric(
    metric: str,
    trend: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Genera alertas basadas en el análisis de tendencia de una métrica.

    Args:
        metric: Nombre de la métrica
        trend: Resultado del análisis de tendencia

    Returns:
        Lista de alertas
    """
    alerts = []

    # Alertas para peso
    if metric == 'weight_kg':
        velocity_per_week = abs(trend['velocity_per_week'])

        if velocity_per_week > 1.0:
            alerts.append({
                'metric': metric,
                'level': AlertLevel.CRITICAL,
                'message': f'Cambio rápido de peso: {velocity_per_week:.2f} kg/semana',
                'recommendation': 'Consulta con un profesional. Los cambios rápidos pueden ser perjudiciales.'
            })
        elif velocity_per_week > SIGNIFICANT_WEIGHT_CHANGE_KG_PER_WEEK:
            alerts.append({
                'metric': metric,
                'level': AlertLevel.WARNING,
                'message': f'Cambio significativo de peso: {velocity_per_week:.2f} kg/semana',
                'recommendation': 'Monitorea tu progreso de cerca y ajusta tu plan si es necesario.'
            })

    # Alertas para grasa corporal
    if metric == 'body_fat_percentage':
        velocity_per_month = abs(trend['velocity_per_month'])

        if velocity_per_month > 2.0:
            alerts.append({
                'metric': metric,
                'level': AlertLevel.CRITICAL,
                'message': f'Cambio rápido de grasa corporal: {velocity_per_month:.2f}%/mes',
                'recommendation': 'Este cambio es inusualmente rápido. Consulta con un profesional.'
            })
        elif velocity_per_month > SIGNIFICANT_BF_CHANGE_PCT_PER_MONTH:
            alerts.append({
                'metric': metric,
                'level': AlertLevel.WARNING,
                'message': f'Cambio significativo de grasa corporal: {velocity_per_month:.2f}%/mes',
                'recommendation': 'Buen progreso. Mantén tu plan actual.'
            })

    # Alertas para masa muscular
    if metric == 'muscle_mass_kg':
        velocity_per_month = trend['velocity_per_month']

        if velocity_per_month < -1.0:
            alerts.append({
                'metric': metric,
                'level': AlertLevel.CRITICAL,
                'message': f'Pérdida rápida de masa muscular: {abs(velocity_per_month):.2f} kg/mes',
                'recommendation': 'Revisa tu ingesta de proteína y programa de entrenamiento.'
            })
        elif velocity_per_month < -SIGNIFICANT_MUSCLE_CHANGE_KG_PER_MONTH:
            alerts.append({
                'metric': metric,
                'level': AlertLevel.WARNING,
                'message': f'Pérdida de masa muscular: {abs(velocity_per_month):.2f} kg/mes',
                'recommendation': 'Considera aumentar el entrenamiento de fuerza.'
            })
        elif velocity_per_month > 0.5:
            alerts.append({
                'metric': metric,
                'level': AlertLevel.INFO,
                'message': f'Ganancia de masa muscular: {velocity_per_month:.2f} kg/mes',
                'recommendation': '¡Excelente progreso! Continúa con tu plan actual.'
            })

    # Alertas para circunferencia de cintura
    if metric == 'waist_circumference_cm':
        velocity_per_month = trend['velocity_per_month']

        if velocity_per_month > 2.0:
            alerts.append({
                'metric': metric,
                'level': AlertLevel.WARNING,
                'message': f'Aumento de circunferencia de cintura: {velocity_per_month:.2f} cm/mes',
                'recommendation': 'La grasa abdominal aumenta el riesgo cardiovascular. Consulta con un profesional.'
            })
        elif velocity_per_month < -2.0:
            alerts.append({
                'metric': metric,
                'level': AlertLevel.INFO,
                'message': f'Reducción de circunferencia de cintura: {abs(velocity_per_month):.2f} cm/mes',
                'recommendation': '¡Excelente! Esto reduce tu riesgo cardiovascular.'
            })

    return alerts


def _calculate_period(measurements: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Calcula el período cubierto por las mediciones.

    Args:
        measurements: Lista de mediciones

    Returns:
        Dict con start, end y days
    """
    if not measurements:
        return None

    dates = [_parse_date(m.get('recorded_at')) for m in measurements]
    dates = [d for d in dates if d is not None]

    if not dates:
        return None

    start_date = min(dates)
    end_date = max(dates)
    days = (end_date - start_date).days

    return {
        'start': start_date.strftime('%Y-%m-%d'),
        'end': end_date.strftime('%Y-%m-%d'),
        'days': days
    }


def _parse_date(date_value: Any) -> Optional[datetime]:
    """
    Parsea una fecha en múltiples formatos.

    Args:
        date_value: Valor de fecha (str, datetime, etc.)

    Returns:
        Objeto datetime o None
    """
    if isinstance(date_value, datetime):
        return date_value

    if isinstance(date_value, str):
        try:
            # Intenta ISO format
            return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass

        try:
            # Intenta formato común
            return datetime.strptime(date_value, '%Y-%m-%d')
        except ValueError:
            pass

    return None


def _generate_summary(
    trends: Dict[str, Dict[str, Any]],
    measurement_count: int,
    period: Optional[Dict[str, Any]]
) -> str:
    """
    Genera un resumen textual del análisis de tendencias.

    Args:
        trends: Resultados de análisis de tendencias
        measurement_count: Número de mediciones
        period: Período analizado

    Returns:
        Resumen en texto plano
    """
    if not trends:
        return 'No hay suficientes datos para generar un resumen.'

    summary_parts = []

    # Período
    if period:
        summary_parts.append(
            f"Análisis de {measurement_count} mediciones durante {period['days']} días "
            f"({period['start']} a {period['end']})."
        )

    # Peso
    if 'weight_kg' in trends:
        weight = trends['weight_kg']
        direction_text = {
            TrendDirection.INCREASING: 'aumentando',
            TrendDirection.DECREASING: 'disminuyendo',
            TrendDirection.STABLE: 'estable'
        }.get(weight['direction'], 'sin cambios significativos')

        summary_parts.append(
            f"Peso: {direction_text} ({weight['change_total']:+.2f} kg, "
            f"{weight['change_percent']:+.1f}%)."
        )

    # Grasa corporal
    if 'body_fat_percentage' in trends:
        bf = trends['body_fat_percentage']
        direction_text = {
            TrendDirection.INCREASING: 'aumentando',
            TrendDirection.DECREASING: 'disminuyendo',
            TrendDirection.STABLE: 'estable'
        }.get(bf['direction'], 'sin cambios')

        summary_parts.append(
            f"Grasa corporal: {direction_text} ({bf['change_total']:+.2f}%)."
        )

    # Masa muscular
    if 'muscle_mass_kg' in trends:
        muscle = trends['muscle_mass_kg']
        direction_text = {
            TrendDirection.INCREASING: 'aumentando',
            TrendDirection.DECREASING: 'disminuyendo',
            TrendDirection.STABLE: 'estable'
        }.get(muscle['direction'], 'sin cambios')

        summary_parts.append(
            f"Masa muscular: {direction_text} ({muscle['change_total']:+.2f} kg)."
        )

    return ' '.join(summary_parts)


# ============================================================================
# FUNCIONES DE PROYECCIÓN
# ============================================================================

def project_metric_to_date(
    measurements: List[Dict[str, Any]],
    metric: str,
    target_date: datetime
) -> Optional[Dict[str, Any]]:
    """
    Proyecta el valor de una métrica a una fecha futura.

    Args:
        measurements: Lista de mediciones históricas
        metric: Métrica a proyectar
        target_date: Fecha objetivo

    Returns:
        Dict con proyección:
        {
            'projected_value': float,
            'confidence_interval': (float, float),
            'method': str,
            'r_squared': float
        }
    """
    if len(measurements) < MIN_MEASUREMENTS_FOR_REGRESSION:
        return None

    # Extraer datos
    data_points = []
    for m in measurements:
        value = m.get(metric)
        date = _parse_date(m.get('recorded_at'))
        if value is not None and date is not None:
            data_points.append((date, float(value)))

    if len(data_points) < MIN_MEASUREMENTS_FOR_REGRESSION:
        return None

    # Ordenar
    data_points.sort(key=lambda x: x[0])
    dates = [dp[0] for dp in data_points]
    values = np.array([dp[1] for dp in data_points])

    # Días desde inicio
    reference_date = dates[0]
    days_from_start = np.array([(date - reference_date).days for date in dates])
    target_days = (target_date - reference_date).days

    # Regresión
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        days_from_start, values
    )

    # Proyección
    projected_value = slope * target_days + intercept

    # Intervalo de confianza (simplificado)
    residuals = values - (slope * days_from_start + intercept)
    std_residual = np.std(residuals)
    margin = 1.96 * std_residual  # 95% CI

    # Asegurar margen mínimo (para evitar intervalos degenerados)
    min_margin = 0.5  # Mínimo de 0.5 unidades
    if margin < min_margin:
        margin = min_margin

    return {
        'projected_value': round(projected_value, 2),
        'confidence_interval': (
            round(projected_value - margin, 2),
            round(projected_value + margin, 2)
        ),
        'method': 'linear_regression',
        'r_squared': round(r_value ** 2, 4),
        'p_value': round(p_value, 4)
    }


# ============================================================================
# FUNCIONES DE COMPARACIÓN
# ============================================================================

def compare_periods(
    measurements: List[Dict[str, Any]],
    period1_days: int,
    period2_days: int
) -> Dict[str, Any]:
    """
    Compara tendencias entre dos períodos de tiempo.

    Args:
        measurements: Lista de mediciones
        period1_days: Duración del primer período (más antiguo)
        period2_days: Duración del segundo período (más reciente)

    Returns:
        Dict con comparación de períodos
    """
    now = datetime.now()

    # Período 2 (más reciente)
    period2_start = now - timedelta(days=period2_days)
    period2_measurements = [
        m for m in measurements
        if _parse_date(m.get('recorded_at')) >= period2_start
    ]

    # Período 1 (anterior al período 2)
    period1_end = period2_start
    period1_start = period1_end - timedelta(days=period1_days)
    period1_measurements = [
        m for m in measurements
        if period1_start <= _parse_date(m.get('recorded_at')) < period1_end
    ]

    # Analizar ambos períodos
    period1_analysis = analyze_measurement_trends(period1_measurements)
    period2_analysis = analyze_measurement_trends(period2_measurements)

    return {
        'period1': {
            'range': f'{period1_days} días previos',
            'analysis': period1_analysis
        },
        'period2': {
            'range': f'Últimos {period2_days} días',
            'analysis': period2_analysis
        },
        'comparison_summary': _generate_comparison_summary(
            period1_analysis, period2_analysis
        )
    }


def _generate_comparison_summary(
    period1: Dict[str, Any],
    period2: Dict[str, Any]
) -> str:
    """Genera resumen comparativo entre dos períodos."""
    if not period1.get('trends') or not period2.get('trends'):
        return 'Datos insuficientes para comparación.'

    summaries = []

    for metric in ['weight_kg', 'body_fat_percentage', 'muscle_mass_kg']:
        if metric in period1['trends'] and metric in period2['trends']:
            trend1 = period1['trends'][metric]
            trend2 = period2['trends'][metric]

            velocity1 = trend1.get('velocity_per_week', 0)
            velocity2 = trend2.get('velocity_per_week', 0)

            if abs(velocity2) > abs(velocity1):
                summaries.append(
                    f"{metric}: Ritmo acelerado en período reciente"
                )
            elif abs(velocity2) < abs(velocity1):
                summaries.append(
                    f"{metric}: Ritmo desacelerado en período reciente"
                )

    return '; '.join(summaries) if summaries else 'Ritmo similar en ambos períodos.'
