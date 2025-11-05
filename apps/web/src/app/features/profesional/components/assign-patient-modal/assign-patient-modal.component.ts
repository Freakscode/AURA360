import {
  Component,
  inject,
  signal,
  output,
  input,
  effect,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CareRelationshipService } from '../../services/care-relationship.service';
import { PatientInfo } from '../../models/care-relationship.model';
import { ButtonComponent, BadgeComponent } from '../../../../shared/components/ui';

@Component({
  selector: 'app-assign-patient-modal',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonComponent, BadgeComponent],
  template: `
    @if (isOpen()) {
      <div class="modal-overlay" (click)="onOverlayClick($event)">
        <div class="modal" (click)="$event.stopPropagation()">
          <!-- Header -->
          <header class="modal__header">
            <h2>Asignar Nuevo Paciente</h2>
            <button class="modal__close" (click)="close()">&times;</button>
          </header>

          <!-- Body -->
          <div class="modal__body">
            <!-- Búsqueda de usuarios -->
            <div class="form-group">
              <label>Buscar Usuario</label>
              <input
                type="text"
                [value]="searchQuery()"
                (input)="onSearchInput($event)"
                placeholder="Buscar por nombre o email..."
                class="form-input"
                [disabled]="loading()"
              />
              <p class="form-hint">
                Busca usuarios existentes para asignarlos como tus pacientes
              </p>
            </div>

            <!-- Loading state -->
            @if (loading()) {
              <div class="text-center py-8">
                <div class="spinner mx-auto mb-4"></div>
                <p class="text-muted">Buscando usuarios...</p>
              </div>
            }
            <!-- Results -->
            @else if (searchQuery().length >= 3) {
              @if (searchResults().length > 0) {
                <div class="mt-4">
                  <p class="text-sm font-semibold text-secondary mb-3">
                    Resultados de búsqueda:
                  </p>
                  <div class="d-flex flex-column gap-3">
                    @for (user of searchResults(); track user.id) {
                      <div
                        class="user-card"
                        [class.user-card--selected]="selectedUser()?.id === user.id"
                        (click)="selectUser(user)">
                        <div class="flex-1">
                          <h4 class="text-base font-semibold text-primary mb-1">
                            {{ user.full_name }}
                          </h4>
                          <p class="text-sm text-muted mb-2">{{ user.email }}</p>
                          @if (user.role_global) {
                            <ui-badge variant="secondary" size="sm">
                              {{ user.role_global }}
                            </ui-badge>
                          }
                        </div>
                        @if (selectedUser()?.id === user.id) {
                          <div class="user-card__check">✓</div>
                        }
                      </div>
                    }
                  </div>
                </div>
              } @else {
                <div class="text-center py-8 text-muted">
                  <p>No se encontraron usuarios con ese criterio.</p>
                </div>
              }
            }
            <!-- Hint -->
            @else if (searchQuery().length > 0) {
              <div class="text-center py-8 text-muted">
                <p>Escribe al menos 3 caracteres para buscar</p>
              </div>
            }

            <!-- Selected User Configuration -->
            @if (selectedUser(); as user) {
              <div class="mt-6 pt-6 border-t border-gray-200">
                <p class="text-sm font-semibold text-secondary mb-3">
                  Usuario seleccionado:
                </p>

                <!-- Selected User Card -->
                <div class="selected-card">
                  <div class="flex-1">
                    <h4 class="text-base font-semibold text-primary mb-1">
                      {{ user.full_name }}
                    </h4>
                    <p class="text-sm text-muted">{{ user.email }}</p>
                  </div>
                  <ui-button variant="outline" size="sm" (clicked)="clearSelection()">
                    Cambiar
                  </ui-button>
                </div>

                <!-- Context Type -->
                <div class="form-group">
                  <label>Tipo de Relación</label>
                  <select [(ngModel)]="contextType" class="form-select">
                    <option value="independent">Práctica Independiente</option>
                    <option value="institutional">Institucional</option>
                  </select>
                </div>

                <!-- Notes -->
                <div class="form-group">
                  <label>Notas (Opcional)</label>
                  <textarea
                    [(ngModel)]="notes"
                    placeholder="Agrega notas sobre esta relación de cuidado..."
                    class="form-textarea"
                    rows="3"></textarea>
                </div>
              </div>
            }

            <!-- Error Alert -->
            @if (error()) {
              <div class="bg-error-50 border border-error-200 rounded-md p-4 mt-4">
                <p class="text-error text-sm">{{ error() }}</p>
              </div>
            }
          </div>

          <!-- Footer -->
          <footer class="modal__footer">
            <ui-button
              variant="secondary"
              (clicked)="close()"
              [disabled]="saving()">
              Cancelar
            </ui-button>
            <ui-button
              variant="primary"
              (clicked)="assignPatient()"
              [disabled]="!selectedUser() || saving()"
              [loading]="saving()">
              Asignar Paciente
            </ui-button>
          </footer>
        </div>
      </div>
    }
  `,
  styles: [
    `
      @use '../../../../../styles/variables' as *;

      .user-card {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        border: 2px solid $color-border-light;
        border-radius: 0.5rem;
        cursor: pointer;
        transition: all 0.2s;

        &:hover {
          border-color: $color-primary-500;
          background: $color-primary-50;
        }

        &--selected {
          border-color: $color-primary-500;
          background: $color-primary-100;
        }
      }

      .user-card__check {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 2rem;
        height: 2rem;
        background: $color-primary-500;
        color: white;
        border-radius: 50%;
        font-size: 1.25rem;
        font-weight: bold;
      }

      .selected-card {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        background: $color-primary-100;
        border: 1px solid $color-primary-500;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
      }
    `,
  ],
})
export class AssignPatientModalComponent {
  private readonly careService = inject(CareRelationshipService);

  // Inputs/Outputs
  readonly isOpen = input<boolean>(false);
  readonly closed = output<void>();
  readonly patientAssigned = output<void>();

  // Estado local
  readonly searchQuery = signal('');
  readonly searchResults = signal<PatientInfo[]>([]);
  readonly selectedUser = signal<PatientInfo | null>(null);
  readonly contextType = signal<'independent' | 'institutional'>('independent');
  readonly notes = signal('');
  readonly loading = signal(false);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);

  private searchTimeout: any;

  constructor() {
    // Resetear estado cuando se abre el modal
    effect(() => {
      if (this.isOpen()) {
        this.resetState();
      }
    });
  }

  private resetState(): void {
    this.searchQuery.set('');
    this.searchResults.set([]);
    this.selectedUser.set(null);
    this.contextType.set('independent');
    this.notes.set('');
    this.error.set(null);
  }

  onSearchInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const query = input.value;

    // Update signal immediately for UI
    this.searchQuery.set(query);

    // Debounce search
    clearTimeout(this.searchTimeout);

    if (query.length < 3) {
      this.searchResults.set([]);
      return;
    }

    this.loading.set(true);
    this.searchTimeout = setTimeout(async () => {
      try {
        const results = await this.careService.searchAvailableUsers(query);
        this.searchResults.set(results);
        this.error.set(null);
      } catch (err) {
        console.error('Error en búsqueda:', err);
        this.error.set('Error al buscar usuarios');
      } finally {
        this.loading.set(false);
      }
    }, 500);
  }

  selectUser(user: PatientInfo): void {
    this.selectedUser.set(user);
  }

  clearSelection(): void {
    this.selectedUser.set(null);
  }

  async assignPatient(): Promise<void> {
    const user = this.selectedUser();
    if (!user) return;

    this.saving.set(true);
    this.error.set(null);

    try {
      await this.careService.assignPatient(
        user.id,
        this.contextType(),
        this.notes() || undefined
      );

      this.patientAssigned.emit();
      this.close();
    } catch (err) {
      console.error('Error al asignar paciente:', err);
      this.error.set(
        'Error al asignar el paciente. Por favor intenta nuevamente.'
      );
    } finally {
      this.saving.set(false);
    }
  }

  close(): void {
    this.closed.emit();
  }

  onOverlayClick(event: MouseEvent): void {
    if (event.target === event.currentTarget) {
      this.close();
    }
  }
}
