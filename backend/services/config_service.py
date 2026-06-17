import json
import os

from ..core.logger import get_logger

logger = get_logger(__name__)


def save_deepseek_config(secrets_file: str, api_key: str, model: str) -> dict:
    if not api_key:
        raise ValueError("API Key is required")
    key = api_key.strip()
    os.environ["DEEPSEEK_API_KEY"] = key
    os.environ["DEEPSEEK_MODEL"] = model
    try:
        with open(secrets_file, "w", encoding="utf-8") as file:
            json.dump({"deepseek_api_key": key, "deepseek_model": model}, file)
    except Exception:
        pass
    return {"message": "API Key saved", "status": "ok"}
