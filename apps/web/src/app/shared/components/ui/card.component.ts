import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';

export type CardVariant = 'default' | 'flat' | 'elevated' | 'outlined';
export type CardSize = 'sm' | 'base' | 'lg';
export type CardColor = 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info';

@Component({
  selector: 'ui-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div [class]="cardClasses()">
      @if (loading()) {
        <div class="card__loading">
          <div class="card__skeleton"></div>
          <div class="card__skeleton card__skeleton--short"></div>
          <div class="card__skeleton card__skeleton--medium"></div>
        </div>
      } @else {
        @if (hasHeader()) {
          <div [class]="headerClasses()">
            <ng-content select="[slot=header]"></ng-content>
          </div>
        }

        <div [class]="bodyClasses()">
          <ng-content></ng-content>
        </div>

        @if (hasFooter()) {
          <div [class]="footerClasses()">
            <ng-content select="[slot=footer]"></ng-content>
          </div>
        }
      }
    </div>
  `,
  styles: [
    `
      .card__loading {
        padding: 1.5rem;
      }

      .card__skeleton {
        height: 1rem;
        background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%);
        background-size: 200% 100%;
        animation: loading 1.5s ease-in-out infinite;
        border-radius: 0.25rem;
        margin-bottom: 0.75rem;

        &:last-child {
          margin-bottom: 0;
        }

        &--short {
          width: 40%;
        }

        &--medium {
          width: 70%;
        }
      }

      @keyframes loading {
        0% {
          background-position: 200% 0;
        }
        100% {
          background-position: -200% 0;
        }
      }
    `,
  ],
})
export class CardComponent {
  // Inputs
  readonly variant = input<CardVariant>('default');
  readonly size = input<CardSize>('base');
  readonly color = input<CardColor>('default');
  readonly clickable = input<boolean>(false);
  readonly loading = input<boolean>(false);
  readonly hasHeader = input<boolean>(false);
  readonly hasFooter = input<boolean>(false);
  readonly headerActions = input<boolean>(false);
  readonly footerActions = input<boolean>(false);

  cardClasses(): string {
    const classes = ['card'];

    // Variant
    if (this.variant() !== 'default') {
      classes.push(`card--${this.variant()}`);
    }

    // Color
    if (this.color() !== 'default') {
      classes.push(`card--${this.color()}`);
    }

    // Size
    if (this.size() !== 'base') {
      classes.push(`card--${this.size()}`);
    }

    // Modifiers
    if (this.clickable()) {
      classes.push('card--clickable');
    }
    if (this.loading()) {
      classes.push('card--loading');
    }

    return classes.join(' ');
  }

  headerClasses(): string {
    const classes = ['card__header'];
    if (this.headerActions()) {
      classes.push('card__header--with-actions');
    }
    return classes.join(' ');
  }

  bodyClasses(): string {
    return 'card__body';
  }

  footerClasses(): string {
    const classes = ['card__footer'];
    if (this.footerActions()) {
      classes.push('card__footer--actions');
    }
    return classes.join(' ');
  }
}
