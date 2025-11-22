import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatChipsModule } from '@angular/material/chips';
import { MatMenuModule } from '@angular/material/menu';

interface MealSlot {
  type: 'Desayuno' | 'Almuerzo' | 'Cena' | 'Snack';
  items: string[];
  calories: number;
}

interface DailyPlan {
  day: string;
  meals: MealSlot[];
}

@Component({
  selector: 'app-meal-planner',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatTabsModule,
    MatChipsModule,
    MatMenuModule
  ],
  template: `
    <div class="planner-container">
      <header class="planner-header">
        <div>
          <h1>Planificador Nutricional</h1>
          <p>Diseña planes de alimentación semanales personalizados</p>
        </div>
        <div class="header-actions">
          <button mat-stroked-button>
            <mat-icon>save</mat-icon>
            Guardar Plantilla
          </button>
          <button mat-flat-button color="primary">
            <mat-icon>send</mat-icon>
            Asignar a Paciente
          </button>
        </div>
      </header>

      <div class="macros-summary">
        <mat-card class="macro-card calories">
          <div class="macro-value">1,850</div>
          <div class="macro-label">Kcal / día</div>
        </mat-card>
        <mat-card class="macro-card protein">
          <div class="macro-value">140g</div>
          <div class="macro-label">Proteína</div>
        </mat-card>
        <mat-card class="macro-card carbs">
          <div class="macro-value">210g</div>
          <div class="macro-label">Carbos</div>
        </mat-card>
        <mat-card class="macro-card fats">
          <div class="macro-value">65g</div>
          <div class="macro-label">Grasas</div>
        </mat-card>
      </div>

      <mat-tab-group class="week-tabs" animationDuration="0ms">
        @for (plan of weeklyPlan(); track plan.day) {
          <mat-tab [label]="plan.day">
            <div class="day-view">
              @for (meal of plan.meals; track meal.type) {
                <mat-card class="meal-card">
                  <div class="meal-header">
                    <div class="meal-title">
                      <mat-icon class="meal-icon">
                        {{ getIconForMeal(meal.type) }}
                      </mat-icon>
                      <span>{{ meal.type }}</span>
                    </div>
                    <span class="meal-cals">{{ meal.calories }} kcal</span>
                  </div>
                  
                  <div class="meal-items">
                    @for (item of meal.items; track item) {
                      <div class="food-item">
                        <span>{{ item }}</span>
                        <button mat-icon-button class="remove-btn">
                          <mat-icon>close</mat-icon>
                        </button>
                      </div>
                    }
                    <button class="add-item-btn">
                      <mat-icon>add</mat-icon> Agregar alimento
                    </button>
                  </div>
                </mat-card>
              }
            </div>
          </mat-tab>
        }
      </mat-tab-group>
    </div>
  `,
  styles: [`
    .planner-container {
      display: flex;
      flex-direction: column;
      gap: 24px;
      padding-bottom: 40px;
    }

    .planner-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      h1 { margin: 0; font-size: 1.75rem; color: #1e293b; }
      p { margin: 4px 0 0; color: #64748b; }
      
      .header-actions {
        display: flex;
        gap: 12px;
      }
    }

    .macros-summary {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      
      .macro-card {
        padding: 16px;
        text-align: center;
        
        .macro-value { font-size: 1.5rem; font-weight: 700; }
        .macro-label { font-size: 0.8rem; text-transform: uppercase; opacity: 0.7; margin-top: 4px; }
        
        &.calories { background: #fdf4ff; color: #86198f; }
        &.protein { background: #eff6ff; color: #1e40af; }
        &.carbs { background: #f0fdf4; color: #166534; }
        &.fats { background: #fff7ed; color: #9a3412; }
      }
    }

    .day-view {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 20px;
      padding-top: 24px;
    }

    .meal-card {
      height: 100%;
      
      .meal-header {
        padding: 16px;
        background: #f8fafc;
        border-bottom: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        .meal-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 600;
          color: #334155;
        }
        
        .meal-cals {
          font-size: 0.8rem;
          font-weight: 600;
          color: #64748b;
          background: #e2e8f0;
          padding: 2px 8px;
          border-radius: 12px;
        }
      }
      
      .meal-items {
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        
        .food-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px;
          background: #fff;
          border: 1px solid #f1f5f9;
          border-radius: 8px;
          font-size: 0.9rem;
          
          .remove-btn {
            width: 24px;
            height: 24px;
            line-height: 24px;
            font-size: 16px;
            color: #cbd5e1;
            
            mat-icon { font-size: 16px; width: 16px; height: 16px; }
            
            &:hover { color: #ef4444; }
          }
        }
        
        .add-item-btn {
          margin-top: 8px;
          background: none;
          border: 1px dashed #cbd5e1;
          color: #64748b;
          padding: 8px;
          border-radius: 8px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          font-size: 0.9rem;
          transition: all 0.2s;
          
          &:hover {
            border-color: #ac4fc6;
            color: #ac4fc6;
            background: #fdf4ff;
          }
          
          mat-icon { font-size: 18px; width: 18px; height: 18px; }
        }
      }
    }
  `]
})
export class MealPlannerComponent {
  weeklyPlan = signal<DailyPlan[]>([
    {
      day: 'Lunes',
      meals: [
        { type: 'Desayuno', calories: 450, items: ['Avena con frutos rojos', '2 Huevos cocidos', 'Café negro'] },
        { type: 'Snack', calories: 150, items: ['Manzana verde', '10 Almendras'] },
        { type: 'Almuerzo', calories: 650, items: ['Pechuga de pollo a la plancha', 'Quinoa (1 taza)', 'Ensalada verde'] },
        { type: 'Cena', calories: 400, items: ['Pescado blanco al horno', 'Espárragos salteados'] }
      ]
    },
    { day: 'Martes', meals: [{ type: 'Desayuno', calories: 0, items: [] }, { type: 'Almuerzo', calories: 0, items: [] }, { type: 'Cena', calories: 0, items: [] }] },
    { day: 'Miércoles', meals: [{ type: 'Desayuno', calories: 0, items: [] }, { type: 'Almuerzo', calories: 0, items: [] }, { type: 'Cena', calories: 0, items: [] }] },
    { day: 'Jueves', meals: [{ type: 'Desayuno', calories: 0, items: [] }, { type: 'Almuerzo', calories: 0, items: [] }, { type: 'Cena', calories: 0, items: [] }] },
    { day: 'Viernes', meals: [{ type: 'Desayuno', calories: 0, items: [] }, { type: 'Almuerzo', calories: 0, items: [] }, { type: 'Cena', calories: 0, items: [] }] }
  ]);

  getIconForMeal(type: string): string {
    switch (type) {
      case 'Desayuno': return 'bakery_dining';
      case 'Almuerzo': return 'restaurant';
      case 'Snack': return 'nutrition';
      case 'Cena': return 'nightlight';
      default: return 'restaurant';
    }
  }
}
