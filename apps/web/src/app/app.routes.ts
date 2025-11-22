import { Routes } from '@angular/router';

import { AppShellComponent } from './core/layout/app-shell.component';
import { adminGuard } from './auth/guards/admin.guard';
import { authGuard } from './auth/guards/auth.guard';
import { noAuthGuard } from './auth/guards/no-auth.guard';
import { roleGuard } from './auth/guards/role.guard';
import { GlobalRole } from './core/models/global-role.enum';
import { InstitutionRole } from './core/models/institution-role.enum';

export const routes: Routes = [
  {
    path: '',
    canActivate: [authGuard],
    component: AppShellComponent,
    children: [
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'dashboard',
      },
      // Dashboard genérico (redirige según rol)
      {
        path: 'dashboard',
        loadChildren: () =>
          import('./features/dashboard/dashboard.routes').then((m) => m.dashboardRoutes),
      },
      // Rutas por rol - Admin Sistema
      {
        path: 'admin-sistema',
        canActivate: [roleGuard([GlobalRole.ADMIN_SISTEMA])],
        loadChildren: () =>
          import('./features/admin-sistema/admin-sistema.routes').then(
            (m) => m.adminSistemaRoutes
          ),
      },
      // Rutas por rol - Admin Institución
      {
        path: 'admin-institucion',
        canActivate: [
          roleGuard([GlobalRole.ADMIN_INSTITUCION, InstitutionRole.ADMIN_INSTITUCION]),
        ],
        loadChildren: () =>
          import('./features/admin-institucion/admin-institucion.routes').then(
            (m) => m.adminInstitucionRoutes
          ),
      },
      // Rutas por rol - Admin Institución de Salud
      {
        path: 'admin-salud',
        canActivate: [
          roleGuard([
            GlobalRole.ADMIN_INSTITUCION_SALUD,
            InstitutionRole.ADMIN_INSTITUCION_SALUD,
          ]),
        ],
        loadChildren: () =>
          import('./features/admin-salud/admin-salud.routes').then((m) => m.adminSaludRoutes),
      },
      // Rutas por rol - Profesional de Salud
      {
        path: 'profesional',
        canActivate: [
          roleGuard([GlobalRole.PROFESIONAL_SALUD, InstitutionRole.PROFESIONAL_SALUD]),
        ],
        loadChildren: () =>
          import('./features/profesional/profesional.routes').then((m) => m.profesionalRoutes),
      },
      // Rutas por rol - Paciente
      {
        path: 'paciente',
        canActivate: [roleGuard([GlobalRole.PACIENTE, InstitutionRole.PACIENTE])],
        loadChildren: () =>
          import('./features/paciente/paciente.routes').then((m) => m.pacienteRoutes),
      },
      // Rutas por rol - General (usuario sin rol específico)
      {
        path: 'general',
        canActivate: [roleGuard([GlobalRole.GENERAL])],
        loadChildren: () =>
          import('./features/general/general.routes').then((m) => m.generalRoutes),
      },
      // Ruta de administración antigua (compatibilidad)
      {
        path: 'admin',
        redirectTo: 'admin-sistema',
        pathMatch: 'full',
      },
    ],
  },
  {
    path: 'auth',
    canActivate: [noAuthGuard],
    loadChildren: () => import('./features/auth/auth.routes').then((m) => m.authRoutes),
  },
  {
    path: 'public',
    loadChildren: () => import('./features/public/public.routes').then((m) => m.publicRoutes),
  },
  {
    path: '**',
    redirectTo: '',
  },
];
