/**
 * Servicio de autenticación para AURA360
 * Maneja login, logout, gestión de sesión e integración con Supabase
 * 
 * @module AuthService
 */

import { HttpClient } from '@angular/common/http';
import { Injectable, PLATFORM_ID, inject } from '@angular/core';
import { Router } from '@angular/router';
import { isPlatformBrowser } from '@angular/common';
import type { AuthChangeEvent, Session, User } from '@supabase/supabase-js';
import { Observable, Subject, firstValueFrom } from 'rxjs';

import { SupabaseClientService } from '../../../auth/services/supabase-client.service';
import { AuthSessionStore } from './auth-session.store';
import { ActiveContextService } from '../../../core/services/active-context.service';
import type { LoginCredentials } from '../login/models/login-form.model';
import { AUTH_ERROR_MESSAGES, mapSupabaseError, type AuthError } from '../models/auth-error.model';

/**
 * Resultado exitoso de login
 */
export interface LoginSuccess {
  readonly session: Session;
  readonly user: User;
  readonly shouldRemember: boolean;
}

/**
 * Opciones para el método login
 */
export interface LoginOptions {
  readonly rememberMe?: boolean;
}

/**
 * Perfil de usuario desde el backend Django
 */
export interface UserProfile {
  readonly id: string;
  readonly email: string;
  readonly role_global: string;
  readonly tier: string;
  readonly full_name: string | null;
  readonly avatar_url?: string | null;
  readonly created_at?: string;
  readonly updated_at?: string;
}

/**
 * Servicio de autenticación principal de AURA360.
 * Proporciona métodos para login, logout, gestión de sesión y obtención de perfil de usuario.
 */
@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly supabaseClient = inject(SupabaseClientService);
  private readonly authSessionStore = inject(AuthSessionStore);
  private readonly activeContextService = inject(ActiveContextService);
  private readonly httpClient = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly platformId = inject(PLATFORM_ID);

  // Subject para emitir cambios de sesión
  private readonly sessionChangeSubject = new Subject<Session | null>();

  constructor() {
    // Inicializar listener de cambios de auth state si estamos en browser
    if (isPlatformBrowser(this.platformId)) {
      this.initAuthStateListener();
    }
  }

  /**
   * Proceso completo de login con email y password
   * 
   * @param credentials - Email y password del usuario
   * @param options - Opciones adicionales como rememberMe
   * @returns Promise con resultado del login exitoso
   * @throws AuthError si el login falla
   */
  async login(
    credentials: LoginCredentials,
    options: LoginOptions = {}
  ): Promise<LoginSuccess> {
    console.log('[AuthService] Login called with email:', credentials.email);

    // 1. Validar que estamos en browser
    if (!isPlatformBrowser(this.platformId)) {
      throw this.createAuthError(
        'unknown_error',
        'Login solo disponible en navegador'
      );
    }

    try {
      // 2. Establecer estado de carga
      this.authSessionStore.setLoading(true);
      this.authSessionStore.setError(null);

      // 3. Obtener cliente Supabase
      console.log('[AuthService] Getting Supabase client...');
      const client = await this.supabaseClient.getClient();
      console.log('[AuthService] Supabase client obtained');

      // 4. Llamar a signInWithPassword
      console.log('[AuthService] Calling signInWithPassword...');
      const { data, error } = await client.auth.signInWithPassword({
        email: credentials.email,
        password: credentials.password
      });

      // 5. Manejar error de Supabase
      if (error) {
        console.error('[AuthService] Supabase error:', error);
        const authError = mapSupabaseError(error);
        this.authSessionStore.setError(authError);
        throw authError;
      }
      console.log('[AuthService] signInWithPassword successful');

      // 6. Validar respuesta
      if (!data.session || !data.user) {
        const authError = this.createAuthError(
          'unknown_error',
          AUTH_ERROR_MESSAGES.unknown_error
        );
        this.authSessionStore.setError(authError);
        throw authError;
      }

      // 7. Actualizar store con la sesión
      this.authSessionStore.setSession(data.session, data.user);
      console.log('[AuthService] Session established for user:', data.user.email);
      console.log('[AuthService] User role:', data.user.user_metadata?.['role_global']);

      // 8. Cargar contextos de acceso para el usuario
      try {
        await firstValueFrom(
          this.activeContextService.initializeContexts(data.user.id)
        );
        this.authSessionStore.setContextsLoaded(true);
        console.log('[AuthService] Contexts loaded successfully');
      } catch (error) {
        console.error('[AuthService] Error loading user contexts:', error);
        // No fallar el login si los contextos no se cargan
        // El usuario aún puede autenticarse
      }

      // 9. Persistir sesión si remember me está activado
      if (options.rememberMe) {
        this.persistSession(data.session);
      }

      // 10. Emitir cambio de sesión
      this.sessionChangeSubject.next(data.session);

      return {
        session: data.session,
        user: data.user,
        shouldRemember: options.rememberMe ?? false
      };
    } catch (error) {
      // Si el error ya es un AuthError, re-lanzarlo
      if (this.isAuthError(error)) {
        throw error;
      }
      
      // Mapear errores desconocidos
      const authError = mapSupabaseError(error);
      this.authSessionStore.setError(authError);
      throw authError;
    } finally {
      // Siempre limpiar estado de carga
      this.authSessionStore.setLoading(false);
    }
  }

  /**
   * Obtiene el perfil del usuario autenticado desde el backend Django
   * 
   * @returns Promise con el perfil del usuario
   * @throws AuthError si no hay token o falla la petición
   */
  async getUserProfile(): Promise<UserProfile> {
    const token = this.authSessionStore.accessToken();

    if (!token) {
      throw this.createAuthError(
        'profile_fetch_failed',
        AUTH_ERROR_MESSAGES.profile_fetch_failed
      );
    }

    try {
      const profile = await firstValueFrom(
        this.httpClient.get<UserProfile>('/api/users/profile', {
          headers: {
            Authorization: `Bearer ${token}`
          }
        })
      );

      return profile;
    } catch (error: any) {
      throw this.createAuthError(
        'profile_fetch_failed',
        AUTH_ERROR_MESSAGES.profile_fetch_failed,
        error?.message || 'Error al obtener perfil'
      );
    }
  }

  /**
   * Cierra sesión del usuario y limpia todos los estados
   * 
   * @returns Promise que se resuelve cuando el logout está completo
   */
  async logout(): Promise<void> {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    try {
      // Intentar cerrar sesión en Supabase
      const client = await this.supabaseClient.getClient();
      await client.auth.signOut();
    } catch (error) {
      // Loguear error pero continuar con limpieza local
      console.error('[AuthService] Error during Supabase logout:', error);
    } finally {
      // Siempre limpiar estado local
      this.authSessionStore.clearSession();
      this.clearPersistedSession();

      // Limpiar contextos de acceso
      this.activeContextService.clearContexts();

      // Emitir cambio de sesión
      this.sessionChangeSubject.next(null);

      // Redirigir a login
      await this.router.navigate(['/auth/login']);
    }
  }

  /**
   * Obtiene la sesión actual desde Supabase
   * 
   * @returns Promise con la sesión actual o null
   */
  async getSession(): Promise<Session | null> {
    if (!isPlatformBrowser(this.platformId)) {
      return null;
    }

    try {
      const client = await this.supabaseClient.getClient();
      const { data } = await client.auth.getSession();
      return data.session;
    } catch (error) {
      console.error('[AuthService] Error getting session:', error);
      return null;
    }
  }

  /**
   * Verifica si hay una sesión activa
   * 
   * @returns true si hay una sesión válida
   */
  hasActiveSession(): boolean {
    return this.authSessionStore.hasValidSession();
  }

  /**
   * Observable de cambios en la sesión
   * 
   * @returns Observable que emite cuando cambia la sesión
   */
  onSessionChange(): Observable<Session | null> {
    return this.sessionChangeSubject.asObservable();
  }

  /**
   * Registra un callback para cambios en el estado de autenticación de Supabase
   * 
   * @param callback - Función a ejecutar cuando cambia el estado de auth
   * @returns Promise con función de unsubscribe
   */
  async onAuthStateChange(
    callback: (event: AuthChangeEvent, session: Session | null) => void
  ): Promise<() => void> {
    if (!isPlatformBrowser(this.platformId)) {
      return () => undefined;
    }

    return this.supabaseClient.onAuthStateChange(callback);
  }

  /**
   * Intenta restaurar la sesión desde storage persistido
   * 
   * @returns Promise que se resuelve cuando la restauración está completa
   */
  async tryRestoreSession(): Promise<boolean> {
    if (!isPlatformBrowser(this.platformId)) {
      return false;
    }

    try {
      // 1. Intentar obtener sesión de Supabase (localStorage)
      let session = await this.getSession();

      // 2. Fallback: Intentar recuperar backup manual (sessionStorage)
      if (!session) {
        console.log('[AuthService] No session in Supabase storage, trying backup...');
        session = await this.restoreFromBackup();
      }
      
      if (session) {
        console.log('[AuthService] Session restored successfully');
        // Actualizar store con sesión restaurada
        this.authSessionStore.setSession(session, session.user);

        // Cargar contextos de acceso
        try {
          await firstValueFrom(
            this.activeContextService.initializeContexts(session.user.id)
          );
          this.authSessionStore.setContextsLoaded(true);
        } catch (error) {
          console.error('[AuthService] Error loading contexts on restore:', error);
        }

        return true;
      }

      return false;
    } catch (error) {
      console.error('[AuthService] Error restoring session:', error);
      return false;
    }
  }

  // Métodos privados

  /**
   * Intenta restaurar la sesión desde el backup manual en sessionStorage
   */
  private async restoreFromBackup(): Promise<Session | null> {
    try {
      const backup = sessionStorage.getItem('aura_session');
      if (!backup) return null;

      const data = JSON.parse(backup);
      if (!data.refresh_token) return null;

      console.log('[AuthService] Found backup session, attempting refresh...');
      const client = await this.supabaseClient.getClient();
      
      // Intentar refrescar sesión usando el refresh token guardado
      const { data: refreshData, error } = await client.auth.refreshSession({ 
        refresh_token: data.refresh_token 
      });

      if (error || !refreshData.session) {
        console.warn('[AuthService] Failed to restore backup session:', error);
        this.clearPersistedSession(); // Limpiar backup corrupto/expirado
        return null;
      }

      return refreshData.session;
    } catch (e) {
      console.error('[AuthService] Error reading backup session:', e);
      return null;
    }
  }

  /**
   * Inicializa el listener de cambios de estado de autenticación
   */
  private async initAuthStateListener(): Promise<void> {
    try {
      await this.supabaseClient.onAuthStateChange((event, session) => {
        console.log('[AuthService] Auth state changed:', event);
        
        // Actualizar store según el evento
        if (event === 'SIGNED_IN' && session) {
          this.authSessionStore.setSession(session, session.user);
          this.sessionChangeSubject.next(session);
        } else if (event === 'SIGNED_OUT') {
          this.authSessionStore.clearSession();
          this.sessionChangeSubject.next(null);
        } else if (event === 'TOKEN_REFRESHED' && session) {
          this.authSessionStore.setSession(session, session.user);
          this.sessionChangeSubject.next(session);
        }
      });
    } catch (error) {
      console.error('[AuthService] Error initializing auth state listener:', error);
    }
  }

  /**
   * Persiste información mínima de sesión en sessionStorage
   * 
   * @param session - Sesión a persistir
   */
  private persistSession(session: Session): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    try {
      const sessionData = {
        access_token: session.access_token,
        expires_at: session.expires_at,
        refresh_token: session.refresh_token
      };

      sessionStorage.setItem('aura_session', JSON.stringify(sessionData));
    } catch (error) {
      console.error('[AuthService] Error persisting session:', error);
    }
  }

  /**
   * Limpia la sesión persistida de sessionStorage
   */
  private clearPersistedSession(): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    try {
      sessionStorage.removeItem('aura_session');
    } catch (error) {
      console.error('[AuthService] Error clearing persisted session:', error);
    }
  }

  /**
   * Crea un AuthError con tipo y mensaje específicos
   * 
   * @param type - Tipo de error
   * @param message - Mensaje del error
   * @param technicalDetails - Detalles técnicos opcionales
   * @returns AuthError construido
   */
  private createAuthError(
    type: AuthError['type'],
    message: string,
    technicalDetails?: string
  ): AuthError {
    return {
      type,
      message,
      technicalDetails,
      canRetry: type !== 'user_disabled' && type !== 'email_not_confirmed'
    };
  }

  /**
   * Type guard para verificar si un error es AuthError
   * 
   * @param error - Error a verificar
   * @returns true si es AuthError
   */
  private isAuthError(error: any): error is AuthError {
    return (
      error &&
      typeof error === 'object' &&
      'type' in error &&
      'message' in error &&
      'canRetry' in error
    );
  }
}