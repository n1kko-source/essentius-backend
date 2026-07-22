from typing import Optional, Any
from fastapi import Header, HTTPException, Depends
from app.core.config import get_settings
from app.infrastructure.database.supabase_client import get_supabase


async def get_current_user(authorization: str = Header(None)) -> Any:
    if not authorization:
        raise HTTPException(status_code=401, detail="No autorizado")

    supabase = get_supabase()
    token = authorization.replace("Bearer ", "")

    try:
        user = supabase.auth.get_user(token)
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


async def optional_user(authorization: str = Header(None)) -> Optional[Any]:
    """Try JWT when present; require it only if AUTH_REQUIRED=true."""
    if authorization:
        try:
            return await get_current_user(authorization=authorization)
        except HTTPException:
            if get_settings().auth_required:
                raise
            return None
    if get_settings().auth_required:
        raise HTTPException(status_code=401, detail="No autorizado")
    return None


def require_user_if_configured():
    return Depends(optional_user)


def extract_user_id(user: Any) -> Optional[str]:
    if user is None:
        return None
    inner = getattr(user, "user", user)
    uid = getattr(inner, "id", None)
    if uid:
        return str(uid)
    if isinstance(inner, dict) and inner.get("id"):
        return str(inner["id"])
    return None
