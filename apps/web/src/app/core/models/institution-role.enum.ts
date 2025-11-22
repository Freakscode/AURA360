/**
 * Roles específicos de institución
 * Sincronizado con backend institution_memberships tabla
 */
export enum InstitutionRole {
  ADMIN_INSTITUCION = 'AdminInstitucion',
  ADMIN_INSTITUCION_SALUD = 'AdminInstitucionSalud',
  PROFESIONAL_SALUD = 'ProfesionalSalud',
  PACIENTE = 'Paciente',
}

/**
 * Labels legibles para roles institucionales
 */
export const INSTITUTION_ROLE_LABELS: Record<InstitutionRole, string> = {
  [InstitutionRole.ADMIN_INSTITUCION]: 'Admin. Institución',
  [InstitutionRole.ADMIN_INSTITUCION_SALUD]: 'Admin. Institución Salud',
  [InstitutionRole.PROFESIONAL_SALUD]: 'Profesional Salud',
  [InstitutionRole.PACIENTE]: 'Paciente',
};

/**
 * Roles institucionales que son administrativos
 */
export const INSTITUTION_ADMIN_ROLES: InstitutionRole[] = [
  InstitutionRole.ADMIN_INSTITUCION,
  InstitutionRole.ADMIN_INSTITUCION_SALUD,
];

/**
 * Verifica si un rol institucional es válido
 */
export function isValidInstitutionRole(role: string): role is InstitutionRole {
  return Object.values(InstitutionRole).includes(role as InstitutionRole);
}

/**
 * Verifica si un rol institucional es administrativo
 */
export function isInstitutionAdminRole(role: InstitutionRole | string): boolean {
  return INSTITUTION_ADMIN_ROLES.includes(role as InstitutionRole);
}
