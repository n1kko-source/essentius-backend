from abc import ABC, abstractmethod
from typing import List, Any, Optional


class IDocumentProcessor(ABC):
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        pass

    @abstractmethod
    def create_chunks(self, text: str) -> List[str]:
        pass


class IVectorRepository(ABC):
    @abstractmethod
    def save_embedding(self, vector: List[float], metadata: dict):
        pass

    @abstractmethod
    def search_similar(
        self,
        query_vector: List[float],
        limit: int = 5,
        *,
        filter_source: Optional[str] = None,
        filter_document_id: Optional[str] = None,
        match_threshold: float = 0.5,
    ) -> List[Any]:
        pass


class IEmbeddingProvider(ABC):
    @abstractmethod
    def create_embedding(self, text: str) -> List[float]:
        """Convierte texto en un vector matemático."""
        pass


class ILLMProvider(ABC):
    @abstractmethod
    def generate_answer(self, prompt: str, context: List[dict]) -> str:
        """Genera una respuesta basada en el contexto proporcionado."""
        pass


class IGraphGenerator(ABC):
    @abstractmethod
    def generate_roadmap(self, text: str) -> dict:
        """Analiza el texto y devuelve un JSON con nodos y conexiones."""
        pass


class ICalendarProvider(ABC):
    @abstractmethod
    def schedule_event(self, title: str, description: str, date: str) -> dict:
        """Crea un evento en el calendario del usuario."""
        pass

    @abstractmethod
    def get_upcoming_events(self) -> List[dict]:
        """Lee los eventos próximos para evitar solapamientos."""
        pass


class INotesRepository(ABC):
    @abstractmethod
    def create(self, note: dict) -> dict:
        pass

    @abstractmethod
    def get(self, note_id: str) -> Optional[dict]:
        pass

    @abstractmethod
    def list_all(self, user_id: Optional[str] = None) -> List[dict]:
        pass

    @abstractmethod
    def update(self, note_id: str, fields: dict) -> Optional[dict]:
        pass

    @abstractmethod
    def delete(self, note_id: str) -> bool:
        pass
