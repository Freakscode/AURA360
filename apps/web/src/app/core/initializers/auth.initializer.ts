import { APP_INITIALIZER, PLATFORM_ID, Provider, inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { AuthService } from '../../features/auth/services/auth.service';

/**
 * Factory function to initialize authentication state
 */
export function authInitializerFactory(authService: AuthService): () => Promise<void> {
  const platformId = inject(PLATFORM_ID);
  
  return async () => {
    if (!isPlatformBrowser(platformId)) {
      return;
    }

    console.log('[AuthInitializer] Checking for existing session in browser storage...');
    try {
      const restored = await authService.tryRestoreSession();
      if (restored) {
         console.log('[AuthInitializer] Session successfully restored');
      } else {
         console.log('[AuthInitializer] No valid session found to restore');
      }
    } catch (error) {
      console.error('[AuthInitializer] Error restoring session:', error);
    }
  };
}

/**
 * Provider for the APP_INITIALIZER token to restore session on startup
 */
export const provideAuthInitializer = (): Provider => ({
  provide: APP_INITIALIZER,
  useFactory: authInitializerFactory,
  deps: [AuthService],
  multi: true,
});
