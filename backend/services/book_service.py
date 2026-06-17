from sqlalchemy.orm import Session

from ..core.logger import get_logger
from ..models import Book, Chapter, KnowledgePoint, UserBook
from ..schemas import BookResponse, ChapterResponse

logger = get_logger(__name__)


def _book_response(book: Book) -> BookResponse:
    return BookResponse(
        id=book.id,
        is_preset=book.is_preset,
        title=book.title,
        author=book.author,
        total_chapters=book.total_chapters,
        status=book.status,
        created_at=book.created_at,
    )


def list_user_books(db: Session, user_id: int) -> list[BookResponse]:
    user_books = db.query(UserBook).filter(UserBook.user_id == user_id).order_by(UserBook.added_at.desc()).all()
    books = []
    for user_book in user_books:
        book = db.query(Book).filter(Book.id == user_book.book_id).first()
        if book:
            books.append(_book_response(book))
    return books


def list_preset_books(db: Session) -> list[BookResponse]:
    books = db.query(Book).filter(Book.is_preset == True).order_by(Book.created_at.desc()).all()
    return [_book_response(book) for book in books]


def add_book_to_user_learning(db: Session, user_id: int, book_id: int) -> None:
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise LookupError("Book not found")
    if not book.is_preset:
        raise ValueError("Only preset books can be added to my learning")
    existing = db.query(UserBook).filter(UserBook.user_id == user_id, UserBook.book_id == book_id).first()
    if existing:
        raise ValueError("Book already in my learning")
    db.add(UserBook(user_id=user_id, book_id=book_id))
    db.commit()


def remove_book_from_user_learning(db: Session, user_id: int, book_id: int) -> None:
    user_book = db.query(UserBook).filter(UserBook.user_id == user_id, UserBook.book_id == book_id).first()
    if not user_book:
        raise LookupError("Book not in my learning")
    db.delete(user_book)
    db.commit()


def get_book_detail(db: Session, book_id: int) -> BookResponse:
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise LookupError("Book not found")
    return _book_response(book)


def list_book_chapters(db: Session, book_id: int) -> list[ChapterResponse]:
    chapters = db.query(Chapter).filter(Chapter.book_id == book_id).order_by(Chapter.chapter_number).all()
    result = []
    for chapter in chapters:
        kp_count = db.query(KnowledgePoint).filter(KnowledgePoint.chapter_id == chapter.id).count()
        result.append(
            ChapterResponse(
                id=chapter.id,
                book_id=chapter.book_id,
                title=chapter.title,
                chapter_number=chapter.chapter_number,
                status=chapter.status,
                knowledge_point_count=kp_count,
            )
        )
    return result
