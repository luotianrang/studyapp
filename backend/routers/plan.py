from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.auth import get_current_user
from ..core.logger import get_logger
from ..database import get_db
from ..schemas import (
    PlanDayResponse,
    PlanGenerateRequest,
    PlanResponse,
    ReviewRecordResponse,
    ReviewStatsResponse,
    ReviewSubmitRequest,
)
from ..services import plan_service

logger = get_logger(__name__)
router = APIRouter(prefix="/api/plans", tags=["plans"])


@router.post("/generate", response_model=PlanResponse)
def create_plan(req: PlanGenerateRequest, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return plan_service.create_plan(db, user_id, req.book_id, req.total_days, req.daily_minutes, req.book_ids)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@router.get("/", response_model=list[PlanResponse])
def list_plans(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    return plan_service.list_plans(db, user_id)


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: int, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return plan_service.get_plan(db, plan_id, user_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except PermissionError as exc:
        raise HTTPException(403, str(exc))


@router.get("/{plan_id}/days", response_model=list[PlanDayResponse])
def list_plan_days(plan_id: int, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return plan_service.list_plan_days(db, plan_id, user_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except PermissionError as exc:
        raise HTTPException(403, str(exc))


@router.post("/{plan_id}/days/{day_id}/complete")
def complete_day(plan_id: int, day_id: int, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return plan_service.complete_day(db, plan_id, day_id, user_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except PermissionError as exc:
        raise HTTPException(403, str(exc))


@router.post("/{plan_id}/items/{item_id}/review")
def submit_review(plan_id: int, item_id: int, req: ReviewSubmitRequest, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return plan_service.submit_review(db, plan_id, item_id, req.quality, user_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except PermissionError as exc:
        raise HTTPException(403, str(exc))


@router.get("/{plan_id}/review-stats", response_model=ReviewStatsResponse)
def get_review_stats(plan_id: int, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return plan_service.get_review_stats(db, plan_id, user_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except PermissionError as exc:
        raise HTTPException(403, str(exc))


@router.get("/{plan_id}/review-records", response_model=list[ReviewRecordResponse])
def list_review_records(plan_id: int, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return plan_service.list_review_records(db, plan_id, user_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except PermissionError as exc:
        raise HTTPException(403, str(exc))


@router.delete("/{plan_id}")
def delete_plan(plan_id: int, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return plan_service.delete_plan(db, plan_id, user_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc))
    except PermissionError as exc:
        raise HTTPException(403, str(exc))
