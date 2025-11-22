import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthSessionStore } from '../../features/auth/services/auth-session.store';

/**
 * Guard que protege rutas de autenticación (login, register, etc.)
 * 
 * Verifica si el usuario ya está autenticado usando AuthSessionStore.
 * Si está autenticado, redirige al dashboard correspondiente según su rol.
 * Si no está autenticado, permite el acceso a la ruta.
 * 
 * @example
 * ```typescript
 * {
 *   path: 'login',
 *   component: LoginComponent,
 *   canActivate: [noAuthGuard]
 * }
 * ```
 */
export const noAuthGuard: CanActivateFn = () => {
  const authSessionStore = inject(AuthSessionStore);
  const router = inject(Router);

  // Verificar si el usuario ya está autenticado
  if (!authSessionStore.isAuthenticated()) {
    // Usuario no autenticado, permitir acceso a la ruta de auth
    return true;
  }

  // Usuario ya autenticado, redirigir según su rol
  const role = authSessionStore.userRole();
  
  /**
   * Mapa de redirección por rol según la arquitectura del sistema
   */
  const roleRedirectMap: Record<string, string> = {
    'AdminSistema': '/admin',
    'AdminClinica': '/clinic-admin',
    'Medico': '/doctor',
    'Paciente': '/dashboard'
  };

  // Obtener ruta de redirección según el rol, con fallback a dashboard
  const redirectTo = role ? roleRedirectMap[role] || '/dashboard' : '/dashboard';

  return router.createUrlTree([redirectTo]);
};