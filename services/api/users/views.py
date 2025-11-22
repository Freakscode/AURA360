"""
Views y ViewSets para la aplicación de usuarios.

Este módulo define los endpoints de la API REST usando Django REST Framework.
Los ViewSets proporcionan operaciones CRUD completas con soporte para filtrado,
búsqueda, ordenamiento y paginación.
"""

import uuid

from django.db.models import Count, Avg, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import AppUser, GlobalRole, UserTier, UsageLedger, CareRelationship, CareRelationshipContext
from .serializers import (
    AppUserSerializer,
    AppUserListSerializer,
    AppUserCreateSerializer,
    AppUserUpdateSerializer,
    AppUserSummarySerializer,
    QuotaStatusSerializer,
    AppUserRoleUpdateSerializer,
    SupabaseAdminUserCreateSerializer,
    UsageLedgerSerializer,
)
from .services import (
    QuotaExceeded,
    consume_quota,
    get_quota_snapshot,
    get_supabase_admin_client,
    SupabaseAdminError,
)
from .permissions import (
    SupabaseJWTOptionalPermission,
    SupabaseJWTRequiredPermission,
    SupabaseServiceRolePermission,
)


class AppUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para operaciones CRUD de usuarios.
    
    Este ViewSet proporciona los siguientes endpoints:
    
    - GET /dashboard/users/ - Lista todos los usuarios (paginado)
    - POST /dashboard/users/ - Crea un nuevo usuario
    - GET /dashboard/users/{id}/ - Obtiene un usuario específico
    - PUT /dashboard/users/{id}/ - Actualiza un usuario completo
    - PATCH /dashboard/users/{id}/ - Actualiza parcialmente un usuario
    - DELETE /dashboard/users/{id}/ - Elimina un usuario
    
    Endpoints adicionales:
    - GET /dashboard/users/by_auth_id/{uuid}/ - Buscar por auth_user_id
    - GET /dashboard/users/premium/ - Lista solo usuarios premium
    - GET /dashboard/users/free/ - Lista solo usuarios free
    - GET /dashboard/users/stats/ - Estadísticas de usuarios
    """
    
    queryset = AppUser.objects.all()
    permission_classes = [SupabaseJWTOptionalPermission]
    
    # Configuración de filtros y búsqueda
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tier', 'gender', 'age', 'role_global', 'billing_plan', 'is_independent']
    search_fields = ['full_name', 'email', 'phone_number']
    ordering_fields = ['created_at', 'updated_at', 'full_name', 'age', 'tier', 'role_global', 'billing_plan']
    ordering = ['-created_at']  # Ordenamiento por defecto
    
    def get_serializer_class(self):
        """
        Selecciona el serializer apropiado según la acción.
        
        - list: Usa AppUserListSerializer (campos reducidos)
        - create: Usa AppUserCreateSerializer
        - update/partial_update: Usa AppUserUpdateSerializer
        - retrieve/default: Usa AppUserSerializer (completo)
        """
        if self.action == 'list':
            return AppUserListSerializer
        elif self.action == 'create':
            return AppUserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AppUserUpdateSerializer
        return AppUserSerializer
    
    def get_queryset(self):
        """
        Personaliza el queryset base según parámetros de query.
        
        Parámetros opcionales:
        - tier: Filtra por tipo de membresía (free, premium)
        - min_age: Edad mínima
        - max_age: Edad máxima
        """
        queryset = super().get_queryset()
        
        # Filtro por edad mínima
        min_age = self.request.query_params.get('min_age', None)
        if min_age is not None:
            try:
                queryset = queryset.filter(age__gte=int(min_age))
            except ValueError:
                pass
        
        # Filtro por edad máxima
        max_age = self.request.query_params.get('max_age', None)
        if max_age is not None:
            try:
                queryset = queryset.filter(age__lte=int(max_age))
            except ValueError:
                pass
        
        return queryset
    
    @action(
        detail=False,
        methods=['post'],
        url_path='provision',
        permission_classes=[SupabaseServiceRolePermission],
    )
    def provision(self, request):
        """
        Provisiona un usuario en Supabase Auth y sincroniza su perfil en app_users.
        
        POST /dashboard/users/provision/
        """
        serializer = SupabaseAdminUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            client = get_supabase_admin_client()
        except SupabaseAdminError as error:
            raise APIException(str(error)) from error

        payload = serializer.validated_data
        metadata = payload['user_metadata']
        app_metadata = payload.get('app_metadata')

        try:
            supabase_payload = client.create_user(
                email=payload['email'],
                password=payload['password'],
                email_confirm=payload['email_confirm'],
                user_metadata=metadata,
                app_metadata=app_metadata,
            )
        except SupabaseAdminError as error:
            if error.status_code and 400 <= error.status_code < 500:
                raise ValidationError({'detail': str(error)}) from error
            raise APIException(str(error)) from error

        supabase_user = supabase_payload.get('user', supabase_payload)
        auth_user_id = supabase_user.get('id')
        if not auth_user_id:
            raise APIException('Supabase no devolvió el identificador del usuario.')

        app_user = self._sync_app_user(
            auth_user_id=auth_user_id,
            email=payload['email'],
            metadata=metadata,
        )

        return Response(
            {
                'supabase_user': supabase_payload,
                'app_user': AppUserSerializer(app_user).data,
            },
            status=status.HTTP_201_CREATED,
        )
    
    @action(detail=False, methods=['get'], url_path='by_auth_id/(?P<auth_user_id>[^/.]+)')
    def by_auth_id(self, request, auth_user_id=None):
        """
        Busca un usuario por su auth_user_id (UUID de Supabase Auth).
        
        GET /dashboard/users/by_auth_id/{uuid}/
        
        Este endpoint es útil cuando tienes el UUID de autenticación
        y necesitas obtener el perfil completo del usuario.
        """
        try:
            user = self.queryset.get(auth_user_id=auth_user_id)
            serializer = AppUserSerializer(user)
            return Response(serializer.data)
        except AppUser.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado con ese auth_user_id'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def premium(self, request):
        """
        Lista solo usuarios con membresía premium.
        
        GET /dashboard/users/premium/
        
        Soporta paginación, búsqueda y ordenamiento como el listado normal.
        """
        premium_users = self.queryset.filter(tier=UserTier.PREMIUM)
        page = self.paginate_queryset(premium_users)
        
        if page is not None:
            serializer = AppUserListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AppUserListSerializer(premium_users, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        url_path='invite-patient',
        permission_classes=[SupabaseJWTRequiredPermission],
    )
    def invite_patient(self, request):
        """
        Crea un nuevo paciente y establece una relación de cuidado con el profesional actual.
        
        POST /dashboard/users/invite-patient/
        Body: { "email": "...", "full_name": "...", "phone_number": "..." }
        """
        # 1. Identificar al profesional (usuario actual)
        try:
            professional_uuid = request.user.id
            professional = AppUser.objects.get(auth_user_id=professional_uuid)
        except AppUser.DoesNotExist:
            return Response(
                {'error': 'Perfil de profesional no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validar que sea profesional (opcional, según reglas de negocio)
        # if professional.global_role != GlobalRole.PROFESIONAL_SALUD: ...

        # 2. Preparar payload para provisión
        email = request.data.get('email')
        full_name = request.data.get('full_name')
        phone = request.data.get('phone_number')
        
        if not email:
            return Response({'error': 'El email es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        # Datos para crear el usuario
        provision_data = {
            "email": email,
            "password": uuid.uuid4().hex[:12], # Contraseña temporal aleatoria
            "email_confirm": True, # Auto-confirmar para evitar fricción en demo
            "user_metadata": {
                "full_name": full_name,
                "phone_number": phone,
                "role_global": "Paciente", # Forzar rol Paciente
                "tier": "free",
                "billing_plan": "individual"
            }
        }

        # 3. Reutilizar lógica de provisión
        # Instanciamos el serializer para validar
        serializer = SupabaseAdminUserCreateSerializer(data=provision_data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Llamamos a la lógica de provisión interna (copiada de provision action)
            client = get_supabase_admin_client()
            payload = serializer.validated_data
            metadata = payload['user_metadata']
            
            # Verificar si ya existe en Supabase
            # Nota: create_user lanzará error si existe.
            # Podríamos intentar get_user_by_email primero si queremos manejar "Asociar existente".
            
            try:
                supabase_payload = client.create_user(
                    email=payload['email'],
                    password=payload['password'],
                    email_confirm=payload['email_confirm'],
                    user_metadata=metadata,
                )
                auth_user_id = supabase_payload.get('user', supabase_payload).get('id')
                
                # Sincronizar AppUser
                patient = self._sync_app_user(
                    auth_user_id=auth_user_id,
                    email=payload['email'],
                    metadata=metadata,
                )
                
            except SupabaseAdminError as e:
                if "User already registered" in str(e):
                    # El usuario ya existe, buscamos su AppUser
                    # TODO: Implementar búsqueda por email en AppUser
                    # Por ahora asumimos que si existe en Auth, existe en AppUser o lo sincronizamos
                    # Necesitamos el ID de auth.
                    users = client.list_users() # Ineficiente, pero admin client no tiene get_by_email fácil en algunas versiones
                    # Mejor: Asumir que falla y pedir al usuario que use "Asociar Paciente Existente"
                    return Response(
                        {'error': 'El usuario ya está registrado. Use la función de búsqueda para asociarlo.'},
                        status=status.HTTP_409_CONFLICT
                    )
                raise e

            # 4. Crear Relación de Cuidado
            CareRelationship.objects.create(
                professional_user=professional,
                patient_user=patient,
                context_type=CareRelationshipContext.INDEPENDENT,
                status='active'
            )

            return Response({
                'message': 'Paciente creado y asociado exitosamente.',
                'patient': AppUserSerializer(patient).data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
             return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='roles')
    def roles_summary(self, request):
        """
        Devuelve un resumen de usuarios agrupados por rol global.
        """
        summary = (
            self.queryset
            .values('role_global')
            .annotate(total=Count('id'))
            .order_by('role_global')
        )

        by_role = {item['role_global']: item['total'] for item in summary}
        data = []
        for role in GlobalRole:
            data.append(
                {
                    'role_global': role.value,
                    'label': role.label,
                    'total': by_role.get(role.value, 0),
                }
            )

        return Response(data)

    @action(detail=False, methods=['get'], url_path='roles/(?P<role_slug>[^/.]+)')
    def role_members(self, request, role_slug: str):
        """
        Lista usuarios pertenecientes a un rol global específico.
        """
        role = self._resolve_role_slug(role_slug)
        if role is None:
            return Response(
                {'detail': f'Rol desconocido: {role_slug}'},
                status=status.HTTP_404_NOT_FOUND,
            )

        queryset = self.queryset.filter(role_global=role.value)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AppUserListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AppUserListSerializer(queryset, many=True)
        return Response(serializer.data)

    def _sync_app_user(self, *, auth_user_id: str, email: str, metadata: dict) -> AppUser:
        """Crea o actualiza el registro en app_users con la metadata recibida."""
        try:
            auth_uuid = uuid.UUID(str(auth_user_id))
        except (ValueError, TypeError) as error:
            raise APIException('El ID devuelto por Supabase no es un UUID válido.') from error

        age_value = metadata.get('age', 0)
        try:
            age = int(age_value) if age_value is not None else 0
        except (TypeError, ValueError):
            age = 0

        defaults = {
            'full_name': metadata.get('full_name') or email,
            'age': age,
            'email': email,
            'phone_number': metadata.get('phone_number'),
            'gender': metadata.get('gender'),
            'tier': metadata.get('tier'),
            'role_global': metadata.get('role_global'),
            'is_independent': metadata.get('is_independent', False),
            'billing_plan': metadata.get('billing_plan'),
        }

        try:
            app_user, _ = AppUser.objects.update_or_create(
                auth_user_id=auth_uuid,
                defaults=defaults,
            )
        except Exception as error:  # pragma: no cover - capturamos errores inusuales de DB
            raise APIException(
                f'El usuario se creó en Supabase pero falló la sincronización local: {error}',
            ) from error

        return app_user
    
    @action(detail=False, methods=['get'])
    def free(self, request):
        """
        Lista solo usuarios con membresía gratuita.
        
        GET /dashboard/users/free/
        
        Soporta paginación, búsqueda y ordenamiento como el listado normal.
        """
        free_users = self.queryset.filter(tier=UserTier.FREE)
        page = self.paginate_queryset(free_users)
        
        if page is not None:
            serializer = AppUserListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AppUserListSerializer(free_users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Obtiene estadísticas agregadas de usuarios.
        
        GET /dashboard/users/stats/
        
        Retorna:
        - total_users: Total de usuarios registrados
        - free_users: Usuarios con plan gratuito
        - premium_users: Usuarios con plan premium
        - average_age: Edad promedio de todos los usuarios
        """
        stats = self.queryset.aggregate(
            total_users=Count('id'),
            free_users=Count('id', filter=Q(tier=UserTier.FREE)),
            premium_users=Count('id', filter=Q(tier=UserTier.PREMIUM)),
            average_age=Avg('age')
        )
        
        serializer = AppUserSummarySerializer(stats)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upgrade_to_premium(self, request, pk=None):
        """
        Actualiza un usuario de free a premium.
        
        POST /dashboard/users/{id}/upgrade_to_premium/
        
        Este endpoint es útil para procesos de upgrade de membresía.
        """
        user = self.get_object()
        
        if user.is_premium:
            return Response(
                {'message': 'El usuario ya tiene membresía premium'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.tier = UserTier.PREMIUM
        user.save()
        
        serializer = AppUserSerializer(user)
        return Response({
            'message': 'Usuario actualizado a premium exitosamente',
            'user': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def downgrade_to_free(self, request, pk=None):
        """
        Actualiza un usuario de premium a free.
        
        POST /dashboard/users/{id}/downgrade_to_free/
        
        Este endpoint es útil para cancelaciones de membresía.
        """
        user = self.get_object()
        
        if user.is_free:
            return Response(
                {'message': 'El usuario ya tiene membresía gratuita'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.tier = UserTier.FREE
        user.save()
        
        serializer = AppUserSerializer(user)
        return Response({
            'message': 'Usuario actualizado a free exitosamente',
            'user': serializer.data
        })

    @action(
        detail=True,
        methods=['post'],
        url_path='set-role',
        permission_classes=[SupabaseServiceRolePermission],
    )
    def set_role(self, request, pk=None):
        """
        Actualiza el rol global, independencia o plan comercial de un usuario.
        """
        user = self.get_object()
        serializer = AppUserRoleUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        updated_fields = []
        if 'role_global' in data:
            user.role_global = data['role_global']
            updated_fields.append('role_global')
        if 'is_independent' in data:
            user.is_independent = data['is_independent']
            updated_fields.append('is_independent')
        if 'billing_plan' in data:
            user.billing_plan = data['billing_plan']
            updated_fields.append('billing_plan')

        if updated_fields:
            user.save(update_fields=updated_fields + ['updated_at'])

        return Response(AppUserSerializer(user).data)

    def _resolve_role_slug(self, slug: str) -> GlobalRole | None:
        """Mapea slugs flexibles a GlobalRole."""
        normalized = slug.strip().lower()
        normalized = normalized.replace('_', '').replace('-', '')

        for role in GlobalRole:
            if normalized == role.name.lower():
                return role
            value_norm = role.value.lower().replace('_', '').replace('-', '')
            if normalized == value_norm:
                return role
        return None

    def _consume_resource(self, request, user: AppUser, resource_code: str, success_message: str, *, metadata=None):
        metadata_payload = dict(metadata or {})
        actor = getattr(request, 'user', None)
        if actor is not None and getattr(actor, 'is_authenticated', False):
            metadata_payload.setdefault('actor_id', getattr(actor, 'id', None))

        try:
            consumption = consume_quota(user, resource_code, metadata=metadata_payload)
        except QuotaExceeded as exc:
            snapshot = next(
                (status.as_dict() for status in get_quota_snapshot(user) if status.resource_code == resource_code),
                None,
            )
            return Response(
                {
                    'detail': 'quota_exceeded',
                    'resource_code': resource_code,
                    'limit': exc.decision.limit,
                    'remaining': exc.decision.remaining,
                    'reason': exc.decision.reason,
                    'quota': snapshot,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        snapshot = next(
            (status.as_dict() for status in get_quota_snapshot(user) if status.resource_code == resource_code),
            None,
        )

        return Response(
            {
                'message': success_message,
                'resource_code': resource_code,
                'ledger_id': consumption.ledger.id,
                'limit': consumption.decision.limit,
                'remaining': consumption.decision.remaining,
                'reason': consumption.decision.reason,
                'quota': snapshot,
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='generate-metabolic-report',
        permission_classes=[SupabaseJWTRequiredPermission],
    )
    def generate_metabolic_report(self, request, pk=None):
        """Consume la cuota correspondiente a un reporte metabólico manual."""

        user = self.get_object()
        return self._consume_resource(
            request,
            user,
            'metabolic_report',
            'Reporte metabólico encolado correctamente',
            metadata={'action': 'generate_metabolic_report'},
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='request-realtime-update',
        permission_classes=[SupabaseJWTRequiredPermission],
    )
    def request_realtime_update(self, request, pk=None):
        """Solicita una actualización en tiempo real de indicadores."""

        user = self.get_object()
        return self._consume_resource(
            request,
            user,
            'realtime_update',
            'Actualización en tiempo real registrada',
            metadata={'action': 'request_realtime_update'},
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='chatbot-session',
        permission_classes=[SupabaseJWTRequiredPermission],
    )
    def chatbot_session(self, request, pk=None):
        """Abre una sesión de chatbot personalizada."""

        user = self.get_object()
        return self._consume_resource(
            request,
            user,
            'chatbot_session',
            'Sesión de chatbot registrada',
            metadata={'action': 'chatbot_session'},
        )

    @action(
        detail=True,
        methods=['get'],
        url_path='quota-status',
        permission_classes=[SupabaseJWTRequiredPermission],
    )
    def quota_status(self, request, pk=None):
        """Devuelve el estado actual de todas las cuotas del usuario."""

        user = self.get_object()
        snapshot = [status.as_dict() for status in get_quota_snapshot(user)]
        serializer = QuotaStatusSerializer(snapshot, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['get'],
        url_path='usage-history',
        permission_classes=[SupabaseJWTRequiredPermission],
    )
    def usage_history(self, request, pk=None):
        """Lista los últimos movimientos de consumo del usuario."""

        user = self.get_object()
        try:
            limit = int(request.query_params.get('limit', 20))
        except ValueError:
            limit = 20
        limit = max(1, min(limit, 100))

        entries = UsageLedger.objects.filter(user_id=user.pk).order_by('-occurred_at')[:limit]
        serializer = UsageLedgerSerializer(entries, many=True)
        return Response(serializer.data)
