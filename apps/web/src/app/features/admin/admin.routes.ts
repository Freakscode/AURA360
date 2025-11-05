import { Component } from '@angular/core';
import { Routes } from '@angular/router';

@Component({
  standalone: true,
  selector: 'app-admin-placeholder',
  template: `
    <section class="admin-placeholder">
      <p>Admin route placeholder</p>
    </section>
  `
})
class AdminPlaceholderComponent {}

export const adminRoutes: Routes = [
  {
    path: '',
    component: AdminPlaceholderComponent
  }
];