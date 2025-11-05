import { GlobalRole } from './global-role.enum';
import { InstitutionRole } from './institution-role.enum';
import { BillingPlan } from './billing-plan.enum';
import { Institution } from './institution.interface';

/**
 * Tipo de contexto de acceso
 */
export enum AccessContextType {
  INSTITUTIONAL = 'institutional',
  INDEPENDENT = 'independent',
}

/**
 * Interfaz para contexto de acceso del usuario
 * Representa el contexto operativo actual (institucional o independiente)
 * Replicado del patrón Flutter AccessContext
 */
export interface AccessContext {
  /**
   * Tipo de contexto
   */
  type: AccessContextType;

  /**
   * Rol global del usuario
   */
  globalRole: GlobalRole;

  /**
   * Datos de institución (solo para contexto institucional)
   */
  institution: Institution | null;

  /**
   * Rol específico dentro de la institución (solo para contexto institucional)
   */
  institutionRole: InstitutionRole | null;

  /**
   * ID de la membresía (solo para contexto institucional)
   */
  membershipId: number | null;

  /**
   * Indica si es el contexto primario del usuario
   */
  isPrimary: boolean;

  /**
   * Plan de facturación asociado al contexto
   */
  billingPlan: BillingPlan;

  /**
   * Label legible para mostrar en UI
   */
  displayLabel: string;
}

/**
 * Factory para crear contexto institucional
 */
export function createInstitutionalContext(params: {
  globalRole: GlobalRole;
  institution: Institution;
  institutionRole: InstitutionRole;
  membershipId: number;
  isPrimary: boolean;
  billingPlan: BillingPlan;
}): AccessContext {
  return {
    type: AccessContextType.INSTITUTIONAL,
    globalRole: params.globalRole,
    institution: params.institution,
    institutionRole: params.institutionRole,
    membershipId: params.membershipId,
    isPrimary: params.isPrimary,
    billingPlan: params.billingPlan,
    displayLabel: `${params.institution.name} - ${params.institutionRole}`,
  };
}

/**
 * Factory para crear contexto independiente
 */
export function createIndependentContext(params: {
  globalRole: GlobalRole;
  billingPlan: BillingPlan;
}): AccessContext {
  return {
    type: AccessContextType.INDEPENDENT,
    globalRole: params.globalRole,
    institution: null,
    institutionRole: null,
    membershipId: null,
    isPrimary: false,
    billingPlan: params.billingPlan,
    displayLabel: 'Práctica Independiente',
  };
}

/**
 * Verifica si un contexto es institucional
 */
export function isInstitutionalContext(context: AccessContext): boolean {
  return context.type === AccessContextType.INSTITUTIONAL;
}

/**
 * Verifica si un contexto es independiente
 */
export function isIndependentContext(context: AccessContext): boolean {
  return context.type === AccessContextType.INDEPENDENT;
}
