import { Component, input, output } from '@angular/core';
import { CommonModule } from '@angular/common';

export type BadgeVariant =
  | 'primary'
  | 'secondary'
  | 'success'
  | 'warning'
  | 'error'
  | 'info';

export type BadgeStyle = 'default' | 'solid' | 'outline';
export type BadgeSize = 'sm' | 'base' | 'lg';

@Component({
  selector: 'ui-badge',
  standalone: true,
  imports: [CommonModule],
  template: `
    <span [class]="badgeClasses()" [ngStyle]="badgeStyles()">
      @if (dot()) {
        <span class="badge__dot"></span>
      }
      <ng-content></ng-content>
      @if (dismissible()) {
        <button
          type="button"
          class="badge__close"
          (click)="onDismiss()"
          aria-label="Cerrar">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round">
            <line x1="9" y1="3" x2="3" y2="9"></line>
            <line x1="3" y1="3" x2="9" y2="9"></line>
          </svg>
        </button>
      }
    </span>
  `,
  styles: [
    `
      .badge__dot {
        display: inline-block;
        width: 0.5rem;
        height: 0.5rem;
        border-radius: 9999px;
        background-color: currentColor;
        margin-right: 0.5rem;
      }

      .badge--truncate {
        display: inline-block;
        max-width: 12rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        vertical-align: middle;
      }
    `,
  ],
})
export class BadgeComponent {
  // Inputs
  readonly variant = input<BadgeVariant>('primary');
  readonly style = input<BadgeStyle>('default');
  readonly size = input<BadgeSize>('base');
  readonly dot = input<boolean>(false);
  readonly pill = input<boolean>(false);
  readonly dismissible = input<boolean>(false);
  readonly truncate = input<boolean>(false);
  readonly maxWidth = input<string>('none');

  // Outputs
  readonly dismissed = output<void>();

  badgeClasses(): string {
    const classes = ['badge'];

    // Variant with style
    const stylePrefix = this.style() === 'default' ? '' : `${this.style()}-`;
    classes.push(`badge--${stylePrefix}${this.variant()}`);

    // Size
    if (this.size() !== 'base') {
      classes.push(`badge--${this.size()}`);
    }

    // Modifiers
    if (this.dot()) {
      classes.push('badge--dot');
    }
    if (this.pill()) {
      classes.push('badge--pill');
    }
    if (this.dismissible()) {
      classes.push('badge--dismissible');
    }
    if (this.truncate()) {
      classes.push('badge--truncate');
    }

    return classes.join(' ');
  }

  badgeStyles(): { [key: string]: string } {
    const styles: { [key: string]: string } = {};
    if (this.truncate() && this.maxWidth() !== 'none') {
      styles['max-width'] = this.maxWidth();
    }
    return styles;
  }

  onDismiss(): void {
    this.dismissed.emit();
  }
}
