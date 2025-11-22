# ROL: QA Facilitator (Tester / QA)

**Proyecto:** AURA360  
**Fecha:** 30 de octubre de 2025  
**Versión:** 1.0  
**Marco normativo:** ISO 1012 - Directrices de Gobierno para User Acceptance Testing  
**Entorno UAT:** Staging integrado con servicios reales

---

## 1. DESCRIPCIÓN DEL ROL

El QA Facilitator coordina la ejecución operativa del UAT, garantizando que las pruebas se realicen conforme a los criterios de aceptación, que la evidencia sea confiable y que el ciclo de retroalimentación se mantenga activo.

### 1.1 Objetivo Principal
Asegurar la trazabilidad completa entre requisitos, casos de prueba y hallazgos, facilitando la ejecución rigurosa de las pruebas en el entorno de Staging integrado.

### 1.2 Perfil Requerido
- Experiencia en pruebas funcionales y UAT
- Conocimiento de procesos de negocio de AURA360
- Capacidad para documentar hallazgos con enfoque ISO 1012
- Habilidades de facilitación y comunicación efectiva
- Conocimiento básico de herramientas de gestión de incidencias

---

## 2. RESPONSABILIDADES ESPECÍFICAS

### 2.1 Fase de Planificación
- ✅ Elaborar el plan UAT operativo a partir de HU refinadas
- ✅ Coordinar con Business Analyst y Developer la disponibilidad de datos semilla en Staging
- ✅ Identificar y priorizar casos de prueba para:
  - Registro de mediciones corporales
  - Dashboard ejecutivo
  - Alertas de salud
- ✅ Preparar credenciales, accesos y scripts de soporte
- ✅ Definir criterios de entrada/salida por sesión de prueba
- ✅ Alinear calendario y recursos junto con UAT Manager

### 2.2 Fase de Ejecución
- ✅ Guiar al UAT User durante la ejecución de cada caso
- ✅ Registrar evidencia (capturas, logs, tiempos de respuesta)
- ✅ Validar resultados contra criterios de aceptación y métricas ISO 1012
- ✅ Documentar incidentes en la bitácora y gestionar su escalamiento
- ✅ Verificar disponibilidad del Developer para aclaraciones técnicas
- ✅ Mantener actualizada la matriz de cobertura UAT

### 2.3 Fase de Evaluación
- ✅ Consolidar observaciones y defectos por funcionalidad crítica
- ✅ Clasificar hallazgos (impacto, severidad, causa probable)
- ✅ Elaborar informe de sesión con métricas y desviaciones
- ✅ Proponer acciones correctivas y seguimiento
- ✅ Aportar insumos para la decisión GO/NO-GO
- ✅ Archivar evidencia conforme a la política ISO 1012

---

## 3. PLAN OPERATIVO DE PRUEBAS

### 3.1 Estructura del Mini Plan UAT
```markdown
# Plan Operativo Sesión UAT

**Funcionalidad:** [Registro de mediciones corporales / Dashboard ejecutivo / Alertas de salud]  
**Fecha:** [DD/MM/AAAA]  
**Objetivo de la sesión:** [Validación flujo principal, casos alternos, etc.]

## Casos de Prueba Priorizados
| ID | Tipo | Objetivo | Datos requeridos | Responsable |
|----|------|----------|------------------|-------------|
| UAT-RMC-01 | Camino feliz | Crear medición completa | Usuario demo RMC-001, peso 72kg | QA Facilitator |

## Criterios de Entrada
- Acceso verificado a Staging integrado
- Datos semilla cargados según lista de control
- Disponibilidad de UAT User y Developer confirmada

## Criterios de Salida
- Casos ejecutados y documentados al 100%
- Defectos registrados con evidencia
- Observaciones firmadas por UAT User
```

### 3.2 Lista de Datos de Prueba Críticos
| Funcionalidad | Datos requeridos | Observaciones |
|---------------|------------------|---------------|
| Registro de mediciones corporales | Usuarios RMC-001 a RMC-010 con historiales previos | Verificar consistencia de unidades |
| Dashboard ejecutivo | Roles directivos con métricas históricas | Confirmar actualización de KPIs diarios |
| Alertas de salud | Eventos configurados con umbrales personalizados | Validar notificaciones push y correo |

---

## 4. PLANTILLAS Y ARTEFACTOS

### 4.1 Matriz de Casos UAT
```markdown
| Funcionalidad | Caso | Criticidad | Pasos resumidos | Resultado esperado | Estado | Evidencia |
|---------------|------|------------|-----------------|--------------------|--------|-----------|
| Registro de mediciones corporales | UAT-RMC-01 | P0 | Registrar peso y medidas completas | Datos visibles en perfil y dashboard | ⬜ | |
| Dashboard ejecutivo | UAT-DBE-02 | P1 | Navegar a panel, filtrar por mes actual | KPIs consistentes con base histórica | ⬜ | |
| Alertas de salud | UAT-ALT-03 | P0 | Configurar umbral de frecuencia cardíaca | Notificación inmediata al usuario | ⬜ | |
```

### 4.2 Bitácora de Incidentes
```markdown
# Bitácora de Incidentes UAT

| ID | Fecha | Funcionalidad | Severidad | Descripción | Evidencia | Estado | Responsable | SLA |
|----|-------|---------------|-----------|-------------|-----------|--------|-------------|-----|
| DEF-UAT-001 | 30/10/2025 | Registro de mediciones corporales | Alta | No persiste medición de cintura > 120 cm | Captura, log API | Abierto | Developer A | 24h |
```

### 4.3 Checklist de Sesión
- [ ] Credenciales verificadas
- [ ] Datos de prueba validados
- [ ] HU y criterios de aceptación abiertos
- [ ] UAT User conectado y con guía disponible
- [ ] Developer en canal de soporte
- [ ] Evidencia almacenada en repositorio de auditoría

### 4.4 Formato de Triaje
```markdown
| Defecto | Impacto negocio | Severidad | Rol asignado | Fecha compromiso | Estado |
|---------|-----------------|-----------|--------------|------------------|--------|
| DEF-UAT-001 | Alto (no se registran medidas críticas) | Crítica | Developer A | 31/10/2025 | En progreso |
```

---

## 5. COMUNICACIÓN Y ESCALAMIENTO

| Situación | Acción inmediata | Canal | Escalada |
|-----------|------------------|-------|----------|
| Duda de requisito | Consultar al Business Analyst | Slack #uat | UAT Manager si no hay respuesta en 15 min |
| Incidente crítico | Notificar al Developer y registrar en bitácora | Llamada + ticket | UAT Manager si excede SLA |
| Bloqueo de entorno | Escalar a infraestructura | Service Desk | Dirección de TI si afecta agenda |

---

## 6. MÉTRICAS Y KPIs (ISO 1012)

| Métrica | Definición | Objetivo | Frecuencia |
|---------|------------|----------|------------|
| Cobertura de pruebas | % de casos ejecutados vs planificados | ≥ 95% | Diario |
| Defect density UAT | Defectos encontrados / Casos ejecutados | ≤ 0.3 | Diario |
| Tiempo de respuesta | Latencia promedio funcionalidades críticas | ≤ 2 s | Por ejecución |
| Tiempo de resolución | Tiempo desde defecto reportado hasta resuelto | ≤ 48h (P0) | Diario |
| Tasa de re-ejecución exitosa | % casos reprobados que pasan tras corrección | ≥ 90% | Cada iteración |

> **Nota:** Todas las métricas deben registrarse en el repositorio de auditoría siguiendo el control documental ISO 1012 (código UAT-AUD-2025).

---

## 7. CHECKLIST DEL ROL

### Antes de la sesión
- [ ] Revisión de criterios de aceptación y HU
- [ ] Confirmación de disponibilidad del entorno Staging
- [ ] Datos de prueba preparados y validados
- [ ] Plan operativo compartido con UAT User y UAT Manager

### Durante la sesión
- [ ] Casos ejecutados en el orden priorizado
- [ ] Evidencia recopilada y vinculada
- [ ] Defectos registrados con impacto de negocio
- [ ] Actualización de métricas en tablero UAT

### Después de la sesión
- [ ] Informe parcial enviado en ≤ 2 horas
- [ ] Incidentes escalados y con responsable asignado
- [ ] Documentación versionada en repositorio ISO 1012
- [ ] Retroalimentación capturada para próxima iteración

---

## 8. BUENAS PRÁCTICAS

### 8.1 Ejecución
1. Mantener enfoque en escenarios End-to-End.
2. Validar datos persistidos en todas las vistas.
3. Confirmar con el UAT User la interpretación de resultados.
4. Registrar tiempos exactos de cada paso para análisis de rendimiento.
5. Utilizar nomenclatura estándar ISO 1012 en incidentes y reportes.

### 8.2 Evidencia
- Capturas de pantalla con timestamp
- Exportes de logs con hash de integridad
- Referencia cruzada a criterios de aceptación
- Almacenamiento en carpeta Documentos/Auditoria/Evidencias/UAT

### 8.3 Mejora Continua
- Identificar patrones de defectos recurrentes
- Proponer ajustes a criterios de aceptación si detecta vacíos
- Documentar lecciones aprendidas por funcionalidad crítica

---

## 9. GLOSARIO

- **ISO 1012:** Norma interna adoptada para gobierno de UAT y control documental.
- **Bitácora UAT:** Registro auditado de incidentes y observaciones.
- **Defect density:** Métrica de densidad de defectos por caso.
- **Re-ejecución:** Nueva ejecución de un caso previamente fallido.
- **SLA UAT:** Compromisos de tiempo definidos para atención de incidentes.

---

## 10. ANEXOS

### Anexo A: Lista de Verificación de Datos Semilla Staging
| Recurso | Responsable | Estado |
|---------|-------------|--------|
| Usuarios demo 10 perfiles | QA Facilitator | ⬜ |
| Planes nutricionales históricos | Developer | ⬜ |
| Alertas configuradas por perfil | Business Analyst | ⬜ |

### Anexo B: Formato de Reporte de Sesión
```markdown
# Reporte Sesión UAT QA Facilitator

**Fecha:** [DD/MM/AAAA]  
**Funcionalidad:** [Nombre]  
**Casos ejecutados:** [Número]  
**Defectos encontrados:** [Lista ID]  
**Métricas clave:**  
- Cobertura: __%
- Defect density: __
- Tiempo respuesta promedio: __ s

**Observaciones:**  
1. [Detalle]
2. [Detalle]

**Acciones pendientes:**  
- [ ] Acción 1 (Responsable, fecha)
- [ ] Acción 2 (Responsable, fecha)

**Preparado por:** [Nombre QA Facilitator]
```

---

**Documento preparado conforme a:**
- ISO 1012 - Directrices de Gobierno para User Acceptance Testing
- ISTQB Test Manager
- Políticas de Auditoría AURA360 2025

**Fin del documento**