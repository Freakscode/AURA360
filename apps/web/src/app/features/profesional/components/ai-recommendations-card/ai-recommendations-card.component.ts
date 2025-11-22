import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  AIRecommendationsService,
  AIRecommendationsResponse,
  AIRecommendation
} from '../../services/ai-recommendations.service';
import { PapersService } from '../../services/papers.service';

@Component({
  selector: 'app-ai-recommendations-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="recommendations-card">
      <!-- Header -->
      <div class="recommendations-header">
        <h3 class="recommendations-title">
          <span class="icon">🤖</span>
          Recomendaciones con IA
        </h3>
        <button
          class="generate-btn"
          (click)="generateRecommendations()"
          [disabled]="loading">
          <span class="icon">{{ loading ? '⏳' : '✨' }}</span>
          {{ loading ? 'Generando...' : 'Generar Recomendaciones' }}
        </button>
      </div>

      <!-- Info Banner -->
      <div class="info-banner" *ngIf="!loading && !response">
        <span class="icon">💡</span>
        <p>
          Genera recomendaciones personalizadas basadas en tus tendencias de progreso,
          adherencia nutricional y mediciones actuales usando Inteligencia Artificial.
        </p>
      </div>

      <!-- Loading State -->
      <div *ngIf="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Analizando datos y generando recomendaciones...</p>
        <p class="loading-hint">Esto puede tardar 30-60 segundos</p>
      </div>

      <!-- Error State -->
      <div *ngIf="error && !loading" class="error-state">
        <span class="icon">⚠️</span>
        <p>{{ error }}</p>
        <button class="retry-btn" (click)="generateRecommendations()">Reintentar</button>
      </div>

      <!-- Content -->
      <div *ngIf="response && !loading && !error" class="recommendations-content">

        <!-- Meta Info -->
        <div class="meta-info">
          <div class="meta-item">
            <span class="icon">📅</span>
            <span>{{ aiService.formatGeneratedDate(response.generated_at) }}</span>
          </div>
          <div class="meta-item">
            <span class="icon">{{ aiService.isAIGenerated(response.model) ? '🤖' : '💻' }}</span>
            <span>{{ aiService.isAIGenerated(response.model) ? 'Gemini AI' : 'Sistema Local' }}</span>
          </div>
          <div class="meta-item">
            <span class="icon">📊</span>
            <span>{{ response.recommendations.length }} recomendaciones</span>
          </div>
        </div>

        <!-- Overall Assessment -->
        <div class="assessment-section" *ngIf="response.overall_assessment">
          <h4 class="section-title">
            <span class="icon">📋</span>
            Evaluación General
          </h4>
          <p class="assessment-text">{{ response.overall_assessment }}</p>
        </div>

        <!-- Key Focus Areas -->
        <div class="focus-areas" *ngIf="response.key_focus_areas.length > 0">
          <h4 class="section-title">
            <span class="icon">🎯</span>
            Áreas Clave de Enfoque
          </h4>
          <div class="focus-tags">
            <span class="focus-tag" *ngFor="let area of response.key_focus_areas">
              {{ area }}
            </span>
          </div>
        </div>

        <!-- Recommendations List -->
        <div class="recommendations-list">
          <div
            class="recommendation-card"
            *ngFor="let rec of sortedRecommendations; let i = index"
            [style.border-left-color]="aiService.getPriorityColor(rec.priority)">

            <!-- Recommendation Header -->
            <div class="rec-header">
              <div class="rec-number">{{ i + 1 }}</div>
              <div class="rec-title-wrapper">
                <div class="rec-title">
                  <span class="type-icon">{{ aiService.getTypeIcon(rec.type) }}</span>
                  {{ rec.title }}
                </div>
                <div class="rec-meta">
                  <span class="priority-badge" [style.color]="aiService.getPriorityColor(rec.priority)">
                    {{ aiService.getPriorityBadge(rec.priority) }} {{ aiService.getPriorityText(rec.priority) }}
                  </span>
                  <span class="type-badge">{{ getTypeText(rec.type) }}</span>
                </div>
              </div>
            </div>

            <!-- Recommendation Description -->
            <div class="rec-description">
              {{ rec.description }}
            </div>

            <!-- Rationale -->
            <div class="rec-rationale">
              <strong>Por qué:</strong> {{ rec.rationale }}
            </div>

            <!-- Action Steps -->
            <div class="rec-steps" *ngIf="rec.action_steps.length > 0">
              <strong class="steps-title">Pasos a seguir:</strong>
              <ol class="steps-list">
                <li *ngFor="let step of rec.action_steps">{{ step }}</li>
              </ol>
            </div>

            <!-- Scientific References -->
            <div class="rec-references" *ngIf="rec.references && rec.references.length > 0">
              <strong class="references-title">
                <span class="icon">📚</span>
                Referencias Científicas:
              </strong>
              <div class="references-list">
                <button
                  *ngFor="let refId of rec.references"
                  class="reference-btn"
                  (click)="openPaper(refId)"
                  title="Ver artículo científico">
                  <span class="icon">📄</span>
                  Ver artículo
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Data Sources Info -->
        <div class="data-sources">
          <p class="data-sources-text">
            <span class="icon">ℹ️</span>
            Basado en:
            <span *ngIf="response.source_data.has_trends"> tendencias de progreso,</span>
            <span *ngIf="response.source_data.has_adherence"> adherencia nutricional,</span>
            <span *ngIf="response.source_data.has_measurement"> mediciones actuales</span>
          </p>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .recommendations-card {
      background: white;
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .recommendations-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
    }

    .recommendations-title {
      font-size: 20px;
      font-weight: 600;
      color: #1f2937;
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
    }

    .generate-btn {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 24px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
      transition: all 0.3s;
      box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);
    }

    .generate-btn:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
    }

    .generate-btn:disabled {
      opacity: 0.7;
      cursor: not-allowed;
      transform: none;
    }

    .info-banner {
      display: flex;
      gap: 12px;
      padding: 16px;
      background: #eff6ff;
      border-left: 4px solid #3b82f6;
      border-radius: 8px;
      margin-bottom: 24px;
    }

    .info-banner p {
      margin: 0;
      font-size: 14px;
      color: #1e40af;
      line-height: 1.5;
    }

    .loading-state, .error-state {
      text-align: center;
      padding: 60px 20px;
      color: #6b7280;
    }

    .spinner {
      width: 50px;
      height: 50px;
      border: 5px solid #f3f4f6;
      border-top-color: #667eea;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin: 0 auto 20px;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .loading-hint {
      font-size: 12px;
      color: #9ca3af;
      margin-top: 8px;
    }

    .error-state {
      color: #ef4444;
    }

    .retry-btn {
      margin-top: 16px;
      padding: 10px 20px;
      background: #ef4444;
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 600;
    }

    .meta-info {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid #e5e7eb;
    }

    .meta-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      color: #6b7280;
    }

    .section-title {
      font-size: 16px;
      font-weight: 600;
      color: #1f2937;
      margin: 0 0 12px 0;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .assessment-section {
      margin-bottom: 24px;
    }

    .assessment-text {
      margin: 0;
      padding: 16px;
      background: #f0fdf4;
      border-radius: 8px;
      font-size: 15px;
      color: #166534;
      line-height: 1.6;
    }

    .focus-areas {
      margin-bottom: 32px;
    }

    .focus-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .focus-tag {
      padding: 8px 16px;
      background: #dbeafe;
      color: #1e40af;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 600;
    }

    .recommendations-list {
      display: flex;
      flex-direction: column;
      gap: 20px;
      margin-bottom: 24px;
    }

    .recommendation-card {
      padding: 20px;
      background: #fafafa;
      border-left: 4px solid;
      border-radius: 8px;
      transition: all 0.3s;
    }

    .recommendation-card:hover {
      background: #f5f5f5;
      transform: translateX(4px);
    }

    .rec-header {
      display: flex;
      gap: 16px;
      margin-bottom: 16px;
    }

    .rec-number {
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 16px;
      flex-shrink: 0;
    }

    .rec-title-wrapper {
      flex: 1;
    }

    .rec-title {
      font-size: 18px;
      font-weight: 600;
      color: #1f2937;
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .type-icon {
      font-size: 20px;
    }

    .rec-meta {
      display: flex;
      gap: 12px;
      font-size: 13px;
    }

    .priority-badge {
      font-weight: 600;
    }

    .type-badge {
      color: #6b7280;
      background: #e5e7eb;
      padding: 2px 10px;
      border-radius: 12px;
    }

    .rec-description {
      margin-bottom: 12px;
      font-size: 15px;
      color: #4b5563;
      line-height: 1.6;
    }

    .rec-rationale {
      margin-bottom: 16px;
      padding: 12px;
      background: #fff7ed;
      border-radius: 6px;
      font-size: 14px;
      color: #92400e;
    }

    .rec-steps {
      margin-top: 16px;
      padding: 16px;
      background: white;
      border-radius: 6px;
    }

    .steps-title {
      display: block;
      margin-bottom: 12px;
      color: #1f2937;
      font-size: 14px;
    }

    .steps-list {
      margin: 0;
      padding-left: 20px;
    }

    .steps-list li {
      margin-bottom: 8px;
      color: #4b5563;
      font-size: 14px;
      line-height: 1.5;
    }

    .steps-list li:last-child {
      margin-bottom: 0;
    }

    .data-sources {
      padding: 12px;
      background: #f9fafb;
      border-radius: 8px;
    }

    .data-sources-text {
      margin: 0;
      font-size: 12px;
      color: #6b7280;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .icon {
      font-size: 18px;
    }

    .rec-references {
      margin-top: 16px;
      padding: 16px;
      background: #f0f9ff;
      border-radius: 6px;
      border-left: 3px solid #3b82f6;
    }

    .references-title {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 12px;
      color: #1e40af;
      font-size: 14px;
    }

    .references-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .reference-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 16px;
      background: white;
      color: #1e40af;
      border: 1px solid #3b82f6;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }

    .reference-btn:hover {
      background: #3b82f6;
      color: white;
      transform: translateY(-1px);
      box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
    }

    .reference-btn .icon {
      font-size: 14px;
    }
  `]
})
export class AIRecommendationsCardComponent {
  @Input() userId?: string;

  response: AIRecommendationsResponse | null = null;
  loading = false;
  error: string | null = null;

  constructor(
    public aiService: AIRecommendationsService,
    private papersService: PapersService
  ) {}

  generateRecommendations() {
    this.loading = true;
    this.error = null;

    this.aiService.generateRecommendations(this.userId, true, true, 30, false).subscribe({
      next: (response) => {
        if (response.status === 'success') {
          this.response = response;
        } else {
          this.error = response.error || 'Error al generar recomendaciones';
        }
        this.loading = false;
      },
      error: (err) => {
        console.error('Error generating recommendations:', err);
        this.error = err.error?.detail || 'Error al generar recomendaciones';
        this.loading = false;
      }
    });
  }

  get sortedRecommendations(): AIRecommendation[] {
    if (!this.response) return [];
    return this.aiService.sortByPriority(this.response.recommendations);
  }

  getTypeText(type: string): string {
    const types: { [key: string]: string } = {
      'nutrition': 'Nutrición',
      'exercise': 'Ejercicio',
      'lifestyle': 'Estilo de Vida',
      'medical': 'Médico',
      'motivational': 'Motivacional'
    };
    return types[type] || type;
  }

  /**
   * Abre un paper científico en una nueva pestaña.
   *
   * @param docId UUID del documento
   */
  openPaper(docId: string): void {
    this.papersService.openPaper(docId);
  }
}
