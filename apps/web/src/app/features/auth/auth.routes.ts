import { Routes } from '@angular/router';
import { noAuthGuard } from '../../auth/guards/no-auth.guard';

/**
 * Rutas del módulo de autenticación
 * 
 * Todas las rutas están protegidas con noAuthGuard para redirigir
 * usuarios autenticados a su dashboard correspondiente.
 */
export const authRoutes: Routes = [
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
  },
  {
    path: 'login',
    loadComponent: () => 
      import('./login/login.component').then(m => m.LoginComponent),
    canActivate: [noAuthGuard],
    title: 'Iniciar Sesión - AURA360'
  }
  // TODO: Descomentar cuando los componentes estén implementados
  // Placeholders para futuras rutas de autenticación:
  //
  // {
  //   path: 'register',
  //   loadComponent: () =>
  //     import('./register/register.component').then(m => m.RegisterComponent),
  //   canActivate: [noAuthGuard],
  //   title: 'Registro - AURA360'
  // },
  // {
  //   path: 'forgot-password',
  //   loadComponent: () =>
  //     import('./forgot-password/forgot-password.component').then(m => m.ForgotPasswordComponent),
  //   canActivate: [noAuthGuard],
  //   title: 'Recuperar Contraseña - AURA360'
  // },
  // {
  //   path: 'reset-password',
  //   loadComponent: () =>
  //     import('./reset-password/reset-password.component').then(m => m.ResetPasswordComponent),
  //   canActivate: [noAuthGuard],
  //   title: 'Restablecer Contraseña - AURA360'
  // }
];