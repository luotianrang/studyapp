import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Time, Date
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), default="")
    is_preset = Column(Boolean, default=False)  # 是否为预设书库
    total_chapters = Column(Integer, default=0)
    current_chapter = Column(Integer, default=0)
    status = Column(String(20), default='uploaded')
    error_message = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.datetime.now)

    chapters = relationship("Chapter", back_populates="book", cascade="all, delete-orphan")
    plans = relationship("StudyPlan", back_populates="book", cascade="all, delete-orphan")

class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    title = Column(String(255), nullable=False)
    chapter_number = Column(Integer, default=0)
    content = Column(Text, default="")
    status = Column(String(20), default="pending")

    book = relationship("Book", back_populates="chapters")
    knowledge_points = relationship("KnowledgePoint", back_populates="chapter", cascade="all, delete-orphan")

class KnowledgePoint(Base):
    __tablename__ = "knowledge_points"

    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    importance = Column(Integer, default=3)
    estimated_minutes = Column(Integer, default=10)
    order_index = Column(Integer, default=0)

    chapter = relationship("Chapter", back_populates="knowledge_points")
    plan_items = relationship("PlanItem", back_populates="knowledge_point", cascade="all, delete-orphan")

class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user_id = Column(Integer, nullable=False, default=1, index=True)
    name = Column(String(255), default="")
    total_days = Column(Integer, nullable=False)
    daily_minutes = Column(Integer, nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.datetime.now)

    book = relationship("Book", back_populates="plans")
    days = relationship("PlanDay", back_populates="plan", cascade="all, delete-orphan")

class PlanDay(Base):
    __tablename__ = "plan_days"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("study_plans.id"), nullable=False)
    day_number = Column(Integer, nullable=False)
    target_date = Column(DateTime, nullable=True)
    total_minutes = Column(Integer, default=0)
    completed = Column(Boolean, default=False)

    plan = relationship("StudyPlan", back_populates="days")
    items = relationship("PlanItem", back_populates="plan_day", cascade="all, delete-orphan")

class PlanItem(Base):
    __tablename__ = "plan_items"

    id = Column(Integer, primary_key=True, index=True)
    plan_day_id = Column(Integer, ForeignKey("plan_days.id"), nullable=False)
    knowledge_point_id = Column(Integer, ForeignKey("knowledge_points.id"), nullable=False)
    item_type = Column(String(20), default="learning")  # "learning" | "review"
    order_index = Column(Integer, default=0)
    estimated_minutes = Column(Integer, default=10)
    completed = Column(Boolean, default=False)

    plan_day = relationship("PlanDay", back_populates="items")
    knowledge_point = relationship("KnowledgePoint", back_populates="plan_items")

class NotificationSetting(Base):
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, default=1, index=True)
    provider = Column(String(50), default="")
    token = Column(String(255), default="")
    user_key = Column(String(255), default="")
    notify_time = Column(Time, default=datetime.time(9, 0))
    enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.now)



class UserBook(Base):
    __tablename__ = "user_books"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.datetime.now)

    book = relationship("Book")


class ReviewRecord(Base):
    """Spaced repetition review state (SM-2) for each knowledge point in a plan"""
    __tablename__ = "review_records"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("study_plans.id"), nullable=False)
    knowledge_point_id = Column(Integer, ForeignKey("knowledge_points.id"), nullable=False)
    user_id = Column(Integer, default=1, nullable=False)

    # SM-2 parameters
    ease_factor = Column(Float, default=2.5)
    interval_days = Column(Integer, default=0)
    repetitions = Column(Integer, default=0)

    next_review_date = Column(Date, nullable=True)
    last_review_date = Column(Date, nullable=True)
    last_quality = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.now)

    plan = relationship("StudyPlan")
    knowledge_point = relationship("KnowledgePoint")


class ReviewLog(Base):
    """Audit log for every review done"""
    __tablename__ = "review_logs"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("study_plans.id"), nullable=False)
    knowledge_point_id = Column(Integer, ForeignKey("knowledge_points.id"), nullable=False)
    plan_item_id = Column(Integer, ForeignKey("plan_items.id"), nullable=False)
    user_id = Column(Integer, default=1, nullable=False)

    quality = Column(Integer, nullable=False)
    ease_factor_after = Column(Float, nullable=False)
    interval_days_after = Column(Integer, nullable=False)
    repetitions_after = Column(Integer, nullable=False)

    reviewed_at = Column(DateTime, default=datetime.datetime.now)

    plan = relationship("StudyPlan")
    knowledge_point = relationship("KnowledgePoint")
    plan_item = relationship("PlanItem")
