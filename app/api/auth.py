from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import utcnow
from app.database.session import get_db
from app.dependencies.auth import get_current_session, get_current_user
from app.models.auth_session import AuthSession
from app.models.user import User
from app.schemas.user import PasswordChangeRequest, RefreshRequest, RegisterRequest, Token, UserResponse
from app.services.auth import authenticate_user, change_password, create_session, refresh_session
from app.services.user import create_account

router = APIRouter()


def no_store(response: Response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


@router.post("/register", response_model=UserResponse, status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    return create_account(db, request, role="Student")


@router.post("/login", response_model=Token)
def login(response: Response, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    no_store(response)
    return create_session(db, authenticate_user(db, form.username, form.password))


@router.post("/refresh", response_model=Token)
def refresh(request: RefreshRequest, response: Response, db: Session = Depends(get_db)):
    no_store(response)
    return refresh_session(db, request.refresh_token)


@router.post("/logout", status_code=204)
def logout(db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
           session: AuthSession = Depends(get_current_session)):
    session.revoked_at = utcnow()
    db.flush()
    return Response(status_code=204)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/password", status_code=204)
def update_password(request: PasswordChangeRequest, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    change_password(db, current_user.id, request.current_password, request.new_password)
    return Response(status_code=204)
