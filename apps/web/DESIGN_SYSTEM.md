# AURA360 Design System 🎨

Sistema de diseño completo para la aplicación web AURA360 construido con SCSS modular.

## 📁 Estructura

```
src/styles/
├── _variables.scss       # Design tokens (colores, espaciados, tipografía, etc.)
├── _typography.scss      # Sistema tipográfico
├── _mixins.scss         # Mixins y funciones reutilizables
├── _reset.scss          # CSS reset/normalize
├── components/
│   ├── _buttons.scss    # Estilos de botones
│   ├── _inputs.scss     # Estilos de formularios
│   ├── _cards.scss      # Estilos de tarjetas
│   ├── _badges.scss     # Estilos de badges/etiquetas
│   ├── _modals.scss     # Estilos de modales
│   ├── _tables.scss     # Estilos de tablas
│   └── _index.scss      # Índice de componentes
├── utilities/
│   ├── _spacing.scss    # Utilidades de espaciado (margin, padding, gap)
│   ├── _colors.scss     # Utilidades de colores y bordes
│   ├── _layout.scss     # Utilidades de layout (flex, grid, position)
│   └── _index.scss      # Índice de utilidades
└── styles.scss          # Archivo principal
```

## 🎨 Design Tokens

### Colores

#### Primarios (Verde)
```scss
$color-primary-50: #ecfdf5;
$color-primary-100: #d1fae5;
$color-primary-500: #10b981;  // Color principal de la marca
$color-primary-600: #059669;
$color-primary-700: #047857;
```

#### Neutrales (Grises)
```scss
$color-gray-50: #f9fafb;
$color-gray-100: #f3f4f6;
$color-gray-500: #6b7280;
$color-gray-900: #111827;
```

#### Semánticos
```scss
// Success (Verde)
$color-success-500: #22c55e;

// Warning (Amarillo/Naranja)
$color-warning-500: #f59e0b;

// Error (Rojo)
$color-error-500: #ef4444;

// Info (Azul)
$color-info-500: #3b82f6;
```

### Tipografía

**Fuente**: Red Hat Display (Google Fonts)

```scss
// Tamaños
$font-size-xs: 0.75rem;   // 12px
$font-size-sm: 0.875rem;  // 14px
$font-size-base: 1rem;    // 16px
$font-size-lg: 1.125rem;  // 18px
$font-size-xl: 1.25rem;   // 20px
$font-size-2xl: 1.5rem;   // 24px

// Pesos
$font-weight-normal: 400;
$font-weight-medium: 500;
$font-weight-semibold: 600;
$font-weight-bold: 700;
```

### Espaciado

Sistema basado en 4px:

```scss
$space-1: 0.25rem;   // 4px
$space-2: 0.5rem;    // 8px
$space-3: 0.75rem;   // 12px
$space-4: 1rem;      // 16px
$space-6: 1.5rem;    // 24px
$space-8: 2rem;      // 32px
```

### Border Radius

```scss
$radius-sm: 0.125rem;    // 2px
$radius-base: 0.25rem;   // 4px
$radius-md: 0.375rem;    // 6px
$radius-lg: 0.5rem;      // 8px
$radius-full: 9999px;    // Completamente redondeado
```

### Sombras

```scss
$shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
$shadow-base: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
$shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
$shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
```

## 🧩 Componentes

### Botones

```html
<!-- Variantes -->
<button class="btn btn--primary">Primario</button>
<button class="btn btn--secondary">Secundario</button>
<button class="btn btn--outline">Outlined</button>
<button class="btn btn--ghost">Ghost</button>
<button class="btn btn--danger">Peligro</button>

<!-- Tamaños -->
<button class="btn btn--primary btn--xs">Extra pequeño</button>
<button class="btn btn--primary btn--sm">Pequeño</button>
<button class="btn btn--primary">Base</button>
<button class="btn btn--primary btn--lg">Grande</button>

<!-- Modificadores -->
<button class="btn btn--primary btn--block">Full width</button>
<button class="btn btn--primary btn--rounded">Redondeado</button>
<button class="btn btn--primary btn--loading">Cargando...</button>
<button class="btn btn--primary" disabled>Deshabilitado</button>
```

### Inputs

```html
<!-- Input básico -->
<div class="form-group">
  <label>Nombre de usuario</label>
  <input type="text" class="form-input" placeholder="usuario@ejemplo.com">
</div>

<!-- Select -->
<div class="form-group">
  <label>País</label>
  <select class="form-select">
    <option>Colombia</option>
    <option>México</option>
  </select>
</div>

<!-- Textarea -->
<div class="form-group">
  <label>Descripción</label>
  <textarea class="form-textarea" rows="4"></textarea>
</div>

<!-- Con error -->
<div class="form-group">
  <label class="required">Email</label>
  <input type="email" class="form-input error" value="email-invalido">
  <span class="form-error">El email no es válido</span>
</div>

<!-- Checkbox -->
<div class="form-check">
  <input type="checkbox" id="accept">
  <label for="accept">Acepto los términos</label>
</div>

<!-- Switch -->
<div class="form-switch">
  <input type="checkbox" id="notifications">
  <label for="notifications">Notificaciones</label>
</div>
```

### Cards

```html
<!-- Card básica -->
<div class="card">
  <div class="card__header">
    <h3>Título de la card</h3>
  </div>
  <div class="card__body">
    <p>Contenido de la card...</p>
  </div>
  <div class="card__footer card__footer--actions">
    <button class="btn btn--secondary">Cancelar</button>
    <button class="btn btn--primary">Guardar</button>
  </div>
</div>

<!-- Card con imagen -->
<div class="card card--image-top">
  <img src="imagen.jpg" alt="Descripción" class="card__image">
  <div class="card__body">
    <h4>Título</h4>
    <p>Descripción...</p>
  </div>
</div>

<!-- Card elevada y clickeable -->
<div class="card card--elevated card--clickable">
  <div class="card__body">
    <p>Click en toda la card...</p>
  </div>
</div>

<!-- Grid de cards -->
<div class="card-grid card-grid--3-cols">
  <div class="card">Card 1</div>
  <div class="card">Card 2</div>
  <div class="card">Card 3</div>
</div>
```

### Badges

```html
<!-- Variantes básicas -->
<span class="badge badge--primary">Primario</span>
<span class="badge badge--success">Éxito</span>
<span class="badge badge--warning">Advertencia</span>
<span class="badge badge--error">Error</span>
<span class="badge badge--info">Info</span>

<!-- Sólidos -->
<span class="badge badge--solid-primary">Primario</span>
<span class="badge badge--solid-success">Éxito</span>

<!-- Outlined -->
<span class="badge badge--outline-primary">Primario</span>

<!-- Con punto -->
<span class="badge badge--dot badge--success">Activo</span>

<!-- Badge de notificación -->
<div class="badge-wrapper">
  <button class="btn btn--primary">Mensajes</button>
  <span class="badge badge--notification">12</span>
</div>
```

### Tables

```html
<!-- Tabla básica -->
<div class="table-container">
  <table class="table">
    <thead>
      <tr>
        <th>Nombre</th>
        <th>Email</th>
        <th>Rol</th>
        <th>Estado</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Juan Pérez</td>
        <td>juan@ejemplo.com</td>
        <td>Admin</td>
        <td><span class="badge badge--success">Activo</span></td>
      </tr>
    </tbody>
  </table>
</div>

<!-- Tabla con variantes -->
<table class="table table--bordered table--striped table--hoverable">
  <!-- ... -->
</table>

<!-- Tabla compacta -->
<table class="table table--compact">
  <!-- ... -->
</table>
```

### Modals

```html
<!-- Modal básico -->
<div class="modal-overlay">
  <div class="modal">
    <div class="modal__header">
      <h2>Título del Modal</h2>
      <button class="modal__close">&times;</button>
    </div>
    <div class="modal__body">
      <p>Contenido del modal...</p>
    </div>
    <div class="modal__footer">
      <button class="btn btn--secondary">Cancelar</button>
      <button class="btn btn--primary">Confirmar</button>
    </div>
  </div>
</div>

<!-- Modal de confirmación -->
<div class="modal modal--confirm">
  <div class="modal__body">
    <div class="modal__icon modal__icon--warning">
      <!-- Icono SVG -->
    </div>
    <h3 class="modal__title">¿Estás seguro?</h3>
    <p class="modal__message">Esta acción no se puede deshacer.</p>
  </div>
  <div class="modal__footer">
    <button class="btn btn--secondary">Cancelar</button>
    <button class="btn btn--danger">Eliminar</button>
  </div>
</div>

<!-- Tamaños -->
<div class="modal modal--sm">Small modal</div>
<div class="modal modal--lg">Large modal</div>
<div class="modal modal--full">Full modal</div>
```

## 🛠️ Utilidades

### Spacing

```html
<!-- Margin -->
<div class="m-4">Margin en todos los lados</div>
<div class="mt-2">Margin top</div>
<div class="mx-auto">Margin horizontal auto (centrado)</div>
<div class="my-6">Margin vertical</div>

<!-- Padding -->
<div class="p-4">Padding en todos los lados</div>
<div class="px-6">Padding horizontal</div>
<div class="py-3">Padding vertical</div>

<!-- Gap (para flex/grid) -->
<div class="d-flex gap-4">
  <div>Item 1</div>
  <div>Item 2</div>
</div>
```

### Layout

```html
<!-- Display -->
<div class="d-none">Oculto</div>
<div class="d-block">Block</div>
<div class="d-flex">Flex</div>
<div class="d-grid">Grid</div>

<!-- Flexbox -->
<div class="d-flex justify-between items-center gap-4">
  <div>Izquierda</div>
  <div>Derecha</div>
</div>

<div class="d-flex flex-column gap-2">
  <div>Item 1</div>
  <div>Item 2</div>
</div>

<!-- Grid -->
<div class="d-grid grid-cols-3 gap-4">
  <div>Col 1</div>
  <div>Col 2</div>
  <div>Col 3</div>
</div>

<!-- Posicionamiento -->
<div class="relative">
  <div class="absolute top-0 right-0">Badge</div>
</div>

<!-- Width/Height -->
<div class="w-full">100% width</div>
<div class="h-screen">100vh height</div>
<div class="max-w-lg">Max width large</div>
```

### Colors

```html
<!-- Backgrounds -->
<div class="bg-primary-500">Background primario</div>
<div class="bg-gray-100">Background gris claro</div>

<!-- Borders -->
<div class="border border-gray-300">Con borde</div>
<div class="border-2 border-primary">Borde primario grueso</div>

<!-- Border radius -->
<div class="rounded-lg">Bordes redondeados</div>
<div class="rounded-full">Completamente redondo</div>

<!-- Sombras -->
<div class="shadow-md">Sombra mediana</div>
<div class="shadow-lg">Sombra grande</div>
```

### Typography

```html
<!-- Tamaños -->
<p class="text-xs">Texto extra pequeño</p>
<p class="text-base">Texto base</p>
<p class="text-2xl">Texto 2XL</p>

<!-- Pesos -->
<p class="font-light">Ligero</p>
<p class="font-normal">Normal</p>
<p class="font-medium">Medio</p>
<p class="font-bold">Negrita</p>

<!-- Colores -->
<p class="text-primary">Texto primario</p>
<p class="text-muted">Texto apagado</p>
<p class="text-error">Texto error</p>

<!-- Alineación -->
<p class="text-center">Centrado</p>
<p class="text-right">Derecha</p>

<!-- Otros -->
<p class="uppercase">Mayúsculas</p>
<p class="truncate">Texto truncado con ellipsis...</p>
```

## 📖 Mixins

### Responsive Breakpoints

```scss
.mi-componente {
  padding: 1rem;

  @include md {
    padding: 2rem;
  }

  @include lg {
    padding: 3rem;
  }
}
```

### Focus Ring

```scss
.btn-custom {
  @include focus-ring;
  // o con color personalizado
  @include focus-ring($color-error-500);
}
```

### Flexbox Helpers

```scss
.header {
  @include flex-between;  // flex con space-between
}

.modal {
  @include flex-center;  // flex centrado
}
```

### Custom Scrollbar

```scss
.scrollable-container {
  @include custom-scrollbar(8px, $color-primary-300, $color-gray-100);
}
```

## 🎯 Mejores Prácticas

### 1. Usa Design Tokens
✅ **Correcto**:
```scss
.card {
  padding: $space-6;
  border-radius: $radius-lg;
  background: $color-bg-primary;
}
```

❌ **Incorrecto**:
```scss
.card {
  padding: 24px;
  border-radius: 8px;
  background: #ffffff;
}
```

### 2. Reutiliza Componentes
✅ **Correcto**:
```html
<button class="btn btn--primary">Guardar</button>
```

❌ **Incorrecto**:
```html
<button style="background: #10b981; padding: 12px 24px;">Guardar</button>
```

### 3. Usa Utilidades para Ajustes Rápidos
✅ **Correcto**:
```html
<div class="card p-6 rounded-lg shadow-md">
  <h3 class="text-xl font-bold mb-4">Título</h3>
  <p class="text-muted">Descripción...</p>
</div>
```

### 4. Combina Componentes y Utilidades
```html
<button class="btn btn--primary btn--lg mt-4">
  <svg>...</svg>
  Guardar cambios
</button>
```

## 🔧 Configuración

### Angular.json

El sistema de diseño ya está configurado en `angular.json`:

```json
{
  "styles": [
    "src/styles.scss"
  ]
}
```

### Importar en Componentes

Para usar variables y mixins en componentes:

```scss
// component.scss
@use '/src/styles/variables' as *;
@use '/src/styles/mixins' as *;

.mi-componente {
  background: $color-primary-500;
  @include flex-center;
}
```

## 📚 Referencias

- [Tailwind CSS](https://tailwindcss.com/) - Inspiración para utilidades
- [Material Design](https://material.io/) - Principios de diseño
- [Bootstrap](https://getbootstrap.com/) - Estructura de componentes
- [Red Hat Display](https://fonts.google.com/specimen/Red+Hat+Display) - Tipografía

## 🚀 Próximas Mejoras

- [ ] Dark mode support
- [ ] Componentes Angular reutilizables (`ButtonComponent`, `CardComponent`, etc.)
- [ ] Animaciones y transiciones avanzadas
- [ ] Sistema de iconos
- [ ] Temas personalizables
- [ ] Storybook para documentación interactiva

---

**Documentación creada:** 2025-11-01
**Última actualización:** 2025-11-01
**Versión:** 1.0.0
