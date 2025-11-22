# Plan de Aseguramiento de Calidad del Software (SQAP)
# Proyecto AURA360 - Plataforma Holística de Wellness

**Basado en IEEE 730-2014: Standard for Software Quality Assurance Processes**

---

## Información del Documento

| Campo | Valor |
|-------|-------|
| **Proyecto** | AURA360 - Holistic Wellness Platform |
| **Versión del Documento** | 1.0 |
| **Fecha** | Noviembre 2025 |
| **Estado** | Borrador para Revisión |
| **Preparado por** | Equipo de Calidad AURA360 |
| **Estándar de Referencia** | IEEE 730-2014 |

---

## Control de Versiones

| Versión | Fecha | Autor | Cambios |
|---------|-------|-------|---------|
| 1.0 | 2025-11-16 | Equipo QA | Versión inicial del SQAP |

---

## Tabla de Contenidos

1. [Propósito](#1-propósito)
2. [Productos a Entregar](#2-productos-a-entregar)
3. [Actividades de SQA](#3-actividades-de-sqa)
4. [Actividades de Verificación y Validación (V&V)](#4-actividades-de-verificación-y-validación-vv)
5. [Gestión de Problemas y Acciones Correctivas](#5-gestión-de-problemas-y-acciones-correctivas)
6. [Herramientas, Técnicas y Metodologías](#6-herramientas-técnicas-y-metodologías)
7. [Control de Código Fuente](#7-control-de-código-fuente)
8. [Gestión de Medios](#8-gestión-de-medios)
9. [Gestión de Proveedores](#9-gestión-de-proveedores)
10. [Gestión de Registros](#10-gestión-de-registros)
11. [Formación](#11-formación)
12. [Gestión de Riesgos](#12-gestión-de-riesgos)

---

## 1. Propósito

### 1.1 Objetivo del Plan

Este Plan de Aseguramiento de Calidad del Software (SQAP) define los procesos, actividades, estándares y métricas que garantizarán la calidad del software de la plataforma AURA360. El plan establece un marco sistemático para:

- Asegurar que todos los entregables cumplan con los requisitos especificados
- Prevenir defectos mediante prácticas proactivas de calidad
- Detectar y corregir defectos tempranamente en el ciclo de desarrollo
- Mantener la coherencia con estándares de la industria y mejores prácticas
- Proporcionar visibilidad y trazabilidad de la calidad del producto

### 1.2 Alcance del Proyecto

**Descripción del Sistema**: AURA360 es una plataforma integral de wellness holístico que integra el seguimiento de mente, cuerpo y alma con orientación personalizada impulsada por inteligencia artificial.

**Componentes en Alcance**:

| Componente | Descripción | Tecnología Principal |
|------------|-------------|---------------------|
| **Mobile App** | Aplicación móvil Flutter para iOS y Android | Flutter 3.24+, Dart |
| **Web App** | Aplicación web progresiva (PWA) | Angular 20, TypeScript |
| **API Backend** | API REST para gestión de usuarios y orquestación | Django 5.1, DRF, PostgreSQL |
| **Agents Service** | Servicio de agentes de IA holísticos | Google ADK, FastAPI |
| **VectorDB Service** | Servicio de búsqueda semántica biomédica | FastAPI, Qdrant, Celery, Redis |
| **PDF Extraction** | Servicio de extracción de documentos PDF | Python, GROBID |
| **Infrastructure** | IaC, despliegue y orquestación | Terraform, Kubernetes, Azure AKS |

**Módulos Funcionales Principales**:

1. **Mind Module**: Seguimiento de estado de ánimo, análisis emocional, gestión de contexto psicosocial
2. **Body Module**: Actividad física, planes nutricionales, registro de comidas, monitoreo de sueño
3. **Soul Module**: Gestión de perfil IKIGAI, alineación de propósito y valores
4. **Holistic AI**: Recomendaciones contextuales, recuperación de conocimiento biomédico vectorial

### 1.3 Definiciones y Acrónimos

| Término | Definición |
|---------|-----------|
| **SQA** | Software Quality Assurance (Aseguramiento de Calidad del Software) |
| **V&V** | Verification and Validation (Verificación y Validación) |
| **CI/CD** | Continuous Integration / Continuous Deployment |
| **ADK** | Agent Development Kit (Google) |
| **RAG** | Retrieval-Augmented Generation |
| **IaC** | Infrastructure as Code |
| **IKIGAI** | Concepto japonés de propósito de vida |
| **DRF** | Django REST Framework |
| **PWA** | Progressive Web Application |

### 1.4 Referencias

- IEEE 730-2014: Standard for Software Quality Assurance Processes
- ISO/IEC 25010: Systems and software Quality Requirements and Evaluation (SQuaRE)
- CONTRIBUTING.md: Guías de contribución del proyecto
- docs/testing/README_PRUEBAS.md: Sistema de pruebas de integración
- Conventional Commits: https://www.conventionalcommits.org/

---

## 2. Productos a Entregar

### 2.1 Entregables de Software

| ID | Producto | Descripción | Criterios de Aceptación |
|----|----------|-------------|------------------------|
| **SW-01** | AURA360 Mobile App | Aplicación móvil Flutter compilada para iOS y Android | - Pruebas unitarias > 80% cobertura<br>- Análisis estático sin errores críticos<br>- Rendimiento < 2s tiempo de carga inicial |
| **SW-02** | AURA360 Web App | PWA Angular desplegada | - Lighthouse score > 90<br>- Pruebas E2E pasando<br>- Compatible con Chrome, Firefox, Safari |
| **SW-03** | API Backend | Servicio Django REST API containerizado | - Cobertura de tests > 80%<br>- Documentación API actualizada<br>- Endpoints < 500ms p95 |
| **SW-04** | Agents Service | Servicio de agentes Google ADK | - Respuestas < 10s p95<br>- Precisión de recomendaciones validada<br>- Integración con VectorDB funcional |
| **SW-05** | VectorDB Service | Servicio de búsqueda semántica | - Tests de integración pasando<br>- Ingesta de documentos funcional<br>- Búsqueda < 2s p95 |
| **SW-06** | Infrastructure Code | Terraform modules, Helm charts | - Despliegue reproducible<br>- Validación de templates<br>- Documentación de runbooks |

### 2.2 Entregables de Documentación

| ID | Documento | Descripción | Responsable |
|----|-----------|-------------|-------------|
| **DOC-01** | Especificación de Requisitos | Requisitos funcionales y no funcionales completos | Product Owner |
| **DOC-02** | Documento de Arquitectura | Diseño de sistema, componentes, integraciones | Arquitecto de Software |
| **DOC-03** | Plan de Pruebas | Estrategia, casos de prueba, cobertura | QA Lead |
| **DOC-04** | Guía de Usuario | Manuales de usuario para Mobile y Web | Technical Writer |
| **DOC-05** | Documentación de API | Especificaciones OpenAPI/Swagger | Backend Lead |
| **DOC-06** | Runbooks Operacionales | Guías de despliegue, troubleshooting, monitoreo | DevOps Engineer |
| **DOC-07** | Informe de Calidad | Métricas de calidad, defectos, tendencias | QA Manager |

### 2.3 Entregables de Verificación y Validación

| ID | Entregable | Contenido |
|----|-----------|-----------|
| **VV-01** | Casos de Prueba Unitaria | Suite completa de unit tests para todos los servicios |
| **VV-02** | Casos de Prueba de Integración | Tests de integración entre servicios (ver docs/testing/) |
| **VV-03** | Casos de Prueba E2E | Flujos completos de usuario end-to-end |
| **VV-04** | Reportes de Cobertura | Reportes de coverage para Mobile, Backend, Agents, VectorDB |
| **VV-05** | Reportes de Análisis Estático | Resultados de flutter analyze, ESLint, Ruff, mypy |
| **VV-06** | Reportes de Performance | Latencias, throughput, uso de recursos |
| **VV-07** | Reportes de Seguridad | Análisis de vulnerabilidades, auditorías de dependencias |

### 2.4 Criterios de Completitud

Un producto se considera **completo** cuando cumple con:

1. ✅ Todos los requisitos funcionales implementados y probados
2. ✅ Cobertura de pruebas >= umbral definido (ver sección 4.3)
3. ✅ Análisis estático sin errores críticos o de alta severidad
4. ✅ Documentación técnica actualizada
5. ✅ Code review aprobado por al menos 1 reviewer
6. ✅ CI/CD pipeline ejecutado exitosamente
7. ✅ Métricas de performance dentro de objetivos
8. ✅ No hay defectos críticos abiertos

---

## 3. Actividades de SQA

### 3.1 Planificación de Calidad

**Responsable**: QA Manager
**Frecuencia**: Inicio de proyecto y revisión trimestral

**Actividades**:
- Definir estándares de calidad y criterios de aceptación
- Establecer métricas de calidad y objetivos
- Identificar puntos de control de calidad en el SDLC
- Planificar recursos necesarios para actividades de QA
- Alinear plan de calidad con roadmap del producto

**Entregables**:
- SQAP (este documento)
- Plan de pruebas maestro
- Definición de umbrales de calidad

### 3.2 Revisiones Técnicas

#### 3.2.1 Revisiones de Código (Code Reviews)

**Responsable**: Desarrolladores Senior, Tech Leads
**Frecuencia**: Cada Pull Request

**Proceso**:
1. Desarrollador crea PR siguiendo template establecido
2. CI/CD ejecuta automáticamente: linters, tests, security scans
3. Asignación automática de reviewers según CODEOWNERS
4. Reviewer verifica:
   - Cumplimiento de coding standards
   - Cobertura de pruebas adecuada
   - Documentación de código
   - Ausencia de vulnerabilidades de seguridad
   - Performance y eficiencia
5. Aprobación requiere al menos 1 reviewer + CI passing
6. Merge solo permitido si cumple criterios

**Herramientas**:
- GitHub Pull Requests
- GitHub Actions (CI/CD)
- SonarQube / CodeClimate (análisis estático)

**Criterios de Aprobación**:
- ✅ 0 errores críticos de análisis estático
- ✅ Cobertura de tests no disminuye
- ✅ Cumple guías de estilo (flutter analyze, ESLint, Ruff)
- ✅ Documentación adecuada (docstrings, comentarios)
- ✅ No introduce deuda técnica significativa

#### 3.2.2 Revisiones de Diseño

**Responsable**: Arquitecto de Software, Tech Leads
**Frecuencia**: Antes de implementar features mayores

**Proceso**:
1. Product Owner define requisitos en documento de PRD
2. Equipo técnico crea propuesta de diseño (ADR - Architecture Decision Record)
3. Sesión de revisión con stakeholders técnicos
4. Validación de:
   - Alineación con arquitectura existente
   - Escalabilidad y performance
   - Seguridad y privacidad
   - Mantenibilidad y testabilidad
5. Aprobación formal antes de iniciar implementación

**Documentación**:
- ADRs en `docs/architecture/adr/`
- Diagramas de arquitectura (C4 model)

#### 3.2.3 Auditorías de Calidad

**Responsable**: QA Manager
**Frecuencia**: Mensual

**Actividades**:
- Revisar adherencia a procesos de SQA
- Analizar métricas de calidad y tendencias
- Identificar áreas de mejora
- Verificar cumplimiento de estándares
- Auditar documentación y trazabilidad

**Entregables**:
- Informe de auditoría de calidad mensual
- Plan de acciones correctivas si aplica

### 3.3 Gestión de Configuración

**Responsable**: DevOps Engineer, Tech Lead

**Actividades**:

1. **Control de Versiones**:
   - Todo código en repositorio Git (GitHub)
   - Convenciones de commits: Conventional Commits
   - Branching strategy: GitFlow adaptado (main, develop, feature/*, fix/*, hotfix/*)

2. **Control de Builds**:
   - Builds automatizados en CI/CD para cada commit
   - Versionado semántico (SemVer)
   - Build artifacts almacenados en registries (Docker Hub, npm, pub.dev)

3. **Control de Releases**:
   - Release notes generados automáticamente
   - Tagging de versiones en Git
   - Despliegues controlados con aprobaciones

4. **Gestión de Dependencias**:
   - Lockfiles versionados (uv.lock, package-lock.json, pubspec.lock)
   - Auditorías de seguridad automatizadas (Dependabot, npm audit)
   - Actualizaciones controladas y probadas

### 3.4 Métricas de Calidad

#### 3.4.1 Métricas de Proceso

| Métrica | Objetivo | Medición | Frecuencia |
|---------|----------|----------|------------|
| **Velocidad de PR Merge** | < 24h promedio | Tiempo desde PR creation hasta merge | Semanal |
| **Tasa de Aprobación First-Time** | > 70% | PRs aprobados sin cambios / Total PRs | Semanal |
| **Cobertura de Code Review** | 100% | PRs revisados / Total PRs | Semanal |
| **Tiempo de Build CI** | < 10 min | Duración pipeline CI/CD | Diaria |

#### 3.4.2 Métricas de Producto

| Métrica | Objetivo | Medición | Frecuencia |
|---------|----------|----------|------------|
| **Cobertura de Código - Mobile** | ≥ 80% | flutter test --coverage | Por PR |
| **Cobertura de Código - Backend** | ≥ 80% | pytest --cov | Por PR |
| **Cobertura de Código - Agents** | ≥ 80% | pytest --cov | Por PR |
| **Cobertura de Código - VectorDB** | ≥ 80% | pytest --cov | Por PR |
| **Errores de Análisis Estático** | 0 críticos, < 10 mayores | flutter analyze, ESLint, Ruff | Por PR |
| **Deuda Técnica** | Rating A | SonarQube Technical Debt Ratio | Semanal |
| **Vulnerabilidades de Seguridad** | 0 críticas/altas | npm audit, pip audit, Snyk | Diaria |

#### 3.4.3 Métricas de Defectos

| Métrica | Objetivo | Medición | Frecuencia |
|---------|----------|----------|------------|
| **Defect Density** | < 5 defectos / KLOC | Defectos encontrados / Líneas de código | Sprint |
| **Defect Leakage** | < 10% | Defectos en producción / Total defectos | Mensual |
| **Defect Removal Efficiency** | > 90% | Defectos pre-release / Total defectos | Sprint |
| **Mean Time to Fix (MTTF)** | < 48h para críticos | Tiempo promedio de resolución | Semanal |

#### 3.4.4 Métricas de Performance

| Métrica | Objetivo | Medición | Frecuencia |
|---------|----------|----------|------------|
| **API Response Time (p95)** | < 500ms | Monitoreo APM | Continua |
| **Agents Service Response (p95)** | < 10s | Monitoreo APM | Continua |
| **VectorDB Search (p95)** | < 2s | Logs de servicio | Continua |
| **Mobile App Load Time** | < 2s | Métricas de performance Flutter | Por release |
| **Web App Lighthouse Score** | ≥ 90 | Lighthouse CI | Por deploy |

### 3.5 Reportes de Calidad

**Responsable**: QA Manager
**Audiencia**: Tech Lead, Product Owner, Stakeholders

**Tipos de Reportes**:

1. **Reporte Semanal de QA** (lunes):
   - Resumen de actividades de QA
   - Métricas clave de calidad
   - Defectos encontrados y estado
   - Bloqueadores y riesgos

2. **Reporte Mensual de Calidad**:
   - Análisis de tendencias de métricas
   - Comparativa con objetivos
   - Lecciones aprendidas
   - Recomendaciones de mejora

3. **Reporte de Release**:
   - Estado de completitud del release
   - Cobertura de pruebas
   - Defectos conocidos
   - Métricas de calidad del release
   - Readiness para producción

---

## 4. Actividades de Verificación y Validación (V&V)

### 4.1 Estrategia de Pruebas

La estrategia de pruebas de AURA360 sigue el modelo de **pirámide de pruebas**:

```
        ┌─────────────┐
        │   E2E (10%) │  ← Manual + Automated End-to-End
        ├─────────────┤
       /│ Integration │\  ← API, Service-to-Service Tests
      / │   (20%)     │ \
     /  ├─────────────┤  \
    /   │    Unit     │   \ ← Unit Tests (Functions, Classes)
   /    │    (70%)    │    \
  /     └─────────────┘     \
```

**Principios**:
- Tests automatizados preferidos sobre manuales
- Tests rápidos y determinísticos
- Cobertura balanceada: unit > integration > E2E
- Tests independientes y aislados
- Datos de prueba gestionados y reproducibles

### 4.2 Niveles de Prueba

#### 4.2.1 Pruebas Unitarias

**Objetivo**: Verificar el comportamiento correcto de unidades individuales de código (funciones, métodos, clases).

**Responsable**: Desarrolladores
**Frecuencia**: Continua durante desarrollo
**Ejecución**: Automática en CI/CD por cada commit

| Componente | Framework | Ubicación | Comando |
|------------|-----------|-----------|---------|
| **Mobile** | Flutter Test | `apps/mobile/test/` | `flutter test --coverage` |
| **Web** | Jasmine + Karma | `apps/web/src/**/*.spec.ts` | `ng test` |
| **API Backend** | Django TestCase | `services/api/**/tests/` | `python manage.py test` |
| **Agents Service** | pytest | `services/agents/tests/unit/` | `pytest tests/unit/ -v` |
| **VectorDB Service** | pytest | `services/vectordb/tests/unit/` | `pytest tests/unit/ -v --cov=vectosvc` |

**Criterios de Éxito**:
- ✅ 100% de tests unitarios pasan
- ✅ Cobertura ≥ 80% para cada componente
- ✅ Tiempo de ejecución < 5 minutos total
- ✅ Tests determinísticos (no flaky tests)

**Ejemplo de Unit Test (Python)**:
```python
# services/agents/tests/unit/test_holistic_coordinator.py
import pytest
from agents.holistic_coordinator import HolisticCoordinator

def test_generate_advice_for_mind_category():
    """Verificar generación de recomendaciones para categoría Mind."""
    coordinator = HolisticCoordinator()
    advice = coordinator.generate_advice(
        category="mind",
        user_profile={"age": 30, "mood_history": [...]},
        context="Estrés laboral alto"
    )

    assert advice is not None
    assert "recommendations" in advice
    assert len(advice["recommendations"]) > 0
    assert advice["category"] == "mind"
```

#### 4.2.2 Pruebas de Integración

**Objetivo**: Verificar la interacción correcta entre componentes y servicios.

**Responsable**: QA Engineers + Desarrolladores
**Frecuencia**: Por cada PR y pre-release
**Ejecución**: Automática en CI/CD + Manual cuando necesario

**Suites de Integración** (ver `docs/testing/README_PRUEBAS.md`):

| Suite | Descripción | Archivo | Tests |
|-------|-------------|---------|-------|
| **Servicio Vectorial** | Validación de ingesta, búsqueda, DLQ | `vectordb/tests/integration/test_vectorial_service_integration.py` | ~8 |
| **Servicio de Agentes** | Generación de recomendaciones, RAG | `agents/tests/integration/test_agents_service_integration.py` | ~10 |
| **Backend Django** | Orquestación, persistencia | `api/holistic/tests/test_backend_integration.py` | ~9 |
| **End-to-End** | Flujo completo Cliente→Backend→Agents→VectorDB | `tests/e2e/test_full_integration_flow.py` | ~6 |

**Comando de Ejecución**:
```bash
# Script orquestado que ejecuta todas las suites
./scripts/run_integration_tests.sh

# Opciones disponibles
./scripts/run_integration_tests.sh --only-vectorial
./scripts/run_integration_tests.sh --only-agents
./scripts/run_integration_tests.sh --only-backend
./scripts/run_integration_tests.sh --only-e2e
./scripts/run_integration_tests.sh --coverage
```

**Criterios de Éxito**:
- ✅ 100% de tests de integración pasan
- ✅ Cobertura de paths críticos completa
- ✅ Latencia dentro de objetivos (ver sección 3.4.4)
- ✅ Todos los servicios responden correctamente

**Prerequisitos**:
- Servicios dependientes ejecutándose (Qdrant, Redis, PostgreSQL)
- Variables de entorno configuradas (GOOGLE_API_KEY, SUPABASE_URL, etc.)
- Datos de prueba cargados

#### 4.2.3 Pruebas End-to-End (E2E)

**Objetivo**: Validar flujos completos de usuario desde la interfaz hasta la persistencia.

**Responsable**: QA Engineers
**Frecuencia**: Pre-release, regresión
**Ejecución**: Automática (preferido) + Manual (exploratorio)

**Herramientas**:
- **Mobile**: Flutter Integration Tests (`integration_test/`)
- **Web**: Cypress o Playwright
- **API**: Postman Collections / Newman

**Flujos Críticos a Validar**:

| ID | Flujo | Descripción | Prioridad |
|----|-------|-------------|-----------|
| E2E-01 | Registro y Onboarding | Usuario nuevo completa registro, perfil inicial, tutorial | Alta |
| E2E-02 | Registro de Estado de Ánimo | Usuario registra mood entry con tags y notas | Alta |
| E2E-03 | Solicitud de Recomendaciones | Usuario solicita consejo holístico, recibe recomendaciones personalizadas | Crítica |
| E2E-04 | Creación de Plan Nutricional | Usuario crea plan nutricional, registra comidas | Alta |
| E2E-05 | Sincronización Offline | Usuario realiza acciones offline, se sincronizan al conectar | Media |
| E2E-06 | Búsqueda de Información Biomédica | Usuario busca información de salud, obtiene resultados relevantes | Media |

**Criterios de Éxito**:
- ✅ 100% de flujos críticos funcionan correctamente
- ✅ Tiempos de respuesta aceptables (< 30s para flujos completos)
- ✅ UI/UX cumple con diseño especificado
- ✅ Manejo correcto de errores y edge cases

#### 4.2.4 Pruebas de Regresión

**Objetivo**: Asegurar que cambios nuevos no introducen defectos en funcionalidad existente.

**Responsable**: QA Engineers
**Frecuencia**: Cada release, cambios mayores
**Ejecución**: Automática (suite de regresión)

**Estrategia**:
- Suite de regresión automatizada con tests críticos
- Re-ejecución de tests unitarios e integración
- Smoke tests post-deploy en ambientes staging/producción

**Contenido de Suite de Regresión**:
- Todos los flujos E2E críticos
- Tests de integración completos
- Subset representativo de tests unitarios (fast tests)

**Tiempo de Ejecución Objetivo**: < 30 minutos

#### 4.2.5 Pruebas de Performance

**Objetivo**: Verificar que el sistema cumple con requisitos no funcionales de rendimiento.

**Responsable**: Performance Engineer, DevOps
**Frecuencia**: Pre-release, cambios arquitectónicos

**Tipos de Pruebas**:

1. **Load Testing**: Simular carga normal esperada
   - Herramienta: k6, Locust
   - Métrica: p50, p95, p99 de latencias
   - Objetivo: Cumplir SLOs definidos (sección 3.4.4)

2. **Stress Testing**: Identificar límites del sistema
   - Incrementar carga gradualmente hasta encontrar breaking point
   - Validar degradación graciosa

3. **Spike Testing**: Evaluar comportamiento ante picos de tráfico
   - Simular incrementos súbitos de carga
   - Validar auto-scaling y recuperación

4. **Endurance Testing**: Validar estabilidad en el tiempo
   - Ejecutar carga sostenida durante horas
   - Detectar memory leaks, degradación de performance

**Criterios de Éxito**:
- ✅ API p95 < 500ms bajo carga normal
- ✅ Agents Service p95 < 10s
- ✅ VectorDB Search p95 < 2s
- ✅ Sin errores bajo carga esperada
- ✅ Recovery automático después de spikes

**Escenarios de Carga**:
- Normal: 100 RPS (Requests Per Second)
- Peak: 500 RPS
- Stress: 1000+ RPS

#### 4.2.6 Pruebas de Seguridad

**Objetivo**: Identificar vulnerabilidades y asegurar cumplimiento de requisitos de seguridad.

**Responsable**: Security Engineer, DevOps
**Frecuencia**: Continua (SAST), Pre-release (DAST, Penetration Testing)

**Actividades**:

1. **SAST (Static Application Security Testing)**:
   - Análisis estático de código fuente
   - Herramientas: SonarQube, Bandit (Python), ESLint security plugins
   - Ejecución: Automática en CI/CD

2. **DAST (Dynamic Application Security Testing)**:
   - Escaneo de aplicación en ejecución
   - Herramientas: OWASP ZAP, Burp Suite
   - Ejecución: Semanal en staging

3. **Dependency Scanning**:
   - Auditoría de vulnerabilidades en dependencias
   - Herramientas: Dependabot, npm audit, pip audit, Snyk
   - Ejecución: Diaria

4. **Penetration Testing**:
   - Pruebas manuales de penetración
   - Frecuencia: Trimestral o pre-release mayor
   - Responsable: Equipo externo de seguridad

**Áreas de Foco**:
- ✅ OWASP Top 10 (Injection, XSS, CSRF, etc.)
- ✅ Autenticación y autorización (JWT, Supabase Auth)
- ✅ Manejo seguro de datos sensibles
- ✅ Configuración segura de infraestructura
- ✅ Secrets management

**Criterios de Éxito**:
- ✅ 0 vulnerabilidades críticas o altas
- ✅ Vulnerabilidades medias con plan de mitigación
- ✅ Cumplimiento de checklist de seguridad

#### 4.2.7 Pruebas de Usabilidad

**Objetivo**: Validar que la interfaz es intuitiva y cumple expectativas de usuarios.

**Responsable**: UX Designer, Product Owner
**Frecuencia**: Por feature nueva, cambios mayores de UI

**Métodos**:
- Pruebas con usuarios reales (user testing)
- Encuestas de satisfacción
- Análisis de métricas de uso (analytics)

**Métricas**:
- Task Success Rate > 90%
- Time on Task dentro de objetivos
- User Satisfaction Score (SUS) > 75

### 4.3 Criterios de Cobertura de Pruebas

**Umbrales Mínimos de Cobertura**:

| Componente | Cobertura Mínima | Objetivo | Medición |
|------------|------------------|----------|----------|
| **Mobile App** | 70% | 80% | Lines + Branches |
| **Web App** | 70% | 80% | Statements + Branches |
| **API Backend** | 75% | 85% | Statements + Branches |
| **Agents Service** | 75% | 85% | Statements + Branches |
| **VectorDB Service** | 80% | 90% | Statements + Branches |

**Excepciones**:
- Código generado automáticamente (migrations, protobuf)
- Configuración y setup boilerplate
- Scripts de utilidad no críticos

**Enforcement**:
- CI/CD falla si cobertura cae por debajo del mínimo
- PRs requieren mantener o incrementar cobertura

### 4.4 Validación de Requisitos

**Responsable**: Product Owner, QA Lead

**Proceso**:
1. Requisitos documentados en formato User Stories con Acceptance Criteria
2. Casos de prueba mapeados a requisitos (trazabilidad)
3. Tests de aceptación ejecutados por PO/QA antes de marcar como Done
4. UAT (User Acceptance Testing) con usuarios beta

**Herramientas**:
- Jira / Linear para gestión de requisitos y trazabilidad
- Matriz de trazabilidad Requisito ↔ Test Case

**Criterios de Validación**:
- ✅ 100% de Acceptance Criteria cumplidos
- ✅ Funcionalidad demostrada en Sprint Review
- ✅ Feedback de UAT incorporado

---

## 5. Gestión de Problemas y Acciones Correctivas

### 5.1 Clasificación de Defectos

**Severidades**:

| Severidad | Descripción | Ejemplos | SLA Resolución |
|-----------|-------------|----------|----------------|
| **Critical (P0)** | Sistema no funcional, pérdida de datos, vulnerabilidad de seguridad crítica | - App crashea al abrir<br>- Pérdida de datos de usuario<br>- Brecha de seguridad activa | 4 horas |
| **High (P1)** | Funcionalidad principal no disponible, workaround difícil | - Login no funciona<br>- No se pueden crear mood entries<br>- Recomendaciones no generan | 24 horas |
| **Medium (P2)** | Funcionalidad secundaria afectada, workaround disponible | - Filtros de búsqueda no funcionan<br>- UI incorrecta en casos específicos | 1 semana |
| **Low (P3)** | Problema menor, cosmético, mejora | - Texto mal alineado<br>- Mensaje de error poco claro<br>- Sugerencia de UX | Próximo sprint |

**Tipos**:
- **Bug**: Comportamiento incorrecto vs. especificación
- **Regression**: Funcionalidad que previamente trabajaba, ahora falla
- **Enhancement**: Mejora sugerida, no un error
- **Task**: Trabajo técnico (refactoring, deuda técnica)

### 5.2 Proceso de Gestión de Defectos

**Flujo de Vida de un Defecto**:

```
[New] → [Triaged] → [Assigned] → [In Progress] → [In Review] → [Verified] → [Closed]
                           ↓
                      [Won't Fix / Duplicate]
```

**Estados**:

| Estado | Descripción | Responsable |
|--------|-------------|-------------|
| **New** | Defecto reportado, pendiente de triage | Reportador |
| **Triaged** | Severidad y prioridad asignadas | QA Lead |
| **Assigned** | Asignado a desarrollador | Tech Lead |
| **In Progress** | Desarrollador trabajando en fix | Desarrollador |
| **In Review** | Fix en PR, pendiente de revisión | Reviewer |
| **Verified** | Fix verificado por QA en ambiente de pruebas | QA Engineer |
| **Closed** | Defecto resuelto y verificado en producción | QA Lead |
| **Won't Fix** | Defecto válido pero no será corregido (justificación requerida) | Product Owner |
| **Duplicate** | Duplicado de otro defecto existente | QA Lead |

**Actividades de Triage** (diario):
- QA Lead revisa nuevos defectos
- Asigna severidad y prioridad
- Valida reproducibilidad
- Asigna a desarrollador apropiado
- Notifica a stakeholders si es crítico

### 5.3 Acciones Correctivas

**Desencadenantes de Acciones Correctivas**:
- Incremento significativo en defect density
- Defectos críticos recurrentes
- Fallas en producción
- Violaciones de SLAs
- Incumplimiento de métricas de calidad

**Proceso**:
1. **Identificación**: Detectar patrón o problema sistémico
2. **Análisis de Causa Raíz**: 5 Whys, Fishbone Diagram
3. **Definición de Acción**: Plan de corrección específico
4. **Implementación**: Ejecutar cambios en procesos/prácticas
5. **Seguimiento**: Monitorear efectividad de la acción
6. **Cierre**: Documentar lecciones aprendidas

**Ejemplo de Acción Correctiva**:

| Campo | Valor |
|-------|-------|
| **Trigger** | Incremento de bugs de integración Mobile↔Backend (15 bugs en 1 mes) |
| **Causa Raíz** | Especificación de API incompleta, cambios no comunicados |
| **Acción** | - Implementar OpenAPI spec como fuente de verdad<br>- Contract testing automatizado<br>- Revisión de cambios de API en PRs |
| **Responsable** | Backend Lead + Mobile Lead |
| **Fecha Implementación** | 2025-12-01 |
| **Seguimiento** | Monitorear bugs de integración próximos 3 meses |

### 5.4 Acciones Preventivas

**Objetivo**: Evitar problemas antes de que ocurran.

**Prácticas Preventivas**:

1. **Shift-Left Testing**: Pruebas tempranas en el ciclo
   - Tests unitarios escritos junto con código
   - TDD (Test-Driven Development) para lógica crítica

2. **Análisis Estático Continuo**:
   - Linters configurados con reglas estrictas
   - SonarQube en CI/CD
   - Revisión automática de complejidad ciclomática

3. **Pair Programming** para features críticas:
   - Reducir defectos mediante revisión continua
   - Transferencia de conocimiento

4. **Postmortems sin culpa**:
   - Análisis de incidentes en producción
   - Documentación de lecciones aprendidas
   - Implementación de mejoras de proceso

5. **Training y Capacitación**:
   - Onboarding robusto para nuevos miembros
   - Sesiones de tech talks y knowledge sharing

### 5.5 Escalamiento

**Niveles de Escalamiento**:

| Condición | Escalar a | Tiempo |
|-----------|-----------|--------|
| Defecto P0 no resuelto en 4h | Engineering Manager | Inmediato |
| Defecto P1 no resuelto en 24h | Tech Lead → Engineering Manager | 24h |
| Múltiples defectos P1 simultáneos | Engineering Manager | Inmediato |
| Falla de producción con impacto a usuarios | CTO, Product Owner | Inmediato |

**Comunicación durante Incidentes**:
- Canal dedicado de Slack: #incidents
- Status updates cada 30 min para P0
- Postmortem obligatorio para todos los incidentes de producción

---

## 6. Herramientas, Técnicas y Metodologías

### 6.1 Herramientas de Desarrollo

| Categoría | Herramienta | Propósito | Componentes |
|-----------|-------------|-----------|-------------|
| **IDEs** | VSCode, Android Studio, Xcode | Desarrollo de código | Todos |
| **Control de Versiones** | Git, GitHub | Gestión de código fuente | Todos |
| **Package Managers** | uv (Python), npm (Node.js), pub (Dart) | Gestión de dependencias | Todos |
| **Containerización** | Docker, Docker Compose | Entornos consistentes, despliegue | Backend, Infraestructura |
| **Orquestación** | Kubernetes (AKS), Helm | Despliegue y gestión de contenedores | Producción |
| **IaC** | Terraform | Infraestructura como código | Azure Cloud |

### 6.2 Herramientas de Calidad y Testing

| Categoría | Herramienta | Propósito | Componentes |
|-----------|-------------|-----------|-------------|
| **Unit Testing** | Flutter Test, pytest, Jasmine/Karma | Pruebas unitarias | Mobile, Backend, Web |
| **Integration Testing** | pytest, Flutter integration_test | Pruebas de integración | Todos |
| **E2E Testing** | Cypress, Playwright | Pruebas end-to-end | Web |
| **API Testing** | Postman, Newman | Testing de APIs REST | Backend, Agents, VectorDB |
| **Performance Testing** | k6, Locust | Load, stress, endurance testing | Backend |
| **Coverage** | coverage.py, lcov | Medición de cobertura de código | Todos |

### 6.3 Herramientas de Análisis Estático

| Herramienta | Lenguaje/Componente | Propósito |
|-------------|---------------------|-----------|
| **flutter analyze** | Dart/Flutter | Linter y analyzer para Dart |
| **ESLint** | TypeScript/JavaScript | Linter para Angular/Web |
| **Ruff** | Python | Linter extremadamente rápido |
| **mypy** | Python | Type checking estático |
| **Bandit** | Python | Security linter |
| **SonarQube** | Multi-lenguaje | Análisis de calidad y seguridad |

### 6.4 Herramientas de CI/CD

| Herramienta | Propósito |
|-------------|-----------|
| **GitHub Actions** | Pipeline de CI/CD, automatización |
| **Docker Hub / ACR** | Registry de imágenes Docker |
| **ArgoCD / Flux** | GitOps para despliegues Kubernetes |

### 6.5 Herramientas de Gestión de Proyectos

| Herramienta | Propósito |
|-------------|-----------|
| **Jira / Linear** | Gestión de tareas, sprints, backlog |
| **Confluence** | Documentación colaborativa |
| **Slack** | Comunicación del equipo |
| **Miro** | Whiteboarding, diagramas colaborativos |

### 6.6 Herramientas de Monitoreo y Observabilidad

| Categoría | Herramienta | Propósito |
|-----------|-------------|-----------|
| **APM** | DataDog, New Relic, Sentry | Application Performance Monitoring |
| **Logging** | ELK Stack (Elasticsearch, Logstash, Kibana) | Gestión centralizada de logs |
| **Metrics** | Prometheus + Grafana | Métricas de sistema y aplicación |
| **Tracing** | Jaeger, OpenTelemetry | Distributed tracing |
| **Alerting** | PagerDuty, OpsGenie | Gestión de alertas e incidentes |

### 6.7 Metodologías de Desarrollo

**Agile Scrum**:
- Sprints de 2 semanas
- Daily standups (15 min)
- Sprint Planning (inicio de sprint)
- Sprint Review/Demo (fin de sprint)
- Retrospective (fin de sprint)

**Prácticas de Ingeniería**:
- **Continuous Integration**: Integración de código varias veces al día
- **Continuous Deployment**: Despliegues automatizados a staging
- **Trunk-Based Development**: Branches de corta duración, integración frecuente
- **Code Reviews**: Revisión obligatoria de todo código
- **Pair/Mob Programming**: Para features complejas o críticas
- **Test-Driven Development (TDD)**: Para lógica de negocio crítica

**Gestión de Configuración**:
- GitFlow adaptado para branching
- Conventional Commits para mensajes de commit
- Semantic Versioning para releases

---

## 7. Control de Código Fuente

### 7.1 Estrategia de Branching

**Modelo**: GitFlow Adaptado

**Branches Principales**:

| Branch | Propósito | Protección |
|--------|-----------|------------|
| **main** | Código en producción, siempre deployable | ✅ Protected, requiere PR + reviews + CI passing |
| **develop** | Branch de integración para desarrollo | ✅ Protected, requiere PR + CI passing |

**Branches de Trabajo**:

| Tipo | Nomenclatura | Propósito | Ciclo de Vida |
|------|--------------|-----------|---------------|
| **Feature** | `feat/descripcion-corta` | Nuevas funcionalidades | Creado desde develop, merge a develop |
| **Fix** | `fix/descripcion-bug` | Corrección de bugs | Creado desde develop, merge a develop |
| **Hotfix** | `hotfix/descripcion-urgente` | Corrección urgente en producción | Creado desde main, merge a main Y develop |
| **Release** | `release/v1.2.3` | Preparación de release | Creado desde develop, merge a main y develop |

**Reglas de Protección de Branch (main, develop)**:
- ✅ Require pull request before merging
- ✅ Require approvals: mínimo 1 reviewer
- ✅ Dismiss stale pull request approvals
- ✅ Require status checks to pass (CI/CD)
- ✅ Require branches to be up to date
- ✅ Include administrators (no bypass)
- ✅ Restrict who can push (solo via PR)

### 7.2 Convenciones de Commits

**Formato**: Conventional Commits (https://www.conventionalcommits.org/)

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Tipos**:
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Formateo, espacios (no afecta lógica)
- `refactor`: Refactorización de código
- `perf`: Mejoras de performance
- `test`: Añadir o actualizar tests
- `chore`: Tareas de mantenimiento
- `ci`: Cambios en CI/CD

**Scopes**:
- `mobile`: Flutter mobile app
- `web`: Angular web frontend
- `api`: Django backend
- `agents`: Agents service
- `vectordb`: VectorDB service
- `pdf`: PDF extraction service
- `infra`: Infraestructura
- `docs`: Documentación

**Ejemplos**:
```
feat(mobile): add mood tagging functionality
fix(api): resolve JWT validation issue
docs(agents): update RAG pipeline documentation
chore(vectordb): upgrade Qdrant to v1.8.0
ci(web): add Lighthouse CI check
```

**Enforcement**:
- Pre-commit hooks validan formato (commitlint)
- CI/CD verifica commits en PR

### 7.3 Proceso de Pull Request

**Template de PR**:

```markdown
## Descripción
[Descripción clara de los cambios]

## Tipo de cambio
- [ ] Bug fix
- [ ] Nueva funcionalidad
- [ ] Breaking change
- [ ] Documentación

## Relacionado con
Closes #[issue number]

## Checklist
- [ ] Tests agregados/actualizados
- [ ] Documentación actualizada
- [ ] CI passing
- [ ] Self-review completado
- [ ] Cobertura de código no disminuyó
```

**Flujo de PR**:
1. Desarrollador crea PR desde feature branch a develop
2. CI/CD ejecuta automáticamente:
   - Linters y análisis estático
   - Tests unitarios
   - Tests de integración
   - Security scans
   - Coverage check
3. Asignación automática de reviewers (CODEOWNERS)
4. Code review por al menos 1 reviewer
5. Aprobación + CI passing = PR mergeable
6. Squash merge (preferido) o merge commit
7. Branch feature eliminado automáticamente

**Criterios de Aprobación**:
- ✅ 1+ aprobación de reviewer
- ✅ CI/CD passing
- ✅ No conflictos con base branch
- ✅ Cobertura de código adecuada
- ✅ Documentación actualizada si aplica

### 7.4 Gestión de Releases

**Versionado**: Semantic Versioning (SemVer) - MAJOR.MINOR.PATCH

- **MAJOR**: Cambios incompatibles de API
- **MINOR**: Nueva funcionalidad compatible hacia atrás
- **PATCH**: Bug fixes compatibles

**Proceso de Release**:

1. **Preparación**:
   - Crear branch `release/vX.Y.Z` desde develop
   - Actualizar version numbers en archivos correspondientes
   - Actualizar CHANGELOG.md con cambios desde último release

2. **Testing**:
   - Ejecutar suite completa de regresión
   - Realizar UAT con usuarios beta
   - Performance testing
   - Security audit

3. **Aprobación**:
   - Product Owner aprueba funcionalidad
   - QA Lead aprueba calidad
   - Engineering Manager aprueba readiness técnico

4. **Merge y Tag**:
   - Merge release branch a main
   - Tag commit en main con vX.Y.Z
   - Merge release branch de vuelta a develop

5. **Despliegue**:
   - CI/CD construye artifacts para producción
   - Despliegue a staging para smoke tests finales
   - Despliegue a producción (blue-green o canary)

6. **Post-Release**:
   - Monitoreo intensivo primeras 24h
   - Release notes publicados
   - Comunicación a usuarios

**Automatización**:
- GitHub Releases generado automáticamente
- Release notes desde commits (Conventional Commits)
- Artifacts publicados en registries

### 7.5 Gestión de Dependencias

**Políticas**:

1. **Lockfiles Comprometidos**:
   - `uv.lock` (Python)
   - `package-lock.json` (Node.js)
   - `pubspec.lock` (Dart)
   - Garantiza builds reproducibles

2. **Actualizaciones**:
   - Dependabot configurado para PRs automáticos de actualizaciones
   - Actualizaciones de seguridad: inmediatas
   - Actualizaciones menores: semanales
   - Actualizaciones mayores: planificadas en sprint

3. **Auditorías de Seguridad**:
   - `npm audit` diario en CI/CD
   - `pip audit` diario en CI/CD
   - Snyk scan en PRs

4. **Restricciones**:
   - No usar dependencias sin mantenimiento activo
   - Revisar licencias de dependencias nuevas
   - Limitar dependencias transitivas cuando posible

### 7.6 Backup y Recuperación

**Código Fuente**:
- Repositorio principal en GitHub
- Mirror automático en servidor privado
- Backups diarios de repositorio completo

**Branches Críticos**:
- main y develop respaldados antes de merges significativos
- Tags de releases permanentes

**Recuperación**:
- Procedimiento documentado para restaurar desde backup
- Drill de recuperación anual

---

## 8. Gestión de Medios

### 8.1 Artefactos de Build

**Tipos de Artefactos**:

| Tipo | Formato | Almacenamiento | Retención |
|------|---------|----------------|-----------|
| **Mobile APK** | .apk (Android) | Google Play Console | Indefinido |
| **Mobile IPA** | .ipa (iOS) | App Store Connect | Indefinido |
| **Web Build** | Assets estáticos | Azure Blob Storage / CDN | Último 6 meses |
| **Docker Images** | Docker image | Azure Container Registry (ACR) | Último 12 meses |
| **Terraform State** | .tfstate | Azure Storage (encrypted) | Indefinido con versionado |

**Nomenclatura de Artifacts**:
- Mobile: `aura360-mobile-{version}-{build-number}.{apk|ipa}`
- Docker: `{service}:{version}-{git-sha}`
- Ejemplo: `aura360/api:1.2.3-a1b2c3d`

**Gestión de Espacio**:
- Limpieza automática de artifacts obsoletos
- Retención configurada según políticas

### 8.2 Entornos

**Ambientes Disponibles**:

| Ambiente | Propósito | Acceso | Datos |
|----------|-----------|--------|-------|
| **Development (Local)** | Desarrollo individual | Desarrollador | Datos de prueba locales |
| **Integration** | Integración de features, CI/CD | CI/CD, QA | Datos de prueba |
| **Staging** | Replica de producción para UAT | QA, Stakeholders | Datos sanitizados de producción |
| **Production** | Usuarios reales | Público | Datos reales |

**Configuración**:
- Cada ambiente tiene sus propios secrets y configuración
- Variables de entorno gestionadas con Azure Key Vault
- Configuración declarativa en Terraform

**Promoción entre Ambientes**:
```
Development → Integration → Staging → Production
```

- Código promovido via Git (branches/tags)
- Artefactos promovidos via CI/CD pipelines
- Aprobaciones manuales requeridas para Staging → Production

### 8.3 Datos de Prueba

**Gestión de Datos de Test**:

1. **Generación**:
   - Scripts de seeding para datos sintéticos
   - Faker libraries para datos realistas
   - Anonimización de datos de producción para staging

2. **Almacenamiento**:
   - Datasets de prueba en `tests/fixtures/`
   - Scripts de carga en `scripts/seed_data.py`

3. **Actualización**:
   - Revisión trimestral de relevancia de datos
   - Actualización cuando modelo de datos cambia

**Datos Sensibles**:
- ❌ NUNCA usar datos reales de usuarios en ambientes no productivos
- ✅ Sanitización y anonimización obligatoria
- ✅ PII (Personally Identifiable Information) removida

### 8.4 Documentación

**Repositorio de Documentación**:
- Colocada junto a código en `/docs`
- Versionada con el código
- Formato preferido: Markdown

**Tipos de Documentación**:

| Tipo | Ubicación | Audiencia |
|------|-----------|-----------|
| **README** | Raíz de cada servicio | Desarrolladores |
| **Arquitectura** | `docs/architecture/` | Arquitectos, Desarrolladores |
| **API** | `docs/api/`, OpenAPI specs | Desarrolladores Frontend/Integraciones |
| **Runbooks** | `docs/runbooks/` | DevOps, Soporte |
| **Testing** | `docs/testing/` | QA, Desarrolladores |
| **Usuario** | `docs/user-guides/` | Usuarios finales |

**Actualización**:
- Documentación actualizada junto con código (mismo PR)
- Revisión de docs en code reviews
- Documentación desactualizada tratada como defecto

### 8.5 Medios de Instalación

**Distribución de Aplicaciones**:

| Aplicación | Canal | Proceso |
|------------|-------|---------|
| **Mobile (Android)** | Google Play Store | CI/CD build → Google Play Console → Release (manual/automated) |
| **Mobile (iOS)** | Apple App Store | CI/CD build → App Store Connect → Review → Release |
| **Web** | CDN (Azure) | CI/CD build → Azure Blob Storage → CDN purge |

**Instaladores de Desarrollo**:
- Android APK firmado para testing interno
- iOS TestFlight para beta testers

---

## 9. Gestión de Proveedores

### 9.1 Identificación de Proveedores

**Proveedores Externos**:

| Proveedor | Servicio | Componente Afectado | Criticidad |
|-----------|----------|---------------------|------------|
| **Google Cloud** | Gemini API, Google ADK | Agents Service | Alta |
| **Supabase** | Auth, PostgreSQL, Storage | API Backend, Mobile | Crítica |
| **Microsoft Azure** | Cloud hosting (AKS, ACR, Storage) | Infraestructura | Crítica |
| **Qdrant Cloud** | Vector database managed service (opcional) | VectorDB Service | Media |
| **Sentry** | Error tracking & monitoring | Todos los componentes | Media |
| **GitHub** | Repositorio, CI/CD | Desarrollo | Alta |

### 9.2 Criterios de Selección de Proveedores

**Evaluación de Proveedores Nuevos**:

| Criterio | Peso | Requisito Mínimo |
|----------|------|------------------|
| **Confiabilidad (SLA)** | 30% | SLA ≥ 99.9% uptime |
| **Seguridad** | 25% | SOC 2 Type II, ISO 27001, GDPR compliant |
| **Soporte** | 15% | Soporte 24/7 para tier crítico |
| **Costo** | 15% | Dentro de presupuesto aprobado |
| **Escalabilidad** | 10% | Soporta crecimiento proyectado 3 años |
| **Documentación** | 5% | Documentación completa, APIs bien documentadas |

**Proceso de Aprobación**:
1. Technical Lead evalúa proveedor según criterios
2. Security review para proveedores que manejan datos sensibles
3. Aprobación de Engineering Manager + CFO (si > $10k/año)

### 9.3 Gestión de Dependencias de Proveedores

**Monitoreo de SLAs**:
- Dashboards con uptime de servicios críticos
- Alertas automáticas si servicio externo cae
- Revisión mensual de cumplimiento de SLAs

**Gestión de Cambios de Proveedores**:
- Suscripción a changelogs y notificaciones de proveedores
- Evaluación de impacto de cambios (breaking changes, deprecations)
- Plan de migración si es necesario

**Estrategias de Mitigación**:
- **Multi-cloud**: Evitar vendor lock-in cuando crítico
- **Fallbacks**: Degradación graciosa si servicio externo falla
- **Caching**: Reducir dependencia en real-time de servicios externos

### 9.4 Evaluación Continua de Proveedores

**Revisión Trimestral**:
- Performance vs. SLA
- Costos vs. presupuesto
- Incidentes y resolución
- Satisfacción del equipo

**Criterios de Re-evaluación**:
- Violación de SLA > 2 veces en 6 meses
- Incremento de costo > 30% sin justificación
- Cambio en modelo de negocio del proveedor
- Aparición de alternativas superiores

### 9.5 Proveedores de Bibliotecas y Componentes Open Source

**Uso de OSS (Open Source Software)**:

**Políticas**:
1. **Licencias Permitidas**:
   - ✅ MIT, Apache 2.0, BSD
   - ⚠️ LGPL (revisar caso por caso)
   - ❌ GPL, AGPL (restrictivas)

2. **Evaluación de Salud de Proyecto OSS**:
   - Actividad de commits reciente (último 6 meses)
   - Comunidad activa (issues respondidos)
   - Mantenimiento activo de seguridad

3. **Gestión de Vulnerabilidades**:
   - Dependabot alertas activadas
   - Actualización de dependencias con CVEs críticos: < 48h
   - Fork interno si proyecto abandonado pero crítico

**Contribuciones a OSS**:
- Equipo puede contribuir fixes a proyectos OSS usados
- Aprobación de Engineering Manager para contribuciones significativas
- Política de CLA (Contributor License Agreement)

---

## 10. Gestión de Registros

### 10.1 Tipos de Registros

**Registros de Calidad a Mantener**:

| Tipo de Registro | Contenido | Responsable | Retención |
|------------------|-----------|-------------|-----------|
| **Registros de Pruebas** | Resultados de ejecución de tests, cobertura | QA Engineers | 2 años |
| **Registros de Defectos** | Bugs reportados, estado, resolución | QA Lead | Indefinido (histórico) |
| **Registros de Code Review** | PRs, comentarios, aprobaciones | GitHub | Indefinido |
| **Registros de Auditoría SQA** | Informes de auditoría de calidad | QA Manager | 3 años |
| **Registros de Incidentes** | Postmortems, RCA, acciones correctivas | Engineering Manager | Indefinido |
| **Registros de Releases** | Versiones, release notes, criterios cumplidos | Release Manager | Indefinido |
| **Registros de Capacitación** | Entrenamientos completados, asistencia | HR + Engineering Manager | 3 años |
| **Registros de Cambios** | Cambios en configuración, infraestructura | DevOps | 1 año |

### 10.2 Almacenamiento de Registros

**Ubicaciones**:

| Tipo | Sistema | Backup |
|------|---------|--------|
| **Código y PRs** | GitHub | Diario a storage privado |
| **Defectos y Tareas** | Jira / Linear | Exportación mensual |
| **Documentación** | GitHub (`/docs`) + Confluence | Versionado en Git |
| **Logs de Aplicación** | ELK Stack (Elasticsearch) | Retención 90 días, archive 1 año |
| **Métricas** | Prometheus + Grafana | Retención 6 meses |
| **Artifacts** | ACR, Blob Storage | Ver sección 8.1 |
| **Reportes de QA** | Confluence + GitHub | Versionado |

**Seguridad de Registros**:
- Acceso restringido según roles
- Encriptación en reposo para datos sensibles
- Audit logs de acceso a registros críticos

### 10.3 Formato y Estándares

**Formatos Estándar**:
- Documentación: Markdown (.md)
- Reportes de Tests: JUnit XML, HTML
- Logs: JSON estructurado
- Métricas: Prometheus format

**Nomenclatura**:
- Fechas: ISO 8601 (YYYY-MM-DD)
- Versiones: Semantic Versioning
- Archivos: kebab-case.md

### 10.4 Acceso y Trazabilidad

**Control de Acceso**:

| Registro | Acceso | Justificación |
|----------|--------|---------------|
| **Código Fuente** | Equipo de desarrollo | Necesario para trabajo diario |
| **Defectos** | Equipo de desarrollo + QA + PO | Gestión de calidad |
| **Auditorías SQA** | QA Manager, Engineering Manager, Stakeholders | Visibilidad de calidad |
| **Incidentes** | Engineering team, Management | Aprendizaje organizacional |
| **Logs de Producción** | DevOps, On-call engineers | Debugging, troubleshooting |

**Trazabilidad**:
- Requisito ↔ Código: Commits referencia issue numbers
- Requisito ↔ Tests: Test cases mapeados a user stories
- Defecto ↔ Fix: PR references bug ticket
- Release ↔ Features/Fixes: CHANGELOG.md y release notes

### 10.5 Retención y Archivo

**Políticas de Retención**:

| Categoría | Retención Activa | Archivo | Eliminación |
|-----------|------------------|---------|-------------|
| **Logs de Aplicación** | 90 días (búsqueda rápida) | 1 año (archive storage) | Después de 1 año |
| **Métricas** | 6 meses (granularidad alta) | 2 años (granularidad reducida) | Después de 2 años |
| **Artifacts de Build** | Ver sección 8.1 | N/A | Según política |
| **Documentación** | Indefinido (versionado en Git) | N/A | N/A |
| **Defectos Cerrados** | Indefinido (histórico) | N/A | N/A |

**Proceso de Archivo**:
- Automatización de movimiento a cold storage
- Indexación para búsqueda futura si necesario
- Compresión para optimizar espacio

---

## 11. Formación

### 11.1 Necesidades de Capacitación

**Identificación de Gaps**:
- Evaluación anual de competencias del equipo
- Encuestas de necesidades de capacitación
- Identificación de gaps durante code reviews y retrospectives

**Áreas de Capacitación Clave**:

| Área | Audiencia | Prioridad |
|------|-----------|-----------|
| **Estándares de Código y Best Practices** | Todos los desarrolladores | Alta |
| **Testing (Unit, Integration, E2E)** | Desarrolladores, QA | Alta |
| **Herramientas de QA (pytest, flutter test, etc.)** | Desarrolladores, QA | Alta |
| **Seguridad (OWASP Top 10, Secure Coding)** | Desarrolladores | Alta |
| **Arquitectura de AURA360** | Nuevos miembros del equipo | Crítica |
| **Google ADK y Agents** | Backend/AI developers | Media |
| **Flutter avanzado** | Mobile developers | Media |
| **Kubernetes y DevOps** | DevOps, Backend developers | Media |
| **Gestión de Incidentes** | On-call engineers | Alta |

### 11.2 Programa de Onboarding

**Duración**: 2 semanas para nuevos miembros

**Semana 1: Fundamentos**
- Día 1-2: Setup de ambiente de desarrollo
  - Instalación de herramientas
  - Clonación de repositorio
  - Ejecución local de servicios
- Día 3: Arquitectura y tecnologías
  - Sesión de overview con Arquitecto
  - Revisión de documentación técnica
- Día 4-5: Estándares de código y procesos
  - Guías de estilo y convenciones
  - Proceso de PR y code review
  - Conventional Commits

**Semana 2: Hands-on**
- Día 1-2: Shadowing de desarrollador senior
  - Participación en code reviews
  - Observación de desarrollo de feature
- Día 3-4: Primera contribución guiada
  - Asignación de "good first issue"
  - Soporte de mentor
- Día 5: Retrospectiva de onboarding
  - Feedback sobre proceso
  - Identificación de gaps

**Materiales de Onboarding**:
- README.md actualizado en cada servicio
- CONTRIBUTING.md con guías de contribución
- docs/onboarding/WELCOME.md
- Videos de arquitectura y demos

### 11.3 Capacitación Continua

**Formatos de Capacitación**:

1. **Tech Talks Internos** (Quincenal):
   - Miembros del equipo presentan temas técnicos
   - Compartir conocimiento de features implementados
   - Lecciones aprendidas de incidentes

2. **Workshops Hands-on** (Mensual):
   - Sesiones prácticas de tecnologías nuevas
   - Code katas para mejorar habilidades
   - Pair programming sessions

3. **Cursos Online** (Continuo):
   - Presupuesto para cursos (Udemy, Pluralsight, Coursera)
   - Tiempo asignado para aprendizaje (4h/mes)

4. **Conferencias y Eventos** (Anual):
   - Asistencia a conferencias relevantes (Flutter Forward, Google I/O, etc.)
   - Presentación de aprendizajes al equipo

5. **Certificaciones** (Según rol):
   - GCP certifications para Backend/DevOps
   - Certificaciones de seguridad (CEH, etc.)
   - Scrum/Agile certifications para leads

### 11.4 Capacitación Específica de SQA

**Programa de QA Training**:

**Para Desarrolladores**:
- Testing Fundamentals (8h)
  - Unit testing best practices
  - Integration testing strategies
  - Test-Driven Development (TDD)
- Code Quality Tools (4h)
  - Uso de linters y analyzers
  - SonarQube interpretation
  - Coverage tools

**Para QA Engineers**:
- Advanced Testing Techniques (16h)
  - Performance testing con k6
  - Security testing
  - Automatización de E2E tests
- Test Management (8h)
  - Planificación de testing
  - Gestión de defectos
  - Reporting y métricas

**Para Todos**:
- Secure Coding Practices (4h)
  - OWASP Top 10
  - Common vulnerabilities
  - Security mindset

### 11.5 Evaluación de Efectividad

**Métricas de Capacitación**:
- % de equipo capacitado en áreas clave: > 90%
- Satisfacción con capacitaciones (encuestas): > 4/5
- Aplicación práctica de conocimiento (observable en PRs)

**Seguimiento**:
- Registro de capacitaciones completadas por miembro
- Revisión trimestral de gaps de conocimiento
- Ajuste de programa de capacitación según necesidades

### 11.6 Documentación y Knowledge Base

**Repositorio de Conocimiento**:
- Wiki interna (Confluence)
- `docs/` en repositorio GitHub
- Runbooks operacionales
- Postmortems de incidentes

**Prácticas de Knowledge Sharing**:
- Documentación como parte del Definition of Done
- Brown bag sessions semanales
- Slack channels para Q&A (`#dev-questions`, `#architecture`)

---

## 12. Gestión de Riesgos

### 12.1 Identificación de Riesgos

**Categorías de Riesgos de Calidad**:

1. **Riesgos Técnicos**: Arquitectura, deuda técnica, tecnología
2. **Riesgos de Proceso**: Procesos inadecuados, falta de adherencia
3. **Riesgos de Recursos**: Falta de personal, capacitación insuficiente
4. **Riesgos de Dependencias**: Proveedores externos, bibliotecas terceras
5. **Riesgos de Seguridad**: Vulnerabilidades, brechas de datos
6. **Riesgos de Performance**: Escalabilidad, latencias

**Proceso de Identificación**:
- Sesión de identificación de riesgos al inicio de proyecto
- Revisión de riesgos en retrospectives
- Análisis de riesgos antes de features mayores
- Lecciones aprendidas de incidentes

### 12.2 Registro de Riesgos

**Formato de Registro de Riesgo**:

| Campo | Descripción |
|-------|-------------|
| **ID** | Identificador único (RISK-XXX) |
| **Categoría** | Técnico, Proceso, Recursos, etc. |
| **Descripción** | Descripción detallada del riesgo |
| **Probabilidad** | Baja / Media / Alta |
| **Impacto** | Bajo / Medio / Alto / Crítico |
| **Nivel de Riesgo** | Probabilidad × Impacto |
| **Mitigación** | Estrategia para reducir riesgo |
| **Contingencia** | Plan si el riesgo se materializa |
| **Responsable** | Owner del riesgo |
| **Estado** | Abierto / Mitigado / Cerrado |

### 12.3 Riesgos Identificados para AURA360

#### RISK-001: Latencia Alta en Servicio de Agentes

| Campo | Valor |
|-------|-------|
| **Categoría** | Performance |
| **Descripción** | El servicio de agentes de IA puede tener latencias > 10s afectando UX |
| **Probabilidad** | Media |
| **Impacto** | Alto |
| **Nivel de Riesgo** | ⚠️ Alto |
| **Mitigación** | - Implementar caching de recomendaciones<br>- Optimizar prompts<br>- Streaming de respuestas<br>- Performance testing regular |
| **Contingencia** | - Degradación graciosa con recomendaciones pre-calculadas<br>- UI indica "cargando" claramente |
| **Responsable** | Backend Lead |
| **Estado** | Abierto - Mitigación en progreso |

#### RISK-002: Dependencia Crítica en Google Gemini API

| Campo | Valor |
|-------|-------|
| **Categoría** | Dependencias |
| **Descripción** | El servicio de agentes depende 100% de Google Gemini API. Si Google tiene outage, funcionalidad crítica cae. |
| **Probabilidad** | Baja (SLA 99.9%) |
| **Impacto** | Crítico |
| **Nivel de Riesgo** | ⚠️ Alto |
| **Mitigación** | - Monitoreo de uptime de Google APIs<br>- Caching agresivo de respuestas<br>- Evaluación de modelo fallback (OpenAI) |
| **Contingencia** | - Mostrar últimas recomendaciones cacheadas<br>- Degradación graciosa de funcionalidad de agentes |
| **Responsable** | Arquitecto de Software |
| **Estado** | Abierto - Requiere decisión arquitectónica |

#### RISK-003: Cobertura de Tests Insuficiente en Mobile

| Campo | Valor |
|-------|-------|
| **Categoría** | Proceso |
| **Descripción** | Históricamente, mobile app tiene < 70% de cobertura, por debajo del objetivo. |
| **Probabilidad** | Media |
| **Impacto** | Medio |
| **Nivel de Riesgo** | ⚠️ Medio |
| **Mitigación** | - Enforcement de cobertura en CI/CD (bloquea PR si < 70%)<br>- Capacitación en Flutter testing<br>- Refactoring de código legacy para testabilidad |
| **Contingencia** | - Incrementar testing manual<br>- E2E tests compensan gaps de unit tests |
| **Responsable** | Mobile Lead |
| **Estado** | Mitigado - Coverage ahora enforced en CI |

#### RISK-004: Vulnerabilidades en Dependencias OSS

| Campo | Valor |
|-------|-------|
| **Categoría** | Seguridad |
| **Descripción** | Dependencias terceras pueden tener CVEs críticos que afectan seguridad. |
| **Probabilidad** | Media |
| **Impacto** | Alto |
| **Nivel de Riesgo** | ⚠️ Alto |
| **Mitigación** | - Dependabot alertas activas<br>- Snyk scan en PRs<br>- SLA de 48h para parchar CVEs críticos<br>- Revisión mensual de dependencias |
| **Contingencia** | - Fork interno de dependencia crítica si no parcheable<br>- Rollback a versión segura |
| **Responsable** | DevOps + Security Lead |
| **Estado** | Mitigado - Proceso activo |

#### RISK-005: Pérdida de Conocimiento por Rotación de Personal

| Campo | Valor |
|-------|-------|
| **Categoría** | Recursos |
| **Descripción** | Miembros clave del equipo pueden dejar el proyecto, llevándose conocimiento crítico. |
| **Probabilidad** | Media |
| **Impacto** | Medio |
| **Nivel de Riesgo** | ⚠️ Medio |
| **Mitigación** | - Documentación exhaustiva<br>- Pair programming y knowledge sharing<br>- Redundancia de conocimiento (2+ personas por área crítica)<br>- Onboarding robusto |
| **Contingencia** | - Contratación rápida de reemplazo<br>- Consultores externos temporales |
| **Responsable** | Engineering Manager |
| **Estado** | Mitigado - Prácticas establecidas |

#### RISK-006: Escalabilidad de VectorDB con Crecimiento de Usuarios

| Campo | Valor |
|-------|-------|
| **Categoría** | Performance |
| **Descripción** | A medida que crece la base de documentos en Qdrant, búsquedas pueden degradarse. |
| **Probabilidad** | Alta (esperado con crecimiento) |
| **Impacto** | Medio |
| **Nivel de Riesgo** | ⚠️ Alto |
| **Mitigación** | - Performance testing con datasets grandes<br>- Optimización de índices Qdrant<br>- Horizontal scaling configurado<br>- Monitoreo de performance continuo |
| **Contingencia** | - Migración a Qdrant Cloud managed (auto-scaling)<br>- Particionamiento de colecciones |
| **Responsable** | VectorDB Lead |
| **Estado** | Abierto - Monitoreo activo |

#### RISK-007: Complejidad de Despliegue Multi-Servicio

| Campo | Valor |
|-------|-------|
| **Categoría** | Proceso |
| **Descripción** | Arquitectura de microservicios incrementa complejidad de despliegues y coordinación de versiones. |
| **Probabilidad** | Media |
| **Impacto** | Medio |
| **Nivel de Riesgo** | ⚠️ Medio |
| **Mitigación** | - CI/CD robusto automatizado<br>- Smoke tests post-deploy<br>- Blue-green / canary deployments<br>- Runbooks de deployment documentados |
| **Contingencia** | - Rollback automatizado si smoke tests fallan<br>- Feature flags para desactivar funcionalidad problemática |
| **Responsable** | DevOps Lead |
| **Estado** | Mitigado - Infraestructura implementada |

### 12.4 Evaluación de Riesgos

**Matriz de Riesgo (Probabilidad × Impacto)**:

```
              Impacto
              Bajo   Medio   Alto   Crítico
Probabilidad
Alta          🟡     🟠      🔴     🔴
Media         🟢     🟡      🟠     🔴
Baja          🟢     🟢      🟡     🟠
```

- 🔴 Riesgo Crítico: Acción inmediata requerida
- 🟠 Riesgo Alto: Plan de mitigación debe estar activo
- 🟡 Riesgo Medio: Monitoreo y mitigación planificada
- 🟢 Riesgo Bajo: Aceptable, monitoreo pasivo

**Priorización**:
1. Riesgos críticos (🔴) - Máxima prioridad
2. Riesgos altos (🟠) - Alta prioridad
3. Riesgos medios (🟡) - Prioridad normal
4. Riesgos bajos (🟢) - Baja prioridad

### 12.5 Estrategias de Mitigación

**Tipos de Estrategias**:

1. **Evitar**: Eliminar la fuente del riesgo
   - Ejemplo: No usar biblioteca OSS abandonada

2. **Mitigar**: Reducir probabilidad o impacto
   - Ejemplo: Implementar tests automatizados para reducir riesgo de regresiones

3. **Transferir**: Mover riesgo a tercero
   - Ejemplo: Usar servicio managed (Qdrant Cloud) en vez de self-hosted

4. **Aceptar**: Reconocer riesgo y aceptar consecuencias
   - Ejemplo: Riesgo bajo de outage de GitHub - costo de mitigación > impacto

**Implementación**:
- Estrategias de mitigación documentadas en registro de riesgos
- Owner asignado para cada riesgo
- Seguimiento en reuniones de engineering

### 12.6 Monitoreo y Revisión de Riesgos

**Frecuencia de Revisión**:
- Revisión mensual de registro de riesgos (Engineering Manager + Leads)
- Revisión ad-hoc cuando:
  - Nuevo riesgo identificado
  - Riesgo se materializa
  - Cambio significativo en proyecto

**Métricas de Gestión de Riesgos**:
- % de riesgos con plan de mitigación: 100%
- Riesgos críticos abiertos: 0
- Tiempo promedio de respuesta a riesgo materializado: < 24h

**Reportes**:
- Dashboard de riesgos actualizado mensualmente
- Riesgos críticos escalados a stakeholders inmediatamente

### 12.7 Plan de Contingencia

**Riesgos con Mayor Necesidad de Contingencia**:

1. **Outage de Proveedor Crítico (Supabase, Google, Azure)**:
   - Comunicación inmediata a usuarios
   - Activación de modo degradado si disponible
   - Escalamiento a soporte del proveedor

2. **Brecha de Seguridad**:
   - Activación de Incident Response Plan
   - Contención inmediata
   - Comunicación según GDPR/regulaciones

3. **Pérdida de Datos**:
   - Activación de procedimiento de recuperación desde backups
   - Evaluación de impacto
   - Comunicación a usuarios afectados

4. **Bug Crítico en Producción**:
   - Rollback inmediato si disponible
   - Hotfix process activado
   - Postmortem obligatorio

---

## Aprobación del Plan

Este Plan de Aseguramiento de Calidad del Software (SQAP) debe ser revisado y aprobado por los siguientes stakeholders:

| Rol | Nombre | Firma | Fecha |
|-----|--------|-------|-------|
| **QA Manager** | _______________ | _______________ | _______________ |
| **Engineering Manager** | _______________ | _______________ | _______________ |
| **Product Owner** | _______________ | _______________ | _______________ |
| **Arquitecto de Software** | _______________ | _______________ | _______________ |
| **CTO** | _______________ | _______________ | _______________ |

---

## Revisión y Mantenimiento del Plan

**Frecuencia de Revisión**: Trimestral o cuando haya cambios significativos en el proyecto

**Responsable de Mantenimiento**: QA Manager

**Proceso de Actualización**:
1. Revisión de efectividad de procesos actuales
2. Incorporación de lecciones aprendidas
3. Actualización de métricas y objetivos
4. Aprobación de cambios por stakeholders
5. Comunicación de cambios al equipo

**Historial de Revisiones**: Ver sección "Control de Versiones" al inicio del documento.

---

## Anexos

### Anexo A: Glosario de Términos

Ver sección 1.3 "Definiciones y Acrónimos"

### Anexo B: Referencias

- IEEE 730-2014: Standard for Software Quality Assurance Processes
- ISO/IEC 25010: Systems and software Quality Requirements and Evaluation (SQuaRE)
- AURA360 CONTRIBUTING.md
- AURA360 docs/testing/README_PRUEBAS.md
- Conventional Commits Specification: https://www.conventionalcommits.org/

### Anexo C: Plantillas

**Plantilla de Reporte de Defecto**:
```markdown
## Resumen
[Descripción breve del problema]

## Severidad
- [ ] Critical (P0)
- [ ] High (P1)
- [ ] Medium (P2)
- [ ] Low (P3)

## Pasos para Reproducir
1.
2.
3.

## Comportamiento Esperado
[Qué debería ocurrir]

## Comportamiento Actual
[Qué ocurre actualmente]

## Evidencia
[Screenshots, logs, etc.]

## Ambiente
- OS:
- App Version:
- Device:
```

**Plantilla de Postmortem**:
```markdown
## Resumen del Incidente
- **Fecha**:
- **Duración**:
- **Impacto**:
- **Severidad**:

## Línea de Tiempo
- [HH:MM] Evento 1
- [HH:MM] Evento 2

## Causa Raíz
[Análisis de 5 Whys o Fishbone]

## Resolución
[Cómo se resolvió]

## Acciones Correctivas
1. [ ] Acción 1 - Responsable - Fecha
2. [ ] Acción 2 - Responsable - Fecha

## Lecciones Aprendidas
```

### Anexo D: Métricas y Dashboards

**Dashboard de Calidad (actualización semanal)**:
- Cobertura de código (Mobile, Web, Backend, Agents, VectorDB)
- Defect density y tendencia
- Velocidad de PR merge
- Resultados de CI/CD (pass rate)
- Vulnerabilidades de seguridad abiertas

**Dashboard de Performance (actualización continua)**:
- API latencies (p50, p95, p99)
- Agents Service latencies
- VectorDB search latencies
- Error rates por servicio

---

**Fin del Documento**

---

**Documento preparado por**: Equipo de Calidad AURA360
**Fecha de preparación**: 2025-11-16
**Próxima revisión programada**: 2026-02-16
**Versión**: 1.0
