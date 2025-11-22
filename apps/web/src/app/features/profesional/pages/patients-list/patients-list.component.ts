import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CareRelationshipService } from '../../services/care-relationship.service';
import { CareRelationshipWithPatient } from '../../models/care-relationship.model';
import { AssignPatientModalComponent } from '../../components/assign-patient-modal/assign-patient-modal.component';
import { CreatePatientModalComponent } from '../../components/create-patient-modal/create-patient-modal.component';
import { ButtonComponent, CardComponent, BadgeComponent } from '../../../../shared/components/ui';

type SortField = 'name' | 'email' | 'date' | null;
type SortDirection = 'asc' | 'desc';
type FilterStatus = 'all' | 'active' | 'inactive';

@Component({
  selector: 'app-patients-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    FormsModule,
    AssignPatientModalComponent,
    CreatePatientModalComponent,
    ButtonComponent,
    CardComponent,
    BadgeComponent,
  ],
  template: `
    <div class="container my-8">
      <!-- Header -->
      <header class="d-flex justify-between items-center mb-8">
        <div>
          <h1 class="text-4xl font-bold text-primary mb-2">Mis Pacientes</h1>
          <p class="text-muted">Pacientes bajo mi cuidado profesional</p>
        </div>
        <div class="d-flex gap-3">
            <ui-button variant="outline" (clicked)="openAssignModal()">
              Buscar Existente
            </ui-button>
            <ui-button variant="primary" (clicked)="openCreateModal()">
              + Nuevo Paciente
            </ui-button>
        </div>
      </header>

      <!-- Filters Card -->
      <ui-card [hasHeader]="false" class="mb-6">
        <div class="d-flex gap-4 items-center flex-wrap">
          <!-- Search Box -->
          <div class="flex-1" style="min-width: 300px;">
            <div class="input-group">
              <input
                type="text"
                [(ngModel)]="searchQuery"
                (ngModelChange)="onSearchChange()"
                placeholder="Buscar por nombre o email..."
                class="form-input"
              />
              @if (searchQuery()) {
                <button
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-error transition-colors"
                  style="background: none; border: none; cursor: pointer; font-size: 1.25rem;"
                  (click)="clearSearch()">
                  ✕
                </button>
              }
            </div>
          </div>

          <!-- Status Filter -->
          <div class="d-flex gap-2 items-center">
            <label class="text-sm font-semibold text-secondary">Estado:</label>
            <select
              [(ngModel)]="filterStatus"
              (ngModelChange)="onFilterChange()"
              class="form-select form-select--sm">
              <option value="all">Todos</option>
              <option value="active">Activos</option>
              <option value="inactive">Inactivos</option>
            </select>
          </div>

          <!-- Sort Buttons -->
          <div class="d-flex gap-2 items-center">
            <label class="text-sm font-semibold text-secondary">Ordenar:</label>
            <ui-button
              variant="outline"
              size="sm"
              [class.btn--primary]="sortField() === 'name'"
              (clicked)="toggleSort('name')">
              Nombre
              @if (sortField() === 'name') {
                <span>{{ sortDirection() === 'asc' ? '↑' : '↓' }}</span>
              }
            </ui-button>
            <ui-button
              variant="outline"
              size="sm"
              [class.btn--primary]="sortField() === 'date'"
              (clicked)="toggleSort('date')">
              Fecha
              @if (sortField() === 'date') {
                <span>{{ sortDirection() === 'asc' ? '↑' : '↓' }}</span>
              }
            </ui-button>
          </div>
        </div>
      </ui-card>

      <!-- Loading / Error States -->
      @if (careService.loading()) {
        <ui-card>
          <div class="text-center py-12">
            <div class="spinner mx-auto mb-4"></div>
            <p class="text-muted">Cargando pacientes...</p>
          </div>
        </ui-card>
      } @else if (careService.error()) {
        <ui-card>
          <div class="text-center py-12 text-error">
            <p>Error: {{ careService.error() }}</p>
          </div>
        </ui-card>
      } @else {
        <!-- Summary Cards -->
        <div class="card-grid card-grid--4-cols mb-6">
          <ui-card size="sm">
            <div class="text-center">
              <div class="text-3xl font-bold text-primary mb-2">
                {{ activePatients().length }}
              </div>
              <div class="text-sm text-muted">Activos</div>
            </div>
          </ui-card>

          <ui-card size="sm">
            <div class="text-center">
              <div class="text-3xl font-bold text-secondary mb-2">
                {{ inactivePatients().length }}
              </div>
              <div class="text-sm text-muted">Inactivos</div>
            </div>
          </ui-card>

          <ui-card size="sm">
            <div class="text-center">
              <div class="text-3xl font-bold text-secondary mb-2">
                {{ careService.patients().length }}
              </div>
              <div class="text-sm text-muted">Total</div>
            </div>
          </ui-card>

          <ui-card size="sm" variant="elevated" class="bg-primary-50">
            <div class="text-center">
              <div class="text-3xl font-bold text-primary mb-2">
                {{ filteredPatients().length }}
              </div>
              <div class="text-sm font-semibold text-primary">Mostrando</div>
            </div>
          </ui-card>
        </div>

        <!-- Empty States -->
        @if (filteredPatients().length === 0 && careService.patients().length > 0) {
          <ui-card>
            <div class="text-center py-12">
              <p class="text-muted mb-4">
                No se encontraron pacientes con los criterios de búsqueda.
              </p>
              <ui-button variant="secondary" (clicked)="clearFilters()">
                Limpiar Filtros
              </ui-button>
            </div>
          </ui-card>
        } @else if (careService.patients().length === 0) {
          <ui-card>
            <div class="text-center py-12">
              <p class="text-muted">No tienes pacientes asignados aún.</p>
            </div>
          </ui-card>
        } @else {
          <!-- Patients Table -->
          <div class="table-container">
            <table class="table table--hoverable">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Email</th>
                  <th>Teléfono</th>
                  <th>Edad</th>
                  <th>Género</th>
                  <th>Contexto</th>
                  <th>Estado</th>
                  <th>Fecha Inicio</th>
                </tr>
              </thead>
              <tbody>
                @for (relationship of filteredPatients(); track relationship.id) {
                  <tr
                    [class.inactive]="relationship.status !== 'active'"
                    [routerLink]="['/profesional/pacientes', relationship.id]"
                    class="cursor-pointer">
                    <td class="font-medium">{{ relationship.patient.full_name }}</td>
                    <td>{{ relationship.patient.email }}</td>
                    <td>{{ relationship.patient.phone_number || '-' }}</td>
                    <td>{{ relationship.patient.age || '-' }}</td>
                    <td>{{ relationship.patient.gender || '-' }}</td>
                    <td>
                      <ui-badge
                        [variant]="relationship.context_type === 'independent' ? 'info' : 'secondary'">
                        {{ relationship.context_type === 'independent' ? 'Independiente' : 'Institucional' }}
                      </ui-badge>
                    </td>
                    <td>
                      <ui-badge
                        [variant]="relationship.status === 'active' ? 'success' : 'secondary'"
                        [dot]="true">
                        {{ getStatusLabel(relationship.status) }}
                      </ui-badge>
                    </td>
                    <td>{{ formatDate(relationship.started_at) }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        }
      }

      <!-- Modal de asignación -->
      <app-assign-patient-modal
        [isOpen]="showAssignModal()"
        (closed)="closeAssignModal()"
        (patientAssigned)="onPatientActionComplete()" />
        
      <!-- Modal de creación -->
      <app-create-patient-modal
        [isOpen]="showCreateModal()"
        (closed)="closeCreateModal()"
        (created)="onPatientActionComplete()" />
    </div>
  `,
  styles: [
    `
      .inactive {
        opacity: 0.6;
      }

      .input-group {
        position: relative;
      }
    `,
  ],
})
export class PatientsListComponent implements OnInit {
  readonly careService = inject(CareRelationshipService);

  // Estado local para búsqueda y filtros
  readonly searchQuery = signal('');
  readonly filterStatus = signal<FilterStatus>('all');
  readonly sortField = signal<SortField>(null);
  readonly sortDirection = signal<SortDirection>('asc');
  
  readonly showAssignModal = signal(false);
  readonly showCreateModal = signal(false);

  // Computed values
  readonly activePatients = computed(() =>
    this.careService.patients().filter((p) => p.status === 'active')
  );

  readonly inactivePatients = computed(() =>
    this.careService.patients().filter((p) => p.status !== 'active')
  );

  readonly filteredPatients = computed(() => {
    let patients = [...this.careService.patients()];

    // Aplicar búsqueda
    const query = this.searchQuery().toLowerCase();
    if (query) {
      patients = patients.filter(
        (p) =>
          p.patient.full_name.toLowerCase().includes(query) ||
          p.patient.email.toLowerCase().includes(query)
      );
    }

    // Aplicar filtro de estado
    const status = this.filterStatus();
    if (status === 'active') {
      patients = patients.filter((p) => p.status === 'active');
    } else if (status === 'inactive') {
      patients = patients.filter((p) => p.status !== 'active');
    }

    // Aplicar ordenamiento
    const field = this.sortField();
    if (field) {
      patients.sort((a, b) => {
        let comparison = 0;

        if (field === 'name') {
          comparison = a.patient.full_name.localeCompare(b.patient.full_name);
        } else if (field === 'date') {
          comparison =
            new Date(a.started_at).getTime() - new Date(b.started_at).getTime();
        }

        return this.sortDirection() === 'asc' ? comparison : -comparison;
      });
    }

    return patients;
  });

  async ngOnInit(): Promise<void> {
    await this.careService.loadMyPatients();
  }

  onSearchChange(): void {
    // Búsqueda reactiva gracias a signals
  }

  onFilterChange(): void {
    // Filtro reactivo gracias a signals
  }

  toggleSort(field: SortField): void {
    if (this.sortField() === field) {
      // Toggle direction
      this.sortDirection.set(this.sortDirection() === 'asc' ? 'desc' : 'asc');
    } else {
      this.sortField.set(field);
      this.sortDirection.set('asc');
    }
  }

  clearSearch(): void {
    this.searchQuery.set('');
  }

  clearFilters(): void {
    this.searchQuery.set('');
    this.filterStatus.set('all');
    this.sortField.set(null);
  }

  openAssignModal(): void {
    this.showAssignModal.set(true);
  }

  closeAssignModal(): void {
    this.showAssignModal.set(false);
  }
  
  openCreateModal(): void {
    this.showCreateModal.set(true);
  }
  
  closeCreateModal(): void {
    this.showCreateModal.set(false);
  }

  async onPatientActionComplete(): Promise<void> {
    this.showAssignModal.set(false);
    this.showCreateModal.set(false);
    await this.careService.loadMyPatients();
  }

  getStatusLabel(status: string): string {
    const labels: Record<string, string> = {
      active: 'Activo',
      inactive: 'Inactivo',
      ended: 'Finalizado',
    };
    return labels[status] || status;
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }
}
