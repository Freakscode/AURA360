# vectosvc (Qdrant + FastAPI + Celery)

Arranque rápido:

1. `docker compose up --build`
2. `POST http://localhost:8000/ingest` con `{ "doc_id": "demo", "text": "hola mundo..." }`
3. `POST http://localhost:8000/search` con `{ "query": "hola", "limit": 5 }`

