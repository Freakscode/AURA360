export type IntakeQuestionId =
  | 'F1'
  | 'F2'
  | 'F3'
  | 'F4'
  | 'M1'
  | 'M2'
  | 'M3'
  | 'M4'
  | 'S1'
  | 'S2'
  | 'S3'
  | 'S4';

export type IntakeSectionKey = 'physical' | 'mental' | 'spiritual';

export interface IntakeAnswerPayload {
  question_id: IntakeQuestionId;
  value: unknown;
}

export interface CreateIntakeSubmissionRequest {
  answers: IntakeAnswerPayload[];
  free_text?: string;
  vectorize_snapshot?: boolean;
}

export type IntakeSubmissionStatus = 'pending' | 'processing' | 'ready' | 'failed';

export interface IntakeSubmissionResponse {
  id: string;
  trace_id: string;
  status: IntakeSubmissionStatus;
  processing_stage: string;
  answers: Record<string, unknown>;
  free_text: string;
  vectorize_snapshot: boolean;
  estimated_wait_seconds: number;
  report_url?: string | null;
  report_storage_path?: string;
  report_metadata?: Record<string, unknown>;
  failure_reason?: string;
  last_error_at?: string | null;
  created_at: string;
  updated_at: string;
  task_id?: string;
}

export interface IntakeOption {
  readonly value: string;
  readonly label: string;
  readonly helper?: string;
  readonly exclusive?: boolean;
}

export interface IntakeQuestionConfig {
  readonly id: IntakeQuestionId;
  readonly title: string;
  readonly description?: string;
  readonly type: 'likert' | 'single' | 'multi' | 'compound';
  readonly options?: readonly IntakeOption[];
}

export interface IntakeSectionConfig {
  readonly key: IntakeSectionKey;
  readonly title: string;
  readonly description: string;
  readonly questions: readonly IntakeQuestionConfig[];
}
