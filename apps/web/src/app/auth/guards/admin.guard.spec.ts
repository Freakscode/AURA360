import { provideZonelessChangeDetection } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import type { ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';

import { adminGuard } from './admin.guard';
import { SupabaseClientService } from '../services/supabase-client.service';

describe('adminGuard', () => {
  const route = {} as ActivatedRouteSnapshot;
  const state = {} as RouterStateSnapshot;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideZonelessChangeDetection(),
        {
          provide: SupabaseClientService,
          useValue: {}
        }
      ]
    });
  });

  it('should block navigation while role evaluation is TODO', () => {
    const canActivate = TestBed.runInInjectionContext(() => adminGuard(route, state));
    expect(canActivate).toBeFalse();
  });
});