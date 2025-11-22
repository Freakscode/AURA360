/**
 * Roles globales del sistema AURA360
 * Sincronizado con backend/users/models.py GlobalRole
 */
export enum GlobalRole {
  ADMIN_SISTEMA = 'AdminSistema',
  ADMIN_INSTITUCION = 'AdminInstitucion',
  ADMIN_INSTITUCION_SALUD = 'AdminInstitucionSalud',
  PROFESIONAL_SALUD = 'ProfesionalSalud',
  PACIENTE = 'Paciente',
  INSTITUCION = 'Institucion',
  GENERAL = 'General',
}

/**
 * Roles administrativos del sistema
 */
export const ADMIN_ROLES: GlobalRole[] = [
  GlobalRole.ADMIN_SISTEMA,
  GlobalRole.ADMIN_INSTITUCION,
  GlobalRole.ADMIN_INSTITUCION_SALUD,
];

/**
 * Labels legibles para cada rol
 */
export const GLOBAL_ROLE_LABELS: Record<GlobalRole, string> = {
  [GlobalRole.ADMIN_SISTEMA]: 'Admin. Sistema',
  [GlobalRole.ADMIN_INSTITUCION]: 'Admin. Institución',
  [GlobalRole.ADMIN_INSTITUCION_SALUD]: 'Admin. Institución Salud',
  [GlobalRole.PROFESIONAL_SALUD]: 'Profesional Salud',
  [GlobalRole.PACIENTE]: 'Paciente',
  [GlobalRole.INSTITUCION]: 'Institución',
  [GlobalRole.GENERAL]: 'General',
};

/**
 * Verifica si un rol es administrativo
 */
export function isAdminRole(role: GlobalRole | string | null): boolean {
  if (!role) return false;
  return ADMIN_ROLES.includes(role as GlobalRole);
}

/**
 * Verifica si un rol es válido
 */
export function isValidGlobalRole(role: string): role is GlobalRole {
  return Object.values(GlobalRole).includes(role as GlobalRole);
}
