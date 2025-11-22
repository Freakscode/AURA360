import { inject } from '@angular/core';
import type { SupabaseClient } from '@supabase/supabase-js';

import {
  SupabaseClientService,
  type SupabaseReadinessState
} from '../services/supabase-client.service';

export interface SupabaseClientHandle {
  /**
   * Lazily resolves the underlying Supabase client. Only safe to call within the browser runtime.
   */
  readonly getClient: () => Promise<SupabaseClient>;
  /**
   * Convenience bridge to the Supabase auth state change subscription.
   */
  readonly onAuthStateChange: SupabaseClientService['onAuthStateChange'];
  /**
   * Read-only signal describing the readiness state of the client factory.
   */
  readonly readiness: () => SupabaseReadinessState;
}

/**
 * Standalone composable helper to interact with the Supabase client service without manually injecting it.
 */
export function useSupabaseClient(): SupabaseClientHandle {
  const service = inject(SupabaseClientService);
  return {
    getClient: () => service.getClient(),
    onAuthStateChange: (handler) => service.onAuthStateChange(handler),
    readiness: () => service.readiness()
  };
}