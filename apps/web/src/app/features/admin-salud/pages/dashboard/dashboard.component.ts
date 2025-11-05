import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActiveContextService } from '../../../../core/services/active-context.service';

@Component({
  selector: 'app-admin-salud-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="dashboard">
      <header class="dashboard__header">
        <h1>Dashboard Admin Institución de Salud</h1>
        @if (activeInstitution(); as institution) {
          <p class="dashboard__subtitle">{{ institution.name }}</p>
        }
      </header>

      <div class="dashboard__grid">
        <div class="dashboard__card">
          <h2>Profesionales</h2>
          <p class="dashboard__card-value">--</p>
          <p class="dashboard__card-label">Profesionales activos</p>
        </div>

        <div class="dashboard__card">
          <h2>Pacientes</h2>
          <p class="dashboard__card-value">--</p>
          <p class="dashboard__card-label">Pacientes registrados</p>
        </div>

        <div class="dashboard__card">
          <h2>Consultas</h2>
          <p class="dashboard__card-value">--</p>
          <p class="dashboard__card-label">Consultas del mes</p>
        </div>

        <div class="dashboard__card">
          <h2>Ocupación</h2>
          <p class="dashboard__card-value">--%</p>
          <p class="dashboard__card-label">Capacidad utilizada</p>
        </div>
      </div>

      <div class="dashboard__section">
        <h2>Gestión Clínica</h2>
        <div class="dashboard__actions">
          <button class="dashboard__action-btn">Gestionar Profesionales</button>
          <button class="dashboard__action-btn">Registro de Pacientes</button>
          <button class="dashboard__action-btn">Agenda Clínica</button>
          <button class="dashboard__action-btn">Reportes Médicos</button>
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
        background: #10b981;
        color: white;
        border: none;
        border-radius: 0.375rem;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.2s;

        &:hover {
          background: #059669;
        }
      }
    `,
  ],
})
export class DashboardComponent {
  private readonly activeContextService = inject(ActiveContextService);
  readonly activeInstitution = this.activeContextService.activeInstitution;
}
