
import { InjectionToken, Provider } from '@angular/core';

import { SupabaseSettings } from '../../environments/environment.model';
import { environment } from '../../environments/environment';

export interface SupabaseSettingsProviderOptions {
  /**
   * Optional override for Supabase settings. Defaults to build-time environment values.
   */
  readonly settings?: SupabaseSettings;
}

/**
 * Injection token representing the public Supabase configuration used by the client service.
 */
export const SUPABASE_SETTINGS = new InjectionToken<SupabaseSettings>('SUPABASE_SETTINGS');

/**
 * Builds providers that supply Supabase settings to the dependency injection graph.
 */
export function provideSupabaseSettings(
  options: SupabaseSettingsProviderOptions = {}
): Provider[] {
  const settings = options.settings ?? environment.supabase;
  return [
    {
      provide: SUPABASE_SETTINGS,
      useValue: settings
    }
  ];
}
