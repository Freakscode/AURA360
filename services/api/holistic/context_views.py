"""Views para gestión de contexto de usuario (snapshots, mood, IKIGAI)."""

from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    IntakeSubmission,
    MoodEntry,
    UserContextSnapshot,
    UserProfileExtended,
)
from .serializers import (
    CreateSnapshotRequestSerializer,
    IntakeSubmissionCreateSerializer,
    IntakeSubmissionSerializer,
    MoodEntrySerializer,
    UserContextSnapshotSerializer,
    UserProfileExtendedSerializer,
)

# Import messaging for event publishing
try:
    from messaging import publish_event, MoodCreatedEvent, IkigaiUpdatedEvent
    MESSAGING_AVAILABLE = True
except ImportError:
    MESSAGING_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Messaging module not available. Events will not be published.")

# Import tasks solo si Celery está disponible
try:
    from .tasks import generate_user_context_snapshot_for_user, process_intake_submission
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    generate_user_context_snapshot_for_user = None
    process_intake_submission = None

logger = logging.getLogger(__name__)

__all__ = [
    "UserContextSnapshotListView",
    "UserContextSnapshotDetailView",
    "CreateSnapshotView",
    "MoodEntryListCreateView",
    "UserProfileExtendedView",
    "IntakeSubmissionListCreateView",
    "IntakeSubmissionDetailView",
    "MessagingHealthView",
]


class IntakeSubmissionListCreateView(APIView):
    """Lista o crea submissions del intake holístico."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = str(request.user.id)
        try:
            limit = int(request.query_params.get("limit", 10))
        except ValueError:
            limit = 10
        limit = max(1, min(limit, 50))

        queryset = IntakeSubmission.objects.filter(auth_user_id=user_id).order_by("-created_at")
        total = queryset.count()
        submissions = list(queryset[:limit])
        serializer = IntakeSubmissionSerializer(submissions, many=True)
        return Response({"count": total, "results": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        user_id = str(request.user.id)
        serializer = IntakeSubmissionCreateSerializer(
            data=request.data,
            context={"auth_user_id": user_id},
        )
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()
        response_data = IntakeSubmissionSerializer(submission).data

        task_id = None
        if CELERY_AVAILABLE and process_intake_submission:
            try:
                async_result = process_intake_submission.delay(str(submission.id))
                task_id = async_result.id
            except Exception as exc:  # pragma: no cover - depends on broker
                logger.warning(
                    "No se pudo encolar el intake %s en Celery: %s",
                    submission.id,
                    exc,
                )
        if task_id:
            response_data["task_id"] = task_id

        return Response(response_data, status=status.HTTP_201_CREATED)


class IntakeSubmissionDetailView(APIView):
    """Detalle de un intake submission."""

    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
        user_id = str(request.user.id)
        try:
            submission = IntakeSubmission.objects.get(id=submission_id, auth_user_id=user_id)
        except IntakeSubmission.DoesNotExist:
            return Response({"detail": "Registro no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        serializer = IntakeSubmissionSerializer(submission)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserContextSnapshotListView(APIView):
    """Lista snapshots activos del usuario autenticado."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/holistic/user-context/snapshots/"""
        user_id = str(request.user.id)

        # Query params opcionales
        snapshot_type = request.query_params.get("snapshot_type")
        timeframe = request.query_params.get("timeframe")

        # Filtrar snapshots
        queryset = UserContextSnapshot.objects.filter(
            auth_user_id=user_id, is_active=True
        )

        if snapshot_type:
            queryset = queryset.filter(snapshot_type=snapshot_type)

        if timeframe:
            queryset = queryset.filter(timeframe=timeframe)

        snapshots = queryset.order_by("-created_at")

        serializer = UserContextSnapshotSerializer(snapshots, many=True)

        return Response(
            {"count": len(serializer.data), "results": serializer.data},
            status=status.HTTP_200_OK,
        )


class UserContextSnapshotDetailView(APIView):
    """Obtiene o elimina un snapshot específico."""

    permission_classes = [IsAuthenticated]

    def get(self, request, snapshot_id):
        """GET /api/holistic/user-context/snapshots/{snapshot_id}/"""
        user_id = str(request.user.id)

        try:
            snapshot = UserContextSnapshot.objects.get(
                id=snapshot_id, auth_user_id=user_id
            )
        except UserContextSnapshot.DoesNotExist:
            return Response(
                {"detail": "Snapshot no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserContextSnapshotSerializer(snapshot)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, snapshot_id):
        """DELETE /api/holistic/user-context/snapshots/{snapshot_id}/

        Elimina el snapshot y sus embeddings (GDPR compliance).
        """
        user_id = str(request.user.id)

        try:
            snapshot = UserContextSnapshot.objects.get(
                id=snapshot_id, auth_user_id=user_id
            )
        except UserContextSnapshot.DoesNotExist:
            return Response(
                {"detail": "Snapshot no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Eliminar de vector store si está vectorizado
        if snapshot.vectorized_at and snapshot.vector_doc_id:
            from .context_vectorizer import UserContextVectorizer

            vectorizer = UserContextVectorizer()
            deleted = vectorizer.delete_snapshot_from_vector_store(snapshot)

            if not deleted:
                logger.warning(
                    f"Failed to delete vector document for snapshot {snapshot_id}"
                )

        # Eliminar snapshot
        snapshot.delete()

        logger.info(
            f"Deleted snapshot {snapshot_id} for user {user_id} (GDPR compliance)"
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class CreateSnapshotView(APIView):
    """Crea un nuevo snapshot para el usuario (event-driven trigger)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """POST /api/holistic/user-context/snapshots/create/

        Body:
        {
            "user_id": "uuid",  # Debe coincidir con request.user.id
            "snapshot_type": "mind|body|soul|holistic",
            "timeframe": "7d|30d|90d",
            "vectorize": true
        }
        """
        serializer = CreateSnapshotRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = str(serializer.validated_data["user_id"])
        snapshot_type = serializer.validated_data["snapshot_type"]
        timeframe = serializer.validated_data["timeframe"]
        vectorize = serializer.validated_data["vectorize"]

        # Verificar que el user_id coincida con el usuario autenticado
        if user_id != str(request.user.id):
            return Response(
                {"detail": "No tienes permiso para crear snapshots de otros usuarios"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Encolar task asíncrona
        if not CELERY_AVAILABLE:
            return Response(
                {"detail": "Celery is not configured. Install celery to use async snapshot generation."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        task_result = generate_user_context_snapshot_for_user.delay(
            user_id=user_id,
            snapshot_type=snapshot_type,
            timeframe=timeframe,
            vectorize=vectorize,
        )

        logger.info(
            f"Enqueued snapshot generation task {task_result.id} "
            f"for user {user_id} (type={snapshot_type})"
        )

        return Response(
            {
                "status": "accepted",
                "task_id": task_result.id,
                "message": "Snapshot generation enqueued",
            },
            status=status.HTTP_202_ACCEPTED,
        )


class MoodEntryListCreateView(APIView):
    """Lista o crea mood entries del usuario."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/holistic/mood-entries/

        Query params:
        - limit: Número máximo de entries (default: 50)
        - days: Días hacia atrás (default: 30)
        """
        user_id = str(request.user.id)
        limit = int(request.query_params.get("limit", 50))
        days = int(request.query_params.get("days", 30))

        from datetime import timedelta

        from django.utils import timezone

        cutoff = timezone.now() - timedelta(days=days)

        moods = MoodEntry.objects.filter(
            auth_user_id=user_id, recorded_at__gte=cutoff
        ).order_by("-recorded_at")[:limit]

        serializer = MoodEntrySerializer(moods, many=True)

        return Response(
            {"count": len(serializer.data), "results": serializer.data},
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """POST /api/holistic/mood-entries/

        Body:
        {
            "auth_user_id": "uuid",  # Debe coincidir con request.user.id
            "recorded_at": "2025-01-15T10:30:00Z",
            "level": "good",
            "note": "Feeling energized today",
            "tags": ["work", "productive"]
        }
        """
        serializer = MoodEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = str(serializer.validated_data["auth_user_id"])

        # Verificar permiso
        if user_id != str(request.user.id):
            return Response(
                {"detail": "No tienes permiso para crear mood entries de otros usuarios"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Crear mood entry
        mood = MoodEntry.objects.create(**serializer.validated_data)

        logger.info(f"Created mood entry {mood.id} for user {user_id}")

        # Publish event to messaging backend (Kafka or Celery)
        if MESSAGING_AVAILABLE:
            try:
                event = MoodCreatedEvent.from_mood_entry(
                    user_id=user_id,
                    mood_data={
                        "mood_id": str(mood.id),
                        "level": mood.level,
                        "recorded_at": mood.recorded_at.isoformat(),
                        "note": mood.note,
                        "tags": mood.tags,
                    }
                )
                publish_event(event)
                logger.debug(f"Published MoodCreatedEvent for user {user_id}")
            except Exception as e:
                # Don't fail the request if event publishing fails
                logger.error(f"Failed to publish MoodCreatedEvent: {e}", exc_info=True)

        # Si hay 5+ moods en el día, trigger snapshot update
        from django.utils import timezone

        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        moods_today = MoodEntry.objects.filter(
            auth_user_id=user_id, recorded_at__gte=today_start
        ).count()

        if moods_today >= 5 and CELERY_AVAILABLE:
            logger.info(
                f"User {user_id} has {moods_today} moods today, triggering mind snapshot update"
            )
            generate_user_context_snapshot_for_user.delay(
                user_id=user_id, snapshot_type="mind", timeframe="7d", vectorize=True
            )

        response_serializer = MoodEntrySerializer(mood)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class UserProfileExtendedView(APIView):
    """Obtiene o actualiza el perfil extendido del usuario (IKIGAI + psychosocial)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/holistic/user-profile-extended/"""
        user_id = str(request.user.id)

        try:
            profile = UserProfileExtended.objects.get(auth_user_id=user_id)
        except UserProfileExtended.DoesNotExist:
            return Response(
                {"detail": "Perfil extendido no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserProfileExtendedSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        """PUT /api/holistic/user-profile-extended/

        Actualiza o crea el perfil extendido del usuario.
        """
        user_id = str(request.user.id)

        serializer = UserProfileExtendedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile, created = UserProfileExtended.objects.update_or_create(
            auth_user_id=user_id, defaults=serializer.validated_data
        )

        logger.info(
            f"{'Created' if created else 'Updated'} extended profile for user {user_id}"
        )

        # Publish IKIGAI updated event
        if MESSAGING_AVAILABLE:
            try:
                event = IkigaiUpdatedEvent(
                    user_id=user_id,
                    data={
                        "ikigai_passion": profile.ikigai_passion,
                        "ikigai_mission": profile.ikigai_mission,
                        "ikigai_vocation": profile.ikigai_vocation,
                        "ikigai_profession": profile.ikigai_profession,
                        "ikigai_statement": profile.ikigai_statement,
                        "psychosocial_context": profile.psychosocial_context,
                        "support_network": profile.support_network,
                        "current_stressors": profile.current_stressors,
                        "updated_at": profile.updated_at.isoformat(),
                    }
                )
                publish_event(event)
                logger.debug(f"Published IkigaiUpdatedEvent for user {user_id}")
            except Exception as e:
                # Don't fail the request if event publishing fails
                logger.error(f"Failed to publish IkigaiUpdatedEvent: {e}", exc_info=True)

        # Trigger soul snapshot update
        if CELERY_AVAILABLE:
            generate_user_context_snapshot_for_user.delay(
                user_id=user_id, snapshot_type="soul", vectorize=True
            )

        response_serializer = UserProfileExtendedSerializer(profile)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def patch(self, request):
        """PATCH /api/holistic/user-profile-extended/

        Actualización parcial del perfil extendido.
        """
        user_id = str(request.user.id)

        try:
            profile = UserProfileExtended.objects.get(auth_user_id=user_id)
        except UserProfileExtended.DoesNotExist:
            return Response(
                {"detail": "Perfil extendido no encontrado. Usa PUT para crear."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserProfileExtendedSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Actualizar campos
        for field, value in serializer.validated_data.items():
            setattr(profile, field, value)

        profile.save()

        logger.info(f"Partially updated extended profile for user {user_id}")

        # Publish IKIGAI updated event if relevant fields changed
        ikigai_fields = [
            "ikigai_passion",
            "ikigai_mission",
            "ikigai_vocation",
            "ikigai_profession",
            "ikigai_statement",
        ]
        if MESSAGING_AVAILABLE and any(field in serializer.validated_data for field in ikigai_fields):
            try:
                event = IkigaiUpdatedEvent(
                    user_id=user_id,
                    data={
                        "ikigai_passion": profile.ikigai_passion,
                        "ikigai_mission": profile.ikigai_mission,
                        "ikigai_vocation": profile.ikigai_vocation,
                        "ikigai_profession": profile.ikigai_profession,
                        "ikigai_statement": profile.ikigai_statement,
                        "psychosocial_context": profile.psychosocial_context,
                        "support_network": profile.support_network,
                        "current_stressors": profile.current_stressors,
                        "updated_at": profile.updated_at.isoformat(),
                    }
                )
                publish_event(event)
                logger.debug(f"Published IkigaiUpdatedEvent for user {user_id} (partial update)")
            except Exception as e:
                # Don't fail the request if event publishing fails
                logger.error(f"Failed to publish IkigaiUpdatedEvent: {e}", exc_info=True)

        # Trigger soul snapshot update si cambió IKIGAI
        if CELERY_AVAILABLE and any(field in serializer.validated_data for field in ikigai_fields):
            generate_user_context_snapshot_for_user.delay(
                user_id=user_id, snapshot_type="soul", vectorize=True
            )

        response_serializer = UserProfileExtendedSerializer(profile)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class MessagingHealthView(APIView):
    """Health check endpoint para verificar el backend de mensajería configurado."""

    permission_classes = []  # Public endpoint

    def get(self, request):
        """GET /api/holistic/messaging/health/

        Returns:
        {
            "status": "ok",
            "messaging_backend": "kafka|celery|disabled",
            "messaging_available": true|false,
            "celery_available": true|false
        }
        """
        import os

        messaging_backend = os.getenv("MESSAGING_BACKEND", "kafka")

        response_data = {
            "status": "ok",
            "messaging_backend": messaging_backend,
            "messaging_available": MESSAGING_AVAILABLE,
            "celery_available": CELERY_AVAILABLE,
        }

        # Add additional info based on backend type
        if MESSAGING_AVAILABLE and messaging_backend == "kafka":
            try:
                from messaging import get_backend
                backend = get_backend()
                response_data["backend_type"] = type(backend).__name__
            except Exception as e:
                logger.error(f"Failed to get messaging backend info: {e}")
                response_data["error"] = str(e)

        return Response(response_data, status=status.HTTP_200_OK)
