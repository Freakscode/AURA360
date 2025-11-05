import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { PermissionService } from '../../core/services/permission.service';
import { ActiveContextService } from '../../core/services/active-context.service';
import { GlobalRole } from '../../core/models/global-role.enum';
import { InstitutionRole } from '../../core/models/institution-role.enum';

/**
 * Factory function para crear un guard de rol específico.
 * Verifica que el usuario tenga uno de los roles permitidos.
 *
 * @param allowedRoles - Array de roles globales o institucionales permitidos
 * @returns CanActivateFn guard
 *
 * @example
 * ```typescript
 * {
 *   path: 'profesional',
 *   canActivate: [roleGuard([GlobalRole.PROFESIONAL_SALUD])]
 * }
 * ```
 */
export function roleGuard(
  allowedRoles: (GlobalRole | InstitutionRole)[]
): CanActivateFn {
  return () => {
    const permissionService = inject(PermissionService);
    const activeContextService = inject(ActiveContextService);
    const router = inject(Router);

    // Verificar que haya un contexto activo
    if (!activeContextService.hasActiveContext()) {
      console.warn('Role guard: No active context');
      return router.parseUrl('/auth/login');
    }

    // Verificar que el usuario tenga uno de los roles permitidos
    if (!permissionService.hasRole(allowedRoles)) {
      console.warn(
        'Role guard: User does not have required roles',
        allowedRoles
      );
      return router.parseUrl('/'); // Redirect a home o dashboard general
    }

    return true;
  };
}