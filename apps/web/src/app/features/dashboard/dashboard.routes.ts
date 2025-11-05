import { Component } from '@angular/core';
import { Routes } from '@angular/router';

@Component({
  standalone: true,
  selector: 'app-dashboard-placeholder',
  template: `
    <section class="dashboard-placeholder">
      <p>Dashboard route placeholder</p>
    </section>
  `
})
class DashboardPlaceholderComponent {}

export const dashboardRoutes: Routes = [
  {
    path: '',
    component: DashboardPlaceholderComponent
  }
];