-- Migration: Create nutrition_plans table
-- Created: 2025-10-28
-- Description: Tabla para almacenar planes nutricionales estructurados
-- con soporte completo para el esquema nutrition-plan.schema.json

-- ================================================================
-- 1. Crear la tabla nutrition_plans
-- ================================================================

CREATE TABLE IF NOT EXISTS public.nutrition_plans (
    -- Identificadores
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Campos principales para consultas rápidas
    title VARCHAR(255) NOT NULL,
    language VARCHAR(10) NOT NULL DEFAULT 'es',
    issued_at DATE,
    valid_until DATE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    
    -- Estructura completa del plan en JSON
    -- Sigue el esquema nutrition-plan.schema.json
    plan_data JSONB NOT NULL,
    
    -- Metadatos de origen
    source_kind VARCHAR(32),
    source_uri TEXT,
    extracted_at TIMESTAMPTZ,
    extractor VARCHAR(128),
    
    -- Timestamps automáticos
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ================================================================
-- 2. Crear índices para optimizar consultas
-- ================================================================

-- Índice principal: usuario + estado activo
CREATE INDEX IF NOT EXISTS idx_nutrition_plans_user_active 
ON public.nutrition_plans(auth_user_id, is_active);

-- Índice: usuario + vigencia
CREATE INDEX IF NOT EXISTS idx_nutrition_plans_user_validity 
ON public.nutrition_plans(auth_user_id, valid_until);

-- Índice: búsqueda por usuario y fecha de emisión
CREATE INDEX IF NOT EXISTS idx_nutrition_plans_user_issued 
ON public.nutrition_plans(auth_user_id, issued_at DESC);

-- Índice GIN para búsquedas dentro del JSON
CREATE INDEX IF NOT EXISTS idx_nutrition_plans_data_gin 
ON public.nutrition_plans USING GIN (plan_data);

-- ================================================================
-- 3. Crear función para actualizar updated_at automáticamente
-- ================================================================

CREATE OR REPLACE FUNCTION update_nutrition_plans_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ================================================================
-- 4. Crear trigger para updated_at
-- ================================================================

DROP TRIGGER IF EXISTS trigger_update_nutrition_plans_updated_at 
ON public.nutrition_plans;

CREATE TRIGGER trigger_update_nutrition_plans_updated_at
    BEFORE UPDATE ON public.nutrition_plans
    FOR EACH ROW
    EXECUTE FUNCTION update_nutrition_plans_updated_at();

-- ================================================================
-- 5. Habilitar Row Level Security (RLS)
-- ================================================================

ALTER TABLE public.nutrition_plans ENABLE ROW LEVEL SECURITY;

-- ================================================================
-- 6. Crear políticas RLS
-- ================================================================

-- Política: Los usuarios solo pueden ver sus propios planes
DROP POLICY IF EXISTS "Users can view their own nutrition plans" 
ON public.nutrition_plans;

CREATE POLICY "Users can view their own nutrition plans"
ON public.nutrition_plans
FOR SELECT
USING (auth.uid() = auth_user_id);

-- Política: Los usuarios pueden insertar sus propios planes
DROP POLICY IF EXISTS "Users can insert their own nutrition plans" 
ON public.nutrition_plans;

CREATE POLICY "Users can insert their own nutrition plans"
ON public.nutrition_plans
FOR INSERT
WITH CHECK (auth.uid() = auth_user_id);

-- Política: Los usuarios pueden actualizar sus propios planes
DROP POLICY IF EXISTS "Users can update their own nutrition plans" 
ON public.nutrition_plans;

CREATE POLICY "Users can update their own nutrition plans"
ON public.nutrition_plans
FOR UPDATE
USING (auth.uid() = auth_user_id)
WITH CHECK (auth.uid() = auth_user_id);

-- Política: Los usuarios pueden eliminar sus propios planes
DROP POLICY IF EXISTS "Users can delete their own nutrition plans" 
ON public.nutrition_plans;

CREATE POLICY "Users can delete their own nutrition plans"
ON public.nutrition_plans
FOR DELETE
USING (auth.uid() = auth_user_id);

-- ================================================================
-- 7. Comentarios en la tabla y columnas para documentación
-- ================================================================

COMMENT ON TABLE public.nutrition_plans IS 
'Planes nutricionales estructurados que incluyen directivas, evaluaciones, 
restricciones, sustituciones y recomendaciones. Sigue el esquema JSON 
nutrition-plan.schema.json.';

COMMENT ON COLUMN public.nutrition_plans.id IS 
'Identificador único del plan nutricional (UUID v4).';

COMMENT ON COLUMN public.nutrition_plans.auth_user_id IS 
'ID del usuario en Supabase Auth (auth.users.id) propietario del plan.';

COMMENT ON COLUMN public.nutrition_plans.title IS 
'Título descriptivo del plan nutricional.';

COMMENT ON COLUMN public.nutrition_plans.language IS 
'Código de idioma ISO 639-1 (es, en, etc.).';

COMMENT ON COLUMN public.nutrition_plans.issued_at IS 
'Fecha de emisión o creación del plan.';

COMMENT ON COLUMN public.nutrition_plans.valid_until IS 
'Fecha de expiración o fin de vigencia del plan.';

COMMENT ON COLUMN public.nutrition_plans.is_active IS 
'Indica si el plan está activo (true) o archivado/inactivo (false).';

COMMENT ON COLUMN public.nutrition_plans.plan_data IS 
'Estructura completa del plan en formato JSONB. Incluye: plan (metadatos, 
source, units), subject (user_id, demographics), assessment (timeseries, 
diagnoses, goals), directives (meals, restrictions, substitutions, 
weekly_frequency), supplements, recommendations, activity_guidance y free_text.';

COMMENT ON COLUMN public.nutrition_plans.source_kind IS 
'Tipo de fuente del plan: pdf, image, text, web.';

COMMENT ON COLUMN public.nutrition_plans.source_uri IS 
'URI o ruta del documento fuente original del plan.';

COMMENT ON COLUMN public.nutrition_plans.extracted_at IS 
'Timestamp de cuando se extrajo/procesó el plan desde la fuente.';

COMMENT ON COLUMN public.nutrition_plans.extractor IS 
'Nombre del sistema, herramienta o agente que extrajo el plan.';

COMMENT ON COLUMN public.nutrition_plans.created_at IS 
'Timestamp de creación del registro en la base de datos.';

COMMENT ON COLUMN public.nutrition_plans.updated_at IS 
'Timestamp de última actualización del registro (se actualiza automáticamente).';

-- ================================================================
-- 8. Grants de permisos
-- ================================================================

-- Otorgar permisos básicos a usuarios autenticados
GRANT SELECT, INSERT, UPDATE, DELETE ON public.nutrition_plans 
TO authenticated;

-- Otorgar permisos completos al service role
GRANT ALL ON public.nutrition_plans TO service_role;

