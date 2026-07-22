from typing import List, Any, Optional
import uuid
from app.domain.interfaces import (
    IEmbeddingProvider,
    IVectorRepository,
    ILLMProvider,
    IGraphGenerator,
    ICalendarProvider,
)
from datetime import datetime, timedelta


class MockEmbeddingProvider(IEmbeddingProvider):
    def create_embedding(self, text: str) -> List[float]:
        """Finge que va a Gemini y devuelve un vector de 768 ceros y unos."""
        print(f"🧠 [MOCK] Vectorizando texto: '{text[:20]}...'")
        return [0.1] * 768

class MockVectorRepo(IVectorRepository):
    def save_embedding(self, vector: List[float], metadata: dict):
        """Finge que guarda en Supabase."""
        print(f"💾 [MOCK] Guardando en BD: {metadata.get('source')} - Chunk {metadata.get('chunk_index')}")

    def search_similar(
        self,
        query_vector: List[float],
        limit: int = 5,
        *,
        filter_source: Optional[str] = None,
        filter_document_id: Optional[str] = None,
        match_threshold: float = 0.5,
    ) -> List[Any]:
        """Finge buscar en la base de datos y devuelve fragmentos inventados."""
        print(f"🔎 [MOCK] Buscando fragmentos similares (threshold={match_threshold})...")
        source = filter_source or "archivo_de_prueba.pdf"
        return [
            {
                "id": str(uuid.uuid4()),
                "content": "Este es un fragmento clave extraído de tu documento que responde directamente a tu pregunta.",
                "metadata": {
                    "source": source,
                    "document_id": filter_document_id,
                },
                "similarity": 0.95,
            }
        ][:limit]

class MockLLMProvider(ILLMProvider):
    def generate_answer(self, prompt: str, context: List[dict]) -> str:
        """Finge que Gemini genera una respuesta."""
        print(f"🤖 [MOCK] Generando respuesta con contexto de {len(context)} nodos...")
        return "¡Hola! Esta es una respuesta simulada de Essentius. El flujo de tu API funciona perfectamente. Cuando configures tu archivo .env, cambiaré esta respuesta por una real generada por IA."


class MockGraphGenerator(IGraphGenerator):
    def generate_roadmap(self, text: str) -> dict:
        """Simula la respuesta de Gemini sin gastar tokens (100% Gratis)."""
        print(f"🗺️ [MOCK] Analizando {len(text)} caracteres para crear el mapa...")
        
        # Devolvemos la estructura exacta que el Frontend espera
        return {
            "nodes": [
                { "id": "1", "title": "Introducción (Mock)", "description": "Conceptos base extraídos del PDF.", "category": "Módulo 1", "status": "completed" },
                { "id": "2", "title": "Teoría Principal", "description": "El núcleo de tu documento.", "category": "Módulo 2", "status": "current" },
                { "id": "3", "title": "Casos Prácticos", "description": "Aplicación en el mundo real.", "category": "Práctica", "status": "locked" },
                { "id": "4", "title": "Evaluación Final", "description": "Demuestra lo aprendido.", "category": "Examen", "status": "locked" }
            ],
            "edges": [
                { "source": "1", "target": "2" },
                { "source": "2", "target": "3" },
                { "source": "2", "target": "4" }
            ]
        }
        

class MockNotionCalendar(ICalendarProvider):
    def get_upcoming_events(self) -> List[dict]:
        print("🗓️ [MOCK MCP] Leyendo el calendario de Notion del usuario...")
        # Simulamos que el usuario tiene un examen pronto
        return [
            {"title": "Examen de Física", "date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")}
        ]

    def schedule_event(self, title: str, description: str, date: str) -> dict:
        print(f"✅ [MOCK MCP] Agendado en Notion: '{title}' para el día {date}")
        return {
            "status": "success",
            "notion_url": f"https://notion.so/mock-page-{title.replace(' ', '-')}",
            "scheduled_date": date
        }