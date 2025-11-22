"""
Módulo de Cálculos Antropométricos

Implementa fórmulas científicas validadas para:
- Índice de Masa Corporal (IMC)
- Composición corporal (% grasa, masa grasa, masa muscular)
- Somatotipo Heath-Carter
- Índices de salud (ICC, ICE)

Referencias:
- Jackson, A.S. & Pollock, M.L. (1978). Generalized equations for predicting body density of men.
- Durnin, J.V.G.A. & Womersley, J. (1974). Body fat assessed from total body density.
- Heath, B.H. & Carter, J.E.L. (1967). A modified somatotype method.
- Slaughter et al. (1988). Skinfold equations for estimation of body fatness in children and youth.
- ISAK Manual (2001). International Standards for Anthropometric Assessment.
"""

import math
from typing import Optional, Dict, Any, Tuple
from decimal import Decimal
from loguru import logger


# ============================================================================
# 1. ÍNDICE DE MASA CORPORAL (IMC)
# ============================================================================

def calculate_bmi(weight_kg: float, height_cm: float) -> Optional[float]:
    """
    Calcula el Índice de Masa Corporal (IMC).

    Fórmula: IMC = peso (kg) / altura (m)²

    Args:
        weight_kg: Peso en kilogramos
        height_cm: Altura en centímetros

    Returns:
        IMC redondeado a 2 decimales, o None si datos inválidos

    Example:
        >>> calculate_bmi(75.0, 175.0)
        24.49
    """
    if not weight_kg or not height_cm or height_cm <= 0 or weight_kg <= 0:
        return None

    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    return round(bmi, 2)


def get_bmi_category(bmi: float) -> str:
    """
    Clasifica el IMC según criterios de la OMS.

    Args:
        bmi: Índice de Masa Corporal

    Returns:
        Categoría: "underweight", "normal", "overweight", "obese_1", "obese_2", "obese_3"
    """
    if bmi < 18.5:
        return "underweight"
    elif bmi < 25.0:
        return "normal"
    elif bmi < 30.0:
        return "overweight"
    elif bmi < 35.0:
        return "obese_1"
    elif bmi < 40.0:
        return "obese_2"
    else:
        return "obese_3"


# ============================================================================
# 2. COMPOSICIÓN CORPORAL - FÓRMULAS DE DENSIDAD CORPORAL
# ============================================================================

def calculate_body_density_jp7(
    chest_mm: float,
    abdominal_mm: float,
    thigh_mm: float,
    triceps_mm: float,
    subscapular_mm: float,
    suprailiac_mm: float,
    midaxillary_mm: float,
    age: int,
    gender: str
) -> Optional[float]:
    """
    Densidad corporal usando Jackson-Pollock 7 pliegues.

    Ecuación más precisa para deportistas y población general.

    Args:
        chest_mm: Pliegue pectoral (mm)
        abdominal_mm: Pliegue abdominal (mm)
        thigh_mm: Pliegue muslo anterior (mm)
        triceps_mm: Pliegue tricipital (mm)
        subscapular_mm: Pliegue subescapular (mm)
        suprailiac_mm: Pliegue suprailiaco (mm)
        midaxillary_mm: Pliegue axilar medio (mm)
        age: Edad en años
        gender: 'M' o 'F'

    Returns:
        Densidad corporal (g/cm³)

    Reference:
        Jackson, A.S. & Pollock, M.L. (1978). British Journal of Nutrition, 40(3), 497-504.
    """
    # Validar que tengamos todos los pliegues
    skinfolds = [chest_mm, abdominal_mm, thigh_mm, triceps_mm,
                 subscapular_mm, suprailiac_mm, midaxillary_mm]

    if any(sf is None or sf <= 0 for sf in skinfolds):
        return None

    sum_7_skinfolds = sum(skinfolds)

    if gender.upper() == 'M':
        # Hombres
        density = (1.112 - 0.00043499 * sum_7_skinfolds +
                  0.00000055 * (sum_7_skinfolds ** 2) -
                  0.00028826 * age)
    elif gender.upper() == 'F':
        # Mujeres
        density = (1.097 - 0.00046971 * sum_7_skinfolds +
                  0.00000056 * (sum_7_skinfolds ** 2) -
                  0.00012828 * age)
    else:
        return None

    return round(density, 5)


def calculate_body_density_jp3(
    chest_mm: Optional[float],
    abdominal_mm: Optional[float],
    thigh_mm: Optional[float],
    triceps_mm: Optional[float],
    suprailiac_mm: Optional[float],
    age: int,
    gender: str
) -> Optional[float]:
    """
    Densidad corporal usando Jackson-Pollock 3 pliegues (simplificado).

    Para hombres: pectoral, abdominal, muslo
    Para mujeres: tríceps, suprailiaco, muslo

    Args:
        chest_mm: Pliegue pectoral (mm) - solo hombres
        abdominal_mm: Pliegue abdominal (mm) - solo hombres
        thigh_mm: Pliegue muslo anterior (mm) - ambos
        triceps_mm: Pliegue tricipital (mm) - solo mujeres
        suprailiac_mm: Pliegue suprailiaco (mm) - solo mujeres
        age: Edad en años
        gender: 'M' o 'F'

    Returns:
        Densidad corporal (g/cm³)
    """
    if gender.upper() == 'M':
        # Hombres: pectoral, abdominal, muslo
        if not all([chest_mm, abdominal_mm, thigh_mm]):
            return None
        sum_3 = chest_mm + abdominal_mm + thigh_mm
        density = 1.10938 - 0.0008267 * sum_3 + 0.0000016 * (sum_3 ** 2) - 0.0002574 * age
    elif gender.upper() == 'F':
        # Mujeres: tríceps, suprailiaco, muslo
        if not all([triceps_mm, suprailiac_mm, thigh_mm]):
            return None
        sum_3 = triceps_mm + suprailiac_mm + thigh_mm
        density = 1.0994921 - 0.0009929 * sum_3 + 0.0000023 * (sum_3 ** 2) - 0.0001392 * age
    else:
        return None

    return round(density, 5)


def body_fat_from_density(density: float) -> float:
    """
    Convierte densidad corporal a porcentaje de grasa.

    Fórmula de Siri (1961): % Grasa = (495 / Densidad) - 450

    Args:
        density: Densidad corporal en g/cm³

    Returns:
        Porcentaje de grasa corporal
    """
    if density <= 0:
        return 0.0

    body_fat = (495 / density) - 450
    return round(max(0, body_fat), 2)


def calculate_body_fat_percentage(
    weight_kg: float,
    age: int,
    gender: str,
    # Pliegues (todos opcionales)
    chest_mm: Optional[float] = None,
    abdominal_mm: Optional[float] = None,
    thigh_mm: Optional[float] = None,
    triceps_mm: Optional[float] = None,
    subscapular_mm: Optional[float] = None,
    suprailiac_mm: Optional[float] = None,
    midaxillary_mm: Optional[float] = None,
    calf_mm: Optional[float] = None,
    biceps_mm: Optional[float] = None
) -> Optional[float]:
    """
    Calcula el porcentaje de grasa corporal usando el mejor método disponible.

    Prioridad:
    1. Jackson-Pollock 7 pliegues (más preciso)
    2. Jackson-Pollock 3 pliegues (simplificado)
    3. None (insuficientes datos)

    Args:
        weight_kg: Peso en kg
        age: Edad en años
        gender: 'M' o 'F'
        *_mm: Pliegues cutáneos en milímetros (opcionales)

    Returns:
        Porcentaje de grasa corporal, o None si datos insuficientes
    """
    # Intentar JP7 primero (más preciso)
    if all([chest_mm, abdominal_mm, thigh_mm, triceps_mm,
            subscapular_mm, suprailiac_mm, midaxillary_mm]):
        density = calculate_body_density_jp7(
            chest_mm, abdominal_mm, thigh_mm, triceps_mm,
            subscapular_mm, suprailiac_mm, midaxillary_mm,
            age, gender
        )
        if density:
            return body_fat_from_density(density)

    # Intentar JP3 (simplificado)
    density = calculate_body_density_jp3(
        chest_mm, abdominal_mm, thigh_mm,
        triceps_mm, suprailiac_mm,
        age, gender
    )
    if density:
        return body_fat_from_density(density)

    return None


# ============================================================================
# 3. COMPOSICIÓN CORPORAL - MASAS DERIVADAS
# ============================================================================

def calculate_fat_mass(weight_kg: float, body_fat_percentage: float) -> float:
    """
    Calcula la masa grasa en kilogramos.

    Args:
        weight_kg: Peso corporal total
        body_fat_percentage: % de grasa corporal

    Returns:
        Masa grasa en kg
    """
    if not weight_kg or body_fat_percentage is None:
        return 0.0

    fat_mass = weight_kg * (body_fat_percentage / 100)
    return round(fat_mass, 2)


def calculate_lean_mass(weight_kg: float, fat_mass_kg: float) -> float:
    """
    Calcula la masa magra (libre de grasa).

    Args:
        weight_kg: Peso corporal total
        fat_mass_kg: Masa grasa

    Returns:
        Masa magra en kg
    """
    if not weight_kg or fat_mass_kg is None:
        return 0.0

    lean_mass = weight_kg - fat_mass_kg
    return round(max(0, lean_mass), 2)


def calculate_muscle_mass_percentage(body_fat_percentage: float) -> float:
    """
    Estima el porcentaje de masa muscular.

    Aproximación: % Músculo ≈ (100 - % Grasa) × 0.5
    Nota: Es una estimación. La masa magra incluye huesos, órganos, agua, etc.

    Args:
        body_fat_percentage: % de grasa corporal

    Returns:
        Porcentaje estimado de masa muscular
    """
    if body_fat_percentage is None:
        return 0.0

    # Masa magra total
    lean_percentage = 100 - body_fat_percentage

    # Aproximar que ~50% de la masa magra es músculo esquelético
    muscle_percentage = lean_percentage * 0.5

    return round(muscle_percentage, 2)


# ============================================================================
# 4. SOMATOTIPO HEATH-CARTER
# ============================================================================

def calculate_endomorphy(
    triceps_mm: float,
    subscapular_mm: float,
    suprailiac_mm: float,
    height_cm: float
) -> Optional[float]:
    """
    Calcula el componente de Endomorfia (adiposidad).

    Args:
        triceps_mm: Pliegue tricipital
        subscapular_mm: Pliegue subescapular
        suprailiac_mm: Pliegue suprailiaco
        height_cm: Estatura

    Returns:
        Puntuación de endomorfia (0-10+)

    Reference:
        Heath & Carter (1967)
    """
    if any(x is None or x <= 0 for x in [triceps_mm, subscapular_mm, suprailiac_mm, height_cm]):
        return None

    # Suma de 3 pliegues
    sum_3_skinfolds = triceps_mm + subscapular_mm + suprailiac_mm

    # Corrección por estatura (170.18 cm es la estatura de referencia)
    height_correction = 170.18 / height_cm
    corrected_sum = sum_3_skinfolds * height_correction

    # Fórmula de endomorfia
    endomorphy = -0.7182 + 0.1451 * corrected_sum - 0.00068 * (corrected_sum ** 2) + 0.0000014 * (corrected_sum ** 3)

    return round(max(0.5, endomorphy), 2)


def calculate_mesomorphy(
    humerus_breadth_mm: float,
    femur_breadth_mm: float,
    arm_flexed_circ_cm: float,
    calf_circ_cm: float,
    triceps_mm: float,
    calf_mm: float,
    height_cm: float
) -> Optional[float]:
    """
    Calcula el componente de Mesomorfia (músculo-esqueleto).

    Args:
        humerus_breadth_mm: Diámetro biepicondilar del húmero
        femur_breadth_mm: Diámetro bicondilar del fémur
        arm_flexed_circ_cm: Circunferencia de brazo flexionado
        calf_circ_cm: Circunferencia de pantorrilla
        triceps_mm: Pliegue tricipital
        calf_mm: Pliegue de pantorrilla
        height_cm: Estatura

    Returns:
        Puntuación de mesomorfia (0-10+)
    """
    if any(x is None or x <= 0 for x in [humerus_breadth_mm, femur_breadth_mm,
                                          arm_flexed_circ_cm, calf_circ_cm,
                                          triceps_mm, calf_mm, height_cm]):
        return None

    # Convertir diámetros a cm
    humerus_cm = humerus_breadth_mm / 10
    femur_cm = femur_breadth_mm / 10

    # Circunferencias corregidas (restar pliegues)
    arm_corrected = arm_flexed_circ_cm - (triceps_mm / 10)
    calf_corrected = calf_circ_cm - (calf_mm / 10)

    # Fórmula de mesomorfia
    height_m = height_cm / 100
    mesomorphy = (0.858 * humerus_cm + 0.601 * femur_cm +
                  0.188 * arm_corrected + 0.161 * calf_corrected -
                  height_m * 0.131 + 4.5)

    return round(max(0.5, mesomorphy), 2)


def calculate_ectomorphy(weight_kg: float, height_cm: float) -> Optional[float]:
    """
    Calcula el componente de Ectomorfia (linealidad/delgadez).

    Args:
        weight_kg: Peso corporal
        height_cm: Estatura

    Returns:
        Puntuación de ectomorfia (0-10+)
    """
    if not weight_kg or not height_cm or height_cm <= 0 or weight_kg <= 0:
        return None

    # Índice Ponderal = estatura / ∛peso
    height_m = height_cm / 100
    ponderal_index = height_m / (weight_kg ** (1/3))

    # Fórmula de ectomorfia según Heath-Carter
    if ponderal_index >= 40.75:
        ectomorphy = 0.732 * ponderal_index - 28.58
    elif ponderal_index > 38.25:
        ectomorphy = 0.463 * ponderal_index - 17.63
    else:
        ectomorphy = 0.1

    return round(max(0.5, ectomorphy), 2)


def calculate_somatotype(
    weight_kg: float,
    height_cm: float,
    triceps_mm: Optional[float] = None,
    subscapular_mm: Optional[float] = None,
    suprailiac_mm: Optional[float] = None,
    calf_mm: Optional[float] = None,
    humerus_breadth_mm: Optional[float] = None,
    femur_breadth_mm: Optional[float] = None,
    arm_flexed_circ_cm: Optional[float] = None,
    calf_circ_cm: Optional[float] = None
) -> Dict[str, Optional[float]]:
    """
    Calcula el somatotipo completo Heath-Carter.

    Args:
        weight_kg: Peso corporal
        height_cm: Estatura
        triceps_mm: Pliegue tricipital
        subscapular_mm: Pliegue subescapular
        suprailiac_mm: Pliegue suprailiaco
        calf_mm: Pliegue pantorrilla
        humerus_breadth_mm: Diámetro húmero
        femur_breadth_mm: Diámetro fémur
        arm_flexed_circ_cm: Circunferencia brazo
        calf_circ_cm: Circunferencia pantorrilla

    Returns:
        Dict con endomorphy, mesomorphy, ectomorphy (None si datos insuficientes)
    """
    result = {
        'endomorphy': None,
        'mesomorphy': None,
        'ectomorphy': None
    }

    # Endomorfia (requiere 3 pliegues)
    if all([triceps_mm, subscapular_mm, suprailiac_mm, height_cm]):
        result['endomorphy'] = calculate_endomorphy(
            triceps_mm, subscapular_mm, suprailiac_mm, height_cm
        )

    # Mesomorfia (requiere diámetros, circunferencias, pliegues)
    if all([humerus_breadth_mm, femur_breadth_mm, arm_flexed_circ_cm,
            calf_circ_cm, triceps_mm, calf_mm, height_cm]):
        result['mesomorphy'] = calculate_mesomorphy(
            humerus_breadth_mm, femur_breadth_mm,
            arm_flexed_circ_cm, calf_circ_cm,
            triceps_mm, calf_mm, height_cm
        )

    # Ectomorfia (solo requiere peso y estatura)
    result['ectomorphy'] = calculate_ectomorphy(weight_kg, height_cm)

    return result


# ============================================================================
# 5. ÍNDICES DE SALUD
# ============================================================================

def calculate_waist_hip_ratio(
    waist_cm: float,
    hip_cm: float
) -> Optional[float]:
    """
    Calcula el Índice Cintura-Cadera (ICC).

    Indicador de distribución de grasa y riesgo cardiovascular.

    Args:
        waist_cm: Circunferencia de cintura
        hip_cm: Circunferencia de cadera

    Returns:
        ICC (Waist-Hip Ratio)

    Interpretación:
        Hombres: >0.90 = riesgo alto
        Mujeres: >0.85 = riesgo alto
    """
    if not waist_cm or not hip_cm or hip_cm <= 0:
        return None

    whr = waist_cm / hip_cm
    return round(whr, 3)


def calculate_waist_height_ratio(
    waist_cm: float,
    height_cm: float
) -> Optional[float]:
    """
    Calcula el Índice Cintura-Estatura (ICE).

    Mejor predictor de riesgo metabólico que IMC.

    Args:
        waist_cm: Circunferencia de cintura
        height_cm: Estatura

    Returns:
        ICE (Waist-Height Ratio)

    Interpretación:
        <0.5 = saludable
        0.5-0.6 = precaución
        >0.6 = riesgo alto
    """
    if not waist_cm or not height_cm or height_cm <= 0:
        return None

    whr = waist_cm / height_cm
    return round(whr, 3)


def get_cardiovascular_risk(
    waist_hip_ratio: Optional[float],
    waist_height_ratio: Optional[float],
    gender: str
) -> str:
    """
    Evalúa el riesgo cardiovascular basado en índices.

    Args:
        waist_hip_ratio: ICC
        waist_height_ratio: ICE
        gender: 'M' o 'F'

    Returns:
        "low", "moderate", "high", "very_high"
    """
    risk_level = "unknown"

    # Evaluar ICC
    if waist_hip_ratio:
        if gender.upper() == 'M':
            if waist_hip_ratio > 0.95:
                return "very_high"
            elif waist_hip_ratio > 0.90:
                risk_level = "high"
            elif waist_hip_ratio > 0.85:
                risk_level = "moderate"
            else:
                risk_level = "low"
        else:  # Mujer
            if waist_hip_ratio > 0.90:
                return "very_high"
            elif waist_hip_ratio > 0.85:
                risk_level = "high"
            elif waist_hip_ratio > 0.80:
                risk_level = "moderate"
            else:
                risk_level = "low"

    # Evaluar ICE (más estricto)
    if waist_height_ratio:
        if waist_height_ratio > 0.6:
            return "very_high"
        elif waist_height_ratio > 0.55:
            if risk_level in ["low", "unknown"]:
                risk_level = "high"
        elif waist_height_ratio > 0.5:
            if risk_level in ["low", "unknown"]:
                risk_level = "moderate"

    return risk_level if risk_level != "unknown" else "low"


# ============================================================================
# 6. FUNCIÓN PRINCIPAL DE CÁLCULO COMPLETO
# ============================================================================

def calculate_all_metrics(measurement_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula todas las métricas antropométricas disponibles.

    Args:
        measurement_data: Dict con todos los campos de BodyMeasurement

    Returns:
        Dict con todos los campos calculados

    Example:
        >>> data = {
        ...     'weight_kg': 75.0,
        ...     'height_cm': 175.0,
        ...     'age': 30,
        ...     'gender': 'M',
        ...     'triceps_skinfold_mm': 12.0,
        ...     # ... más campos
        ... }
        >>> results = calculate_all_metrics(data)
        >>> results['bmi']
        24.49
    """
    results = {}

    # Extraer campos básicos
    weight_kg = float(measurement_data.get('weight_kg', 0))
    height_cm = float(measurement_data.get('height_cm') or 0)
    age = int(measurement_data.get('age', 0))
    gender = measurement_data.get('gender', 'M')

    # 1. IMC
    if weight_kg and height_cm:
        results['bmi'] = calculate_bmi(weight_kg, height_cm)
        results['bmi_category'] = get_bmi_category(results['bmi']) if results['bmi'] else None

    # 2. Composición Corporal
    body_fat = calculate_body_fat_percentage(
        weight_kg=weight_kg,
        age=age,
        gender=gender,
        chest_mm=measurement_data.get('chest_skinfold_mm'),
        abdominal_mm=measurement_data.get('abdominal_skinfold_mm'),
        thigh_mm=measurement_data.get('thigh_skinfold_mm'),
        triceps_mm=measurement_data.get('triceps_skinfold_mm'),
        subscapular_mm=measurement_data.get('subscapular_skinfold_mm'),
        suprailiac_mm=measurement_data.get('suprailiac_skinfold_mm'),
        midaxillary_mm=measurement_data.get('midaxillary_skinfold_mm'),
        calf_mm=measurement_data.get('calf_skinfold_mm'),
        biceps_mm=measurement_data.get('biceps_skinfold_mm')
    )

    if body_fat is not None:
        results['body_fat_percentage'] = body_fat
        results['fat_mass_kg'] = calculate_fat_mass(weight_kg, body_fat)
        results['muscle_mass_kg'] = calculate_lean_mass(weight_kg, results['fat_mass_kg'])
        results['muscle_mass_percentage'] = calculate_muscle_mass_percentage(body_fat)

    # 3. Somatotipo
    somatotype = calculate_somatotype(
        weight_kg=weight_kg,
        height_cm=height_cm,
        triceps_mm=measurement_data.get('triceps_skinfold_mm'),
        subscapular_mm=measurement_data.get('subscapular_skinfold_mm'),
        suprailiac_mm=measurement_data.get('suprailiac_skinfold_mm'),
        calf_mm=measurement_data.get('calf_skinfold_mm'),
        humerus_breadth_mm=measurement_data.get('humerus_breadth_mm'),
        femur_breadth_mm=measurement_data.get('femur_breadth_mm'),
        arm_flexed_circ_cm=measurement_data.get('arm_flexed_circumference_cm'),
        calf_circ_cm=measurement_data.get('calf_circumference_cm')
    )
    results.update(somatotype)

    # 4. Índices de Salud
    waist_cm = measurement_data.get('waist_circumference_cm')
    hip_cm = measurement_data.get('hip_circumference_cm')

    if waist_cm and hip_cm:
        results['waist_hip_ratio'] = calculate_waist_hip_ratio(waist_cm, hip_cm)

    if waist_cm and height_cm:
        results['waist_height_ratio'] = calculate_waist_height_ratio(waist_cm, height_cm)

    if results.get('waist_hip_ratio') or results.get('waist_height_ratio'):
        results['cardiovascular_risk'] = get_cardiovascular_risk(
            results.get('waist_hip_ratio'),
            results.get('waist_height_ratio'),
            gender
        )

    logger.info(
        f"Calculated metrics for {gender} {age}y {weight_kg}kg {height_cm}cm: "
        f"BMI={results.get('bmi')}, BF%={results.get('body_fat_percentage')}"
    )

    return results
