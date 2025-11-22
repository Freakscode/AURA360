import { Component, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';

export type ButtonVariant =
  | 'primary'
  | 'secondary'
  | 'outline'
  | 'ghost'
  | 'danger'
  | 'success'
  | 'warning'
  | 'link';

export type ButtonSize = 'xs' | 'sm' | 'base' | 'lg' | 'xl';

@Component({
  selector: 'ui-button',
  standalone: true,
  imports: [CommonModule],
  template: `
    <button
      [type]="type()"
      [disabled]="disabled() || loading()"
      [class]="buttonClasses()"
      [attr.aria-label]="ariaLabel()"
      (click)="handleClick($event)">
      @if (loading()) {
        <span class="btn-spinner"></span>
      }
      @if (iconLeft() && !loading()) {
        <ng-content select="[slot=icon-left]"></ng-content>
      }
      <ng-content></ng-content>
      @if (iconRight() && !loading()) {
        <ng-content select="[slot=icon-right]"></ng-content>
      }
    </button>
  `,
  styles: [
    `
      .btn-spinner {
        display: inline-block;
        width: 1rem;
        height: 1rem;
        border: 2px solid currentColor;
        border-radius: 50%;
        border-top-color: transparent;
        animation: spinner 0.6s linear infinite;
      }

      @keyframes spinner {
        to {
          transform: rotate(360deg);
        }
      }
    `,
  ],
})
export class ButtonComponent {
  // Inputs
  readonly variant = input<ButtonVariant>('primary');
  readonly size = input<ButtonSize>('base');
  readonly type = input<'button' | 'submit' | 'reset'>('button');
  readonly disabled = input<boolean>(false);
  readonly loading = input<boolean>(false);
  readonly block = input<boolean>(false);
  readonly rounded = input<boolean>(false);
  readonly square = input<boolean>(false);
  readonly iconLeft = input<boolean>(false);
  readonly iconRight = input<boolean>(false);
  readonly ariaLabel = input<string | undefined>(undefined);

  // Outputs
  readonly clicked = output<MouseEvent>();

  buttonClasses(): string {
    const classes = ['btn'];

    // Variant
    classes.push(`btn--${this.variant()}`);

    // Size
    if (this.size() !== 'base') {
      classes.push(`btn--${this.size()}`);
    }

    // Modifiers
    if (this.block()) classes.push('btn--block');
    if (this.rounded()) classes.push('btn--rounded');
    if (this.square()) classes.push('btn--square');
    if (this.loading()) classes.push('btn--loading');

    return classes.join(' ');
  }

  handleClick(event: MouseEvent): void {
    if (!this.disabled() && !this.loading()) {
      this.clicked.emit(event);
    }
  }
}
