-- =====================================================================
-- Migración: Tablas del módulo Body (Salud Física)
-- Propósito: Crear tablas para actividad física, nutrición y sueño
-- Fecha: 2025-10-28
-- =====================================================================

-- =====================================================================
-- TABLA: body_activities
-- Propósito: Registro de sesiones de actividad física del usuario
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.body_activities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  activity_type text NOT NULL CHECK (activity_type IN ('cardio', 'strength', 'flexibility', 'mindfulness')),
  intensity text NOT NULL DEFAULT 'moderate' CHECK (intensity IN ('low', 'moderate', 'high')),
  duration_minutes int NOT NULL CHECK (duration_minutes > 0),
  session_date date NOT NULL DEFAULT CURRENT_DATE,
  notes text,
  created_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
  updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
);

-- Índices para búsquedas eficientes
CREATE INDEX idx_body_activities_user ON public.body_activities(auth_user_id);
CREATE INDEX idx_body_activities_date ON public.body_activities(session_date DESC);
CREATE INDEX idx_body_activities_type ON public.body_activities(activity_type);

-- Comentarios de columnas
COMMENT ON TABLE public.body_activities IS 'Registros de sesiones de actividad física de los usuarios';
COMMENT ON COLUMN public.body_activities.id IS 'Identificador único de la sesión de actividad';
COMMENT ON COLUMN public.body_activities.auth_user_id IS 'ID del usuario en Supabase (auth.users.id)';
COMMENT ON COLUMN public.body_activities.activity_type IS 'Tipo de actividad: cardio, strength, flexibility, mindfulness';
COMMENT ON COLUMN public.body_activities.intensity IS 'Intensidad percibida: low, moderate, high';
COMMENT ON COLUMN public.body_activities.duration_minutes IS 'Duración de la sesión en minutos';
COMMENT ON COLUMN public.body_activities.session_date IS 'Fecha en la que se realizó la actividad';
COMMENT ON COLUMN public.body_activities.notes IS 'Notas opcionales o contexto adicional de la sesión';

-- =====================================================================
-- TABLA: body_nutrition_logs
-- Propósito: Registro de ingesta alimentaria y macronutrientes
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.body_nutrition_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  meal_type text NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
  timestamp timestamptz NOT NULL DEFAULT timezone('utc', now()),
  items jsonb DEFAULT '[]'::jsonb,
  calories int CHECK (calories >= 0),
  protein decimal(6,2) CHECK (protein >= 0),
  carbs decimal(6,2) CHECK (carbs >= 0),
  fats decimal(6,2) CHECK (fats >= 0),
  notes text,
  created_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
  updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
);

-- Índices para búsquedas eficientes
CREATE INDEX idx_body_nutrition_user ON public.body_nutrition_logs(auth_user_id);
CREATE INDEX idx_body_nutrition_timestamp ON public.body_nutrition_logs(timestamp DESC);
CREATE INDEX idx_body_nutrition_meal_type ON public.body_nutrition_logs(meal_type);

-- Comentarios de columnas
COMMENT ON TABLE public.body_nutrition_logs IS 'Registros de ingesta alimentaria de los usuarios';
COMMENT ON COLUMN public.body_nutrition_logs.id IS 'Identificador único del registro nutricional';
COMMENT ON COLUMN public.body_nutrition_logs.auth_user_id IS 'ID del usuario en Supabase (auth.users.id)';
COMMENT ON COLUMN public.body_nutrition_logs.meal_type IS 'Tipo de comida: breakfast, lunch, dinner, snack';
COMMENT ON COLUMN public.body_nutrition_logs.timestamp IS 'Fecha y hora en la que se consumió la comida';
COMMENT ON COLUMN public.body_nutrition_logs.items IS 'Array JSON de alimentos incluidos en la comida';
COMMENT ON COLUMN public.body_nutrition_logs.calories IS 'Calorías estimadas de la comida';
COMMENT ON COLUMN public.body_nutrition_logs.protein IS 'Proteínas en gramos';
COMMENT ON COLUMN public.body_nutrition_logs.carbs IS 'Carbohidratos en gramos';
COMMENT ON COLUMN public.body_nutrition_logs.fats IS 'Grasas en gramos';
COMMENT ON COLUMN public.body_nutrition_logs.notes IS 'Notas adicionales relacionadas a la comida';

-- =====================================================================
-- TABLA: body_sleep_logs
-- Propósito: Registro de ciclos de sueño y calidad percibida
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.body_sleep_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  auth_user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  bedtime timestamptz NOT NULL,
  wake_time timestamptz NOT NULL,
  duration_hours decimal(4,1) NOT NULL CHECK (duration_hours > 0 AND duration_hours <= 24),
  quality text NOT NULL DEFAULT 'good' CHECK (quality IN ('poor', 'fair', 'good', 'excellent')),
  notes text,
  created_at timestamptz NOT NULL DEFAULT timezone('utc', now()),
  updated_at timestamptz NOT NULL DEFAULT timezone('utc', now())
);

-- Índices para búsquedas eficientes
CREATE INDEX idx_body_sleep_user ON public.body_sleep_logs(auth_user_id);
CREATE INDEX idx_body_sleep_wake_time ON public.body_sleep_logs(wake_time DESC);
CREATE INDEX idx_body_sleep_bedtime ON public.body_sleep_logs(bedtime DESC);

-- Comentarios de columnas
COMMENT ON TABLE public.body_sleep_logs IS 'Registros de periodos de sueño de los usuarios';
COMMENT ON COLUMN public.body_sleep_logs.id IS 'Identificador único del registro de sueño';
COMMENT ON COLUMN public.body_sleep_logs.auth_user_id IS 'ID del usuario en Supabase (auth.users.id)';
COMMENT ON COLUMN public.body_sleep_logs.bedtime IS 'Hora de irse a dormir';
COMMENT ON COLUMN public.body_sleep_logs.wake_time IS 'Hora de despertar';
COMMENT ON COLUMN public.body_sleep_logs.duration_hours IS 'Duración total del sueño en horas';
COMMENT ON COLUMN public.body_sleep_logs.quality IS 'Calidad del sueño reportada: poor, fair, good, excellent';
COMMENT ON COLUMN public.body_sleep_logs.notes IS 'Notas adicionales sobre el sueño';

-- =====================================================================
-- TRIGGERS: Actualización automática de updated_at
-- =====================================================================

CREATE TRIGGER set_body_activities_updated_at
  BEFORE UPDATE ON public.body_activities
  FOR EACH ROW
  EXECUTE FUNCTION public.set_current_timestamp_updated_at();

CREATE TRIGGER set_body_nutrition_updated_at
  BEFORE UPDATE ON public.body_nutrition_logs
  FOR EACH ROW
  EXECUTE FUNCTION public.set_current_timestamp_updated_at();

CREATE TRIGGER set_body_sleep_updated_at
  BEFORE UPDATE ON public.body_sleep_logs
  FOR EACH ROW
  EXECUTE FUNCTION public.set_current_timestamp_updated_at();

-- =====================================================================
-- ROW LEVEL SECURITY (RLS)
-- =====================================================================

-- Habilitar RLS en todas las tablas
ALTER TABLE public.body_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.body_nutrition_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.body_sleep_logs ENABLE ROW LEVEL SECURITY;

-- =====================================================================
-- POLÍTICAS RLS: body_activities
-- =====================================================================

-- Usuarios autenticados pueden ver solo sus propias actividades
CREATE POLICY "Users can view own activities"
  ON public.body_activities FOR SELECT
  TO authenticated
  USING (auth_user_id = auth.uid());

-- Usuarios autenticados pueden insertar solo sus propias actividades
CREATE POLICY "Users can insert own activities"
  ON public.body_activities FOR INSERT
  TO authenticated
  WITH CHECK (auth_user_id = auth.uid());

-- Usuarios autenticados pueden actualizar solo sus propias actividades
CREATE POLICY "Users can update own activities"
  ON public.body_activities FOR UPDATE
  TO authenticated
  USING (auth_user_id = auth.uid())
  WITH CHECK (auth_user_id = auth.uid());

-- Usuarios autenticados pueden eliminar solo sus propias actividades
CREATE POLICY "Users can delete own activities"
  ON public.body_activities FOR DELETE
  TO authenticated
  USING (auth_user_id = auth.uid());

-- Service role tiene acceso completo
CREATE POLICY "Service role full access activities"
  ON public.body_activities FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- =====================================================================
-- POLÍTICAS RLS: body_nutrition_logs
-- =====================================================================

CREATE POLICY "Users can view own nutrition logs"
  ON public.body_nutrition_logs FOR SELECT
  TO authenticated
  USING (auth_user_id = auth.uid());

CREATE POLICY "Users can insert own nutrition logs"
  ON public.body_nutrition_logs FOR INSERT
  TO authenticated
  WITH CHECK (auth_user_id = auth.uid());

CREATE POLICY "Users can update own nutrition logs"
  ON public.body_nutrition_logs FOR UPDATE
  TO authenticated
  USING (auth_user_id = auth.uid())
  WITH CHECK (auth_user_id = auth.uid());

CREATE POLICY "Users can delete own nutrition logs"
  ON public.body_nutrition_logs FOR DELETE
  TO authenticated
  USING (auth_user_id = auth.uid());

CREATE POLICY "Service role full access nutrition"
  ON public.body_nutrition_logs FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- =====================================================================
-- POLÍTICAS RLS: body_sleep_logs
-- =====================================================================

CREATE POLICY "Users can view own sleep logs"
  ON public.body_sleep_logs FOR SELECT
  TO authenticated
  USING (auth_user_id = auth.uid());

CREATE POLICY "Users can insert own sleep logs"
  ON public.body_sleep_logs FOR INSERT
  TO authenticated
  WITH CHECK (auth_user_id = auth.uid());

CREATE POLICY "Users can update own sleep logs"
  ON public.body_sleep_logs FOR UPDATE
  TO authenticated
  USING (auth_user_id = auth.uid())
  WITH CHECK (auth_user_id = auth.uid());

CREATE POLICY "Users can delete own sleep logs"
  ON public.body_sleep_logs FOR DELETE
  TO authenticated
  USING (auth_user_id = auth.uid());

CREATE POLICY "Service role full access sleep"
  ON public.body_sleep_logs FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

