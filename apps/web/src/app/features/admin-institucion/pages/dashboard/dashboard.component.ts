import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActiveContextService } from '../../../../core/services/active-context.service';

@Component({
  selector: 'app-admin-institucion-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="dashboard">
      <header class="dashboard__header">
        <h1>Dashboard Admin Institución</h1>
        @if (activeInstitution(); as institution) {
          <p class="dashboard__subtitle">{{ institution.name }}</p>
        }
      </header>

      <div class="dashboard__grid">
        <div class="dashboard__card">
          <h2>Miembros</h2>
          <p class="dashboard__card-value">--</p>
          <p class="dashboard__card-label">Total miembros de la institución</p>
        </div>

        <div class="dashboard__card">
          <h2>Departamentos</h2>
          <p class="dashboard__card-value">--</p>
          <p class="dashboard__card-label">Departamentos activos</p>
        </div>

        <div class="dashboard__card">
          <h2>Actividad</h2>
          <p class="dashboard__card-value">--</p>
          <p class="dashboard__card-label">Actividad del mes</p>
        </div>

        <div class="dashboard__card">
          <h2>Suscripción</h2>
          <p class="dashboard__card-value">Activa</p>
          <p class="dashboard__card-label">Estado del plan</p>
        </div>
      </div>

      <div class="dashboard__section">
        <h2>Gestión Institucional</h2>
        <div class="dashboard__actions">
          <button class="dashboard__action-btn">Gestionar Miembros</button>
          <button class="dashboard__action-btn">Ver Departamentos</button>
          <button class="dashboard__action-btn">Reportes</button>
          <button class="dashboard__action-btn">Configuración</button>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .dashboard {
        padding: 2rem;
      }

      .dashboard__header {
        margin-bottom: 2rem;

        h1 {
          font-size: 2rem;
          font-weight: 700;
          color: #111827;
          margin: 0 0 0.5rem 0;
        }
      }

      .dashboard__subtitle {
        font-size: 1rem;
        color: #6b7280;
        margin: 0;
      }

      .dashboard__grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
      }

      .dashboard__card {
        padding: 1.5rem;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;

        h2 {
          font-size: 0.875rem;
          font-weight: 600;
          color: #6b7280;
          margin: 0 0 1rem 0;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
      }

      .dashboard__card-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #111827;
        margin: 0 0 0.5rem 0;
      }

      .dashboard__card-label {
        font-size: 0.875rem;
        color: #6b7280;
        margin: 0;
      }

      .dashboard__section {
        margin-bottom: 2rem;

        h2 {
          font-size: 1.25rem;
          font-weight: 600;
          color: #111827;
          margin: 0 0 1rem 0;
        }
      }

      .dashboard__actions {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
      }

      .dashboard__action-btn {
        padding: 0.75rem 1.5rem;
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 0.375rem;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.2s;

        &:hover {
          background: #2563eb;
        }
      }
    `,
  ],
})
export class DashboardComponent {
  private readonly activeContextService = inject(ActiveContextService);
  readonly activeInstitution = this.activeContextService.activeInstitution;
}
