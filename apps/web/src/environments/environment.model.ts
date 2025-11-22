export interface SupabaseSettings {
  /**
   * Public Supabase project URL. Do not embed service-role URLs or secrets here.
   */
  readonly url: string;

  /**
   * Public anonymous key used for browser authentication flows.
   */
  readonly anonKey: string;
}

export interface Aura360Environment {
  readonly production: boolean;
  readonly supabase: SupabaseSettings;
  /** Base URL for the Django API (e.g., https://api.example.com/api). */
  readonly apiBaseUrl: string;
  /**
   * Deprecated alias kept for backward compatibility with legacy services.
   * Prefer `apiBaseUrl` going forward.
   */
  readonly apiUrl?: string;
}

/**
 * Utility helper to detect whether a Supabase configuration uses placeholder values.
 * This can be leveraged by runtime guards before attempting to create clients.
 */
export function isSupabaseConfigured(config: SupabaseSettings): boolean {
  const placeholderHints = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'YOUR_', '__'];
  const hasEmptyValues = !config.url || !config.anonKey;
  const hasPlaceholders = placeholderHints.some((hint) =>
    config.url.includes(hint) || config.anonKey.includes(hint)
  );
  return !(hasEmptyValues || hasPlaceholders);
}
