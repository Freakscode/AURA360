import { Injectable, inject } from '@angular/core';
import { Observable, of, forkJoin } from 'rxjs';
import { map, catchError, switchMap } from 'rxjs/operators';
import { UserProfileService } from './user-profile.service';
import { InstitutionMembershipService } from './institution-membership.service';
import {
  AccessContext,
  createInstitutionalContext,
  createIndependentContext,
} from '../models/access-context.interface';
import { InstitutionRole } from '../models/institution-role.enum';
import { GlobalRole } from '../models/global-role.enum';

/**
 * Servicio para construir y gestionar contextos de acceso
 * Replica la lógica del Flutter AccessContextRepository
 */
@Injectable({
  providedIn: 'root',
})
export class AccessContextService {
  private readonly userProfileService = inject(UserProfileService);
  private readonly membershipService = inject(InstitutionMembershipService);

  /**
   * Carga todos los contextos disponibles para un usuario
   * Replica el patrón del AccessContextRepository de Flutter
   *
   * @param authUserId - ID de autenticación del usuario (UUID de Supabase)
   * @returns Observable con la lista de contextos disponibles
   */
  loadUserContexts(authUserId: string): Observable<AccessContext[]> {
    return this.userProfileService.getProfileByAuthId(authUserId).pipe(
      switchMap((profile) => {
        if (!profile) {
          console.warn('No user profile found for auth ID:', authUserId);
          return of([]);
        }

        const contexts: Observable<AccessContext>[] = [];

        // 1. Cargar contextos institucionales (de memberships)
        const institutionalContexts$ = this.membershipService
          .getUserMemberships(profile.id)
          .pipe(
            map((memberships) => {
              return memberships.map((membership) => {
                if (!membership.institution) {
                  console.warn('Membership without institution data:', membership.id);
                  return null;
                }

                return createInstitutionalContext({
                  globalRole: profile.role_global,
                  institution: membership.institution,
                  institutionRole: membership.role_institution,
                  membershipId: membership.id,
                  isPrimary: membership.is_primary,
                  billingPlan: profile.billing_plan,
                });
              }).filter((ctx): ctx is AccessContext => ctx !== null);
            }),
            catchError((error) => {
              console.error('Error loading institutional contexts:', error);
              return of([]);
            })
          );

        // 2. Determinar si el usuario tiene práctica independiente
        const independentContext$ = of(profile.is_independent).pipe(
          map((isIndependent) => {
            if (!isIndependent) {
              return null;
            }

            // Solo ciertos roles pueden tener práctica independiente
            const allowedRoles = [
              GlobalRole.ADMIN_SISTEMA,
              GlobalRole.PROFESIONAL_SALUD,
            ];

            if (!allowedRoles.includes(profile.role_global)) {
              return null;
            }

            return createIndependentContext({
              globalRole: profile.role_global,
              billingPlan: profile.billing_plan,
            });
          })
        );

        // 3. Combinar contextos institucionales e independientes
        return forkJoin({
          institutional: institutionalContexts$,
          independent: independentContext$,
        }).pipe(
          map(({ institutional, independent }) => {
            const allContexts: AccessContext[] = [...institutional];

            if (independent) {
              allContexts.push(independent);
            }

            // 4. Garantizar al menos un contexto (patrón Flutter)
            if (allContexts.length === 0) {
              console.warn(
                'User has no contexts, creating default independent context'
              );
              allContexts.push(
                createIndependentContext({
                  globalRole: profile.role_global,
                  billingPlan: profile.billing_plan,
                })
              );
            }

            // 5. Ordenar: primario primero, luego por fecha
            return this.sortContexts(allContexts);
          })
        );
      }),
      catchError((error) => {
        console.error('Error loading user contexts:', error);
        return of([]);
      })
    );
  }

  /**
   * Obtiene el contexto primario del usuario
   * Si no hay primario explícito, retorna el primer contexto disponible
   */
  getPrimaryContext(authUserId: string): Observable<AccessContext | null> {
    return this.loadUserContexts(authUserId).pipe(
      map((contexts) => {
        if (contexts.length === 0) {
          return null;
        }

        // Buscar el contexto marcado como primario
        const primary = contexts.find((ctx) => ctx.isPrimary);
        if (primary) {
          return primary;
        }

        // Si no hay primario, retornar el primero de la lista ordenada
        return contexts[0];
      })
    );
  }

  /**
   * Obtiene contextos institucionales únicamente
   */
  getInstitutionalContexts(authUserId: string): Observable<AccessContext[]> {
    return this.loadUserContexts(authUserId).pipe(
      map((contexts) => contexts.filter((ctx) => ctx.institution !== null))
    );
  }

  /**
   * Obtiene el contexto independiente si existe
   */
  getIndependentContext(authUserId: string): Observable<AccessContext | null> {
    return this.loadUserContexts(authUserId).pipe(
      map((contexts) => {
        const independent = contexts.find((ctx) => ctx.institution === null);
        return independent || null;
      })
    );
  }

  /**
   * Verifica si un usuario tiene acceso a un rol específico en algún contexto
   */
  hasRoleInAnyContext(
    authUserId: string,
    roles: (GlobalRole | InstitutionRole)[]
  ): Observable<boolean> {
    return this.loadUserContexts(authUserId).pipe(
      map((contexts) => {
        return contexts.some((ctx) => {
          // Verificar rol global
          if (roles.includes(ctx.globalRole)) {
            return true;
          }

          // Verificar rol institucional
          if (ctx.institutionRole && roles.includes(ctx.institutionRole)) {
            return true;
          }

          return false;
        });
      })
    );
  }

  /**
   * Ordena contextos por prioridad:
   * 1. Primario primero
   * 2. Institucionales antes que independientes
   * 3. Por nombre de institución alfabéticamente
   */
  private sortContexts(contexts: AccessContext[]): AccessContext[] {
    return contexts.sort((a, b) => {
      // 1. Primario primero
      if (a.isPrimary && !b.isPrimary) return -1;
      if (!a.isPrimary && b.isPrimary) return 1;

      // 2. Institucionales antes que independientes
      if (a.institution && !b.institution) return -1;
      if (!a.institution && b.institution) return 1;

      // 3. Por nombre de institución
      if (a.institution && b.institution) {
        return a.institution.name.localeCompare(b.institution.name);
      }

      return 0;
    });
  }
}
