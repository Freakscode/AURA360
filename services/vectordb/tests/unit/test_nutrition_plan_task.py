from __future__ import annotations

from types import SimpleNamespace
from unittest import mock

import pytest

from vectosvc.api.schemas import NutritionPlanIngestRequest, NutritionPlanSource
from vectosvc.core.nutrition_plan import (
    NutritionPlanProcessingError,
    dispatch_callback,
    process_nutrition_plan,
)
from vectosvc.worker.tasks import enqueue_nutrition_plan


def _build_request(**overrides) -> NutritionPlanIngestRequest:
    payload = {
        "job_id": "job-123",
        "auth_user_id": "user-abc",
        "source": {
            "kind": "supabase",
            "bucket": "nutrition-plans",
            "path": "nutrition-plans/user/plans.pdf",
            "public_url": "https://cdn.example.com/plans.pdf",
        },
        "metadata": {
            "title": "Plan semanal",
            "language": "es",
        },
        "callback": None,
    }
    payload.update(overrides)
    return NutritionPlanIngestRequest.model_validate(payload)


@mock.patch("vectosvc.core.nutrition_plan._generate_structured_plan")
@mock.patch("vectosvc.core.nutrition_plan._extract_text")
@mock.patch("vectosvc.core.nutrition_plan._download_pdf")
def test_process_nutrition_plan_builds_payload(mock_download, mock_text, mock_structured):
    mock_download.return_value = b"%PDF-1.4"
    mock_text.return_value = "texto base"
    mock_structured.return_value = (
        {
            "title": "Plan ajustado",
            "language": "es",
            "issued_at": "2025-10-29",
            "valid_until": "2026-01-29",
            "plan_data": {"plan": {"title": "Plan ajustado"}},
        },
        {"raw_response": "{}", "usage": None, "prompt_chars": 120},
    )

    result = process_nutrition_plan(_build_request())

    assert result["title"] == "Plan ajustado"
    assert result["language"] == "es"
    assert result["plan_data"]["plan"]["title"] == "Plan ajustado"
    assert result["source"]["kind"] == "pdf"
    assert result["source"]["storage_kind"] == "supabase"
    assert result["llm"]["prompt_chars"] == 120


def test_download_raises_for_unknown_source():
    source = SimpleNamespace(kind="ftp", path="/tmp/foo.pdf", bucket=None, public_url=None)
    from vectosvc.core import nutrition_plan as module

    with pytest.raises(NutritionPlanProcessingError) as exc:
        module._download_pdf(source)  # type: ignore[arg-type]

    assert exc.value.phase == "download"


@mock.patch("vectosvc.core.nutrition_plan.httpx.Client")
def test_dispatch_callback_sends_authorization(mock_client):
    callback_payload = {
        "job_id": "job-123",
        "title": "Plan",
    }
    callback = NutritionPlanIngestRequest.model_validate(
        {
            "job_id": "job-123",
            "auth_user_id": "user-abc",
            "source": {
                "kind": "local",
                "path": "/tmp/foo.pdf",
            },
            "callback": {
                "url": "https://backend.example.com/callback",
                "token": "secret-token",
            },
        }
    ).callback

    dispatch_callback(callback=callback, payload=callback_payload)

    client_instance = mock_client.return_value.__enter__.return_value
    request = client_instance.post.call_args
    assert request[1]["headers"]["Authorization"] == "Bearer secret-token"
    assert request[1]["json"] == callback_payload


@mock.patch("vectosvc.worker.tasks.nutrition_plan_ingest_task.delay")
def test_enqueue_nutrition_plan_returns_task_id(mock_delay):
    mock_delay.return_value.id = "celery-789"

    task_id = enqueue_nutrition_plan(_build_request())

    assert task_id == "celery-789"
    mock_delay.assert_called_once()

