from typing import Optional
from app.core.config import get_settings
from app.domain.interfaces import IEmbeddingProvider, IVectorRepository, ILLMProvider


_SUMMARY_HINTS = (
    "analisis",
    "análisis",
    "resume",
    "resumen",
    "resúme",
    "sintesis",
    "síntesis",
    "overview",
    "qué dice",
    "que dice",
    "de este documento",
    "del documento",
    "este archivo",
)


class ChatService:
    def __init__(
        self,
        embedder: IEmbeddingProvider,
        repo: IVectorRepository,
        llm: ILLMProvider,
    ):
        self.embedder = embedder
        self.repo = repo
        self.llm = llm

    @staticmethod
    def _is_summary_intent(question: str) -> bool:
        q = (question or "").lower()
        return any(h in q for h in _SUMMARY_HINTS)

    def ask_question(
        self,
        question: str,
        *,
        filter_source: Optional[str] = None,
        filter_document_id: Optional[str] = None,
    ) -> dict:
        """Flujo: pregunta → búsqueda vectorial (opcionalmente filtrada) → LLM."""

        question_vector = self.embedder.create_embedding(question)
        has_doc = bool(filter_source or filter_document_id)
        summary = has_doc and self._is_summary_intent(question)
        match_threshold = 0.25 if summary else (0.35 if has_doc else 0.5)
        match_count = 8 if summary else (5 if has_doc else 3)

        try:
            relevant_nodes = self.repo.search_similar(
                query_vector=question_vector,
                limit=match_count,
                filter_source=filter_source,
                filter_document_id=filter_document_id,
                match_threshold=match_threshold,
            )
        except Exception as e:
            if not get_settings().use_mock_ai:
                print(f"⚠️ [RAG] Búsqueda vectorial falló: {e}")
                return {
                    "answer": (
                        "No pude buscar en tu biblioteca indexada. "
                        "Re-sube el PDF en Biblioteca (los embeddings mock no sirven con Gemini) "
                        "e inténtalo de nuevo."
                    ),
                    "sources": [],
                    "error": "vector_search_failed",
                }
            from app.infrastructure.mock_providers import MockVectorRepo

            relevant_nodes = MockVectorRepo().search_similar(
                query_vector=question_vector,
                limit=match_count,
                filter_source=filter_source,
                filter_document_id=filter_document_id,
                match_threshold=match_threshold,
            )

        if not relevant_nodes:
            hint = (
                f' del documento "{filter_source}"'
                if filter_source
                else " en tus documentos"
            )
            return {
                "answer": (
                    f"No encontré fragmentos similares{hint}. "
                    "Si el PDF es reciente o falló a medias al subirlo, "
                    "re-súbelo en Biblioteca e inténtalo de nuevo."
                ),
                "sources": [],
            }

        answer = self.llm.generate_answer(prompt=question, context=relevant_nodes)

        sources_used = [
            {
                "source": node.get("metadata", {}).get("source"),
                "similarity": node.get("similarity"),
            }
            for node in relevant_nodes
        ]

        return {
            "answer": answer,
            "sources": sources_used,
        }
