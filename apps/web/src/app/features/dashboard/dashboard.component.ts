import { Component, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatGridListModule } from '@angular/material/grid-list';
import { AuthSessionStore } from '../auth/services/auth-session.store';

interface Activity {
  id: string;
  title: string;
  time: string;
  type: 'mind' | 'body' | 'soul';
  icon: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatGridListModule
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent {
  private readonly authSessionStore = inject(AuthSessionStore);

  readonly userName = computed(() => {
    const name = this.authSessionStore.userFullName();
    return name ? name.split(' ')[0] : 'Usuario';
  });

  // Mock data for the prototype
  readonly activities = computed<Activity[]>(() => [
    {
      id: '1',
      title: 'Meditación Matutina Completada',
      time: 'Hace 2 horas',
      type: 'mind',
      icon: 'self_improvement'
    },
    {
      id: '2',
      title: 'Registro de Caminata (5km)',
      time: 'Hace 4 horas',
      type: 'body',
      icon: 'directions_walk'
    },
    {
      id: '3',
      title: 'Lectura Diaria de Ikigai',
      time: 'Ayer',
      type: 'soul',
      icon: 'menu_book'
    },
    {
      id: '4',
      title: 'Registro de Hidratación',
      time: 'Ayer',
      type: 'body',
      icon: 'water_drop'
    }
  ]);
}
