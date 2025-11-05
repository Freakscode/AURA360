import { Routes } from '@angular/router';

export const profesionalRoutes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/dashboard/dashboard.component').then((m) => m.DashboardComponent),
  },
  {
    path: 'pacientes',
    loadComponent: () =>
      import('./pages/patients-list/patients-list.component').then(
        (m) => m.PatientsListComponent
      ),
  },
  {
    path: 'pacientes/:id',
    loadComponent: () =>
      import('./pages/patient-detail/patient-detail.component').then(
        (m) => m.PatientDetailComponent
      ),
    data: { prerender: false },
  },
];
