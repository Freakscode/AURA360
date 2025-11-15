import { Aura360Environment } from './environment.model';

/**
 * Production Environment Configuration
 *
 * INSTRUCCIONES DE CONFIGURACIÓN:
 *
 * 1. Obtener credenciales de Supabase:
 *    - Ve a https://app.supabase.com/project/YOUR_PROJECT/settings/api
 *    - Copia el "Project URL" (ej: https://abc123.supabase.co)
 *    - Copia el "Project API keys" > "anon/public"
 *
 * 2. Reemplazar los valores:
 *    - url: Pega el Project URL
 *    - anonKey: Pega la clave anon/public
 *
 * IMPORTANTE:
 * - NO uses la clave "service_role" en el frontend
 * - NO cometas este archivo con credenciales reales
 * - Usa variables de entorno en CI/CD para reemplazar estos valores
 *
 * EJEMPLO DE CONFIGURACIÓN:
 * url: 'https://xyzcompany.supabase.co'
 * anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
 */
export const environment: Aura360Environment = {
  production: true,
  apiBaseUrl: 'https://api.aura360.local/api',
  supabase: {
    // TODO: Reemplazar con tu URL de Supabase de producción
    url: 'http://127.0.0.1:54321',

    // TODO: Reemplazar con tu anon key de Supabase de producción
    anonKey:
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0',
  },
};
