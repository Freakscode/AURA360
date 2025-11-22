import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule, DatePipe, TitleCasePipe, DecimalPipe } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

// Services & Models
import { CareRelationshipService } from '../../services/care-relationship.service';
import { NutritionPlanService } from '../../services/nutrition-plan.service';
import { BodyMeasurementService } from '../../services/body-measurement.service';
import { CareRelationshipWithPatient } from '../../models/care-relationship.model';
import { NutritionPlan } from '../../models/nutrition-plan.model';
import { BodyMeasurement } from '../../../../core/models/body-measurement.interface';

// Components
import { ButtonComponent, CardComponent, BadgeComponent } from '../../../../shared/components/ui';
import { CreateNutritionPlanModalComponent } from '../../components/create-nutrition-plan-modal/create-nutrition-plan-modal.component';
import { ProgressChartComponent, ChartPoint } from '../../components/progress-chart/progress-chart.component';
import { AddMeasurementModalComponent } from '../../components/add-measurement-modal/add-measurement-modal.component';
import { NutritionAdherenceCardComponent } from '../../components/nutrition-adherence-card/nutrition-adherence-card.component';
import { AIRecommendationsCardComponent } from '../../components/ai-recommendations-card/ai-recommendations-card.component';

type TabType = 'overview' | 'anthropometry' | 'nutrition' | 'profile';

@Component({
  selector: 'app-patient-detail',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    DatePipe,
    TitleCasePipe,
    DecimalPipe,
    ButtonComponent,
    CardComponent,
    BadgeComponent,
    CreateNutritionPlanModalComponent,
    ProgressChartComponent,
    AddMeasurementModalComponent,
    NutritionAdherenceCardComponent,
    AIRecommendationsCardComponent
  ],
  template: `
    <div class="detail-container">
      @if (loading()) {
        <div class="loading-state">
          <div class="spinner"></div>
          <p>Cargando expediente...</p>
        </div>
      } @else if (error()) {
        <ui-card class="error-state">
          <div class="error-icon">⚠️</div>
          <h2>Error al cargar</h2>
          <p>{{ error() }}</p>
          <ui-button variant="primary" routerLink="/profesional/pacientes">Volver a la lista</ui-button>
        </ui-card>
      } @else if (relationship(); as rel) {
        
        <!-- Header Profile -->
        <header class="profile-header">
           <div class="header-content">
              <div class="profile-info">
                 <div class="profile-avatar">
                    {{ rel.patient.full_name.charAt(0) }}
                 </div>
                 <div>
                    <h1>{{ rel.patient.full_name }}</h1>
                    <div class="profile-meta">
                        <span>{{ rel.patient.age ? rel.patient.age + ' años' : 'Edad N/A' }}</span>
                        <span class="separator">•</span>
                        <span>{{ rel.patient.email }}</span>
                        <ui-badge [variant]="rel.status === 'active' ? 'success' : 'secondary'" size="sm" [dot]="true">
                            {{ rel.status === 'active' ? 'Activo' : 'Inactivo' }}
                        </ui-badge>
                    </div>
                 </div>
              </div>
              
              <div class="header-actions">
                  <ui-button variant="outline" [iconLeft]="true" (clicked)="openAddMeasurementModal()">
                    <span slot="icon-left">📏</span> Medir
                  </ui-button>
                  <ui-button variant="primary" [iconLeft]="true" (clicked)="openCreatePlanModal()">
                     <span slot="icon-left">🍽️</span> Plan
                  </ui-button>
              </div>
           </div>
           
           <!-- Navigation Tabs -->
           <nav class="profile-tabs">
              <button 
                class="tab-btn" 
                [class.active]="activeTab() === 'overview'"
                (click)="activeTab.set('overview')">
                Resumen General
              </button>
              <button 
                class="tab-btn" 
                [class.active]="activeTab() === 'anthropometry'"
                (click)="activeTab.set('anthropometry')">
                Antropometría
              </button>
              <button 
                class="tab-btn" 
                [class.active]="activeTab() === 'nutrition'"
                (click)="activeTab.set('nutrition')">
                Nutrición
              </button>
              <button 
                class="tab-btn" 
                [class.active]="activeTab() === 'profile'"
                (click)="activeTab.set('profile')">
                Perfil
              </button>
           </nav>
        </header>

        <!-- CONTENT: OVERVIEW -->
        @if (activeTab() === 'overview') {
            <div class="layout-grid">
                <!-- Chart Card -->
                <div class="main-col">
                    <ui-card>
                        <div class="card-header-row">
                            <h3>Evolución de Peso</h3>
                            <div class="toggle-group">
                                <button 
                                    class="toggle-btn"
                                    [class.active]="chartMetric() === 'weight'"
                                    (click)="chartMetric.set('weight')">Peso</button>
                                <button 
                                    class="toggle-btn"
                                    [class.active]="chartMetric() === 'fat'"
                                    (click)="chartMetric.set('fat')">% Grasa</button>
                            </div>
                        </div>
                        
                        @if (loadingMeasurements()) {
                            <div class="chart-placeholder">Cargando datos...</div>
                        } @else if (measurements().length > 0) {
                            <div class="chart-container">
                                <app-progress-chart 
                                     [data]="chartData()" 
                                     [color]="chartMetric() === 'weight' ? '#0ea5e9' : '#ec4899'">
                                </app-progress-chart>
                            </div>
                        } @else {
                             <div class="empty-chart">
                                <p>Sin datos registrados</p>
                                <ui-button variant="outline" size="sm" (clicked)="openAddMeasurementModal()">Registrar inicio</ui-button>
                            </div>
                        }
                    </ui-card>
                </div>

                <!-- Quick Summary Side -->
                <div class="side-col">
                    <!-- Active Plan Card -->
                    <ui-card>
                        <h3 class="card-title">Plan Nutricional</h3>
                        @if (loadingPlan()) {
                            <div class="skeleton-box"></div>
                        } @else if (nutritionPlan(); as plan) {
                            <div class="plan-summary-box">
                                <div class="status-label">Activo</div>
                                <h4>{{ plan.title }}</h4>
                                <p>Vence: {{ plan.valid_until | date:'mediumDate' }}</p>
                            </div>
                            <ui-button variant="outline" [block]="true" (clicked)="activeTab.set('nutrition')">Ver Detalles</ui-button>
                        } @else {
                            <div class="empty-box">
                                <p>No hay plan activo</p>
                                <ui-button variant="primary" size="sm" (clicked)="openCreatePlanModal()">Crear Plan</ui-button>
                            </div>
                        }
                    </ui-card>

                    <!-- Last Measurement Card -->
                    <ui-card>
                        <h3 class="card-title">Última Medición</h3>
                        @if (measurements().length > 0) {
                            @let last = measurements()[0];
                            <div class="metrics-grid">
                                <div class="metric-item">
                                    <span class="label">Peso</span>
                                    <span class="value">{{ last.weight_kg }} kg</span>
                                </div>
                                <div class="metric-item">
                                    <span class="label">IMC</span>
                                    <span class="value">{{ last.bmi ? (last.bmi | number:'1.1-1') : '-' }}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="label">% Grasa</span>
                                    <span class="value">{{ last.body_fat_percentage ? last.body_fat_percentage + '%' : '-' }}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="label">Cintura</span>
                                    <span class="value">{{ last.waist_circumference_cm || '-' }} cm</span>
                                </div>
                            </div>
                            <div class="timestamp">
                                {{ last.recorded_at | date:'medium' }}
                            </div>
                        } @else {
                            <p class="text-muted text-center">Sin registros recientes</p>
                        }
                    </ui-card>
                </div>
            </div>
        }

        <!-- CONTENT: ANTHROPOMETRY -->
        @if (activeTab() === 'anthropometry') {
             <div class="tab-content">
                <div class="section-header">
                    <h2>Historial de Mediciones</h2>
                    <ui-button variant="primary" [iconLeft]="true" (clicked)="openAddMeasurementModal()">
                        <span slot="icon-left">+</span> Nueva Medición
                    </ui-button>
                </div>

                <ui-card padding="0" class="overflow-hidden">
                    <div class="table-responsive">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Fecha</th>
                                    <th>Protocolo</th>
                                    <th>Peso</th>
                                    <th>IMC</th>
                                    <th>% Grasa</th>
                                    <th>Masa Musc.</th>
                                    <th>Cintura</th>
                                    <th>Sum. Pliegues</th>
                                </tr>
                            </thead>
                            <tbody>
                                @for (m of measurements(); track m.id) {
                                    <tr>
                                        <td class="font-medium">
                                            {{ m.recorded_at | date:'dd/MM/yyyy' }}
                                            <span class="sub-text">{{ m.recorded_at | date:'HH:mm' }}</span>
                                        </td>
                                        <td>
                                            <ui-badge variant="secondary" size="sm">{{ formatProtocol(m.protocol) }}</ui-badge>
                                        </td>
                                        <td class="font-bold">{{ m.weight_kg }} kg</td>
                                        <td>
                                            <span [class.warn]="(m.bmi || 0) > 25" [class.success]="(m.bmi || 0) >= 18.5 && (m.bmi || 0) <= 25">
                                                {{ m.bmi ? (m.bmi | number:'1.1-1') : '-' }}
                                            </span>
                                        </td>
                                        <td>{{ m.body_fat_percentage ? m.body_fat_percentage + '%' : '-' }}</td>
                                        <td>{{ m.muscle_mass_kg ? m.muscle_mass_kg + ' kg' : '-' }}</td>
                                        <td>{{ m.waist_circumference_cm || '-' }}</td>
                                        <td class="text-muted">
                                            {{ calculateSkinfoldSum(m) || '-' }} mm
                                        </td>
                                    </tr>
                                }
                                @if (measurements().length === 0) {
                                    <tr>
                                        <td colspan="8" class="empty-cell">
                                            No hay mediciones registradas.
                                        </td>
                                    </tr>
                                }
                            </tbody>
                        </table>
                    </div>
                </ui-card>
             </div>
        }
        
        <!-- CONTENT: NUTRITION -->
        @if (activeTab() === 'nutrition') {
            <div class="tab-content space-y">
                 @if (nutritionPlan(); as plan) {
                     <div class="plan-banner">
                        <div class="plan-header">
                            <div>
                                <span class="tag-active">Plan Activo</span>
                                <h2>{{ plan.title }}</h2>
                                <p>Creado el {{ plan.created_at | date }} • Vence el {{ plan.valid_until | date }}</p>
                            </div>
                            <ui-button variant="outline" size="sm" (clicked)="openCreatePlanModal()">Editar</ui-button>
                        </div>
                        
                        @if (plan.plan_data?.assessment?.goals) {
                            <div class="goals-grid">
                                @for (goal of plan.plan_data.assessment.goals; track $index) {
                                    <div class="goal-card">
                                        <span class="goal-label">{{ goal.target }}</span>
                                        <span class="goal-value">{{ goal.value }} <small>{{ goal.unit }}</small></span>
                                    </div>
                                }
                            </div>
                        }
                     </div>
                     
                     <h3 class="subsection-title">Detalle de Comidas</h3>
                     <div class="meals-grid">
                         @for (meal of getMeals(plan); track $index) {
                             <ui-card>
                                 <h4>{{ meal.name }}</h4>
                                 <div class="meal-components">
                                     @for (comp of meal.components; track $index) {
                                         <div class="component-row">
                                             <span>{{ comp.group || comp.item }}</span>
                                             <div class="portion-col">
                                                <span class="portion">
                                                    {{ comp.quantity?.portions ? comp.quantity.portions + ' Porc.' : (comp.portion_size || '') }}
                                                </span>
                                                @if(comp.quantity?.notes) {
                                                    <span class="portion-note">{{ comp.quantity.notes }}</span>
                                                }
                                             </div>
                                         </div>
                                     }
                                 </div>
                             </ui-card>
                         }
                     </div>

                     <!-- Nutrition Adherence Analysis -->
                     <h3 class="subsection-title">Análisis y Recomendaciones</h3>
                     <div class="analysis-grid">
                         <app-nutrition-adherence-card
                           [userId]="rel.patient.auth_user_id"
                           [days]="14">
                         </app-nutrition-adherence-card>
                         <app-ai-recommendations-card
                           [userId]="rel.patient.auth_user_id">
                         </app-ai-recommendations-card>
                     </div>

                 } @else {
                     <div class="empty-plan-state">
                         <div class="icon">🥗</div>
                         <h3>Sin Plan Nutricional</h3>
                         <p>Este paciente aún no tiene un plan de alimentación asignado. Crea uno nuevo para comenzar el tratamiento.</p>
                         <ui-button variant="primary" size="lg" [iconLeft]="true" (clicked)="openCreatePlanModal()">
                            <span slot="icon-left">+</span> Crear Primer Plan
                         </ui-button>
                     </div>
                 }
            </div>
        }

        <!-- CONTENT: PROFILE -->
        @if (activeTab() === 'profile') {
             <div class="layout-grid">
                <ui-card>
                    <h3 class="card-title border-b">Datos Personales</h3>
                    <dl class="desc-list">
                        <div class="desc-row">
                            <dt>Nombre</dt>
                            <dd>{{ rel.patient.full_name }}</dd>
                        </div>
                        <div class="desc-row">
                            <dt>Email</dt>
                            <dd>{{ rel.patient.email }}</dd>
                        </div>
                        <div class="desc-row">
                            <dt>Teléfono</dt>
                            <dd>{{ rel.patient.phone_number || '-' }}</dd>
                        </div>
                        <div class="desc-row">
                            <dt>Género</dt>
                            <dd>{{ rel.patient.gender || '-' | titlecase }}</dd>
                        </div>
                    </dl>
                </ui-card>

                <ui-card>
                    <h3 class="card-title border-b">Configuración de Cuidado</h3>
                    <dl class="desc-list mb-4">
                        <div class="desc-row">
                            <dt>Inicio</dt>
                            <dd>{{ rel.started_at | date }}</dd>
                        </div>
                        <div class="desc-row">
                            <dt>Contexto</dt>
                            <dd>
                                {{ rel.context_type === 'independent' ? 'Privado / Independiente' : 'Institucional' }}
                            </dd>
                        </div>
                    </dl>
                    
                    <div class="danger-zone">
                        <button class="btn-danger-link" (click)="endRelationship()">
                            Finalizar relación con paciente
                        </button>
                    </div>
                </ui-card>
             </div>
        }
      }

      <!-- MODALS -->
      <app-create-nutrition-plan-modal
        [isOpen]="showCreatePlanModal()"
        [patient]="relationship()"
        (closed)="closeCreatePlanModal()"
        (planCreated)="onPlanCreated()"
      ></app-create-nutrition-plan-modal>

      <app-add-measurement-modal
        [isOpen]="showAddMeasurementModal()"
        [userId]="relationship()?.patient?.auth_user_id || ''"
        (closed)="closeAddMeasurementModal()"
        (saved)="onMeasurementSaved()"
      ></app-add-measurement-modal>
    </div>
  `,
  styles: [`
    /* Base */
    .detail-container {
        max-width: 1200px; margin: 0 auto; padding: 2rem; font-family: 'Inter', sans-serif;
    }
    
    /* Loading & Error */
    .loading-state { display: flex; flex-direction: column; align-items: center; padding: 5rem; color: #6b7280; }
    .spinner { width: 3rem; height: 3rem; border: 3px solid #e5e7eb; border-top-color: #3b82f6; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 1rem; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .error-state { max-width: 400px; margin: 3rem auto; text-align: center; padding: 2rem; }
    .error-icon { font-size: 3rem; margin-bottom: 1rem; }

    /* Header */
    .profile-header { background: white; border-radius: 1rem; border: 1px solid #e5e7eb; padding: 1.5rem; margin-bottom: 2rem; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .header-content { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem; }
    .profile-info { display: flex; align-items: center; gap: 1rem; }
    .profile-avatar { width: 4rem; height: 4rem; border-radius: 50%; background: #eff6ff; color: #1d4ed8; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: 700; }
    .profile-info h1 { margin: 0; font-size: 1.5rem; color: #111827; font-weight: 700; }
    .profile-meta { display: flex; align-items: center; gap: 0.75rem; color: #6b7280; font-size: 0.875rem; margin-top: 0.25rem; }
    .separator { color: #d1d5db; }
    .header-actions { display: flex; gap: 0.5rem; }

    /* Tabs */
    .profile-tabs { display: flex; gap: 1.5rem; margin-top: 2rem; border-bottom: 1px solid #e5e7eb; overflow-x: auto; }
    .tab-btn {
        background: none; border: none; border-bottom: 2px solid transparent; padding: 0.75rem 0.25rem; font-weight: 500; color: #6b7280; cursor: pointer; white-space: nowrap; transition: all 0.2s;
        &:hover { color: #374151; }
        &.active { border-bottom-color: #3b82f6; color: #2563eb; }
    }

    /* Layout */
    .layout-grid { display: grid; grid-template-columns: 1fr; gap: 2rem; margin-top: 1rem; }
    @media (min-width: 1024px) { .layout-grid { grid-template-columns: 2fr 1fr; } }
    .main-col, .side-col { display: flex; flex-direction: column; gap: 1.5rem; }
    
    /* Cards & Widgets */
    .card-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
    .card-header-row h3 { margin: 0; font-weight: 700; color: #1f2937; font-size: 1.125rem; }
    
    .toggle-group { background: #f3f4f6; padding: 0.25rem; border-radius: 0.5rem; display: flex; }
    .toggle-btn {
        padding: 0.25rem 0.75rem; border: none; background: none; border-radius: 0.375rem; font-size: 0.75rem; font-weight: 600; color: #6b7280; cursor: pointer;
        &.active { background: white; color: #111827; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    }
    
    .chart-container { height: 18rem; width: 100%; }
    .chart-placeholder, .empty-chart { height: 16rem; display: flex; align-items: center; justify-content: center; color: #9ca3af; flex-direction: column; gap: 0.5rem; background: #f9fafb; border-radius: 0.5rem; border: 2px dashed #e5e7eb; }

    /* Summary Side */
    .card-title { font-size: 1rem; font-weight: 700; color: #1f2937; margin: 0 0 1rem; }
    .skeleton-box { height: 5rem; background: #f3f4f6; border-radius: 0.5rem; }
    .plan-summary-box { background: #f0fdf4; border: 1px solid #dcfce7; border-radius: 0.75rem; padding: 1rem; margin-bottom: 0.75rem; }
    .status-label { font-size: 0.75rem; font-weight: 700; color: #15803d; text-transform: uppercase; margin-bottom: 0.25rem; }
    .plan-summary-box h4 { margin: 0; font-weight: 700; color: #14532d; }
    .plan-summary-box p { margin: 0.25rem 0 0; font-size: 0.875rem; color: #166534; }
    .empty-box { text-align: center; padding: 1.5rem; background: #f9fafb; border: 2px dashed #e5e7eb; border-radius: 0.75rem; color: #6b7280; font-size: 0.875rem; p { margin-bottom: 0.75rem; } }

    /* Metrics Grid */
    .metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }
    .metric-item { background: #f9fafb; padding: 0.75rem; border-radius: 0.5rem; display: flex; flex-direction: column; }
    .metric-item .label { font-size: 0.75rem; color: #6b7280; }
    .metric-item .value { font-weight: 700; color: #111827; font-size: 1.125rem; }
    .timestamp { text-align: center; font-size: 0.75rem; color: #9ca3af; }

    /* Table */
    .tab-content { animation: fadeIn 0.3s ease; }
    .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; h2 { font-size: 1.25rem; font-weight: 700; color: #1f2937; margin: 0; } }
    .overflow-hidden { overflow: hidden; border-radius: 0.75rem; border: 1px solid #e5e7eb; }
    .table-responsive { overflow-x: auto; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    .data-table th { background: #f9fafb; text-align: left; padding: 1rem; font-weight: 600; color: #6b7280; border-bottom: 1px solid #e5e7eb; }
    .data-table td { padding: 1rem; border-bottom: 1px solid #f3f4f6; color: #374151; }
    .data-table tr:hover { background: #f9fafb; }
    .data-table .font-medium { font-weight: 500; color: #111827; }
    .data-table .font-bold { font-weight: 700; }
    .data-table .sub-text { display: block; font-size: 0.75rem; color: #9ca3af; font-weight: 400; }
    .data-table .warn { color: #f59e0b; font-weight: 600; }
    .data-table .success { color: #10b981; font-weight: 600; }
    .data-table .text-muted { color: #9ca3af; }
    .empty-cell { text-align: center; padding: 3rem; color: #6b7280; }

    /* Plan Detail */
    .space-y { display: flex; flex-direction: column; gap: 1.5rem; }
    .plan-banner { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 1rem; padding: 1.5rem; }
    .plan-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; }
    .tag-active { font-size: 0.75rem; font-weight: 800; color: #15803d; text-transform: uppercase; letter-spacing: 0.05em; }
    .plan-header h2 { margin: 0.25rem 0; font-size: 1.5rem; color: #14532d; font-weight: 700; }
    .plan-header p { margin: 0; color: #166534; font-size: 0.875rem; }
    .goals-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; }
    .goal-card { background: rgba(255,255,255,0.6); border: 1px solid #dcfce7; padding: 1rem; border-radius: 0.75rem; }
    .goal-label { display: block; font-size: 0.75rem; font-weight: 700; color: #166534; text-transform: uppercase; margin-bottom: 0.25rem; }
    .goal-value { font-size: 1.25rem; font-weight: 700; color: #14532d; small { font-size: 0.875rem; font-weight: 400; color: #166534; margin-left: 0.25rem; } }
    .subsection-title { font-size: 1.125rem; font-weight: 700; color: #1f2937; margin: 0 0 1rem; }
    .meals-grid { display: grid; gap: 1rem; }
    .meal-components { display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.5rem; }
    .component-row { display: flex; justify-content: space-between; font-size: 0.875rem; color: #4b5563; border-bottom: 1px solid #f3f4f6; padding-bottom: 0.25rem; align-items: flex-start; }
    .component-row .portion { font-weight: 500; color: #111827; }
    .portion-col { text-align: right; display: flex; flex-direction: column; align-items: flex-end; }
    .portion-note { font-size: 0.7rem; color: #9ca3af; }
    .analysis-grid { display: grid; grid-template-columns: 1fr; gap: 1.5rem; }
    @media (min-width: 768px) { .analysis-grid { grid-template-columns: 1fr 1fr; } }
    .empty-plan-state { text-align: center; padding: 4rem 2rem; background: #f9fafb; border-radius: 1rem; border: 2px dashed #e5e7eb; .icon { font-size: 3rem; margin-bottom: 1rem; } h3 { margin: 0 0 0.5rem; font-size: 1.25rem; font-weight: 700; color: #1f2937; } p { color: #6b7280; max-width: 400px; margin: 0 auto 1.5rem; } }

    /* Profile */
    .desc-list { margin: 0; }
    .desc-row { display: grid; grid-template-columns: 1fr 2fr; padding: 0.75rem 0; border-bottom: 1px solid #f3f4f6; &:last-child { border-bottom: none; } }
    .desc-row dt { font-size: 0.875rem; font-weight: 500; color: #6b7280; }
    .desc-row dd { font-size: 0.875rem; font-weight: 500; color: #111827; margin: 0; }
    .border-b { border-bottom: 1px solid #e5e7eb; padding-bottom: 0.75rem; margin-bottom: 1rem; }
    .danger-zone { padding-top: 1rem; border-top: 1px solid #f3f4f6; }
    .btn-danger-link { background: none; border: none; color: #dc2626; font-size: 0.875rem; font-weight: 500; cursor: pointer; padding: 0; &:hover { text-decoration: underline; } }
    
    @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
    .text-center { text-align: center; }
    .text-muted { color: #9ca3af; }
  `]
})
export class PatientDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly careService = inject(CareRelationshipService);
  private readonly nutritionService = inject(NutritionPlanService);
  private readonly bodyService = inject(BodyMeasurementService);

  // Signals
  readonly relationship = signal<CareRelationshipWithPatient | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly activeTab = signal<TabType>('overview');

  // Nutrition Plan State
  readonly nutritionPlan = signal<NutritionPlan | null>(null);
  readonly loadingPlan = signal(false);
  readonly showCreatePlanModal = signal(false);

  // Body Measurements State
  readonly measurements = signal<BodyMeasurement[]>([]);
  readonly loadingMeasurements = signal(false);
  readonly showAddMeasurementModal = signal(false);
  readonly chartMetric = signal<'weight' | 'fat'>('weight');
  
  // Computed
  readonly chartData = computed<ChartPoint[]>(() => {
      const data = this.measurements();
      const metric = this.chartMetric();
      
      // Sort by date ascending for chart
      const sorted = [...data].sort((a, b) => new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime());
      
      return sorted
        .filter(m => metric === 'weight' ? !!m.weight_kg : !!m.body_fat_percentage)
        .map(m => ({
            date: m.recorded_at,
            value: metric === 'weight' ? Number(m.weight_kg) : Number(m.body_fat_percentage),
            label: metric === 'weight' ? 'Peso' : '% Grasa'
        }));
  });

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
      const relationship = await this.careService.getPatientRelationship(relationshipId);

      if (!relationship) {
        this.error.set('No se encontró la relación con el paciente');
        return;
      }

      this.relationship.set(relationship);
      
      const patientId = relationship.patient.auth_user_id;
      await Promise.all([
          this.loadActivePlan(patientId),
          this.loadMeasurements(patientId)
      ]);
      
    } catch (err) {
      console.error('Error al cargar detalle del paciente:', err);
      this.error.set('Error al cargar la información del paciente');
    } finally {
      this.loading.set(false);
    }
  }
  
  private async loadActivePlan(patientId: string): Promise<void> {
    this.loadingPlan.set(true);
    try {
       const plan = await this.nutritionService.getActivePlan(patientId);
       this.nutritionPlan.set(plan);
    } catch (err) {
       // Silent fail for plan
    } finally {
      this.loadingPlan.set(false);
    }
  }

  private async loadMeasurements(patientId: string): Promise<void> {
    this.loadingMeasurements.set(true);
    try {
        this.bodyService.getMeasurementsByPatient(patientId).subscribe({
            next: (data) => {
                // Sort descending for table
                const sorted = [...data].sort((a, b) => new Date(b.recorded_at).getTime() - new Date(a.recorded_at).getTime());
                this.measurements.set(sorted);
            },
            error: (err) => console.error('Error cargando mediciones:', err),
            complete: () => this.loadingMeasurements.set(false)
        });
    } catch (err) {
        this.loadingMeasurements.set(false);
    }
  }

  async endRelationship(): Promise<void> {
    if (!this.relationship()) return;
    if (!confirm('¿Estás seguro de finalizar esta relación?')) return;

    try {
      await this.careService.endRelationship(this.relationship()!.id);
      this.router.navigate(['/profesional/pacientes']);
    } catch (error) {
      alert('Error al finalizar la relación.');
    }
  }
  
  // Helpers
  getMeals(plan: NutritionPlan): any[] {
      return plan.plan_data?.directives?.meals || [];
  }

  formatProtocol(p: string | undefined): string {
      const map: any = {
          'clinical_basic': 'Clínico',
          'isak_restricted': 'ISAK 1',
          'isak_full': 'ISAK 2',
          'elderly_sarcopenia': 'Sarcopenia'
      };
      return map[p || ''] || 'Básico';
  }
  
  calculateSkinfoldSum(m: BodyMeasurement): number | null {
      const folds = [
          m.triceps_skinfold_mm, m.biceps_skinfold_mm, m.subscapular_skinfold_mm,
          m.suprailiac_skinfold_mm, m.abdominal_skinfold_mm, m.thigh_skinfold_mm, 
          m.calf_skinfold_mm
      ];
      const sum = folds.reduce((acc, curr) => {
          if (curr === null || curr === undefined) return acc;
          const currentAcc = acc ?? 0;
          return currentAcc + Number(curr);
      }, 0 as number | null);

      return (sum !== null && sum > 0) ? Math.round(sum * 10) / 10 : null;
  }

  // Modal Controllers
  openCreatePlanModal() { this.showCreatePlanModal.set(true); }
  closeCreatePlanModal() { this.showCreatePlanModal.set(false); }
  async onPlanCreated() { 
      if (this.relationship()) await this.loadActivePlan(this.relationship()!.patient.auth_user_id); 
  }

  openAddMeasurementModal() { this.showAddMeasurementModal.set(true); }
  closeAddMeasurementModal() { this.showAddMeasurementModal.set(false); }
  onMeasurementSaved() {
      if (this.relationship()) this.loadMeasurements(this.relationship()!.patient.auth_user_id);
  }
}