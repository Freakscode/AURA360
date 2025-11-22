import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface AIRecommendation {
  type: 'nutrition' | 'exercise' | 'lifestyle' | 'medical' | 'motivational';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  rationale: string;
  action_steps: string[];
  references?: string[];  // Lista de doc_ids de papers científicos
}

export interface AIRecommendationsResponse {
  user_id: string;
  generated_at: string;
  model: string;
  recommendations: AIRecommendation[];
  overall_assessment: string;
  key_focus_areas: string[];
  source_data: {
    has_trends: boolean;
    has_adherence: boolean;
    has_measurement: boolean;
  };
  status: 'success' | 'failed';
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AIRecommendationsService {
  private apiUrl = `${environment.apiUrl}/body/recommendations/ai/`;

  constructor(private http: HttpClient) {}

  /**
   * Genera recomendaciones personalizadas usando IA.
   *
   * @param userId - ID del usuario a analizar (opcional, usa el usuario autenticado si no se proporciona)
   * @param includeTrends - Incluir análisis de tendencias (default: true)
   * @param includeAdherence - Incluir análisis de adherencia (default: true)
   * @param days - Días de historia a considerar (default: 30)
   * @param async - Si true, retorna job_id para consultar después (default: false)
   * @returns Observable con las recomendaciones generadas
   */
  generateRecommendations(
    userId?: string,
    includeTrends: boolean = true,
    includeAdherence: boolean = true,
    days: number = 30,
    async: boolean = false
  ): Observable<AIRecommendationsResponse> {
    let params = new HttpParams()
      .set('include_trends', includeTrends.toString())
      .set('include_adherence', includeAdherence.toString())
      .set('days', days.toString())
      .set('async', async.toString());

    if (userId) {
      params = params.set('user_id', userId);
    }

    return this.http.get<AIRecommendationsResponse>(this.apiUrl, { params });
  }

  /**
   * Obtiene el icono del tipo de recomendación.
   */
  getTypeIcon(type: string): string {
    const icons: { [key: string]: string } = {
      'nutrition': '🍽️',
      'exercise': '💪',
      'lifestyle': '🧘',
      'medical': '⚕️',
      'motivational': '🎯'
    };
    return icons[type] || '📌';
  }

  /**
   * Obtiene el color de la prioridad.
   */
  getPriorityColor(priority: string): string {
    const colors: { [key: string]: string } = {
      'high': '#ef4444',      // red-500
      'medium': '#f59e0b',    // amber-500
      'low': '#10b981'        // green-500
    };
    return colors[priority] || '#6b7280';
  }

  /**
   * Obtiene el texto de la prioridad.
   */
  getPriorityText(priority: string): string {
    const texts: { [key: string]: string } = {
      'high': 'Alta',
      'medium': 'Media',
      'low': 'Baja'
    };
    return texts[priority] || priority;
  }

  /**
   * Obtiene el badge de prioridad (emoji).
   */
  getPriorityBadge(priority: string): string {
    const badges: { [key: string]: string } = {
      'high': '🔴',
      'medium': '🟡',
      'low': '🟢'
    };
    return badges[priority] || '⚪';
  }

  /**
   * Filtra recomendaciones por tipo.
   */
  filterByType(recommendations: AIRecommendation[], type: string): AIRecommendation[] {
    return recommendations.filter(rec => rec.type === type);
  }

  /**
   * Filtra recomendaciones por prioridad.
   */
  filterByPriority(recommendations: AIRecommendation[], priority: string): AIRecommendation[] {
    return recommendations.filter(rec => rec.priority === priority);
  }

  /**
   * Ordena recomendaciones por prioridad (alta primero).
   */
  sortByPriority(recommendations: AIRecommendation[]): AIRecommendation[] {
    const priorityOrder: { [key: string]: number } = {
      'high': 1,
      'medium': 2,
      'low': 3
    };

    return [...recommendations].sort((a, b) => {
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    });
  }

  /**
   * Obtiene estadísticas de las recomendaciones.
   */
  getStats(recommendations: AIRecommendation[]): {
    total: number;
    byPriority: { [key: string]: number };
    byType: { [key: string]: number };
  } {
    const stats = {
      total: recommendations.length,
      byPriority: {
        high: 0,
        medium: 0,
        low: 0
      },
      byType: {
        nutrition: 0,
        exercise: 0,
        lifestyle: 0,
        medical: 0,
        motivational: 0
      }
    };

    recommendations.forEach(rec => {
      stats.byPriority[rec.priority] = (stats.byPriority[rec.priority] || 0) + 1;
      stats.byType[rec.type] = (stats.byType[rec.type] || 0) + 1;
    });

    return stats;
  }

  /**
   * Formatea la fecha de generación.
   */
  formatGeneratedDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  /**
   * Verifica si la respuesta fue generada por IA o fallback.
   */
  isAIGenerated(model: string): boolean {
    return model !== 'fallback' && model.includes('gemini');
  }
}
