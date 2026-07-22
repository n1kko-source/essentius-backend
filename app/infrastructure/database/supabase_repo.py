from typing import List, Any, Optional
from app.domain.interfaces import IVectorRepository
from app.infrastructure.database.supabase_client import get_supabase


class SupabaseVectorRepo(IVectorRepository):
    def __init__(self):
        self.client = get_supabase()

    def save_embedding(self, vector: List[float], metadata: dict):
        """Guarda un fragmento y su vector en knowledge_nodes."""
        content = metadata.get("content") or metadata.get("text") or ""
        data = {
            "content": content,
            "embedding": vector,
            "metadata": metadata,
        }
        self.client.table("knowledge_nodes").insert(data).execute()

    def search_similar(
        self,
        query_vector: List[float],
        limit: int = 5,
        *,
        filter_source: Optional[str] = None,
        filter_document_id: Optional[str] = None,
        match_threshold: float = 0.5,
    ) -> List[Any]:
        # Pedimos más filas si hay filtro post-RPC (metadata jsonb).
        fetch_count = limit * 8 if (filter_source or filter_document_id) else limit
        rpc_params = {
            "query_embedding": query_vector,
            "match_threshold": match_threshold,
            "match_count": max(fetch_count, limit),
        }
        response = self.client.rpc("match_knowledge_nodes", rpc_params).execute()
        rows = response.data or []

        if filter_document_id:
            rows = [
                r
                for r in rows
                if (r.get("metadata") or {}).get("document_id") == filter_document_id
            ]
        elif filter_source:
            rows = [
                r
                for r in rows
                if (r.get("metadata") or {}).get("source") == filter_source
            ]

        return rows[:limit]
