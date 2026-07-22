1. Configuración del Entorno Virtual
¿Por qué un entorno Virtual?
 - Evitar el "Conflicto de Versiones"
 - Limpieza en tu Sistema Operativo
 - Replicabilidad (El archivo requirements.txt)

# Crear el entorno virtual
python -m venv venv

# Activarlo (Windows - PowerShell)
.\venv\Scripts\activate


# Activarlo (Mac/Linux)
source venv/bin/activate


2. Instalación de Dependencias Core
¿Para qué sirve cada una?

FastAPI: El framework web ultra rápido para nuestra API.

LangChain: El orquestador para conectar los LLMs con nuestras bases de datos.

Unstructured/Pytube: Para "leer" PDFs, Word y extraer datos de YouTube.

Supabase/Psycopg2: Para la base de datos relacional y vectorial.

Tavily: Para que Essentius busque en la web de forma inteligente.

pip install fastapi[all] langchain langchain-community langchain-openai unstructured[pdf] python-docx pytube youtube-transcript-api supabase psycopg2-binary tavily-python tiktoken qdrant-client

# Creacion de Estructura del proyecto con Terminal GitBash
mkdir -p app/api/v1/endpoints app/core app/domain app/services app/infrastructure/database app/infrastructure/mcp app/infrastructure/processors app/infrastructure/blockchain tests app/main.py app/api/v1/api.py app/domain/interfaces.py app/domain/models.py .env requirements.txt

essentius-backend/
├── app/
│   ├── api/                    # CAPA DE ENTRADA (Adaptadores de Entrada)
│   │   ├── v1/
│   │   │   ├── endpoints/      # Rutas: ingest.py, chat.py, calendar.py
│   │   │   └── api.py          # Router principal
│   ├── core/                   # CONFIGURACIÓN GLOBAL
│   │   ├── config.py           # Pydantic Settings (.env)
│   │   └── security.py         # JWT, hashing, etc.
│   ├── domain/                 # EL CORAZÓN (Reglas de Negocio - SOLID)
│   │   ├── models.py           # Entidades puras (User, Path, Node)
│   │   └── interfaces.py       # Interfaces/Abstracciones (Repository, Processor)
│   ├── services/               # CASOS DE USO (Application Layer)
│   │   ├── orchestrator.py     # Coordina entre IA, DB y Notion
│   │   ├── learning_service.py # Lógica para generar rutas
│   │   └── gamification.py     # Lógica de cálculo de XP
│   ├── infrastructure/         # DETALLES TÉCNICOS (Adaptadores de Salida)
│   │   ├── database/           # Supabase / pgvector repository
│   │   ├── mcp/                # Servidores MCP (Notion, Web Search)
│   │   ├── processors/         # Implementaciones de PDF, Video, Word
│   │   └── blockchain/         # Bridge para Smart Contracts (Web3.py)
│   └── main.py                 # Punto de entrada
├── tests/                      # Unitarios y de Integración
├── .env
└── pyproject.toml


# PyMuPDF (muy rápido para PDFs) o puedes usar langchain_community.document_loaders
pip install pymupdf

#Base de Datos Vectorial
pip install supabase

#GEMINI
pip install langchain-google-genai

#¿Cómo levantar el servidor?
uvicorn app.main:app --reload

# Para Levantar el servidor vamos a seguir los pasos de FastAPI
   1. Ejecutar en entorno virtual
      uvicorn app.main:
   2. Entrar a la "Sala de Control" (Swagger UI)
    Abre tu navegador web favorito.
    Ve a la siguiente dirección: http://localhost:8000/docs
   3. Prueba de Ingesta (Subir Conocimiento)
     Vamos a alimentar a Essentius con su primer documento. Busca en tu computadora un PDF pequeño (unos apuntes, un artículo corto o un temario) que sepas de qué trata.
     Despliega la pestaña del endpoint POST /api/v1/ingest/upload-pdf.
     Haz clic en el botón "Try it out" (Probar) en la esquina superior derecha de esa sección.
     Haz clic en "Seleccionar archivo" (Choose File) y sube tu PDF de prueba.
     Haz clic en el botón azul "Execute" (Ejecutar).
   4. Prueba de Chat (Consultar Conocimiento)
     Si el paso anterior funcionó, ¡Essentius ya memorizó tu PDF! Ahora vamos a interrogarlo.
     Despliega la pestaña del endpoint POST /api/v1/chat/ask.
     Haz clic en "Try it out".

## Nota de contexto del proyecto (actualizar al avanzar)

**Producto:** plataforma web de aprendizaje personalizado y autónomo.

**Doble cerebro:**
1. Cerebro de plataforma = fuentes + vectores + grafo + contraste (sesgo).
2. Notas humanas = escritura sin IA + espejo de sesgo (`/api/v1/notes`, `/api/v1/brain/bias-mirror`).

**Estado actual (2026-07):** MVP de tubería PDF→vectores→chat/grafo/Notion; flag `USE_MOCK_AI` (default true); domain models de notas y bias-mirror activos; auth opcional vía `AUTH_REQUIRED`.

**Estructura repo:** carpetas hermanas `Essentius/backend` + `Essentius/frontend` (no monorepo). Alinear por contrato API HTTP. Abrir el padre `Essentius/` si se quiere un solo workspace Cursor.

**Variables clave (.env):** `SUPABASE_URL`, `SUPABASE_KEY`, `GOOGLE_API_KEY`, `USE_MOCK_AI=true|false`, `AUTH_REQUIRED=false|true`.

**Próximo hito técnico:** `USE_MOCK_AI=false` con Gemini real; auth en producción; tests; persistir notas en Supabase (hoy in-memory).

**Próximo hito de producto:** UI `deep-learning/notes` (editor sin IA) + visualización del espejo de sesgo en frontend.

**Para el agente del frontend:** consumir `http://localhost:8000/api/v1/*`; CORS en `3000`; priorizar `library` + `path` + nueva ruta `deep-learning/notes` (editor humano-only, sin copiloto IA).