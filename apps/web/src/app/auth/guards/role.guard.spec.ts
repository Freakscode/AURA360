import { provideZonelessChangeDetection } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import type { ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';

import { roleGuard } from './role.guard';
import { SupabaseClientService } from '../services/supabase-client.service';

describe('roleGuard', () => {
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

  it('should block navigation until role checks are implemented', () => {
    const canActivate = TestBed.runInInjectionContext(() => roleGuard(route, state));
    expect(canActivate).toBeFalse();
  });
});