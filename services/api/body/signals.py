"""
Django Signals para Procesamiento Automático de Mediciones Corporales

Conecta eventos del modelo con tareas asíncronas de Celery:
- post_save de BodyMeasurement → calculate_body_composition
- post_save de BodyMeasurement → vectorize_body_measurement (si completa)
- post_save de NutritionPlan → vectorize_nutrition_plan (futuro)
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from loguru import logger

from .models import BodyMeasurement, NutritionPlan


# ============================================================================
# BODY MEASUREMENT SIGNALS
# ============================================================================

@receiver(post_save, sender=BodyMeasurement)
def process_new_measurement(sender, instance, created, **kwargs):
    """
    Procesa automáticamente una nueva medición corporal.

    Al crear/actualizar un BodyMeasurement:
    1. Dispara cálculo de composición corporal (IMC, % grasa, somatotipo, etc.)
    2. Si la medición está completa, dispara vectorización para RAG

    Args:
        sender: Clase BodyMeasurement
        instance: Instancia del modelo
        created: True si es una creación nueva
        **kwargs: Argumentos adicionales de Django
    """
    # Solo procesar si es nueva o si se actualizaron campos relevantes
    if created or _should_recalculate(instance, kwargs):
        logger.info(
            f"📊 Processing body measurement: id={instance.id} user={instance.auth_user_id}"
        )

        try:
            # Importar Celery task
            from celery import chain
            from vectosvc.worker.body_tasks import (
                calculate_body_composition,
                vectorize_body_measurement
            )

            # Preparar datos para la tarea
            measurement_data = _extract_measurement_data(instance)

            # Disparar cálculos (tarea asíncrona)
            calc_task = calculate_body_composition.signature(
                args=[str(instance.id), measurement_data],
                immutable=True
            )

            # Si queremos vectorizar después, podemos encadenar tareas
            # Pero primero esperemos a tener los cálculos
            calc_task.apply_async()

            logger.info(
                f"✅ Triggered calculation for measurement {instance.id}"
            )

        except ImportError:
            logger.warning(
                "Celery not available, skipping async calculation. "
                "Install Celery or calculate manually."
            )
        except Exception as e:
            logger.error(
                f"❌ Failed to trigger calculation for measurement {instance.id}: {e}",
                exc_info=True
            )


def _should_recalculate(instance: BodyMeasurement, kwargs: dict) -> bool:
    """
    Determina si se debe recalcular la composición corporal.

    Args:
        instance: BodyMeasurement instance
        kwargs: Signal kwargs (incluye update_fields si viene de save())

    Returns:
        True si se debe recalcular
    """
    # Si es creación nueva, siempre calcular
    if kwargs.get('created', False):
        return True

    # Si se actualizaron campos específicos, recalcular
    update_fields = kwargs.get('update_fields')
    if update_fields:
        # Campos que deberían disparar recálculo
        trigger_fields = {
            'weight_kg',
            'height_cm',
            'triceps_skinfold_mm',
            'subscapular_skinfold_mm',
            'suprailiac_skinfold_mm',
            'abdominal_skinfold_mm',
            'thigh_skinfold_mm',
            'calf_skinfold_mm',
            'waist_circumference_cm',
            'hip_circumference_cm',
            'arm_flexed_circumference_cm',
            'calf_circumference_cm',
            'humerus_breadth_mm',
            'femur_breadth_mm',
        }

        return bool(set(update_fields) & trigger_fields)

    # Por defecto, recalcular
    return True


def _extract_measurement_data(instance: BodyMeasurement) -> dict:
    """
    Extrae datos de la medición para enviar a Celery.

    Args:
        instance: BodyMeasurement instance

    Returns:
        Dict con todos los campos necesarios para cálculos
    """
    # Obtener edad y género del usuario (necesarios para fórmulas)
    # TODO: Implementar lookup a tabla de usuarios o agregar campos al modelo
    # Por ahora, usar valores por defecto o desde metadata
    age = 30  # TODO: Obtener de auth_user o perfil
    gender = 'M'  # TODO: Obtener de auth_user o perfil

    return {
        # Datos básicos
        'weight_kg': float(instance.weight_kg) if instance.weight_kg else None,
        'height_cm': float(instance.height_cm) if instance.height_cm else None,
        'age': age,
        'gender': gender,

        # Pliegues cutáneos
        'triceps_skinfold_mm': float(instance.triceps_skinfold_mm) if instance.triceps_skinfold_mm else None,
        'biceps_skinfold_mm': float(instance.biceps_skinfold_mm) if instance.biceps_skinfold_mm else None,
        'subscapular_skinfold_mm': float(instance.subscapular_skinfold_mm) if instance.subscapular_skinfold_mm else None,
        'suprailiac_skinfold_mm': float(instance.suprailiac_skinfold_mm) if instance.suprailiac_skinfold_mm else None,
        'abdominal_skinfold_mm': float(instance.abdominal_skinfold_mm) if instance.abdominal_skinfold_mm else None,
        'thigh_skinfold_mm': float(instance.thigh_skinfold_mm) if instance.thigh_skinfold_mm else None,
        'calf_skinfold_mm': float(instance.calf_skinfold_mm) if instance.calf_skinfold_mm else None,

        # Circunferencias
        'waist_circumference_cm': float(instance.waist_circumference_cm) if instance.waist_circumference_cm else None,
        'hip_circumference_cm': float(instance.hip_circumference_cm) if instance.hip_circumference_cm else None,
        'arm_relaxed_circumference_cm': float(instance.arm_relaxed_circumference_cm) if instance.arm_relaxed_circumference_cm else None,
        'arm_flexed_circumference_cm': float(instance.arm_flexed_circumference_cm) if instance.arm_flexed_circumference_cm else None,
        'calf_circumference_cm': float(instance.calf_circumference_cm) if instance.calf_circumference_cm else None,
        'thigh_circumference_cm': float(instance.thigh_circumference_cm) if instance.thigh_circumference_cm else None,

        # Diámetros óseos
        'humerus_breadth_mm': float(instance.humerus_breadth_mm) if instance.humerus_breadth_mm else None,
        'femur_breadth_mm': float(instance.femur_breadth_mm) if instance.femur_breadth_mm else None,
        'wrist_breadth_mm': float(instance.wrist_breadth_mm) if instance.wrist_breadth_mm else None,

        # Contexto
        'protocol': instance.protocol,
        'patient_type': instance.patient_type,
        'recorded_at': instance.recorded_at.isoformat() if instance.recorded_at else None,
    }


@receiver(post_save, sender=BodyMeasurement)
def update_measurement_with_calculations(sender, instance, created, **kwargs):
    """
    Actualiza la medición con los resultados de los cálculos.

    Este signal se dispara DESPUÉS de que Celery complete los cálculos.
    La tarea Celery debe llamar a este endpoint o actualizar directamente.

    NOTA: En producción, esto debería ser un webhook o callback desde Celery,
    no un signal directo, para evitar bloqueos.
    """
    # Este es solo un placeholder para documentación
    # La actualización real se hace desde el view después de obtener resultado de Celery
    pass


# ============================================================================
# NUTRITION PLAN SIGNALS (Futuro - Fase 2)
# ============================================================================

@receiver(post_save, sender=NutritionPlan)
def process_new_nutrition_plan(sender, instance, created, **kwargs):
    """
    Vectoriza un plan nutricional para búsqueda semántica.

    Args:
        sender: Clase NutritionPlan
        instance: Instancia del modelo
        created: True si es nueva
        **kwargs: Argumentos adicionales
    """
    # Solo vectorizar planes asignados (no templates)
    if created and not instance.is_template and instance.auth_user_id:
        logger.info(
            f"📋 Processing nutrition plan: id={instance.id} user={instance.auth_user_id}"
        )

        try:
            # TODO: Implementar en Fase 2
            # from vectosvc.worker.body_tasks import vectorize_nutrition_plan
            # vectorize_nutrition_plan.delay(str(instance.id), str(instance.auth_user_id))

            logger.info(f"✅ Plan {instance.id} queued for vectorization (TODO)")

        except Exception as e:
            logger.error(
                f"❌ Failed to trigger vectorization for plan {instance.id}: {e}"
            )


# ============================================================================
# HELPER: CALLBACK FROM CELERY
# ============================================================================

def apply_calculated_fields(measurement_id: str, calculated_fields: dict) -> bool:
    """
    Aplica los campos calculados a la medición.

    Esta función debe ser llamada desde el view después de que Celery complete.

    Args:
        measurement_id: UUID de la medición
        calculated_fields: Dict con campos calculados

    Returns:
        True si se actualizó correctamente

    Example:
        >>> from body.signals import apply_calculated_fields
        >>> # Después de obtener resultado de Celery
        >>> task_result = celery_task.get(timeout=10)
        >>> if task_result['status'] == 'success':
        ...     apply_calculated_fields(
        ...         measurement_id=task_result['measurement_id'],
        ...         calculated_fields=task_result['calculated_fields']
        ...     )
    """
    try:
        measurement = BodyMeasurement.objects.get(id=measurement_id)

        # Actualizar campos calculados
        update_fields = []
        for field, value in calculated_fields.items():
            if hasattr(measurement, field) and value is not None:
                setattr(measurement, field, value)
                update_fields.append(field)

        if update_fields:
            # Usar update_fields para evitar disparar signals innecesarios
            measurement.save(update_fields=update_fields)

            logger.info(
                f"✅ Updated measurement {measurement_id} with {len(update_fields)} calculated fields"
            )
            return True
        else:
            logger.warning(f"No fields to update for measurement {measurement_id}")
            return False

    except BodyMeasurement.DoesNotExist:
        logger.error(f"Measurement {measurement_id} not found")
        return False
    except Exception as e:
        logger.error(f"Failed to update measurement {measurement_id}: {e}")
        return False
