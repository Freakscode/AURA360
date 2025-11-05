"""Serializadores para exponer el dominio de hábitos corporales vía API."""

from __future__ import annotations

from rest_framework import serializers

from .models import (
    BodyActivity,
    NutritionLog,
    NutritionPlan,
    SleepLog,
)


class BodyActivitySerializer(serializers.ModelSerializer):
    """Serializa sesiones de actividad física."""

    class Meta:
        model = BodyActivity
        fields = (
            'id',
            'activity_type',
            'intensity',
            'duration_minutes',
            'session_date',
            'notes',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class NutritionLogSerializer(serializers.ModelSerializer):
    """Serializa registros de nutrición."""

    protein = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        allow_null=True,
        required=False,
        coerce_to_string=False,
    )
    carbs = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        allow_null=True,
        required=False,
        coerce_to_string=False,
    )
    fats = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        allow_null=True,
        required=False,
        coerce_to_string=False,
    )

    class Meta:
        model = NutritionLog
        fields = (
            'id',
            'meal_type',
            'timestamp',
            'items',
            'calories',
            'protein',
            'carbs',
            'fats',
            'notes',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class SleepLogSerializer(serializers.ModelSerializer):
    """Serializa registros de sueño."""

    duration_hours = serializers.DecimalField(
        max_digits=4,
        decimal_places=1,
        coerce_to_string=False,
    )

    class Meta:
        model = SleepLog
        fields = (
            'id',
            'bedtime',
            'wake_time',
            'duration_hours',
            'quality',
            'notes',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class BodyDashboardSnapshotSerializer(serializers.Serializer):
    """
    Representa un resumen compuesto de la actividad corporal del usuario.

    Mantiene la misma estructura que consume la app móvil.
    """

    activities = BodyActivitySerializer(many=True)
    nutrition = NutritionLogSerializer(many=True)
    sleep = SleepLogSerializer(many=True)


class NutritionPlanSerializer(serializers.ModelSerializer):
    """
    Serializa planes nutricionales estructurados.
    
    Valida la estructura completa del plan según el esquema JSON,
    extrae metadatos clave y proporciona acceso a secciones específicas.
    """
    
    # Campos computados para facilitar el consumo
    is_valid = serializers.ReadOnlyField(help_text="Indica si el plan está vigente")
    meals = serializers.SerializerMethodField(help_text="Lista de comidas del plan")
    restrictions = serializers.SerializerMethodField(help_text="Restricciones alimentarias")
    goals = serializers.SerializerMethodField(help_text="Objetivos nutricionales")
    
    class Meta:
        model = NutritionPlan
        fields = (
            'id',
            'title',
            'language',
            'issued_at',
            'valid_until',
            'is_active',
            'is_valid',
            'plan_data',
            'source_kind',
            'source_uri',
            'extracted_at',
            'extractor',
            'meals',
            'restrictions',
            'goals',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_valid')
    
    def validate_plan_data(self, value):
        """
        Valida la estructura del plan_data contra el esquema esperado.
        
        Verifica que contenga las secciones requeridas: plan, subject, directives.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("plan_data debe ser un objeto JSON")
        
        # Validar campos requeridos de nivel superior
        required_fields = ['plan', 'subject', 'directives']
        missing = [field for field in required_fields if field not in value]
        if missing:
            raise serializers.ValidationError(
                f"Faltan campos requeridos en plan_data: {', '.join(missing)}"
            )
        
        # Validar estructura de 'plan'
        plan = value.get('plan', {})
        if not isinstance(plan, dict):
            raise serializers.ValidationError("El campo 'plan' debe ser un objeto")
        
        plan_required = ['source', 'language']
        plan_missing = [field for field in plan_required if field not in plan]
        if plan_missing:
            raise serializers.ValidationError(
                f"Faltan campos requeridos en 'plan': {', '.join(plan_missing)}"
            )
        
        # Validar estructura de 'source'
        source = plan.get('source', {})
        if not isinstance(source, dict):
            raise serializers.ValidationError("El campo 'plan.source' debe ser un objeto")
        
        if 'kind' not in source:
            raise serializers.ValidationError("El campo 'plan.source.kind' es requerido")
        
        valid_kinds = ['pdf', 'image', 'text', 'web']
        if source['kind'] not in valid_kinds:
            raise serializers.ValidationError(
                f"plan.source.kind debe ser uno de: {', '.join(valid_kinds)}"
            )
        
        # Validar estructura de 'directives'
        directives = value.get('directives', {})
        if not isinstance(directives, dict):
            raise serializers.ValidationError("El campo 'directives' debe ser un objeto")
        
        if 'meals' not in directives:
            raise serializers.ValidationError(
                "El campo 'directives.meals' es requerido"
            )
        
        meals = directives.get('meals', [])
        if not isinstance(meals, list):
            raise serializers.ValidationError("'directives.meals' debe ser una lista")
        
        # Validar cada comida tiene campos requeridos
        for idx, meal in enumerate(meals):
            if not isinstance(meal, dict):
                raise serializers.ValidationError(
                    f"La comida en posición {idx} debe ser un objeto"
                )
            if 'name' not in meal or 'components' not in meal:
                raise serializers.ValidationError(
                    f"La comida en posición {idx} requiere 'name' y 'components'"
                )
            if not isinstance(meal.get('components', []), list):
                raise serializers.ValidationError(
                    f"Los components de la comida {idx} deben ser una lista"
                )
        
        return value
    
    def validate(self, attrs):
        """
        Valida consistencia entre campos extraídos y plan_data.
        """
        plan_data = attrs.get('plan_data', {})
        
        # Sincronizar title desde plan_data si no se proporciona
        if not attrs.get('title') and 'plan' in plan_data:
            attrs['title'] = plan_data['plan'].get('title', 'Plan sin título')
        
        # Sincronizar language desde plan_data si no se proporciona
        if not attrs.get('language') and 'plan' in plan_data:
            attrs['language'] = plan_data['plan'].get('language', 'es')
        
        # Sincronizar issued_at desde plan_data
        if not attrs.get('issued_at') and 'plan' in plan_data:
            issued_str = plan_data['plan'].get('issued_at')
            if issued_str:
                from datetime import datetime
                try:
                    attrs['issued_at'] = datetime.strptime(issued_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    pass
        
        # Sincronizar valid_until desde plan_data
        if not attrs.get('valid_until') and 'plan' in plan_data:
            valid_str = plan_data['plan'].get('valid_until')
            if valid_str:
                from datetime import datetime
                try:
                    attrs['valid_until'] = datetime.strptime(valid_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    pass
        
        # Sincronizar metadatos de source
        if 'plan' in plan_data and 'source' in plan_data['plan']:
            source = plan_data['plan']['source']
            if not attrs.get('source_kind'):
                attrs['source_kind'] = source.get('kind')
            if not attrs.get('source_uri'):
                attrs['source_uri'] = source.get('uri')
            if not attrs.get('extracted_at'):
                extracted_str = source.get('extracted_at')
                if extracted_str:
                    from datetime import datetime
                    try:
                        attrs['extracted_at'] = datetime.fromisoformat(
                            extracted_str.replace('Z', '+00:00')
                        )
                    except (ValueError, TypeError):
                        pass
            if not attrs.get('extractor'):
                attrs['extractor'] = source.get('extractor')
        
        return attrs
    
    def get_meals(self, obj):
        """Extrae las comidas del plan."""
        return obj.get_meals()
    
    def get_restrictions(self, obj):
        """Extrae las restricciones alimentarias."""
        return obj.get_restrictions()
    
    def get_goals(self, obj):
        """Extrae los objetivos nutricionales."""
        return obj.get_goals()


class NutritionPlanIngestCallbackSerializer(serializers.Serializer):
    """Valida el payload recibido desde el servicio vectorial."""

    job_id = serializers.UUIDField()
    auth_user_id = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    language = serializers.CharField(max_length=10, default='es')
    issued_at = serializers.DateField(required=False, allow_null=True)
    valid_until = serializers.DateField(required=False, allow_null=True)
    is_active = serializers.BooleanField(default=True)
    plan_data = serializers.JSONField()
    metadata = serializers.JSONField(required=False)
    source = serializers.JSONField()
    extractor = serializers.JSONField()
    raw_text_excerpt = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    llm = serializers.JSONField(required=False)

    def validate_plan_data(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError('plan_data debe ser un objeto JSON.')
        return value

    def validate_source(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError('source debe ser un objeto JSON.')
        return value

    def validate_extractor(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError('extractor debe ser un objeto JSON.')
        return value
