# Funcionalidades de Gestión de Pacientes - AURA360

## 📋 Resumen

Se implementaron 3 funcionalidades principales para la gestión de pacientes por parte de profesionales de salud:

1. ✅ **Vista de Detalle del Paciente** con perfil completo, historial y plan nutricional
2. ✅ **Búsqueda y Filtros** en la lista de pacientes (nombre/email, estado, ordenamiento)
3. ✅ **Asignación de Nuevos Pacientes** mediante modal interactivo

---

## 🎯 Funcionalidad 1: Vista de Detalle del Paciente

### Ruta
`/profesional/pacientes/:id`

### Componente
`src/app/features/profesional/pages/patient-detail/patient-detail.component.ts`

### Características

#### Información Personal
- Nombre completo
- Email
- Teléfono
- Edad
- Género
- Rol en el sistema

#### Relación de Cuidado
- Tipo de contexto (Independiente/Institucional)
- Fecha de inicio de la relación
- Fecha de finalización (si aplica)
- Notas sobre la relación
- Estado actual (Activo/Inactivo/Finalizado)

#### Historial de Consultas (Placeholder)
- Estructura preparada para listar consultas
- Mock data de ejemplo
- Botón "Nueva Consulta" (preparado para implementación)
- Diseño de cards para cada consulta

#### Plan Nutricional (Placeholder)
- Estructura preparada para el plan
- Mock data con:
  - Objetivo del plan
  - Calorías diarias recomendadas
  - Última actualización
  - Lista de recomendaciones nutricionales
- Botón "Editar Plan" (preparado para implementación)

#### Acciones
- ✅ **Finalizar Relación**: Marca la relación como finalizada
- ✅ **Volver a la Lista**: Navegación de regreso
- ✅ **Breadcrumb**: Dashboard > Pacientes > [Nombre]

### Navegación
- Click en cualquier fila de la tabla de pacientes
- Las filas tienen efecto hover y cursor pointer
- Animación smooth al hover

---

## 🔍 Funcionalidad 2: Búsqueda y Filtros

### Ubicación
`/profesional/pacientes`

### Componente Actualizado
`src/app/features/profesional/pages/patients-list/patients-list.component.ts`

### Características Implementadas

#### 2.1 Búsqueda en Tiempo Real
- **Campo de búsqueda** con placeholder claro
- **Búsqueda reactiva** usando Angular Signals
- **Búsqueda por**:
  - Nombre del paciente (case-insensitive)
  - Email del paciente (case-insensitive)
- **Botón de limpieza** (✕) que aparece cuando hay texto
- **Actualizaci\u00f3n automática** de resultados

#### 2.2 Filtros por Estado
- **Dropdown selector** con opciones:
  - **Todos**: Muestra todos los pacientes
  - **Activos**: Solo pacientes con relación activa
  - **Inactivos**: Pacientes con relación inactiva o finalizada
- **Cambio reactivo** al seleccionar una opción
- **Contador "Mostrando"** que refleja el filtro aplicado

#### 2.3 Ordenamiento
- **Botones de ordenamiento**:
  - **Por Nombre**: Orden alfabético A-Z o Z-A
  - **Por Fecha**: Orden cronológico por fecha de inicio
- **Indicador visual**:
  - Botón activo resaltado en verde
  - Flecha ↑ para ascendente
  - Flecha ↓ para descendente
- **Toggle**: Click nuevamente invierte la dirección

#### 2.4 Contador Dinámico
- **4 Cards de resumen**:
  1. Activos: Pacientes con relación activa
  2. Inactivos: Pacientes con relación no activa
  3. Total: Todos los pacientes
  4. **Mostrando**: Pacientes visibles después de filtros (destacado en verde)

#### 2.5 Botón Limpiar Filtros
- Aparece cuando no hay resultados pero hay filtros activos
- Resetea búsqueda, filtro de estado y ordenamiento
- Un solo click restaura la vista completa

### Implementación Técnica
```typescript
// Búsqueda reactiva
readonly searchQuery = signal('');

// Filtros
readonly filterStatus = signal<FilterStatus>('all');

// Ordenamiento
readonly sortField = signal<SortField>(null);
readonly sortDirection = signal<SortDirection>('asc');

// Computed value para resultados filtrados
readonly filteredPatients = computed(() => {
  let patients = [...this.careService.patients()];

  // Aplicar búsqueda
  // Aplicar filtro de estado
  // Aplicar ordenamiento

  return patients;
});
```

---

## ➕ Funcionalidad 3: Asignación de Nuevos Pacientes

### Componente Modal
`src/app/features/profesional/components/assign-patient-modal/assign-patient-modal.component.ts`

### Servicio Actualizado
`src/app/features/profesional/services/care-relationship.service.ts`

### Flujo de Asignación

#### 3.1 Abrir Modal
- **Botón "+ Asignar Paciente"** en la lista de pacientes
- Modal overlay con diseño moderno
- Click fuera del modal lo cierra

#### 3.2 Buscar Usuario Disponible
```typescript
async searchAvailableUsers(query: string): Promise<PatientInfo[]>
```

**Características**:
- **Mínimo 3 caracteres** para iniciar búsqueda
- **Debounce de 500ms** para optimizar peticiones
- **Búsqueda en**:
  - Nombre del usuario (ILIKE)
  - Email del usuario (ILIKE)
- **Filtrado automático**:
  - ❌ Excluye usuarios con rol `ProfesionalSalud`
  - ✅ Solo muestra potenciales pacientes
- **Límite de 10 resultados**

#### 3.3 Resultados de Búsqueda
- **Cards clickeables** para cada usuario encontrado
- **Información mostrada**:
  - Nombre completo
  - Email
  - Rol en el sistema
- **Feedback visual**:
  - Hover effect en verde
  - Check mark (✓) cuando se selecciona
  - Background verde para el seleccionado

#### 3.4 Configurar Relación
Una vez seleccionado el usuario:

**Tipo de Relación**:
- Dropdown selector
- Opciones:
  - **Práctica Independiente**: Para profesionales autónomos
  - **Institucional**: Para profesionales en instituciones

**Notas Opcionales**:
- Textarea para agregar contexto
- Placeholder descriptivo
- Campo opcional

#### 3.5 Asignar Paciente
```typescript
async assignPatient(
  patientUserId: number,
  contextType: 'independent' | 'institutional',
  notes?: string
): Promise<void>
```

**Proceso**:
1. ✅ Validar usuario autenticado
2. ✅ Obtener ID del profesional actual
3. ✅ Crear registro en `care_relationships`
4. ✅ Recargar automáticamente la lista de pacientes
5. ✅ Cerrar modal
6. ✅ Mostrar mensaje de éxito

**Manejo de Errores**:
- ❌ Usuario no autenticado
- ❌ Error de conexión con la base de datos
- ❌ Relación duplicada
- Mensajes descriptivos en español

### Validaciones
- ✅ Botón "Asignar" deshabilitado hasta seleccionar usuario
- ✅ Botón deshabilitado durante el proceso de guardado
- ✅ Loading state: "Asignando..."
- ✅ No se pueden asignar profesionales de salud como pacientes

---

## 📁 Archivos Creados

### Nuevos Componentes
```
src/app/features/profesional/
├── pages/
│   ├── patient-detail/
│   │   └── patient-detail.component.ts (nuevo)
│   └── patients-list/
│       └── patients-list.component.ts (actualizado)
└── components/
    └── assign-patient-modal/
        └── assign-patient-modal.component.ts (nuevo)
```

### Modelos
```
src/app/features/profesional/models/
└── care-relationship.model.ts (ya existía, no modificado)
```

### Servicios
```
src/app/features/profesional/services/
└── care-relationship.service.ts (actualizado con nuevos métodos)
```

### Rutas
```
src/app/features/profesional/
└── profesional.routes.ts (agregada ruta de detalle)
```

---

## 🎨 Diseño y UX

### Colores y Tema
- **Verde primario**: `#10b981` (botones principales, highlights)
- **Verde claro**: `#d1fae5` (backgrounds, selections)
- **Gris**: `#f3f4f6` (backgrounds secundarios)
- **Bordes**: `#e5e7eb`
- **Texto**: `#111827` (principal), `#6b7280` (secundario)

### Badges y Estados
- **Activo**: Verde (`#d1fae5` background, `#065f46` text)
- **Inactivo/Finalizado**: Rojo (`#fee2e2` background, `#991b1b` text)
- **Independiente**: Azul (`#dbeafe` background, `#1e40af` text)
- **Institucional**: Amarillo (`#fef3c7` background, `#92400e` text)

### Interactividad
- ✅ Hover effects en tablas y cards
- ✅ Smooth transitions (0.2s)
- ✅ Loading states con spinners/texto
- ✅ Cursors apropiados (pointer, not-allowed)
- ✅ Focus states con ring verde
- ✅ Animaciones sutiles (transform en hover)

### Responsive
- ✅ Grid layouts con `auto-fit`
- ✅ Flex-wrap para elementos que se apilan
- ✅ Padding y spacing consistentes
- ✅ Modal centrado con overflow-y
- ✅ Min-width en campos de búsqueda

---

## 🔧 Detalles Técnicos

### Angular Signals (Reactive UI)
```typescript
// Estado reactivo
readonly searchQuery = signal('');
readonly selectedUser = signal<PatientInfo | null>(null);

// Valores computados
readonly filteredPatients = computed(() => {
  // Lógica de filtrado reactiva
});

readonly activePatients = computed(() =>
  this.careService.patients().filter(p => p.status === 'active')
);
```

### Debouncing
```typescript
private searchTimeout: any;

onSearchChange(): void {
  clearTimeout(this.searchTimeout);
  this.searchTimeout = setTimeout(async () => {
    // Búsqueda después de 500ms de inactividad
  }, 500);
}
```

### Lazy Loading
```typescript
{
  path: 'pacientes/:id',
  loadComponent: () =>
    import('./pages/patient-detail/patient-detail.component').then(
      (m) => m.PatientDetailComponent
    ),
}
```

### Error Handling
```typescript
try {
  await this.careService.assignPatient(...);
  this.patientAssigned.emit();
  this.close();
} catch (err) {
  console.error('Error al asignar paciente:', err);
  this.error.set('Error al asignar el paciente...');
}
```

---

## 🧪 Testing

### Cómo Probar

1. **Login como Profesional**:
   ```
   Email: angie.martinez@aurademo.com
   Password: Aura360!
   ```

2. **Dashboard**:
   - Verifica contador "2" en "Mis Pacientes"
   - Ve la sección "Pacientes Recientes"

3. **Lista Completa**:
   - Click en "Mis Pacientes"
   - Prueba búsqueda: "gabriel"
   - Prueba filtro: "Activos"
   - Prueba ordenamiento: Click en "Nombre" y "Fecha"

4. **Detalle**:
   - Click en cualquier fila
   - Navega por las secciones
   - Prueba "Finalizar Relación"

5. **Asignación**:
   - Click "+ Asignar Paciente"
   - Busca "pac" o "paciente"
   - Selecciona un usuario
   - Configura y asigna

---

## 🚀 Próximas Mejoras Sugeridas

### Funcionalidades de Historial
- [ ] Implementar creación de consultas
- [ ] Vista detallada de cada consulta
- [ ] Filtros y búsqueda en historial
- [ ] Exportar historial a PDF

### Funcionalidades de Plan Nutricional
- [ ] Crear/editar planes nutricionales
- [ ] Templates de planes
- [ ] Tracking de progreso del paciente
- [ ] Recordatorios automáticos

### Mejoras UX/UI
- [ ] Notificaciones toast en lugar de alerts
- [ ] Confirmación más elegante para acciones destructivas
- [ ] Paginación para listas largas
- [ ] Exportar lista de pacientes a CSV/Excel
- [ ] Bulk actions (asignar múltiples pacientes)

### Optimizaciones
- [ ] Virtual scrolling para listas muy largas
- [ ] Cache de búsquedas recientes
- [ ] Optimistic UI updates
- [ ] Offline support con PWA

---

## 📝 Notas de Implementación

### Decisiones de Diseño

1. **Angular Signals sobre RxJS**: Elegido por su simplicidad y mejor rendimiento para estado local
2. **Computed Values**: Para derivar datos sin re-computar innecesariamente
3. **Standalone Components**: Arquitectura moderna de Angular 20
4. **FormsModule (Template-driven)**: Suficiente para formularios simples del modal
5. **RouterLink sobre Router.navigate**: Mejor para accesibilidad y SEO

### Convenciones de Código

- **Naming**: `kebab-case` para archivos, `PascalCase` para clases
- **Suffixes**: `.component.ts`, `.service.ts`, `.model.ts`
- **Signals**: `readonly` para proteger el estado
- **Async/Await**: Preferido sobre Promises encadenadas
- **Error handling**: Try-catch con logs descriptivos

---

## ✅ Checklist de Completitud

### Funcionalidad 1: Detalle del Paciente
- [x] Componente creado
- [x] Ruta configurada
- [x] Navegación desde lista
- [x] Información personal completa
- [x] Datos de relación
- [x] Placeholders para historial y plan
- [x] Acción de finalizar relación
- [x] Breadcrumb navigation

### Funcionalidad 2: Búsqueda y Filtros
- [x] Campo de búsqueda reactivo
- [x] Botón limpiar búsqueda
- [x] Filtro por estado (dropdown)
- [x] Ordenamiento por nombre
- [x] Ordenamiento por fecha
- [x] Contador dinámico "Mostrando"
- [x] Mensaje cuando no hay resultados
- [x] Botón limpiar todos los filtros

### Funcionalidad 3: Asignación de Pacientes
- [x] Botón "+ Asignar Paciente"
- [x] Modal component creado
- [x] Búsqueda de usuarios disponibles
- [x] Filtrado de profesionales
- [x] Selección visual de usuario
- [x] Configuración de tipo de relación
- [x] Campo de notas opcionales
- [x] Método de asignación en servicio
- [x] Recarga automática de lista
- [x] Manejo de errores

### General
- [x] Documentación actualizada (SETUP_LOCAL.md)
- [x] Todos los componentes con estilos completos
- [x] Responsive design
- [x] Error handling
- [x] Loading states
- [x] TypeScript types correctos
- [x] Imports organizados

---

¡Todas las funcionalidades implementadas y listas para usar! 🎉
