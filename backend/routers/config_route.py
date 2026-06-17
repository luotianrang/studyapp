import os
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from ..core.logger import get_logger
from ..services.config_service import save_deepseek_config

router = APIRouter(prefix="/api/config", tags=["config"])
logger = get_logger(__name__)

SECRETS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "secrets.json")
IS_RENDER = os.environ.get("RENDER") == "true"


class ApiKeyUpdate(BaseModel):
    api_key: str
    model: str = "deepseek-chat"


@router.post("/deepseek")
def set_deepseek_config(update: ApiKeyUpdate):
    if IS_RENDER:
        raise HTTPException(400, "Render 环境请在 Dashboard 中配置 DEEPSEEK_API_KEY 和 DEEPSEEK_MODEL")
    try:
        return save_deepseek_config(SECRETS_FILE, update.api_key, update.model)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
