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
  {
    path: 'consultas',
    loadComponent: () =>
      import('./pages/consultas/consultas.component').then((m) => m.ConsultasComponent),
  },
  {
    path: 'historial',
    loadComponent: () =>
      import('./pages/historial/historial.component').then((m) => m.HistorialComponent),
  },
  {
    path: 'mensajes',
    loadComponent: () =>
      import('./pages/mensajes/mensajes.component').then((m) => m.MensajesComponent),
  },
  {
    path: 'herramientas/planificador',
    loadComponent: () =>
      import('./pages/nutrition-tools/meal-planner/meal-planner.component').then(
        (m) => m.MealPlannerComponent
      ),
  },
  {
    path: 'herramientas/antropometria',
    loadComponent: () =>
      import('./pages/nutrition-tools/anthropometry/anthropometry.component').then(
        (m) => m.AnthropometryComponent
      ),
  },
];
