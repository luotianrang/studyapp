from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.auth import get_current_user
from ..core.logger import get_logger
from ..database import get_db
from ..schemas import BookResponse, ChapterResponse
from ..services import book_service

logger = get_logger(__name__)
router = APIRouter(prefix="/api/books", tags=["books"])


@router.get("/", response_model=list[BookResponse])
def list_books(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    return book_service.list_user_books(db, user_id)


@router.get("/preset", response_model=list[BookResponse])
def list_preset_books(db: Session = Depends(get_db)):
    return book_service.list_preset_books(db)


@router.get("/my-learning", response_model=list[BookResponse])
def list_my_learning_books(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    return book_service.list_user_books(db, user_id)


@router.post("/add-to-my-learning")
def add_to_my_learning(book_id: int, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        book_service.add_book_to_user_learning(db, user_id, book_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return {"message": "Book added to my learning"}


@router.delete("/remove-from-my-learning/{book_id}")
def remove_from_my_learning(book_id: int, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        book_service.remove_book_from_user_learning(db, user_id, book_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    return {"message": "Book removed from my learning"}


@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    try:
        return book_service.get_book_detail(db, book_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@router.get("/{book_id}/chapters", response_model=list[ChapterResponse])
def list_chapters(book_id: int, db: Session = Depends(get_db)):
    return book_service.list_book_chapters(db, book_id)
