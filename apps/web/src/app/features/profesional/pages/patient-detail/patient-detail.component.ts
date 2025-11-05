import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CareRelationshipService } from '../../services/care-relationship.service';
import { CareRelationshipWithPatient } from '../../models/care-relationship.model';

@Component({
  selector: 'app-patient-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="patient-detail">
      @if (loading()) {
        <div class="patient-detail__loading">
          <p>Cargando información del paciente...</p>
        </div>
      } @else if (error()) {
        <div class="patient-detail__error">
          <p>{{ error() }}</p>
          <a routerLink="/profesional/pacientes" class="btn btn--secondary">Volver a la lista</a>
        </div>
      } @else if (relationship(); as rel) {
        <header class="patient-detail__header">
          <div class="header__breadcrumb">
            <a routerLink="/profesional" class="breadcrumb__link">Dashboard</a>
            <span class="breadcrumb__separator">/</span>
            <a routerLink="/profesional/pacientes" class="breadcrumb__link">Pacientes</a>
            <span class="breadcrumb__separator">/</span>
            <span class="breadcrumb__current">{{ rel.patient.full_name }}</span>
          </div>
          <h1>Perfil del Paciente</h1>
        </header>

        <div class="patient-detail__grid">
          <!-- Información Personal -->
          <section class="detail-card">
            <div class="detail-card__header">
              <h2>Información Personal</h2>
              <span [class]="'status-badge status-badge--' + rel.status">
                {{ getStatusLabel(rel.status) }}
              </span>
            </div>
            <div class="detail-card__content">
              <div class="info-grid">
                <div class="info-item">
                  <span class="info-item__label">Nombre Completo</span>
                  <span class="info-item__value">{{ rel.patient.full_name }}</span>
                </div>
                <div class="info-item">
                  <span class="info-item__label">Email</span>
                  <span class="info-item__value">{{ rel.patient.email }}</span>
                </div>
                <div class="info-item">
                  <span class="info-item__label">Teléfono</span>
                  <span class="info-item__value">{{ rel.patient.phone_number || 'No registrado' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-item__label">Edad</span>
                  <span class="info-item__value">{{ rel.patient.age || 'No registrada' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-item__label">Género</span>
                  <span class="info-item__value">{{ formatGender(rel.patient.gender) }}</span>
                </div>
                <div class="info-item">
                  <span class="info-item__label">Rol</span>
                  <span class="info-item__value">{{ rel.patient.role_global }}</span>
                </div>
              </div>
            </div>
          </section>

          <!-- Información de la Relación -->
          <section class="detail-card">
            <div class="detail-card__header">
              <h2>Relación de Cuidado</h2>
            </div>
            <div class="detail-card__content">
              <div class="info-grid">
                <div class="info-item">
                  <span class="info-item__label">Contexto</span>
                  <span [class]="'context-badge context-badge--' + rel.context_type">
                    {{ rel.context_type === 'independent' ? 'Independiente' : 'Institucional' }}
                  </span>
                </div>
                <div class="info-item">
                  <span class="info-item__label">Fecha de Inicio</span>
                  <span class="info-item__value">{{ formatDate(rel.started_at) }}</span>
                </div>
                @if (rel.ended_at) {
                  <div class="info-item">
                    <span class="info-item__label">Fecha de Finalización</span>
                    <span class="info-item__value">{{ formatDate(rel.ended_at) }}</span>
                  </div>
                }
                @if (rel.notes) {
                  <div class="info-item info-item--full">
                    <span class="info-item__label">Notas</span>
                    <span class="info-item__value">{{ rel.notes }}</span>
                  </div>
                }
              </div>
            </div>
          </section>

          <!-- Historial de Consultas -->
          <section class="detail-card detail-card--full">
            <div class="detail-card__header">
              <h2>Historial de Consultas</h2>
              <button class="btn btn--primary btn--sm">Nueva Consulta</button>
            </div>
            <div class="detail-card__content">
              @if (consultations().length === 0) {
                <div class="empty-state">
                  <p>No hay consultas registradas aún.</p>
                  <button class="btn btn--primary">Registrar Primera Consulta</button>
                </div>
              } @else {
                <div class="consultations-list">
                  @for (consultation of consultations(); track consultation.id) {
                    <div class="consultation-item">
                      <div class="consultation-item__date">{{ consultation.date }}</div>
                      <div class="consultation-item__content">
                        <h4>{{ consultation.title }}</h4>
                        <p>{{ consultation.summary }}</p>
                      </div>
                      <div class="consultation-item__actions">
                        <button class="btn btn--ghost btn--sm">Ver Detalles</button>
                      </div>
                    </div>
                  }
                </div>
              }
            </div>
          </section>

          <!-- Plan Nutricional -->
          <section class="detail-card detail-card--full">
            <div class="detail-card__header">
              <h2>Plan Nutricional</h2>
              <button class="btn btn--primary btn--sm">Editar Plan</button>
            </div>
            <div class="detail-card__content">
              @if (!nutritionPlan()) {
                <div class="empty-state">
                  <p>No hay un plan nutricional asignado.</p>
                  <button class="btn btn--primary">Crear Plan Nutricional</button>
                </div>
              } @else {
                <div class="nutrition-plan">
                  <div class="nutrition-plan__summary">
                    <div class="summary-item">
                      <span class="summary-item__label">Objetivo</span>
                      <span class="summary-item__value">{{ nutritionPlan()!.goal }}</span>
                    </div>
                    <div class="summary-item">
                      <span class="summary-item__label">Calorías Diarias</span>
                      <span class="summary-item__value">{{ nutritionPlan()!.calories }} kcal</span>
                    </div>
                    <div class="summary-item">
                      <span class="summary-item__label">Última Actualización</span>
                      <span class="summary-item__value">{{ nutritionPlan()!.lastUpdate }}</span>
                    </div>
                  </div>
                  <div class="nutrition-plan__details">
                    <h4>Recomendaciones</h4>
                    <ul>
                      @for (recommendation of nutritionPlan()!.recommendations; track $index) {
                        <li>{{ recommendation }}</li>
                      }
                    </ul>
                  </div>
                </div>
              }
            </div>
          </section>

          <!-- Acciones -->
          <section class="detail-card detail-card--full">
            <div class="detail-card__content">
              <div class="actions-bar">
                <a routerLink="/profesional/pacientes" class="btn btn--secondary">
                  ← Volver a la Lista
                </a>
                @if (rel.status === 'active') {
                  <button class="btn btn--danger" (click)="endRelationship()">
                    Finalizar Relación
                  </button>
                }
              </div>
            </div>
          </section>
        </div>
      }
    </div>
  `,
  styles: [
    `
      .patient-detail {
        padding: 2rem;
        max-width: 1400px;
        margin: 0 auto;
      }

      .patient-detail__header {
        margin-bottom: 2rem;

        h1 {
          font-size: 2rem;
          font-weight: 700;
          color: #111827;
          margin: 0.5rem 0 0 0;
        }
      }

      .header__breadcrumb {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.875rem;
        margin-bottom: 0.5rem;
      }

      .breadcrumb__link {
        color: #6b7280;
        text-decoration: none;
        transition: color 0.2s;

        &:hover {
          color: #10b981;
        }
      }

      .breadcrumb__separator {
        color: #d1d5db;
      }

      .breadcrumb__current {
        color: #111827;
        font-weight: 500;
      }

      .patient-detail__loading,
      .patient-detail__error {
        padding: 3rem;
        text-align: center;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;

        p {
          margin: 0 0 1rem 0;
          color: #6b7280;
        }
      }

      .patient-detail__error {
        border-color: #fca5a5;
        background: #fef2f2;

        p {
          color: #dc2626;
        }
      }

      .patient-detail__grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1.5rem;
      }

      .detail-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        overflow: hidden;

        &--full {
          grid-column: 1 / -1;
        }
      }

      .detail-card__header {
        padding: 1.5rem;
        background: #f9fafb;
        border-bottom: 1px solid #e5e7eb;
        display: flex;
        justify-content: space-between;
        align-items: center;

        h2 {
          font-size: 1.125rem;
          font-weight: 600;
          color: #111827;
          margin: 0;
        }
      }

      .detail-card__content {
        padding: 1.5rem;
      }

      .info-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1.5rem;
      }

      .info-item {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;

        &--full {
          grid-column: 1 / -1;
        }
      }

      .info-item__label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }

      .info-item__value {
        font-size: 1rem;
        color: #111827;
        font-weight: 500;
      }

      .status-badge,
      .context-badge {
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

      .context-badge--independent {
        background: #dbeafe;
        color: #1e40af;
      }

      .context-badge--institutional {
        background: #fef3c7;
        color: #92400e;
      }

      .empty-state {
        padding: 3rem;
        text-align: center;

        p {
          margin: 0 0 1.5rem 0;
          color: #6b7280;
        }
      }

      .consultations-list {
        display: flex;
        flex-direction: column;
        gap: 1rem;
      }

      .consultation-item {
        display: grid;
        grid-template-columns: 120px 1fr auto;
        gap: 1.5rem;
        padding: 1rem;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        transition: border-color 0.2s;

        &:hover {
          border-color: #10b981;
        }
      }

      .consultation-item__date {
        font-size: 0.875rem;
        font-weight: 600;
        color: #6b7280;
      }

      .consultation-item__content {
        h4 {
          font-size: 1rem;
          font-weight: 600;
          color: #111827;
          margin: 0 0 0.5rem 0;
        }

        p {
          font-size: 0.875rem;
          color: #6b7280;
          margin: 0;
        }
      }

      .nutrition-plan__summary {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
        margin-bottom: 2rem;
        padding-bottom: 2rem;
        border-bottom: 1px solid #e5e7eb;
      }

      .summary-item {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
      }

      .summary-item__label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }

      .summary-item__value {
        font-size: 1.25rem;
        color: #111827;
        font-weight: 600;
      }

      .nutrition-plan__details {
        h4 {
          font-size: 1rem;
          font-weight: 600;
          color: #111827;
          margin: 0 0 1rem 0;
        }

        ul {
          margin: 0;
          padding-left: 1.5rem;

          li {
            color: #374151;
            margin-bottom: 0.5rem;
            line-height: 1.6;
          }
        }
      }

      .actions-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .btn {
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 0.375rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
        display: inline-block;

        &--sm {
          padding: 0.5rem 1rem;
          font-size: 0.875rem;
        }

        &--primary {
          background: #10b981;
          color: white;

          &:hover {
            background: #059669;
          }
        }

        &--secondary {
          background: #f3f4f6;
          color: #374151;

          &:hover {
            background: #e5e7eb;
          }
        }

        &--danger {
          background: #ef4444;
          color: white;

          &:hover {
            background: #dc2626;
          }
        }

        &--ghost {
          background: transparent;
          color: #10b981;
          border: 1px solid #10b981;

          &:hover {
            background: #d1fae5;
          }
        }
      }
    `,
  ],
})
export class PatientDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly careService = inject(CareRelationshipService);

  readonly relationship = signal<CareRelationshipWithPatient | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  // Mock data - en el futuro se cargará de la API
  readonly consultations = signal<any[]>([]);
  readonly nutritionPlan = signal<any | null>(null);

  async ngOnInit(): Promise<void> {
    const relationshipId = this.route.snapshot.paramMap.get('id');

    if (!relationshipId) {
      this.error.set('ID de relación no válido');
      this.loading.set(false);
      return;
    }

    await this.loadPatientDetail(parseInt(relationshipId, 10));
  }

  private async loadPatientDetail(relationshipId: number): Promise<void> {
    try {
      this.loading.set(true);
      const relationship =
        await this.careService.getPatientRelationship(relationshipId);

      if (!relationship) {
        this.error.set('No se encontró la relación con el paciente');
        return;
      }

      this.relationship.set(relationship);

      // Mock data - en producción se cargaría de la API
      this.loadMockData();
    } catch (err) {
      console.error('Error al cargar detalle del paciente:', err);
      this.error.set('Error al cargar la información del paciente');
    } finally {
      this.loading.set(false);
    }
  }

  private loadMockData(): void {
    // Mock consultations
    this.consultations.set([
      {
        id: 1,
        date: '15 Oct 2024',
        title: 'Consulta de seguimiento',
        summary:
          'Revisión del progreso del plan nutricional. Paciente muestra mejoría en sus hábitos alimenticios.',
      },
      {
        id: 2,
        date: '1 Oct 2024',
        title: 'Primera consulta',
        summary:
          'Evaluación inicial. Se establecieron objetivos y se diseñó plan nutricional personalizado.',
      },
    ]);

    // Mock nutrition plan
    this.nutritionPlan.set({
      goal: 'Control de peso y mejora de hábitos alimenticios',
      calories: 2000,
      lastUpdate: '1 Oct 2024',
      recommendations: [
        'Consumir 5 porciones de frutas y verduras al día',
        'Incluir proteína magra en cada comida principal',
        'Reducir el consumo de azúcares refinados',
        'Beber al menos 2 litros de agua al día',
        'Realizar 3 comidas principales y 2 snacks saludables',
      ],
    });
  }

  async endRelationship(): Promise<void> {
    if (!this.relationship()) return;

    const confirmed = confirm(
      '¿Estás seguro de que deseas finalizar esta relación de cuidado?'
    );

    if (!confirmed) return;

    try {
      await this.careService.endRelationship(this.relationship()!.id);
      alert('Relación finalizada exitosamente');
      this.router.navigate(['/profesional/pacientes']);
    } catch (error) {
      console.error('Error al finalizar relación:', error);
      alert('Error al finalizar la relación. Por favor intenta nuevamente.');
    }
  }

  getStatusLabel(status: string): string {
    const labels: Record<string, string> = {
      active: 'Activo',
      inactive: 'Inactivo',
      ended: 'Finalizado',
    };
    return labels[status] || status;
  }

  formatGender(gender: string | null): string {
    if (!gender) return 'No especificado';
    const genders: Record<string, string> = {
      male: 'Masculino',
      female: 'Femenino',
      other: 'Otro',
    };
    return genders[gender] || gender;
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  }
}
