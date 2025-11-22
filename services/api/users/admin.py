"""
Configuración del panel de administración para usuarios.

Este módulo personaliza la interfaz de administración de Django
para el modelo AppUser, facilitando la gestión de usuarios.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    AppUser,
    SubscriptionTier,
    UsageLedger,
    UsageQuota,
    UserTier,
)


@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    """
    Configuración del admin para AppUser.
    
    Proporciona una interfaz completa para visualizar y gestionar usuarios
    con filtros, búsqueda, acciones en lote y vistas personalizadas.
    """
    
    # Campos a mostrar en el listado
    list_display = [
        'id',
        'full_name',
        'email',
        'tier_badge',
        'role_badge',
        'billing_plan',
        'independent_flag',
        'age',
        'created_at',
        'auth_user_id_short',
    ]
    
    # Campos para búsqueda
    search_fields = [
        'full_name',
        'email',
        'phone_number',
        'auth_user_id',
    ]
    
    # Filtros laterales
    list_filter = [
        'tier',
        'gender',
        'role_global',
        'billing_plan',
        'is_independent',
        'created_at',
        'updated_at',
    ]
    
    # Ordenamiento por defecto
    ordering = ['-created_at']
    
    # Campos de solo lectura (no editables en el admin)
    readonly_fields = [
        'id',
        'auth_user_id',
        'role_global',
        'billing_plan',
        'is_independent',
        'created_at',
        'updated_at',
    ]
    
    # Organización de campos en el formulario de edición
    fieldsets = (
        ('Identificación', {
            'fields': ('id', 'auth_user_id')
        }),
        ('Información Personal', {
            'fields': ('full_name', 'age', 'gender')
        }),
        ('Contacto', {
            'fields': ('email', 'phone_number')
        }),
        ('Rol y Plan Comercial', {
            'fields': ('role_global', 'billing_plan', 'is_independent'),
            'description': 'Metadatos sincronizados desde Supabase'
        }),
        ('Membresía', {
            'fields': ('tier',),
            'description': 'Plan de membresía del usuario'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)  # Sección colapsable
        }),
    )
    
    # Configuración de paginación
    list_per_page = 25
    
    # Habilitar acciones en lote
    actions = ['upgrade_to_premium', 'downgrade_to_free']
    
    def tier_badge(self, obj):
        """
        Muestra un badge colorido para el tier del usuario.
        """
        if obj.is_premium:
            color = '#ffc107'  # Amarillo/oro para premium
            icon = '⭐'
        else:
            color = '#6c757d'  # Gris para free
            icon = '👤'
        
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px; font-weight: bold;">'
            '{} {}</span>',
            color,
            icon,
            obj.get_tier_display()
    )
    tier_badge.short_description = 'Membresía'

    def role_badge(self, obj):
        """
        Muestra un badge para el rol global.
        """
        palette = {
            'AdminSistema': '#6f42c1',
            'AdminInstitucion': '#20c997',
            'AdminInstitucionSalud': '#17a2b8',
            'ProfesionalSalud': '#0d6efd',
            'Paciente': '#198754',
            'Institucion': '#fd7e14',
            'General': '#6c757d',
        }
        color = palette.get(obj.role_global, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_role_global_display(),
        )
    role_badge.short_description = 'Rol Global'

    def independent_flag(self, obj):
        """Indica si el usuario opera de forma independiente."""
        return obj.is_independent
    independent_flag.boolean = True
    independent_flag.short_description = 'Independiente'
    
    def auth_user_id_short(self, obj):
        """
        Muestra una versión corta del UUID de auth.
        """
        uuid_str = str(obj.auth_user_id)
        return f"{uuid_str[:8]}..."
    auth_user_id_short.short_description = 'Auth UUID'
    
    @admin.action(description='Actualizar usuarios seleccionados a Premium')
    def upgrade_to_premium(self, request, queryset):
        """
        Acción en lote para actualizar usuarios a premium.
        """
        updated = queryset.filter(tier=UserTier.FREE).update(tier=UserTier.PREMIUM)
        self.message_user(
            request,
            f'{updated} usuario(s) actualizados a Premium exitosamente.'
        )
    
    @admin.action(description='Actualizar usuarios seleccionados a Free')
    def downgrade_to_free(self, request, queryset):
        """
        Acción en lote para actualizar usuarios a free.
        """
        updated = queryset.filter(tier=UserTier.PREMIUM).update(tier=UserTier.FREE)
        self.message_user(
            request,
            f'{updated} usuario(s) actualizados a Free exitosamente.'
        )


@admin.register(SubscriptionTier)
class SubscriptionTierAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'monthly_price', 'report_frequency', 'reports_per_period']
    search_fields = ['code', 'name']
    list_filter = ['report_frequency', 'scientific_library_access', 'preventive_recommendations']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UsageQuota)
class UsageQuotaAdmin(admin.ModelAdmin):
    list_display = ['tier', 'resource_code', 'limit', 'period']
    list_filter = ['period', 'tier__code']
    search_fields = ['resource_code', 'tier__code']
    autocomplete_fields = ['tier']


@admin.register(UsageLedger)
class UsageLedgerAdmin(admin.ModelAdmin):
    list_display = ['user', 'resource_code', 'amount', 'occurred_at']
    list_filter = ['resource_code', 'occurred_at']
    search_fields = ['user__email', 'user__full_name', 'resource_code']
    autocomplete_fields = ['user', 'quota']
    readonly_fields = ['occurred_at']
