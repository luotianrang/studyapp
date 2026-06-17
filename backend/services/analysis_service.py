from sqlalchemy.orm import Session

from ..core.logger import get_logger
from ..models import Book, Chapter, KnowledgePoint

logger = get_logger(__name__)


def list_chapter_knowledge_points(db: Session, chapter_id: int):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise LookupError("Chapter not found")
    return db.query(KnowledgePoint).filter(KnowledgePoint.chapter_id == chapter_id).order_by(KnowledgePoint.order_index).all()


def list_book_knowledge_points(db: Session, book_id: int):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise LookupError("Book not found")
    chapters = db.query(Chapter).filter(Chapter.book_id == book_id).all()
    chapter_ids = [chapter.id for chapter in chapters]
    return db.query(KnowledgePoint).filter(KnowledgePoint.chapter_id.in_(chapter_ids)).order_by(KnowledgePoint.order_index).all()
