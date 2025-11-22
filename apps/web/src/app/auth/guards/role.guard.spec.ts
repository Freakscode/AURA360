import { provideZonelessChangeDetection } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import type { ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';

import { roleGuard } from './role.guard';
import { SupabaseClientService } from '../services/supabase-client.service';

describe('roleGuard', () => {
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
    const guard = roleGuard([]);
    const canActivate = TestBed.runInInjectionContext(() => guard({} as ActivatedRouteSnapshot, {} as RouterStateSnapshot));
    expect(canActivate).toBeFalse();
  });
});