from __future__ import annotations

from typing import Any

from rest_framework import serializers

from .intake_definitions import INTAKE_QUESTION_REGISTRY, REQUIRED_QUESTION_IDS
from .models import HolisticCategory, HolisticRequestStatus, IntakeSubmission


class HolisticAdviceRequestSerializer(serializers.Serializer):
    """Serializer encargado de validar las solicitudes entrantes."""

    user_id = serializers.CharField(max_length=64)
    category = serializers.ChoiceField(choices=HolisticCategory.choices)
    metadata = serializers.JSONField(required=False, default=dict)

    def validate_user_id(self, value: str) -> str:
        user_identifier = value.strip()
        if not user_identifier:
            raise serializers.ValidationError("El identificador de usuario no puede estar vacío.")
        return user_identifier

    def validate_metadata(self, value: Any) -> dict[str, Any]:
        if value in (None, ""):
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("Metadata debe ser un objeto JSON.")
        return value


class HolisticAdviceResponseSerializer(serializers.Serializer):
    """Serializer para estructurar la respuesta entregada al cliente."""

    trace_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=HolisticRequestStatus.choices)
    result = serializers.JSONField(required=False, allow_null=True)
    error = serializers.JSONField(required=False, allow_null=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        status_value = attrs.get("status")
        if status_value == HolisticRequestStatus.COMPLETED and "result" not in attrs:
            raise serializers.ValidationError("El campo 'result' es obligatorio cuando el estado es 'completed'.")
        return attrs


class UserContextSnapshotSerializer(serializers.Serializer):
    """Serializer para snapshots de contexto de usuario."""

    id = serializers.UUIDField(read_only=True)
    auth_user_id = serializers.UUIDField(read_only=True)
    snapshot_type = serializers.CharField(max_length=16)
    timeframe = serializers.CharField(max_length=8)
    consolidated_text = serializers.CharField()
    metadata = serializers.JSONField(default=dict)
    topics = serializers.ListField(child=serializers.CharField(), default=list)
    confidence_score = serializers.DecimalField(
        max_digits=5, decimal_places=2, default=0.0
    )
    is_active = serializers.BooleanField(default=True)
    vectorized_at = serializers.DateTimeField(read_only=True, allow_null=True)
    vector_doc_id = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class CreateSnapshotRequestSerializer(serializers.Serializer):
    """Serializer para solicitud de creación de snapshot."""

    user_id = serializers.UUIDField()
    snapshot_type = serializers.ChoiceField(
        choices=["mind", "body", "soul", "holistic"]
    )
    timeframe = serializers.ChoiceField(
        choices=["7d", "30d", "90d"], default="7d"
    )
    vectorize = serializers.BooleanField(default=True)

    def validate_user_id(self, value):
        """Validar que el UUID sea válido."""
        return value


class MoodEntrySerializer(serializers.Serializer):
    """Serializer para mood entries."""

    id = serializers.UUIDField(read_only=True)
    auth_user_id = serializers.UUIDField()
    recorded_at = serializers.DateTimeField()
    level = serializers.ChoiceField(
        choices=["very_low", "low", "moderate", "good", "excellent"]
    )
    note = serializers.CharField(allow_blank=True, default="")
    tags = serializers.ListField(child=serializers.CharField(), default=list)
    created_at = serializers.DateTimeField(read_only=True)


class UserProfileExtendedSerializer(serializers.Serializer):
    """Serializer para perfil extendido de usuario."""

    auth_user_id = serializers.UUIDField(read_only=True)
    ikigai_passion = serializers.ListField(child=serializers.CharField(), default=list)
    ikigai_mission = serializers.ListField(child=serializers.CharField(), default=list)
    ikigai_vocation = serializers.ListField(child=serializers.CharField(), default=list)
    ikigai_profession = serializers.ListField(
        child=serializers.CharField(), default=list
    )
    ikigai_statement = serializers.CharField(allow_blank=True, default="")
    psychosocial_context = serializers.CharField(allow_blank=True, default="")
    support_network = serializers.CharField(allow_blank=True, default="")
    current_stressors = serializers.CharField(allow_blank=True, default="")
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class IntakeAnswerSerializer(serializers.Serializer):
    """Valida cada respuesta individual del intake."""

    question_id = serializers.CharField(max_length=4)
    value = serializers.JSONField()

    default_error_messages = {
        "unknown_question": "Pregunta no soportada.",
        "invalid_type": "Tipo de dato inválido para esta pregunta.",
        "missing_required": "Campo requerido faltante en la respuesta.",
    }

    def validate_question_id(self, value: str) -> str:
        question_id = value.strip().upper()
        if question_id not in INTAKE_QUESTION_REGISTRY:
            self.fail("unknown_question")
        return question_id

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        question_def = INTAKE_QUESTION_REGISTRY[attrs["question_id"]]
        validated_value = self._validate_value(question_def, attrs["value"], attrs["question_id"])
        attrs["value"] = validated_value
        return attrs

    # Value validators --------------------------------------------------
    def _validate_value(self, definition: dict, value: Any, question_id: str):
        qtype = definition["type"]
        if qtype in {"likert", "single_choice"}:
            return self._validate_single_choice(definition, value, question_id)
        if qtype == "multi_choice":
            return self._validate_multi_choice(definition, value, question_id)
        if qtype == "boolean":
            if not isinstance(value, bool):
                self.fail("invalid_type")
            return value
        if qtype == "compound":
            return self._validate_compound(definition, value, question_id)
        self.fail("invalid_type")

    def _validate_single_choice(self, definition: dict, value: Any, question_id: str) -> str:
        if not isinstance(value, str):
            self.fail("invalid_type")
        normalized = value.strip()
        if normalized not in definition.get("choices", []):
            raise serializers.ValidationError(
                {"value": f"Respuesta no permitida para {question_id}"}
            )
        return normalized

    def _validate_multi_choice(self, definition: dict, value: Any, question_id: str) -> dict:
        if not isinstance(value, dict):
            self.fail("invalid_type")
        if "selected" not in value:
            raise serializers.ValidationError({"value": "El campo 'selected' es obligatorio."})

        selected = value.get("selected")
        if not isinstance(selected, list) or not selected:
            raise serializers.ValidationError({"value": "Debes seleccionar al menos una opción."})

        normalized_selection: list[str] = []
        for choice in selected:
            if not isinstance(choice, str):
                self.fail("invalid_type")
            choice_value = choice.strip()
            if choice_value not in definition.get("choices", []):
                raise serializers.ValidationError({"value": f"Opción '{choice_value}' no permitida."})
            if choice_value in normalized_selection:
                raise serializers.ValidationError({"value": "No se permiten duplicados en la selección."})
            normalized_selection.append(choice_value)

        min_required = definition.get("min_selections", 0)
        if min_required and len(normalized_selection) < min_required:
            raise serializers.ValidationError(
                {"value": f"Debes seleccionar al menos {min_required} opción(es)."}
            )

        exclusive = definition.get("mutually_exclusive_option")
        if exclusive and exclusive in normalized_selection and len(normalized_selection) > 1:
            raise serializers.ValidationError(
                {"value": "La opción seleccionada no puede combinarse con otras."}
            )

        other_selected = "other" in normalized_selection
        allow_other = definition.get("allow_other_text", False)
        other_text = value.get("other_text", "")
        if other_selected and not allow_other:
            raise serializers.ValidationError({"value": "La opción 'other' no está permitida."})
        if other_selected and allow_other:
            if not isinstance(other_text, str) or not other_text.strip():
                raise serializers.ValidationError(
                    {"other_text": "Debes detallar cuando seleccionas 'Otro'."}
                )
            max_len = definition.get("other_text_max_length", 255)
            if len(other_text.strip()) > max_len:
                raise serializers.ValidationError(
                    {"other_text": f"Máximo {max_len} caracteres."}
                )
            other_text = other_text.strip()
        else:
            other_text = ""

        if not allow_other and other_text:
            raise serializers.ValidationError({"other_text": "Campo no permitido."})

        return {
            "selected": normalized_selection,
            **({"other_text": other_text} if allow_other else {}),
        }

    def _validate_compound(self, definition: dict, value: Any, question_id: str) -> dict:
        if not isinstance(value, dict):
            self.fail("invalid_type")

        schema = definition.get("schema", {})
        normalized: dict[str, Any] = {}
        for key, field_schema in schema.items():
            if key not in value:
                if field_schema.get("required"):
                    raise serializers.ValidationError({"value": f"'{key}' es requerido"})
                continue
            normalized[key] = self._validate_value(field_schema, value[key], f"{question_id}.{key}")

        # Reglas específicas
        if "has_strategies" in normalized:
            has_strategies = normalized["has_strategies"]
            strategies = normalized.get("strategies")
            if has_strategies and not strategies:
                raise serializers.ValidationError(
                    {"value": "Debes listar al menos una estrategia cuando respondes Sí."}
                )
            if not has_strategies and strategies:
                normalized.pop("strategies", None)

        if "has_guide" in normalized:
            has_guide = normalized["has_guide"]
            guide_type = normalized.get("guide_type")
            if has_guide and not guide_type:
                raise serializers.ValidationError(
                    {"value": "Debes indicar el tipo de guía cuando respondes Sí."}
                )
            if not has_guide and guide_type:
                normalized.pop("guide_type", None)

        return normalized


class IntakeSubmissionCreateSerializer(serializers.Serializer):
    """Serializer para la creación del intake inicial."""

    answers = serializers.ListField(
        child=IntakeAnswerSerializer(),
        min_length=1,
    )
    free_text = serializers.CharField(max_length=280, allow_blank=True, required=False)
    vectorize_snapshot = serializers.BooleanField(default=True)

    def validate_answers(self, value):
        seen_ids: set[str] = set()
        for answer in value:
            qid = answer["question_id"]
            if qid in seen_ids:
                raise serializers.ValidationError(f"La pregunta {qid} está duplicada.")
            seen_ids.add(qid)

        missing = set(REQUIRED_QUESTION_IDS) - seen_ids
        if missing:
            raise serializers.ValidationError(
                f"Faltan respuestas para las preguntas: {', '.join(sorted(missing))}."
            )
        return value

    def create(self, validated_data):
        auth_user_id = self.context["auth_user_id"]
        answers_payload = {
            answer["question_id"]: answer["value"] for answer in validated_data["answers"]
        }
        submission = IntakeSubmission.objects.create(
            auth_user_id=auth_user_id,
            answers=answers_payload,
            free_text=validated_data.get("free_text", ""),
            vectorize_snapshot=validated_data.get("vectorize_snapshot", True),
        )
        return submission


class IntakeSubmissionSerializer(serializers.ModelSerializer):
    """Serializer de lectura para submissions."""

    class Meta:
        model = IntakeSubmission
        fields = [
            "id",
            "trace_id",
            "status",
            "processing_stage",
            "answers",
            "free_text",
            "vectorize_snapshot",
            "estimated_wait_seconds",
            "report_url",
            "report_storage_path",
            "report_metadata",
            "failure_reason",
            "last_error_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
