import base64
import hashlib

import httpx
from urllib.parse import urlparse
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ai import AISetting
from app.schemas.ai import AISettingsUpdate

SUPPORTED_PROVIDERS = {"openai", "openai-compatible", "anthropic", "google"}


def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    return Fernet(key)


def encrypt_api_key(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_api_key(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _fernet().decrypt(value.encode()).decode()
    except (InvalidToken, ValueError) as exc:
        raise HTTPException(500, "Stored AI API key cannot be decrypted") from exc


def _validate_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized not in SUPPORTED_PROVIDERS:
        raise HTTPException(422, "Unsupported AI provider")
    return normalized


def get_settings(db: Session, teacher_id: int) -> AISetting | None:
    return db.query(AISetting).filter(AISetting.teacher_id == teacher_id).first()


def to_response(item: AISetting | None):
    if item is None:
        return {"provider": "openai-compatible", "model": "", "base_url": None,
                "has_api_key": False, "is_enabled": False}
    return {"provider": item.provider, "model": item.model, "base_url": item.base_url,
            "has_api_key": bool(item.api_key_encrypted), "is_enabled": item.is_enabled}


def save_settings(db: Session, teacher_id: int, request: AISettingsUpdate) -> AISetting:
    provider = _validate_provider(request.provider)
    item = get_settings(db, teacher_id)
    if item is None:
        item = AISetting(teacher_id=teacher_id, provider=provider, model=request.model.strip())
        db.add(item)
    item.provider = provider
    item.model = request.model.strip()
    base_url = request.base_url.strip() if request.base_url else None
    if base_url:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise HTTPException(422, "Base URL must be a valid HTTP(S) URL")
        if settings.ENVIRONMENT == "production" and parsed.scheme != "https":
            raise HTTPException(422, "Production Base URL must use HTTPS")
    item.base_url = base_url
    item.is_enabled = request.is_enabled
    if request.api_key is not None:
        item.api_key_encrypted = encrypt_api_key(request.api_key.strip())
    db.flush()
    db.refresh(item)
    return item


def clear_api_key(db: Session, teacher_id: int) -> AISetting:
    item = get_settings(db, teacher_id)
    if item is None:
        raise HTTPException(404, "AI settings not found")
    item.api_key_encrypted = None
    item.is_enabled = False
    db.flush()
    db.refresh(item)
    return item


def _endpoint(item: AISetting) -> tuple[str, dict[str, str], dict[str, str]]:
    key = decrypt_api_key(item.api_key_encrypted)
    if not key:
        raise HTTPException(422, "AI API key is not configured")
    provider = item.provider
    if provider in {"openai", "openai-compatible"}:
        base = (item.base_url or "https://api.openai.com/v1").rstrip("/")
        return f"{base}/models", {"Authorization": f"Bearer {key}"}, {}
    if provider == "anthropic":
        base = (item.base_url or "https://api.anthropic.com").rstrip("/")
        return f"{base}/v1/models", {"x-api-key": key, "anthropic-version": "2023-06-01"}, {}
    return "https://generativelanguage.googleapis.com/v1beta/models", {}, {"key": key}


async def test_connection(db: Session, teacher_id: int) -> tuple[bool, str]:
    item = get_settings(db, teacher_id)
    if item is None or not item.model:
        raise HTTPException(422, "Provider and model are required")
    url, headers, params = _endpoint(item)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, headers=headers, params=params)
    except httpx.HTTPError as exc:
        return False, f"Cannot reach provider: {exc}"
    if response.is_success:
        return True, "Connection successful"
    return False, f"Provider returned HTTP {response.status_code}"
