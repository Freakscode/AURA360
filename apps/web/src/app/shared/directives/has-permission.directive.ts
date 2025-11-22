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

/**
 * Tipo de permiso personalizado
 */
export type Permission =
  | 'admin'
  | 'system-admin'
  | 'manage-users'
  | 'manage-institution'
  | 'view-clinical-data'
  | 'premium-features';

/**
 * Directiva estructural para mostrar/ocultar elementos basado en permisos específicos
 *
 * @example
 * ```html
 * <button *hasPermission="'manage-users'">
 *   Gestionar usuarios
 * </button>
 *
 * <div *hasPermission="'premium-features'; else upgradeTemplate">
 *   Features premium
 * </div>
 * <ng-template #upgradeTemplate>
 *   <a href="/upgrade">Actualiza a premium</a>
 * </ng-template>
 * ```
 */
@Directive({
  selector: '[hasPermission]',
  standalone: true,
})
export class HasPermissionDirective {
  private readonly permissionService = inject(PermissionService);
  private readonly activeContextService = inject(ActiveContextService);
  private readonly templateRef = inject(TemplateRef<any>);
  private readonly viewContainer = inject(ViewContainerRef);

  private requiredPermission: Permission | null = null;
  private hasView = false;
  private elseTemplateRef: TemplateRef<any> | null = null;

  @Input() set hasPermission(permission: Permission) {
    this.requiredPermission = permission;
    this.updateView();
  }

  @Input() set hasPermissionElse(templateRef: TemplateRef<any> | null) {
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
    const hasPermission = this.checkPermission(this.requiredPermission);

    this.viewContainer.clear();
    this.hasView = false;

    if (hasPermission) {
      this.viewContainer.createEmbeddedView(this.templateRef);
      this.hasView = true;
    } else if (this.elseTemplateRef) {
      this.viewContainer.createEmbeddedView(this.elseTemplateRef);
    }
  }

  private checkPermission(permission: Permission | null): boolean {
    if (!permission) return false;

    switch (permission) {
      case 'admin':
        return this.permissionService.isAdmin();

      case 'system-admin':
        return this.permissionService.isSystemAdmin();

      case 'manage-users':
        return this.permissionService.canManageUsers();

      case 'manage-institution':
        return this.permissionService.canManageInstitution();

      case 'view-clinical-data':
        return this.permissionService.canViewClinicalData();

      case 'premium-features':
        return this.permissionService.canAccessPremiumFeatures();

      default:
        console.warn('Unknown permission:', permission);
        return false;
    }
  }
}
