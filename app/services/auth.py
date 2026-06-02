from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.user import user as user_repo
from app.models.user import User
from app.core.security import verify_password, get_password_hash

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    db_user = user_repo.get_by_username(db, username=username)
    if not db_user:
        return None
    if not verify_password(password, db_user.password_hash):
        return None
    return db_user
