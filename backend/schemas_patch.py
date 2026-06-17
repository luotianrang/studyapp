class ReviewSubmitRequest(BaseModel):
    quality: int  # 0-5 recall quality rating
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
