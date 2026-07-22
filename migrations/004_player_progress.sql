-- ============================================================
-- Essentius — progreso / gamificación (nivel + prestigio)
-- ============================================================

create table if not exists public.player_progress (
  id uuid primary key references auth.users (id) on delete cascade,
  xp_cycle int not null default 0,
  level int not null default 1,
  prestige int not null default 0,
  lifetime_xp int not null default 0,
  unlocked_badges jsonb not null default '[]'::jsonb,
  daily_counts jsonb not null default '{}'::jsonb,
  daily_counts_date date,
  updated_at timestamptz not null default now()
);

create table if not exists public.player_xp_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  event_type text not null,
  xp int not null,
  created_at timestamptz not null default now()
);

create index if not exists player_xp_events_user_day_idx
  on public.player_xp_events (user_id, created_at desc);

alter table public.player_progress enable row level security;
alter table public.player_xp_events enable row level security;

drop policy if exists "Users can read own progress" on public.player_progress;
drop policy if exists "Users can insert own progress" on public.player_progress;
drop policy if exists "Users can update own progress" on public.player_progress;

create policy "Users can read own progress"
  on public.player_progress for select
  using (auth.uid() = id);

create policy "Users can insert own progress"
  on public.player_progress for insert
  with check (auth.uid() = id);

create policy "Users can update own progress"
  on public.player_progress for update
  using (auth.uid() = id);

drop policy if exists "Users can read own xp events" on public.player_xp_events;
drop policy if exists "Users can insert own xp events" on public.player_xp_events;

create policy "Users can read own xp events"
  on public.player_xp_events for select
  using (auth.uid() = user_id);

create policy "Users can insert own xp events"
  on public.player_xp_events for insert
  with check (auth.uid() = user_id);
