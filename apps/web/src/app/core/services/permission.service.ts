import { Injectable, inject, computed } from '@angular/core';
import { ActiveContextService } from './active-context.service';
import { GlobalRole, ADMIN_ROLES, isAdminRole } from '../models/global-role.enum';
import {
  InstitutionRole,
  INSTITUTION_ADMIN_ROLES,
  isInstitutionAdminRole,
} from '../models/institution-role.enum';
import { UserTier, isPremiumTier } from '../models/user-tier.enum';
import { BillingPlan } from '../models/billing-plan.enum';

/**
 * Servicio para verificar permisos basados en el contexto activo
 * Proporciona métodos helper para guards, directivas y lógica de negocio
 */
@Injectable({
  providedIn: 'root',
})
export class PermissionService {
  private readonly activeContextService = inject(ActiveContextService);

  /**
   * Computed: indica si el usuario tiene rol administrativo en el contexto activo
   */
  readonly isAdmin = computed(() => {
    const role = this.activeContextService.effectiveRole();
    if (!role) return false;

    return isAdminRole(role as GlobalRole) || isInstitutionAdminRole(role);
  });

  /**
   * Computed: indica si el usuario es AdminSistema
   */
  readonly isSystemAdmin = computed(() => {
    const context = this.activeContextService.activeContext();
    return context?.globalRole === GlobalRole.ADMIN_SISTEMA;
  });

  /**
   * Computed: indica si el usuario es Profesional de Salud
   */
  readonly isHealthProfessional = computed(() => {
    const role = this.activeContextService.effectiveRole();
    return (
      role === GlobalRole.PROFESIONAL_SALUD ||
      role === InstitutionRole.PROFESIONAL_SALUD
    );
  });

  /**
   * Computed: indica si el usuario tiene tier premium
   */
  readonly isPremium = computed(() => {
    const tier = this.activeContextService.effectiveTier();
    return tier === BillingPlan.INDIVIDUAL || tier === BillingPlan.INSTITUTION;
  });

  /**
   * Verifica si el usuario tiene uno de los roles especificados
   */
  hasRole(roles: (GlobalRole | InstitutionRole)[]): boolean {
    const effectiveRole = this.activeContextService.effectiveRole();
    if (!effectiveRole) return false;

    return roles.includes(effectiveRole as any);
  }

  /**
   * Verifica si el usuario tiene un rol global específico
   */
  hasGlobalRole(roles: GlobalRole[]): boolean {
    const context = this.activeContextService.activeContext();
    if (!context) return false;

    return roles.includes(context.globalRole);
  }

  /**
   * Verifica si el usuario tiene un rol institucional específico
   */
  hasInstitutionRole(roles: InstitutionRole[]): boolean {
    const context = this.activeContextService.activeContext();
    if (!context || !context.institutionRole) return false;

    return roles.includes(context.institutionRole);
  }

  /**
   * Verifica si el usuario tiene tier mínimo requerido
   */
  hasTier(minimumTier: UserTier): boolean {
    const tier = this.activeContextService.effectiveTier();
    if (!tier) return false;

    // Lógica simple: premium > free
    if (minimumTier === UserTier.PREMIUM) {
      return isPremiumTier(tier);
    }

    return true; // free tier siempre es accesible
  }

  /**
   * Verifica si el usuario tiene un billing plan específico
   */
  hasBillingPlan(plans: BillingPlan[]): boolean {
    const context = this.activeContextService.activeContext();
    if (!context) return false;

    return plans.includes(context.billingPlan);
  }

  /**
   * Verifica si el usuario está en un contexto institucional
   */
  isInInstitutionalContext(): boolean {
    return this.activeContextService.isInstitutionalContext();
  }

  /**
   * Verifica si el usuario está en un contexto independiente
   */
  isInIndependentContext(): boolean {
    return this.activeContextService.isIndependentContext();
  }

  /**
   * Verifica si el usuario pertenece a una institución específica
   */
  belongsToInstitution(institutionId: number): boolean {
    const institution = this.activeContextService.activeInstitution();
    return institution?.id === institutionId;
  }

  /**
   * Verifica si el usuario puede gestionar usuarios
   * Solo admins del sistema o de institución
   */
  canManageUsers(): boolean {
    const role = this.activeContextService.effectiveRole();
    if (!role) return false;

    const allowedRoles = [
      GlobalRole.ADMIN_SISTEMA,
      GlobalRole.ADMIN_INSTITUCION,
      GlobalRole.ADMIN_INSTITUCION_SALUD,
      InstitutionRole.ADMIN_INSTITUCION,
      InstitutionRole.ADMIN_INSTITUCION_SALUD,
    ];

    return allowedRoles.includes(role as any);
  }

  /**
   * Verifica si el usuario puede gestionar una institución
   */
  canManageInstitution(institutionId?: number): boolean {
    const context = this.activeContextService.activeContext();
    if (!context) return false;

    // AdminSistema puede gestionar cualquier institución
    if (context.globalRole === GlobalRole.ADMIN_SISTEMA) {
      return true;
    }

    // AdminInstitucion solo puede gestionar su propia institución
    const adminRoles = [
      GlobalRole.ADMIN_INSTITUCION,
      GlobalRole.ADMIN_INSTITUCION_SALUD,
      InstitutionRole.ADMIN_INSTITUCION,
      InstitutionRole.ADMIN_INSTITUCION_SALUD,
    ];

    const hasAdminRole = adminRoles.includes(context.globalRole) ||
      (context.institutionRole && adminRoles.includes(context.institutionRole));

    if (!hasAdminRole) return false;

    // Si se especifica institutionId, verificar que sea la institución del contexto
    if (institutionId !== undefined) {
      return context.institution?.id === institutionId;
    }

    return true;
  }

  /**
   * Verifica si el usuario puede ver datos clínicos
   */
  canViewClinicalData(): boolean {
    const role = this.activeContextService.effectiveRole();
    if (!role) return false;

    const allowedRoles = [
      GlobalRole.ADMIN_SISTEMA,
      GlobalRole.ADMIN_INSTITUCION_SALUD,
      GlobalRole.PROFESIONAL_SALUD,
      InstitutionRole.ADMIN_INSTITUCION_SALUD,
      InstitutionRole.PROFESIONAL_SALUD,
    ];

    return allowedRoles.includes(role as any);
  }

  /**
   * Verifica si el usuario puede acceder a features premium
   */
  canAccessPremiumFeatures(): boolean {
    return this.isPremium();
  }

  /**
   * Obtiene información del contexto activo en formato legible
   */
  getActiveContextInfo(): {
    hasContext: boolean;
    role: string | null;
    tier: string | null;
    isInstitutional: boolean;
    institutionName: string | null;
  } {
    const context = this.activeContextService.activeContext();

    return {
      hasContext: context !== null,
      role: this.activeContextService.effectiveRole(),
      tier: this.activeContextService.effectiveTier(),
      isInstitutional: this.activeContextService.isInstitutionalContext(),
      institutionName: context?.institution?.name || null,
    };
  }
}
