import { Component } from '@angular/core';
import { Routes } from '@angular/router';

@Component({
  standalone: true,
  selector: 'app-public-placeholder',
  template: `
    <section class="public-placeholder">
      <p>Public route placeholder</p>
    </section>
  `
})
class PublicPlaceholderComponent {}

export const publicRoutes: Routes = [
  {
    path: '',
    component: PublicPlaceholderComponent
  }
];