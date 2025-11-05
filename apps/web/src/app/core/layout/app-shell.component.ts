import { Component, computed, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
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

  constructor() {
    console.debug('[AppShell] init');
  }

  // UI State
  protected readonly isSideNavOpen = signal(true);
  protected readonly notificationsCount = signal(3);
  protected readonly isUserMenuOpen = signal(false);

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

    // Priorizar rol institucional si existe
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

  toggleUserMenu(): void {
    this.isUserMenuOpen.update((open) => !open);
  }

  async logout(): Promise<void> {
    await this.authService.logout();
  }

  navigateToProfile(): void {
    this.isUserMenuOpen.set(false);
    this.router.navigate(['/profile']);
  }

  navigateToSettings(): void {
    this.isUserMenuOpen.set(false);
    this.router.navigate(['/settings']);
  }
}