import threading
from datetime import datetime, time

from sqlalchemy.orm import Session

from ..core.logger import get_logger
from ..models import NotificationSetting, PlanDay, PlanItem, StudyPlan
from .notifier import send_notification

logger = get_logger(__name__)
_scheduler_started = False


def get_notification_settings(db: Session, user_id: int) -> NotificationSetting:
    setting = db.query(NotificationSetting).filter(NotificationSetting.user_id == user_id).first()
    if not setting:
        setting = NotificationSetting(provider="none", enabled=False, notify_time=time(9, 0), user_id=user_id)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


def update_notification_settings(db: Session, user_id: int, provider: str, token: str, user_key: str, notify_time: str, enabled: bool) -> NotificationSetting:
    setting = db.query(NotificationSetting).filter(NotificationSetting.user_id == user_id).first()
    if not setting:
        setting = NotificationSetting(user_id=user_id)
        db.add(setting)
    setting.provider = provider
    setting.token = token
    setting.user_key = user_key
    setting.enabled = enabled
    if notify_time:
        try:
            parts = notify_time.split(":")
            setting.notify_time = time(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
        except (ValueError, IndexError):
            pass
    db.commit()
    db.refresh(setting)
    return setting


def get_due_items(db: Session):
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start.replace(hour=23, minute=59, second=59)
    return db.query(PlanItem).join(PlanDay).join(StudyPlan).filter(
        PlanDay.target_date >= today_start,
        PlanDay.target_date <= today_end,
        PlanItem.completed == False,
        StudyPlan.status == "active",
    ).order_by(PlanDay.day_number, PlanItem.order_index).all()


def run_notification_cycle(db: Session) -> None:
    setting = db.query(NotificationSetting).filter(NotificationSetting.enabled == True).first()
    if not setting:
        return
    items = get_due_items(db)
    if not items:
        return
    today_str = datetime.now().strftime("%Y-%m-%d")
    for item in items[:5]:
        plan_day = item.plan_day
        if plan_day and plan_day.target_date and plan_day.target_date.strftime("%Y-%m-%d") == today_str:
            send_notification(
                title="学习时间到！",
                message=f"今日学习内容：\n{item.estimated_minutes}分钟 路 {'待获取知识点'}\n\n坚持学习，每天进步！",
                provider=setting.provider,
                token=setting.token,
                user_key=setting.user_key,
            )
            break


def notification_loop(session_factory) -> None:
    import time as _time

    while True:
        try:
            db = session_factory()
            try:
                run_notification_cycle(db)
            finally:
                db.close()
        except Exception as exc:
            logger.error(f"Notification loop error: {exc}")
        _time.sleep(60)


def start_notification_scheduler(session_factory) -> None:
    global _scheduler_started
    if not _scheduler_started:
        _scheduler_started = True
        threading.Thread(target=notification_loop, args=(session_factory,), daemon=True).start()
        logger.info("Notification scheduler started")
