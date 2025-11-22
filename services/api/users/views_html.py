"""Vistas HTML básicas para gestionar usuarios por rol."""

from __future__ import annotations

from typing import List

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import Http404
from django.urls import reverse
from django.utils.text import slugify
from django.views.generic import TemplateView

from .models import AppUser, GlobalRole


def _resolve_role_slug(slug: str) -> GlobalRole:
    """Convierte un slug flexible en un GlobalRole o lanza 404."""
    normalized = slug.strip().lower().replace('_', '').replace('-', '')
    for role in GlobalRole:
        name_norm = role.name.lower()
        value_norm = role.value.lower().replace('_', '').replace('-', '')
        if normalized in (name_norm, value_norm):
            return role
    raise Http404(f'Rol no encontrado: {slug}')


class RoleSummaryView(LoginRequiredMixin, TemplateView):
    """Muestra un resumen de usuarios agrupados por rol."""

    template_name = 'users/roles_summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        raw_counts = (
            AppUser.objects.values('role_global')
            .annotate(total=Count('id'))
            .order_by('role_global')
        )
        counts_map = {row['role_global']: row['total'] for row in raw_counts}

        roles: List[dict] = []
        for role in GlobalRole:
            roles.append(
                {
                    'code': role.value,
                    'label': role.label,
                    'count': counts_map.get(role.value, 0),
                    'url': reverse('users:role-detail', kwargs={'role_slug': slugify(role.value)}),
                }
            )

        context['roles'] = roles
        return context


class RoleDetailView(LoginRequiredMixin, TemplateView):
    """Lista usuarios pertenecientes a un rol específico."""

    template_name = 'users/role_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role_slug: str = kwargs.get('role_slug', '')
        role = _resolve_role_slug(role_slug)

        query = self.request.GET.get('q', '').strip()
        queryset = AppUser.objects.filter(role_global=role.value)
        if query:
            queryset = queryset.filter(
                Q(full_name__icontains=query) | Q(email__icontains=query)
            )

        queryset = queryset.order_by('full_name')

        context.update(
            {
                'role': role,
                'role_slug': role_slug,
                'roles_url': reverse('users:role-summary'),
                'users': queryset,
                'search_query': query,
            }
        )
        return context
