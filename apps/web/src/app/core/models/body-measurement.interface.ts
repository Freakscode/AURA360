export type MeasurementProtocol = 'isak_restricted' | 'isak_full' | 'clinical_basic' | 'elderly_sarcopenia' | 'self_reported';
export type PatientType = 'sedentary' | 'active' | 'athlete' | 'elderly' | 'child';

export interface BodyMeasurement {
  id: string;
  auth_user_id: string;
  recorded_at: string; // ISO Date
  
  // Contexto
  protocol: MeasurementProtocol;
  patient_type: PatientType;
  
  // 1. Medidas Básicas
  weight_kg: number;
  height_cm?: number;
  bmi?: number; // Calculado
  
  // 2. Circunferencias (cm)
  waist_circumference_cm?: number;
  hip_circumference_cm?: number;
  arm_relaxed_circumference_cm?: number;
  arm_flexed_circumference_cm?: number;
  calf_circumference_cm?: number;
  thigh_circumference_cm?: number;
  
  // 3. Pliegues (mm)
  triceps_skinfold_mm?: number;
  biceps_skinfold_mm?: number;
  subscapular_skinfold_mm?: number;
  suprailiac_skinfold_mm?: number;
  abdominal_skinfold_mm?: number;
  thigh_skinfold_mm?: number;
  calf_skinfold_mm?: number;
  
  // 4. Diámetros (mm)
  humerus_breadth_mm?: number;
  femur_breadth_mm?: number;
  wrist_breadth_mm?: number;
  
  // 5. Resultados Calculados
  body_fat_percentage?: number;
  fat_mass_kg?: number;
  muscle_mass_kg?: number;
  muscle_mass_percentage?: number;
  visceral_fat_level?: number;
  
  // Somatotipo
  endomorphy?: number;
  mesomorphy?: number;
  ectomorphy?: number;
  
  // Índices
  waist_hip_ratio?: number;
  waist_height_ratio?: number;
  
  // Metadatos
  notes?: string;
  measured_by?: string;
  photos?: string[];
  
  created_at: string;
  updated_at: string;
}

export interface CreateBodyMeasurementDTO extends Partial<Omit<BodyMeasurement, 'id' | 'created_at' | 'updated_at'>> {
  auth_user_id: string;
  weight_kg: number; // Requerido mínimo
}