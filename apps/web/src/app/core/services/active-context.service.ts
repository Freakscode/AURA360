import { Injectable, inject, signal, computed, effect } from '@angular/core';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { AccessContextService } from './access-context.service';
import { AccessContext, AccessContextType } from '../models/access-context.interface';

const ACTIVE_CONTEXT_STORAGE_KEY = 'aura360_active_context';

/**
 * Servicio para gestionar el contexto de acceso activo
 * Replica el patrón del ActiveAccessContextController de Flutter con Riverpod
 * Usa Angular Signals para state management reactivo
 */
@Injectable({
  providedIn: 'root',
})
export class ActiveContextService {
  private readonly accessContextService = inject(AccessContextService);

  /**
   * Signal con el contexto activo actual
   */
  private readonly _activeContext = signal<AccessContext | null>(null);
  readonly activeContext = this._activeContext.asReadonly();

  /**
   * Signal con todos los contextos disponibles
   */
  private readonly _availableContexts = signal<AccessContext[]>([]);
  readonly availableContexts = this._availableContexts.asReadonly();

  /**
   * Computed: indica si hay un contexto activo
   */
  readonly hasActiveContext = computed(() => this._activeContext() !== null);

  /**
   * Computed: rol efectivo del contexto activo
   */
  readonly effectiveRole = computed(() => {
    const context = this._activeContext();
    if (!context) return null;

    // Priorizar rol institucional si existe
    return context.institutionRole || context.globalRole;
  });

  /**
   * Computed: tier efectivo del contexto activo
   */
  readonly effectiveTier = computed(() => {
    const context = this._activeContext();
    if (!context) return null;

    // Extraer tier del billing plan o del contexto
    // Por ahora, retornamos el billing plan
    return context.billingPlan;
  });

  /**
   * Computed: indica si el contexto activo es institucional
   */
  readonly isInstitutionalContext = computed(() => {
    const context = this._activeContext();
    return context?.type === AccessContextType.INSTITUTIONAL;
  });

  /**
   * Computed: indica si el contexto activo es independiente
   */
  readonly isIndependentContext = computed(() => {
    const context = this._activeContext();
    return context?.type === AccessContextType.INDEPENDENT;
  });

  /**
   * Computed: institución activa (si aplica)
   */
  readonly activeInstitution = computed(() => {
    const context = this._activeContext();
    return context?.institution || null;
  });

  constructor() {
    // Effect para persistir el contexto activo en localStorage
    effect(() => {
      const context = this._activeContext();
      if (context) {
        this.persistActiveContext(context);
      }
    });
  }

  /**
   * Inicializa los contextos para un usuario
   * Carga todos los contextos y establece el activo (primario o restaurado)
   */
  initializeContexts(authUserId: string): Observable<AccessContext[]> {
    return this.accessContextService.loadUserContexts(authUserId).pipe(
      tap((contexts) => {
        this._availableContexts.set(contexts);

        // Intentar restaurar el contexto previamente activo
        const restored = this.restoreActiveContext(contexts);

        if (restored) {
          this._activeContext.set(restored);
        } else {
          // Si no se puede restaurar, seleccionar el primario
          const primary = contexts.find((ctx) => ctx.isPrimary);
          this._activeContext.set(primary || contexts[0] || null);
        }
      })
    );
  }

  /**
   * Cambia el contexto activo
   */
  setActiveContext(context: AccessContext): void {
    const available = this._availableContexts();

    // Verificar que el contexto está en la lista de disponibles
    const exists = available.some((ctx) => {
      if (ctx.institution && context.institution) {
        return ctx.institution.id === context.institution.id &&
               ctx.institutionRole === context.institutionRole;
      }
      return ctx.type === context.type && !ctx.institution && !context.institution;
    });

    if (!exists) {
      console.error('Attempted to set an unavailable context:', context);
      return;
    }

    this._activeContext.set(context);
  }

  /**
   * Cambia el contexto activo por índice en la lista de disponibles
   */
  setActiveContextByIndex(index: number): void {
    const available = this._availableContexts();

    if (index < 0 || index >= available.length) {
      console.error('Invalid context index:', index);
      return;
    }

    this._activeContext.set(available[index]);
  }

  /**
   * Cambia el contexto activo por membership ID (solo contextos institucionales)
   */
  setActiveContextByMembershipId(membershipId: number): void {
    const available = this._availableContexts();
    const context = available.find((ctx) => ctx.membershipId === membershipId);

    if (!context) {
      console.error('Context not found for membership ID:', membershipId);
      return;
    }

    this._activeContext.set(context);
  }

  /**
   * Limpia el contexto activo y los disponibles
   * Útil al cerrar sesión
   */
  clearContexts(): void {
    this._activeContext.set(null);
    this._availableContexts.set([]);
    this.clearPersistedContext();
  }

  /**
   * Recarga los contextos para el usuario actual
   */
  reloadContexts(authUserId: string): Observable<AccessContext[]> {
    return this.initializeContexts(authUserId);
  }

  /**
   * Persiste el contexto activo en localStorage
   */
  private persistActiveContext(context: AccessContext): void {
    try {
      const data = {
        type: context.type,
        membershipId: context.membershipId,
        institutionId: context.institution?.id || null,
        globalRole: context.globalRole,
      };

      localStorage.setItem(ACTIVE_CONTEXT_STORAGE_KEY, JSON.stringify(data));
    } catch (error) {
      console.error('Error persisting active context:', error);
    }
  }

  /**
   * Restaura el contexto activo desde localStorage
   */
  private restoreActiveContext(
    availableContexts: AccessContext[]
  ): AccessContext | null {
    try {
      const stored = localStorage.getItem(ACTIVE_CONTEXT_STORAGE_KEY);
      if (!stored) return null;

      const data = JSON.parse(stored);

      // Buscar el contexto en la lista de disponibles
      const context = availableContexts.find((ctx) => {
        if (data.type === AccessContextType.INSTITUTIONAL) {
          return (
            ctx.membershipId === data.membershipId &&
            ctx.institution?.id === data.institutionId
          );
        } else {
          return ctx.type === AccessContextType.INDEPENDENT;
        }
      });

      return context || null;
    } catch (error) {
      console.error('Error restoring active context:', error);
      return null;
    }
  }

  /**
   * Limpia el contexto persistido en localStorage
   */
  private clearPersistedContext(): void {
    try {
      localStorage.removeItem(ACTIVE_CONTEXT_STORAGE_KEY);
    } catch (error) {
      console.error('Error clearing persisted context:', error);
    }
  }
}
