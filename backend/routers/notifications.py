from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.auth import get_current_user
from ..core.logger import get_logger
from ..database import get_db
from ..schemas import NotificationSettingResponse, NotificationSettingUpdate
from ..services.notification_service import get_notification_settings, update_notification_settings

logger = get_logger(__name__)
router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/settings", response_model=NotificationSettingResponse)
def get_settings(user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    setting = get_notification_settings(db, user_id)
    return NotificationSettingResponse(
        id=setting.id,
        provider=setting.provider,
        notify_time=setting.notify_time,
        enabled=setting.enabled,
    )


@router.put("/settings", response_model=NotificationSettingResponse)
def update_settings(update: NotificationSettingUpdate, user_id: int = Depends(get_current_user), db: Session = Depends(get_db)):
    setting = update_notification_settings(
        db,
        user_id,
        update.provider,
        update.token,
        update.user_key,
        update.notify_time,
        update.enabled,
    )
    return NotificationSettingResponse(
        id=setting.id,
        provider=setting.provider,
        notify_time=setting.notify_time,
        enabled=setting.enabled,
    )
