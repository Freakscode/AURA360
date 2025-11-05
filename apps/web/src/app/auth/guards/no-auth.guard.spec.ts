import { provideZonelessChangeDetection } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import type { ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { Router } from '@angular/router';

import { noAuthGuard } from './no-auth.guard';
import { SupabaseClientService } from '../services/supabase-client.service';

describe('noAuthGuard', () => {
  const route = {} as ActivatedRouteSnapshot;
  const state = {} as RouterStateSnapshot;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideZonelessChangeDetection(),
        {
          provide: SupabaseClientService,
          useValue: {}
        },
        {
          provide: Router,
          useValue: jasmine.createSpyObj<Router>('Router', ['navigateByUrl'])
        }
      ]
    });
  });

  it('should allow navigation to auth views while redirect logic is pending', () => {
    const canActivate = TestBed.runInInjectionContext(() => noAuthGuard(route, state));
    expect(canActivate).toBeTrue();
  });
});