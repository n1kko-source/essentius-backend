"""Print whether Gemini/Tavily are ready (bloque final — GUIA_INICIO §8).

Usage (from backend/ with venv):
  python scripts/check_api_readiness.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.infrastructure.live_knowledge import LiveKnowledgeProvider
from app.infrastructure.providers import get_embedding_provider, get_llm_provider


def main() -> None:
    s = get_settings()
    print("USE_MOCK_AI:", s.use_mock_ai)
    print("GOOGLE_API_KEY set:", bool(s.google_api_key))
    print("TAVILY_API_KEY set:", bool(s.tavily_api_key))
    print("GEMINI_MODEL:", s.gemini_model, "(free-tier target)")
    print("TAVILY_MAX_RESULTS:", s.tavily_max_results)
    print("embedder:", type(get_embedding_provider()).__name__)
    print("llm:", type(get_llm_provider()).__name__)
    live = LiveKnowledgeProvider().search("aprendizaje", limit=1)
    print("live mode:", live.get("mode"))

    if s.use_mock_ai or not s.google_api_key:
        print(
            "STATUS: mocks activos — free tier: "
            "pega GOOGLE_API_KEY (aistudio.google.com/apikey) y "
            "USE_MOCK_AI=false (GUIA_INICIO.md §8.1)"
        )
    else:
        print("STATUS: Gemini path activo (modelo", s.gemini_model + ")")

    if not s.tavily_api_key:
        print(
            "STATUS: Mundo en mock — free tier: "
            "pega TAVILY_API_KEY (app.tavily.com) (GUIA_INICIO.md §8.2)"
        )
    else:
        print("STATUS: Tavily key presente (mode=", live.get("mode"), ")")


if __name__ == "__main__":
    main()
