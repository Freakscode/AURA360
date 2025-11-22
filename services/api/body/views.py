"""Vistas y ViewSets para exponer el dominio de hábitos corporales."""

from __future__ import annotations

import copy
import logging
import uuid

from django.conf import settings
from django.db import models as django_models
from rest_framework import status, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError

from users.permissions import SupabaseJWTRequiredPermission

from django.utils.crypto import constant_time_compare

from .models import BodyActivity, BodyMeasurement, NutritionLog, NutritionPlan, SleepLog
from .serializers import (
    BodyActivitySerializer,
    BodyMeasurementSerializer,
    BodyDashboardSnapshotSerializer,
    NutritionLogSerializer,
    NutritionPlanSerializer,
    NutritionPlanIngestCallbackSerializer,
    SleepLogSerializer,
)
from .services import (
    build_metadata_from_request,
    enqueue_nutrition_plan_ingestion,
    store_nutrition_plan_pdf,
    NutritionPlanIngestionError,
    NutritionPlanStorageError,
)


logger = logging.getLogger(__name__)


class _UserScopedMixin:
    """Helper para extraer el ID de usuario autenticado."""

    def _auth_user_id(self) -> str:
        request = getattr(self, 'request', None)
        user = getattr(request, 'user', None)
        if user and getattr(user, 'is_authenticated', False):
            return str(getattr(user, 'id'))
        raise PermissionDenied('Token Supabase inválido o faltante.')


class BodyMeasurementViewSet(_UserScopedMixin, viewsets.ModelViewSet):
    """
    CRUD para mediciones corporales (Peso, Talla, Pliegues).
    Permite a pacientes ver sus medidas y a profesionales gestionarlas.
    """
    serializer_class = BodyMeasurementSerializer
    queryset = BodyMeasurement.objects.all()
    permission_classes = (SupabaseJWTRequiredPermission,)
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        # Permitir a profesionales ver medidas de pacientes específicos
        target_user_id = self.request.query_params.get('user_id')
        if target_user_id:
             # TODO: Validar permisos (profesional -> paciente)
            return self.queryset.filter(auth_user_id=target_user_id)
        
        return super().get_queryset().filter(auth_user_id=self._auth_user_id())

    def perform_create(self, serializer):
        # Si se especifica un usuario destino, usarlo (para profesionales)
        target_user_id = self.request.data.get('auth_user_id')
        if target_user_id:
            # TODO: Validar que request.user sea profesional
            serializer.save(auth_user_id=target_user_id, measured_by=self.request.user.id)
        else:
            serializer.save(auth_user_id=self._auth_user_id())

    def perform_update(self, serializer):
        # Al actualizar, mantener el usuario original
        serializer.save()


class BodyActivityViewSet(_UserScopedMixin, viewsets.ModelViewSet):
    """CRUD de actividades físicas filtradas por usuario autenticado."""

    serializer_class = BodyActivitySerializer
    queryset = BodyActivity.objects.all()
    permission_classes = (SupabaseJWTRequiredPermission,)
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return super().get_queryset().filter(auth_user_id=self._auth_user_id())

    def perform_create(self, serializer):
        serializer.save(auth_user_id=self._auth_user_id())

    def perform_update(self, serializer):
        serializer.save(auth_user_id=self._auth_user_id())


class NutritionLogViewSet(_UserScopedMixin, viewsets.ModelViewSet):
    """CRUD para registros de nutrición."""

    serializer_class = NutritionLogSerializer
    queryset = NutritionLog.objects.all()
    permission_classes = (SupabaseJWTRequiredPermission,)
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return super().get_queryset().filter(auth_user_id=self._auth_user_id())

    def perform_create(self, serializer):
        serializer.save(auth_user_id=self._auth_user_id())

    def perform_update(self, serializer):
        serializer.save(auth_user_id=self._auth_user_id())


class SleepLogViewSet(_UserScopedMixin, viewsets.ModelViewSet):
    """CRUD para registros de sueño."""

    serializer_class = SleepLogSerializer
    queryset = SleepLog.objects.all()
    permission_classes = (SupabaseJWTRequiredPermission,)
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return super().get_queryset().filter(auth_user_id=self._auth_user_id())

    def perform_create(self, serializer):
        serializer.save(auth_user_id=self._auth_user_id())

    def perform_update(self, serializer):
        serializer.save(auth_user_id=self._auth_user_id())


class NutritionPlanViewSet(_UserScopedMixin, viewsets.ModelViewSet):
    """
    CRUD completo para planes nutricionales estructurados.
    
    Proporciona operaciones para crear, leer, actualizar y eliminar
    planes nutricionales del usuario autenticado. Incluye filtros
    para planes activos y vigentes.
    
    Endpoints:
    - GET /nutrition-plans/ - Lista todos los planes del usuario
    - GET /nutrition-plans/?active=true - Solo planes activos
    - GET /nutrition-plans/?valid=true - Solo planes vigentes
    - GET /nutrition-plans/{id}/ - Detalle de un plan específico
    - POST /nutrition-plans/ - Crear nuevo plan
    - PATCH /nutrition-plans/{id}/ - Actualizar plan
    - DELETE /nutrition-plans/{id}/ - Eliminar plan
    """
    
    serializer_class = NutritionPlanSerializer
    queryset = NutritionPlan.objects.all()
    permission_classes = (SupabaseJWTRequiredPermission,)
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    
    def get_queryset(self):
        """
        Filtra planes por usuario autenticado y parámetros opcionales.
        
        Query params:
        - active: true/false - Filtra por planes activos
        - valid: true/false - Filtra por planes vigentes (no expirados)
        - user_id: UUID - Filtra por usuario específico (para profesionales)
        """
        # Permitir filtrar por usuario específico si se proporciona user_id
        # Esto es útil para profesionales que ven planes de sus pacientes
        target_user_id = self.request.query_params.get('user_id')
        
        if target_user_id:
            # TODO: Validar permisos reales (ej. verificar relación de cuidado)
            queryset = self.queryset.filter(auth_user_id=target_user_id)
        else:
            queryset = super().get_queryset().filter(auth_user_id=self._auth_user_id())
        
        # Filtro por estado activo
        active = self.request.query_params.get('active')
        if active is not None:
            is_active = active.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_active=is_active)
        
        # Filtro por vigencia
        valid = self.request.query_params.get('valid')
        if valid is not None and valid.lower() in ('true', '1', 'yes'):
            from django.utils import timezone
            today = timezone.now().date()
            queryset = queryset.filter(
                is_active=True
            ).filter(
                django_models.Q(valid_until__isnull=True) | 
                django_models.Q(valid_until__gte=today)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        """Asigna el usuario al crear un plan."""
        # Verificar si se está creando para otro usuario (desde plan_data.subject.user_id)
        # Esto permite a profesionales crear planes para pacientes
        plan_data = serializer.validated_data.get('plan_data', {})
        subject_user_id = plan_data.get('subject', {}).get('user_id')
        
        # Guardar quién creó el plan (auditoría)
        created_by = self.request.user.id if self.request.user.is_authenticated else None

        if subject_user_id:
            # Usar el ID proporcionado en el payload
            serializer.save(auth_user_id=subject_user_id, created_by=created_by)
        else:
            # Fallback al usuario autenticado
            serializer.save(auth_user_id=self._auth_user_id(), created_by=created_by)
    
    def perform_update(self, serializer):
        """Mantiene el usuario autenticado al actualizar un plan."""
        serializer.save(auth_user_id=self._auth_user_id())


class BodyDashboardView(_UserScopedMixin, APIView):
    """
    Devuelve la instantánea consolidada para el panel Body.

    Incluye actividades recientes, registros de nutrición y sueño ordenados
    de forma descendente para facilitar la presentación en la app.
    """

    permission_classes = (SupabaseJWTRequiredPermission, IsAuthenticated)

    def get(self, request, *args, **kwargs) -> Response:
        auth_user_id = self._auth_user_id()
        activities = BodyActivity.objects.filter(auth_user_id=auth_user_id)
        nutrition = NutritionLog.objects.filter(auth_user_id=auth_user_id)
        sleep = SleepLog.objects.filter(auth_user_id=auth_user_id)

        payload = BodyDashboardSnapshotSerializer({
            'activities': BodyActivitySerializer(activities, many=True).data,
            'nutrition': NutritionLogSerializer(nutrition, many=True).data,
            'sleep': SleepLogSerializer(sleep, many=True).data,
        })
        return Response(payload.data, status=status.HTTP_200_OK)


class BodyMeasurementTrendsView(_UserScopedMixin, APIView):
    """
    Analiza tendencias de progreso en las mediciones corporales del usuario.

    Proporciona análisis estadístico de series temporales incluyendo:
    - Tendencias lineales (aumento/disminución/estable)
    - Velocidades de cambio (kg/semana, %/mes)
    - Significancia estadística (p-value, R²)
    - Proyecciones a 30 días
    - Alertas sobre cambios rápidos o preocupantes

    Query Parameters:
    - user_id: UUID (opcional, para profesionales que ven tendencias de pacientes)
    - days: int (opcional, rango temporal en días, default: todas las mediciones)
    - metrics: str (opcional, métricas específicas separadas por coma)

    Ejemplo:
        GET /api/body/measurements/trends/?days=90&metrics=weight_kg,body_fat_percentage
    """

    permission_classes = (SupabaseJWTRequiredPermission, IsAuthenticated)

    def get(self, request, *args, **kwargs) -> Response:
        """Obtiene el análisis de tendencias para el usuario."""

        # Determinar el usuario objetivo
        target_user_id = request.query_params.get('user_id')
        if target_user_id:
            # TODO: Validar permisos (profesional -> paciente)
            auth_user_id = target_user_id
        else:
            auth_user_id = self._auth_user_id()

        # Obtener parámetros opcionales
        time_range_days = request.query_params.get('days')
        if time_range_days:
            try:
                time_range_days = int(time_range_days)
                if time_range_days <= 0:
                    return Response(
                        {'detail': 'El parámetro "days" debe ser un número positivo.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except ValueError:
                return Response(
                    {'detail': 'El parámetro "days" debe ser un número entero.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Métricas específicas
        target_metrics = None
        metrics_param = request.query_params.get('metrics')
        if metrics_param:
            target_metrics = [m.strip() for m in metrics_param.split(',') if m.strip()]

        # Verificar si el análisis debe ser asíncrono o síncrono
        async_mode = request.query_params.get('async', 'false').lower() in ('true', '1', 'yes')

        if async_mode:
            # Modo asíncrono: enqueue tarea de Celery y retornar job_id
            try:
                from vectosvc.worker.body_tasks import analyze_progress_trends

                task = analyze_progress_trends.delay(
                    auth_user_id=auth_user_id,
                    time_range_days=time_range_days,
                    target_metrics=target_metrics
                )

                return Response(
                    {
                        'job_id': task.id,
                        'status': 'queued',
                        'detail': 'Análisis de tendencias encolado. Consulta el estado con /api/body/measurements/trends/status/{job_id}/'
                    },
                    status=status.HTTP_202_ACCEPTED
                )
            except ImportError:
                logger.warning("Celery not available, falling back to synchronous analysis")
                async_mode = False

        if not async_mode:
            # Modo síncrono: ejecutar análisis directamente
            try:
                from vectosvc.core.trends import analyze_measurement_trends

                # Obtener mediciones
                queryset = BodyMeasurement.objects.filter(
                    auth_user_id=auth_user_id
                ).order_by('-recorded_at')

                if time_range_days:
                    from datetime import datetime, timedelta
                    cutoff_date = datetime.now() - timedelta(days=time_range_days)
                    queryset = queryset.filter(recorded_at__gte=cutoff_date)

                # Convertir a lista de dicts
                measurements = []
                for m in queryset:
                    measurements.append({
                        'id': str(m.id),
                        'recorded_at': m.recorded_at.isoformat() if m.recorded_at else None,
                        'weight_kg': float(m.weight_kg) if m.weight_kg else None,
                        'height_cm': float(m.height_cm) if m.height_cm else None,
                        'bmi': float(m.bmi) if m.bmi else None,
                        'body_fat_percentage': float(m.body_fat_percentage) if m.body_fat_percentage else None,
                        'fat_mass_kg': float(m.fat_mass_kg) if m.fat_mass_kg else None,
                        'muscle_mass_kg': float(m.muscle_mass_kg) if m.muscle_mass_kg else None,
                        'waist_circumference_cm': float(m.waist_circumference_cm) if m.waist_circumference_cm else None,
                        'hip_circumference_cm': float(m.hip_circumference_cm) if m.hip_circumference_cm else None,
                        'waist_hip_ratio': float(m.waist_hip_ratio) if m.waist_hip_ratio else None,
                        'waist_height_ratio': float(m.waist_height_ratio) if m.waist_height_ratio else None,
                        'cardiovascular_risk': m.cardiovascular_risk
                    })

                # Analizar tendencias
                analysis = analyze_measurement_trends(
                    measurements=measurements,
                    time_range_days=time_range_days,
                    target_metrics=target_metrics
                )

                return Response(
                    {
                        'user_id': auth_user_id,
                        'status': 'success',
                        'analysis': analysis
                    },
                    status=status.HTTP_200_OK
                )

            except Exception as e:
                logger.error(f"Failed to analyze trends: {e}", exc_info=True)
                return Response(
                    {
                        'detail': f'Error al analizar tendencias: {str(e)}',
                        'error': 'analysis_error'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


class BodyMeasurementTrendsStatusView(APIView):
    """
    Consulta el estado de un trabajo de análisis de tendencias asíncrono.

    Endpoint:
        GET /api/body/measurements/trends/status/{job_id}/
    """

    permission_classes = (SupabaseJWTRequiredPermission, IsAuthenticated)

    def get(self, request, job_id: str) -> Response:
        """Obtiene el estado de un trabajo de análisis."""
        try:
            from celery.result import AsyncResult

            result = AsyncResult(job_id)

            if result.ready():
                if result.successful():
                    return Response(
                        {
                            'job_id': job_id,
                            'status': 'completed',
                            'result': result.get()
                        },
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {
                            'job_id': job_id,
                            'status': 'failed',
                            'error': str(result.info)
                        },
                        status=status.HTTP_200_OK
                    )
            else:
                return Response(
                    {
                        'job_id': job_id,
                        'status': 'processing',
                        'detail': 'El análisis está en progreso.'
                    },
                    status=status.HTTP_200_OK
                )

        except ImportError:
            return Response(
                {
                    'detail': 'Celery no está disponible.',
                    'error': 'celery_unavailable'
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return Response(
                {
                    'detail': 'Error al consultar el estado del trabajo.',
                    'error': 'status_check_error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NutritionAdherenceView(_UserScopedMixin, APIView):
    """
    Analiza la adherencia del usuario a su plan nutricional.

    Compara el plan prescrito con los registros reales de consumo.

    Query Parameters:
    - user_id: str (opcional, para profesionales que consultan datos de pacientes)
    - plan_id: UUID (opcional, si no se proporciona usa el plan activo)
    - days: int (opcional, días a analizar, default: 7)
    - async: bool (opcional, modo asíncrono, default: false)

    Ejemplo:
        GET /api/body/nutrition/adherence/?days=7
        GET /api/body/nutrition/adherence/?user_id=patient-uuid&days=14
        GET /api/body/nutrition/adherence/?plan_id=xxx&days=14&async=true
    """

    permission_classes = (SupabaseJWTRequiredPermission, IsAuthenticated)

    def get(self, request, *args, **kwargs) -> Response:
        """Obtiene el análisis de adherencia nutricional."""

        # Determinar el usuario objetivo (puede ser el usuario logueado o un paciente)
        target_user_id = request.query_params.get('user_id')
        requesting_user_id = self._auth_user_id()

        if target_user_id:
            # Verificar que el usuario logueado tenga permiso para ver datos de este usuario
            # (por ejemplo, que sea profesional con relación de cuidado activa)
            from users.models import CareRelationship
            has_permission = CareRelationship.objects.filter(
                professional__auth_user_id=requesting_user_id,
                patient__auth_user_id=target_user_id,
                status='active'
            ).exists()

            if not has_permission:
                return Response(
                    {'detail': 'No tienes permiso para ver los datos de este usuario.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            auth_user_id = target_user_id
        else:
            auth_user_id = requesting_user_id

        # Obtener parámetros
        plan_id = request.query_params.get('plan_id')
        days = request.query_params.get('days', '7')
        async_mode = request.query_params.get('async', 'false').lower() in ('true', '1', 'yes')

        # Validar días
        try:
            time_range_days = int(days)
            if time_range_days <= 0 or time_range_days > 90:
                return Response(
                    {'detail': 'El parámetro "days" debe estar entre 1 y 90.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {'detail': 'El parámetro "days" debe ser un número entero.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener plan activo si no se proporciona plan_id
        if not plan_id:
            active_plan = NutritionPlan.objects.filter(
                auth_user_id=auth_user_id,
                is_active=True
            ).order_by('-created_at').first()

            if not active_plan:
                return Response(
                    {
                        'detail': 'No tienes un plan nutricional activo.',
                        'error': 'no_active_plan'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            plan_id = str(active_plan.id)

        # Modo asíncrono
        if async_mode:
            try:
                from vectosvc.worker.body_tasks import analyze_nutrition_adherence

                task = analyze_nutrition_adherence.delay(
                    auth_user_id=auth_user_id,
                    nutrition_plan_id=plan_id,
                    time_range_days=time_range_days
                )

                return Response(
                    {
                        'job_id': task.id,
                        'status': 'queued',
                        'detail': 'Análisis de adherencia encolado.'
                    },
                    status=status.HTTP_202_ACCEPTED
                )
            except ImportError:
                logger.warning("Celery not available, falling back to sync")
                async_mode = False

        # Modo síncrono
        if not async_mode:
            try:
                from vectosvc.core.nutrition_adherence import analyze_nutrition_adherence as analyze

                # Obtener plan
                try:
                    plan = NutritionPlan.objects.get(id=plan_id, auth_user_id=auth_user_id)
                except NutritionPlan.DoesNotExist:
                    return Response(
                        {'detail': 'Plan nutricional no encontrado.'},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # Obtener logs
                from datetime import datetime, timedelta
                cutoff_date = datetime.now() - timedelta(days=time_range_days)
                logs = NutritionLog.objects.filter(
                    auth_user_id=auth_user_id,
                    logged_at__gte=cutoff_date
                ).order_by('-logged_at')

                # Convertir a dicts
                nutrition_plan_dict = {
                    'id': str(plan.id),
                    'title': plan.title,
                    'plan_data': plan.plan_data,
                    'daily_calories': plan.plan_data.get('nutrition', {}).get('daily_calories'),
                    'daily_protein_g': plan.plan_data.get('nutrition', {}).get('daily_protein_g'),
                    'daily_carbs_g': plan.plan_data.get('nutrition', {}).get('daily_carbs_g'),
                    'daily_fats_g': plan.plan_data.get('nutrition', {}).get('daily_fats_g')
                }

                nutrition_logs = [
                    {
                        'logged_at': log.logged_at.isoformat() if log.logged_at else None,
                        'total_calories': float(log.total_calories) if log.total_calories else 0,
                        'total_protein_g': float(log.total_protein_g) if log.total_protein_g else 0,
                        'total_carbs_g': float(log.total_carbs_g) if log.total_carbs_g else 0,
                        'total_fats_g': float(log.total_fats_g) if log.total_fats_g else 0,
                        'meal_type': log.meal_type
                    }
                    for log in logs
                ]

                # Analizar
                analysis = analyze(
                    nutrition_plan=nutrition_plan_dict,
                    nutrition_logs=nutrition_logs,
                    time_range_days=time_range_days
                )

                return Response(
                    {
                        'user_id': auth_user_id,
                        'plan_id': plan_id,
                        'status': 'success',
                        'analysis': analysis
                    },
                    status=status.HTTP_200_OK
                )

            except Exception as e:
                logger.error(f"Failed to analyze adherence: {e}", exc_info=True)
                return Response(
                    {
                        'detail': f'Error al analizar adherencia: {str(e)}',
                        'error': 'analysis_error'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


class AIRecommendationsView(_UserScopedMixin, APIView):
    """
    Genera recomendaciones personalizadas usando IA.

    Integra datos de tendencias, adherencia y mediciones para generar
    5 recomendaciones accionables usando LLM (Gemini).

    Query Parameters:
    - user_id: str (opcional, para profesionales que consultan datos de pacientes)
    - include_trends: bool (default: true)
    - include_adherence: bool (default: true)
    - days: int (default: 30, días de historia)
    - async: bool (default: false)

    Ejemplo:
        GET /api/body/recommendations/ai/
        GET /api/body/recommendations/ai/?user_id=patient-uuid&include_trends=true&days=90
    """

    permission_classes = (SupabaseJWTRequiredPermission, IsAuthenticated)

    def get(self, request, *args, **kwargs) -> Response:
        """Genera recomendaciones con IA."""

        # Determinar el usuario objetivo (puede ser el usuario logueado o un paciente)
        target_user_id = request.query_params.get('user_id')
        requesting_user_id = self._auth_user_id()

        if target_user_id:
            # Verificar que el usuario logueado tenga permiso para ver datos de este usuario
            from users.models import CareRelationship
            has_permission = CareRelationship.objects.filter(
                professional__auth_user_id=requesting_user_id,
                patient__auth_user_id=target_user_id,
                status='active'
            ).exists()

            if not has_permission:
                return Response(
                    {'detail': 'No tienes permiso para ver los datos de este usuario.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            auth_user_id = target_user_id
        else:
            auth_user_id = requesting_user_id

        # Obtener parámetros
        include_trends = request.query_params.get('include_trends', 'true').lower() in ('true', '1', 'yes')
        include_adherence = request.query_params.get('include_adherence', 'true').lower() in ('true', '1', 'yes')
        days = request.query_params.get('days', '30')
        async_mode = request.query_params.get('async', 'false').lower() in ('true', '1', 'yes')

        # Validar días
        try:
            time_range_days = int(days)
            if time_range_days <= 0 or time_range_days > 365:
                return Response(
                    {'detail': 'El parámetro "days" debe estar entre 1 y 365.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {'detail': 'El parámetro "days" debe ser un número entero.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Modo asíncrono
        if async_mode:
            try:
                from vectosvc.worker.body_tasks import generate_ai_recommendations

                task = generate_ai_recommendations.delay(
                    auth_user_id=auth_user_id,
                    include_trends=include_trends,
                    include_adherence=include_adherence,
                    time_range_days=time_range_days
                )

                return Response(
                    {
                        'job_id': task.id,
                        'status': 'queued',
                        'detail': 'Generación de recomendaciones encolada. Puede tardar 30-60 segundos.'
                    },
                    status=status.HTTP_202_ACCEPTED
                )
            except ImportError:
                logger.warning("Celery not available, falling back to sync")
                async_mode = False

        # Modo síncrono (puede tardar por llamada a LLM)
        if not async_mode:
            try:
                from vectosvc.worker.body_tasks import generate_ai_recommendations

                # Llamar directamente (sin .delay())
                result = generate_ai_recommendations(
                    auth_user_id=auth_user_id,
                    include_trends=include_trends,
                    include_adherence=include_adherence,
                    time_range_days=time_range_days
                )

                if result['status'] == 'success':
                    return Response(result, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {
                            'detail': 'Error al generar recomendaciones.',
                            'error': result.get('error', 'unknown')
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            except Exception as e:
                logger.error(f"Failed to generate AI recommendations: {e}", exc_info=True)
                return Response(
                    {
                        'detail': f'Error al generar recomendaciones: {str(e)}',
                        'error': 'generation_error'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


class NutritionPlanUploadView(_UserScopedMixin, APIView):
    """Recibe un PDF, lo almacena y delega su procesamiento al servicio vectorial."""

    permission_classes = (SupabaseJWTRequiredPermission, IsAuthenticated)
    parser_classes = (MultiPartParser,)

    def post(self, request, *args, **kwargs) -> Response:
        pdf_file = request.FILES.get('plan_pdf') or request.FILES.get('file')
        if pdf_file is None:
            return Response(
                {
                    'detail': 'Debes adjuntar el archivo del plan en el campo plan_pdf.',
                    'error': 'missing_file',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_types = getattr(settings, 'NUTRITION_PLAN_ALLOWED_FILE_TYPES', ['application/pdf'])
        if pdf_file.content_type not in allowed_types:
            return Response(
                {
                    'detail': 'El archivo debe ser un PDF válido.',
                    'error': 'invalid_content_type',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_size_mb = getattr(settings, 'NUTRITION_PLAN_MAX_UPLOAD_MB', 10)
        max_size_bytes = max_size_mb * 1024 * 1024
        if pdf_file.size > max_size_bytes:
            return Response(
                {
                    'detail': f'El PDF no puede exceder {max_size_mb} MB.',
                    'error': 'file_too_large',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        auth_user_id = self._auth_user_id()
        job_id = uuid.uuid4()

        uploaded_bytes = pdf_file.read()
        metadata = build_metadata_from_request(request.data)

        try:
            storage_result = store_nutrition_plan_pdf(
                uploaded_bytes=uploaded_bytes,
                content_type=pdf_file.content_type,
                auth_user_id=auth_user_id,
                job_id=job_id,
                original_name=getattr(pdf_file, 'name', None),
            )
        except NutritionPlanStorageError as exc:
            return Response(
                {
                    'detail': str(exc),
                    'error': 'storage_error',
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        try:
            enqueue_payload = enqueue_nutrition_plan_ingestion(
                job_id=job_id,
                auth_user_id=auth_user_id,
                storage_result=storage_result,
                metadata=metadata,
            )
        except NutritionPlanIngestionError as exc:
            return Response(
                {
                    'detail': str(exc),
                    'error': 'ingestion_error',
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        response_payload = {
            'job_id': str(job_id),
            'detail': 'Plan recibido. El procesamiento se realizará en segundo plano.',
            'storage': {
                'kind': storage_result.storage_kind,
                'path': storage_result.path,
                'bucket': storage_result.bucket,
                'public_url': storage_result.public_url,
            },
            'ingest_request': enqueue_payload.get('request'),
            'ingest_response': enqueue_payload.get('payload'),
        }

        return Response(response_payload, status=status.HTTP_202_ACCEPTED)


class NutritionPlanIngestCallbackView(APIView):
    """Recibe el JSON final del servicio vectorial y persiste el plan."""

    authentication_classes: tuple = ()
    permission_classes: tuple = ()
    serializer_class = NutritionPlanIngestCallbackSerializer

    def post(self, request, *args, **kwargs) -> Response:
        self._enforce_callback_token(request)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        plan_data = self._enrich_plan_data(payload)
        plan_payload = self._build_plan_payload(payload, plan_data)

        plan, created = self._persist_plan(
            auth_user_id=payload['auth_user_id'],
            plan_payload=plan_payload,
            metadata=payload.get('metadata') or {},
        )

        logger.info(
            "nutrition_plan.callback.persisted",
            extra={
                'plan_id': str(plan.id),
                'auth_user_id': str(payload['auth_user_id']),
                'job_id': str(payload['job_id']),
                'was_created': created,
            },
        )

        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            {
                'plan_id': str(plan.id),
                'job_id': str(payload['job_id']),
                'status': 'created' if created else 'updated',
            },
            status=response_status,
        )

    def _enforce_callback_token(self, request) -> None:
        expected = getattr(settings, 'NUTRITION_PLAN_CALLBACK_TOKEN', None)
        if not expected:
            logger.warning(
                "nutrition_plan.callback.token_missing",
                extra={'path': request.path},
            )
            return

        auth_header = request.headers.get('Authorization') or ''
        if not auth_header.startswith('Bearer '):
            raise PermissionDenied('Token de servicio inválido o faltante.')
        provided = auth_header.split(' ', 1)[1].strip()
        if not constant_time_compare(provided, expected):
            raise PermissionDenied('Token de servicio inválido o faltante.')

    def _enrich_plan_data(self, payload: dict) -> dict:
        plan_data = copy.deepcopy(payload['plan_data'])
        if not isinstance(plan_data, dict):
            raise ValidationError({'plan_data': 'plan_data debe ser un objeto JSON.'})

        plan_section = plan_data.setdefault('plan', {})
        if not isinstance(plan_section, dict):
            plan_section = {}
            plan_data['plan'] = plan_section

        plan_section.setdefault('title', payload['title'])
        plan_section.setdefault('language', payload['language'])
        plan_section.setdefault('job_id', str(payload['job_id']))

        if payload.get('raw_text_excerpt'):
            plan_section.setdefault('raw_text_excerpt', payload['raw_text_excerpt'])

        if payload.get('llm'):
            plan_section.setdefault('llm', payload['llm'])

        metadata = payload.get('metadata')
        if metadata:
            plan_section.setdefault('metadata', metadata)

        source_input = payload.get('source') or {}
        plan_source = plan_section.setdefault('source', {})
        if not isinstance(plan_source, dict):
            plan_source = {}
            plan_section['source'] = plan_source

        plan_source.setdefault('kind', 'pdf')
        plan_source.setdefault('storage_kind', source_input.get('storage_kind') or source_input.get('kind'))
        if source_input.get('public_url'):
            plan_source.setdefault('public_url', source_input.get('public_url'))
        if source_input.get('path'):
            plan_source.setdefault('path', source_input.get('path'))
        if source_input.get('bucket'):
            plan_source.setdefault('bucket', source_input.get('bucket'))

        extractor_input = payload.get('extractor') or {}
        if extractor_input.get('name') or extractor_input.get('model'):
            plan_section.setdefault('extractor', extractor_input.get('name') or extractor_input.get('model'))
        if extractor_input.get('extracted_at'):
            plan_section.setdefault('extracted_at', extractor_input.get('extracted_at'))

        return plan_data

    def _build_plan_payload(self, payload: dict, plan_data: dict) -> dict:
        source_input = payload.get('source') or {}
        extractor_input = payload.get('extractor') or {}

        return {
            'title': payload['title'],
            'language': payload['language'],
            'issued_at': payload.get('issued_at'),
            'valid_until': payload.get('valid_until'),
            'is_active': payload.get('is_active', True),
            'plan_data': plan_data,
            'source_kind': source_input.get('kind') or 'pdf',
            'source_uri': source_input.get('public_url') or source_input.get('uri') or source_input.get('path'),
            'extracted_at': extractor_input.get('extracted_at'),
            'extractor': extractor_input.get('name') or extractor_input.get('model'),
        }

    def _persist_plan(self, *, auth_user_id, plan_payload: dict, metadata: dict) -> tuple[NutritionPlan, bool]:
        plan_id = metadata.get('plan_id') if isinstance(metadata, dict) else None
        instance: NutritionPlan | None = None
        created = True

        if plan_id:
            try:
                instance = NutritionPlan.objects.get(id=plan_id)
                created = False
            except NutritionPlan.DoesNotExist:
                logger.warning(
                    "nutrition_plan.callback.plan_not_found",
                    extra={'plan_id': plan_id},
                )

        serializer = NutritionPlanSerializer(instance, data=plan_payload)
        serializer.is_valid(raise_exception=True)
        plan = serializer.save(auth_user_id=auth_user_id)
        return plan, created
