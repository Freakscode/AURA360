# ROL: Business Analyst (Analista de Negocio)

**Proyecto:** AURA360  
**Fecha:** 30 de octubre de 2025  
**Versión:** 1.0  
**Marco normativo:** ISO/IEC 25010:2011 - Calidad del Producto Software

---

## 1. DESCRIPCIÓN DEL ROL

El Business Analyst actúa como puente entre el negocio y el equipo técnico durante el proceso de UAT. Es responsable de asegurar que todos los participantes comprendan los requisitos, criterios de aceptación y el valor de negocio de cada funcionalidad.

### 1.1 Objetivo Principal
Garantizar que las pruebas UAT validen efectivamente que el sistema cumple con los requisitos de negocio y aporta el valor esperado a la organización.

### 1.2 Perfil Requerido
- Conocimiento profundo de los procesos de negocio de AURA360
- Experiencia en análisis y documentación de requisitos
- Habilidades de comunicación y facilitación
- Capacidad para traducir lenguaje técnico a lenguaje de negocio
- Conocimiento de metodologías ágiles (Historias de Usuario)

---

## 2. RESPONSABILIDADES ESPECÍFICAS

### 2.1 Fase de Planificación
- ✅ Preparar y refinar las Historias de Usuario (HU) antes del UAT
- ✅ Definir y documentar criterios de aceptación claros y medibles
- ✅ Explicar el contexto de negocio de cada funcionalidad
- ✅ Identificar casos de uso críticos y escenarios edge cases
- ✅ Validar que los casos de prueba cubren todos los criterios de aceptación
- ✅ Preparar material de referencia (glosario, diagramas de proceso, etc.)
- ✅ Coordinar sesión de kick-off con todo el equipo

### 2.2 Fase de Ejecución
- ✅ Explicar requisitos y criterios de aceptación al equipo
- ✅ Aclarar dudas sobre comportamientos esperados del sistema
- ✅ Validar que las pruebas se enfocan en objetivos de negocio
- ✅ Interpretar resultados desde perspectiva de negocio
- ✅ Ayudar a priorizar defectos según impacto en el negocio
- ✅ Actualizar documentación de requisitos si es necesario
- ✅ Mantener trazabilidad entre requisitos y casos de prueba

### 2.3 Fase de Evaluación
- ✅ Analizar si los requisitos fueron satisfechos
- ✅ Evaluar el impacto de negocio de defectos encontrados
- ✅ Aportar perspectiva de negocio en decisión GO/NO-GO
- ✅ Documentar lecciones aprendidas para futuros desarrollos
- ✅ Identificar oportunidades de mejora en requisitos
- ✅ Contribuir al informe final de UAT

---

## 3. DOCUMENTACIÓN DE REQUISITOS

### 3.1 Template de Historia de Usuario Refinada

```markdown
## Historia de Usuario: [ID-XXX]

**Como:** [Rol del usuario]
**Quiero:** [Acción/Funcionalidad deseada]
**Para:** [Beneficio/Valor de negocio]

### Contexto de Negocio
[Explicación del problema de negocio que resuelve esta funcionalidad]
[Por qué es importante para la organización]
[Cómo se relaciona con objetivos estratégicos]

### Criterios de Aceptación

#### CA-01: [Nombre descriptivo del criterio]
**Dado que:** [Precondición/Contexto inicial]
**Cuando:** [Acción/Evento que ocurre]
**Entonces:** [Resultado esperado]

**Validación:**
- [ ] [Punto de verificación específico 1]
- [ ] [Punto de verificación específico 2]
- [ ] [Punto de verificación específico 3]

**Métricas de éxito:**
- [Métrica cuantificable 1]
- [Métrica cuantificable 2]

#### CA-02: [Siguiente criterio]
[...]

### Reglas de Negocio
1. **RN-01:** [Regla específica que debe cumplirse]
2. **RN-02:** [Otra regla de negocio]

### Casos de Uso Principales
1. **Flujo Principal:** [Descripción del camino feliz]
2. **Flujos Alternativos:** [Variaciones válidas del flujo]
3. **Flujos de Excepción:** [Qué pasa cuando algo sale mal]

### Dependencias
- **Sistemas:** [Sistemas externos o internos relacionados]
- **Datos:** [Datos que deben existir previamente]
- **Usuarios:** [Roles o permisos necesarios]

### Supuestos y Restricciones
- [Supuesto 1]
- [Restricción 1]

### Definición de "Terminado" (DoD)
- [ ] Código implementado y revisado
- [ ] Pruebas unitarias pasando
- [ ] Pruebas de integración pasando
- [ ] Documentación actualizada
- [ ] UAT completado exitosamente
- [ ] Sin defectos críticos o bloqueantes

### Valor de Negocio
**Prioridad:** [Alta/Media/Baja]
**Impacto:** [Descripción del impacto esperado]
**ROI Estimado:** [Si aplica]
```

### 3.2 Matriz de Trazabilidad

| ID Requisito | Historia Usuario | Criterios Aceptación | Casos Prueba UAT | Prioridad | Estado |
|--------------|------------------|----------------------|-------------------|-----------|---------|
| REQ-001 | HU-001 | CA-01, CA-02, CA-03 | UAT-001, UAT-002 | Alta | ⬜ |
| REQ-002 | HU-002 | CA-04, CA-05 | UAT-003 | Media | ⬜ |

---

## 4. FACILITACIÓN DE SESIONES

### 4.1 Agenda de Sesión de Kick-Off UAT

```markdown
# Sesión de Kick-Off UAT - AURA360
**Fecha:** [DD/MM/YYYY]
**Duración:** 90 minutos
**Facilitador:** Business Analyst

## Agenda

### 1. Introducción (10 min)
- Objetivos del UAT
- Roles y responsabilidades
- Cronograma general

### 2. Contexto del Proyecto (15 min)
- Visión general de AURA360
- Módulos a probar en este ciclo
- Relación con objetivos de negocio

### 3. Explicación de Requisitos (30 min)
Por cada módulo/funcionalidad:
- Historia de Usuario
- Criterios de Aceptación
- Casos de uso críticos
- Demostración rápida (si está disponible)

### 4. Proceso de Pruebas (15 min)
- Cómo ejecutar casos de prueba
- Cómo reportar defectos
- Canales de comunicación
- Manejo de bloqueos

### 5. Entorno y Datos de Prueba (10 min)
- Acceso al ambiente de UAT
- Datos de prueba disponibles
- Credenciales y permisos

### 6. Preguntas y Respuestas (10 min)
- Aclaraciones
- Dudas específicas

### 7. Próximos Pasos (5 min)
- Primera sesión de pruebas
- Entregables esperados
- Punto de contacto

## Materiales Requeridos
- [ ] Documentación de HU refinadas
- [ ] Matriz de casos de prueba
- [ ] Guía de acceso al entorno
- [ ] Glosario de términos
- [ ] Diagrama de arquitectura (alto nivel)
```

### 4.2 Script de Explicación de Requisitos

```markdown
## Script para Explicar [Nombre de Funcionalidad]

### 1. Problema de Negocio
"El problema que estamos resolviendo es..."
[Explicar en lenguaje simple el problema actual]

### 2. Solución Propuesta
"Lo que hemos construido permite..."
[Describir la funcionalidad en términos de negocio]

### 3. Beneficios Esperados
"Con esto, los usuarios podrán..."
- [Beneficio 1]
- [Beneficio 2]
- [Beneficio 3]

### 4. Flujo Principal (Demostración)
"Déjenme mostrarles cómo funciona paso a paso..."
Paso 1: [Acción]
Paso 2: [Acción]
[...]

### 5. Casos Especiales
"Situaciones importantes a validar..."
- [Caso especial 1]
- [Caso especial 2]

### 6. Criterios de Éxito
"Sabremos que funciona correctamente cuando..."
- [Criterio 1]
- [Criterio 2]

### 7. Preguntas Guía para UAT User
"Al probar, pregúntense..."
- ¿Esto resuelve mi problema real?
- ¿Es intuitivo de usar?
- ¿Qué falta para que sea perfecto?
```

---

## 5. ANÁLISIS DE FUNCIONALIDADES CRÍTICAS

### 5.1 Matriz de Criticidad

| Funcionalidad | Impacto Negocio | Frecuencia Uso | Complejidad | Riesgo | Prioridad UAT |
|---------------|-----------------|----------------|-------------|--------|---------------|
| Login/Autenticación | Crítico | Muy Alta | Media | Alto | P0 |
| Creación Plan Nutricional | Crítico | Alta | Alta | Alto | P0 |
| Registro Mediciones Corporales | Alto | Alta | Media | Medio | P1 |
| Visualización Dashboard | Alto | Alta | Media | Medio | P1 |
| Exportación Reportes | Medio | Media | Baja | Bajo | P2 |

**Leyenda de Prioridades:**
- **P0:** Funcionalidad crítica - debe funcionar perfectamente para GO
- **P1:** Funcionalidad importante - defectos mayores bloquean GO
- **P2:** Funcionalidad deseable - defectos menores aceptables

### 5.2 Análisis de Impacto de Negocio

```markdown
## Funcionalidad: [Nombre]

### Impacto en el Negocio
**Criticidad:** [Crítica/Alta/Media/Baja]

**Si falla, el impacto es:**
- **Operacional:** [Cómo afecta operaciones diarias]
- **Financiero:** [Costo potencial de falla]
- **Reputacional:** [Efecto en imagen o satisfacción]
- **Legal/Regulatorio:** [Cumplimiento afectado]
- **Usuarios Afectados:** [Cantidad/Tipo de usuarios]

### Frecuencia de Uso
- **Diaria:** X usuarios
- **Semanal:** X usuarios  
- **Mensual:** X usuarios

### Alternativas si Falla
- [ ] Existe proceso manual de contingencia
- [ ] No existe alternativa (bloqueante crítico)
- [ ] Puede postponerse temporalmente
- [ ] Workaround disponible: [Descripción]

### Dependencias
- **Upstream:** [Qué debe funcionar antes]
- **Downstream:** [Qué depende de esto]

### Justificación de Prioridad
[Explicar por qué esta prioridad es apropiada]
```

---

## 6. GESTIÓN DE CRITERIOS DE ACEPTACIÓN

### 6.1 Checklist de Calidad de Criterios

Para cada criterio de aceptación, verificar que cumple:

#### Características INVEST
- [ ] **Independent** (Independiente): No depende de otros criterios
- [ ] **Negotiable** (Negociable): Puede discutirse cómo implementarlo
- [ ] **Valuable** (Valioso): Aporta valor claro al negocio
- [ ] **Estimable** (Estimable): Se puede estimar esfuerzo
- [ ] **Small** (Pequeño): Suficientemente específico
- [ ] **Testable** (Testeable): Se puede probar objetivamente

#### Formato SMART
- [ ] **Specific** (Específico): Claro y sin ambigüedad
- [ ] **Measurable** (Medible): Resultado cuantificable o verificable
- [ ] **Achievable** (Alcanzable): Técnicamente posible
- [ ] **Relevant** (Relevante): Alineado con objetivos de negocio
- [ ] **Time-bound** (Temporal): Con límite de tiempo si aplica

### 6.2 Ejemplos de Criterios Bien Definidos

#### ✅ BUEN EJEMPLO
```
CA-01: Validación de formato de email
Dado que: un usuario está registrándose
Cuando: ingresa un email en formato inválido (sin @, sin dominio)
Entonces: 
- El sistema muestra mensaje de error "Email inválido"
- El botón "Registrar" permanece deshabilitado
- El campo email se marca con borde rojo
- El mensaje desaparece cuando se corrige el formato
```

#### ❌ MAL EJEMPLO
```
CA-01: El email debe ser válido
(Demasiado vago, no testeable objetivamente)
```

### 6.3 Plantilla de Refinamiento de Criterios

```markdown
## Criterio Original
[Criterio como fue definido inicialmente]

## Problemas Identificados
- [ ] Ambiguo
- [ ] No medible
- [ ] Falta contexto
- [ ] Muy general

## Criterio Refinado
**Dado que:** [Contexto específico]
**Cuando:** [Acción concreta]
**Entonces:** [Resultado observable y medible]

## Ejemplo Concreto
[Caso específico con datos reales]

## Forma de Validación
1. [Paso verificable 1]
2. [Paso verificable 2]
3. [...]

## Resultado Esperado vs No Esperado
✅ Esperado: [Descripción]
❌ No esperado: [Qué NO debe pasar]
```

---

## 7. COMUNICACIÓN Y FACILITACIÓN

### 7.1 Plan de Comunicación UAT

| Audiencia | Mensaje Clave | Frecuencia | Canal | Responsable |
|-----------|---------------|------------|-------|-------------|
| UAT Team completo | Estado general | Diario | Email/Slack | BA + UAT Manager |
| UAT User | Aclaraciones requisitos | On-demand | Presencial/Video | BA |
| Developer | Validación técnica | On-demand | Chat/Reunión | BA |
| Stakeholders | Progreso UAT | Semanal | Reporte | BA + UAT Manager |

### 7.2 FAQ (Preguntas Frecuentes)

```markdown
## Preguntas Frecuentes sobre Requisitos

### General

**P: ¿Qué es un criterio de aceptación?**
R: Es una condición específica que debe cumplir el sistema para que la funcionalidad sea aceptada. Define el "listo" desde perspectiva de negocio.

**P: ¿Qué diferencia hay entre requisito y criterio de aceptación?**
R: El requisito describe QUÉ necesita el negocio. El criterio de aceptación define CÓMO se validará que se cumplió.

**P: ¿Pueden cambiar los criterios durante UAT?**
R: Idealmente no. Si se descubre algo crítico omitido, se debe evaluar impacto, documentar el cambio y potencialmente re-planificar.

### Específicas de AURA360

**P: ¿Qué se considera un "plan nutricional válido"?**
R: [Explicación específica con ejemplo]

**P: ¿Cuándo un usuario está "activo"?**
R: [Definición clara del negocio]

**P: ¿Qué nivel de precisión se requiere en mediciones corporales?**
R: [Especificación exacta]

[Agregar más según el proyecto]
```

### 7.3 Técnicas de Facilitación

#### Para Resolver Ambigüedades
1. **Técnica de "5 Whys"**
   - Preguntar "¿Por qué?" 5 veces para llegar a la raíz
   - Ejemplo: "¿Por qué necesitan esta validación?" → ... → Requisito real

2. **Ejemplos Concretos**
   - Pedir al usuario que dé un ejemplo específico
   - Convertir el ejemplo en criterio testeable

3. **Diagramas de Flujo**
   - Visualizar el proceso esperado
   - Identificar puntos de decisión

4. **Prototipado Rápido**
   - Mostrar mockups o flujo actual
   - "¿Así o diferente?"

---

## 8. CHECKLIST DE ACTIVIDADES DEL BA

### Fase de Preparación (1-2 semanas antes)
- [ ] Revisar y refinar todas las HU del alcance UAT
- [ ] Validar criterios de aceptación con stakeholders
- [ ] Preparar material de referencia (glosario, diagramas)
- [ ] Coordinar con QA la cobertura de casos de prueba
- [ ] Identificar funcionalidades críticas
- [ ] Agendar sesión de kick-off
- [ ] Preparar presentación de requisitos
- [ ] Validar disponibilidad de datos de prueba

### Durante la Planificación
- [ ] Facilitar sesión de kick-off
- [ ] Explicar cada HU y sus criterios
- [ ] Responder preguntas del equipo
- [ ] Validar comprensión común
- [ ] Documentar acuerdos y decisiones
- [ ] Establecer canales de comunicación

### Durante la Ejecución
- [ ] Estar disponible para aclaraciones
- [ ] Participar en revisiones de defectos
- [ ] Ayudar a priorizar issues según impacto
- [ ] Actualizar documentación si es necesario
- [ ] Mantener comunicación con stakeholders
- [ ] Documentar cambios o desviaciones

### Durante la Evaluación
- [ ] Revisar todos los resultados
- [ ] Analizar cumplimiento de criterios
- [ ] Evaluar impacto de defectos en negocio
- [ ] Participar en decisión GO/NO-GO
- [ ] Documentar lecciones aprendidas
- [ ] Contribuir al informe final
- [ ] Planificar follow-up si es necesario

---

## 9. HERRAMIENTAS Y TEMPLATES

### 9.1 Matriz de Cobertura Requisitos-Pruebas

```markdown
| Historia Usuario | Criterio | Caso Prueba | Cobertura | Notas |
|------------------|----------|-------------|-----------|-------|
| HU-001 | CA-01 | UAT-001, UAT-002 | ✅ 100% | |
| HU-001 | CA-02 | UAT-003 | ✅ 100% | |
| HU-002 | CA-03 | - | ❌ 0% | Falta caso de prueba |
```

### 9.2 Template de Análisis de Gap

```markdown
## Análisis de Brechas - [Módulo]

### Requisito Original
[Lo que se pidió inicialmente]

### Implementación Actual
[Lo que realmente se construyó]

### Diferencias Identificadas
1. [Gap 1]
   - Impacto: [Alto/Medio/Bajo]
   - Acción: [Ajustar requisito / Ajustar implementación / Aceptar]
   
2. [Gap 2]
   [...]

### Recomendaciones
- [Recomendación 1]
- [Recomendación 2]
```

### 9.3 Registro de Decisiones (ADR - Architecture Decision Record)

```markdown
## Decisión de Requisito: [ID-XXX]

**Fecha:** [DD/MM/YYYY]
**Estado:** [Propuesta/Aceptada/Rechazada/Superada]

### Contexto
[Situación que requiere una decisión]

### Decisión
[Qué se decidió]

### Consecuencias
**Positivas:**
- [Beneficio 1]
- [Beneficio 2]

**Negativas:**
- [Trade-off 1]
- [Trade-off 2]

### Alternativas Consideradas
1. [Alternativa 1] - Rechazada porque [razón]
2. [Alternativa 2] - Rechazada porque [razón]

### Participantes
- [Nombre 1] - [Rol]
- [Nombre 2] - [Rol]
```

---

## 10. MÉTRICAS Y KPIs

### 10.1 Métricas de Calidad de Requisitos

| Métrica | Fórmula | Objetivo | Actual |
|---------|---------|----------|--------|
| **Claridad de Requisitos** | % HU sin ambigüedades | >95% | __% |
| **Cobertura de Criterios** | # Criterios / # Requisitos | >3 por HU | __ |
| **Trazabilidad** | % Criterios con casos de prueba | 100% | __% |
| **Cambios durante UAT** | # Cambios de criterios / # Total criterios | <5% | __% |
| **Comprensión del Equipo** | % Equipo que entiende requisitos | 100% | __% |

### 10.2 Indicadores de Éxito del BA

- ✅ Cero bloqueos por falta de claridad en requisitos
- ✅ Todos los criterios de aceptación son testeables
- ✅ UAT User puede validar sin escalamiento constante
- ✅ Trazabilidad completa requisito → criterio → prueba
- ✅ Documentación actualizada y accesible

---

## 11. GESTIÓN DE CAMBIOS

### 11.1 Proceso de Cambio de Requisito Durante UAT

```markdown
## Solicitud de Cambio: [ID]

### 1. Identificación
**Fecha:** [DD/MM/YYYY]
**Solicitante:** [Nombre - Rol]
**Tipo:** [Nuevo requisito / Modificación / Aclaración / Corrección]

### 2. Descripción
**Requisito Actual:**
[Estado actual]

**Cambio Propuesto:**
[Qué se quiere cambiar]

**Justificación:**
[Por qué es necesario]

### 3. Análisis de Impacto
**Impacto en:**
- Casos de prueba: [Alto/Medio/Bajo/Ninguno]
- Cronograma: [Días de retraso estimados]
- Recursos: [Esfuerzo adicional requerido]
- Otros requisitos: [Dependencias afectadas]

**Riesgo si NO se implementa:**
[Consecuencias de no hacer el cambio]

### 4. Decisión
☐ Aprobado - Implementar inmediatamente
☐ Aprobado - Para siguiente versión
☐ Rechazado - Razón: [____________]
☐ En análisis - Necesita más información

**Aprobadores:**
- [ ] Business Analyst
- [ ] UAT Manager
- [ ] Stakeholder clave

### 5. Plan de Implementación (si aprobado)
1. [Acción 1]
2. [Acción 2]
3. [...]

**Fecha compromiso:** [DD/MM/YYYY]
```

---

## 12. BUENAS PRÁCTICAS

### 12.1 Principios Fundamentales

1. **Claridad sobre Concisión**
   - Es mejor ser explícito y largo que breve y ambiguo
   - Use ejemplos concretos siempre que sea posible

2. **Lenguaje del Negocio**
   - Evite jerga técnica en documentación para usuarios
   - Traduzca conceptos técnicos a términos de negocio

3. **Pensamiento Crítico**
   - Cuestione supuestos
   - Valide que cada requisito agrega valor real
   - No asuma que "obvio" es lo mismo para todos

4. **Documentación Viva**
   - Actualice documentos cuando haya cambios
   - Marque versiones y fecha de actualización
   - Mantenga historial de cambios significativos

5. **Colaboración Continua**
   - UAT no es "validación al final", es colaboración durante
   - Involucre a usuarios temprano y frecuentemente
   - Genere feedback loops cortos

### 12.2 Anti-patrones a Evitar

❌ **"Funciona en mi ambiente"**
- Siempre validar en ambiente de UAT real

❌ **"Supuse que era obvio"**
- Documentar explícitamente todo comportamiento esperado

❌ **"Ya lo explicamos antes"**
- Estar dispuesto a re-explicar con paciencia

❌ **"Es un problema técnico, no de requisitos"**
- Si el usuario no entiende o no puede usar, ES un problema de requisitos

❌ **"Cambiaremos los requisitos sobre la marcha"**
- Control de cambios formal para mantener trazabilidad

---

## 13. GLOSARIO DEL BA

- **Criterio de Aceptación (CA):** Condición verificable que debe cumplirse para aceptar una funcionalidad
- **Historia de Usuario (HU):** Descripción simple de una funcionalidad desde perspectiva del usuario
- **Regla de Negocio (RN):** Política o restricción del negocio que el sistema debe respetar
- **Flujo Alternativo:** Variación válida del flujo principal
- **Flujo de Excepción:** Camino cuando ocurre un error o condición no esperada
- **Trazabilidad:** Capacidad de rastrear un requisito desde su origen hasta su prueba
- **Refinamiento:** Proceso de agregar detalle y claridad a requisitos de alto nivel
- **DoD (Definition of Done):** Checklist que define cuándo una funcionalidad está completa

---

## 14. CONTACTOS Y ESCALAMIENTO

| Situación | Acción | Contacto |
|-----------|--------|----------|
| Ambigüedad en requisito | Clarificar con stakeholder | [Product Owner] |
| Cambio de alcance | Proceso de control de cambios | [UAT Manager] |
| Conflicto de prioridades | Escalamiento | [Sponsor/Director] |
| Duda técnica profunda | Consultar arquitectura | [Tech Lead] |

---

## 15. ANEXOS

### Anexo A: Ejemplo Completo de HU Refinada para AURA360

```markdown
## HU-001: Crear Plan Nutricional Personalizado

**Como:** Nutricionista de AURA360
**Quiero:** Crear un plan nutricional personalizado para un usuario
**Para:** Proporcionar orientación nutricional específica basada en objetivos y condiciones individuales

### Contexto de Negocio
Los usuarios de AURA360 buscan mejorar su salud holística. Un componente crítico es la nutrición personalizada. Los nutricionistas necesitan una herramienta que les permita crear planes adaptados considerando:
- Objetivos del usuario (pérdida de peso, ganancia muscular, mantenimiento)
- Restricciones alimentarias (alergias, preferencias dietéticas)
- Condiciones de salud existentes

Esto permite a AURA360 diferenciarse por ofrecer planes verdaderamente personalizados vs. plantillas genéricas.

### Criterios de Aceptación

#### CA-01: Ingreso de Información Básica del Plan
**Dado que:** un nutricionista autenticado accede al módulo de planes
**Cuando:** hace clic en "Crear Nuevo Plan" e ingresa:
- Nombre del plan: "Plan de Juan - Pérdida de Peso Q1"
- Usuario objetivo: "Juan Pérez" (seleccionado de lista)
- Objetivo: "Pérdida de Peso" (dropdown)
- Duración: 90 días
- Fecha inicio: 01/01/2026
**Entonces:**
- El sistema guarda el plan con estado "Borrador"
- Asigna ID único (ej: NP-001)
- Calcula fecha fin automáticamente (01/04/2026)
- Permite continuar a configuración de macros

**Validación:**
- [ ] Plan aparece en lista de planes del nutricionista
- [ ] Plan aparece en perfil del usuario con estado "Borrador"
- [ ] Fechas calculadas correctamente
- [ ] No permite duración <7 días o >365 días

#### CA-02: Configuración de Macronutrientes
**Dado que:** un plan en borrador está creado
**Cuando:** el nutricionista configura:
- Calorías diarias objetivo: 1800 kcal
- Distribución de macros: 
  - Proteínas: 30% (135g)
  - Carbohidratos: 40% (180g)
  - Grasas: 30% (60g)
**Entonces:**
- Sistema calcula gramos automáticamente basado en porcentajes
- Valida que suma sea 100%
- Muestra previsualización de distribución

**Validación:**
- [ ] Cálculos matemáticos correctos (1g proteína=4kcal, 1g carbs=4kcal, 1g grasa=9kcal)
- [ ] Alerta si distribución no suma 100%
- [ ] Permite ajuste fino manual
- [ ] Rango válido: 1200-4000 kcal

#### CA-03: Definir Restricciones y Preferencias
[...]

### Reglas de Negocio
1. **RN-01:** Solo nutricionistas certificados pueden crear planes
2. **RN-02:** Un usuario puede tener máximo 1 plan activo simultáneamente
3. **RN-03:** Planes en borrador expiran después de 30 días sin activar
4. **RN-04:** Modificaciones a plan activo requieren aprobación del usuario

### Valor de Negocio
**Prioridad:** P0 - Crítica
**Impacto:** Funcionalidad core del producto
**Usuarios beneficiados:** 100% de usuarios premium
**ROI:** Diferenciador clave para conversión freemium → premium
```

### Anexo B: Checklist Pre-UAT del BA

```markdown
# Checklist de Preparación UAT - Business Analyst

## Documentación
- [ ] Todas las HU refinadas y aprobadas
- [ ] Criterios de aceptación SMART para cada HU
- [ ] Reglas de negocio documentadas
- [ ] Glosario de términos actualizado
- [ ] Diagramas de flujo preparados
- [ ] Matriz de trazabilidad completa

## Coordinación
- [ ] Sesión kick-off agendada
- [ ] Todos los participantes confirmados
- [ ] Material de presentación preparado
- [ ] Ambiente de UAT validado
- [ ] Datos de prueba cargados

## Validación
- [ ] QA ha revisado cobertura de casos de prueba
- [ ] Developer ha validado factibilidad técnica
- [ ] UAT User ha recibido documentación preliminar
- [ ] Stakeholders alineados con criterios

## Riesgos
- [ ] Riesgos identificados y mitigados
- [ ] Plan B para bloqueos críticos
- [ ] Escalamiento definido

✅ READY para iniciar UAT cuando todos los items están completos
```

---

**Documento preparado conforme a:**
- ISO/IEC 25010:2011 - Systems and software Quality Requirements and Evaluation (SQuaRE)
- IIBA BABOK v3 - Business Analysis Body of Knowledge
- ISTQB Advanced Level Test Analyst
- Agile Extension to the BABOK Guide

**Fin del documento**
