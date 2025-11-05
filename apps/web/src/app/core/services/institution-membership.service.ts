import { Injectable, inject } from '@angular/core';
import { from, Observable, throwError } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { SupabaseClientService } from '../../auth/services/supabase-client.service';
import {
  InstitutionMembership,
  MembershipStatus,
  CreateMembershipDto,
  UpdateMembershipDto,
} from '../models/institution-membership.interface';

/**
 * Servicio para gestión de membresías institucionales
 * Interactúa con la tabla public.institution_memberships de Supabase
 */
@Injectable({
  providedIn: 'root',
})
export class InstitutionMembershipService {
  private readonly supabase = inject(SupabaseClientService);

  /**
   * Obtiene todas las membresías activas de un usuario
   * Incluye datos de institución mediante join
   */
  getUserMemberships(userId: number): Observable<InstitutionMembership[]> {
    const queryPromise = this.supabase.getClient().then(client =>
      client
        .from('institution_memberships')
        .select(
          `
          *,
          institution:institutions(*)
        `
        )
        .eq('user_id', userId)
        .eq('status', MembershipStatus.ACTIVE)
        .is('ended_at', null)
        .order('is_primary', { ascending: false })
        .order('started_at', { ascending: false })
    );

    return from(queryPromise).pipe(
      map((response) => {
        if (response.error) {
          throw new Error(response.error.message);
        }
        return (response.data || []) as InstitutionMembership[];
      }),
      catchError((error) => {
        console.error('Error fetching user memberships:', error);
        return throwError(() => new Error('Failed to fetch user memberships'));
      })
    );
  }

  /**
   * Obtiene una membresía específica por ID
   */
  getMembershipById(membershipId: number): Observable<InstitutionMembership | null> {
    const queryPromise = this.supabase.getClient().then(client =>
      client
        .from('institution_memberships')
        .select(
          `
          *,
          institution:institutions(*)
        `
        )
        .eq('id', membershipId)
        .single()
    );

    return from(queryPromise).pipe(
      map((response) => {
        if (response.error) {
          if (response.error.code === 'PGRST116') {
            // No rows returned
            return null;
          }
          throw new Error(response.error.message);
        }
        return response.data as InstitutionMembership;
      }),
      catchError((error) => {
        console.error('Error fetching membership by ID:', error);
        return throwError(() => new Error('Failed to fetch membership'));
      })
    );
  }

  /**
   * Obtiene la membresía primaria de un usuario
   */
  getPrimaryMembership(userId: number): Observable<InstitutionMembership | null> {
    const queryPromise = this.supabase.getClient().then(client =>
      client
        .from('institution_memberships')
        .select(
          `
          *,
          institution:institutions(*)
        `
        )
        .eq('user_id', userId)
        .eq('is_primary', true)
        .eq('status', MembershipStatus.ACTIVE)
        .is('ended_at', null)
        .maybeSingle()
    );

    return from(queryPromise).pipe(
      map((response) => {
        if (response.error) {
          throw new Error(response.error.message);
        }
        return (response.data as InstitutionMembership) || null;
      }),
      catchError((error) => {
        console.error('Error fetching primary membership:', error);
        return throwError(() => new Error('Failed to fetch primary membership'));
      })
    );
  }

  /**
   * Obtiene todas las membresías de una institución
   */
  getInstitutionMemberships(institutionId: number): Observable<InstitutionMembership[]> {
    const queryPromise = this.supabase.getClient().then(client =>
      client
        .from('institution_memberships')
        .select('*')
        .eq('institution_id', institutionId)
        .eq('status', MembershipStatus.ACTIVE)
        .is('ended_at', null)
        .order('started_at', { ascending: false })
    );

    return from(queryPromise).pipe(
      map((response) => {
        if (response.error) {
          throw new Error(response.error.message);
        }
        return (response.data || []) as InstitutionMembership[];
      }),
      catchError((error) => {
        console.error('Error fetching institution memberships:', error);
        return throwError(() => new Error('Failed to fetch institution memberships'));
      })
    );
  }

  /**
   * Crea una nueva membresía
   */
  createMembership(dto: CreateMembershipDto): Observable<InstitutionMembership> {
    const queryPromise = this.supabase.getClient().then(client =>
      client
        .from('institution_memberships')
        .insert({
          institution_id: dto.institution_id,
          user_id: dto.user_id,
          role_institution: dto.role_institution,
          is_primary: dto.is_primary ?? false,
          status: dto.status ?? MembershipStatus.ACTIVE,
          started_at: dto.started_at ?? new Date().toISOString(),
        })
        .select(
          `
          *,
          institution:institutions(*)
        `
        )
        .single()
    );

    return from(queryPromise).pipe(
      map((response) => {
        if (response.error) {
          throw new Error(response.error.message);
        }
        return response.data as InstitutionMembership;
      }),
      catchError((error) => {
        console.error('Error creating membership:', error);
        return throwError(() => new Error('Failed to create membership'));
      })
    );
  }

  /**
   * Actualiza una membresía existente
   */
  updateMembership(dto: UpdateMembershipDto): Observable<InstitutionMembership> {
    const { id, ...updates } = dto;

    const queryPromise = this.supabase.getClient().then(client =>
      client
        .from('institution_memberships')
        .update({
          ...updates,
          updated_at: new Date().toISOString(),
        })
        .eq('id', id)
        .select(
          `
          *,
          institution:institutions(*)
        `
        )
        .single()
    );

    return from(queryPromise).pipe(
      map((response) => {
        if (response.error) {
          throw new Error(response.error.message);
        }
        return response.data as InstitutionMembership;
      }),
      catchError((error) => {
        console.error('Error updating membership:', error);
        return throwError(() => new Error('Failed to update membership'));
      })
    );
  }

  /**
   * Termina una membresía (soft delete)
   */
  endMembership(membershipId: number): Observable<void> {
    const queryPromise = this.supabase.getClient().then(client =>
      client
        .from('institution_memberships')
        .update({
          status: MembershipStatus.INACTIVE,
          ended_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        })
        .eq('id', membershipId)
    );

    return from(queryPromise).pipe(
      map((response) => {
        if (response.error) {
          throw new Error(response.error.message);
        }
      }),
      catchError((error) => {
        console.error('Error ending membership:', error);
        return throwError(() => new Error('Failed to end membership'));
      })
    );
  }

  /**
   * Establece una membresía como primaria
   * Desactiva cualquier otra membresía primaria del usuario
   */
  setPrimaryMembership(membershipId: number, userId: number): Observable<void> {
    const operationPromise = this.supabase.getClient().then(async client => {
      // Primero, desactivar todas las membresías primarias del usuario
      const deactivateResponse = await client
        .from('institution_memberships')
        .update({
          is_primary: false,
          updated_at: new Date().toISOString(),
        })
        .eq('user_id', userId)
        .eq('is_primary', true);

      if (deactivateResponse.error) {
        throw new Error(deactivateResponse.error.message);
      }

      // Luego, activar la nueva membresía primaria
      const activateResponse = await client
        .from('institution_memberships')
        .update({
          is_primary: true,
          updated_at: new Date().toISOString(),
        })
        .eq('id', membershipId);

      if (activateResponse.error) {
        throw new Error(activateResponse.error.message);
      }
    });

    return from(operationPromise).pipe(
      catchError((error) => {
        console.error('Error updating primary membership:', error);
        return throwError(() => new Error('Failed to update primary membership'));
      })
    );
  }
}
