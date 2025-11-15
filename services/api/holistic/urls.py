from django.urls import path

from .context_views import (
    CreateSnapshotView,
    IntakeSubmissionDetailView,
    IntakeSubmissionListCreateView,
    MessagingHealthView,
    MoodEntryListCreateView,
    UserContextSnapshotDetailView,
    UserContextSnapshotListView,
    UserProfileExtendedView,
)
from .views import HolisticAdviceView

app_name = "holistic"

urlpatterns = [
    # Health check endpoint
    path("messaging/health/", MessagingHealthView.as_view(), name="messaging-health"),
    # Holistic advice endpoint
    path("advice/", HolisticAdviceView.as_view(), name="holistic-advice"),
    # User context snapshots
    path(
        "user-context/snapshots/",
        UserContextSnapshotListView.as_view(),
        name="user-context-snapshots-list",
    ),
    path(
        "user-context/snapshots/<uuid:snapshot_id>/",
        UserContextSnapshotDetailView.as_view(),
        name="user-context-snapshot-detail",
    ),
    path(
        "user-context/snapshots/create/",
        CreateSnapshotView.as_view(),
        name="user-context-snapshot-create",
    ),
    # Mood entries
    path(
        "mood-entries/",
        MoodEntryListCreateView.as_view(),
        name="mood-entries-list-create",
    ),
    # Intake submissions
    path(
        "intake-submissions/",
        IntakeSubmissionListCreateView.as_view(),
        name="intake-submissions",
    ),
    path(
        "intake-submissions/<uuid:submission_id>/",
        IntakeSubmissionDetailView.as_view(),
        name="intake-submission-detail",
    ),
    # User profile extended (IKIGAI + psychosocial)
    path(
        "user-profile-extended/",
        UserProfileExtendedView.as_view(),
        name="user-profile-extended",
    ),
]
