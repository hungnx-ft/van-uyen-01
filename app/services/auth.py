from datetime import timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (DUMMY_HASH, create_access_token, get_password_hash,
                               new_refresh_token, refresh_digest, utcnow, verify_password)
from app.dependencies.auth import invalid_credentials
from app.models.auth_session import AuthSession
from app.models.user import User


def authenticate_user(db: Session, username: str, password: str) -> User:
    # Serialize session creation with password changes and account locking.
    user = db.query(User).filter(User.username == username.strip()).with_for_update().first()
    valid = verify_password(password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid or not user.is_active:
        raise invalid_credentials()
    return user


def token_response(user: User, session: AuthSession, refresh_token: str):
    return {"access_token": create_access_token(user.id, session.id), "refresh_token": refresh_token,
            "token_type": "bearer", "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60}


def create_session(db: Session, user: User):
    refresh_token = new_refresh_token()
    session = AuthSession(id=str(uuid4()), user_id=user.id, refresh_token_hash=refresh_digest(refresh_token),
                          expires_at=utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    db.add(session)
    db.flush()
    return token_response(user, session, refresh_token)


def refresh_session(db: Session, refresh_token: str):
    digest = refresh_digest(refresh_token)
    candidate = db.query(AuthSession).filter(AuthSession.refresh_token_hash == digest).first()
    if not candidate:
        raise invalid_credentials()
    # Lock user before session, consistently with password changes.
    user = db.query(User).filter(User.id == candidate.user_id).with_for_update().populate_existing().first()
    session = db.query(AuthSession).filter(AuthSession.id == candidate.id).with_for_update().populate_existing().first()
    if (not user or not user.is_active or not session or session.revoked_at
            or session.expires_at <= utcnow() or session.refresh_token_hash != digest):
        raise invalid_credentials()
    replacement = new_refresh_token()
    session.refresh_token_hash = refresh_digest(replacement)
    db.flush()
    return token_response(user, session, replacement)


def revoke_all_sessions(db: Session, user_id: int):
    db.query(AuthSession).filter(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None)).update(
        {AuthSession.revoked_at: utcnow()}, synchronize_session="fetch"
    )


def change_password(db: Session, user_id: int, current_password: str, new_password: str):
    user = db.query(User).filter(User.id == user_id).with_for_update().populate_existing().one()
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect")
    user.password_hash = get_password_hash(new_password)
    revoke_all_sessions(db, user_id)
    db.flush()
