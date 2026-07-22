-- ============================================================
-- Essentius — perfil extendido (país, idioma, bio, foco)
-- ============================================================

alter table public.profiles
  add column if not exists country text;

alter table public.profiles
  add column if not exists preferred_language text default 'es';

alter table public.profiles
  add column if not exists bio text;

alter table public.profiles
  add column if not exists learning_focus text;
