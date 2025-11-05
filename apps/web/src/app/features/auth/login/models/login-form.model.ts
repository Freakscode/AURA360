/**
 * Modelos y tipos para el formulario de login de AURA360
 * 
 * @module LoginFormModel
 */

/**
 * Valores del formulario de login
 */
export interface LoginFormValue {
  readonly email: string;
  readonly password: string;
  readonly rememberMe: boolean;
}

/**
 * Datos de entrada para el proceso de login
 */
export interface LoginCredentials {
  readonly email: string;
  readonly password: string;
}

/**
 * Configuración de validación del formulario
 */
export interface LoginFormValidation {
  readonly email: {
    required: string;
    email: string;
    maxLength: string;
  };
  readonly password: {
    required: string;
    minLength: string;
    maxLength: string;
  };
}

/**
 * Constantes de validación para el formulario de login
 */
export const LOGIN_VALIDATION_RULES = {
  email: {
    maxLength: 255
  },
  password: {
    minLength: 6,
    maxLength: 100
  }
} as const;