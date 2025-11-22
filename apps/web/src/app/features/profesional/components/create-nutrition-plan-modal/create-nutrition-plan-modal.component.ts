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
import { NutritionPlanService } from '../../services/nutrition-plan.service';
import { CareRelationshipWithPatient } from '../../models/care-relationship.model';
import { ButtonComponent } from '../../../../shared/components/ui';

@Component({
  selector: 'app-create-nutrition-plan-modal',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonComponent],
  template: `
    @if (isOpen()) {
      <div class="modal-overlay" (click)="onOverlayClick($event)">
        <div class="modal" (click)="$event.stopPropagation()">
          <!-- Header -->
          <header class="modal__header">
            <h2>Crear Nuevo Plan Nutricional</h2>
            <button class="modal__close" (click)="close()">&times;</button>
          </header>

          <!-- Body -->
          <div class="modal__body">
            <p class="modal__description">
              Creando plan para: <strong>{{ patient()?.patient?.full_name }}</strong>
            </p>

            <!-- Title -->
            <div class="form-group">
              <label>Título del Plan</label>
              <input
                type="text"
                [(ngModel)]="title"
                placeholder="Ej: Plan de Pérdida de Peso - Fase 1"
                class="form-input"
                [disabled]="saving()"
              />
            </div>

            <!-- Goal -->
            <div class="form-group">
              <label>Objetivo Principal</label>
              <textarea
                [(ngModel)]="goal"
                placeholder="Describe el objetivo nutricional..."
                class="form-textarea"
                rows="3"
                [disabled]="saving()"></textarea>
            </div>

            <!-- Calories -->
            <div class="form-group">
              <label>Calorías Diarias (kcal)</label>
              <input
                type="number"
                [(ngModel)]="calories"
                placeholder="2000"
                class="form-input"
                [disabled]="saving()"
              />
            </div>

            <!-- Template Checkbox -->
            <div class="form-group-checkbox">
              <input 
                type="checkbox" 
                id="isTemplate" 
                [(ngModel)]="isTemplate" 
                [disabled]="saving()"
              />
              <label for="isTemplate">Guardar también como Plantilla</label>
            </div>

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
              (clicked)="createPlan()"
              [disabled]="!isValid || saving()"
              [loading]="saving()">
              Crear Plan
            </ui-button>
          </footer>
        </div>
      </div>
    }
  `,
  styles: [
    `
      @use '../../../../../styles/variables' as *;

      .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
        backdrop-filter: blur(4px);
      }

      .modal {
        background: white;
        border-radius: 0.75rem;
        width: 90%;
        max-width: 500px;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
      }

      .modal__header {
        padding: 1.5rem;
        border-bottom: 1px solid $color-border-light;
        display: flex;
        justify-content: space-between;
        align-items: center;

        h2 {
          font-size: 1.25rem;
          font-weight: 600;
          color: $color-text-primary;
          margin: 0;
        }
      }

      .modal__close {
        background: none;
        border: none;
        font-size: 1.5rem;
        color: $color-text-muted;
        cursor: pointer;
        padding: 0.25rem;
        line-height: 1;
        
        &:hover {
          color: $color-text-primary;
        }
      }

      .modal__body {
        padding: 1.5rem;
      }

      .modal__description {
        margin-bottom: 1.5rem;
        color: $color-text-secondary;
      }

      .form-group {
        margin-bottom: 1.5rem;

        label {
          display: block;
          font-size: 0.875rem;
          font-weight: 500;
          color: $color-text-primary;
          margin-bottom: 0.5rem;
        }
      }
      
      .form-group-checkbox {
          display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1.5rem;
          
          input[type="checkbox"] {
              width: 1rem; height: 1rem;
          }
          
          label {
              font-size: 0.875rem; color: $color-text-primary;
          }
      }

      .form-input,
      .form-select,
      .form-textarea {
        width: 100%;
        padding: 0.625rem;
        border: 1px solid $color-border-light;
        border-radius: 0.375rem;
        font-size: 0.875rem;
        transition: border-color 0.2s;

        &:focus {
          outline: none;
          border-color: $color-primary-500;
          box-shadow: 0 0 0 3px rgba($color-primary-500, 0.1);
        }

        &:disabled {
          background-color: $color-bg-secondary;
          cursor: not-allowed;
        }
      }

      .modal__footer {
        padding: 1.25rem 1.5rem;
        background: $color-bg-secondary;
        border-top: 1px solid $color-border-light;
        display: flex;
        justify-content: flex-end;
        gap: 0.75rem;
      }

      .bg-error-50 { background-color: #fef2f2; }
      .border-error-200 { border-color: #fecaca; }
      .text-error { color: #dc2626; }
    `,
  ],
})
export class CreateNutritionPlanModalComponent {
  private readonly nutritionService = inject(NutritionPlanService);

  // Inputs/Outputs
  readonly isOpen = input<boolean>(false);
  readonly patient = input<CareRelationshipWithPatient | null>(null);
  readonly closed = output<void>();
  readonly planCreated = output<void>();

  // State
  readonly title = signal('');
  readonly goal = signal('');
  readonly calories = signal<number>(2000);
  readonly isTemplate = signal(false);
  
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);

  constructor() {
    effect(() => {
      if (this.isOpen()) {
        this.resetState();
      }
    });
  }

  private resetState(): void {
    this.title.set('Plan Nutricional Personalizado');
    this.goal.set('');
    this.calories.set(2000);
    this.isTemplate.set(false);
    this.error.set(null);
  }

  get isValid(): boolean {
    return !!this.title() && !!this.goal() && this.calories() > 0;
  }

  async createPlan(): Promise<void> {
    const patientData = this.patient();
    if (!patientData) return;

    this.saving.set(true);
    this.error.set(null);

    try {
      // Generate payload
      const payload = this.nutritionService.generateDefaultPlan(
        patientData.patient.id.toString(), 
        patientData.patient.full_name,
        this.title(),
        this.goal(),
        this.calories()
      );
      
      // Inject Template Flag
      if (this.isTemplate()) {
          (payload as any).is_template = true;
          (payload as any).description = `Plantilla generada desde plan para ${patientData.patient.full_name}`;
      }
      
      await this.nutritionService.createPlan(payload);
      this.planCreated.emit();
      this.close();
    } catch (err) {
      console.error('Error creating plan:', err);
      this.error.set('Error al crear el plan. Intenta nuevamente.');
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

