import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ActiveContextService } from '../../../../core/services/active-context.service';
import { CareRelationshipService } from '../../services/care-relationship.service';
import { PatientsSummary } from '../../models/care-relationship.model';

@Component({
  selector: 'app-profesional-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="dashboard">
      <header class="dashboard__header">
        <h1>Dashboard Profesional de Salud</h1>
        @if (activeContext(); as context) {
          @if (context.institution) {
            <p class="dashboard__subtitle">{{ context.institution.name }}</p>
          } @else {
            <p class="dashboard__subtitle">Práctica Independiente</p>
          }
        }
      </header>

      <div class="dashboard__grid">
        <div class="dashboard__card">
          <h2>Mis Pacientes</h2>
          @if (careService.loading()) {
            <p class="dashboard__card-value">...</p>
          } @else {
            <p class="dashboard__card-value">{{ patientsSummary()?.active ?? 0 }}</p>
          }
          <p class="dashboard__card-label">Pacientes bajo mi cuidado</p>
        </div>

        <div class="dashboard__card">
          <h2>Consultas Hoy</h2>
          <p class="dashboard__card-value">--</p>
          <p class="dashboard__card-label">Agenda del día</p>
        </div>

        <div class="dashboard__card">
          <h2>Pendientes</h2>
          <p class="dashboard__card-value">--</p>
          <p class="dashboard__card-label">Tareas por completar</p>
        </div>

        <div class="dashboard__card">
          <h2>Mensajes</h2>
          <p class="dashboard__card-value">--</p>
          <p class="dashboard__card-label">Mensajes no leídos</p>
        </div>
      </div>

      <div class="dashboard__section">
        <h2>Gestión Profesional</h2>
        <div class="dashboard__actions">
          <button class="dashboard__action-btn">Ver Agenda</button>
          <a routerLink="/profesional/pacientes" class="dashboard__action-btn">Mis Pacientes</a>
          <button class="dashboard__action-btn">Nueva Consulta</button>
          <button class="dashboard__action-btn">Historial Clínico</button>
        </div>
      </div>

      @if (patientsSummary(); as summary) {
        @if (summary.patients.length > 0) {
          <div class="dashboard__section">
            <h2>Pacientes Recientes</h2>
            <div class="patients-preview">
              @for (relationship of summary.patients.slice(0, 5); track relationship.id) {
                <div class="patient-card">
                  <div class="patient-card__info">
                    <h3>{{ relationship.patient.full_name }}</h3>
                    <p>{{ relationship.patient.email }}</p>
                  </div>
                  <div class="patient-card__meta">
                    <span [class]="'status-badge status-badge--' + relationship.status">
                      {{ relationship.status === 'active' ? 'Activo' : 'Inactivo' }}
                    </span>
                  </div>
                </div>
              }
              @if (summary.patients.length > 5) {
                <a routerLink="/profesional/pacientes" class="patients-preview__more">
                  Ver todos los {{ summary.patients.length }} pacientes →
                </a>
              }
            </div>
          </div>
        }
      }
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
        text-decoration: none;
        display: inline-block;

        &:hover {
          background: #059669;
        }
      }

      .patients-preview {
        display: flex;
        flex-direction: column;
        gap: 1rem;
      }

      .patient-card {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        transition: border-color 0.2s;

        &:hover {
          border-color: #10b981;
        }
      }

      .patient-card__info {
        h3 {
          font-size: 1rem;
          font-weight: 600;
          color: #111827;
          margin: 0 0 0.25rem 0;
        }

        p {
          font-size: 0.875rem;
          color: #6b7280;
          margin: 0;
        }
      }

      .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }

      .status-badge--active {
        background: #d1fae5;
        color: #065f46;
      }

      .status-badge--inactive,
      .status-badge--ended {
        background: #fee2e2;
        color: #991b1b;
      }

      .patients-preview__more {
        padding: 0.75rem;
        text-align: center;
        color: #10b981;
        font-weight: 500;
        text-decoration: none;
        border: 1px dashed #10b981;
        border-radius: 0.5rem;
        transition: all 0.2s;

        &:hover {
          background: #d1fae5;
          border-style: solid;
        }
      }
    `,
  ],
})
export class DashboardComponent implements OnInit {
  private readonly activeContextService = inject(ActiveContextService);
  readonly careService = inject(CareRelationshipService);

  readonly activeContext = this.activeContextService.activeContext;
  readonly patientsSummary = signal<PatientsSummary | null>(null);

  async ngOnInit(): Promise<void> {
    await this.loadPatients();
  }

  private async loadPatients(): Promise<void> {
    try {
      const summary = await this.careService.loadMyPatients();
      this.patientsSummary.set(summary);
    } catch (error) {
      console.error('Error al cargar pacientes:', error);
    }
  }
}
