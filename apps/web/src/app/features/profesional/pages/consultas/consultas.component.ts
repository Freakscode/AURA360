import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

interface Consulta {
  id: string;
  paciente: string;
  fecha: string;
  hora: string;
  tipo: string;
  estado: 'programada' | 'completada' | 'cancelada';
  modalidad: 'virtual' | 'presencial';
}

@Component({
  selector: 'app-consultas',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule
  ],
  template: `
    <div class="page-container">
      <div class="page-header">
        <div>
          <h1 class="page-title">Gestión de Consultas</h1>
          <p class="page-subtitle">Administra tus citas y sesiones con pacientes</p>
        </div>
        <button mat-flat-button color="primary">
          <mat-icon>add</mat-icon>
          Nueva Consulta
        </button>
      </div>

      <!-- Filtros -->
      <mat-card class="filters-card">
        <mat-card-content>
          <div class="filters-grid">
            <mat-form-field appearance="outline">
              <mat-label>Buscar paciente</mat-label>
              <mat-icon matPrefix>search</mat-icon>
              <input matInput placeholder="Nombre o expediente...">
            </mat-form-field>

            <mat-form-field appearance="outline">
              <mat-label>Estado</mat-label>
              <mat-select value="todas">
                <mat-option value="todas">Todas</mat-option>
                <mat-option value="programada">Programadas</mat-option>
                <mat-option value="completada">Completadas</mat-option>
                <mat-option value="cancelada">Canceladas</mat-option>
              </mat-select>
            </mat-form-field>

            <mat-form-field appearance="outline">
              <mat-label>Fecha</mat-label>
              <input matInput type="date">
            </mat-form-field>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Tabla -->
      <mat-card class="table-card">
        <mat-table [dataSource]="consultas()">
          
          <!-- Hora Column -->
          <ng-container matColumnDef="hora">
            <mat-header-cell *matHeaderCellDef> Hora </mat-header-cell>
            <mat-cell *matCellDef="let row"> 
              <div class="time-cell">
                <span class="time-text">{{row.hora}}</span>
                <span class="date-subtext">{{row.fecha}}</span>
              </div>
            </mat-cell>
          </ng-container>

          <!-- Paciente Column -->
          <ng-container matColumnDef="paciente">
            <mat-header-cell *matHeaderCellDef> Paciente </mat-header-cell>
            <mat-cell *matCellDef="let row"> 
              <div class="patient-cell">
                <div class="patient-avatar">{{row.paciente.charAt(0)}}</div>
                <span class="patient-name">{{row.paciente}}</span>
              </div>
            </mat-cell>
          </ng-container>

          <!-- Tipo Column -->
          <ng-container matColumnDef="tipo">
            <mat-header-cell *matHeaderCellDef> Tipo </mat-header-cell>
            <mat-cell *matCellDef="let row"> {{row.tipo}} </mat-cell>
          </ng-container>

          <!-- Modalidad Column -->
          <ng-container matColumnDef="modalidad">
            <mat-header-cell *matHeaderCellDef> Modalidad </mat-header-cell>
            <mat-cell *matCellDef="let row"> 
              <div class="mode-badge" [class.virtual]="row.modalidad === 'virtual'">
                <mat-icon class="mode-icon">{{ row.modalidad === 'virtual' ? 'videocam' : 'apartment' }}</mat-icon>
                {{row.modalidad}} 
              </div>
            </mat-cell>
          </ng-container>

          <!-- Estado Column -->
          <ng-container matColumnDef="estado">
            <mat-header-cell *matHeaderCellDef> Estado </mat-header-cell>
            <mat-cell *matCellDef="let row">
              <span class="status-chip" [ngClass]="row.estado">
                {{row.estado}}
              </span>
            </mat-cell>
          </ng-container>

          <!-- Actions Column -->
          <ng-container matColumnDef="acciones">
            <mat-header-cell *matHeaderCellDef></mat-header-cell>
            <mat-cell *matCellDef="let row">
              <button mat-icon-button color="primary" matTooltip="Ver detalles">
                <mat-icon>visibility</mat-icon>
              </button>
              @if (row.modalidad === 'virtual' && row.estado === 'programada') {
                <button mat-icon-button color="accent" matTooltip="Iniciar videollamada">
                  <mat-icon>video_call</mat-icon>
                </button>
              }
            </mat-cell>
          </ng-container>

          <mat-header-row *matHeaderRowDef="displayedColumns"></mat-header-row>
          <mat-row *matRowDef="let row; columns: displayedColumns;"></mat-row>
        </mat-table>
      </mat-card>
    </div>
  `,
  styles: [`
    .page-container {
      display: flex;
      flex-direction: column;
      gap: 24px;
    }

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      
      .page-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0;
        color: #1e293b;
      }
      
      .page-subtitle {
        margin: 4px 0 0;
        color: #64748b;
      }
    }

    .filters-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 16px;
      
      @media (min-width: 768px) {
        grid-template-columns: 2fr 1fr 1fr;
      }
    }

    .time-cell {
      display: flex;
      flex-direction: column;
      
      .time-text { font-weight: 600; color: #0f172a; }
      .date-subtext { font-size: 0.75rem; color: #64748b; }
    }

    .patient-cell {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .patient-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background-color: #e0e7ff;
        color: #4338ca;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.85rem;
      }
      
      .patient-name { font-weight: 500; }
    }

    .mode-badge {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 0.85rem;
      color: #475569;
      
      .mode-icon { font-size: 18px; width: 18px; height: 18px; }
      
      &.virtual { color: #0284c7; }
    }

    .status-chip {
      padding: 4px 12px;
      border-radius: 16px;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      
      &.programada { background-color: #e0f2fe; color: #0284c7; }
      &.completada { background-color: #dcfce7; color: #16a34a; }
      &.cancelada { background-color: #fee2e2; color: #dc2626; }
    }
  `]
})
export class ConsultasComponent {
  displayedColumns: string[] = ['hora', 'paciente', 'tipo', 'modalidad', 'estado', 'acciones'];
  
  consultas = signal<Consulta[]>([
    {
      id: '1',
      paciente: 'María González',
      fecha: 'Hoy',
      hora: '10:00 AM',
      tipo: 'Psicología',
      estado: 'programada',
      modalidad: 'virtual'
    },
    {
      id: '2',
      paciente: 'Carlos Rodríguez',
      fecha: 'Hoy',
      hora: '11:30 AM',
      tipo: 'Nutrición',
      estado: 'programada',
      modalidad: 'presencial'
    },
    {
      id: '3',
      paciente: 'Ana López',
      fecha: 'Ayer',
      hora: '03:00 PM',
      tipo: 'Seguimiento',
      estado: 'completada',
      modalidad: 'virtual'
    },
    {
      id: '4',
      paciente: 'Roberto Díaz',
      fecha: 'Ayer',
      hora: '09:00 AM',
      tipo: 'Consulta Inicial',
      estado: 'cancelada',
      modalidad: 'presencial'
    }
  ]);
}
