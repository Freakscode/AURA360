import { Component, inject, input, output, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators, FormGroup, FormControl } from '@angular/forms';
import { BodyMeasurementService } from '../../services/body-measurement.service';
import { ButtonComponent } from '../../../../shared/components/ui';
import { MeasurementProtocol, PatientType } from '../../../../core/models/body-measurement.interface';

@Component({
  selector: 'app-add-measurement-modal',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, ButtonComponent],
  template: `
    @if (isOpen()) {
      <div class="modal-overlay" (click)="onOverlayClick($event)">
        <div class="modal" (click)="$event.stopPropagation()">
          <header class="modal__header">
            <h2>Nueva Medición</h2>
            <button class="modal__close" (click)="close()">&times;</button>
          </header>

          <div class="modal__body">
             <!-- Step 1: Configuración -->
             <div class="config-panel">
                <div class="grid-2">
                    <div class="form-group">
                        <label>Protocolo</label>
                        <select [formControl]="protocolControl" class="form-select">
                            <option value="clinical_basic">Clínico Básico</option>
                            <option value="isak_restricted">ISAK Restringido (Deportistas)</option>
                            <option value="isak_full">ISAK Completo</option>
                            <option value="elderly_sarcopenia">Adulto Mayor (Sarcopenia)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Tipo Paciente</label>
                        <select [formControl]="patientTypeControl" class="form-select">
                            <option value="sedentary">Sedentario</option>
                            <option value="active">Activo</option>
                            <option value="athlete">Deportista</option>
                            <option value="elderly">Adulto Mayor</option>
                        </select>
                    </div>
                </div>
             </div>

             <!-- Tabs de Navegación -->
             <div class="tabs">
                <button class="tab-btn" [class.active]="activeTab() === 'basics'" (click)="activeTab.set('basics')">Básicos</button>
                @if (showPerimeters()) {
                    <button class="tab-btn" [class.active]="activeTab() === 'girths'" (click)="activeTab.set('girths')">Perímetros</button>
                }
                @if (showSkinfolds()) {
                    <button class="tab-btn" [class.active]="activeTab() === 'skinfolds'" (click)="activeTab.set('skinfolds')">Pliegues</button>
                }
                @if (showBones()) {
                    <button class="tab-btn" [class.active]="activeTab() === 'bones'" (click)="activeTab.set('bones')">Diámetros</button>
                }
             </div>

             <form [formGroup]="form" (ngSubmit)="onSubmit()" class="form-content">
                
                <!-- TAB: BASICOS -->
                @if (activeTab() === 'basics') {
                    <div class="tab-pane">
                        <div class="form-group">
                           <label>Fecha</label>
                           <input type="datetime-local" formControlName="recorded_at" class="form-input">
                        </div>
                        <div class="grid-2">
                            <div class="form-group">
                                <label>Peso (kg) *</label>
                                <input type="number" step="0.1" formControlName="weight_kg" class="form-input">
                            </div>
                            <div class="form-group">
                                <label>Estatura (cm)</label>
                                <input type="number" step="0.1" formControlName="height_cm" class="form-input">
                            </div>
                        </div>
                        
                        <div class="form-group">
                           <label>Notas Clínicas</label>
                           <textarea formControlName="notes" class="form-textarea" rows="3"></textarea>
                        </div>
                    </div>
                }

                <!-- TAB: PERIMETROS -->
                @if (activeTab() === 'girths') {
                    <div class="tab-pane">
                        <div class="grid-2">
                            <div class="form-group">
                                <label>Cintura (cm)</label>
                                <input type="number" step="0.1" formControlName="waist_circumference_cm" class="form-input">
                            </div>
                            <div class="form-group">
                                <label>Cadera (cm)</label>
                                <input type="number" step="0.1" formControlName="hip_circumference_cm" class="form-input">
                            </div>
                            <div class="form-group">
                                <label>Brazo Relajado (cm)</label>
                                <input type="number" step="0.1" formControlName="arm_relaxed_circumference_cm" class="form-input">
                            </div>
                            <div class="form-group">
                                <label>Brazo Flexionado (cm)</label>
                                <input type="number" step="0.1" formControlName="arm_flexed_circumference_cm" class="form-input">
                            </div>
                            <div class="form-group">
                                <label>Pantorrilla Máx (cm)</label>
                                <input type="number" step="0.1" formControlName="calf_circumference_cm" class="form-input">
                            </div>
                        </div>
                    </div>
                }

                <!-- TAB: PLIEGUES -->
                @if (activeTab() === 'skinfolds') {
                    <div class="tab-pane">
                        <p class="hint">Medidas en milímetros (mm)</p>
                        <div class="grid-2">
                            <div class="form-group">
                                <label>Tríceps</label>
                                <input type="number" step="0.1" formControlName="triceps_skinfold_mm" class="form-input">
                            </div>
                            <div class="form-group">
                                <label>Subescapular</label>
                                <input type="number" step="0.1" formControlName="subscapular_skinfold_mm" class="form-input">
                            </div>
                            <div class="form-group">
                                <label>Bíceps</label>
                                <input type="number" step="0.1" formControlName="biceps_skinfold_mm" class="form-input">
                            </div>
                            <div class="form-group">
                                <label>Cresta Ilíaca</label>
                                <input type="number" step="0.1" formControlName="suprailiac_skinfold_mm" class="form-input">
                            </div>
                            <div class="form-group">
                                <label>Abdominal</label>
                                <input type="number" step="0.1" formControlName="abdominal_skinfold_mm" class="form-input">
                            </div>
                            <div class="form-group">
                                <label>Muslo Frontal</label>
                                <input type="number" step="0.1" formControlName="thigh_skinfold_mm" class="form-input">
                            </div>
                            <div class="form-group">
                                <label>Pantorrilla</label>
                                <input type="number" step="0.1" formControlName="calf_skinfold_mm" class="form-input">
                            </div>
                        </div>
                    </div>
                }
                
                <!-- TAB: DIAMETROS -->
                @if (activeTab() === 'bones') {
                    <div class="tab-pane">
                        <p class="hint">Medidas en milímetros (mm)</p>
                        <div class="grid-2">
                            <div class="form-group">
                                <label>Húmero (Biepicondilar)</label>
                                <input type="number" step="0.1" formControlName="humerus_breadth_mm" class="form-input">
                            </div>
                            <div class="form-group">
                                <label>Fémur (Bicondilar)</label>
                                <input type="number" step="0.1" formControlName="femur_breadth_mm" class="form-input">
                            </div>
                            <div class="form-group">
                                <label>Muñeca (Biestiloideo)</label>
                                <input type="number" step="0.1" formControlName="wrist_breadth_mm" class="form-input">
                            </div>
                        </div>
                    </div>
                }

                @if (error()) {
                    <div class="error-box">{{ error() }}</div>
                }
             </form>
          </div>

          <footer class="modal__footer">
            <div class="footer-left">
                 <!-- Posible indicador de campos completados -->
            </div>
            <div class="footer-right">
                <ui-button variant="secondary" (clicked)="close()">Cancelar</ui-button>
                <ui-button 
                    variant="primary" 
                    (clicked)="onSubmit()" 
                    [loading]="saving()"
                    [disabled]="form.invalid || saving()">
                    Guardar Medición
                </ui-button>
            </div>
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
        background: white; border-radius: 0.75rem; width: 95%; max-width: 700px;
        max-height: 90vh; display: flex; flex-direction: column;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
      }
      .modal__header {
        padding: 1.25rem 1.5rem; border-bottom: 1px solid $color-border-light;
        display: flex; justify-content: space-between; align-items: center;
        h2 { margin: 0; font-size: 1.25rem; color: $color-text-primary; }
      }
      .modal__close { background: none; border: none; font-size: 1.5rem; cursor: pointer; color: $color-text-muted; }
      
      .modal__body { padding: 0; flex: 1; overflow-y: auto; display: flex; flex-direction: column; }
      
      .config-panel {
          padding: 1.5rem; background: $color-bg-secondary; border-bottom: 1px solid $color-border-light;
      }
      
      .tabs {
          display: flex; border-bottom: 1px solid $color-border-light; background: white;
          position: sticky; top: 0; z-index: 10;
      }
      .tab-btn {
          flex: 1; padding: 1rem; background: none; border: none;
          border-bottom: 2px solid transparent; font-weight: 500; color: $color-text-muted;
          cursor: pointer; transition: all 0.2s;
          
          &:hover { background: $color-gray-50; color: $color-primary-600; }
          &.active { border-bottom-color: $color-primary-500; color: $color-primary-700; font-weight: 600; }
      }
      
      .form-content { padding: 1.5rem; }
      .tab-pane { animation: fadeIn 0.3s ease; }
      
      .modal__footer {
        padding: 1.25rem 1.5rem; background: white; border-top: 1px solid $color-border-light;
        display: flex; justify-content: flex-end; gap: 0.75rem;
      }
      
      .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
      .form-group { margin-bottom: 1rem; }
      label { display: block; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.5rem; color: $color-text-primary; }
      .form-input, .form-select, .form-textarea {
        width: 100%; padding: 0.625rem; border: 1px solid $color-border-light; border-radius: 0.375rem;
        font-family: inherit;
        &:focus { outline: none; border-color: $color-primary-500; box-shadow: 0 0 0 2px rgba($color-primary-500, 0.1); }
      }
      .hint { font-size: 0.75rem; color: $color-text-muted; margin-bottom: 1rem; font-style: italic; }
      .error-box { color: #dc2626; background: #fef2f2; padding: 0.75rem; border-radius: 0.375rem; margin-top: 1rem; }
      
      @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
  `]
})
export class AddMeasurementModalComponent {
  private fb = inject(FormBuilder);
  private service = inject(BodyMeasurementService);

  isOpen = input<boolean>(false);
  userId = input.required<string>();
  closed = output<void>();
  saved = output<void>();

  // Estado UI
  activeTab = signal<'basics' | 'girths' | 'skinfolds' | 'bones'>('basics');
  saving = signal(false);
  error = signal<string | null>(null);

  // Formulario Principal
  form: FormGroup = this.fb.group({
    // Contexto
    protocol: ['clinical_basic', Validators.required],
    patient_type: ['sedentary', Validators.required],
    recorded_at: [new Date().toISOString().slice(0, 16), Validators.required],
    notes: [''],
    
    // Básicos
    weight_kg: [null, [Validators.required, Validators.min(1)]],
    height_cm: [null, [Validators.min(30), Validators.max(250)]],
    
    // Perímetros
    waist_circumference_cm: [null],
    hip_circumference_cm: [null],
    arm_relaxed_circumference_cm: [null],
    arm_flexed_circumference_cm: [null],
    calf_circumference_cm: [null],
    
    // Pliegues
    triceps_skinfold_mm: [null],
    subscapular_skinfold_mm: [null],
    biceps_skinfold_mm: [null],
    suprailiac_skinfold_mm: [null],
    abdominal_skinfold_mm: [null],
    thigh_skinfold_mm: [null],
    calf_skinfold_mm: [null],
    
    // Diámetros
    humerus_breadth_mm: [null],
    femur_breadth_mm: [null],
    wrist_breadth_mm: [null],
  });

  // Getters para controles casted a FormControl
  get protocolControl() { return this.form.get('protocol') as FormControl; }
  get patientTypeControl() { return this.form.get('patient_type') as FormControl; }

  // Computed visibility based on protocol
  showSkinfolds = computed(() => {
      const p = this.protocolControl.value;
      return p === 'isak_restricted' || p === 'isak_full';
  });
  
  showBones = computed(() => {
      const p = this.protocolControl.value;
      return p === 'isak_full'; // Solo completo requiere diametros para Heath-Carter completo
  });

  showPerimeters = computed(() => {
      const p = this.protocolControl.value;
      return p !== 'clinical_basic';
  });

  constructor() {
      // Reset form when opened
      effect(() => {
          if (this.isOpen()) {
             this.form.patchValue({
                 recorded_at: new Date().toISOString().slice(0, 16),
                 protocol: 'clinical_basic'
             });
             this.activeTab.set('basics');
          }
      });
  }

  onSubmit() {
    if (this.form.invalid) return;

    this.saving.set(true);
    this.error.set(null);

    const val = this.form.value;
    
    // Clean empty strings/nulls
    const payload: any = {
        auth_user_id: this.userId(),
        ...val
    };

    this.service.createMeasurement(payload).subscribe({
        next: () => {
            this.saved.emit();
            this.close();
        },
        error: (err) => {
            console.error(err);
            this.error.set('Error al guardar la medición.');
            this.saving.set(false);
        }
    });
  }

  close() {
    this.form.reset({
        recorded_at: new Date().toISOString().slice(0, 16),
        protocol: 'clinical_basic',
        patient_type: 'sedentary'
    });
    this.closed.emit();
  }

  onOverlayClick(event: MouseEvent) {
    if (event.target === event.currentTarget) this.close();
  }
}