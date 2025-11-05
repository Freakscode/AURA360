# ROL: UAT Manager / Líder de Pruebas

**Proyecto:** AURA360  
**Fecha:** 30 de octubre de 2025  
**Versión:** 1.0  
**Marco normativo:** ISO 1012 - Directrices de Gobierno para User Acceptance Testing  
**Entorno UAT:** Staging integrado con servicios reales

---

## 1. DESCRIPCIÓN DEL ROL

El UAT Manager lidera el ciclo completo de UAT, asegurando la coordinación de roles, la ejecución conforme al plan maestro, la consolidación de resultados y el cumplimiento de la normativa ISO 1012 para auditoría y control.

### 1.1 Objetivo Principal
Dirigir el proceso de aceptación del usuario garantizando cobertura, trazabilidad, control documental y una decisión GO/NO-GO fundamentada en criterios de negocio y evidencias objetivas.

### 1.2 Perfil Requerido
- Experiencia en gestión de pruebas y proyectos
- Conocimiento de procesos de negocio AURA360
- Habilidades de liderazgo, negociación y comunicación ejecutiva
- Dominio de métricas de calidad y reporting
- Enfoque en cumplimiento normativo y auditorías

---

## 2. RESPONSABILIDADES ESPECÍFICAS

### 2.1 Fase de Planificación
- ✅ Elaborar el plan maestro UAT con calendario, alcance y hitos
- ✅ Validar la disponibilidad y capacitación de roles: UAT User, BA, QA Facilitator, Developer
- ✅ Definir criterios de entrada y salida alineados a ISO 1012
- ✅ Establecer mecanismos de control de cambios y escalamiento
- ✅ Coordinar la preparación del entorno Staging y datos semilla
- ✅ Aprobar el mini plan operativo preparado por el QA Facilitator
- ✅ Publicar agenda de checkpoints y reuniones ejecutivas

### 2.2 Fase de Ejecución
- ✅ Supervisar el avance diario respecto al plan maestro
- ✅ Garantizar la recolección sistemática de evidencia y métricas
- ✅ Resolver bloqueos inter-rol y negociar prioridades
- ✅ Mantener actualizado el tablero de indicadores (cobertura, defectos, SLA)
- ✅ Facilitar reuniones de triaje y seguimiento
- ✅ Asegurar comunicación constante con stakeholders clave

### 2.3 Fase de Evaluación
- ✅ Consolidar resultados de todas las sesiones y roles
- ✅ Analizar riesgos residuales y planes de contingencia
- ✅ Preparar informe ejecutivo de UAT con recomendación GO/NO-GO
- ✅ Coordinar sign-off formal y archivado de evidencia ISO 1012
- ✅ Registrar lecciones aprendidas y plan de mejoras
- ✅ Preparar paquete de auditoría para comités de control interno

---

## 3. PLAN MAESTRO DEL CICLO UAT

### 3.1 Calendario y Hitos
| Hito | Fecha | Responsable | Entregable |
|------|-------|-------------|------------|
| Kick-off UAT | 01/11/2025 | UAT Manager | Acta de inicio |
| Finalización pruebas Registro de mediciones | 05/11/2025 | QA Facilitator | Informe funcional |
| Finalización pruebas Dashboard ejecutivo | 07/11/2025 | QA Facilitator | Informe funcional |
| Finalización pruebas Alertas de salud | 09/11/2025 | QA Facilitator | Informe funcional |
| Comité de evaluación | 10/11/2025 | UAT Manager | Informe consolidado |
| Sign-off final | 11/11/2025 | Sponsor negocio | Acta de aceptación |

### 3.2 Control de Cambios (ISO 1012)
```markdown
# Registro Control Cambios UAT (ISO1012-CC)

| ID | Fecha | Solicitante | Descripción | Impacto | Decisión | Fecha implementación | Documentos asociados |
|----|-------|-------------|-------------|---------|----------|-----------------------|----------------------|
| CC-UAT-001 | 02/11/2025 | Business Analyst | Ajuste criterio de aceptación Alertas | Medio | Aprobado | 03/11/2025 | HU-ALT-02 v1.1, Plan UAT |
```

### 3.3 Matriz RACI
| Actividad | UAT Manager | BA | QA Facilitator | Developer | UAT User |
|-----------|-------------|----|----------------|-----------|----------|
| Definir alcance UAT | R | C | C | I | I |
| Elaborar plan operativo | A | C | R | C | I |
| Ejecución casos críticos | I | C | A | C | R |
| Gestión de defectos | A | C | R | R | C |
| Informe final UAT | R | C | C | C | A |
> Leyenda: R (Responsible), A (Accountable), C (Consulted), I (Informed)

---

## 4. GOBERNANZA Y REPORTING

### 4.1 Modelo de Reporting Diario
```markdown
# Daily UAT Status - [DD/MM/AAAA]

**Resumen general:** [Verde/Amarillo/Rojo]

## Métricas clave
- Cobertura acumulada: __%
- Defectos abiertos (P0/P1/P2): __/__/__
- SLA cumplidos: __%
- Tiempo medio de respuesta: __ min

## Riesgos / Bloqueos
1. [Descripción + impacto + propietario]

## Acciones para el día siguiente
- [ ] Acción 1 (Rol, fecha)
- [ ] Acción 2 (Rol, fecha)

**Emitido por:** UAT Manager
```

### 4.2 Protocolo de Reuniones
| Reunión | Frecuencia | Participantes | Objetivo | Output |
|---------|------------|---------------|----------|--------|
| Daily UAT | Diario | Todos los roles | Revisión de avance y bloqueos | Minuta + tablero actualizado |
| Revisión de defectos | Diario (16:00) | QA Facilitator, Developer, BA | Priorizar y planificar correcciones | Lista de acciones |
| Comité de riesgos | En caso crítico | UAT Manager, Sponsor | Decidir mitigaciones | Registro de decisión |
| Comité final GO/NO-GO | Fin del ciclo | Stakeholders clave | Aprobar liberación | Acta firmada |

---

## 5. CONTROL DOCUMENTAL Y AUDITORÍA

### 5.1 Repositorio de Evidencias ISO 1012
- Estructura: `Documentos/Auditoria/UAT/2025/`
  - `/Roles/` (documentos individuales)
  - `/Planes/` (plan maestro, mini planes)
  - `/Evidencias/` (capturas, logs, reportes)
  - `/Decisiones/` (actas, ADR, control de cambios)
  - `/Reportes/` (daily, semanal, consolidado)
- Convención de nombres: `YYYYMMDD_tipo_documento_version`
- Control de versiones: utilizar registros ISO 1012 con hash y firmas digitales

### 5.2 Checklist de Auditoría
- [ ] Plan maestro aprobado y versionado
- [ ] Matriz RACI firmada
- [ ] Evidencia de ejecución de todas las funcionalidades críticas
- [ ] Registro de defectos con ciclo completo
- [ ] Informe consolidado con métricas y análisis de riesgo
- [ ] Acta de GO/NO-GO firmada
- [ ] Lecciones aprendidas documentadas

---

## 6. MÉTRICAS Y KPIs DEL PROCESO

| Indicador | Definición | Objetivo | Frecuencia | Responsable |
|-----------|------------|----------|------------|-------------|
| Cobertura planificada | Casos ejecutados / planificados | ≥ 95% | Diario | QA Facilitator (reporta), UAT Manager (valida) |
| Cumplimiento cronograma | Hitos cumplidos / totales | ≥ 90% | Semanal | UAT Manager |
| Severidad defectos abiertos | % P0 y P1 sobre total | ≤ 10% | Diario | UAT Manager |
| Tiempo de resolución defectos críticos | Promedio en horas | ≤ 48h | Diario | Developer (reporta), UAT Manager (controla) |
| Satisfacción UAT User | Encuesta final | ≥ 4/5 | Fin del ciclo | UAT Manager |
| Calidad documental | % documentos con control ISO 1012 | 100% | Semanal | UAT Manager |

---

## 7. CHECKLIST DEL ROL

### Antes del UAT
- [ ] Alcance y funcionalidad crítica validados
- [ ] Plan maestro publicado y comunicado
- [ ] Matriz RACI y canales definidos
- [ ] Entorno Staging certificado
- [ ] Datos de prueba y accesos confirmados
- [ ] Calendario de reuniones agendado

### Durante el UAT
- [ ] Daily report emitido cada día
- [ ] Defectos priorizados y con responsable asignado
- [ ] Control de cambios actualizado
- [ ] Evidencia respaldada en repositorio auditable
- [ ] Riesgos evaluados y mitigaciones definidas

### Después del UAT
- [ ] Informe consolidado elaborado
- [ ] Comité GO/NO-GO realizado y documentado
- [ ] Sign-off registrado y archivado
- [ ] Plan de acción post-UAT documentado
- [ ] Transferencia de conocimiento a equipos productivos

---

## 8. BUENAS PRÁCTICAS

### 8.1 Liderazgo y Coordinación
1. Mantener comunicación proactiva con cada rol.
2. Resolver conflictos priorizando el compromiso con criterios de aceptación.
3. Asegurar la participación del UAT User en decisiones clave.
4. Proveer visibilidad ejecutiva constante (indicadores claros y concisos).

### 8.2 Gestión de Riesgos
- Identificar riesgos técnicos y de negocio diariamente.
- Clasificar riesgos (probabilidad, impacto, plan de mitigación).
- Documentar decisiones de aceptar, mitigar o transferir riesgos.
- Escalar oportunamente riesgos críticos al sponsor.

### 8.3 Conformidad ISO 1012
- Verificar que todos los artefactos tengan firma digital o trazabilidad.
- Mantener historial de cambios y versiones.
- Revisar cumplimiento de políticas de privacidad y seguridad en evidencias.
- Preparar paquete de auditoría antes del cierre del ciclo.

---

## 9. GLOSARIO

- **GO/NO-GO:** Decisión formal sobre la liberación del sistema tras UAT.
- **Plan maestro UAT:** Documento rector con calendario y responsabilidades.
- **Control de cambios UAT:** Procedimiento para gestionar ajustes durante pruebas.
- **Sponsor:** Ejecutivo responsable de aprobar la entrega.
- **Paquete de auditoría:** Conjunto de artefactos requeridos por control interno.

---

## 10. ANEXOS

### Anexo A: Formato de Informe Consolidado UAT
```markdown
# Informe Consolidado UAT - AURA360

**Periodo:** [Fecha inicio - Fecha fin]  
**Entorno:** Staging integrado  
**Roles participantes:** [Lista]

## 1. Resumen Ejecutivo
- Estado general: [Verde/Amarillo/Rojo]
- Recomendación: [GO / NO-GO / GO condicional]
- Principales hallazgos: 
  1. [Descripción]
  2. [Descripción]

## 2. Cobertura y Métricas
| Funcionalidad | Casos planificados | Ejecutados | Aprobados | Defectos P0/P1 | Estado |
|---------------|-------------------|------------|-----------|----------------|--------|
| Registro mediciones | | | | | |
| Dashboard ejecutivo | | | | | |
| Alertas de salud | | | | | |

## 3. Defectos Críticos
| ID | Descripción | Estado | Mitigación | ETA |
|----|-------------|--------|------------|-----|

## 4. Riesgos y Recomendaciones
- Riesgos: [Listado con impacto y probabilidad]
- Recomendaciones: [Acciones propuestas]

## 5. Decisión y Firmas
- UAT User: [Nombre, firma, fecha]
- UAT Manager: [Nombre, firma, fecha]
- Sponsor negocio: [Nombre, firma, fecha]
```

### Anexo B: Protocolo de Reunión GO/NO-GO
1. Presentación resumen métricas
2. Revisión de defectos abiertos y mitigaciones
3. Evaluación de riesgos residuales
4. Decisión formal (GO/NO-GO/Condicional)
5. Registro de compromisos post-UAT
6. Firma del acta y archivado ISO 1012

---

**Documento preparado conforme a:**
- ISO 1012 - Directrices de Gobierno para User Acceptance Testing
- Normativa interna de Auditoría AURA360 2025
- ITIL Service Transition (adaptado)

**Fin del documento**