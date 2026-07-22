from typing import List
import os
import time
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.domain.interfaces import IEmbeddingProvider
from app.core.config import get_settings


class GeminiEmbeddingProvider(IEmbeddingProvider):
    def __init__(self):
        settings = get_settings()
        api_key = settings.google_api_key or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Falta la GOOGLE_API_KEY en las variables de entorno.")

        # Supabase knowledge_nodes.embedding = vector(768)
        self.embedder = GoogleGenerativeAIEmbeddings(
            model=settings.gemini_embedding_model,
            google_api_key=api_key,
            output_dimensionality=768,
        )

    def create_embedding(self, text: str) -> List[float]:
        """Llama a Gemini para convertir el texto en un vector (reintentos ante 429)."""
        chunk = (text or "")[:3000]
        last_err: Exception | None = None
        for attempt in range(3):
            try:
                return self.embedder.embed_query(chunk)
            except Exception as exc:
                last_err = exc
                msg = str(exc).lower()
                if attempt < 2 and (
                    "429" in msg
                    or "resource_exhausted" in msg
                    or "quota" in msg
                ):
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise
        assert last_err is not None
        raise last_err
