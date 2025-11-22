import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { SupabaseClientService } from '../../auth/services/supabase-client.service';
import { from, of } from 'rxjs';
import { switchMap, catchError } from 'rxjs/operators';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  console.log('INTERCEPTOR: Check URL', req.url);
  const supabaseService = inject(SupabaseClientService);

  if (req.url.includes('localhost:8000') || req.url.includes('/api/')) {
    console.log('INTERCEPTOR: Intercepting API call');
    return from(supabaseService.getClient().then(client => client.auth.getSession())).pipe(
      switchMap(({ data: { session } }) => {
        console.log('INTERCEPTOR: Session found?', !!session);
        if (session?.access_token) {
          console.log('INTERCEPTOR: Adding token');
          const authReq = req.clone({
            setHeaders: {
              Authorization: `Bearer ${session.access_token}`
            }
          });
          return next(authReq);
        }
        return next(req);
      }),
      catchError((err) => {
        console.error('INTERCEPTOR: Error getting session', err);
        return next(req);
      })
    );
  }

  return next(req);
};
