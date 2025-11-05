import { Injectable, inject, signal } from '@angular/core';
import { SupabaseClientService } from '../../../auth/services/supabase-client.service';
import {
  CareRelationship,
  CareRelationshipWithPatient,
  PatientsSummary,
  PatientInfo,
} from '../models/care-relationship.model';

@Injectable({
  providedIn: 'root',
})
export class CareRelationshipService {
  private readonly supabaseClient = inject(SupabaseClientService);

  // Estado reactivo para pacientes
  private readonly _patients = signal<CareRelationshipWithPatient[]>([]);
  readonly patients = this._patients.asReadonly();

  private readonly _loading = signal(false);
  readonly loading = this._loading.asReadonly();

  private readonly _error = signal<string | null>(null);
  readonly error = this._error.asReadonly();

  /**
   * Obtiene todos los pacientes asignados al profesional actual
   */
  async loadMyPatients(): Promise<PatientsSummary> {
    this._loading.set(true);
    this._error.set(null);

    try {
      const client = await this.supabaseClient.getClient();

      // Obtener el usuario actual
      const {
        data: { user },
        error: userError,
      } = await client.auth.getUser();

      if (userError || !user) {
        throw new Error('Usuario no autenticado');
      }

      // Obtener el ID del usuario en app_users
      const { data: appUser, error: appUserError } = await client
        .from('app_users')
        .select('id')
        .eq('auth_user_id', user.id)
        .single();

      if (appUserError || !appUser) {
        throw new Error('No se encontró el perfil del usuario');
      }

      // Obtener las relaciones de cuidado con información del paciente
      const { data, error } = await client
        .from('care_relationships')
        .select(
          `
          *,
          patient:app_users!patient_user_id (
            id,
            email,
            full_name,
            age,
            gender,
            phone_number,
            role_global
          )
        `
        )
        .eq('professional_user_id', appUser.id)
        .order('started_at', { ascending: false });

      if (error) {
        throw error;
      }

      const relationships = (data || []) as CareRelationshipWithPatient[];
      this._patients.set(relationships);

      // Calcular resumen
      const summary: PatientsSummary = {
        total: relationships.length,
        active: relationships.filter((r) => r.status === 'active').length,
        inactive: relationships.filter((r) => r.status !== 'active').length,
        patients: relationships,
      };

      return summary;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Error al cargar pacientes';
      this._error.set(errorMessage);
      throw err;
    } finally {
      this._loading.set(false);
    }
  }

  /**
   * Obtiene un paciente específico por su ID de relación
   */
  async getPatientRelationship(
    relationshipId: number
  ): Promise<CareRelationshipWithPatient | null> {
    try {
      const client = await this.supabaseClient.getClient();

      const { data, error } = await client
        .from('care_relationships')
        .select(
          `
          *,
          patient:app_users!patient_user_id (
            id,
            email,
            full_name,
            age,
            gender,
            phone_number,
            role_global
          )
        `
        )
        .eq('id', relationshipId)
        .single();

      if (error) {
        throw error;
      }

      return data as CareRelationshipWithPatient;
    } catch (err) {
      console.error('Error al obtener relación de paciente:', err);
      return null;
    }
  }

  /**
   * Finaliza una relación de cuidado
   */
  async endRelationship(relationshipId: number): Promise<void> {
    try {
      const client = await this.supabaseClient.getClient();

      const { error } = await client
        .from('care_relationships')
        .update({
          status: 'ended',
          ended_at: new Date().toISOString(),
        })
        .eq('id', relationshipId);

      if (error) {
        throw error;
      }

      // Recargar la lista de pacientes
      await this.loadMyPatients();
    } catch (err) {
      console.error('Error al finalizar relación:', err);
      throw err;
    }
  }

  /**
   * Obtiene el conteo de pacientes activos
   */
  async getActivePatientsCount(): Promise<number> {
    try {
      const summary = await this.loadMyPatients();
      return summary.active;
    } catch (err) {
      console.error('Error al obtener conteo de pacientes:', err);
      return 0;
    }
  }

  /**
   * Busca usuarios disponibles para asignar como pacientes
   */
  async searchAvailableUsers(query: string): Promise<PatientInfo[]> {
    try {
      const client = await this.supabaseClient.getClient();

      // Obtener usuarios que NO son ProfesionalSalud y que coincidan con la búsqueda
      const { data, error } = await client
        .from('app_users')
        .select('id, email, full_name, age, gender, phone_number, role_global')
        .neq('role_global', 'ProfesionalSalud')
        .or(`full_name.ilike.%${query}%,email.ilike.%${query}%`)
        .limit(10);

      if (error) {
        throw error;
      }

      return (data || []) as PatientInfo[];
    } catch (err) {
      console.error('Error al buscar usuarios:', err);
      return [];
    }
  }

  /**
   * Crea una nueva relación de cuidado con un paciente
   */
  async assignPatient(
    patientUserId: number,
    contextType: 'independent' | 'institutional',
    notes?: string
  ): Promise<void> {
    try {
      const client = await this.supabaseClient.getClient();

      // Obtener el usuario actual
      const {
        data: { user },
        error: userError,
      } = await client.auth.getUser();

      if (userError || !user) {
        throw new Error('Usuario no autenticado');
      }

      // Obtener el ID del profesional en app_users
      const { data: appUser, error: appUserError } = await client
        .from('app_users')
        .select('id')
        .eq('auth_user_id', user.id)
        .single();

      if (appUserError || !appUser) {
        throw new Error('No se encontró el perfil del profesional');
      }

      // Crear la relación
      const { error: insertError } = await client
        .from('care_relationships')
        .insert({
          professional_user_id: appUser.id,
          patient_user_id: patientUserId,
          context_type: contextType,
          status: 'active',
          notes: notes || null,
        });

      if (insertError) {
        throw insertError;
      }

      // Recargar la lista de pacientes
      await this.loadMyPatients();
    } catch (err) {
      console.error('Error al asignar paciente:', err);
      throw err;
    }
  }
}
