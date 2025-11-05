/**
 * Componente de login para AURA360
 * Maneja la autenticación de usuarios con formulario reactivo y validaciones
 * 
 * @module LoginComponent
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, computed, inject, signal, type Signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { AbstractControl, FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { startWith } from 'rxjs';

import { AuthService } from '../services/auth.service';
import { AuthSessionStore } from '../services/auth-session.store';
import { INITIAL_LOGIN_STATE, type LoginState } from './models/login-state.model';
import { LOGIN_VALIDATION_RULES } from './models/login-form.model';
import type { AuthError } from '../models/auth-error.model';

/**
 * Controles tipados del formulario de login
 */
interface LoginFormControls {
  email: FormControl<string>;
  password: FormControl<string>;
  rememberMe: FormControl<boolean>;
}

/**
 * Componente de login standalone con formulario reactivo, validaciones y estados de carga.
 * Implementa el flujo completo de autenticación con Supabase y redirección por rol.
 */
@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterModule
  ],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent implements OnInit, OnDestroy {
  // Servicios inyectados
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly authSessionStore = inject(AuthSessionStore);

  // Signals para estado reactivo
  private readonly state = signal<LoginState>(INITIAL_LOGIN_STATE);
  private formStatus!: Signal<string>;
  
  // Signal para controlar la visibilidad del password
  private readonly _showPassword = signal<boolean>(false);

  // Computed signals públicos para el template
  readonly status = computed(() => this.state().status);
  readonly error = computed(() => this.state().error);
  readonly isSubmitting = computed(() => this.state().isSubmitting);
  readonly showPassword = this._showPassword.asReadonly();
  
  /**
   * Indica si el formulario puede ser enviado
   */
  readonly canSubmit = computed(() => {
    const status = this.formStatus();
    return status === 'VALID' && this.loginForm.enabled && !this.isSubmitting();
  });

  /**
   * FormGroup tipado con controles de email, password y rememberMe
   */
  readonly loginForm!: FormGroup<LoginFormControls>;

  constructor() {
    // Construir formulario en el constructor
    this.loginForm = this.buildForm();
    this.formStatus = toSignal(
      this.loginForm.statusChanges.pipe(startWith(this.loginForm.status)),
      { initialValue: this.loginForm.status }
    );
  }

  ngOnInit(): void {
    // Verificar si ya hay una sesión activa
    if (this.authSessionStore.isAuthenticated()) {
      this.handleExistingSession();
    }
  }

  ngOnDestroy(): void {
    // Cleanup si es necesario
  }

  /**
   * Maneja el envío del formulario de login
   */
  async onSubmit(): Promise<void> {
    console.log('[LoginComponent] onSubmit called');

    // Validar formulario
    if (this.loginForm.invalid) {
      console.log('[LoginComponent] Form is invalid');
      this.markFormAsTouched();
      return;
    }

    // Limpiar errores previos
    this.clearError();

    // Establecer estado de carga
    this.setState({
      status: 'loading',
      isSubmitting: true,
      error: null,
      rememberMe: this.loginForm.value.rememberMe ?? false
    });

    try {
      // Extraer credenciales del formulario
      const credentials = {
        email: this.loginForm.value.email!,
        password: this.loginForm.value.password!
      };
      console.log('[LoginComponent] Attempting login with email:', credentials.email);

      const options = {
        rememberMe: this.loginForm.value.rememberMe ?? false
      };

      // Llamar al servicio de autenticación
      const loginResult = await this.authService.login(credentials, options);
      console.log('[LoginComponent] Login successful');

      // Actualizar estado a éxito
      this.setState({
        status: 'success',
        isSubmitting: false,
        error: null,
        rememberMe: loginResult.shouldRemember
      });

      // Obtener perfil del usuario
      await this.handleLoginSuccess();

    } catch (error) {
      console.error('[LoginComponent] Login failed:', error);
      this.handleLoginError(error);
    }
  }

  /**
   * Obtiene el mensaje de error para un campo del formulario
   * 
   * @param fieldName - Nombre del campo del formulario
   * @returns Mensaje de error o null si no hay error
   */
  getFieldError(fieldName: keyof LoginFormControls): string | null {
    const control = this.loginForm.controls[fieldName];
    
    if (!control.touched || !control.errors) {
      return null;
    }

    return this.getErrorMessage(control, fieldName);
  }

  /**
   * Verifica si un campo del formulario es inválido y debe mostrar error
   * 
   * @param fieldName - Nombre del campo del formulario
   * @returns true si el campo debe mostrar error
   */
  isFieldInvalid(fieldName: keyof LoginFormControls): boolean {
    const control = this.loginForm.controls[fieldName];
    return control.invalid && control.touched;
  }

  /**
   * Limpia el error del estado
   */
  clearError(): void {
    this.setState({
      ...this.state(),
      error: null
    });
  }

  /**
   * Alterna la visibilidad del password
   */
  togglePasswordVisibility(): void {
    if (this.loginForm.disabled) {
      return;
    }

    this._showPassword.update(value => !value);
  }

  // Métodos privados

  /**
   * Construye el FormGroup tipado con validaciones
   */
  private buildForm(): FormGroup<LoginFormControls> {
    return new FormGroup<LoginFormControls>({
      email: new FormControl('', {
        nonNullable: true,
        validators: [
          Validators.required,
          Validators.email,
          Validators.maxLength(LOGIN_VALIDATION_RULES.email.maxLength)
        ]
      }),
      password: new FormControl('', {
        nonNullable: true,
        validators: [
          Validators.required,
          Validators.minLength(LOGIN_VALIDATION_RULES.password.minLength),
          Validators.maxLength(LOGIN_VALIDATION_RULES.password.maxLength)
        ]
      }),
      rememberMe: new FormControl(false, {
        nonNullable: true
      })
    });
  }

  /**
   * Obtiene el mensaje de error para un control del formulario
   * 
   * @param control - Control del formulario
   * @param fieldName - Nombre del campo
   * @returns Mensaje de error
   */
  private getErrorMessage(control: AbstractControl, fieldName: string): string | null {
    const errors = control.errors;
    if (!errors) return null;

    if (errors['required']) {
      return fieldName === 'email' ? 'El email es requerido' : 'La contraseña es requerida';
    }

    if (errors['email']) {
      return 'Ingresa un email válido';
    }

    if (errors['minlength']) {
      const minLength = errors['minlength'].requiredLength;
      return `Debe tener al menos ${minLength} caracteres`;
    }

    if (errors['maxlength']) {
      const maxLength = errors['maxlength'].requiredLength;
      return `No puede exceder ${maxLength} caracteres`;
    }

    return 'Campo inválido';
  }

  /**
   * Marca todos los campos del formulario como touched para mostrar errores
   */
  private markFormAsTouched(): void {
    Object.values(this.loginForm.controls).forEach(control => {
      control.markAsTouched();
    });
  }

  /**
   * Actualiza el estado del componente
   * 
   * @param newState - Nuevo estado parcial o completo
   */
  private setState(newState: Partial<LoginState>): void {
    this.state.update(current => {
      const nextState = {
        ...current,
        ...newState
      };

      if (current.isSubmitting !== nextState.isSubmitting) {
        this.updateFormDisabledState(nextState.isSubmitting);
      }

      return nextState;
    });
  }

  private updateFormDisabledState(shouldDisable: boolean): void {
    if (shouldDisable) {
      if (!this.loginForm.disabled) {
        this.loginForm.disable({ emitEvent: false });
      }
      return;
    }

    if (this.loginForm.disabled) {
      this.loginForm.enable({ emitEvent: false });
    }
  }

  /**
   * Maneja el éxito del login, obteniendo el perfil y redirigiendo
   */
  private async handleLoginSuccess(): Promise<void> {
    try {
      // Establecer estado de redirección
      this.setState({
        status: 'redirecting',
        isSubmitting: true
      });

      // Obtener rol desde el store (ya cargado desde Supabase metadata)
      const role = this.authSessionStore.userRole();
      console.log('[LoginComponent] User role from store:', role);

      if (!role) {
        console.error('[LoginComponent] No role found for user');
        throw new Error('No se pudo determinar el rol del usuario');
      }

      // Navegar según el rol
      console.log('[LoginComponent] Navigating to role-based route');
      this.navigateByRole(role);

    } catch (error) {
      // Error al obtener perfil, limpiar sesión y mostrar error
      await this.authService.logout();

      const authError: AuthError = {
        type: 'profile_fetch_failed',
        message: 'No se pudo cargar tu perfil. Por favor intenta iniciar sesión nuevamente.',
        canRetry: true
      };

      this.setState({
        status: 'error',
        isSubmitting: false,
        error: authError
      });
    }
  }

  /**
   * Maneja errores durante el proceso de login
   * 
   * @param error - Error capturado
   */
  private handleLoginError(error: any): void {
    const authError = error as AuthError;

    this.setState({
      status: 'error',
      isSubmitting: false,
      error: authError
    });
  }

  /**
   * Navega al dashboard apropiado según el rol del usuario
   *
   * @param role - Rol global del usuario
   */
  private navigateByRole(role: string): void {
    const roleRoutes: Record<string, string> = {
      'AdminSistema': '/admin-sistema',
      'AdminInstitucion': '/admin-institucion',
      'AdminInstitucionSalud': '/admin-salud',
      'ProfesionalSalud': '/profesional',
      'Paciente': '/paciente',
      'General': '/general'
    };

    const targetRoute = roleRoutes[role] ?? '/general';
    console.log('[LoginComponent] Navigating to:', targetRoute, 'for role:', role);

    this.router.navigate([targetRoute], {
      replaceUrl: true // Reemplazar historial para evitar volver a login
    });
  }

  /**
   * Maneja el caso en que ya existe una sesión activa
   */
  private async handleExistingSession(): Promise<void> {
    const role = this.authSessionStore.userRole();
    if (role) {
      this.navigateByRole(role);
    } else {
      // No hay rol, limpiar sesión para permitir re-login
      this.authSessionStore.clearSession();
    }
  }
}