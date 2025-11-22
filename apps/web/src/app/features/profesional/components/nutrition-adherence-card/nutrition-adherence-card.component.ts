import { Component, Input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  NutritionAdherenceService,
  AdherenceResponse,
  AdherenceAnalysis,
  AdherenceIssue
} from '../../services/nutrition-adherence.service';

@Component({
  selector: 'app-nutrition-adherence-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="adherence-card">
      <!-- Header -->
      <div class="adherence-header">
        <h3 class="adherence-title">
          <span class="icon">🍽️</span>
          Adherencia Nutricional
        </h3>
        <button
          class="refresh-btn"
          (click)="loadAdherence()"
          [disabled]="loading">
          <span class="icon">{{ loading ? '⏳' : '🔄' }}</span>
          Actualizar
        </button>
      </div>

      <!-- Loading State -->
      <div *ngIf="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Analizando adherencia...</p>
      </div>

      <!-- Error State -->
      <div *ngIf="error && !loading" class="error-state">
        <span class="icon">⚠️</span>
        <p>{{ error }}</p>
        <button class="retry-btn" (click)="loadAdherence()">Reintentar</button>
      </div>

      <!-- Content -->
      <div *ngIf="analysis && !loading && !error" class="adherence-content">

        <!-- Overall Score -->
        <div class="overall-score">
          <div class="score-circle" [style.border-color]="getLevelColor()">
            <div class="score-value">{{ analysis.adherence_rates.overall.toFixed(0) }}%</div>
            <div class="score-label">{{ getLevelText() }}</div>
          </div>

          <div class="score-details">
            <div class="score-detail">
              <span class="icon">📊</span>
              <span>{{ analysis.logs_count }} registros</span>
            </div>
            <div class="score-detail">
              <span class="icon">📅</span>
              <span>{{ analysis.coverage.toFixed(0) }}% cobertura</span>
            </div>
            <div class="score-detail" *ngIf="analysis.period">
              <span class="icon">⏱️</span>
              <span>{{ analysis.period.days }} días</span>
            </div>
          </div>
        </div>

        <!-- Macronutrients Breakdown -->
        <div class="macros-section">
          <h4 class="section-title">Cumplimiento por Macronutriente</h4>
          <div class="macros-grid">
            <div class="macro-card">
              <div class="macro-icon">🔥</div>
              <div class="macro-info">
                <div class="macro-name">Calorías</div>
                <div class="macro-value">{{ analysis.adherence_rates.calories.toFixed(1) }}%</div>
                <div class="macro-bar">
                  <div
                    class="macro-bar-fill"
                    [style.width.%]="analysis.adherence_rates.calories"
                    [style.background-color]="getBarColor(analysis.adherence_rates.calories)">
                  </div>
                </div>
              </div>
            </div>

            <div class="macro-card">
              <div class="macro-icon">🥩</div>
              <div class="macro-info">
                <div class="macro-name">Proteína</div>
                <div class="macro-value">{{ analysis.adherence_rates.protein.toFixed(1) }}%</div>
                <div class="macro-bar">
                  <div
                    class="macro-bar-fill"
                    [style.width.%]="analysis.adherence_rates.protein"
                    [style.background-color]="getBarColor(analysis.adherence_rates.protein)">
                  </div>
                </div>
              </div>
            </div>

            <div class="macro-card">
              <div class="macro-icon">🍞</div>
              <div class="macro-info">
                <div class="macro-name">Carbohidratos</div>
                <div class="macro-value">{{ analysis.adherence_rates.carbs.toFixed(1) }}%</div>
                <div class="macro-bar">
                  <div
                    class="macro-bar-fill"
                    [style.width.%]="analysis.adherence_rates.carbs"
                    [style.background-color]="getBarColor(analysis.adherence_rates.carbs)">
                  </div>
                </div>
              </div>
            </div>

            <div class="macro-card">
              <div class="macro-icon">🥑</div>
              <div class="macro-info">
                <div class="macro-name">Grasas</div>
                <div class="macro-value">{{ analysis.adherence_rates.fats.toFixed(1) }}%</div>
                <div class="macro-bar">
                  <div
                    class="macro-bar-fill"
                    [style.width.%]="analysis.adherence_rates.fats"
                    [style.background-color]="getBarColor(analysis.adherence_rates.fats)">
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Issues -->
        <div class="issues-section" *ngIf="analysis.issues.length > 0">
          <h4 class="section-title">
            <span class="icon">⚠️</span>
            Áreas de Mejora ({{ analysis.issues.length }})
          </h4>
          <div class="issues-list">
            <div class="issue-card" *ngFor="let issue of analysis.issues">
              <div class="issue-header">
                <span class="issue-icon">{{ adherenceService.getSeverityIcon(issue.severity) }}</span>
                <span class="issue-description">{{ issue.description }}</span>
              </div>
              <div class="issue-recommendation">
                <span class="icon">💡</span>
                {{ issue.recommendation }}
              </div>
            </div>
          </div>
        </div>

        <!-- Trends -->
        <div class="trends-section" *ngIf="analysis.trends">
          <h4 class="section-title">Tendencias</h4>
          <div class="trends-grid">
            <div class="trend-card" *ngIf="analysis.trends.improving !== null">
              <span class="trend-icon">{{ analysis.trends.improving ? '📈' : '📊' }}</span>
              <span class="trend-text">
                {{ analysis.trends.improving ? 'Mejorando' : 'Estable' }}
              </span>
            </div>
            <div class="trend-card">
              <span class="trend-icon">🎯</span>
              <span class="trend-text">
                Consistencia: {{ analysis.trends.consistency_score.toFixed(0) }}%
              </span>
            </div>
          </div>
        </div>

        <!-- Summary -->
        <div class="summary-section">
          <p class="summary-text">{{ analysis.summary }}</p>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .adherence-card {
      background: white;
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .adherence-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
    }

    .adherence-title {
      font-size: 20px;
      font-weight: 600;
      color: #1f2937;
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
    }

    .refresh-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 16px;
      background: #f3f4f6;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-size: 14px;
      transition: all 0.2s;
    }

    .refresh-btn:hover:not(:disabled) {
      background: #e5e7eb;
    }

    .refresh-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .loading-state, .error-state {
      text-align: center;
      padding: 40px 20px;
      color: #6b7280;
    }

    .spinner {
      width: 40px;
      height: 40px;
      border: 4px solid #f3f4f6;
      border-top-color: #3b82f6;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin: 0 auto 16px;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .error-state {
      color: #ef4444;
    }

    .retry-btn {
      margin-top: 12px;
      padding: 8px 16px;
      background: #ef4444;
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
    }

    .overall-score {
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 24px;
      align-items: center;
      margin-bottom: 32px;
      padding-bottom: 24px;
      border-bottom: 1px solid #e5e7eb;
    }

    .score-circle {
      width: 120px;
      height: 120px;
      border: 8px solid;
      border-radius: 50%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }

    .score-value {
      font-size: 32px;
      font-weight: 700;
      color: #1f2937;
    }

    .score-label {
      font-size: 12px;
      color: #6b7280;
      text-transform: uppercase;
      font-weight: 600;
    }

    .score-details {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .score-detail {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      color: #4b5563;
    }

    .section-title {
      font-size: 16px;
      font-weight: 600;
      color: #1f2937;
      margin: 0 0 16px 0;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .macros-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }

    .macro-card {
      display: flex;
      gap: 12px;
      padding: 16px;
      background: #f9fafb;
      border-radius: 8px;
    }

    .macro-icon {
      font-size: 32px;
    }

    .macro-info {
      flex: 1;
    }

    .macro-name {
      font-size: 13px;
      color: #6b7280;
      margin-bottom: 4px;
    }

    .macro-value {
      font-size: 20px;
      font-weight: 700;
      color: #1f2937;
      margin-bottom: 8px;
    }

    .macro-bar {
      height: 6px;
      background: #e5e7eb;
      border-radius: 3px;
      overflow: hidden;
    }

    .macro-bar-fill {
      height: 100%;
      transition: width 0.3s ease;
    }

    .issues-section {
      margin-bottom: 32px;
    }

    .issues-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .issue-card {
      padding: 16px;
      background: #fef3c7;
      border-left: 4px solid #f59e0b;
      border-radius: 8px;
    }

    .issue-header {
      display: flex;
      gap: 8px;
      align-items: start;
      font-weight: 600;
      color: #92400e;
      margin-bottom: 8px;
    }

    .issue-recommendation {
      display: flex;
      gap: 8px;
      font-size: 14px;
      color: #78350f;
    }

    .trends-section {
      margin-bottom: 24px;
    }

    .trends-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
    }

    .trend-card {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px;
      background: #f0fdf4;
      border-radius: 8px;
    }

    .trend-icon {
      font-size: 24px;
    }

    .trend-text {
      font-size: 14px;
      font-weight: 600;
      color: #166534;
    }

    .summary-section {
      padding: 16px;
      background: #f9fafb;
      border-radius: 8px;
    }

    .summary-text {
      margin: 0;
      font-size: 14px;
      color: #4b5563;
      line-height: 1.6;
    }

    .icon {
      font-size: 18px;
    }
  `]
})
export class NutritionAdherenceCardComponent implements OnInit {
  @Input() userId?: string;
  @Input() planId?: string;
  @Input() days: number = 7;

  analysis: AdherenceAnalysis | null = null;
  loading = false;
  error: string | null = null;

  constructor(public adherenceService: NutritionAdherenceService) {}

  ngOnInit() {
    this.loadAdherence();
  }

  loadAdherence() {
    this.loading = true;
    this.error = null;

    this.adherenceService.getAdherence(this.userId, this.planId, this.days).subscribe({
      next: (response) => {
        this.analysis = response.analysis;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading adherence:', err);
        this.error = err.error?.detail || 'Error al cargar adherencia';
        this.loading = false;
      }
    });
  }

  getLevelText(): string {
    if (!this.analysis) return '';
    return this.adherenceService.getAdherenceLevelText(this.analysis.adherence_level);
  }

  getLevelColor(): string {
    if (!this.analysis) return '#6b7280';
    return this.adherenceService.getAdherenceLevelColor(this.analysis.adherence_level);
  }

  getBarColor(rate: number): string {
    if (rate >= 90) return '#10b981';  // green
    if (rate >= 75) return '#3b82f6';  // blue
    if (rate >= 60) return '#f59e0b';  // amber
    return '#ef4444';  // red
  }
}
