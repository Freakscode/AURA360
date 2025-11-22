import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { PermissionService } from '../../core/services/permission.service';
import { ActiveContextService } from '../../core/services/active-context.service';

/**
 * Guards admin-only routes.
 * Verifica que el usuario tenga rol administrativo en el contexto activo.
 */
export const adminGuard: CanActivateFn = () => {
  const permissionService = inject(PermissionService);
  const activeContextService = inject(ActiveContextService);
  const router = inject(Router);

  // Verificar que haya un contexto activo
  if (!activeContextService.hasActiveContext()) {
    console.warn('Admin guard: No active context');
    return router.parseUrl('/auth/login');
  }

  // Verificar que el usuario tenga rol administrativo
  if (!permissionService.isAdmin()) {
    console.warn('Admin guard: User is not admin');
    return router.parseUrl('/'); // Redirect a home o dashboard general
  }

  return true;
};