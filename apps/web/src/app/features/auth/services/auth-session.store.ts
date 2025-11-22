/**
 * Signal store para gestión del estado de sesión de autenticación
 * 
 * @module AuthSessionStore
 */

import { Injectable, computed, signal } from '@angular/core';
import type { Session, User } from '@supabase/supabase-js';
import type { AuthError } from '../models/auth-error.model';

/**
 * Estado de la sesión de autenticación
 */
export interface AuthSession {
  readonly user: User | null;
  readonly session: Session | null;
  readonly isAuthenticated: boolean;
  readonly expiresAt: number | null;
  readonly accessToken: string | null;
}

/**
 * Signal store para gestionar el estado de sesión global de autenticación.
 * Utiliza Angular signals para estado reactivo y zoneless change detection.
 */
@Injectable({
  providedIn: 'root'
})
export class AuthSessionStore {
  // Signals privados para estado mutable
  private readonly _user = signal<User | null>(null);
  private readonly _session = signal<Session | null>(null);
  private readonly _isLoading = signal<boolean>(false);
  private readonly _error = signal<AuthError | null>(null);

  // Signals públicos de solo lectura
  readonly user = this._user.asReadonly();
  readonly session = this._session.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  // Computed signals para datos derivados
  
  /**
   * Indica si el usuario está autenticado
   */
  readonly isAuthenticated = computed(() => {
    return this._session() !== null && this._user() !== null;
  });

  /**
   * Timestamp de expiración de la sesión en milisegundos
   */
  readonly expiresAt = computed(() => {
    const session = this._session();
    return session?.expires_at ? session.expires_at * 1000 : null;
  });

  /**
   * Token de acceso de la sesión actual
   */
  readonly accessToken = computed(() => {
    return this._session()?.access_token ?? null;
  });

  /**
   * Rol global del usuario desde los metadatos
   */
  readonly userRole = computed(() => {
    const user = this._user();
    if (!user) return null;
    
    // Intentar obtener el rol desde app_metadata o user_metadata
    const role = user.app_metadata?.['role_global'] || 
                 user.user_metadata?.['role_global'] ||
                 null;
    
    return role as string | null;
  });

  /**
   * Tier del usuario desde los metadatos
   */
  readonly userTier = computed(() => {
    const user = this._user();
    if (!user) return null;
    
    // Intentar obtener el tier desde app_metadata o user_metadata
    const tier = user.app_metadata?.['tier'] || 
                 user.user_metadata?.['tier'] ||
                 'free'; // Default tier
    
    return tier as string;
  });

  /**
   * Email del usuario autenticado
   */
  readonly userEmail = computed(() => {
    return this._user()?.email ?? null;
  });

  /**
   * ID del usuario autenticado
   */
  readonly userId = computed(() => {
    return this._user()?.id ?? null;
  });

  /**
   * Nombre completo del usuario desde metadatos
   */
  readonly userFullName = computed(() => {
    const user = this._user();
    if (!user) return null;

    return (
      user.user_metadata?.['full_name'] ||
      user.app_metadata?.['full_name'] ||
      null
    );
  });

  /**
   * Flag indicando si los contextos de acceso han sido cargados
   */
  private readonly _contextsLoaded = signal<boolean>(false);
  readonly contextsLoaded = this._contextsLoaded.asReadonly();

  // Métodos públicos para actualizar el estado

  /**
   * Establece la sesión y el usuario en el store
   *
   * @param session - Sesión de Supabase
   * @param user - Usuario de Supabase
   */
  setSession(session: Session | null, user: User | null): void {
    console.log('[AuthSessionStore] Setting session for user:', user?.email);
    console.log('[AuthSessionStore] User metadata:', user?.user_metadata);
    console.log('[AuthSessionStore] App metadata:', user?.app_metadata);
    this._session.set(session);
    this._user.set(user);
    this._error.set(null); // Limpiar errores al establecer sesión exitosa
  }

  /**
   * Limpia completamente la sesión del store
   */
  clearSession(): void {
    this._session.set(null);
    this._user.set(null);
    this._error.set(null);
    this._isLoading.set(false);
    this._contextsLoaded.set(false);
  }

  /**
   * Marca los contextos como cargados
   */
  setContextsLoaded(loaded: boolean): void {
    this._contextsLoaded.set(loaded);
  }

  /**
   * Establece el estado de carga
   * 
   * @param isLoading - Indica si hay una operación en curso
   */
  setLoading(isLoading: boolean): void {
    this._isLoading.set(isLoading);
  }

  /**
   * Establece un error de autenticación
   * 
   * @param error - Error de autenticación o null para limpiar
   */
  setError(error: AuthError | null): void {
    this._error.set(error);
  }

  /**
   * Obtiene una snapshot del estado actual de la sesión
   * 
   * @returns Estado de sesión completo
   */
  getSessionSnapshot(): AuthSession {
    return {
      user: this._user(),
      session: this._session(),
      isAuthenticated: this.isAuthenticated(),
      expiresAt: this.expiresAt(),
      accessToken: this.accessToken()
    };
  }

  /**
   * Verifica si la sesión ha expirado
   * 
   * @returns true si la sesión está expirada
   */
  isSessionExpired(): boolean {
    const expiresAt = this.expiresAt();
    if (!expiresAt) return false;
    
    return Date.now() >= expiresAt;
  }

  /**
   * Verifica si hay una sesión válida y no expirada
   * 
   * @returns true si hay una sesión válida
   */
  hasValidSession(): boolean {
    return this.isAuthenticated() && !this.isSessionExpired();
  }
}