-- Script para sincronizar nuevos tiers en Supabase
-- Ejecutar en el proyecto de Supabase correspondiente.

BEGIN;

-- Actualizar constraint CHECK existente (ajustar nombre si difiere)
ALTER TABLE public.app_users
    DROP CONSTRAINT IF EXISTS app_users_tier_check;

ALTER TABLE public.app_users
    ADD CONSTRAINT app_users_tier_check
    CHECK (tier IN ('free', 'core', 'plus', 'premium'));

-- Opcional: normalizar datos existentes al nuevo catálogo
UPDATE public.app_users
SET tier = 'free'
WHERE tier NOT IN ('free', 'core', 'plus', 'premium');

COMMIT;
