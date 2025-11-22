/**
 * Planes de facturación del sistema
 * Sincronizado con backend/users/models.py BillingPlan
 */
export enum BillingPlan {
  INDIVIDUAL = 'individual',
  INSTITUTION = 'institution',
  CORPORATE = 'corporate',
  B2B2C = 'b2b2c',
  TRIAL = 'trial',
}

/**
 * Labels legibles para planes
 */
export const BILLING_PLAN_LABELS: Record<BillingPlan, string> = {
  [BillingPlan.INDIVIDUAL]: 'Individual',
  [BillingPlan.INSTITUTION]: 'Institución',
  [BillingPlan.CORPORATE]: 'Corporativo',
  [BillingPlan.B2B2C]: 'B2B2C',
  [BillingPlan.TRIAL]: 'Prueba',
};

/**
 * Verifica si un billing plan es válido
 */
export function isValidBillingPlan(plan: string): plan is BillingPlan {
  return Object.values(BillingPlan).includes(plan as BillingPlan);
}
