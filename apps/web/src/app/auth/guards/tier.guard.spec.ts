import { provideZonelessChangeDetection } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import type { ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';

import { tierGuard } from './tier.guard';
import { SupabaseClientService } from '../services/supabase-client.service';

describe('tierGuard', () => {
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

  it('should block navigation while tier logic is a placeholder', () => {
    const canActivate = TestBed.runInInjectionContext(() => tierGuard(route, state));
    expect(canActivate).toBeFalse();
  });
});