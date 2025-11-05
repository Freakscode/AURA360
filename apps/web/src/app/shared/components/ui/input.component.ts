import { Component, input, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export type InputSize = 'sm' | 'base' | 'lg';
export type InputType = 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search';

@Component({
  selector: 'ui-input',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="form-group">
      @if (label()) {
        <label [for]="id()" [class.required]="required()">
          {{ label() }}
        </label>
      }

      <div [class]="wrapperClasses()">
        @if (iconLeft()) {
          <span class="input-icon">
            <ng-content select="[slot=icon-left]"></ng-content>
          </span>
        }

        <input
          [id]="id()"
          [type]="type()"
          [value]="value()"
          [placeholder]="placeholder()"
          [disabled]="disabled()"
          [required]="required()"
          [class]="inputClasses()"
          (input)="onInput($event)"
          (blur)="onBlur()"
          (focus)="onFocus()" />

        @if (clearable() && value() && !disabled()) {
          <button
            type="button"
            class="input-clear"
            (click)="onClear()"
            aria-label="Limpiar">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round">
              <circle cx="7" cy="7" r="6"></circle>
              <line x1="9.5" y1="4.5" x2="4.5" y2="9.5"></line>
              <line x1="4.5" y1="4.5" x2="9.5" y2="9.5"></line>
            </svg>
          </button>
        }

        @if (iconRight()) {
          <span class="input-icon input-icon--right">
            <ng-content select="[slot=icon-right]"></ng-content>
          </span>
        }
      </div>

      @if (hint() && !error()) {
        <span class="form-hint">{{ hint() }}</span>
      }

      @if (error()) {
        <span class="form-error">{{ error() }}</span>
      }
    </div>
  `,
  styles: [
    `
      .input-clear {
        position: absolute;
        right: 0.75rem;
        top: 50%;
        transform: translateY(-50%);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0.25rem;
        border: none;
        background: transparent;
        color: #6b7280;
        cursor: pointer;
        transition: color 0.2s;
        z-index: 10;

        &:hover {
          color: #374151;
        }

        svg {
          width: 14px;
          height: 14px;
        }
      }
    `,
  ],
})
export class InputComponent {
  // Inputs
  readonly id = input<string>(`input-${Math.random().toString(36).substr(2, 9)}`);
  readonly type = input<InputType>('text');
  readonly label = input<string>('');
  readonly value = input<string>('');
  readonly placeholder = input<string>('');
  readonly hint = input<string>('');
  readonly error = input<string>('');
  readonly size = input<InputSize>('base');
  readonly disabled = input<boolean>(false);
  readonly required = input<boolean>(false);
  readonly iconLeft = input<boolean>(false);
  readonly iconRight = input<boolean>(false);
  readonly clearable = input<boolean>(false);

  // Outputs
  readonly valueChange = output<string>();
  readonly blurred = output<void>();
  readonly focused = output<void>();

  // Internal state
  readonly isFocused = signal(false);

  wrapperClasses(): string {
    if (this.iconLeft() || this.iconRight()) {
      return 'input-group';
    }
    return '';
  }

  inputClasses(): string {
    const classes = ['form-input'];

    // Size
    if (this.size() !== 'base') {
      classes.push(`form-input--${this.size()}`);
    }

    // State
    if (this.error()) {
      classes.push('error');
    }

    // Icons
    if (this.iconLeft()) {
      classes.push('has-icon-left');
    }
    if (this.iconRight()) {
      classes.push('has-icon-right');
    }

    return classes.join(' ');
  }

  onInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.valueChange.emit(input.value);
  }

  onBlur(): void {
    this.isFocused.set(false);
    this.blurred.emit();
  }

  onFocus(): void {
    this.isFocused.set(true);
    this.focused.emit();
  }

  onClear(): void {
    this.valueChange.emit('');
  }
}
