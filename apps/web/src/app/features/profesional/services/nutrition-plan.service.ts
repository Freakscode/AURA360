import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { AuthSessionStore } from '../../auth/services/auth-session.store';
import { NutritionPlan } from '../models/nutrition-plan.model';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class NutritionPlanService {
  private readonly http = inject(HttpClient);
  private readonly authStore = inject(AuthSessionStore);
  
  // Base URL for the API
  private readonly API_URL = `${environment.apiBaseUrl}/body/nutrition-plans/`;

  async getPlans(userId: string): Promise<NutritionPlan[]> {
    let params = new HttpParams();
    if (userId) {
      params = params.set('user_id', userId);
    }
    
    try {
       const response = await firstValueFrom(
         this.http.get<any>(this.API_URL, { params })
       );
       if (response && response.results && Array.isArray(response.results)) {
          return response.results;
       }
       return Array.isArray(response) ? response : [];
    } catch (error) {
      console.error('Error fetching plans', error);
      throw error;
    }
  }

  async getActivePlan(userId: string): Promise<NutritionPlan | null> {
    let params = new HttpParams()
      .set('active', 'true')
      .set('valid', 'true');

    if (userId) {
      params = params.set('user_id', userId);
    }

    try {
      const response = await firstValueFrom(
        this.http.get<any>(this.API_URL, { 
          params 
        })
      );
      const plans = (response && response.results && Array.isArray(response.results)) ? response.results : (Array.isArray(response) ? response : []);
      return plans[0] || null;
    } catch (error) {
      console.error('Error fetching active plan', error);
      return null;
    }
  }

  async createPlan(planData: Partial<NutritionPlan>): Promise<NutritionPlan> {
    return await firstValueFrom(
      this.http.post<NutritionPlan>(this.API_URL, planData)
    );
  }
  
  // Helper to generate a default plan structure
  generateDefaultPlan(
    patientId: string, 
    patientName: string, 
    title: string,
    goal: string,
    calories: number
  ): any {
    const today = new Date();
    const validUntil = new Date();
    validUntil.setMonth(today.getMonth() + 3);

    return {
      title: title,
      language: 'es',
      issued_at: today.toISOString().split('T')[0],
      valid_until: validUntil.toISOString().split('T')[0],
      is_active: true,
      plan_data: {
        plan: {
          title: title,
          version: '1.0',
          issued_at: today.toISOString().split('T')[0],
          valid_until: validUntil.toISOString().split('T')[0],
          language: 'es',
          units: { mass: 'kg', volume: 'ml', energy: 'kcal' },
          source: { kind: 'web' }
        },
        subject: {
          user_id: patientId, // UUID from Supabase
          name: patientName,
          demographics: { sex: 'M', age_years: 30, height_cm: 170, weight_kg: 70 } // Should come from patient profile
        },
        assessment: {
          goals: [
            { target: 'calories', value: calories, unit: 'kcal' },
            { target: 'goal', value: 0, unit: 'text', notes: goal }
          ]
        },
        directives: {
          meals: [], // Empty meals for now
          restrictions: []
        }
      }
    };
  }
}
