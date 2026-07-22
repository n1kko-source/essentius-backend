import os
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from app.domain.interfaces import ILLMProvider
from app.core.config import get_settings


class GeminiLLMProvider(ILLMProvider):
    def __init__(self):
        settings = get_settings()
        api_key = settings.google_api_key or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Falta la GOOGLE_API_KEY en las variables de entorno.")

        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=0.3,
            google_api_key=api_key,
        )

    def generate_answer(self, prompt: str, context: List[dict]) -> str:
        # Free tier: contexto acotado para no quemar cuota
        trimmed = context[:6]
        context_text = "\n\n---\n\n".join(
            [
                f"Fuente: {node.get('metadata', {}).get('source', 'Desconocida')}\n"
                f"Texto: {(node.get('content') or '')[:1200]}"
                for node in trimmed
            ]
        )

        system_prompt = f"""
        Eres Essentius, un tutor de IA avanzado y copiloto académico.
        Tu objetivo es responder a la pregunta del usuario basándote ÚNICAMENTE en el contexto proporcionado.

        Reglas:
        1. Si la respuesta no está en el contexto, di: "No encontré información sobre esto en tus documentos actuales. ¿Quieres que busque en la web?". No inventes.
        2. Mantén un tono motivador, claro y estructurado.
        3. Siempre que sea posible, cita la fuente al final de tu explicación.
        4. Respuestas concisas (máx. ~250 palabras) salvo que pidan detalle.

        CONTEXTO DE LOS DOCUMENTOS DEL USUARIO:
        {context_text}

        PREGUNTA DEL USUARIO:
        {prompt}
        """

        response = self.llm.invoke(system_prompt)
        content = response.content
        if isinstance(content, list):
            parts: List[str] = []
            for block in content:
                if isinstance(block, dict) and block.get("text"):
                    parts.append(str(block["text"]))
                elif isinstance(block, str):
                    parts.append(block)
                else:
                    parts.append(str(block))
            return "".join(parts).strip()
        return (str(content) if content is not None else "").strip()
