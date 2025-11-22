/**
 * Modelos y tipos para el estado del componente de login
 * 
 * @module LoginStateModel
 */

import type { AuthError } from '../../models/auth-error.model';

/**
 * Estados posibles del componente de login
 */
export type LoginComponentState = 
  | 'idle'
  | 'validating'
  | 'loading'
  | 'success'
  | 'error'
  | 'redirecting';

/**
 * Estado completo del componente de login
 */
export interface LoginState {
  readonly status: LoginComponentState;
  readonly error: AuthError | null;
  readonly isSubmitting: boolean;
  readonly rememberMe: boolean;
}

/**
 * Estado inicial del componente de login
 */
export const INITIAL_LOGIN_STATE: LoginState = {
  status: 'idle',
  error: null,
  isSubmitting: false,
  rememberMe: false
} as const;