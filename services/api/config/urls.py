"""
Configuración de URLs para AURA365 Backend API.

Este archivo define el routing principal de la aplicación, incluyendo:
- Panel de administración de Django
- API REST bajo /dashboard/
- Documentación de la API (OpenAPI/Swagger)
- API de autenticación de DRF (para desarrollo)
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from holistic.views import HolisticAdviceView


def health_check(request):
    """Endpoint de health check para pruebas de integración."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    # Health check endpoints (multiple paths for compatibility)
    path('api/health', health_check, name='health_check'),
    path('api/v1/health', health_check, name='health_check_v1'),
    path('health', health_check, name='health_check_root'),

    # Panel de administración de Django
    path('admin/', admin.site.urls),
    
    # API REST - Dashboard endpoints
    # Todos los endpoints de la API están bajo /dashboard/
    # según la preferencia del usuario
    path('dashboard/', include(('users.urls', 'users'), namespace='users')),
    path('dashboard/', include('body.urls')),
    path('api/holistic/', include(('holistic.urls', 'holistic'), namespace='holistic')),
    path('api/v1/holistic/advice', HolisticAdviceView.as_view(), name='holistic-advice-v1'),
    
    # Autenticación de DRF (para desarrollo y testing)
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    
    # =========================================================================
    # DOCUMENTACIÓN DE LA API (OpenAPI/Swagger)
    # =========================================================================
    
    # Schema OpenAPI (JSON/YAML)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # Documentación Swagger UI
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui'
    ),
    path(
        'docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui-root'
    ),
    
    # Documentación ReDoc
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc'
    ),
]
