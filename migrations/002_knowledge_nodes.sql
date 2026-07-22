-- Cerebro vectorial de Essentius (PDF ingest + chat RAG + bias-mirror)
-- Dimensión 768 = Gemini text-embedding-004 / mock del backend

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

-- Índice para búsqueda por similitud (cosine)
create index if not exists knowledge_nodes_embedding_idx
  on public.knowledge_nodes
  using hnsw (embedding vector_cosine_ops);

alter table public.knowledge_nodes enable row level security;

-- El backend usa service_role (bypassa RLS).
-- Sin policies públicas: anon/authenticated no leen/escriben la tabla directo.

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
