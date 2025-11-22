import { Component, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatRadioModule } from '@angular/material/radio';
import { MatSliderModule } from '@angular/material/slider';

@Component({
  selector: 'app-anthropometry',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatRadioModule,
    MatSliderModule
  ],
  template: `
    <div class="tool-container">
      <h1 class="tool-title">Evaluación Antropométrica</h1>
      
      <div class="tool-grid">
        <!-- Input Form -->
        <div class="form-column">
          <mat-card>
            <mat-card-header>
              <mat-card-title>Datos del Paciente</mat-card-title>
            </mat-card-header>
            <mat-card-content class="form-content">
              <div class="row-inputs">
                 <mat-form-field appearance="outline">
                   <mat-label>Género</mat-label>
                   <mat-select [(ngModel)]="gender">
                     <mat-option value="male">Masculino</mat-option>
                     <mat-option value="female">Femenino</mat-option>
                   </mat-select>
                 </mat-form-field>

                 <mat-form-field appearance="outline">
                   <mat-label>Edad</mat-label>
                   <input matInput type="number" [(ngModel)]="age">
                   <span matSuffix>años</span>
                 </mat-form-field>
              </div>

              <div class="row-inputs">
                <mat-form-field appearance="outline">
                  <mat-label>Peso</mat-label>
                  <input matInput type="number" [(ngModel)]="weight">
                  <span matSuffix>kg</span>
                </mat-form-field>

                <mat-form-field appearance="outline">
                  <mat-label>Altura</mat-label>
                  <input matInput type="number" [(ngModel)]="height">
                  <span matSuffix>cm</span>
                </mat-form-field>
              </div>

              <div class="activity-section">
                <label>Nivel de Actividad Física</label>
                <mat-slider min="1.2" max="2.5" step="0.1" showTickMarks discrete>
                  <input matSliderThumb [(ngModel)]="activityLevel">
                </mat-slider>
                <div class="activity-label">
                  Factor: {{ activityLevel() }} - {{ getActivityLabel() }}
                </div>
              </div>
            </mat-card-content>
          </mat-card>
        </div>

        <!-- Results Column -->
        <div class="results-column">
          <mat-card class="result-card imc-card">
             <div class="result-header">
               <mat-icon>monitor_weight</mat-icon>
               <span>IMC (Índice de Masa Corporal)</span>
             </div>
             <div class="result-value">{{ bmi().toFixed(1) }}</div>
             <div class="result-status" [ngClass]="getBmiClass()">
               {{ getBmiLabel() }}
             </div>
          </mat-card>

          <mat-card class="result-card tmb-card">
             <div class="result-header">
               <mat-icon>local_fire_department</mat-icon>
               <span>Tasa Metabólica Basal (TMB)</span>
             </div>
             <div class="result-value">{{ tmb().toFixed(0) }} <small>kcal</small></div>
             <div class="result-subtitle">Gasto en reposo</div>
          </mat-card>

          <mat-card class="result-card get-card">
             <div class="result-header">
               <mat-icon>directions_run</mat-icon>
               <span>Gasto Energético Total (GET)</span>
             </div>
             <div class="result-value">{{ get().toFixed(0) }} <small>kcal</small></div>
             <div class="result-subtitle">Requerimiento diario</div>
          </mat-card>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .tool-container {
      max-width: 1000px;
      margin: 0 auto;
      
      .tool-title {
        font-size: 1.75rem;
        color: #1e293b;
        margin-bottom: 24px;
      }
    }

    .tool-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 24px;
      
      @media (min-width: 768px) {
        grid-template-columns: 1.5fr 1fr;
      }
    }

    .form-content {
      padding-top: 16px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .row-inputs {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    .activity-section {
      display: flex;
      flex-direction: column;
      
      label { font-weight: 500; color: #475569; margin-bottom: 8px; }
      
      .activity-label {
        text-align: center;
        font-weight: 600;
        color: #ac4fc6;
        margin-top: 4px;
      }
    }

    .results-column {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .result-card {
      padding: 20px;
      
      .result-header {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #64748b;
        font-weight: 500;
        margin-bottom: 12px;
      }
      
      .result-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1;
        
        small { font-size: 1rem; color: #64748b; font-weight: 400; }
      }
      
      .result-status, .result-subtitle {
        margin-top: 8px;
        font-weight: 500;
      }
      
      &.imc-card .result-value { color: #4f46e5; }
      &.tmb-card .result-value { color: #ea580c; }
      &.get-card .result-value { color: #16a34a; }
    }

    .result-status {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 16px;
      font-size: 0.85rem;
      
      &.normal { background: #dcfce7; color: #166534; }
      &.overweight { background: #fef3c7; color: #9a3412; }
      &.obese { background: #fee2e2; color: #991b1b; }
    }
  `]
})
export class AnthropometryComponent {
  // Form State
  gender = signal<'male' | 'female'>('female');
  age = signal<number>(32);
  weight = signal<number>(65);
  height = signal<number>(165);
  activityLevel = signal<number>(1.5);

  // Calculations
  bmi = computed(() => {
    const h = this.height() / 100;
    return this.weight() / (h * h);
  });

  // Mifflin-St Jeor Equation
  tmb = computed(() => {
    const w = this.weight();
    const h = this.height();
    const a = this.age();
    
    if (this.gender() === 'male') {
      return (10 * w) + (6.25 * h) - (5 * a) + 5;
    } else {
      return (10 * w) + (6.25 * h) - (5 * a) - 161;
    }
  });

  get = computed(() => {
    return this.tmb() * this.activityLevel();
  });

  // Helpers
  getBmiLabel(): string {
    const bmi = this.bmi();
    if (bmi < 18.5) return 'Bajo Peso';
    if (bmi < 25) return 'Peso Normal';
    if (bmi < 30) return 'Sobrepeso';
    return 'Obesidad';
  }

  getBmiClass(): string {
    const bmi = this.bmi();
    if (bmi < 25) return 'normal';
    if (bmi < 30) return 'overweight';
    return 'obese';
  }

  getActivityLabel(): string {
    const level = this.activityLevel();
    if (level < 1.4) return 'Sedentario';
    if (level < 1.6) return 'Ligero';
    if (level < 1.9) return 'Moderado';
    if (level < 2.2) return 'Intenso';
    return 'Atleta';
  }
}
