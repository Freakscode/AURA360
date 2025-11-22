import { Component, inject, input, output, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators, FormGroup } from '@angular/forms';
import { CareRelationshipService } from '../../services/care-relationship.service';
import { ButtonComponent } from '../../../../shared/components/ui';

@Component({
  selector: 'app-create-patient-modal',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, ButtonComponent],
  template: `
    @if (isOpen()) {
      <div class="modal-overlay" (click)="onOverlayClick($event)">
        <div class="modal" (click)="$event.stopPropagation()">
          <header class="modal__header">
            <h2>Nuevo Paciente</h2>
            <button class="modal__close" (click)="close()">&times;</button>
          </header>

          <form [formGroup]="form" (ngSubmit)="onSubmit()" class="modal__body">
            <p class="description">
                Ingrese los datos del paciente. Se creará una cuenta automáticamente y se le asignará a su lista.
            </p>

            <div class="form-group">
                <label>Nombre Completo *</label>
                <input type="text" formControlName="full_name" class="form-input" placeholder="Ej. Juan Pérez">
                @if (form.get('full_name')?.touched && form.get('full_name')?.invalid) {
                    <span class="error-text">El nombre es requerido</span>
                }
            </div>

            <div class="form-group">
                <label>Email *</label>
                <input type="email" formControlName="email" class="form-input" placeholder="juan@ejemplo.com">
                @if (form.get('email')?.touched && form.get('email')?.invalid) {
                    <span class="error-text">Ingrese un email válido</span>
                }
            </div>

            <div class="form-group">
                <label>Teléfono</label>
                <input type="tel" formControlName="phone_number" class="form-input" placeholder="+52...">
            </div>
            
            @if (error()) {
                <div class="error-box">{{ error() }}</div>
            }
          </form>

          <footer class="modal__footer">
            <ui-button variant="secondary" (clicked)="close()" [disabled]="saving()">Cancelar</ui-button>
            <ui-button 
                variant="primary" 
                (clicked)="onSubmit()" 
                [loading]="saving()"
                [disabled]="form.invalid || saving()">
                Crear Paciente
            </ui-button>
          </footer>
        </div>
      </div>
    }
  `,
  styles: [`
      @use '../../../../../styles/variables' as *;

      .modal-overlay {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.5); display: flex; justify-content: center; align-items: center;
        z-index: 1000; backdrop-filter: blur(4px);
      }
      .modal {
        background: white; border-radius: 0.75rem; width: 90%; max-width: 500px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
      }
      .modal__header {
        padding: 1.5rem; border-bottom: 1px solid $color-border-light;
        display: flex; justify-content: space-between; align-items: center;
        h2 { margin: 0; font-size: 1.25rem; color: $color-text-primary; }
      }
      .modal__close { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: $color-text-muted; }
      .modal__body { padding: 1.5rem; }
      .description { margin-top: 0; margin-bottom: 1.5rem; color: $color-text-secondary; font-size: 0.875rem; }
      
      .form-group { margin-bottom: 1.25rem; }
      label { display: block; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.5rem; color: $color-text-primary; }
      .form-input {
        width: 100%; padding: 0.625rem; border: 1px solid $color-border-light; border-radius: 0.375rem;
        font-family: inherit;
        &:focus { outline: none; border-color: $color-primary-500; box-shadow: 0 0 0 2px rgba($color-primary-500, 0.1); }
      }
      .error-text { color: #dc2626; font-size: 0.75rem; margin-top: 0.25rem; display: block; }
      .error-box { color: #dc2626; background: #fef2f2; padding: 0.75rem; border-radius: 0.375rem; margin-top: 1rem; font-size: 0.875rem; }

      .modal__footer {
        padding: 1.25rem 1.5rem; background: $color-bg-secondary; border-top: 1px solid $color-border-light;
        display: flex; justify-content: flex-end; gap: 0.75rem;
      }
  `]
})
export class CreatePatientModalComponent {
  private fb = inject(FormBuilder);
  private service = inject(CareRelationshipService);

  isOpen = input<boolean>(false);
  closed = output<void>();
  created = output<void>();

  saving = signal(false);
  error = signal<string | null>(null);

  form: FormGroup = this.fb.group({
    full_name: ['', [Validators.required, Validators.minLength(3)]],
    email: ['', [Validators.required, Validators.email]],
    phone_number: ['']
  });

  constructor() {
      effect(() => {
          if (this.isOpen()) {
              this.form.reset();
              this.error.set(null);
          }
      });
  }

  onSubmit() {
    if (this.form.invalid) {
        this.form.markAllAsTouched();
        return;
    }

    this.saving.set(true);
    this.error.set(null);

    const val = this.form.value;
    
    this.service.invitePatient(val).then(
        () => {
            this.created.emit();
            this.close();
        },
        (err) => {
            console.error(err);
            const msg = err.error?.error || 'Error al crear el paciente.';
            this.error.set(msg);
        }
    ).finally(() => {
        this.saving.set(false);
    });
  }

  close() {
    this.closed.emit();
  }

  onOverlayClick(event: MouseEvent) {
    if (event.target === event.currentTarget) this.close();
  }
}
