# Nutrition Plan PDF Ingestion Pipeline

## Overview

The ingestion flow transforms a nutrition plan delivered as a PDF into a structured JSON document that can be stored in the `nutrition_plans` table. The process involves three services:

1. **Mobile / Dashboard** uploads a PDF using `POST /dashboard/nutrition-plans/upload/`.
2. **Backend (Django)** stores the file in Supabase Storage and dispatches a job to the vectorial service.
3. **Vectorial service (FastAPI + Celery)** downloads the PDF, extracts structured data with DeepSeek 7B, and calls back the backend with the final JSON.

```
Flutter client ──► Django backend ──► Supabase Storage
                     │
                     ├──► Vectorial API ──► Celery worker ──► DeepSeek 7B
                     │                                              │
                     └─────── Callback ◄────────────────────────────┘
```

## 1. Upload endpoint (Django)

- **Path:** `POST /dashboard/nutrition-plans/upload/`
- **Auth:** Supabase JWT (same as the rest of `/dashboard/` endpoints)
- **Behaviour:**
  - Validates file size/type.
  - Stores file in Supabase Storage (or configured backend).
  - Sends payload to vectorial API (`NUTRITION_PLAN_INGESTION_URL`).
  - Returns a `202 Accepted` with the job id and storage coordinates.

Relevant settings:

| Variable | Purpose |
| --- | --- |
| `NUTRITION_PLAN_STORAGE_BUCKET` | Supabase bucket where PDFs are placed. |
| `NUTRITION_PLAN_STORAGE_PREFIX` | Path prefix under the bucket. |
| `NUTRITION_PLAN_MAX_UPLOAD_MB` | Max file size accepted by the endpoint. |
| `NUTRITION_PLAN_ALLOWED_FILE_TYPES` | MIME types accepted (defaults to `application/pdf`). |
| `NUTRITION_PLAN_INGESTION_URL` | Vectorial API endpoint that queues the job. |
| `NUTRITION_PLAN_INGESTION_TOKEN` | Bearer token shared with the vectorial API. |
| `NUTRITION_PLAN_CALLBACK_URL` | Public URL that the vectorial worker will call once it finishes. |
| `NUTRITION_PLAN_CALLBACK_TOKEN` | Shared secret required for the callback. |

## 2. Vectorial service

- **Endpoint:** `POST /api/ingest/nutrition-plan`
- **Task:** `nutrition_plan_ingest_task`
- **Pipeline:**
  1. Download PDF (Supabase Storage or public URL).
  2. Extract text (PyMuPDF fallback, optionally GROBID later).
  3. Call DeepSeek 7B to map information to the nutrition plan schema.
  4. Enrich JSON with metadata (source, extractor, job id, excerpt).
  5. Invoke backend callback and push failures to the DLQ if retries are exhausted.

Key environment variables (vectorial service):

| Variable | Purpose |
| --- | --- |
| `SUPABASE_API_URL`, `SUPABASE_SERVICE_ROLE_KEY` | Allow the worker to read PDFs from Supabase Storage when the URL is private. |
| `DEEPSEEK_API_URL`, `DEEPSEEK_API_KEY` | HTTP endpoint + credentials for the LLM. |
| `NUTRITION_PLAN_DOWNLOAD_TIMEOUT` | Timeout (seconds) for downloading PDFs. |
| `NUTRITION_PLAN_PROMPT_MAX_CHARS` | Max characters from the PDF sent to the LLM. |
| `NUTRITION_PLAN_LLM_MODEL` | Identifier of the model used (defaults to `deepseek-7b`). |
| `NUTRITION_PLAN_CALLBACK_TIMEOUT` | Timeout for calling back the backend. |

## 3. Backend callback endpoint

- **Path:** `POST /dashboard/internal/nutrition-plans/ingest-callback/`
- **Auth:** Custom bearer token (`NUTRITION_PLAN_CALLBACK_TOKEN`). No user authentication is expected.
- **Behaviour:**
  - Validates payload structure via `NutritionPlanIngestCallbackSerializer`.
  - Enriches JSON (job id, metadata, raw excerpt) and persists the plan using `NutritionPlanSerializer`.
  - Supports idempotent updates when `metadata.plan_id` is provided.
  - Returns `201` when a new plan is created, `200` when an existing plan is updated.

The persisted record keeps:

- `title`, `language`, `issued_at`, `valid_until`, `is_active`.
- `plan_data` structured according to `docs/nutrition_plan_example.json`.
- `source_kind='pdf'`, `source_uri` pointing to the original document.
- `extractor` metadata (`deepseek-7b` by default) and timestamps.

## Testing checklist

1. **Unit tests**
   - Backend: `uv run python manage.py test body.tests.test_nutrition_plan_upload`.
   - Backend callback: `uv run python manage.py test body.tests.test_nutrition_plan_ingest_callback`.
   - Vector service: `uv run pytest tests/unit/test_nutrition_plan_task.py`.
2. **Manual flow**
   - Upload a PDF via dashboard/mobile (or curl against `/dashboard/nutrition-plans/upload/`).
   - Monitor vectorial worker logs (`docker compose logs -f worker`).
   - Verify callback creation (`nutrition_plans` table via Supabase SQL).

## Future improvements

- Replace PyMuPDF plain-text fallback with GROBID for richer metadata.
- Persist LLM usage metrics in a dedicated table for observability.
- Implement a reconciliation command to re-hydrate plans when Supabase Storage objects are rotated.







