import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-admin-sistema-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="dashboard">
      <header class="dashboard__header">
        <h1>Dashboard Admin Sistema</h1>
        <p class="dashboard__subtitle">
          Panel de administración del sistema completo
        </p>
      </header>

      <div class="dashboard__grid">
        <div class="dashboard__card">
          <h2>Instituciones</h2>
          <p class="dashboard__card-value">--</p>
          <p class="dashboard__card-label">Total instituciones registradas</p>
        </div>

        <div class="dashboard__card">
          <h2>Usuarios</h2>
          <p class="dashboard__card-value">--</p>
          <p class="dashboard__card-label">Total usuarios del sistema</p>
        </div>

        <div class="dashboard__card">
          <h2>Suscripciones</h2>
          <p class="dashboard__card-value">--</p>
          <p class="dashboard__card-label">Suscripciones activas</p>
        </div>

        <div class="dashboard__card">
          <h2>Métricas</h2>
          <p class="dashboard__card-value">--</p>
          <p class="dashboard__card-label">Uso del sistema</p>
        </div>
      </div>

      <div class="dashboard__section">
        <h2>Acciones Rápidas</h2>
        <div class="dashboard__actions">
          <button class="dashboard__action-btn">Crear Institución</button>
          <button class="dashboard__action-btn">Gestionar Usuarios</button>
          <button class="dashboard__action-btn">Ver Reportes</button>
          <button class="dashboard__action-btn">Configuración Global</button>
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
export class DashboardComponent {}
