from typing import List

from fastapi import APIRouter, Depends, HTTPException

from ..core.logger import get_logger
from ..database import get_db
from ..schemas import KnowledgePointResponse
from ..services import analysis_service

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

logger = get_logger(__name__)


@router.get("/knowledge-points/{chapter_id}", response_model=List[KnowledgePointResponse])
def get_knowledge_points(chapter_id: int, db=Depends(get_db)):
    try:
        return analysis_service.list_chapter_knowledge_points(db, chapter_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@router.get("/book/{book_id}/knowledge-points", response_model=List[KnowledgePointResponse])
def get_all_knowledge_points(book_id: int, db=Depends(get_db)):
    try:
        return analysis_service.list_book_knowledge_points(db, book_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
