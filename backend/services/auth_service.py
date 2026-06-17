from sqlalchemy.orm import Session

from ..core.auth import create_access_token, hash_password, verify_password
from ..core.logger import get_logger
from ..models import User

logger = get_logger(__name__)


def register_user(db: Session, username: str, password: str) -> User:
    if len(username) < 2:
        raise ValueError("用户名至少需要2个字符")
    if len(password) < 4:
        raise ValueError("密码至少需要4个字符")

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise ValueError("用户名已存在")

    user = User(username=username, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise PermissionError("用户名或密码错误")
    return user


def build_token_response(user: User) -> dict:
    token = create_access_token({"sub": str(user.id), "username": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "user_id": user.id,
    }


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()
