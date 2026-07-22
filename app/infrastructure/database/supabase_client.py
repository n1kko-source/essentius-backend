from supabase import create_client, Client
from app.core.config import get_settings


def get_supabase() -> Client:
    settings = get_settings()
    url = (settings.supabase_url or "").rstrip("/")
    key = settings.supabase_key

    if not url or not key:
        raise ValueError("Faltan SUPABASE_URL / SUPABASE_KEY en el archivo .env")

    # El cliente de Supabase espera la URL del proyecto, no /rest/v1
    if url.endswith("/rest/v1"):
        url = url[: -len("/rest/v1")]

    return create_client(url, key)
