import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatDividerModule } from '@angular/material/divider';

interface HistorialEntry {
  id: string;
  paciente: string;
  ultimoRegistro: string;
  diagnostico?: string;
  avatar?: string;
}

@Component({
  selector: 'app-historial',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatListModule,
    MatDividerModule
  ],
  template: `
    <div class="page-container">
      <div class="search-section">
        <h1 class="section-title">Historial Clínico</h1>
        <p class="section-desc">Busca expedientes de pacientes para ver su historial completo</p>
        
        <mat-card class="search-card">
          <mat-card-content>
            <div class="search-box">
              <mat-icon class="search-icon">search</mat-icon>
              <input type="text" placeholder="Buscar por nombre, DNI o número de expediente..." class="search-input">
              <button mat-flat-button color="primary" class="search-btn">Buscar</button>
            </div>
          </mat-card-content>
        </mat-card>
      </div>

      <div class="recent-section">
        <h2 class="subsection-title">Accedidos Recientemente</h2>
        
        <div class="history-grid">
          @for (entry of recentHistory(); track entry.id) {
            <mat-card class="history-card" matRipple>
              <div class="card-content">
                <div class="patient-avatar">
                   {{ entry.paciente.charAt(0) }}
                </div>
                <div class="patient-info">
                  <div class="patient-name">{{ entry.paciente }}</div>
                  <div class="last-updated">
                    <mat-icon class="small-icon">history</mat-icon>
                    {{ entry.ultimoRegistro }}
                  </div>
                  @if (entry.diagnostico) {
                    <div class="diagnosis-chip">{{ entry.diagnostico }}</div>
                  }
                </div>
                <button mat-icon-button class="action-btn">
                  <mat-icon>arrow_forward</mat-icon>
                </button>
              </div>
            </mat-card>
          }
        </div>
      </div>
    </div>
  `,
  styles: [`
    .page-container {
      max-width: 1000px;
      margin: 0 auto;
      padding-bottom: 40px;
    }

    .search-section {
      text-align: center;
      padding: 40px 0;
      
      .section-title {
        font-size: 2rem;
        font-weight: 700;
        color: #1e293b;
        margin: 0 0 8px;
      }
      
      .section-desc {
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 32px;
      }
    }

    .search-card {
      max-width: 700px;
      margin: 0 auto;
      border-radius: 16px;
      
      .search-box {
        display: flex;
        align-items: center;
        padding: 8px;
        
        .search-icon {
          color: #94a3b8;
          margin-left: 8px;
        }
        
        .search-input {
          flex: 1;
          border: none;
          outline: none;
          font-size: 1.1rem;
          padding: 12px 16px;
          color: #0f172a;
          
          &::placeholder { color: #cbd5e1; }
        }
        
        .search-btn {
          border-radius: 12px;
          height: 48px;
          padding: 0 32px;
        }
      }
    }

    .recent-section {
      margin-top: 32px;
      
      .subsection-title {
        font-size: 1.25rem;
        color: #334155;
        margin-bottom: 24px;
        padding-left: 8px;
      }
    }

    .history-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 16px;
      
      @media (min-width: 768px) {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    .history-card {
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
      
      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
      }
      
      .card-content {
        padding: 16px;
        display: flex;
        align-items: flex-start;
        gap: 16px;
      }
      
      .patient-avatar {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        background-color: #f1f5f9;
        color: #475569;
        font-size: 1.25rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      
      .patient-info {
        flex: 1;
        
        .patient-name {
          font-weight: 600;
          color: #0f172a;
          font-size: 1.1rem;
          margin-bottom: 4px;
        }
        
        .last-updated {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 0.85rem;
          color: #64748b;
          margin-bottom: 8px;
          
          .small-icon { font-size: 16px; width: 16px; height: 16px; }
        }
        
        .diagnosis-chip {
          display: inline-block;
          padding: 2px 8px;
          background-color: #f0fdf4;
          color: #166534;
          border-radius: 4px;
          font-size: 0.75rem;
          font-weight: 500;
        }
      }
      
      .action-btn {
        color: #cbd5e1;
      }
    }
  `]
})
export class HistorialComponent {
  recentHistory = signal<HistorialEntry[]>([
    {
      id: '101',
      paciente: 'María González',
      ultimoRegistro: 'Editado hace 2 horas',
      diagnostico: 'Ansiedad Generalizada'
    },
    {
      id: '102',
      paciente: 'Pedro Martínez',
      ultimoRegistro: 'Editado ayer',
      diagnostico: 'Hipertensión'
    },
    {
      id: '103',
      paciente: 'Lucía Campos',
      ultimoRegistro: 'Editado hace 3 días',
      diagnostico: 'Seguimiento Nutricional'
    }
  ]);
}
