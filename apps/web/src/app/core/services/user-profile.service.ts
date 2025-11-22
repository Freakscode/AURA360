import { Injectable, inject } from '@angular/core';
import { from, Observable, throwError } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { SupabaseClientService } from '../../auth/services/supabase-client.service';
import {
  UserProfile,
  CreateUserProfileDto,
  UpdateUserProfileDto,
} from '../models/user-profile.interface';

/**
 * Servicio para gestión de perfiles de usuario
 * Interactúa con la tabla public.app_users de Supabase
 */
@Injectable({
  providedIn: 'root',
})
export class UserProfileService {
  private readonly supabase = inject(SupabaseClientService);

  /**
   * Obtiene el perfil de usuario por auth_user_id
   */
  getProfileByAuthId(authUserId: string): Observable<UserProfile | null> {
    const queryPromise = this.supabase.getClient().then(client =>
      client
        .from('app_users')
        .select('*')
        .eq('auth_user_id', authUserId)
        .maybeSingle()
    );

    return from(queryPromise).pipe(
      map((response) => {
        if (response.error) {
          throw new Error(response.error.message);
        }
        return (response.data as UserProfile) || null;
      }),
      catchError((error) => {
        console.error('Error fetching user profile by auth ID:', error);
        return throwError(() => new Error('Failed to fetch user profile'));
      })
    );
  }

  /**
   * Obtiene el perfil de usuario por ID numérico
   */
  getProfileById(userId: number): Observable<UserProfile | null> {
    const queryPromise = this.supabase.getClient().then(client =>
      client
        .from('app_users')
        .select('*')
        .eq('id', userId)
        .maybeSingle()
    );

    return from(queryPromise).pipe(
      map((response) => {
        if (response.error) {
          throw new Error(response.error.message);
        }
        return (response.data as UserProfile) || null;
      }),
      catchError((error) => {
        console.error('Error fetching user profile by ID:', error);
        return throwError(() => new Error('Failed to fetch user profile'));
      })
    );
  }

  /**
   * Obtiene el perfil de usuario por email
   */
  getProfileByEmail(email: string): Observable<UserProfile | null> {
    const queryPromise = this.supabase.getClient().then(client =>
      client
        .from('app_users')
        .select('*')
        .eq('email', email.toLowerCase())
        .maybeSingle()
    );

    return from(queryPromise).pipe(
      map((response) => {
        if (response.error) {
          throw new Error(response.error.message);
        }
        return (response.data as UserProfile) || null;
      }),
      catchError((error) => {
        console.error('Error fetching user profile by email:', error);
        return throwError(() => new Error('Failed to fetch user profile'));
      })
    );
  }

  /**
   * Crea un nuevo perfil de usuario
   */
  createProfile(dto: CreateUserProfileDto): Observable<UserProfile> {
    const queryPromise = this.supabase.getClient().then(client =>
      client
        .from('app_users')
        .insert({
          ...dto,
          email: dto.email.toLowerCase(),
        })
        .select()
        .single()
    );

    return from(queryPromise).pipe(
      map((response) => {
        if (response.error) {
          throw new Error(response.error.message);
        }
        return response.data as UserProfile;
      }),
      catchError((error) => {
        console.error('Error creating user profile:', error);
        return throwError(() => new Error('Failed to create user profile'));
      })
    );
  }

  /**
   * Actualiza un perfil de usuario existente
   */
  updateProfile(dto: UpdateUserProfileDto): Observable<UserProfile> {
    const { id, ...updates } = dto;

    const queryPromise = this.supabase.getClient().then(client =>
      client
        .from('app_users')
        .update({
          ...updates,
          updated_at: new Date().toISOString(),
        })
        .eq('id', id)
        .select()
        .single()
    );

    return from(queryPromise).pipe(
      map((response) => {
        if (response.error) {
          throw new Error(response.error.message);
        }
        return response.data as UserProfile;
      }),
      catchError((error) => {
        console.error('Error updating user profile:', error);
        return throwError(() => new Error('Failed to update user profile'));
      })
    );
  }

  /**
   * Verifica si un usuario tiene práctica independiente
   */
  hasIndependentPractice(userId: number): Observable<boolean> {
    return this.getProfileById(userId).pipe(
      map((profile) => {
        if (!profile) return false;
        return profile.is_independent;
      })
    );
  }

  /**
   * Lista todos los perfiles (solo para admins)
   */
  listProfiles(limit: number = 50, offset: number = 0): Observable<UserProfile[]> {
    const queryPromise = this.supabase.getClient().then(client =>
      client
        .from('app_users')
        .select('*')
        .range(offset, offset + limit - 1)
        .order('created_at', { ascending: false })
    );

    return from(queryPromise).pipe(
      map((response) => {
        if (response.error) {
          throw new Error(response.error.message);
        }
        return (response.data || []) as UserProfile[];
      }),
      catchError((error) => {
        console.error('Error listing user profiles:', error);
        return throwError(() => new Error('Failed to list user profiles'));
      })
    );
  }
}
