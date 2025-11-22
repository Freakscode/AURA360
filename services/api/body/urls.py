"""Rutas para el dominio Body."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AIRecommendationsView,
    BodyActivityViewSet,
    BodyDashboardView,
    BodyMeasurementViewSet,
    BodyMeasurementTrendsView,
    BodyMeasurementTrendsStatusView,
    NutritionAdherenceView,
    NutritionLogViewSet,
    NutritionPlanIngestCallbackView,
    NutritionPlanUploadView,
    NutritionPlanViewSet,
    SleepLogViewSet,
)

router = DefaultRouter()
router.register(r'body/activities', BodyActivityViewSet, basename='body-activities')
router.register(r'body/measurements', BodyMeasurementViewSet, basename='body-measurements')
router.register(r'body/nutrition', NutritionLogViewSet, basename='body-nutrition')
router.register(r'body/nutrition-plans', NutritionPlanViewSet, basename='nutrition-plans')
router.register(r'body/sleep', SleepLogViewSet, basename='body-sleep')

urlpatterns = [
    path('body/dashboard/', BodyDashboardView.as_view(), name='body-dashboard'),
    path('body/measurements/trends/', BodyMeasurementTrendsView.as_view(), name='body-measurements-trends'),
    path('body/measurements/trends/status/<str:job_id>/', BodyMeasurementTrendsStatusView.as_view(), name='body-measurements-trends-status'),
    path('body/nutrition/adherence/', NutritionAdherenceView.as_view(), name='nutrition-adherence'),
    path('body/recommendations/ai/', AIRecommendationsView.as_view(), name='ai-recommendations'),
    path('nutrition-plans/upload/', NutritionPlanUploadView.as_view(), name='dashboard-nutrition-plan-upload'),
    path('internal/nutrition-plans/ingest-callback/', NutritionPlanIngestCallbackView.as_view(), name='nutrition-plan-ingest-callback'),
    path('', include(router.urls)),
]

