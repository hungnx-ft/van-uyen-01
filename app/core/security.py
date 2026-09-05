import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Preserve verification of existing bcrypt hashes. Pin bcrypt for passlib compatibility.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DUMMY_HASH = "$2b$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: int, session_id: str) -> str:
    now = utcnow()
    return jwt.encode(
        {
            "sub": str(user_id), "sid": session_id, "type": "access",
            "iat": now, "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            "iss": settings.TOKEN_ISSUER, "aud": settings.TOKEN_AUDIENCE,
        },
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt truncates after 72 bytes. Reject rather than accept a truncated credential.
    if len(plain_password.encode("utf-8")) > 72:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    if not 8 <= len(password) or len(password.encode("utf-8")) > 72:
        raise ValueError("Password must have at least 8 characters and at most 72 UTF-8 bytes")
    return pwd_context.hash(password)


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def refresh_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
