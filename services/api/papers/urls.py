"""URL configuration for papers app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ClinicalPaperViewSet, PaperDownloadView

router = DefaultRouter()
router.register(r'papers', ClinicalPaperViewSet, basename='paper')

urlpatterns = [
    path('', include(router.urls)),
    # Vista alternativa para download (más simple)
    path('papers/<uuid:doc_id>/download/', PaperDownloadView.as_view(), name='paper-download-alt'),
]
