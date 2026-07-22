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
