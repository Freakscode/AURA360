import { Injectable, inject, computed } from '@angular/core';
import { ActiveContextService } from './active-context.service';
import { PermissionService } from './permission.service';
import { GlobalRole } from '../models/global-role.enum';
import { InstitutionRole } from '../models/institution-role.enum';

/**
 * Item de menú de navegación
 */
export interface NavigationMenuItem {
  label: string;
  route: string;
  icon?: string;
  badge?: string;
  isPremium?: boolean;
}

/**
 * Servicio para generar items de menú basados en el rol activo
 */
@Injectable({
  providedIn: 'root',
})
export class NavigationMenuService {
  private readonly activeContextService = inject(ActiveContextService);
  private readonly permissionService = inject(PermissionService);

  /**
   * Computed: items de menú para el rol activo
   */
  readonly menuItems = computed(() => {
    const context = this.activeContextService.activeContext();
    if (!context) return [];

    const role = this.activeContextService.effectiveRole();
    if (!role) return [];

    return this.getMenuItemsForRole(role);
  });

  /**
   * Genera items de menú según el rol
   */
  private getMenuItemsForRole(role: string): NavigationMenuItem[] {
    switch (role) {
      case GlobalRole.ADMIN_SISTEMA:
        return this.getAdminSistemaMenu();

      case GlobalRole.ADMIN_INSTITUCION:
      case InstitutionRole.ADMIN_INSTITUCION:
        return this.getAdminInstitucionMenu();

      case GlobalRole.ADMIN_INSTITUCION_SALUD:
      case InstitutionRole.ADMIN_INSTITUCION_SALUD:
        return this.getAdminSaludMenu();

      case GlobalRole.PROFESIONAL_SALUD:
      case InstitutionRole.PROFESIONAL_SALUD:
        return this.getProfesionalMenu();

      case GlobalRole.PACIENTE:
      case InstitutionRole.PACIENTE:
        return this.getPacienteMenu();

      case GlobalRole.GENERAL:
        return this.getGeneralMenu();

      default:
        return [];
    }
  }

  /**
   * Menú para AdminSistema
   */
  private getAdminSistemaMenu(): NavigationMenuItem[] {
    return [
      {
        label: 'Dashboard',
        route: '/admin-sistema',
        icon: 'dashboard',
      },
      {
        label: 'Instituciones',
        route: '/admin-sistema/instituciones',
        icon: 'business',
      },
      {
        label: 'Usuarios',
        route: '/admin-sistema/usuarios',
        icon: 'people',
      },
      {
        label: 'Suscripciones',
        route: '/admin-sistema/suscripciones',
        icon: 'credit_card',
      },
      {
        label: 'Reportes',
        route: '/admin-sistema/reportes',
        icon: 'analytics',
      },
      {
        label: 'Configuración',
        route: '/admin-sistema/configuracion',
        icon: 'settings',
      },
    ];
  }

  /**
   * Menú para AdminInstitucion
   */
  private getAdminInstitucionMenu(): NavigationMenuItem[] {
    return [
      {
        label: 'Dashboard',
        route: '/admin-institucion',
        icon: 'dashboard',
      },
      {
        label: 'Miembros',
        route: '/admin-institucion/miembros',
        icon: 'people',
      },
      {
        label: 'Departamentos',
        route: '/admin-institucion/departamentos',
        icon: 'corporate_fare',
      },
      {
        label: 'Reportes',
        route: '/admin-institucion/reportes',
        icon: 'analytics',
      },
      {
        label: 'Configuración',
        route: '/admin-institucion/configuracion',
        icon: 'settings',
      },
    ];
  }

  /**
   * Menú para AdminInstitucionSalud
   */
  private getAdminSaludMenu(): NavigationMenuItem[] {
    return [
      {
        label: 'Dashboard',
        route: '/admin-salud',
        icon: 'dashboard',
      },
      {
        label: 'Profesionales',
        route: '/admin-salud/profesionales',
        icon: 'medical_services',
      },
      {
        label: 'Pacientes',
        route: '/admin-salud/pacientes',
        icon: 'people',
      },
      {
        label: 'Agenda Clínica',
        route: '/admin-salud/agenda',
        icon: 'calendar_month',
      },
      {
        label: 'Reportes Médicos',
        route: '/admin-salud/reportes',
        icon: 'analytics',
        isPremium: true,
      },
      {
        label: 'Configuración',
        route: '/admin-salud/configuracion',
        icon: 'settings',
      },
    ];
  }

  /**
   * Menú para ProfesionalSalud
   */
  private getProfesionalMenu(): NavigationMenuItem[] {
    return [
      {
        label: 'Dashboard',
        route: '/profesional',
        icon: 'dashboard',
      },
      {
        label: 'Mis Pacientes',
        route: '/profesional/pacientes',
        icon: 'people',
      },
      {
        label: 'Agenda',
        route: '/profesional/agenda',
        icon: 'calendar_month',
      },
      {
        label: 'Consultas',
        route: '/profesional/consultas',
        icon: 'medical_services',
      },
      {
        label: 'Historial Clínico',
        route: '/profesional/historial',
        icon: 'folder_shared',
      },
      {
        label: 'Mensajes',
        route: '/profesional/mensajes',
        icon: 'message',
      },
    ];
  }

  /**
   * Menú para Paciente
   */
  private getPacienteMenu(): NavigationMenuItem[] {
    return [
      {
        label: 'Mi Panel',
        route: '/paciente',
        icon: 'dashboard',
      },
      {
        label: 'Mind (Mente)',
        route: '/paciente/mind',
        icon: 'psychology',
      },
      {
        label: 'Body (Cuerpo)',
        route: '/paciente/body',
        icon: 'fitness_center',
      },
      {
        label: 'Soul (Alma)',
        route: '/paciente/soul',
        icon: 'self_improvement',
      },
      {
        label: 'Mis Consultas',
        route: '/paciente/consultas',
        icon: 'calendar_month',
      },
      {
        label: 'Mensajes',
        route: '/paciente/mensajes',
        icon: 'message',
      },
    ];
  }

  /**
   * Menú para usuario General
   */
  private getGeneralMenu(): NavigationMenuItem[] {
    return [
      {
        label: 'Inicio',
        route: '/general',
        icon: 'home',
      },
      {
        label: 'Mind (Mente)',
        route: '/general/mind',
        icon: 'psychology',
        isPremium: true,
      },
      {
        label: 'Body (Cuerpo)',
        route: '/general/body',
        icon: 'fitness_center',
        isPremium: true,
      },
      {
        label: 'Soul (Alma)',
        route: '/general/soul',
        icon: 'self_improvement',
        isPremium: true,
      },
      {
        label: 'Actualizar a Premium',
        route: '/upgrade',
        icon: 'star',
        badge: 'Nuevo',
      },
    ];
  }
}
