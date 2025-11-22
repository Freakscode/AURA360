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
import { GlobalRole } from '../../core/models/global-role.enum';
import { InstitutionRole } from '../../core/models/institution-role.enum';

/**
 * Directiva estructural para mostrar/ocultar elementos basado en roles
 *
 * @example
 * ```html
 * <div *hasRole="[GlobalRole.ADMIN_SISTEMA]">
 *   Solo visible para AdminSistema
 * </div>
 *
 * <button *hasRole="[GlobalRole.PROFESIONAL_SALUD, InstitutionRole.PROFESIONAL_SALUD]">
 *   Visible para profesionales de salud
 * </button>
 * ```
 */
@Directive({
  selector: '[hasRole]',
  standalone: true,
})
export class HasRoleDirective {
  private readonly permissionService = inject(PermissionService);
  private readonly activeContextService = inject(ActiveContextService);
  private readonly templateRef = inject(TemplateRef<any>);
  private readonly viewContainer = inject(ViewContainerRef);

  private requiredRoles: (GlobalRole | InstitutionRole)[] = [];
  private hasView = false;

  @Input() set hasRole(roles: (GlobalRole | InstitutionRole)[]) {
    this.requiredRoles = roles;
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
    const hasPermission = this.permissionService.hasRole(this.requiredRoles);

    if (hasPermission && !this.hasView) {
      this.viewContainer.createEmbeddedView(this.templateRef);
      this.hasView = true;
    } else if (!hasPermission && this.hasView) {
      this.viewContainer.clear();
      this.hasView = false;
    }
  }
}
