from __future__ import annotations

from typing import Any

from rest_framework import serializers

from .models import HolisticCategory, HolisticRequestStatus


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