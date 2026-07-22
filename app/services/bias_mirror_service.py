"""Espejo de sesgo: contrasta notas humanas vs el cerebro vectorial de la plataforma.

La IA (o el mock) asiste en la COMPARACIÓN, no en la redacción de la nota.
Fase 2: opcionalmente añade evidencia viva (ciencia/educación).
"""

from typing import List, Optional

from app.domain.interfaces import IEmbeddingProvider, IVectorRepository, ILLMProvider
from app.domain.models import BiasMirrorResult, EvidenceLink
from app.core.config import get_settings


class BiasMirrorService:
    def __init__(
        self,
        embedder: IEmbeddingProvider,
        repo: IVectorRepository,
        llm: Optional[ILLMProvider] = None,
    ):
        self.embedder = embedder
        self.repo = repo
        self.llm = llm

    def mirror(
        self,
        title: str,
        body: str,
        note_id: Optional[str] = None,
        include_live: bool = False,
    ) -> BiasMirrorResult:
        query = f"{title}\n\n{body}".strip()
        vector = self.embedder.create_embedding(query)
        try:
            nodes = self.repo.search_similar(query_vector=vector, limit=5) or []
        except Exception:
            from app.infrastructure.mock_providers import MockVectorRepo

            nodes = MockVectorRepo().search_similar(query_vector=vector, limit=5)

        mode = "mock" if get_settings().use_mock_ai else "gemini"

        if not nodes:
            result = BiasMirrorResult(
                note_id=note_id,
                alignment_score=0.0,
                coverage_score=0.0,
                confirmation_bias_risk=0.8,
                summary=(
                    "No hay conocimiento en el cerebro de la plataforma para contrastar. "
                    "Sube fuentes primero; tu nota existe sola y el riesgo de sesgo es alto."
                ),
                gaps=["Sin fuentes indexadas en knowledge_nodes"],
                mode=mode,
                sources="library",
            )
        else:
            similarities = [float(n.get("similarity") or 0.0) for n in nodes]
            alignment = sum(similarities) / len(similarities)
            coverage = min(1.0, len(nodes) / 5.0)
            confirmation_bias_risk = round(
                min(1.0, max(0.0, alignment * 0.7 + (1.0 - coverage) * 0.3)), 3
            )

            supporting: List[EvidenceLink] = []
            contradicting: List[EvidenceLink] = []
            gaps: List[str] = []

            note_lower = body.lower()
            for node in nodes:
                excerpt = (node.get("content") or "")[:280]
                sim = float(node.get("similarity") or 0.0)
                source = (node.get("metadata") or {}).get("source")
                link = EvidenceLink(
                    knowledge_node_id=str(node.get("id")) if node.get("id") else None,
                    source=source,
                    excerpt=excerpt,
                    similarity=sim,
                    relation="supports" if sim >= 0.65 else "related",
                )
                if sim >= 0.55:
                    supporting.append(link)
                else:
                    contradicting.append(
                        EvidenceLink(**{**link.model_dump(), "relation": "related"})
                    )

            words = {w for w in note_lower.split() if len(w) > 5}
            corpus = " ".join([(n.get("content") or "").lower() for n in nodes])
            missing = [w for w in list(words)[:12] if w not in corpus]
            if missing:
                gaps.append(
                    "Términos de tu nota poco cubiertos por las fuentes: "
                    + ", ".join(missing[:6])
                )

            summary = self._build_summary(
                alignment=alignment,
                coverage=coverage,
                confirmation_bias_risk=confirmation_bias_risk,
                support_count=len(supporting),
                gaps=gaps,
            )

            result = BiasMirrorResult(
                note_id=note_id,
                alignment_score=round(alignment, 3),
                coverage_score=round(coverage, 3),
                confirmation_bias_risk=confirmation_bias_risk,
                summary=summary,
                supporting_evidence=supporting,
                contradicting_signals=contradicting,
                gaps=gaps,
                mode=mode,
                sources="library",
            )

        if include_live:
            result = self._merge_live(result, query)

        return result

    def _merge_live(self, result: BiasMirrorResult, query: str) -> BiasMirrorResult:
        from app.infrastructure.live_knowledge import get_live_knowledge_provider

        live = get_live_knowledge_provider().search(query, limit=5)
        external = live.get("external_evidence") or []
        citations = live.get("citations") or []
        live_mode = live.get("mode") or "mock_live"

        # Soft bump coverage when external evidence exists
        extra_cov = min(0.25, 0.05 * len(external))
        coverage = min(1.0, result.coverage_score + extra_cov)

        summary = (
            result.summary
            + " | Fuentes vivas: se añadieron referencias de ciencia/educación "
            + f"({live_mode}). No sustituyen revisión humana."
        )

        return result.model_copy(
            update={
                "coverage_score": round(coverage, 3),
                "summary": summary,
                "external_evidence": external,
                "citations": citations,
                "sources": "hybrid" if result.supporting_evidence or result.contradicting_signals else "live",
                "mode": f"{result.mode}+{live_mode}",
            }
        )

    def _build_summary(
        self,
        alignment: float,
        coverage: float,
        confirmation_bias_risk: float,
        support_count: int,
        gaps: List[str],
    ) -> str:
        if get_settings().use_mock_ai or self.llm is None:
            return (
                f"Alineación con fuentes: {alignment:.0%}. "
                f"Cobertura aproximada: {coverage:.0%}. "
                f"Riesgo de sesgo de confirmación: {confirmation_bias_risk:.0%}. "
                f"Evidencias de soporte: {support_count}. "
                + ("Gaps: " + "; ".join(gaps) if gaps else "Sin gaps léxicos obvios.")
            )

        prompt = (
            "Compara la comprensión del usuario con las fuentes. "
            "No reescribas su nota. Describe sesgos, huecos y contradicciones en 3-5 oraciones. "
            f"alignment={alignment:.2f}, coverage={coverage:.2f}, "
            f"confirmation_bias_risk={confirmation_bias_risk:.2f}, gaps={gaps}"
        )
        return self.llm.generate_answer(prompt=prompt, context=[])
