from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import utcnow
from app.database.session import get_db
from app.models.auth_session import AuthSession
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def invalid_credentials():
    return HTTPException(401, "Invalid or expired credentials", headers={"WWW-Authenticate": "Bearer"})


def get_current_session(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> AuthSession:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
                             issuer=settings.TOKEN_ISSUER, audience=settings.TOKEN_AUDIENCE,
                             options={"require_exp": True, "require_sub": True, "require_iat": True})
        if payload.get("type") != "access" or not isinstance(payload.get("sid"), str):
            raise invalid_credentials()
        user_id = int(payload["sub"])
    except (JWTError, ValueError, TypeError, KeyError):
        raise invalid_credentials()
    session = db.get(AuthSession, payload["sid"])
    if not session or session.user_id != user_id or session.revoked_at or session.expires_at <= utcnow():
        raise invalid_credentials()
    return session


def get_current_user(db: Session = Depends(get_db), session: AuthSession = Depends(get_current_session)) -> User:
    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        raise invalid_credentials()
    return user


def require_role(roles: list[str]):
    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(403, "Not enough permissions")
        return current_user
    return checker


def get_current_teacher(current_user: User = Depends(require_role(["Teacher"]))) -> User:
    return current_user


def get_current_student(current_user: User = Depends(require_role(["Student"]))) -> User:
    return current_user
