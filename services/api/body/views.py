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

from .models import BodyActivity, NutritionLog, NutritionPlan, SleepLog
from .serializers import (
    BodyActivitySerializer,
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
        """
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
        """Asigna el usuario autenticado al crear un plan."""
        serializer.save(auth_user_id=self._auth_user_id())
    
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
                'created': created,
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
