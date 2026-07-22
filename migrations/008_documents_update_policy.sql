-- ============================================================
-- Essentius — política UPDATE para catálogo documents
-- Necesaria para renombrar fuentes en /dashboard/library
-- ============================================================

drop policy if exists "Users can update own documents" on public.documents;

create policy "Users can update own documents"
  on public.documents for update
  using (auth.uid() = user_id or user_id is null)
  with check (auth.uid() = user_id or user_id is null);
