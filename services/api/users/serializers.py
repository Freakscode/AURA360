"""
Serializers para la aplicación de usuarios.

Los serializers convierten los modelos Django en JSON y viceversa,
manejando la validación y transformación de datos para la API REST.
"""

from rest_framework import serializers
from .models import AppUser, BillingPlan, GlobalRole, UserTier, UsageLedger


class AppUserSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo AppUser.
    
    Incluye todos los campos del modelo y añade campos computados
    como is_premium e is_free.
    
    Este serializer se usa para operaciones de lectura y escritura completas.
    """
    
    # Campos computados (solo lectura)
    is_premium = serializers.BooleanField(read_only=True)
    is_free = serializers.BooleanField(read_only=True)
    tier_display = serializers.CharField(
        source='get_tier_display',
        read_only=True,
        help_text="Nombre legible del tier"
    )
    role_global_display = serializers.CharField(
        source='get_role_global_display',
        read_only=True,
        help_text="Nombre legible del rol global"
    )
    billing_plan_display = serializers.CharField(
        source='get_billing_plan_display',
        read_only=True,
        help_text="Nombre legible del plan comercial"
    )
    operates_independently = serializers.BooleanField(read_only=True)
    is_admin = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = AppUser
        fields = [
            'id',
            'auth_user_id',
            'full_name',
            'age',
            'email',
            'phone_number',
            'gender',
            'tier',
            'tier_display',
            'role_global',
            'role_global_display',
            'billing_plan',
            'billing_plan_display',
            'is_independent',
            'operates_independently',
            'is_admin',
            'is_premium',
            'is_free',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'is_premium',
            'is_free',
            'tier_display',
            'role_global',
            'role_global_display',
            'billing_plan',
            'billing_plan_display',
            'is_independent',
            'operates_independently',
            'is_admin',
        ]
    
    def validate_age(self, value):
        """
        Valida que la edad sea un valor positivo razonable.
        """
        if value < 0:
            raise serializers.ValidationError("La edad no puede ser negativa.")
        if value > 150:
            raise serializers.ValidationError("La edad parece inválida.")
        return value
    
    def validate_email(self, value):
        """
        Valida el formato del email y normaliza a minúsculas.
        """
        return value.lower().strip()
    
    def validate_tier(self, value):
        """
        Valida que el tier sea uno de los valores permitidos.
        """
        if value not in [choice[0] for choice in UserTier.choices]:
            raise serializers.ValidationError(
                f"Tier inválido. Debe ser uno de: {', '.join([c[0] for c in UserTier.choices])}"
            )
        return value


class AppUserListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listados de usuarios.
    
    Solo incluye los campos esenciales para optimizar el payload
    en operaciones de listado donde se devuelven múltiples usuarios.
    """
    
    tier_display = serializers.CharField(
        source='get_tier_display',
        read_only=True
    )
    role_global_display = serializers.CharField(
        source='get_role_global_display',
        read_only=True
    )
    billing_plan_display = serializers.CharField(
        source='get_billing_plan_display',
        read_only=True
    )
    
    class Meta:
        model = AppUser
        fields = [
            'id',
            'auth_user_id',
            'full_name',
            'email',
            'tier',
            'tier_display',
            'role_global',
            'role_global_display',
            'billing_plan',
            'billing_plan_display',
            'is_independent',
            'created_at',
        ]
        read_only_fields = fields


class AppUserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para creación de usuarios.
    
    Enfocado en los campos requeridos para crear un nuevo usuario.
    Nota: En producción, la creación de usuarios debería manejarse
    principalmente a través de Supabase Auth con triggers.
    """
    
    class Meta:
        model = AppUser
        fields = [
            'auth_user_id',
            'full_name',
            'age',
            'email',
            'phone_number',
            'gender',
            'tier',
        ]
    
    def validate(self, data):
        """
        Validación a nivel de objeto.
        """
        # Asegurar que el tier tenga un valor por defecto
        if 'tier' not in data:
            data['tier'] = UserTier.FREE
        
        return data


class AppUserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualización de usuarios.
    
    Permite actualizar solo los campos del perfil, manteniendo
    auth_user_id como inmutable.
    """
    
    class Meta:
        model = AppUser
        fields = [
            'full_name',
            'age',
            'phone_number',
            'gender',
            'tier',
        ]
    
    def validate(self, data):
        """
        Validación personalizada para actualizaciones.
        """
        # Prevenir cambios no autorizados de tier
        # (en producción, esto debería estar protegido por permisos)
        if 'tier' in data:
            # Aquí podrías añadir lógica para validar que solo
            # ciertos roles pueden cambiar el tier
            pass
        
        return data


class SupabaseUserMetadataSerializer(serializers.Serializer):
    """Metadata de usuario que se sincroniza con public.app_users vía Supabase."""

    full_name = serializers.CharField()
    role_global = serializers.ChoiceField(choices=GlobalRole.choices)
    billing_plan = serializers.ChoiceField(choices=BillingPlan.choices)
    tier = serializers.ChoiceField(choices=UserTier.choices)
    is_independent = serializers.BooleanField(default=False)
    age = serializers.IntegerField(required=False, min_value=0, default=0)
    gender = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_gender(self, value):
        if value is None:
            return None
        text = value.strip()
        return text or None

    def validate_phone_number(self, value):
        if value is None:
            return None
        phone = value.strip()
        return phone or None


class SupabaseAdminUserCreateSerializer(serializers.Serializer):
    """Payload para provisionar usuarios vía Supabase Admin API."""

    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, max_length=128)
    email_confirm = serializers.BooleanField(default=False)
    user_metadata = SupabaseUserMetadataSerializer()
    app_metadata = serializers.JSONField(required=False)

    def validate_email(self, value: str) -> str:
        return value.lower().strip()

    def validate_password(self, value: str) -> str:
        if value.strip() != value:
            raise serializers.ValidationError(
                'La contraseña no debe contener espacios al inicio o final.',
            )
        return value


class AppUserRoleUpdateSerializer(serializers.Serializer):
    """Permite actualizar información básica de rol para AppUser."""

    role_global = serializers.ChoiceField(choices=GlobalRole.choices, required=False)
    is_independent = serializers.BooleanField(required=False)
    billing_plan = serializers.ChoiceField(choices=BillingPlan.choices, required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError('Debes especificar al menos un campo para actualizar.')
        return attrs


class AppUserSummarySerializer(serializers.Serializer):
    """
    Serializer para estadísticas y resúmenes de usuarios.
    
    No está vinculado a un modelo específico, útil para
    endpoints que devuelven agregaciones.
    """
    
    total_users = serializers.IntegerField(
        help_text="Número total de usuarios"
    )
    free_users = serializers.IntegerField(
        help_text="Usuarios con membresía gratuita"
    )
    premium_users = serializers.IntegerField(
        help_text="Usuarios con membresía premium"
    )
    average_age = serializers.FloatField(
        help_text="Edad promedio de usuarios"
    )


class UsageLedgerSerializer(serializers.ModelSerializer):
    """Serializer para movimientos de consumo de cuotas."""

    class Meta:
        model = UsageLedger
        fields = [
            'id',
            'resource_code',
            'amount',
            'occurred_at',
            'metadata',
        ]
        read_only_fields = fields


class QuotaStatusSerializer(serializers.Serializer):
    """Serializer para el estado agregado de una cuota."""

    resource_code = serializers.CharField()
    limit = serializers.IntegerField(allow_null=True)
    period = serializers.CharField()
    consumed = serializers.IntegerField()
    remaining = serializers.IntegerField(allow_null=True)
    unlimited = serializers.BooleanField()
