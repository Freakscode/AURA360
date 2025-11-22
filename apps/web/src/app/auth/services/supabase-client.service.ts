import { isPlatformBrowser } from '@angular/common';
import {
  EnvironmentProviders,
  Injectable,
  InjectionToken,
  NgZone,
  PLATFORM_ID,
  inject,
  makeEnvironmentProviders,
  signal
} from '@angular/core';
import type {
  AuthChangeEvent,
  Session,
  SupabaseClient,
  SupabaseClientOptions
} from '@supabase/supabase-js';

import {
  SUPABASE_SETTINGS,
  SupabaseSettingsProviderOptions,
  provideSupabaseSettings
} from '../auth.config';
import { isSupabaseConfigured, type SupabaseSettings } from '../../../environments/environment.model';

export type SupabaseReadinessState = 'idle' | 'initializing' | 'ready' | 'error';

export type SupabaseClientProviderOptions = SupabaseSettingsProviderOptions;

const SUPABASE_CLIENT_FACTORY = new InjectionToken<() => Promise<SupabaseClient>>(
  'SUPABASE_CLIENT_FACTORY'
);

const supabaseReadyState = signal<SupabaseReadinessState>('idle');

@Injectable()
export class SupabaseClientService {
  private readonly platformId = inject(PLATFORM_ID);
  private readonly zone = inject(NgZone);
  private readonly config = inject<SupabaseSettings>(SUPABASE_SETTINGS);

  private client: SupabaseClient | null = null;
  private clientPromise: Promise<SupabaseClient> | null = null;

  constructor() {
    if (!isPlatformBrowser(this.platformId)) {
      supabaseReadyState.set('idle');
      return;
    }

    if (!isSupabaseConfigured(this.config)) {
      supabaseReadyState.set('error');
    }
  }

  /**
   * Returns the lazily created Supabase client. Throws when invoked during SSR or
   * when configuration placeholders have not been replaced.
   */
  async getClient(): Promise<SupabaseClient> {
    if (!isPlatformBrowser(this.platformId)) {
      throw new Error('Supabase client is only available in the browser runtime.');
    }

    if (!isSupabaseConfigured(this.config)) {
      throw new Error(
        'Supabase configuration is incomplete. Please set SUPABASE_URL and SUPABASE_ANON_KEY.'
      );
    }

    if (this.client) {
      return this.client;
    }

    return this.ensureClientInitialized(this.config);
  }

  /**
   * Registers a listener for Supabase auth state changes. The handler executes inside Angular's zone.
   * Returns an unsubscribe callback that is safe to invoke multiple times.
   */
  async onAuthStateChange(
    handler: (event: AuthChangeEvent, session: Session | null) => void
  ): Promise<() => void> {
    if (!isPlatformBrowser(this.platformId) || !isSupabaseConfigured(this.config)) {
      return () => undefined;
    }

    const client = await this.getClient();
    const {
      data: { subscription }
    } = client.auth.onAuthStateChange((event: AuthChangeEvent, session: Session | null) => {
      this.zone.run(() => handler(event, session));
    });

    return () => subscription.unsubscribe();
  }

  /**
   * Exposes the current client readiness signal for diagnostics (development only).
   */
  get readiness() {
    return supabaseReadyState.asReadonly();
  }

  private ensureClientInitialized(config: SupabaseSettings): Promise<SupabaseClient> {
    if (this.clientPromise) {
      return this.clientPromise;
    }

    supabaseReadyState.set('initializing');

    this.clientPromise = this.zone
      .runOutsideAngular(async () => {
        const { createClient } = await import('@supabase/supabase-js');
        const options: SupabaseClientOptions<'public'> = {
          auth: {
            /**
             * autoRefreshToken is only executed in the browser because ensureClientInitialized is
             * gated behind an isPlatformBrowser check.
             */
            autoRefreshToken: true,
            persistSession: true,
            detectSessionInUrl: true
          }
        };

        const client = createClient(config.url, config.anonKey, options);
        this.client = client;
        supabaseReadyState.set('ready');
        return client;
      })
      .catch((error) => {
        supabaseReadyState.set('error');
        this.clientPromise = null;
        throw error;
      });

    return this.clientPromise;
  }
}

/**
 * Provides the {@link SupabaseClientService} alongside a factory token for consuming the underlying client.
 */
export function provideSupabaseClient(
  options: SupabaseClientProviderOptions = {}
): EnvironmentProviders {
  return makeEnvironmentProviders([
    ...provideSupabaseSettings(options),
    SupabaseClientService,
    {
      provide: SUPABASE_CLIENT_FACTORY,
      useFactory: () => {
        const service = inject(SupabaseClientService);
        return () => service.getClient();
      }
    }
  ]);
}

/**
 * Utility accessor for lazily retrieving the Supabase client factory function via dependency injection.
 */
export function injectSupabaseClientFactory(): () => Promise<SupabaseClient> {
  return inject(SUPABASE_CLIENT_FACTORY);
}