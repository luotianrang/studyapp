import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RUNTIME_BASE_DIR = Path(os.environ.get("APP_RUNTIME_DIR", "/tmp" if os.environ.get("RENDER") == "true" else str(BASE_DIR)))
DATA_DIR = Path(os.environ.get("DATA_DIR", str(RUNTIME_BASE_DIR / "data")))
DATABASE_URL = f"sqlite:///{DATA_DIR / 'studyapp.db'}"
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", str(RUNTIME_BASE_DIR / "uploads")))

LOCAL_AI_PROVIDER = os.environ.get("LOCAL_AI_PROVIDER", "ollama_or_rules")
LOCAL_AI_MODEL = os.environ.get("LOCAL_AI_MODEL", "")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434")

NOTIFICATION_PROVIDER = os.environ.get("NOTIFICATION_PROVIDER", "none")
NOTIFICATION_TOKEN = os.environ.get("NOTIFICATION_TOKEN", "")
NOTIFICATION_USER_KEY = os.environ.get("NOTIFICATION_USER_KEY", "")

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
