from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, time

class BookCreateRequest(BaseModel):
    title: str
    author: str = ""

class BookUpdateRequest(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None

class ChapterCreateRequest(BaseModel):
    title: str
    chapter_number: int = 0
    content: str = ""

class ChapterUpdateRequest(BaseModel):
    title: Optional[str] = None
    chapter_number: Optional[int] = None
    content: Optional[str] = None

class KnowledgePointCreateRequest(BaseModel):
    title: str
    description: str = ""
    importance: int = 3
    estimated_minutes: int = 10
    order_index: int = 0


class KnowledgePointImport(BaseModel):
    """单个知识点导入"""
    title: str
    description: str = ""
    importance: int = 3
    estimated_minutes: int = 10
    order_index: int = 0


class ChapterImport(BaseModel):
    """单个章节导入（含知识点）"""
    title: str
    chapter_number: int = 0
    content: str = ""
    status: str = "analyzed"
    knowledge_points: List[KnowledgePointImport] = []


class BulkImportRequest(BaseModel):
    """批量导入请求"""
    chapters: List[ChapterImport]

class KnowledgePointUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    importance: Optional[int] = None
    estimated_minutes: Optional[int] = None
    order_index: Optional[int] = None

class BookCreate(BaseModel):
    title: str
    author: str = ""

class BookResponse(BaseModel):
    id: int
    is_preset: bool = False
    title: str
    author: str
    total_chapters: int
    status: str
    analysis_result: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChapterResponse(BaseModel):
    id: int
    book_id: int
    title: str
    chapter_number: int
    status: str
    knowledge_point_count: int = 0
    content: str = ""
    analysis_result: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class KnowledgePointResponse(BaseModel):
    id: int
    chapter_id: int
    title: str
    description: str
    importance: int
    estimated_minutes: int
    order_index: int

    class Config:
        from_attributes = True

class PlanGenerateRequest(BaseModel):
    book_id: int
    book_ids: List[int] = []
    total_days: int
    daily_minutes: int

class PlanResponse(BaseModel):
    id: int
    book_id: int
    name: str
    total_days: int
    effective_days: int = 0
    daily_minutes: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class PlanDayResponse(BaseModel):
    id: int
    day_number: int
    target_date: Optional[datetime] = None
    total_minutes: int
    completed: bool
    items: List["PlanItemResponse"] = []
    study_items: List["PlanItemResponse"] = []
    review_items: List["PlanItemResponse"] = []

    class Config:
        from_attributes = True

class PlanItemResponse(BaseModel):
    id: int
    knowledge_point_id: int
    knowledge_point_title: str = ""
    chapter_title: str = ""
    item_type: str = "learning"
    order_index: int
    estimated_minutes: int
    completed: bool

    class Config:
        from_attributes = True

class NotificationSettingResponse(BaseModel):
    id: int
    provider: str
    notify_time: Optional[time] = None
    enabled: bool

    class Config:
        from_attributes = True

class NotificationSettingUpdate(BaseModel):
    provider: str = ""
    token: str = ""
    user_key: str = ""
    notify_time: str = "09:00"
    enabled: bool = False

class AnalysisResponse(BaseModel):
    status: str
    chapters_analyzed: int
    total_knowledge_points: int
    message: str


class UserRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    user_id: int

class ReviewSubmitRequest(BaseModel):
    quality: int
    plan_item_id: int


class ReviewStatsResponse(BaseModel):
    total_reviews: int = 0
    completed_reviews: int = 0
    pending_reviews: int = 0
    average_quality: float = 0.0


class ReviewRecordResponse(BaseModel):
    id: int
    knowledge_point_id: int
    knowledge_point_title: str = ""
    ease_factor: float
    interval_days: int
    repetitions: int
    next_review_date: Optional[str] = None
    last_review_date: Optional[str] = None
    last_quality: Optional[int] = None

    class Config:
        from_attributes = True
