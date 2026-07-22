-- ============================================================
-- Essentius — catálogo de documentos (biblioteca PDF)
-- Persiste la lista de fuentes por usuario tras logout.
-- ============================================================

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
