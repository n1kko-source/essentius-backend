-- ============================================================
-- Essentius — nombre visible del usuario en profiles
-- ============================================================

alter table public.profiles
  add column if not exists display_name text;
