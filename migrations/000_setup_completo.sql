-- ============================================================
-- Essentius — setup completo para un proyecto Supabase NUEVO
-- Pegar TODO este archivo en SQL Editor → Run
-- Incluye: human_notes + knowledge_nodes + match_knowledge_nodes + profiles + player_progress + documents
-- ============================================================

-- ---------- 1) Notas humanas ----------
create table if not exists public.human_notes (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  body text not null,
  topic text,
  user_id uuid references auth.users(id) on delete set null,
  linked_note_ids jsonb not null default '[]'::jsonb,
  human_authored boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists human_notes_user_id_idx on public.human_notes (user_id);
create index if not exists human_notes_updated_at_idx on public.human_notes (updated_at desc);

alter table public.human_notes enable row level security;

drop policy if exists "Users can read own notes" on public.human_notes;
drop policy if exists "Users can insert own notes" on public.human_notes;
drop policy if exists "Users can update own notes" on public.human_notes;
drop policy if exists "Users can delete own notes" on public.human_notes;

create policy "Users can read own notes"
  on public.human_notes for select
  using (auth.uid() = user_id or user_id is null);

create policy "Users can insert own notes"
  on public.human_notes for insert
  with check (auth.uid() = user_id or user_id is null);

create policy "Users can update own notes"
  on public.human_notes for update
  using (auth.uid() = user_id or user_id is null);

create policy "Users can delete own notes"
  on public.human_notes for delete
  using (auth.uid() = user_id or user_id is null);

-- ---------- 2) Cerebro vectorial (PDFs / RAG) ----------
create extension if not exists vector;

create table if not exists public.knowledge_nodes (
  id uuid primary key default gen_random_uuid(),
  content text not null,
  embedding vector(768) not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists knowledge_nodes_created_at_idx
  on public.knowledge_nodes (created_at desc);

create index if not exists knowledge_nodes_embedding_idx
  on public.knowledge_nodes
  using hnsw (embedding vector_cosine_ops);

alter table public.knowledge_nodes enable row level security;

create or replace function public.match_knowledge_nodes(
  query_embedding vector(768),
  match_threshold float default 0.5,
  match_count int default 5
)
returns table (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
language sql
stable
as $$
  select
    kn.id,
    kn.content,
    kn.metadata,
    (1 - (kn.embedding <=> query_embedding))::float as similarity
  from public.knowledge_nodes as kn
  where 1 - (kn.embedding <=> query_embedding) > match_threshold
  order by kn.embedding <=> query_embedding
  limit match_count;
$$;

grant execute on function public.match_knowledge_nodes(vector, float, int) to anon, authenticated, service_role;

-- ---------- 3) Perfil visual (edad / acento) ----------
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

-- ---------- 4) Progreso / gamificación ----------
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

-- ---------- 5) Catálogo de documentos (biblioteca) ----------
create table if not exists public.documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users (id) on delete cascade,
  title text not null,
  chunk_count int not null default 0,
  created_at timestamptz not null default now()
);

create index if not exists documents_user_id_idx
  on public.documents (user_id);

create index if not exists documents_created_at_idx
  on public.documents (created_at desc);

alter table public.documents enable row level security;

drop policy if exists "Users can read own documents" on public.documents;
drop policy if exists "Users can insert own documents" on public.documents;
drop policy if exists "Users can update own documents" on public.documents;
drop policy if exists "Users can delete own documents" on public.documents;

create policy "Users can read own documents"
  on public.documents for select
  using (auth.uid() = user_id or user_id is null);

create policy "Users can insert own documents"
  on public.documents for insert
  with check (auth.uid() = user_id or user_id is null);

create policy "Users can update own documents"
  on public.documents for update
  using (auth.uid() = user_id or user_id is null)
  with check (auth.uid() = user_id or user_id is null);

create policy "Users can delete own documents"
  on public.documents for delete
  using (auth.uid() = user_id or user_id is null);
