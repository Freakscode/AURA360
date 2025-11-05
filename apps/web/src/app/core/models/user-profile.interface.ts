import { GlobalRole } from './global-role.enum';
import { UserTier } from './user-tier.enum';
import { BillingPlan } from './billing-plan.enum';

/**
 * Interfaz para perfil de usuario completo
 * Mapea a la tabla public.app_users de Supabase
 */
export interface UserProfile {
  id: number;
  auth_user_id: string;
  full_name: string;
  age: number;
  email: string;
  phone_number: string | null;
  gender: string | null;

  // RBAC fields
  tier: UserTier;
  role_global: GlobalRole;
  is_independent: boolean;
  billing_plan: BillingPlan;

  // Timestamps
  created_at: string;
  updated_at: string;
}

/**
 * DTO para crear perfil de usuario
 */
export interface CreateUserProfileDto {
  auth_user_id: string;
  full_name: string;
  age: number;
  email: string;
  phone_number?: string;
  gender?: string;
  tier?: UserTier;
  role_global?: GlobalRole;
  is_independent?: boolean;
  billing_plan?: BillingPlan;
}

/**
 * DTO para actualizar perfil de usuario
 */
export interface UpdateUserProfileDto extends Partial<Omit<CreateUserProfileDto, 'auth_user_id' | 'email'>> {
  id: number;
}

/**
 * Interfaz para datos mínimos de usuario en JWT
 */
export interface UserJwtPayload {
  sub: string; // auth_user_id
  email: string;
  role: string; // authenticated | anon
  app_metadata?: {
    role_global?: string;
    tier?: string;
    billing_plan?: string;
  };
  user_metadata?: {
    role_global?: string;
    tier?: string;
    billing_plan?: string;
    full_name?: string;
  };
}
