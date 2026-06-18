from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from ..core.logger import get_logger
from ..models import Book, Chapter, KnowledgePoint, PlanDay, PlanItem, ReviewLog, ReviewRecord, StudyPlan
from ..schemas import PlanDayResponse, PlanItemResponse, PlanResponse, ReviewRecordResponse, ReviewStatsResponse
from .plan_generator import generate_plan
from .review_scheduler import sm2_calculate
from .scheduler import generate_interleaved_plan

logger = get_logger(__name__)


def _plan_response(plan: StudyPlan) -> PlanResponse:
    return PlanResponse(
        id=plan.id,
        book_id=plan.book_id,
        name=plan.name,
        total_days=plan.total_days,
        daily_minutes=plan.daily_minutes,
        status=plan.status,
        created_at=plan.created_at,
    )


def _item_response(db: Session, item: PlanItem) -> PlanItemResponse:
    kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == item.knowledge_point_id).first()
    chapter_title = ""
    if kp:
        chapter = db.query(Chapter).filter(Chapter.id == kp.chapter_id).first()
        chapter_title = chapter.title if chapter else ""
    return PlanItemResponse(
        id=item.id,
        knowledge_point_id=item.knowledge_point_id,
        knowledge_point_title=kp.title if kp else "",
        chapter_title=chapter_title,
        item_type=item.item_type,
        order_index=item.order_index,
        estimated_minutes=item.estimated_minutes,
        completed=item.completed,
    )


def _ensure_owned_plan(db: Session, plan_id: int, user_id: int) -> StudyPlan:
    plan = db.query(StudyPlan).filter(StudyPlan.id == plan_id).first()
    if not plan:
        raise LookupError("Plan not found")
    if plan.user_id != user_id:
        raise PermissionError("Not authorized")
    return plan


def _process_review(db: Session, plan_id: int, item: PlanItem, quality: int, user_id: int) -> ReviewRecord:
    rr = db.query(ReviewRecord).filter(
        ReviewRecord.plan_id == plan_id,
        ReviewRecord.knowledge_point_id == item.knowledge_point_id,
    ).first()
    if not rr:
        rr = ReviewRecord(
            plan_id=plan_id,
            knowledge_point_id=item.knowledge_point_id,
            user_id=user_id,
            ease_factor=2.5,
            interval_days=0,
            repetitions=0,
        )
        db.add(rr)
        db.flush()
    new_ef, new_interval, new_reps = sm2_calculate(quality, rr.repetitions, rr.ease_factor, rr.interval_days)
    rr.ease_factor = new_ef
    rr.interval_days = new_interval
    rr.repetitions = new_reps
    rr.last_quality = quality
    rr.last_review_date = date.today()
    rr.next_review_date = date.today() + timedelta(days=new_interval) if new_interval > 0 else None
    db.add(
        ReviewLog(
            plan_id=plan_id,
            knowledge_point_id=item.knowledge_point_id,
            plan_item_id=item.id,
            user_id=user_id,
            quality=quality,
            ease_factor_after=new_ef,
            interval_days_after=new_interval,
            repetitions_after=new_reps,
        )
    )
    db.flush()
    return rr


def _load_books(db: Session, book_ids: list[int]) -> list[Book]:
    books = db.query(Book).filter(Book.id.in_(book_ids)).order_by(Book.id).all()
    if len(books) != len(set(book_ids)):
        raise LookupError("Book not found")
    for book in books:
        if book.status != "analyzed":
            raise ValueError(f"Book must be analyzed first. Current status: {book.status}")
    return books


def _collect_kp_list(db: Session, book_ids: list[int]) -> list[dict]:
    rows = (
        db.query(
            KnowledgePoint,
            Chapter.title.label("chapter_title"),
            Chapter.chapter_number.label("chapter_number"),
            Book.id.label("book_id"),
            Book.title.label("book_title"),
        )
        .join(Chapter, KnowledgePoint.chapter_id == Chapter.id)
        .join(Book, Chapter.book_id == Book.id)
        .filter(Chapter.book_id.in_(book_ids))
        .order_by(Book.id, Chapter.chapter_number, KnowledgePoint.order_index)
        .all()
    )

    kp_list = []
    for kp, chapter_title, chapter_number, source_book_id, book_title in rows:
        kp_list.append(
            {
                "id": kp.id,
                "title": kp.title,
                "description": kp.description,
                "importance": kp.importance,
                "difficulty": 0.5 if getattr(kp, "difficulty", None) is None else getattr(kp, "difficulty"),
                "estimated_minutes": kp.estimated_minutes,
                "order_index": kp.order_index,
                "chapter_id": kp.chapter_id,
                "chapter_title": chapter_title,
                "chapter_number": chapter_number or 0,
                "book_id": source_book_id,
                "book_title": book_title,
            }
        )
    return kp_list


def create_plan(
    db: Session,
    user_id: int,
    book_id: int,
    total_days: int,
    daily_minutes: int,
    book_ids: list[int] | None = None,
) -> PlanResponse:
    normalized_book_ids = list(dict.fromkeys(book_ids or []))
    if not normalized_book_ids:
        normalized_book_ids = [book_id]

    books = _load_books(db, normalized_book_ids)
    primary_book_id = normalized_book_ids[0]
    existing_active = db.query(StudyPlan).filter(StudyPlan.book_id == primary_book_id, StudyPlan.status == "active").first()
    if existing_active:
        raise ValueError("An active plan already exists for this book")

    kp_list = _collect_kp_list(db, normalized_book_ids)
    use_multibook = len(normalized_book_ids) > 1

    if use_multibook:
        plan_data = generate_interleaved_plan(kp_list, total_days, daily_minutes)
    else:
        plan_data = generate_plan(kp_list, total_days, daily_minutes)

    if not plan_data:
        plan_data = generate_plan(kp_list, total_days, daily_minutes)

    total_kps = sum(len(day["items"]) for day in plan_data)
    plan_title = books[0].title if len(books) == 1 else " / ".join(book.title for book in books)
    plan = StudyPlan(
        book_id=primary_book_id,
        user_id=user_id,
        name=f"{plan_title} - {total_days}澶╄鍒?{total_kps}涓煡璇嗙偣)",
        total_days=total_days,
        daily_minutes=daily_minutes,
        status="active",
    )
    db.add(plan)
    db.flush()

    for day_data in plan_data:
        target_date = None
        if day_data.get("target_date"):
            try:
                target_date = datetime.fromisoformat(day_data["target_date"])
            except (ValueError, TypeError):
                pass
        plan_day = PlanDay(
            plan_id=plan.id,
            day_number=day_data["day"],
            target_date=target_date,
            total_minutes=day_data["total_minutes"],
            completed=False,
        )
        db.add(plan_day)
        db.flush()
        for item in day_data["items"]:
            db.add(
                PlanItem(
                    plan_day_id=plan_day.id,
                    knowledge_point_id=item["knowledge_point_id"],
                    item_type=item.get("item_type", "learning"),
                    order_index=item["order_index"],
                    estimated_minutes=item["estimated_minutes"],
                    completed=False,
                )
            )

    for kp in kp_list:
        existing_rr = db.query(ReviewRecord).filter(
            ReviewRecord.plan_id == plan.id,
            ReviewRecord.knowledge_point_id == kp["id"],
        ).first()
        if not existing_rr:
            db.add(
                ReviewRecord(
                    plan_id=plan.id,
                    knowledge_point_id=kp["id"],
                    user_id=user_id,
                    ease_factor=2.5,
                    interval_days=0,
                    repetitions=0,
                )
            )

    db.commit()
    db.refresh(plan)
    return _plan_response(plan)


def list_plans(db: Session, user_id: int):
    return [_plan_response(plan) for plan in db.query(StudyPlan).filter(StudyPlan.user_id == user_id).order_by(StudyPlan.created_at.desc()).all()]


def get_plan(db: Session, plan_id: int, user_id: int) -> PlanResponse:
    return _plan_response(_ensure_owned_plan(db, plan_id, user_id))


def list_plan_days(db: Session, plan_id: int, user_id: int):
    _ensure_owned_plan(db, plan_id, user_id)
    days = db.query(PlanDay).filter(PlanDay.plan_id == plan_id).order_by(PlanDay.day_number).all()
    result = []
    for day in days:
        items = db.query(PlanItem).filter(PlanItem.plan_day_id == day.id).order_by(PlanItem.order_index).all()
        result.append(
            PlanDayResponse(
                id=day.id,
                day_number=day.day_number,
                target_date=day.target_date,
                total_minutes=day.total_minutes,
                completed=day.completed,
                items=[_item_response(db, item) for item in items],
            )
        )
    return result


def complete_day(db: Session, plan_id: int, day_id: int, user_id: int) -> dict:
    day = db.query(PlanDay).filter(PlanDay.id == day_id, PlanDay.plan_id == plan_id).first()
    if not day:
        raise LookupError("Plan day not found")
    _ensure_owned_plan(db, plan_id, user_id)
    day.completed = True
    items = db.query(PlanItem).filter(PlanItem.plan_day_id == day.id).all()
    for item in items:
        item.completed = True
    for item in items:
        if item.item_type == "review":
            existing_log = db.query(ReviewLog).filter(ReviewLog.plan_item_id == item.id).first()
            if not existing_log:
                _process_review(db, plan_id, item, quality=4, user_id=user_id)
    db.commit()
    return {"message": "Day marked as completed"}


def submit_review(db: Session, plan_id: int, item_id: int, quality: int, user_id: int) -> dict:
    if quality < 0 or quality > 5:
        raise ValueError("Quality must be 0-5")
    item = db.query(PlanItem).filter(PlanItem.id == item_id).first()
    if not item:
        raise LookupError("PlanItem not found")
    _ensure_owned_plan(db, plan_id, user_id)
    rr = _process_review(db, plan_id, item, quality, user_id)
    db.commit()
    return {
        "message": "Review recorded",
        "ease_factor": round(rr.ease_factor, 2),
        "interval_days": rr.interval_days,
        "repetitions": rr.repetitions,
        "next_review_date": rr.next_review_date.isoformat() if rr.next_review_date else None,
    }


def get_review_stats(db: Session, plan_id: int, user_id: int) -> ReviewStatsResponse:
    _ensure_owned_plan(db, plan_id, user_id)
    logs = db.query(ReviewLog).filter(ReviewLog.plan_id == plan_id).all()
    total = len(logs)
    review_items = db.query(PlanItem).join(PlanDay).filter(
        PlanDay.plan_id == plan_id,
        PlanItem.item_type == "review",
        PlanItem.completed == False,
    ).count()
    return ReviewStatsResponse(
        total_reviews=total,
        completed_reviews=total,
        pending_reviews=review_items,
        average_quality=round(sum(log.quality for log in logs) / total, 1) if total else 0.0,
    )


def list_review_records(db: Session, plan_id: int, user_id: int):
    _ensure_owned_plan(db, plan_id, user_id)
    records = db.query(ReviewRecord).filter(ReviewRecord.plan_id == plan_id).all()
    result = []
    for rr in records:
        kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == rr.knowledge_point_id).first()
        result.append(
            ReviewRecordResponse(
                id=rr.id,
                knowledge_point_id=rr.knowledge_point_id,
                knowledge_point_title=kp.title if kp else "",
                ease_factor=rr.ease_factor,
                interval_days=rr.interval_days,
                repetitions=rr.repetitions,
                next_review_date=rr.next_review_date.isoformat() if rr.next_review_date else None,
                last_review_date=rr.last_review_date.isoformat() if rr.last_review_date else None,
                last_quality=rr.last_quality,
            )
        )
    return result


def delete_plan(db: Session, plan_id: int, user_id: int) -> dict:
    plan = _ensure_owned_plan(db, plan_id, user_id)
    db.delete(plan)
    db.commit()
    return {"message": "Plan deleted"}
