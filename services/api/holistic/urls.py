from django.urls import path

from .views import HolisticAdviceView

app_name = "holistic"

urlpatterns = [
    path("advice/", HolisticAdviceView.as_view(), name="holistic-advice"),
]