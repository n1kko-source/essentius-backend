-- ============================================================
-- Essentius — perfil visual (edad / acento)
-- Pegar en SQL Editor si ya corriste 000_setup_completo ANTES
-- de que existiera esta tabla. Proyectos nuevos: usar 000.
-- ============================================================

create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  age_band text not null default '18-25',
  accent text not null default 'cool',
  used_recommendation boolean not null default true,
  onboarding_complete boolean not null default false,
  display_name text,
  country text,
  preferred_language text default 'es',
  bio text,
  learning_focus text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

drop policy if exists "Users can read own profile" on public.profiles;
drop policy if exists "Users can insert own profile" on public.profiles;
drop policy if exists "Users can update own profile" on public.profiles;

create policy "Users can read own profile"
  on public.profiles for select
  using (auth.uid() = id);

create policy "Users can insert own profile"
  on public.profiles for insert
  with check (auth.uid() = id);

create policy "Users can update own profile"
  on public.profiles for update
  using (auth.uid() = id);
