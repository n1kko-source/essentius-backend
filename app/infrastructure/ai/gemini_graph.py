import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from app.domain.interfaces import IGraphGenerator
from app.core.config import get_settings


class GeminiGraphGenerator(IGraphGenerator):
    def __init__(self):
        settings = get_settings()
        api_key = settings.google_api_key or os.environ.get("GOOGLE_API_KEY")
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=0.2,
            google_api_key=api_key,
        )

    def generate_roadmap(self, text: str) -> dict:
        # Free tier: menos tokens de entrada
        content_sample = text[:6000]

        prompt = f"""
        Eres un experto en diseño curricular y mapas mentales. Analiza el siguiente texto educativo y extrae una ruta de aprendizaje lógica.
        
        Debes devolver UNICAMENTE un objeto JSON con esta estructura exacta:
        {{
          "nodes": [
            {{ "id": "1", "title": "Nombre del Concepto", "description": "Breve resumen", "category": "Introducción", "status": "locked" }}
          ],
          "edges": [
            {{ "source": "1", "target": "2" }}
          ]
        }}

        Reglas:
        1. Máximo 6-8 nodos.
        2. El primer nodo debe ser el concepto base.
        3. Las conexiones (edges) deben representar dependencia (Para entender B, debes saber A).

        TEXTO A ANALIZAR:
        {content_sample}
        """

        response = self.llm.invoke(prompt)

        raw_content = response.content.replace("```json", "").replace("```", "").strip()

        return json.loads(raw_content)
