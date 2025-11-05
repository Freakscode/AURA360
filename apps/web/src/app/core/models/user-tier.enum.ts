/**
 * Niveles de suscripción de usuario
 * Sincronizado con backend/users/models.py UserTier
 */
export enum UserTier {
  FREE = 'free',
  PREMIUM = 'premium',
}

/**
 * Labels legibles para tiers
 */
export const USER_TIER_LABELS: Record<UserTier, string> = {
  [UserTier.FREE]: 'Gratis',
  [UserTier.PREMIUM]: 'Premium',
};

/**
 * Verifica si un tier es válido
 */
export function isValidUserTier(tier: string): tier is UserTier {
  return Object.values(UserTier).includes(tier as UserTier);
}

/**
 * Verifica si un usuario es premium
 */
export function isPremiumTier(tier: UserTier | string | null): boolean {
  return tier === UserTier.PREMIUM;
}
