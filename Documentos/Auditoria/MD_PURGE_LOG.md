# Registro de Purga de Markdown

**Fecha:** 16 de noviembre de 2025  
**Responsable:** Equipo AURA360 (UAT Ops)  
**Acción:** Purga selectiva de documentación redundante y artefactos temporales

## Resumen
- **Elementos eliminados:** 60 archivos (*.md*)
- **Motivo:** Limpieza de documentación duplicada/obsoleta para reducir ruido en el repositorio
- **Criterios aplicados:**
  - Samples de `adk-python/contributing/samples/**` (contenido ajeno al producto)
  - Artefactos temporales (`COMMIT_MESSAGE.md`, `TESTING.md`, `sample_users_*.md`)
  - Documentos internos de herramientas externas (`services/api/.claude/**`)

## Detalle de archivos eliminados
```
services/vectordb/COMMIT_MESSAGE.md
services/api/TESTING.md
services/api/.claude/agents/test-executor.md
services/api/docs/data/sample_users_2025-10-16.md
adk-python/contributing/samples/a2a_auth/README.md
adk-python/contributing/samples/a2a_basic/README.md
adk-python/contributing/samples/a2a_human_in_loop/README.md
adk-python/contributing/samples/a2a_root/README.md
adk-python/contributing/samples/adk_agent_builder_assistant/README.md
adk-python/contributing/samples/adk_answering_agent/README.md
adk-python/contributing/samples/adk_documentation/adk_release_analyzer/README.md
adk-python/contributing/samples/adk_knowledge_agent/README.md
adk-python/contributing/samples/adk_pr_triaging_agent/README.md
adk-python/contributing/samples/adk_triaging_agent/README.md
adk-python/contributing/samples/application_integration_agent/README.md
adk-python/contributing/samples/authn-adk-all-in-one/README.md
adk-python/contributing/samples/bigquery/README.md
adk-python/contributing/samples/bigtable/README.md
adk-python/contributing/samples/built_in_multi_tools/README.md
adk-python/contributing/samples/cache_analysis/README.md
adk-python/contributing/samples/computer_use/README.md
adk-python/contributing/samples/core_basic_config/README.md
adk-python/contributing/samples/google_api/README.md
adk-python/contributing/samples/hello_world_ollama/README.md
adk-python/contributing/samples/human_in_loop/README.md
adk-python/contributing/samples/integration_connector_euc_agent/README.md
adk-python/contributing/samples/jira_agent/README.md
adk-python/contributing/samples/langchain_youtube_search_agent/README.md
adk-python/contributing/samples/live_agent_api_server_example/readme.md
adk-python/contributing/samples/live_bidi_streaming_multi_agent/readme.md
adk-python/contributing/samples/live_bidi_streaming_single_agent/readme.md
adk-python/contributing/samples/live_bidi_streaming_tools_agent/readme.md
adk-python/contributing/samples/live_tool_callbacks_agent/readme.md
adk-python/contributing/samples/logprobs/README.md
adk-python/contributing/samples/mcp_dynamic_header_agent/README.md
adk-python/contributing/samples/mcp_postgres_agent/README.md
adk-python/contributing/samples/mcp_sse_agent/README.md
adk-python/contributing/samples/mcp_stdio_notion_agent/README.md
adk-python/contributing/samples/mcp_streamablehttp_agent/README.md
adk-python/contributing/samples/multi_agent_basic_config/README.md
adk-python/contributing/samples/multi_agent_llm_config/README.md
adk-python/contributing/samples/multi_agent_loop_config/README.md
adk-python/contributing/samples/multi_agent_seq_config/README.md
adk-python/contributing/samples/oauth2_client_credentials/README.md
adk-python/contributing/samples/oauth_calendar_agent/README.md
adk-python/contributing/samples/output_schema_with_tools/README.md
adk-python/contributing/samples/parallel_functions/README.md
adk-python/contributing/samples/plugin_basic/README.md
adk-python/contributing/samples/plugin_reflect_tool_retry/README.md
adk-python/contributing/samples/pydantic_argument/README.md
adk-python/contributing/samples/session_state_agent/README.md
adk-python/contributing/samples/spanner/README.md
adk-python/contributing/samples/spanner_rag_agent/README.md
adk-python/contributing/samples/static_instruction/README.md
adk-python/contributing/samples/static_non_text_content/README.md
adk-python/contributing/samples/tool_human_in_the_loop_config/README.md
adk-python/contributing/samples/tool_mcp_stdio_notion_config/README.md
adk-python/contributing/samples/toolbox_agent/README.md
adk-python/contributing/samples/workflow_agent_seq/README.md
adk-python/contributing/samples/workflow_triage/README.md
```

## Próximos pasos
1. Reorganizar los `.md` del directorio raíz en `docs/runbooks/`
2. Ejecutar verificación de enlaces y referencias
3. Mantener este registro actualizado ante futuras purgas
