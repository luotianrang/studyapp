from sqlalchemy.orm import Session

from ..core.logger import get_logger
from ..models import Book, Chapter, KnowledgePoint
from ..schemas import (
    BookCreateRequest,
    BookResponse,
    BookUpdateRequest,
    BulkImportRequest,
    ChapterCreateRequest,
    ChapterResponse,
    ChapterUpdateRequest,
    KnowledgePointCreateRequest,
    KnowledgePointUpdateRequest,
)

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


def _chapter_response(db: Session, chapter: Chapter) -> ChapterResponse:
    kp_count = db.query(KnowledgePoint).filter(KnowledgePoint.chapter_id == chapter.id).count()
    return ChapterResponse(
        id=chapter.id,
        book_id=chapter.book_id,
        title=chapter.title,
        chapter_number=chapter.chapter_number,
        status=chapter.status,
        knowledge_point_count=kp_count,
    )


def list_admin_books(db: Session) -> list[BookResponse]:
    books = db.query(Book).filter(Book.is_preset == True).order_by(Book.created_at.desc()).all()
    return [_book_response(book) for book in books]


def create_book(db: Session, req: BookCreateRequest) -> BookResponse:
    book = Book(title=req.title, author=req.author, is_preset=True)
    db.add(book)
    db.commit()
    db.refresh(book)
    return _book_response(book)


def update_book(db: Session, book_id: int, req: BookUpdateRequest) -> BookResponse:
    book = db.query(Book).filter(Book.id == book_id, Book.is_preset == True).first()
    if not book:
        raise LookupError("Book not found")
    if req.title is not None:
        book.title = req.title
    if req.author is not None:
        book.author = req.author
    db.commit()
    db.refresh(book)
    return _book_response(book)


def delete_book(db: Session, book_id: int) -> dict:
    book = db.query(Book).filter(Book.id == book_id, Book.is_preset == True).first()
    if not book:
        raise LookupError("Book not found")
    db.delete(book)
    db.commit()
    return {"message": "Book deleted"}


def list_admin_chapters(db: Session, book_id: int) -> list[ChapterResponse]:
    book = db.query(Book).filter(Book.id == book_id, Book.is_preset == True).first()
    if not book:
        raise LookupError("Book not found")
    chapters = db.query(Chapter).filter(Chapter.book_id == book_id).order_by(Chapter.chapter_number).all()
    return [_chapter_response(db, chapter) for chapter in chapters]


def create_chapter(db: Session, book_id: int, req: ChapterCreateRequest) -> ChapterResponse:
    book = db.query(Book).filter(Book.id == book_id, Book.is_preset == True).first()
    if not book:
        raise LookupError("Book not found")
    chapter = Chapter(book_id=book_id, title=req.title, chapter_number=req.chapter_number, content=req.content)
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    book.total_chapters = db.query(Chapter).filter(Chapter.book_id == book_id).count()
    db.commit()
    return _chapter_response(db, chapter)


def update_chapter(db: Session, chapter_id: int, req: ChapterUpdateRequest) -> ChapterResponse:
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise LookupError("Chapter not found")
    if req.title is not None:
        chapter.title = req.title
    if req.chapter_number is not None:
        chapter.chapter_number = req.chapter_number
    if req.content is not None:
        chapter.content = req.content
    db.commit()
    db.refresh(chapter)
    return _chapter_response(db, chapter)


def delete_chapter(db: Session, chapter_id: int) -> dict:
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise LookupError("Chapter not found")
    book_id = chapter.book_id
    db.delete(chapter)
    book = db.query(Book).filter(Book.id == book_id).first()
    if book:
        book.total_chapters = db.query(Chapter).filter(Chapter.book_id == book_id).count()
    db.commit()
    return {"message": "Chapter deleted"}


def list_admin_knowledge_points(db: Session, chapter_id: int):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise LookupError("Chapter not found")
    return db.query(KnowledgePoint).filter(KnowledgePoint.chapter_id == chapter_id).order_by(KnowledgePoint.order_index).all()


def create_knowledge_point(db: Session, chapter_id: int, req: KnowledgePointCreateRequest):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise LookupError("Chapter not found")
    kp = KnowledgePoint(
        chapter_id=chapter_id,
        title=req.title,
        description=req.description,
        importance=req.importance,
        estimated_minutes=req.estimated_minutes,
        order_index=req.order_index,
    )
    db.add(kp)
    db.commit()
    db.refresh(kp)
    return kp


def update_knowledge_point(db: Session, kp_id: int, req: KnowledgePointUpdateRequest):
    kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == kp_id).first()
    if not kp:
        raise LookupError("Knowledge point not found")
    if req.title is not None:
        kp.title = req.title
    if req.description is not None:
        kp.description = req.description
    if req.importance is not None:
        kp.importance = req.importance
    if req.estimated_minutes is not None:
        kp.estimated_minutes = req.estimated_minutes
    if req.order_index is not None:
        kp.order_index = req.order_index
    db.commit()
    db.refresh(kp)
    return kp


def delete_knowledge_point(db: Session, kp_id: int) -> dict:
    kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == kp_id).first()
    if not kp:
        raise LookupError("Knowledge point not found")
    db.delete(kp)
    db.commit()
    return {"message": "Knowledge point deleted"}


def bulk_import(db: Session, book_id: int, req: BulkImportRequest) -> dict:
    book = db.query(Book).filter(Book.id == book_id, Book.is_preset == True).first()
    if not book:
        raise LookupError("Book not found")
    created = []
    for chapter_data in req.chapters:
        chapter = Chapter(
            book_id=book_id,
            title=chapter_data.title,
            chapter_number=chapter_data.chapter_number,
            content=chapter_data.content,
            status="pending",
        )
        db.add(chapter)
        db.flush()
        for kp_data in chapter_data.knowledge_points:
            db.add(
                KnowledgePoint(
                    chapter_id=chapter.id,
                    title=kp_data.title,
                    description=kp_data.description,
                    importance=kp_data.importance,
                    estimated_minutes=kp_data.estimated_minutes,
                    order_index=kp_data.order_index,
                )
            )
        created.append(
            {
                "id": chapter.id,
                "title": chapter.title,
                "chapter_number": chapter.chapter_number,
                "knowledge_points_count": len(chapter_data.knowledge_points),
            }
        )
    book.total_chapters = db.query(Chapter).filter(Chapter.book_id == book_id).count()
    db.commit()
    return {
        "message": f"成功导入 {len(created)} 个章节，共 {sum(item['knowledge_points_count'] for item in created)} 个知识点",
        "chapters": created,
    }
