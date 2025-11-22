import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface AdherenceRates {
  overall: number;
  calories: number;
  protein: number;
  carbs: number;
  fats: number;
}

export interface AdherenceIssue {
  type: string;
  severity: string;
  description: string;
  recommendation: string;
}

export interface AdherenceTrends {
  improving: boolean | null;
  consistency_score: number;
}

export interface AdherenceAnalysis {
  period: {
    start: string;
    end: string;
    days: number;
  } | null;
  logs_count: number;
  coverage: number;
  adherence_rates: AdherenceRates;
  adherence_level: 'excellent' | 'good' | 'moderate' | 'poor' | 'insufficient_data';
  daily_analysis: any[];
  issues: AdherenceIssue[];
  trends: AdherenceTrends;
  summary: string;
}

export interface AdherenceResponse {
  user_id: string;
  plan_id: string;
  status: 'success' | 'failed';
  analysis: AdherenceAnalysis;
}

@Injectable({
  providedIn: 'root'
})
export class NutritionAdherenceService {
  private apiUrl = `${environment.apiUrl}/body/nutrition/adherence/`;

  constructor(private http: HttpClient) {}

  /**
   * Obtiene el análisis de adherencia nutricional del usuario.
   *
   * @param userId - ID del usuario a analizar (opcional, usa el usuario autenticado si no se proporciona)
   * @param planId - ID del plan nutricional (opcional, usa el plan activo si no se proporciona)
   * @param days - Número de días a analizar (default: 7)
   * @param async - Si true, retorna job_id para consultar después (default: false)
   * @returns Observable con el análisis de adherencia
   */
  getAdherence(
    userId?: string,
    planId?: string,
    days: number = 7,
    async: boolean = false
  ): Observable<AdherenceResponse> {
    let params = new HttpParams()
      .set('days', days.toString())
      .set('async', async.toString());

    if (userId) {
      params = params.set('user_id', userId);
    }

    if (planId) {
      params = params.set('plan_id', planId);
    }

    return this.http.get<AdherenceResponse>(this.apiUrl, { params });
  }

  /**
   * Obtiene el nivel de adherencia en formato legible.
   */
  getAdherenceLevelText(level: string): string {
    const levels: { [key: string]: string } = {
      'excellent': 'Excelente',
      'good': 'Buena',
      'moderate': 'Moderada',
      'poor': 'Pobre',
      'insufficient_data': 'Datos Insuficientes'
    };
    return levels[level] || level;
  }

  /**
   * Obtiene el color asociado al nivel de adherencia.
   */
  getAdherenceLevelColor(level: string): string {
    const colors: { [key: string]: string } = {
      'excellent': '#10b981', // green-500
      'good': '#3b82f6',      // blue-500
      'moderate': '#f59e0b',  // amber-500
      'poor': '#ef4444',      // red-500
      'insufficient_data': '#6b7280' // gray-500
    };
    return colors[level] || '#6b7280';
  }

  /**
   * Obtiene el icono del nivel de severidad de un issue.
   */
  getSeverityIcon(severity: string): string {
    const icons: { [key: string]: string } = {
      'high': '🔴',
      'medium': '🟡',
      'low': '🟢'
    };
    return icons[severity] || '⚪';
  }

  /**
   * Formatea el porcentaje de adherencia.
   */
  formatAdherenceRate(rate: number): string {
    return `${rate.toFixed(1)}%`;
  }

  /**
   * Determina si la adherencia es preocupante.
   */
  isAdherenceConcerning(level: string): boolean {
    return level === 'poor' || level === 'moderate';
  }

  /**
   * Obtiene el número de issues de alta prioridad.
   */
  getHighPriorityIssuesCount(issues: AdherenceIssue[]): number {
    return issues.filter(issue => issue.severity === 'high').length;
  }
}
