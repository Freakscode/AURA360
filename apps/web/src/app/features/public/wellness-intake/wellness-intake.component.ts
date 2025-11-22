import { CommonModule } from '@angular/common';
import {
  Component,
  OnDestroy,
} from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { Subscription, EMPTY, timer } from 'rxjs';
import { catchError, switchMap, takeWhile } from 'rxjs/operators';

import { WELLNESS_INTAKE_SECTIONS } from './intake-question.config';
import {
  CreateIntakeSubmissionRequest,
  IntakeQuestionId,
  IntakeSectionKey,
  IntakeSubmissionResponse,
  IntakeSubmissionStatus,
} from './models/wellness-intake.models';
import { WellnessIntakeService } from './services/wellness-intake.service';

const requireSelection = (control: AbstractControl): ValidationErrors | null => {
  const value = (control.value as string[]) ?? [];
  return value.length ? null : { required: true };
};

@Component({
  standalone: true,
  selector: 'app-wellness-intake',
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './wellness-intake.component.html',
  styleUrls: ['./wellness-intake.component.scss'],
})
export class WellnessIntakeComponent implements OnDestroy {
  protected readonly sections = WELLNESS_INTAKE_SECTIONS;
  protected readonly steps = [...this.sections.map((section) => section.key), 'summary'] as const;

  protected currentStepIndex = 0;
  protected status: 'idle' | 'submitting' | 'processing' | 'ready' | 'error' | 'pending' = 'idle';
  protected statusMessage = '';
  protected submission: IntakeSubmissionResponse | null = null;

  private pollSub: Subscription | null = null;

  protected form!: FormGroup;

  constructor(
    private readonly fb: FormBuilder,
    private readonly intakeService: WellnessIntakeService,
  ) {
    this.form = this.fb.group({
      physical: this.fb.group({
        F1: this.fb.control<string | null>(null, Validators.required),
        F2: this.fb.control<string | null>(null, Validators.required),
        F3: this.fb.group({
          frequency: this.fb.control<string | null>(null, Validators.required),
          consulted_professional: this.fb.control<boolean>(false),
        }),
        F4: this.fb.group({
          selected: this.fb.control<string[]>([], requireSelection),
          otherText: this.fb.control<string>(''),
        }),
      }),
      mental: this.fb.group({
        M1: this.fb.control<string | null>(null, Validators.required),
        M2: this.fb.group({
          selected: this.fb.control<string[]>([], requireSelection),
          otherText: this.fb.control<string>(''),
        }),
        M3: this.fb.control<string | null>(null, Validators.required),
        M4: this.fb.group({
          has_strategies: this.fb.control<boolean | null>(null, Validators.required),
          strategies: this.fb.group({
            selected: this.fb.control<string[]>([]),
            otherText: this.fb.control<string>(''),
          }),
        }),
      }),
      spiritual: this.fb.group({
        S1: this.fb.control<string | null>(null, Validators.required),
        S2: this.fb.group({
          selected: this.fb.control<string[]>([], requireSelection),
        }),
        S3: this.fb.control<string | null>(null, Validators.required),
        S4: this.fb.group({
          has_guide: this.fb.control<boolean | null>(null, Validators.required),
          guide_type: this.fb.control<string>(''),
        }),
      }),
      freeText: this.fb.control<string>('', [Validators.maxLength(280)]),
    });
  }

  ngOnDestroy(): void {
    this.stopPolling();
  }

  protected get currentStepKey(): string {
    return this.steps[this.currentStepIndex];
  }

  protected stepLabel(step: string): string {
    if (step === 'summary') {
      return 'Resumen';
    }
    const section = this.sections.find((item) => item.key === step);
    return section?.title ?? step;
  }

  protected questionOptions(section: IntakeSectionKey, questionId: string) {
    return (
      this.sections
        .find((config) => config.key === section)
        ?.questions.find((question) => question.id === questionId)?.options ?? []
    );
  }

  protected questionDescription(section: IntakeSectionKey, questionId: string): string | undefined {
    return this.sections
      .find((config) => config.key === section)
      ?.questions.find((question) => question.id === questionId)?.description;
  }

  protected isFirstStep(): boolean {
    return this.currentStepIndex === 0;
  }

  protected isLastStep(): boolean {
    return this.currentStepIndex === this.steps.length - 1;
  }

  protected goToStep(index: number): void {
    if (index < 0 || index >= this.steps.length) {
      return;
    }
    this.currentStepIndex = index;
  }

  protected nextStep(): void {
    if (this.isLastStep()) {
      return;
    }
    const sectionKey = this.steps[this.currentStepIndex] as IntakeSectionKey;
    if (!this.validateSection(sectionKey)) {
      return;
    }
    this.currentStepIndex += 1;
  }

  protected previousStep(): void {
    if (this.isFirstStep()) {
      return;
    }
    this.currentStepIndex -= 1;
  }

  protected onSubmit(): void {
    if (!this.validateEntireForm()) {
      this.status = 'error';
      this.statusMessage = 'Revisa las preguntas pendientes antes de continuar.';
      return;
    }

    const payload = this.buildPayload();
    this.status = 'submitting';
    this.statusMessage = 'Estamos registrando tu información inicial...';
    this.form.disable();

    this.intakeService
      .createSubmission(payload)
      .pipe(
        catchError((error) => {
          this.status = 'error';
          this.statusMessage =
            error?.error?.detail ?? 'No pudimos enviar el formulario. Intenta nuevamente.';
          this.form.enable();
          return EMPTY;
        })
      )
      .subscribe((submission) => {
        this.submission = submission;
        this.status = this.mapStatus(submission.status);
        this.statusMessage = this.status === 'ready'
          ? '¡Listo! Tu reporte personalizado está disponible.'
          : 'Procesando tu contexto para generar recomendaciones personalizadas.';

        if (submission.id) {
          if (submission.status === 'ready' || submission.status === 'failed') {
            this.form.enable();
          } else {
            this.startPolling(submission.id);
          }
        }
      });
  }

  protected toggleMultiSelection(
    section: IntakeSectionKey,
    question: 'F4' | 'M2' | 'S2',
    option: string,
    exclusive = false,
  ): void {
    const control = this.getSectionGroup(section)
      .get(`${question}.selected`);
    
    if (!control) {
      return;
    }

    const formControl = control as FormControl<string[]>;
    const current = formControl.value ?? [];
    let next: string[];

    if (exclusive) {
      next = current.includes(option) ? [] : [option];
    } else {
      if (current.includes(option)) {
        next = current.filter((value: string) => value !== option);
      } else {
        next = current.filter((value: string) => value !== 'none');
        next = [...next, option];
      }
    }

    formControl.setValue(next);
    formControl.markAsDirty();
    formControl.updateValueAndValidity();
  }

  protected multiSelected(
    section: IntakeSectionKey,
    question: 'F4' | 'M2' | 'S2',
  ): string[] {
    return (
      (this.getSectionGroup(section).get(`${question}.selected`) as FormControl<string[]>).value ?? []
    );
  }

  protected hasSelectedOther(section: IntakeSectionKey, question: 'F4' | 'M2'): boolean {
    return this.multiSelected(section, question).includes('other');
  }

  protected toggleStrategy(option: string): void {
    const control = this.form.get('mental.M4.strategies.selected') as FormControl<string[]>;
    const current = control.value ?? [];
    const exists = current.includes(option);
    const next = exists ? current.filter((value) => value !== option) : [...current, option];
    control.setValue(next);
    control.markAsDirty();
    if (!next.includes('other')) {
      const otherControl = this.form.get('mental.M4.strategies.otherText') as FormControl<string>;
      otherControl.setValue('');
    }
    control.updateValueAndValidity();
  }

  protected shouldDisableActions(): boolean {
    return this.status === 'submitting' || this.status === 'processing';
  }

  protected groupInvalid(section: IntakeSectionKey, controlPath: string): boolean {
    const control = this.getSectionGroup(section).get(controlPath);
    return !!control && control.invalid && (control.dirty || control.touched);
  }

  protected selectedGuide(section: IntakeSectionKey, question: 'S4'): string | null {
    const value = this.getSectionGroup(section).get(`${question}.guide_type`)?.value;
    return value || null;
  }

  private validateEntireForm(): boolean {
    let valid = true;
    (['physical', 'mental', 'spiritual'] as IntakeSectionKey[]).forEach((key) => {
      valid = this.validateSection(key) && valid;
    });
    return valid;
  }

  private validateSection(section: IntakeSectionKey): boolean {
    const group = this.getSectionGroup(section);
    this.touchGroup(group);
    this.ensureCompoundConsistency(section);
    return group.valid;
  }

  private getSectionGroup(section: IntakeSectionKey): FormGroup {
    return this.form.get(section) as FormGroup;
  }

  private touchGroup(group: FormGroup): void {
    Object.values(group.controls).forEach((control) => {
      if (control instanceof FormGroup) {
        this.touchGroup(control);
      } else {
        control.markAsTouched();
      }
    });
  }

  private ensureCompoundConsistency(section: IntakeSectionKey): void {
    if (section === 'mental') {
      const m4 = this.getSectionGroup('mental').get('M4') as FormGroup;
      const hasStrategies = !!m4.get('has_strategies')?.value;
      const strategiesSelectedControl = m4.get('strategies.selected') as FormControl<string[]>;
      const otherTextControl = m4.get('strategies.otherText') as FormControl<string>;
      const selections = strategiesSelectedControl.value ?? [];
      if (hasStrategies && selections.length === 0) {
        strategiesSelectedControl.setErrors({ required: true });
      } else if (hasStrategies) {
        strategiesSelectedControl.setErrors(null);
      }
      if (!hasStrategies) {
        strategiesSelectedControl.setValue([]);
        otherTextControl.setValue('');
        strategiesSelectedControl.setErrors(null);
      }
    }

    if (section === 'spiritual') {
      const s4 = this.getSectionGroup('spiritual').get('S4') as FormGroup;
      const hasGuide = !!s4.get('has_guide')?.value;
      const guideTypeControl = s4.get('guide_type') as FormControl<string>;
      if (!hasGuide) {
        guideTypeControl.setValue('');
        guideTypeControl.setErrors(null);
      } else if (!guideTypeControl.value) {
        guideTypeControl.setErrors({ required: true });
      } else {
        guideTypeControl.setErrors(null);
      }
    }
  }

  private buildPayload(): CreateIntakeSubmissionRequest {
    const physical = this.getSectionGroup('physical');
    const mental = this.getSectionGroup('mental');
    const spiritual = this.getSectionGroup('spiritual');

    const f4Group = physical.get('F4') as FormGroup;
    const f4Selected = (f4Group.get('selected')?.value ?? []) as string[];
    const f4OtherText = (f4Group.get('otherText')?.value ?? '').trim();

    const m2Group = mental.get('M2') as FormGroup;
    const m2Selected = (m2Group.get('selected')?.value ?? []) as string[];
    const m2OtherText = (m2Group.get('otherText')?.value ?? '').trim();

    const m4Group = mental.get('M4') as FormGroup;
    const hasStrategies = !!m4Group.get('has_strategies')?.value;
    const strategiesSelected = (
      m4Group.get('strategies.selected')?.value ?? []
    ) as string[];
    const strategiesOther = (m4Group.get('strategies.otherText')?.value ?? '').trim();

    const s2Group = spiritual.get('S2') as FormGroup;
    const s2Selected = (s2Group.get('selected')?.value ?? []) as string[];

    const s4Group = spiritual.get('S4') as FormGroup;
    const hasGuide = !!s4Group.get('has_guide')?.value;
    const guideType = (s4Group.get('guide_type')?.value ?? '').trim();

    const freeText = (this.form.get('freeText')?.value ?? '').trim();

    const answers: Array<{ question_id: IntakeQuestionId; value: unknown }> = [
      { question_id: 'F1' as const, value: physical.get('F1')?.value },
      { question_id: 'F2' as const, value: physical.get('F2')?.value },
      {
        question_id: 'F3' as const,
        value: {
          frequency: (physical.get('F3.frequency')?.value ?? null),
          consulted_professional: !!physical.get('F3.consulted_professional')?.value,
        },
      },
      {
        question_id: 'F4' as const,
        value: {
          selected: f4Selected,
          ...(f4OtherText ? { other_text: f4OtherText } : {}),
        },
      },
      { question_id: 'M1' as const, value: mental.get('M1')?.value },
      {
        question_id: 'M2' as const,
        value: {
          selected: m2Selected,
          ...(m2OtherText ? { other_text: m2OtherText } : {}),
        },
      },
      { question_id: 'M3' as const, value: mental.get('M3')?.value },
      {
        question_id: 'M4' as const,
        value: hasStrategies
          ? {
              has_strategies: true,
              strategies: {
                selected: strategiesSelected,
                ...(strategiesOther ? { other_text: strategiesOther } : {}),
              },
            }
          : { has_strategies: false },
      },
      { question_id: 'S1' as const, value: spiritual.get('S1')?.value },
      {
        question_id: 'S2' as const,
        value: {
          selected: s2Selected,
        },
      },
      { question_id: 'S3' as const, value: spiritual.get('S3')?.value },
      {
        question_id: 'S4' as const,
        value: hasGuide
          ? {
              has_guide: true,
              guide_type: guideType,
            }
          : { has_guide: false },
      },
    ];

    return {
      answers,
      free_text: freeText,
      vectorize_snapshot: true,
    } satisfies CreateIntakeSubmissionRequest;
  }

  private startPolling(submissionId: string): void {
    this.stopPolling();
    this.status = 'processing';
    this.statusMessage = 'Estamos procesando tu información, esto puede tardar menos de un minuto.';

    this.pollSub = timer(5000, 5000)
      .pipe(
        switchMap(() => this.intakeService.getSubmission(submissionId)),
        takeWhile((submission) => submission.status === 'pending' || submission.status === 'processing', true),
        catchError((error) => {
          this.status = 'error';
          this.statusMessage = error?.error?.detail ?? 'No pudimos actualizar el estado del formulario.';
          this.form.enable();
          return EMPTY;
        })
      )
      .subscribe((submission) => {
        this.submission = submission;
        this.status = this.mapStatus(submission.status);

        if (submission.status === 'ready') {
          this.statusMessage = submission.report_url
            ? 'Tu reporte personalizado está listo. Descárgalo y compártelo cuando quieras.'
            : 'Tu reporte ha sido generado.';
          this.form.enable();
          this.stopPolling();
        } else if (submission.status === 'failed') {
          this.status = 'error';
          this.statusMessage =
            submission.failure_reason ?? 'Ocurrió un problema procesando tu reporte. Intenta de nuevo.';
          this.form.enable();
          this.stopPolling();
        }
      });
  }

  private stopPolling(): void {
    this.pollSub?.unsubscribe();
    this.pollSub = null;
  }

  private mapStatus(status: IntakeSubmissionStatus): 'idle' | 'submitting' | 'processing' | 'ready' | 'error' | 'pending' {
    if (status === 'ready') {
      return 'ready';
    }
    if (status === 'failed') {
      return 'error';
    }
    if (status === 'processing') {
      return 'processing';
    }
    if (status === 'pending') {
      return 'pending';
    }
    return 'idle';
  }
}
