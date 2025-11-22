"""
Configuración de URLs para la aplicación de usuarios.

Este módulo define las rutas de la API usando DRF Routers
para generar automáticamente los endpoints CRUD.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppUserViewSet
from .views_html import RoleSummaryView, RoleDetailView

app_name = 'users'

# Crear router para registrar ViewSets
router = DefaultRouter()

# Registrar el ViewSet de usuarios
# Genera automáticamente URLs para:
# - /users/ (GET, POST)
# - /users/{id}/ (GET, PUT, PATCH, DELETE)
# - Y todas las @action definidas en el ViewSet
router.register(r'users', AppUserViewSet, basename='appuser')

urlpatterns = [
    path(
        'users/roles/manage/',
        RoleSummaryView.as_view(),
        name='role-summary',
    ),
    path(
        'users/roles/manage/<slug:role_slug>/',
        RoleDetailView.as_view(),
        name='role-detail',
    ),
    path('', include(router.urls)),
]
