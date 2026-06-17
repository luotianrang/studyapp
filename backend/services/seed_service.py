import json
from pathlib import Path

from sqlalchemy.orm import Session

from ..core.logger import get_logger
from ..models import Book, Chapter, KnowledgePoint

logger = get_logger(__name__)

SEED_FILE = Path(__file__).resolve().parent.parent / "preset_books_seed.json"


def ensure_preset_books_seeded(db: Session) -> int:
    existing_count = db.query(Book).filter(Book.is_preset == True).count()
    if existing_count > 0:
        logger.info("Preset books already exist, skip seeding | count=%s", existing_count)
        return 0

    if not SEED_FILE.exists():
        logger.warning("Preset seed file not found: %s", SEED_FILE)
        return 0

    payload = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    books = payload.get("books", [])
    seeded_count = 0

    for book_data in books:
        book = Book(
            title=book_data.get("title", "未命名预设书籍"),
            author=book_data.get("author", ""),
            is_preset=True,
            total_chapters=book_data.get("total_chapters", 0),
            status=book_data.get("status", "uploaded"),
            analysis_result="",
        )
        db.add(book)
        db.flush()

        for chapter_data in book_data.get("chapters", []):
            chapter = Chapter(
                book_id=book.id,
                title=chapter_data.get("title", "未命名章节"),
                chapter_number=chapter_data.get("chapter_number", 0),
                content=chapter_data.get("content", ""),
                status=chapter_data.get("status", "analyzed"),
                analysis_result="",
            )
            db.add(chapter)
            db.flush()

            for kp_data in chapter_data.get("knowledge_points", []):
                db.add(
                    KnowledgePoint(
                        chapter_id=chapter.id,
                        title=kp_data.get("title", "未命名知识点"),
                        description=kp_data.get("description", ""),
                        importance=kp_data.get("importance", 3),
                        estimated_minutes=kp_data.get("estimated_minutes", 10),
                        order_index=kp_data.get("order_index", 0),
                    )
                )

        seeded_count += 1

    db.commit()
    logger.info("Preset books seeded successfully | count=%s | source=%s", seeded_count, SEED_FILE)
    return seeded_count
