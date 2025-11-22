import { Component, inject, signal, OnInit, computed } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';

import { AuthSessionStore } from '../../../auth/services/auth-session.store';
import { CareRelationshipService } from '../../services/care-relationship.service';
import { CreatePatientModalComponent } from '../../components/create-patient-modal/create-patient-modal.component';
import { ButtonComponent, CardComponent, BadgeComponent } from '../../../../shared/components/ui';

@Component({
  selector: 'app-profesional-dashboard',
  standalone: true,
  imports: [
    CommonModule, 
    RouterLink, 
    DatePipe,
    CreatePatientModalComponent,
    ButtonComponent, 
    CardComponent, 
    BadgeComponent
  ],
  template: `
    <div class="dashboard-container">
      <!-- Header Section -->
      <header class="dashboard-header">
        <div class="header-content">
          <div class="greeting-section">
            <h1>Hola, {{ userDisplayName() }}</h1>
            <p class="subtitle">{{ currentDate | date:'fullDate' | titlecase }}</p>
          </div>
          
          <div class="header-actions">
             <ui-button variant="primary" (clicked)="openCreateModal()">
               + Nuevo Paciente
             </ui-button>
          </div>
        </div>
      </header>

      <!-- KPI Stats Grid -->
      <div class="stats-grid">
        <!-- Pacientes Activos -->
        <ui-card class="stat-card border-primary">
          <div class="stat-content">
             <div>
                <p class="stat-label">Pacientes Activos</p>
                <h3 class="stat-value">
                    @if (careService.loading()) { <span class="loading-dots">...</span> } 
                    @else { {{ activePatientsCount() }} }
                </h3>
             </div>
             <div class="stat-icon icon-primary">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
             </div>
          </div>
          <div class="stat-trend positive">
             <span>↑ 2 nuevos esta semana</span>
          </div>
        </ui-card>

        <!-- Citas Hoy (Mock) -->
        <ui-card class="stat-card border-secondary">
          <div class="stat-content">
             <div>
                <p class="stat-label">Citas Hoy</p>
                <h3 class="stat-value">3</h3>
             </div>
             <div class="stat-icon icon-secondary">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
             </div>
          </div>
          <div class="stat-trend neutral">
             Próxima: 11:30 AM (Juan Pérez)
          </div>
        </ui-card>

        <!-- Alertas -->
        <ui-card class="stat-card border-warning">
          <div class="stat-content">
             <div>
                <p class="stat-label">Alertas</p>
                <h3 class="stat-value">1</h3>
             </div>
             <div class="stat-icon icon-warning">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                   <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
             </div>
          </div>
          <div class="stat-trend text-gray">
             Plan por vencer: Ana Gómez
          </div>
        </ui-card>
      </div>

      <div class="content-grid">
        
        <!-- Columna Izquierda: Herramientas -->
        <div class="main-column">
            
            <!-- Herramientas Rápidas -->
            <section class="section-group">
                <h2 class="section-title">
                    <span class="title-icon">⚡</span> Acciones Rápidas
                </h2>
                <div class="tools-grid">
                    <div class="tool-card" routerLink="/profesional/herramientas/planificador">
                        <div class="tool-icon icon-purple">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
                        </div>
                        <h3>Planificador</h3>
                        <p>Crear dietas y menús.</p>
                    </div>

                    <div class="tool-card" routerLink="/profesional/herramientas/antropometria">
                        <div class="tool-icon icon-teal">
                             <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
                        </div>
                        <h3>Antropometría</h3>
                        <p>Registrar medidas.</p>
                    </div>
                </div>
            </section>

            <!-- Pacientes Recientes -->
            <section class="section-group">
                <div class="section-header">
                    <h2 class="section-title">Pacientes Recientes</h2>
                    <a routerLink="/profesional/pacientes" class="link-action">Ver todos</a>
                </div>
                
                <ui-card padding="0" class="overflow-hidden">
                   @if (careService.loading()) {
                       <div class="p-8 text-center">Cargando...</div>
                   } @else if (recentPatients().length === 0) {
                       <div class="p-8 text-center">
                           <div class="text-muted mb-3">No hay pacientes recientes</div>
                           <ui-button size="sm" variant="outline" (clicked)="openCreateModal()">Agregar Paciente</ui-button>
                       </div>
                   } @else {
                       <table class="recent-table">
                           <thead>
                               <tr>
                                   <th>Nombre</th>
                                   <th>Estado</th>
                                   <th>Acción</th>
                               </tr>
                           </thead>
                           <tbody>
                               @for (rel of recentPatients(); track rel.id) {
                                   <tr>
                                       <td class="font-medium">{{ rel.patient.full_name }}</td>
                                       <td>
                                           <ui-badge [variant]="rel.status === 'active' ? 'success' : 'secondary'" size="sm" [dot]="true">
                                               {{ rel.status === 'active' ? 'Activo' : 'Inactivo' }}
                                           </ui-badge>
                                       </td>
                                       <td>
                                           <a [routerLink]="['/profesional/pacientes', rel.id]" class="link-action">Ver ficha</a>
                                       </td>
                                   </tr>
                               }
                           </tbody>
                       </table>
                   }
                </ui-card>
            </section>
        </div>

        <!-- Columna Derecha: Agenda / Notificaciones -->
        <aside class="aside-column">
            <!-- Próximas Citas (Mock) -->
            <section class="section-group">
                <h2 class="section-title">Agenda de Hoy</h2>
                <ui-card>
                   <div class="agenda-list">
                       <div class="agenda-item">
                           <div class="agenda-time">
                               <span class="time">10:00</span>
                               <span class="meridiem">AM</span>
                           </div>
                           <div class="agenda-details">
                               <h4>Maria Gonzalez</h4>
                               <p class="tag-primary">Consulta Inicial</p>
                           </div>
                       </div>
                       <div class="agenda-item">
                           <div class="agenda-time">
                               <span class="time">11:30</span>
                               <span class="meridiem">AM</span>
                           </div>
                           <div class="agenda-details">
                               <h4>Juan Pérez</h4>
                               <p class="tag-success">Control Mensual</p>
                           </div>
                       </div>
                   </div>
                   <div class="agenda-footer">
                       <button class="link-action">Ver agenda completa</button>
                   </div>
                </ui-card>
            </section>
            
            <!-- Tips / Novedades -->
            <ui-card class="promo-card">
                <h3>¿Sabías qué?</h3>
                <p>Ahora puedes registrar mediciones ISAK completas directamente desde la ficha del paciente.</p>
                <ui-button variant="outline" class="btn-promo">Ver Novedades</ui-button>
            </ui-card>
        </aside>
      </div>
      
      <!-- Modales -->
      <app-create-patient-modal 
         [isOpen]="showCreateModal()"
         (closed)="closeCreateModal()"
         (created)="onPatientCreated()"
      />
    </div>
  `,
  styles: [`
    /* Variables & Base */
    :host { display: block; }
    
    .dashboard-container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 2rem;
      font-family: 'Inter', sans-serif;
    }
    
    /* Header */
    .dashboard-header { margin-bottom: 2rem; }
    .header-content { display: flex; justify-content: space-between; align-items: flex-end; gap: 1rem; flex-wrap: wrap; }
    h1 { font-size: 2rem; font-weight: 700; color: #1f2937; margin: 0; line-height: 1.2; }
    .subtitle { font-size: 1.125rem; color: #6b7280; margin: 0.25rem 0 0; text-transform: capitalize; }

    /* Stats Grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }
    
    .stat-card {
        background: white;
        border-left-width: 4px;
        border-style: solid;
    }
    .border-primary { border-left-color: #3b82f6; }
    .border-secondary { border-left-color: #8b5cf6; }
    .border-warning { border-left-color: #f59e0b; }
    
    .stat-content { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; }
    .stat-label { font-size: 0.875rem; font-weight: 600; text-transform: uppercase; color: #6b7280; margin: 0 0 0.25rem; letter-spacing: 0.05em; }
    .stat-value { font-size: 2.25rem; font-weight: 700; color: #111827; margin: 0; line-height: 1; }
    
    .stat-icon {
        padding: 0.75rem; border-radius: 9999px; display: flex;
        svg { width: 1.5rem; height: 1.5rem; }
    }
    .icon-primary { background: #eff6ff; color: #3b82f6; }
    .icon-secondary { background: #f3e8ff; color: #8b5cf6; }
    .icon-warning { background: #fffbeb; color: #f59e0b; }
    
    .stat-trend { font-size: 0.875rem; font-weight: 500; }
    .positive { color: #10b981; }
    .neutral { color: #6b7280; }
    
    /* Content Grid */
    .content-grid { display: grid; grid-template-columns: 1fr; gap: 2rem; }
    @media (min-width: 1024px) { .content-grid { grid-template-columns: 2fr 1fr; } }

    /* Section Styles */
    .section-group { margin-bottom: 2rem; }
    .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
    .section-title { font-size: 1.25rem; font-weight: 700; color: #1f2937; margin: 0 0 1rem; display: flex; align-items: center; gap: 0.5rem; }
    .title-icon { font-size: 1.25rem; }
    
    /* Tools */
    .tools-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; }
    .tool-card {
        background: white; border: 1px solid #e5e7eb; border-radius: 0.75rem; padding: 1.25rem;
        cursor: pointer; transition: all 0.2s; display: flex; flex-direction: column; align-items: center; text-align: center;
    }
    .tool-card:hover { transform: translateY(-2px); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border-color: #d1d5db; }
    .tool-icon {
        width: 3rem; height: 3rem; border-radius: 0.5rem; display: flex; align-items: center; justify-content: center; margin-bottom: 0.75rem;
        svg { width: 1.5rem; height: 1.5rem; }
    }
    .icon-purple { background: #f3e8ff; color: #7c3aed; }
    .icon-teal { background: #ccfbf6; color: #0d9488; }
    
    .tool-card h3 { font-weight: 600; color: #111827; margin: 0 0 0.25rem; font-size: 1rem; }
    .tool-card p { font-size: 0.875rem; color: #6b7280; margin: 0; }

    /* Recent Table */
    .recent-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    .recent-table th { text-align: left; padding: 0.75rem 1rem; background: #f9fafb; color: #6b7280; font-weight: 600; border-bottom: 1px solid #e5e7eb; }
    .recent-table td { padding: 0.75rem 1rem; border-bottom: 1px solid #f3f4f6; color: #374151; }
    .recent-table tr:last-child td { border-bottom: none; }
    .link-action { color: #3b82f6; font-weight: 500; text-decoration: none; cursor: pointer; }
    .link-action:hover { color: #1d4ed8; text-decoration: underline; }

    /* Agenda */
    .agenda-list { display: flex; flex-direction: column; gap: 1rem; }
    .agenda-item { display: flex; gap: 1rem; padding-bottom: 1rem; border-bottom: 1px solid #f3f4f6; }
    .agenda-time { text-align: center; min-width: 3.5rem; }
    .time { display: block; font-weight: 700; color: #111827; font-size: 1.125rem; }
    .meridiem { font-size: 0.75rem; color: #6b7280; font-weight: 600; }
    .agenda-details h4 { margin: 0 0 0.25rem; font-weight: 600; color: #111827; }
    .tag-primary { color: #3b82f6; font-size: 0.875rem; margin: 0; }
    .tag-success { color: #10b981; font-size: 0.875rem; margin: 0; }
    .agenda-footer { text-align: center; padding-top: 1rem; }

    /* Promo Card */
    .promo-card { background: linear-gradient(135deg, #3b82f6, #1e40af); color: white; border: none; }
    .promo-card h3 { font-weight: 700; font-size: 1.125rem; margin: 0 0 0.5rem; color: white; }
    .promo-card p { font-size: 0.9375rem; margin: 0 0 1rem; color: #dbeafe; }
    
    /* Utils */
    .p-8 { padding: 2rem; }
    .text-center { text-align: center; }
    .text-muted { color: #6b7280; }
    .mb-3 { margin-bottom: 0.75rem; }
    .font-medium { font-weight: 500; }
    .overflow-hidden { overflow: hidden; }
  `]
})
export class DashboardComponent implements OnInit {
  readonly authStore = inject(AuthSessionStore);
  readonly careService = inject(CareRelationshipService);
  
  readonly currentDate = new Date();
  readonly showCreateModal = signal(false);

  // Computed Properties
  readonly userDisplayName = computed(() => 
      this.authStore.userFullName() ?? this.authStore.userEmail()?.split('@')[0] ?? 'Profesional'
  );
  
  readonly activePatientsCount = computed(() => 
     this.careService.patients().filter(p => p.status === 'active').length
  );
  
  readonly recentPatients = computed(() => 
     this.careService.patients().slice(0, 5)
  );

  async ngOnInit() {
      await this.careService.loadMyPatients();
  }
  
  openCreateModal() {
      this.showCreateModal.set(true);
  }
  
  closeCreateModal() {
      this.showCreateModal.set(false);
  }
  
  async onPatientCreated() {
      this.closeCreateModal();
      await this.careService.loadMyPatients();
  }
}
