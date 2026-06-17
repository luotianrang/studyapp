from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.auth import get_current_user
from ..core.logger import get_logger
from ..database import get_db
from ..schemas import TokenResponse, UserLogin, UserRegister
from ..services.auth_service import authenticate_user, build_token_response, get_user_by_id, register_user

logger = get_logger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(req: UserRegister, db: Session = Depends(get_db)):
    try:
        user = register_user(db, req.username, req.password)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return TokenResponse(**build_token_response(user))


@router.post("/login", response_model=TokenResponse)
def login(req: UserLogin, db: Session = Depends(get_db)):
    try:
        user = authenticate_user(db, req.username, req.password)
    except PermissionError as exc:
        raise HTTPException(401, str(exc))
    return TokenResponse(**build_token_response(user))


@router.get("/me")
def get_me(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return {"user_id": user.id, "username": user.username}
