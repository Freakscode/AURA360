# ROL: UAT User (Usuario Final / Negocio)

**Proyecto:** AURA360  
**Fecha:** 30 de octubre de 2025  
**Versión:** 1.0  
**Marco normativo:** ISO/IEC 25010:2011 - Calidad del Producto Software

---

## 1. DESCRIPCIÓN DEL ROL

El UAT User representa al usuario final o stakeholder del negocio que utilizará el sistema AURA360 en producción. Es responsable de validar que el sistema cumple con los requisitos de negocio y los criterios de aceptación definidos.

### 1.1 Objetivo Principal
Verificar que las funcionalidades implementadas satisfacen las necesidades del negocio y pueden ser utilizadas efectivamente en el entorno real de operación.

### 1.2 Perfil Requerido
- Conocimiento profundo del proceso de negocio
- Usuario final representativo del sistema
- Capacidad para tomar decisiones de aceptación
- Disponibilidad para dedicar tiempo a las pruebas

---

## 2. RESPONSABILIDADES ESPECÍFICAS

### 2.1 Fase de Planificación
- ✅ Participar en la reunión de kick-off del UAT
- ✅ Revisar y comprender los criterios de aceptación
- ✅ Validar que los escenarios de prueba reflejan casos de uso reales
- ✅ Confirmar disponibilidad de datos de prueba representativos
- ✅ Identificar condiciones especiales del negocio

### 2.2 Fase de Ejecución
- ✅ Ejecutar los casos de prueba en el entorno designado
- ✅ Simular escenarios reales de uso
- ✅ Validar que los resultados cumplen expectativas de negocio
- ✅ Reportar inmediatamente cualquier desviación o comportamiento inesperado
- ✅ Documentar observaciones sobre usabilidad y experiencia de usuario
- ✅ Probar flujos de trabajo completos end-to-end
- ✅ Verificar integración con procesos existentes

### 2.3 Fase de Evaluación
- ✅ Revisar todos los hallazgos registrados
- ✅ Clasificar la severidad de los defectos desde perspectiva de negocio
- ✅ Tomar decisión de aceptación o rechazo (GO/NO-GO)
- ✅ Justificar la decisión basándose en criterios de aceptación
- ✅ Firmar el acta de aceptación si aplica
- ✅ Proporcionar retroalimentación para mejoras futuras

---

## 3. CRITERIOS DE ACEPTACIÓN DEL ROL

### 3.1 Funcionalidad (ISO 25010)
| Criterio | Descripción | Estado |
|----------|-------------|--------|
| **Completitud funcional** | Todas las funcionalidades requeridas están presentes | ⬜ |
| **Corrección funcional** | Los resultados son precisos y consistentes | ⬜ |
| **Pertinencia funcional** | Las funciones facilitan las tareas especificadas | ⬜ |

### 3.2 Usabilidad (ISO 25010)
| Criterio | Descripción | Estado |
|----------|-------------|--------|
| **Reconocibilidad** | Es fácil entender qué hace el sistema | ⬜ |
| **Operabilidad** | Es fácil operar y controlar el sistema | ⬜ |
| **Protección contra errores** | El sistema previene errores del usuario | ⬜ |
| **Estética de UI** | La interfaz es agradable y apropiada | ⬜ |
| **Accesibilidad** | Puede ser usado por personas con diferentes capacidades | ⬜ |

### 3.3 Rendimiento (ISO 25010)
| Criterio | Descripción | Estado |
|----------|-------------|--------|
| **Tiempo de respuesta** | El sistema responde en tiempos aceptables | ⬜ |
| **Capacidad** | Soporta el volumen de usuarios/datos esperado | ⬜ |

---

## 4. PLANTILLA DE EJECUCIÓN DE PRUEBAS

### 4.1 Información del Caso de Prueba
```
ID del Caso: [UAT-XXX]
Módulo: [Nombre del módulo]
Funcionalidad: [Descripción breve]
Prioridad: [Alta/Media/Baja]
Fecha de Ejecución: [DD/MM/YYYY]
```

### 4.2 Pasos de Ejecución
```
Precondiciones:
- [Listar condiciones necesarias antes de iniciar]

Pasos:
1. [Acción específica a realizar]
   Resultado esperado: [Qué debe ocurrir]
   Resultado obtenido: [Qué ocurrió realmente]
   Estado: [✅ Pasó / ❌ Falló / ⚠️ Bloqueado]

2. [Siguiente acción]
   ...
```

### 4.3 Registro de Defectos
```
DEFECTO ENCONTRADO:
ID: [DEF-XXX]
Severidad: [Crítica/Alta/Media/Baja]
Descripción: [Qué falló]
Pasos para reproducir:
1. [Paso 1]
2. [Paso 2]
3. [...]

Resultado esperado: [Qué debería pasar]
Resultado actual: [Qué pasó]
Evidencia: [Capturas de pantalla, logs, etc.]
Impacto en el negocio: [Cómo afecta a la operación]
```

---

## 5. CHECKLIST DE ACTIVIDADES

### Antes de Iniciar las Pruebas
- [ ] He recibido y comprendido los criterios de aceptación
- [ ] Tengo acceso al entorno de pruebas
- [ ] Conozco los datos de prueba a utilizar
- [ ] He participado en la sesión de inducción
- [ ] Tengo claro el cronograma de pruebas

### Durante las Pruebas
- [ ] Ejecuto cada caso de prueba según lo planificado
- [ ] Registro todas las observaciones (positivas y negativas)
- [ ] Comunico inmediatamente los bloqueos
- [ ] Mantengo enfoque en escenarios de negocio reales
- [ ] No asumo comportamientos - los valido

### Al Finalizar las Pruebas
- [ ] He completado todos los casos de prueba asignados
- [ ] He documentado todos los hallazgos
- [ ] He participado en la sesión de cierre
- [ ] He proporcionado mi decisión de aceptación
- [ ] He firmado/aprobado la documentación final

---

## 6. MATRIZ DE DECISIÓN GO/NO-GO

### 6.1 Criterios para Aceptación (GO)
✅ **Se acepta el sistema cuando:**
- Todas las funcionalidades críticas funcionan correctamente
- Los defectos encontrados son de severidad baja o media y tienen workarounds
- El sistema cumple los criterios de aceptación definidos al 100%
- No existen defectos bloqueantes o críticos sin resolver
- La usabilidad permite operación eficiente
- El rendimiento es aceptable para la carga esperada

### 6.2 Criterios para Rechazo (NO-GO)
❌ **Se rechaza el sistema cuando:**
- Existen defectos críticos o bloqueantes sin resolver
- Funcionalidades críticas no funcionan o están incompletas
- El sistema no cumple requisitos legales o regulatorios
- Los criterios de aceptación no se cumplen en >20%
- El riesgo para el negocio es inaceptable
- No es posible realizar operaciones críticas del negocio

### 6.3 Criterios para Aceptación Condicional
⚠️ **Se acepta con condiciones cuando:**
- Defectos menores que no impactan operación crítica
- Mejoras de usabilidad deseables pero no bloqueantes
- Funcionalidades secundarias con issues menores
- Plan de corrección acordado y con fechas comprometidas

---

## 7. PLANTILLA DE REPORTE DE SESIÓN

```markdown
# Reporte de Sesión UAT - Usuario Final

**Fecha:** [DD/MM/YYYY]
**Sesión:** [Número/Identificador]
**Módulo Probado:** [Nombre]
**Duración:** [HH:MM]

## Casos Ejecutados
- Total de casos: [X]
- Casos exitosos: [X]
- Casos fallidos: [X]
- Casos bloqueados: [X]

## Observaciones Principales
1. [Observación 1]
2. [Observación 2]
3. [...]

## Aspectos Positivos
- [Qué funcionó bien]
- [Qué superó expectativas]

## Aspectos a Mejorar
- [Qué necesita ajustes]
- [Qué dificulta el uso]

## Bloqueos Actuales
- [Descripción de bloqueos]

## Siguiente Sesión
- [Qué se probará]
- [Fecha programada]

**Preparado por:** [Nombre UAT User]
**Firma:** ________________
```

---

## 8. BUENAS PRÁCTICAS

### 8.1 Durante la Ejecución
1. **Piensa como usuario final real**, no como tester técnico
2. **Prueba flujos completos**, no solo funciones aisladas
3. **Usa datos realistas** que reflejen escenarios reales
4. **Documenta TODO**, incluso lo que funciona bien
5. **Sé específico** en las descripciones de problemas
6. **No asumas conocimiento técnico** - si algo es confuso, repórtalo
7. **Valida mensajes de error** - deben ser claros para usuarios de negocio

### 8.2 Comunicación
1. Reporta problemas inmediatamente, no al final
2. Describe el impacto en el negocio, no solo el síntoma técnico
3. Proporciona contexto de cómo afecta el trabajo diario
4. Sé constructivo en la retroalimentación
5. Mantén comunicación abierta con QA y Developer

### 8.3 Enfoque de Negocio
1. Prioriza escenarios que reflejan casos de uso reales
2. Valida que los procesos de negocio se pueden completar
3. Verifica cumplimiento de políticas y regulaciones
4. Considera diferentes perfiles de usuario
5. Evalúa la eficiencia vs. proceso actual

---

## 9. CONTACTOS Y ESCALAMIENTO

| Rol | Nombre | Contacto | Cuándo Contactar |
|-----|--------|----------|------------------|
| QA Facilitator | [Nombre] | [Email/Tel] | Dudas sobre casos de prueba |
| Business Analyst | [Nombre] | [Email/Tel] | Clarificación de requisitos |
| Developer | [Nombre] | [Email/Tel] | Preguntas técnicas |
| UAT Manager | [Nombre] | [Email/Tel] | Bloqueos o decisiones mayores |

---

## 10. GLOSARIO

- **UAT (User Acceptance Testing):** Pruebas de aceptación del usuario
- **Criterios de Aceptación:** Condiciones que debe cumplir el sistema para ser aceptado
- **Defecto Crítico:** Error que impide operación crítica del negocio
- **Defecto Bloqueante:** Error que impide continuar las pruebas
- **Workaround:** Solución temporal o alternativa
- **GO/NO-GO:** Decisión de aceptar o rechazar el sistema
- **End-to-End:** Flujo completo desde inicio hasta fin
- **Escenario de negocio:** Caso de uso real del sistema en operación

---

## 11. ANEXOS

### Anexo A: Ejemplo de Caso de Prueba Completado
```
ID: UAT-001
Módulo: Gestión de Planes Nutricionales
Funcionalidad: Crear plan nutricional para usuario

EJECUCIÓN:
Paso 1: Iniciar sesión como nutricionista
✅ PASÓ - Login exitoso en 2 segundos

Paso 2: Navegar a "Crear Plan Nutricional"
✅ PASÓ - Botón visible y funcional

Paso 3: Ingresar datos del plan (nombre, objetivo, duración)
❌ FALLÓ - Campo "duración" no acepta más de 30 días
Severidad: ALTA
ID Defecto: DEF-001

Paso 4: Guardar plan
⚠️ BLOQUEADO - No se pudo ejecutar por fallo en Paso 3

DECISIÓN: NO-GO hasta resolver DEF-001
IMPACTO: Los planes típicos duran 60-90 días
```

### Anexo B: Template de Sign-Off Final
```
CERTIFICADO DE ACEPTACIÓN UAT

Yo, [Nombre del UAT User], en representación de [Área/Departamento],
certifico que:

☐ He ejecutado los casos de prueba asignados
☐ He validado los criterios de aceptación
☐ He reportado todos los hallazgos
☐ He revisado el informe consolidado

DECISIÓN FINAL: ☐ GO  ☐ NO-GO  ☐ GO CONDICIONAL

JUSTIFICACIÓN:
[Explicación de la decisión basada en criterios de aceptación
y su impacto en el negocio]

CONDICIONES (si aplica):
[Listar condiciones para aceptación]

Firma: ________________
Fecha: ________________
```

---

**Documento preparado conforme a:**
- ISO/IEC 25010:2011 - Systems and software Quality Requirements and Evaluation (SQuaRE)
- ISTQB Advanced Level Test Manager
- PMI - Project Management Body of Knowledge (PMBOK)

**Fin del documento**
