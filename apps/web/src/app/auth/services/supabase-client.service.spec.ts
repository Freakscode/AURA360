import { PLATFORM_ID, provideZonelessChangeDetection } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { useSupabaseClient } from '../hooks/useSupabaseClient';
import {
  SupabaseClientService,
  provideSupabaseClient
} from './supabase-client.service';

describe('SupabaseClientService (DI integration)', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideZonelessChangeDetection(),
        provideSupabaseClient({
          settings: {
            url: 'https://example.supabase.co',
            anonKey: 'public-anon-key'
          }
        }),
        {
          provide: PLATFORM_ID,
          useValue: 'server'
        }
      ]
    });
  });

  it('injects SupabaseClientService via provideSupabaseClient', () => {
    const service = TestBed.inject(SupabaseClientService);

    expect(service).toBeTruthy();
    expect(service.readiness()).toBe('idle');
  });

  it('exposes hook-based access to the injected service', () => {
    TestBed.runInInjectionContext(() => {
      const handle = useSupabaseClient();

      expect(typeof handle.getClient).toBe('function');
      expect(handle.readiness()).toBe('idle');
    });
  });
});