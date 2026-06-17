from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.logger import get_logger
from ..database import get_db
from ..schemas import (
    BookCreateRequest,
    BookResponse,
    BookUpdateRequest,
    BulkImportRequest,
    ChapterCreateRequest,
    ChapterResponse,
    ChapterUpdateRequest,
    KnowledgePointCreateRequest,
    KnowledgePointResponse,
    KnowledgePointUpdateRequest,
)
from ..services import admin_service

logger = get_logger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/books", response_model=List[BookResponse])
def list_admin_books(db: Session = Depends(get_db)):
    return admin_service.list_admin_books(db)


@router.post("/books", response_model=BookResponse, status_code=201)
def create_book(req: BookCreateRequest, db: Session = Depends(get_db)):
    return admin_service.create_book(db, req)


@router.put("/books/{book_id}", response_model=BookResponse)
def update_book(book_id: int, req: BookUpdateRequest, db: Session = Depends(get_db)):
    try:
        return admin_service.update_book(db, book_id, req)
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@router.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    try:
        return admin_service.delete_book(db, book_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@router.get("/books/{book_id}/chapters", response_model=List[ChapterResponse])
def list_admin_chapters(book_id: int, db: Session = Depends(get_db)):
    try:
        return admin_service.list_admin_chapters(db, book_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@router.post("/books/{book_id}/chapters", response_model=ChapterResponse, status_code=201)
def create_chapter(book_id: int, req: ChapterCreateRequest, db: Session = Depends(get_db)):
    try:
        return admin_service.create_chapter(db, book_id, req)
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@router.put("/chapters/{chapter_id}", response_model=ChapterResponse)
def update_chapter(chapter_id: int, req: ChapterUpdateRequest, db: Session = Depends(get_db)):
    try:
        return admin_service.update_chapter(db, chapter_id, req)
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@router.delete("/chapters/{chapter_id}")
def delete_chapter(chapter_id: int, db: Session = Depends(get_db)):
    try:
        return admin_service.delete_chapter(db, chapter_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@router.get("/chapters/{chapter_id}/knowledge-points", response_model=List[KnowledgePointResponse])
def list_admin_knowledge_points(chapter_id: int, db: Session = Depends(get_db)):
    try:
        return admin_service.list_admin_knowledge_points(db, chapter_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@router.post("/chapters/{chapter_id}/knowledge-points", response_model=KnowledgePointResponse, status_code=201)
def create_knowledge_point(chapter_id: int, req: KnowledgePointCreateRequest, db: Session = Depends(get_db)):
    try:
        return admin_service.create_knowledge_point(db, chapter_id, req)
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@router.put("/knowledge-points/{kp_id}", response_model=KnowledgePointResponse)
def update_knowledge_point(kp_id: int, req: KnowledgePointUpdateRequest, db: Session = Depends(get_db)):
    try:
        return admin_service.update_knowledge_point(db, kp_id, req)
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@router.delete("/knowledge-points/{kp_id}")
def delete_knowledge_point(kp_id: int, db: Session = Depends(get_db)):
    try:
        return admin_service.delete_knowledge_point(db, kp_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))


@router.post("/books/{book_id}/import", status_code=201)
def bulk_import(book_id: int, req: BulkImportRequest, db: Session = Depends(get_db)):
    try:
        return admin_service.bulk_import(db, book_id, req)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
