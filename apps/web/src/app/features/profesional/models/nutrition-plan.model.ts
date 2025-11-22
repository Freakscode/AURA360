export interface NutritionPlan {
  id: string;
  auth_user_id: string;
  title: string;
  language: string;
  issued_at: string; // Date string YYYY-MM-DD
  valid_until: string; // Date string YYYY-MM-DD
  is_active: boolean;
  is_valid: boolean;
  plan_data: PlanData;
  created_at: string;
  updated_at: string;
}

export interface PlanData {
  plan: PlanMetadata;
  subject: PlanSubject;
  assessment: PlanAssessment;
  directives: PlanDirectives;
  supplements?: PlanSupplement[];
  recommendations?: string[];
  activity_guidance?: string;
  free_text?: Record<string, string>;
}

export interface PlanMetadata {
  title: string;
  version: string;
  issued_at: string;
  valid_until: string;
  language: string;
  units: {
    mass: 'kg' | 'lb';
    volume: 'ml' | 'l' | 'cup';
    energy: 'kcal' | 'kj';
  };
  source: {
    kind: 'pdf' | 'image' | 'text' | 'web';
    uri?: string;
    extracted_at?: string;
    extractor?: string;
  };
}

export interface PlanSubject {
  user_id?: string;
  name: string;
  demographics: {
    sex: 'M' | 'F';
    age_years: number;
    height_cm: number;
    weight_kg: number;
  };
}

export interface PlanAssessment {
  timeseries?: any[]; // Simplified for now
  diagnoses?: {
    label: string;
    severity?: string;
    notes?: string;
  }[];
  goals: {
    target: string;
    value: number;
    unit: string;
    due_date?: string;
    notes?: string;
  }[];
}

export interface PlanDirectives {
  weekly_frequency?: {
    min_days_per_week: number;
    notes?: string;
  };
  restrictions?: {
    target: string;
    rule: 'forbidden' | 'limited' | 'free';
    details?: string;
  }[];
  meals: PlanMeal[];
  substitutions?: any[];
}

export interface PlanMeal {
  name: string;
  time_window?: string;
  components: {
    group: string;
    quantity: {
      portions?: number;
      unit?: string;
      value?: number;
      notes?: string;
    };
    must_present?: boolean;
  }[];
  notes?: string;
}

export interface PlanSupplement {
  name: string;
  dose: string;
  timing: string;
  notes?: string;
}

