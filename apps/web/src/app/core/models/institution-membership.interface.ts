import { InstitutionRole } from './institution-role.enum';
import { Institution } from './institution.interface';

/**
 * Estado de membresía institucional
 */
export enum MembershipStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
}

/**
 * Interfaz para membresía institución-usuario
 * Mapea a la tabla public.institution_memberships de Supabase
 */
export interface InstitutionMembership {
  id: number;
  institution_id: number;
  user_id: number;
  role_institution: InstitutionRole;
  is_primary: boolean;
  status: MembershipStatus;
  started_at: string;
  ended_at: string | null;
  created_at: string;
  updated_at: string;

  // Relaciones expandidas (opcional)
  institution?: Institution;
}

/**
 * DTO para creación de membresía
 */
export interface CreateMembershipDto {
  institution_id: number;
  user_id: number;
  role_institution: InstitutionRole;
  is_primary?: boolean;
  status?: MembershipStatus;
  started_at?: string;
}

/**
 * DTO para actualización de membresía
 */
export interface UpdateMembershipDto extends Partial<CreateMembershipDto> {
  id: number;
  ended_at?: string | null;
}

/**
 * Labels para estados de membresía
 */
export const MEMBERSHIP_STATUS_LABELS: Record<MembershipStatus, string> = {
  [MembershipStatus.ACTIVE]: 'Activa',
  [MembershipStatus.INACTIVE]: 'Inactiva',
  [MembershipStatus.SUSPENDED]: 'Suspendida',
};
