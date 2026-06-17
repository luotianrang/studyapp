import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RUNTIME_BASE_DIR = Path(os.environ.get("APP_RUNTIME_DIR", "/tmp" if os.environ.get("RENDER") == "true" else str(BASE_DIR)))
DATA_DIR = Path(os.environ.get("DATA_DIR", str(RUNTIME_BASE_DIR / "data")))
DATABASE_URL = f"sqlite:///{DATA_DIR / 'studyapp.db'}"
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", str(RUNTIME_BASE_DIR / "uploads")))

_secrets_file = BASE_DIR / "backend" / "secrets.json"
if not os.environ.get("RENDER") and _secrets_file.exists():
    try:
        with open(_secrets_file, encoding="utf-8") as file:
            _secrets = json.load(file)
            os.environ.setdefault("DEEPSEEK_API_KEY", _secrets.get("deepseek_api_key", ""))
            os.environ.setdefault("DEEPSEEK_MODEL", _secrets.get("deepseek_model", "deepseek-chat"))
    except Exception:
        pass

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

NOTIFICATION_PROVIDER = os.environ.get("NOTIFICATION_PROVIDER", "none")
NOTIFICATION_TOKEN = os.environ.get("NOTIFICATION_TOKEN", "")
NOTIFICATION_USER_KEY = os.environ.get("NOTIFICATION_USER_KEY", "")

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
