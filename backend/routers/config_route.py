from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/config", tags=["config"])


@router.post("/deepseek")
def set_deepseek_config():
    raise HTTPException(status_code=410, detail="DeepSeek configuration has been disabled. The app now uses local automatic analysis.")
