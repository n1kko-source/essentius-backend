"""Live science / education search (Fase 2).

Uses Tavily when TAVILY_API_KEY is set; otherwise returns curated mock results
so the UI and hybrid comparison path stay testable offline.
"""

from __future__ import annotations

import time
from typing import List, Dict, Optional
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.domain.models import Citation, EvidenceLink

# Soft allow-list bias toward educational / scientific domains
_PREFERRED_HINTS = (
    "edu",
    "ac.",
    "arxiv",
    "nature.com",
    "science.org",
    "nih.gov",
    "who.int",
    "unesco",
    "scholar",
    "wikipedia.org",
    "britannica",
    "mit.edu",
    "stanford.edu",
    "harvard.edu",
    "ox.ac.uk",
    "cam.ac.uk",
)

# Simple in-process cache: query -> (expires_at, payload)
_CACHE: Dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 600.0


class LiveKnowledgeProvider:
    def search(self, query: str, limit: int = 5) -> dict:
        key = f"{query.strip().lower()}::{limit}"
        now = time.time()
        cached = _CACHE.get(key)
        if cached and cached[0] > now:
            return cached[1]

        settings = get_settings()
        if settings.tavily_api_key:
            payload = self._tavily_search(query, limit=limit)
        else:
            payload = self._mock_search(query, limit=limit)

        _CACHE[key] = (now + _CACHE_TTL, payload)
        return payload

    def _tavily_search(self, query: str, limit: int) -> dict:
        settings = get_settings()
        # Prefer educational framing; free tier: basic + pocos resultados
        framed = f"{query} (science OR education OR peer-reviewed OR academic)"
        max_results = max(1, min(limit, settings.tavily_max_results, 5))
        try:
            with httpx.Client(timeout=20.0) as client:
                res = client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": settings.tavily_api_key,
                        "query": framed,
                        "search_depth": "basic",
                        "include_answer": False,
                        "max_results": max_results,
                    },
                )
                res.raise_for_status()
                data = res.json()
        except Exception:
            return self._mock_search(query, limit=limit)

        results = data.get("results") or []
        evidence: List[EvidenceLink] = []
        citations: List[Citation] = []

        for i, item in enumerate(results[:limit]):
            url = item.get("url") or ""
            title = item.get("title") or url
            content = (item.get("content") or "")[:280]
            score = float(item.get("score") or max(0.4, 0.85 - i * 0.08))
            preferred = self._is_preferred(url)
            evidence.append(
                EvidenceLink(
                    source=title,
                    excerpt=content or title,
                    similarity=min(1.0, score + (0.05 if preferred else 0)),
                    relation="supports" if score >= 0.55 else "related",
                    url=url or None,
                )
            )
            citations.append(
                Citation(title=title, url=url, snippet=content or None)
            )

        return {
            "external_evidence": evidence,
            "citations": citations,
            "mode": "tavily",
        }

    def _mock_search(self, query: str, limit: int) -> dict:
        seeds = [
            {
                "title": "UNESCO — Education research overview",
                "url": "https://www.unesco.org/en/education",
                "excerpt": (
                    f"Perspectivas educativas relacionadas con: {query[:80]}. "
                    "El aprendizaje activo y la metacognición mejoran la retención."
                ),
            },
            {
                "title": "NIH — Learning and cognition summary",
                "url": "https://www.nih.gov/",
                "excerpt": (
                    "La evidencia en ciencias cognitivas sugiere espaciado, recuperación "
                    "activa y contraste de ideas frente a repetición pasiva."
                ),
            },
            {
                "title": "arXiv — Related scholarly discussion",
                "url": "https://arxiv.org/",
                "excerpt": (
                    f"Trabajos académicos que abordan temas cercanos a «{query[:60]}». "
                    "Revisa abstracts y citas antes de concluir."
                ),
            },
            {
                "title": "Britannica — Concept overview",
                "url": "https://www.britannica.com/",
                "excerpt": (
                    "Síntesis enciclopédica útil como mapa inicial; no sustituye fuentes primarias."
                ),
            },
            {
                "title": "Nature — Science & learning context",
                "url": "https://www.nature.com/",
                "excerpt": (
                    "Hallazgos científicos pueden matizar o contradecir intuiciones personales; "
                    "busca consenso y limitaciones del estudio."
                ),
            },
        ][:limit]

        evidence = [
            EvidenceLink(
                source=s["title"],
                excerpt=s["excerpt"],
                similarity=0.72 - i * 0.06,
                relation="related" if i else "supports",
                url=s["url"],
            )
            for i, s in enumerate(seeds)
        ]
        citations = [
            Citation(title=s["title"], url=s["url"], snippet=s["excerpt"][:120])
            for s in seeds
        ]
        return {
            "external_evidence": evidence,
            "citations": citations,
            "mode": "mock_live",
        }

    @staticmethod
    def _is_preferred(url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return any(h in host for h in _PREFERRED_HINTS)


_live_provider: Optional[LiveKnowledgeProvider] = None


def get_live_knowledge_provider() -> LiveKnowledgeProvider:
    global _live_provider
    if _live_provider is None:
        _live_provider = LiveKnowledgeProvider()
    return _live_provider
