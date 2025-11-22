import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActiveContextService } from '../../../core/services/active-context.service';
import { AccessContext } from '../../../core/models/access-context.interface';
import {
  GLOBAL_ROLE_LABELS,
  GlobalRole,
} from '../../../core/models/global-role.enum';
import {
  INSTITUTION_ROLE_LABELS,
  InstitutionRole,
} from '../../../core/models/institution-role.enum';
import { BillingPlan } from '../../../core/models/billing-plan.enum';

/**
 * Componente dropdown para cambiar entre contextos de acceso disponibles
 */
@Component({
  selector: 'app-context-switcher',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './context-switcher.component.html',
  styleUrl: './context-switcher.component.scss',
})
export class ContextSwitcherComponent {
  private readonly activeContextService = inject(ActiveContextService);

  readonly activeContext = this.activeContextService.activeContext;
  readonly availableContexts = this.activeContextService.availableContexts;
  readonly isOpen = signal(false);

  /**
   * Alterna el dropdown
   */
  toggle(): void {
    this.isOpen.update((value) => !value);
  }

  /**
   * Cierra el dropdown
   */
  close(): void {
    this.isOpen.set(false);
  }

  /**
   * Selecciona un contexto y cierra el dropdown
   */
  selectContext(context: AccessContext): void {
    this.activeContextService.setActiveContext(context);
    this.close();
  }

  /**
   * Obtiene el label legible de un rol
   */
  getRoleLabel(context: AccessContext): string {
    if (context.institutionRole) {
      return INSTITUTION_ROLE_LABELS[context.institutionRole];
    }
    return GLOBAL_ROLE_LABELS[context.globalRole];
  }

  /**
   * Obtiene el badge de tier/plan
   */
  getTierBadge(context: AccessContext): string {
    const plan = context.billingPlan;

    if (plan === BillingPlan.INDIVIDUAL || plan === BillingPlan.INSTITUTION || plan === BillingPlan.CORPORATE) {
      return 'Premium';
    }

    if (plan === BillingPlan.TRIAL) {
      return 'Trial';
    }

    return '';
  }

  /**
   * Verifica si un contexto es el activo
   */
  isActiveContext(context: AccessContext): boolean {
    const active = this.activeContext();
    if (!active) return false;

    if (context.institution && active.institution) {
      return (
        context.institution.id === active.institution.id &&
        context.institutionRole === active.institutionRole
      );
    }

    return context.type === active.type && !context.institution && !active.institution;
  }
}
