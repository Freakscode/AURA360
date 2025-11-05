# Plan de Suscripciones y Cuotas

Este documento describe la arquitectura funcional para los planes de AURA365.

## Objetivos
- Parametrizar planes sin lógica hardcodeada.
- Controlar consumo de recursos IA y reportes.
- Permitir upgrades y reporting de uso.

## Modelos Clave
- **SubscriptionTier**: metadatos por plan (`code`, `monthly_price`, flags de features).
- **UsageQuota**: límites por recurso (`resource_code`, `limit`, `period`, `reset_cron`).
- **UsageLedger**: eventos de consumo con referencia al recurso.
- **ReportSchedule** (opcional): siguiente ejecución programada por usuario.

## Recursos Controlados
| Recurso | Descripción | Periodicidad default |
| --- | --- | --- |
| `metabolic_report` | Generación de reportes analíticos | semanal/mensual |
| `realtime_update` | Actualizaciones inmediatas de indicadores | cada N horas |
| `chatbot_session` | Interacciones con chatbot contextual | diaria |
| `vector_search` | Consultas a la biblioteca científica | diaria |
| `preventive_alert` | Notificaciones proactivas de IA | diaria |

## Definición Inicial de Tiers
| Tier | Precio (USD) | Reportes | Chatbot | Actualización en tiempo real | Biblioteca científica | Recomendaciones preventivas |
| --- | --- | --- | --- | --- | --- | --- |
| `free` | 0 | 1 mensual | No | Semanal | No | No |
| `core` | 5 | 2 semanales | No | Sí (cada 6 h) | No | No |
| `plus` | 15 | 1 semanal | Sí (limitado) | Sí (cada 2 h) | No | Parcial |
| `premium` | 25-30 | Ilimitado | Sí | Sí (inmediata) | Sí | Sí |

## Flujo de Control de Cuotas
1. Endpoint o job solicita acción protegida.
2. `users.services.access.check_quota(user, resource)` obtiene el plan y cuota activa.
3. Si excede el límite, retorna `quota_exceeded` con opciones de upgrade.
4. Si se permite, registra el consumo en `UsageLedger`.
5. Programación (`ReportSchedule`) determina próximas ejecuciones automáticas.

## Integración con IA
- `ai_gateway` verifica cuota antes de usar LLM/vectorial.
- Tiers premium deben incluir referencias (`vector_search`).
- Guardar prompts/versiones por recurso para trazabilidad.

## Endpoints Implementados
- `POST /users/{id}/generate-metabolic-report/`
- `POST /users/{id}/request-realtime-update/`
- `POST /users/{id}/chatbot-session/`
- `GET /users/{id}/quota-status/`
- `GET /users/{id}/usage-history/?limit=N`

> Todos los endpoints anteriores requieren autenticación con `Authorization: Bearer <token>`
> (token emitido por Supabase) además de un usuario autenticado en Django.

## Próximos Pasos
1. Crear modelos y migraciones (ver `users/models.py`).
2. Implementar servicios de cuota y decoradores.
3. Añadir tareas programadas para resets/generaciones.
4. Documentar eventos en `docs/architecture/events.md`.
