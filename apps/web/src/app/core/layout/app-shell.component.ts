import { Component, computed, signal, inject, viewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { MatSidenavModule, MatSidenav } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatMenuModule } from '@angular/material/menu';
import { MatBadgeModule } from '@angular/material/badge';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatRippleModule } from '@angular/material/core';

import { AuthSessionStore } from '../../features/auth/services/auth-session.store';
import { AuthService } from '../../features/auth/services/auth.service';
import { NavigationMenuService } from '../services/navigation-menu.service';
import { ActiveContextService } from '../services/active-context.service';
import { PermissionService } from '../services/permission.service';
import { ContextSwitcherComponent } from '../../shared/components/context-switcher/context-switcher.component';
import { GLOBAL_ROLE_LABELS } from '../models/global-role.enum';
import { INSTITUTION_ROLE_LABELS } from '../models/institution-role.enum';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatSidenavModule,
    MatToolbarModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatMenuModule,
    MatBadgeModule,
    MatTooltipModule,
    MatRippleModule,
    ContextSwitcherComponent,
  ],
  templateUrl: './app-shell.component.html',
  styleUrl: './app-shell.component.scss',
  host: {
    class: 'app-shell',
  },
})
export class AppShellComponent {
  private readonly authSessionStore = inject(AuthSessionStore);
  private readonly authService = inject(AuthService);
  private readonly navigationMenuService = inject(NavigationMenuService);
  private readonly activeContextService = inject(ActiveContextService);
  private readonly permissionService = inject(PermissionService);
  private readonly router = inject(Router);

  // ViewChild to control sidenav programmatically if needed (e.g. on mobile navigation)
  // protected readonly sidenav = viewChild<MatSidenav>('sidenav');

  constructor() {
    console.debug('[AppShell] init');
  }

  // UI State
  // SideNav open state: start open on desktop, closed on mobile (responsive logic can be added via BreakpointObserver)
  protected readonly isSideNavOpen = signal(true);
  protected readonly notificationsCount = signal(3);

  // Auth Data
  readonly user = this.authSessionStore.user;
  readonly activeContext = this.activeContextService.activeContext;

  // Navigation Items
  readonly menuItems = this.navigationMenuService.menuItems;

  // User Info Computed
  readonly userName = computed(() => {
    const fullName = this.authSessionStore.userFullName();
    if (fullName) return fullName;

    const email = this.authSessionStore.userEmail();
    return email || 'Usuario';
  });

  readonly userRole = computed(() => {
    const context = this.activeContext();
    if (!context) return 'Sin rol';

    // Prioritize institutional role if exists
    if (context.institutionRole) {
      return INSTITUTION_ROLE_LABELS[context.institutionRole];
    }

    return GLOBAL_ROLE_LABELS[context.globalRole];
  });

  readonly userInitials = computed(() => {
    return this.userName()
      .split(' ')
      .filter((part: string) => part.length > 0)
      .slice(0, 2)
      .map((part: string) => part[0]?.toUpperCase())
      .join('');
  });

  readonly hasContexts = computed(() => {
    return this.activeContextService.availableContexts().length > 0;
  });

  // Actions
  toggleSideNav(): void {
    this.isSideNavOpen.update((open) => !open);
  }

  async logout(): Promise<void> {
    await this.authService.logout();
  }

  navigateToProfile(): void {
    this.router.navigate(['/profile']);
  }

  navigateToSettings(): void {
    this.router.navigate(['/settings']);
  }
}