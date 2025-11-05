"""Rutas para el dominio Body."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BodyActivityViewSet,
    BodyDashboardView,
    NutritionLogViewSet,
    NutritionPlanIngestCallbackView,
    NutritionPlanUploadView,
    NutritionPlanViewSet,
    SleepLogViewSet,
)

router = DefaultRouter()
router.register(r'body/activities', BodyActivityViewSet, basename='body-activities')
router.register(r'body/nutrition', NutritionLogViewSet, basename='body-nutrition')
router.register(r'body/nutrition-plans', NutritionPlanViewSet, basename='nutrition-plans')
router.register(r'body/sleep', SleepLogViewSet, basename='body-sleep')

urlpatterns = [
    path('body/dashboard/', BodyDashboardView.as_view(), name='body-dashboard'),
    path('nutrition-plans/upload/', NutritionPlanUploadView.as_view(), name='dashboard-nutrition-plan-upload'),
    path('internal/nutrition-plans/ingest-callback/', NutritionPlanIngestCallbackView.as_view(), name='nutrition-plan-ingest-callback'),
    path('', include(router.urls)),
]

