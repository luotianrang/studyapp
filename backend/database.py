import os

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .core.config import DATA_DIR, DATABASE_URL as DEFAULT_DATABASE_URL
from .core.logger import get_logger

logger = get_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _add_column_if_missing("study_plans", "user_id", "INTEGER NOT NULL DEFAULT 1")
    _add_column_if_missing("notification_settings", "user_id", "INTEGER NOT NULL DEFAULT 1")
    _add_column_if_missing("books", "analysis_result", "TEXT DEFAULT ''")
    _add_column_if_missing("chapters", "analysis_result", "TEXT DEFAULT ''")


def _column_exists(table: str, column: str) -> bool:
    try:
        result = engine.connect().execution_options(isolation_level="AUTOCOMMIT").execute(
            text(f"PRAGMA table_info({table})")
        )
        for row in result:
            if row[1] == column:
                return True
        return False
    except Exception:
        return False


def _add_column_if_missing(table: str, column: str, col_def: str):
    try:
        if not _column_exists(table, column):
            conn = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"))
            conn.close()
            logger.info(f"Migration: added column {column} to {table}")
    except Exception as exc:
        logger.warning(f"Migration: could not add {column} to {table}: {exc}")
