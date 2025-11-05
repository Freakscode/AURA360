/**
 * Modelo para representar una relación de cuidado entre profesional y paciente
 */
export interface CareRelationship {
  id: number;
  professional_user_id: number;
  patient_user_id: number;
  professional_membership_id: number | null;
  patient_membership_id: number | null;
  institution_id: number | null;
  context_type: 'institutional' | 'independent';
  status: 'active' | 'inactive' | 'ended';
  started_at: string;
  ended_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Relación de cuidado con información completa del paciente
 */
export interface CareRelationshipWithPatient extends CareRelationship {
  patient: PatientInfo;
}

/**
 * Información básica del paciente
 */
export interface PatientInfo {
  id: number;
  email: string;
  full_name: string;
  age: number | null;
  gender: string | null;
  phone_number: string | null;
  role_global: string;
}

/**
 * Resumen de pacientes del profesional
 */
export interface PatientsSummary {
  total: number;
  active: number;
  inactive: number;
  patients: CareRelationshipWithPatient[];
}
