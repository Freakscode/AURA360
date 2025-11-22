import {
  Directive,
  Input,
  TemplateRef,
  ViewContainerRef,
  inject,
  effect,
} from '@angular/core';
import { PermissionService } from '../../core/services/permission.service';
import { ActiveContextService } from '../../core/services/active-context.service';
import { UserTier } from '../../core/models/user-tier.enum';

/**
 * Directiva estructural para mostrar/ocultar elementos basado en tier de suscripción
 *
 * @example
 * ```html
 * <div *hasTier="UserTier.PREMIUM">
 *   Solo visible para usuarios premium
 * </div>
 *
 * <!-- Con template else -->
 * <div *hasTier="UserTier.PREMIUM; else freeTemplate">
 *   Contenido premium
 * </div>
 * <ng-template #freeTemplate>
 *   Actualiza a premium para acceder a esta función
 * </ng-template>
 * ```
 */
@Directive({
  selector: '[hasTier]',
  standalone: true,
})
export class HasTierDirective {
  private readonly permissionService = inject(PermissionService);
  private readonly activeContextService = inject(ActiveContextService);
  private readonly templateRef = inject(TemplateRef<any>);
  private readonly viewContainer = inject(ViewContainerRef);

  private minimumTier: UserTier = UserTier.FREE;
  private hasView = false;
  private elseTemplateRef: TemplateRef<any> | null = null;

  @Input() set hasTier(tier: UserTier) {
    this.minimumTier = tier;
    this.updateView();
  }

  @Input() set hasTierElse(templateRef: TemplateRef<any> | null) {
    this.elseTemplateRef = templateRef;
    this.updateView();
  }

  constructor() {
    // Effect para actualizar la vista cuando cambia el contexto activo
    effect(() => {
      // Trigger cuando cambia el contexto activo
      this.activeContextService.activeContext();
      this.updateView();
    });
  }

  private updateView(): void {
    const hasPermission = this.permissionService.hasTier(this.minimumTier);

    this.viewContainer.clear();
    this.hasView = false;

    if (hasPermission) {
      this.viewContainer.createEmbeddedView(this.templateRef);
      this.hasView = true;
    } else if (this.elseTemplateRef) {
      this.viewContainer.createEmbeddedView(this.elseTemplateRef);
    }
  }
}
