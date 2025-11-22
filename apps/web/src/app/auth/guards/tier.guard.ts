import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { PermissionService } from '../../core/services/permission.service';
import { ActiveContextService } from '../../core/services/active-context.service';
import { UserTier } from '../../core/models/user-tier.enum';

/**
 * Factory function para crear un guard de tier/suscripción.
 * Verifica que el usuario tenga el tier mínimo requerido.
 *
 * @param minimumTier - Tier mínimo requerido (default: premium)
 * @returns CanActivateFn guard
 *
 * @example
 * ```typescript
 * {
 *   path: 'premium-features',
 *   canActivate: [tierGuard(UserTier.PREMIUM)]
 * }
 * ```
 */
export function tierGuard(minimumTier: UserTier = UserTier.PREMIUM): CanActivateFn {
  return () => {
    const permissionService = inject(PermissionService);
    const activeContextService = inject(ActiveContextService);
    const router = inject(Router);

    // Verificar que haya un contexto activo
    if (!activeContextService.hasActiveContext()) {
      console.warn('Tier guard: No active context');
      return router.parseUrl('/auth/login');
    }

    // Verificar que el usuario tenga el tier mínimo
    if (!permissionService.hasTier(minimumTier)) {
      console.warn('Tier guard: User does not have required tier', minimumTier);
      return router.parseUrl('/upgrade'); // Redirect a página de upgrade
    }

    return true;
  };
}