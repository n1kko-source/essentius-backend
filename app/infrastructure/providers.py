"""Factory de providers: un solo camino de código controlado por USE_MOCK_AI."""

from app.core.config import get_settings
from app.domain.interfaces import (
    IEmbeddingProvider,
    ILLMProvider,
    IGraphGenerator,
    ICalendarProvider,
)
from app.infrastructure.mock_providers import (
    MockEmbeddingProvider,
    MockLLMProvider,
    MockGraphGenerator,
    MockNotionCalendar,
)


def get_embedding_provider() -> IEmbeddingProvider:
    if get_settings().use_mock_ai:
        return MockEmbeddingProvider()
    from app.infrastructure.ai.gemini_embedder import GeminiEmbeddingProvider
    return GeminiEmbeddingProvider()


def get_llm_provider() -> ILLMProvider:
    if get_settings().use_mock_ai:
        return MockLLMProvider()
    from app.infrastructure.ai.gemini_llm import GeminiLLMProvider
    return GeminiLLMProvider()


def get_graph_generator() -> IGraphGenerator:
    if get_settings().use_mock_ai:
        return MockGraphGenerator()
    from app.infrastructure.ai.gemini_graph import GeminiGraphGenerator
    return GeminiGraphGenerator()


def get_calendar_provider() -> ICalendarProvider:
    # Notion real aún no cableado; mock siempre (MCP pendiente)
    return MockNotionCalendar()
