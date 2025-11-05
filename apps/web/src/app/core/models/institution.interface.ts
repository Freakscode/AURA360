/**
 * Interfaz para datos de institución
 * Mapea a la tabla public.institutions de Supabase
 */
export interface Institution {
  id: number;
  name: string;
  slug: string | null;
  is_healthcare: boolean;
  business_tier: string;
  metadata: Record<string, any>;
  billing_email: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * DTO para creación de institución
 */
export interface CreateInstitutionDto {
  name: string;
  slug?: string;
  is_healthcare?: boolean;
  business_tier?: string;
  metadata?: Record<string, any>;
  billing_email?: string;
}

/**
 * DTO para actualización de institución
 */
export interface UpdateInstitutionDto extends Partial<CreateInstitutionDto> {
  id: number;
}
