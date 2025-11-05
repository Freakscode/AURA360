import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthSessionStore } from '../../features/auth/services/auth-session.store';

/**
 * Guard que protege rutas autenticadas
 * 
 * Verifica si el usuario tiene una sesión activa usando AuthSessionStore.
 * Si no está autenticado, redirige a /auth/login guardando la URL intentada
 * para redirección post-login.
 * 
 * @example
 * ```typescript
 * {
 *   path: 'dashboard',
 *   component: DashboardComponent,
 *   canActivate: [authGuard]
 * }
 * ```
 */
export const authGuard: CanActivateFn = (route, state) => {
  const authSessionStore = inject(AuthSessionStore);
  const router = inject(Router);

  // Verificar si hay sesión activa
  if (authSessionStore.isAuthenticated()) {
    return true;
  }

  // Usuario no autenticado, redirigir a login
  // Guardar URL intentada para redirección post-login
  return router.createUrlTree(['/auth/login'], {
    queryParams: { returnUrl: state.url }
  });
};