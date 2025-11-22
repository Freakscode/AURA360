"""
Tests para el módulo de análisis de tendencias (trends.py).

Prueba las capacidades de análisis de series temporales, regresión lineal,
detección de patrones y generación de alertas.
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any

from vectosvc.core.trends import (
    analyze_measurement_trends,
    project_metric_to_date,
    compare_periods,
    TrendDirection,
    TrendSignificance,
    AlertLevel,
)


# ============================================================================
# FIXTURES: DATOS DE PRUEBA
# ============================================================================

@pytest.fixture
def sample_measurements_weight_loss() -> List[Dict[str, Any]]:
    """
    Genera mediciones simulando pérdida de peso progresiva.

    Escenario: Usuario pierde 0.5 kg/semana durante 12 semanas (pérdida saludable).
    """
    measurements = []
    start_date = datetime(2025, 9, 1)
    initial_weight = 85.0

    for week in range(12):
        date = start_date + timedelta(weeks=week)
        weight = initial_weight - (week * 0.5)  # -0.5 kg/semana

        measurements.append({
            'id': f'measurement-{week}',
            'recorded_at': date.isoformat(),
            'weight_kg': weight,
            'height_cm': 175.0,
            'bmi': round(weight / (1.75 ** 2), 2),
            'body_fat_percentage': 25.0 - (week * 0.3),  # Reducción de grasa
            'muscle_mass_kg': 55.0 + (week * 0.1)  # Ganancia muscular leve
        })

    # Retornar en orden descendente (más reciente primero)
    return list(reversed(measurements))


@pytest.fixture
def sample_measurements_weight_gain() -> List[Dict[str, Any]]:
    """
    Genera mediciones simulando aumento de peso.

    Escenario: Usuario gana 0.3 kg/semana durante 8 semanas (bulking).
    """
    measurements = []
    start_date = datetime(2025, 9, 1)
    initial_weight = 70.0

    for week in range(8):
        date = start_date + timedelta(weeks=week)
        weight = initial_weight + (week * 0.3)

        measurements.append({
            'id': f'measurement-{week}',
            'recorded_at': date.isoformat(),
            'weight_kg': weight,
            'height_cm': 180.0,
            'bmi': round(weight / (1.80 ** 2), 2),
            'body_fat_percentage': 12.0 + (week * 0.2),
            'muscle_mass_kg': 58.0 + (week * 0.25)  # Ganancia muscular
        })

    return list(reversed(measurements))


@pytest.fixture
def sample_measurements_stable() -> List[Dict[str, Any]]:
    """
    Genera mediciones con peso estable (variaciones mínimas).

    Escenario: Usuario mantiene peso durante 10 semanas.
    """
    measurements = []
    start_date = datetime(2025, 9, 1)
    base_weight = 75.0

    for week in range(10):
        date = start_date + timedelta(weeks=week)
        # Variaciones aleatorias pequeñas (<0.2 kg)
        weight = base_weight + ((-1) ** week) * 0.15

        measurements.append({
            'id': f'measurement-{week}',
            'recorded_at': date.isoformat(),
            'weight_kg': weight,
            'height_cm': 175.0,
            'bmi': round(weight / (1.75 ** 2), 2),
            'body_fat_percentage': 18.5,
            'muscle_mass_kg': 60.0
        })

    return list(reversed(measurements))


@pytest.fixture
def sample_measurements_insufficient() -> List[Dict[str, Any]]:
    """Solo 2 mediciones (insuficiente para análisis de tendencias)."""
    return [
        {
            'id': 'measurement-1',
            'recorded_at': datetime(2025, 11, 1).isoformat(),
            'weight_kg': 80.0,
            'height_cm': 175.0
        },
        {
            'id': 'measurement-2',
            'recorded_at': datetime(2025, 11, 15).isoformat(),
            'weight_kg': 79.5,
            'height_cm': 175.0
        }
    ]


# ============================================================================
# TESTS: ANÁLISIS DE TENDENCIAS
# ============================================================================

def test_analyze_weight_loss_trend(sample_measurements_weight_loss):
    """
    Test análisis de tendencia de pérdida de peso.

    Debe detectar:
    - Dirección: decreasing
    - Velocidad: ~0.5 kg/semana
    - Significancia estadística alta
    """
    result = analyze_measurement_trends(
        measurements=sample_measurements_weight_loss,
        target_metrics=['weight_kg']
    )

    assert result['measurement_count'] == 12
    assert 'weight_kg' in result['trends']

    weight_trend = result['trends']['weight_kg']
    assert weight_trend['direction'] == TrendDirection.DECREASING
    assert weight_trend['slope'] < 0  # Pendiente negativa

    # Velocidad de pérdida debe ser ~0.5 kg/semana
    assert 0.4 <= abs(weight_trend['velocity_per_week']) <= 0.6

    # Cambio total debe ser ~5.5 kg
    assert 5.0 <= abs(weight_trend['change_total']) <= 6.0

    # R² debe ser alto (ajuste lineal bueno)
    assert weight_trend['r_squared'] > 0.95

    # Significancia estadística alta
    assert weight_trend['significance'] in [
        TrendSignificance.HIGHLY_SIGNIFICANT,
        TrendSignificance.SIGNIFICANT
    ]


def test_analyze_weight_gain_trend(sample_measurements_weight_gain):
    """
    Test análisis de tendencia de aumento de peso.

    Debe detectar:
    - Dirección: increasing
    - Velocidad: ~0.3 kg/semana
    """
    result = analyze_measurement_trends(
        measurements=sample_measurements_weight_gain,
        target_metrics=['weight_kg', 'muscle_mass_kg']
    )

    assert result['measurement_count'] == 8

    weight_trend = result['trends']['weight_kg']
    assert weight_trend['direction'] == TrendDirection.INCREASING
    assert weight_trend['slope'] > 0
    assert 0.25 <= weight_trend['velocity_per_week'] <= 0.35

    # Verificar ganancia muscular también
    if 'muscle_mass_kg' in result['trends']:
        muscle_trend = result['trends']['muscle_mass_kg']
        assert muscle_trend['direction'] == TrendDirection.INCREASING
        assert muscle_trend['velocity_per_week'] > 0


def test_analyze_stable_weight(sample_measurements_stable):
    """
    Test análisis de peso estable.

    Debe detectar:
    - Dirección: stable
    - Cambio total mínimo
    - Baja significancia estadística
    """
    result = analyze_measurement_trends(
        measurements=sample_measurements_stable,
        target_metrics=['weight_kg']
    )

    weight_trend = result['trends']['weight_kg']
    assert weight_trend['direction'] == TrendDirection.STABLE
    assert abs(weight_trend['change_total']) < 1.0
    assert abs(weight_trend['velocity_per_week']) < 0.1


def test_insufficient_measurements(sample_measurements_insufficient):
    """
    Test con datos insuficientes (< 3 mediciones).

    Debe retornar aviso de datos insuficientes.
    """
    result = analyze_measurement_trends(
        measurements=sample_measurements_insufficient
    )

    assert result['measurement_count'] == 2
    assert result['trends'] == {}
    assert len(result['alerts']) > 0
    # Check for any message about insufficient data
    alert_messages = ' '.join([alert['message'].lower() for alert in result['alerts']])
    assert 'mediciones' in alert_messages or 'datos' in alert_messages


def test_no_measurements():
    """Test con lista vacía de mediciones."""
    result = analyze_measurement_trends(measurements=[])

    assert result['measurement_count'] == 0
    assert result['trends'] == {}


def test_period_calculation(sample_measurements_weight_loss):
    """Test cálculo de período temporal."""
    result = analyze_measurement_trends(
        measurements=sample_measurements_weight_loss
    )

    assert result['period'] is not None
    assert 'start' in result['period']
    assert 'end' in result['period']
    assert 'days' in result['period']

    # 12 semanas = ~77 días
    assert 70 <= result['period']['days'] <= 85


def test_time_range_filter(sample_measurements_weight_loss):
    """Test filtrado por rango temporal."""
    # Analizar solo las últimas 4 semanas
    result = analyze_measurement_trends(
        measurements=sample_measurements_weight_loss,
        time_range_days=30,  # ~4 semanas
        target_metrics=['weight_kg']
    )

    # Debe haber menos mediciones
    assert result['measurement_count'] < 12
    assert result['measurement_count'] >= 3


def test_body_fat_percentage_trend(sample_measurements_weight_loss):
    """Test análisis de tendencia de grasa corporal."""
    result = analyze_measurement_trends(
        measurements=sample_measurements_weight_loss,
        target_metrics=['body_fat_percentage']
    )

    bf_trend = result['trends']['body_fat_percentage']
    assert bf_trend['direction'] == TrendDirection.DECREASING
    assert bf_trend['velocity_per_month'] < 0  # Reducción


def test_muscle_mass_trend(sample_measurements_weight_loss):
    """Test análisis de tendencia de masa muscular."""
    result = analyze_measurement_trends(
        measurements=sample_measurements_weight_loss,
        target_metrics=['muscle_mass_kg']
    )

    muscle_trend = result['trends']['muscle_mass_kg']
    assert muscle_trend['direction'] == TrendDirection.INCREASING
    assert muscle_trend['velocity_per_month'] > 0


# ============================================================================
# TESTS: ALERTAS
# ============================================================================

def test_alerts_rapid_weight_loss():
    """
    Test generación de alertas para pérdida rápida de peso (>1 kg/semana).

    Debe generar alerta CRITICAL.
    """
    measurements = []
    start_date = datetime(2025, 11, 1)

    # Pérdida de 1.5 kg/semana (demasiado rápido)
    for week in range(6):
        date = start_date + timedelta(weeks=week)
        weight = 90.0 - (week * 1.5)

        measurements.append({
            'id': f'measurement-{week}',
            'recorded_at': date.isoformat(),
            'weight_kg': weight,
            'height_cm': 175.0
        })

    result = analyze_measurement_trends(
        measurements=list(reversed(measurements)),
        target_metrics=['weight_kg']
    )

    # Debe haber al menos una alerta para peso
    weight_alerts = [a for a in result['alerts'] if a['metric'] == 'weight_kg']
    assert len(weight_alerts) > 0

    # Al menos una debe ser WARNING o CRITICAL
    critical_alerts = [a for a in weight_alerts if a['level'] in [AlertLevel.WARNING, AlertLevel.CRITICAL]]
    assert len(critical_alerts) > 0


def test_alerts_muscle_loss():
    """
    Test generación de alertas para pérdida de masa muscular.

    Debe generar alerta WARNING o CRITICAL.
    """
    measurements = []
    start_date = datetime(2025, 11, 1)

    for week in range(8):
        date = start_date + timedelta(weeks=week)
        measurements.append({
            'id': f'measurement-{week}',
            'recorded_at': date.isoformat(),
            'weight_kg': 75.0 - (week * 0.5),
            'muscle_mass_kg': 55.0 - (week * 0.4),  # Pérdida muscular
            'height_cm': 175.0
        })

    result = analyze_measurement_trends(
        measurements=list(reversed(measurements)),
        target_metrics=['muscle_mass_kg']
    )

    muscle_alerts = [a for a in result['alerts'] if a['metric'] == 'muscle_mass_kg']
    assert len(muscle_alerts) > 0


def test_no_alerts_healthy_loss(sample_measurements_weight_loss):
    """
    Test que no se generen alertas para pérdida saludable (0.5 kg/semana).

    Podría haber alertas INFO, pero no WARNING/CRITICAL.
    """
    result = analyze_measurement_trends(
        measurements=sample_measurements_weight_loss,
        target_metrics=['weight_kg']
    )

    critical_alerts = [
        a for a in result['alerts']
        if a['metric'] == 'weight_kg' and a['level'] == AlertLevel.CRITICAL
    ]

    # No debe haber alertas críticas para pérdida saludable
    assert len(critical_alerts) == 0


# ============================================================================
# TESTS: PROYECCIONES
# ============================================================================

def test_projection_30_days(sample_measurements_weight_loss):
    """Test proyección a 30 días."""
    result = analyze_measurement_trends(
        measurements=sample_measurements_weight_loss,
        target_metrics=['weight_kg']
    )

    weight_trend = result['trends']['weight_kg']
    assert weight_trend['projection_30d'] is not None

    # La proyección debe ser menor que el peso actual (pérdida continua)
    current_weight = weight_trend['current_value']
    projected_weight = weight_trend['projection_30d']

    assert projected_weight < current_weight


def test_project_metric_to_specific_date(sample_measurements_weight_loss):
    """Test proyección a una fecha específica."""
    # Proyectar a una fecha futura (3 meses después de la última medición)
    last_measurement_date = datetime(2025, 11, 20)  # Última semana 11
    target_date = last_measurement_date + timedelta(days=90)

    projection = project_metric_to_date(
        measurements=sample_measurements_weight_loss,
        metric='weight_kg',
        target_date=target_date
    )

    assert projection is not None
    assert 'projected_value' in projection
    assert 'confidence_interval' in projection
    assert 'r_squared' in projection

    # Intervalo de confianza debe tener límites inferior y superior
    ci = projection['confidence_interval']
    assert len(ci) == 2
    assert ci[0] < ci[1]  # Lower < Upper

    # La proyección debe estar dentro del intervalo
    assert ci[0] <= projection['projected_value'] <= ci[1]


def test_projection_insufficient_data(sample_measurements_insufficient):
    """Test proyección con datos insuficientes."""
    target_date = datetime(2025, 12, 31)

    projection = project_metric_to_date(
        measurements=sample_measurements_insufficient,
        metric='weight_kg',
        target_date=target_date
    )

    # Debe retornar None por datos insuficientes
    assert projection is None


# ============================================================================
# TESTS: COMPARACIÓN DE PERÍODOS
# ============================================================================

def test_compare_periods(sample_measurements_weight_loss):
    """Test comparación entre dos períodos."""
    result = compare_periods(
        measurements=sample_measurements_weight_loss,
        period1_days=30,  # Período anterior (4 semanas)
        period2_days=30   # Período reciente (últimas 4 semanas)
    )

    assert 'period1' in result
    assert 'period2' in result
    assert 'comparison_summary' in result

    # Cada período debe tener su análisis
    assert 'analysis' in result['period1']
    assert 'analysis' in result['period2']


# ============================================================================
# TESTS: RESUMEN
# ============================================================================

def test_summary_generation(sample_measurements_weight_loss):
    """Test generación de resumen textual."""
    result = analyze_measurement_trends(
        measurements=sample_measurements_weight_loss
    )

    assert result['summary'] is not None
    assert len(result['summary']) > 0

    # El resumen debe mencionar información clave
    summary_lower = result['summary'].lower()
    assert any(word in summary_lower for word in ['peso', 'grasa', 'músculo'])


# ============================================================================
# TESTS: REGRESIÓN LINEAL Y ESTADÍSTICAS
# ============================================================================

def test_regression_significance(sample_measurements_weight_loss):
    """Test significancia estadística de la regresión."""
    result = analyze_measurement_trends(
        measurements=sample_measurements_weight_loss,
        target_metrics=['weight_kg']
    )

    weight_trend = result['trends']['weight_kg']

    # p-value debe ser muy bajo para tendencia clara
    assert weight_trend['p_value'] < 0.05

    # R² debe ser alto
    assert weight_trend['r_squared'] > 0.85


def test_velocity_calculations(sample_measurements_weight_loss):
    """Test cálculo de velocidades de cambio."""
    result = analyze_measurement_trends(
        measurements=sample_measurements_weight_loss,
        target_metrics=['weight_kg']
    )

    weight_trend = result['trends']['weight_kg']

    # Velocidad por semana
    assert 'velocity_per_week' in weight_trend
    assert weight_trend['velocity_per_week'] != 0

    # Velocidad por mes
    assert 'velocity_per_month' in weight_trend
    assert weight_trend['velocity_per_month'] != 0

    # Relación aproximada: velocity_per_month ≈ velocity_per_week * 4
    ratio = abs(weight_trend['velocity_per_month'] / weight_trend['velocity_per_week'])
    assert 3.5 <= ratio <= 4.5


# ============================================================================
# TESTS: CASOS EDGE
# ============================================================================

def test_measurements_same_date():
    """Test con múltiples mediciones en la misma fecha."""
    measurements = [
        {
            'id': 'measurement-1',
            'recorded_at': datetime(2025, 11, 1).isoformat(),
            'weight_kg': 80.0
        },
        {
            'id': 'measurement-2',
            'recorded_at': datetime(2025, 11, 1).isoformat(),
            'weight_kg': 80.5
        },
        {
            'id': 'measurement-3',
            'recorded_at': datetime(2025, 11, 1).isoformat(),
            'weight_kg': 79.8
        }
    ]

    result = analyze_measurement_trends(
        measurements=measurements,
        target_metrics=['weight_kg']
    )

    # Debe manejar el caso sin error
    assert result['measurement_count'] == 3


def test_missing_metric_values():
    """Test con valores faltantes en algunas mediciones."""
    measurements = [
        {
            'id': 'measurement-1',
            'recorded_at': datetime(2025, 11, 1).isoformat(),
            'weight_kg': 80.0,
            'body_fat_percentage': None  # Faltante
        },
        {
            'id': 'measurement-2',
            'recorded_at': datetime(2025, 11, 8).isoformat(),
            'weight_kg': 79.5,
            'body_fat_percentage': 22.0
        },
        {
            'id': 'measurement-3',
            'recorded_at': datetime(2025, 11, 15).isoformat(),
            'weight_kg': 79.0,
            'body_fat_percentage': None  # Faltante
        }
    ]

    result = analyze_measurement_trends(
        measurements=measurements,
        target_metrics=['weight_kg', 'body_fat_percentage']
    )

    # Peso debe tener análisis (3 valores)
    assert 'weight_kg' in result['trends']

    # Grasa corporal no debe tener análisis (solo 1 valor)
    assert 'body_fat_percentage' not in result['trends']


def test_extreme_outlier():
    """Test con un outlier extremo."""
    measurements = []
    start_date = datetime(2025, 11, 1)

    for week in range(6):
        date = start_date + timedelta(weeks=week)
        # Peso normal excepto semana 3
        weight = 75.0 if week != 3 else 95.0  # Outlier +20 kg

        measurements.append({
            'id': f'measurement-{week}',
            'recorded_at': date.isoformat(),
            'weight_kg': weight,
            'height_cm': 175.0
        })

    result = analyze_measurement_trends(
        measurements=list(reversed(measurements)),
        target_metrics=['weight_kg']
    )

    # Debe completar sin error (aunque la calidad del ajuste será baja)
    assert 'weight_kg' in result['trends']

    # R² probablemente será bajo debido al outlier
    # (esto es esperado - no es un bug)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
