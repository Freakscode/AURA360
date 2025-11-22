import { provideZonelessChangeDetection } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import type { ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';

import { tierGuard } from './tier.guard';
import { SupabaseClientService } from '../services/supabase-client.service';

describe('tierGuard', () => {
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
    const guard = tierGuard();
    const canActivate = TestBed.runInInjectionContext(() => guard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot));
    expect(canActivate).toBeFalse();
  });
});