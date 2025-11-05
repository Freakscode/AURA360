/**
 * Modelos y utilidades para manejo de errores de autenticación
 * 
 * @module AuthErrorModel
 */

/**
 * Tipos de errores de autenticación
 */
export type AuthErrorType =
  | 'invalid_credentials'
  | 'email_not_confirmed'
  | 'user_disabled'
  | 'rate_limit'
  | 'network_error'
  | 'service_unavailable'
  | 'profile_fetch_failed'
  | 'unknown_error';

/**
 * Estructura de error de autenticación
 */
export interface AuthError {
  readonly type: AuthErrorType;
  readonly message: string;
  readonly technicalDetails?: string;
  readonly canRetry: boolean;
}

/**
 * Mapa de mensajes de error en español
 */
export const AUTH_ERROR_MESSAGES: Record<AuthErrorType, string> = {
  invalid_credentials: 'Email o contraseña incorrectos. Por favor verifica tus credenciales.',
  email_not_confirmed: 'Tu cuenta no ha sido confirmada. Revisa tu email para activarla.',
  user_disabled: 'Tu cuenta ha sido deshabilitada. Contacta con soporte para más información.',
  rate_limit: 'Demasiados intentos de inicio de sesión. Por favor espera unos minutos.',
  network_error: 'Error de conexión. Verifica tu conexión a internet e intenta nuevamente.',
  service_unavailable: 'Servicio temporalmente no disponible. Intenta nuevamente en unos momentos.',
  profile_fetch_failed: 'No se pudo cargar tu perfil. Por favor intenta iniciar sesión nuevamente.',
  unknown_error: 'Ocurrió un error inesperado. Por favor intenta nuevamente.'
} as const;

/**
 * Mapea errores de Supabase a errores de la aplicación con mensajes user-friendly
 * 
 * @param error - Error de Supabase o cualquier error genérico
 * @returns AuthError con tipo y mensaje apropiados
 */
export function mapSupabaseError(error: any): AuthError {
  // Extraer información del error
  const errorCode = error?.code || error?.error_code || '';
  const errorMessage = error?.message || '';
  const errorName = error?.name || '';

  // Credenciales inválidas
  if (
    errorMessage.includes('Invalid login credentials') ||
    errorMessage.includes('invalid_grant') ||
    errorCode === 'invalid_credentials'
  ) {
    return {
      type: 'invalid_credentials',
      message: AUTH_ERROR_MESSAGES.invalid_credentials,
      technicalDetails: errorMessage,
      canRetry: true
    };
  }

  // Email no confirmado
  if (
    errorMessage.includes('Email not confirmed') ||
    errorMessage.includes('email_not_confirmed') ||
    errorCode === 'email_not_confirmed'
  ) {
    return {
      type: 'email_not_confirmed',
      message: AUTH_ERROR_MESSAGES.email_not_confirmed,
      technicalDetails: errorMessage,
      canRetry: false
    };
  }

  // Usuario deshabilitado
  if (
    errorMessage.includes('User is disabled') ||
    errorMessage.includes('user_disabled') ||
    errorCode === 'user_disabled'
  ) {
    return {
      type: 'user_disabled',
      message: AUTH_ERROR_MESSAGES.user_disabled,
      technicalDetails: errorMessage,
      canRetry: false
    };
  }

  // Rate limiting
  if (
    errorCode === 'over_rate_limit' ||
    errorMessage.includes('rate limit') ||
    errorMessage.includes('too many requests')
  ) {
    return {
      type: 'rate_limit',
      message: AUTH_ERROR_MESSAGES.rate_limit,
      technicalDetails: errorMessage,
      canRetry: true
    };
  }

  // Error de red
  if (
    errorName === 'NetworkError' ||
    errorMessage.includes('network') ||
    errorMessage.includes('Failed to fetch') ||
    errorCode === 'network_error'
  ) {
    return {
      type: 'network_error',
      message: AUTH_ERROR_MESSAGES.network_error,
      technicalDetails: errorMessage,
      canRetry: true
    };
  }

  // Servicio no disponible
  if (
    errorCode === 'service_unavailable' ||
    errorMessage.includes('service unavailable') ||
    errorMessage.includes('503')
  ) {
    return {
      type: 'service_unavailable',
      message: AUTH_ERROR_MESSAGES.service_unavailable,
      technicalDetails: errorMessage,
      canRetry: true
    };
  }

  // Error al obtener perfil
  if (
    errorMessage.includes('profile') ||
    errorCode === 'profile_fetch_failed'
  ) {
    return {
      type: 'profile_fetch_failed',
      message: AUTH_ERROR_MESSAGES.profile_fetch_failed,
      technicalDetails: errorMessage,
      canRetry: true
    };
  }

  // Error desconocido (fallback)
  return {
    type: 'unknown_error',
    message: AUTH_ERROR_MESSAGES.unknown_error,
    technicalDetails: errorMessage || 'Error sin detalles',
    canRetry: true
  };
}