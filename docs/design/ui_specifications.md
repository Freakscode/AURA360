# Especificaciones de Interfaz de Usuario (UI Specs) - AURA360

Este documento detalla los elementos y funcionalidades propuestos para cada pantalla identificada en el User Flow.

## 1. Inicio y Onboarding

### Splash Screen
*   **Propósito:** Pantalla de carga inicial y branding.
*   **Elementos:**
    *   Logo de AURA360 (Centrado).
    *   Indicador de carga (Spinner o barra de progreso).
    *   Versión de la app (Pie de página, pequeño).

### Onboarding Screens (Carrusel)
*   **Propósito:** Educar al usuario sobre las funcionalidades clave.
*   **Elementos:**
    *   Imágenes/Ilustraciones alusivas (3-4 slides).
    *   Título y descripción breve por slide.
    *   Indicadores de paginación (Puntos).
    *   Botón "Saltar" (Skip).
    *   Botón "Siguiente" / "Empezar".

### Create Account / Login (Landing)
*   **Propósito:** Punto de decisión para autenticación.
*   **Elementos:**
    *   Imagen de bienvenida.
    *   Botón principal "Crear Cuenta".
    *   Botón secundario "Iniciar Sesión".

---

## 2. Autenticación

### Sign Up (Registro)
*   **Propósito:** Formulario de registro manual.
*   **Elementos:**
    *   Campos: Nombre completo, Email, Contraseña, Confirmar contraseña.
    *   Checkbox "Acepto Términos y Condiciones".
    *   Botón "Registrarse".
    *   Separador "O regístrate con".
    *   Botones sociales: Facebook, Google.

### Login (Inicio de Sesión)
*   **Propósito:** Acceso para usuarios existentes.
*   **Elementos:**
    *   Campos: Email, Contraseña.
    *   Enlace "¿Olvidaste tu contraseña?".
    *   Botón "Iniciar Sesión".
    *   Separador "O inicia con".
    *   Botones sociales: Facebook, Google.

### Forgot Password
*   **Propósito:** Iniciar recuperación de cuenta.
*   **Elementos:**
    *   Instrucción: "Ingresa tu email para recibir un enlace".
    *   Campo: Email.
    *   Botón "Enviar enlace".

### Reset Password
*   **Propósito:** Establecer nueva contraseña.
*   **Elementos:**
    *   Campos: Nueva contraseña, Confirmar nueva contraseña.
    *   Botón "Guardar contraseña".

---

## 3. Navegación Principal (Home Screen)

### Home Screen
*   **Propósito:** Dashboard principal.
*   **Elementos:**
    *   Saludo personalizado ("Hola, [Nombre]").
    *   Barra de búsqueda global.
    *   Sección "Cursos en Progreso" (Carrusel horizontal).
    *   Sección "Recomendados para ti".
    *   Barra de navegación inferior (Bottom Navigation): Home, Cursos, Perfil, Mensajes.

---

## 4. Funcionalidades Principales

### Search (Búsqueda)
*   **Search Courses:** Lista de resultados con filtros (Categoría, Precio, Nivel).
*   **Search Tutors:** Lista de tarjetas de tutores con foto, nombre, especialidad y calificación.

### Courses (Mis Cursos)
*   **In Progress:** Lista de cursos activos con barra de progreso.
*   **Bookmark:** Lista de cursos/lecciones guardados.
*   **Test:** Interfaz de examen (Pregunta, Opciones múltiples, Temporizador).
*   **Feedback:** Formulario de calificación (Estrellas 1-5) y campo de texto para comentarios.
*   **Completed:** Lista histórica de cursos finalizados con opción de descargar certificado.

### My Profile (Perfil)
*   **Vista Principal:** Foto de perfil, Nombre, Bio corta, Estadísticas rápidas (Cursos completados).
*   **Edit Profile:** Formulario para modificar datos personales.
*   **Settings:** Switches para notificaciones, selector de idioma, tema (Claro/Oscuro).
*   **My Courses:** Acceso directo al historial completo.
*   **Payments:** Lista de tarjetas guardadas, botón "Añadir método de pago", historial de facturas.
*   **Contacts:** Lista de amigos/tutores con opción de iniciar chat.

### Messages (Mensajería)
*   **Lista de Chats:** Vista previa de conversaciones recientes (Avatar, Nombre, Último mensaje, Hora).
*   **Chat (Individual):** Área de mensajes, campo de texto, botón de enviar, adjuntar archivo.
*   **Group Chat:** Similar al individual, mostrando nombres de participantes en los mensajes.

### Notifications
*   **Updates:** Lista cronológica de alertas (Nuevos cursos, Respuestas en foros, Recordatorios).