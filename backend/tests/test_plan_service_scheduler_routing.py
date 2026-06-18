from types import SimpleNamespace
from datetime import datetime

from backend.services import plan_service


class DummyQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.result[0] if isinstance(self.result, list) and self.result else self.result

    def all(self):
        return self.result if isinstance(self.result, list) else [self.result]

    def count(self):
        return 0

    def join(self, *args, **kwargs):
        return self


class DummyDB:
    def __init__(self, books, kps):
        self.books = books
        self.kps = kps
        self.added = []
        self._next_id = 1

    def query(self, *models):
        if not models:
            return DummyQuery([])

        name = getattr(models[0], "__name__", "")
        if name == "Book":
            return DummyQuery(self.books)
        if name == "KnowledgePoint":
            return DummyQuery([(kp, "ch", 1, kp.book_id, f"book-{kp.book_id}") for kp in self.kps])
        return DummyQuery([])

    def add(self, *args, **kwargs):
        self.added.extend(args)
        for obj in args:
            if getattr(obj, "id", None) is None:
                obj.id = self._next_id
                self._next_id += 1
            if getattr(obj, "created_at", None) is None:
                obj.created_at = datetime.now()
        return None

    def flush(self):
        return None

    def commit(self):
        return None

    def refresh(self, obj):
        return None


def test_single_book_uses_legacy_generator(monkeypatch):
    calls = {"legacy": 0, "multi": 0}

    def fake_legacy(*args, **kwargs):
        calls["legacy"] += 1
        return [{"day": 1, "items": [], "total_minutes": 0}]

    def fake_multi(*args, **kwargs):
        calls["multi"] += 1
        return []

    monkeypatch.setattr(plan_service, "generate_plan", fake_legacy)
    monkeypatch.setattr(plan_service, "generate_interleaved_plan", fake_multi)
    monkeypatch.setattr(plan_service, "_build_learning_metrics", lambda *args, **kwargs: {})

    book = SimpleNamespace(id=1, title="Book A", status="analyzed")
    kp = SimpleNamespace(id=11, chapter_id=101, title="KP", description="", importance=3, estimated_minutes=10, order_index=0, book_id=1)
    db = DummyDB([book], [kp])

    plan_service.create_plan(db, user_id=1, book_id=1, total_days=7, daily_minutes=30, book_ids=[1])

    assert calls["legacy"] == 1
    assert calls["multi"] == 0


def test_multi_book_uses_new_scheduler(monkeypatch):
    calls = {"legacy": 0, "multi": 0}

    def fake_legacy(*args, **kwargs):
        calls["legacy"] += 1
        return [{"day": 1, "items": [], "total_minutes": 0}]

    def fake_multi(*args, **kwargs):
        calls["multi"] += 1
        return [{"day": 1, "items": [], "total_minutes": 0}]

    monkeypatch.setattr(plan_service, "generate_plan", fake_legacy)
    monkeypatch.setattr(plan_service, "generate_interleaved_plan", fake_multi)
    monkeypatch.setattr(plan_service, "_build_learning_metrics", lambda *args, **kwargs: {})

    book1 = SimpleNamespace(id=1, title="Book A", status="analyzed")
    book2 = SimpleNamespace(id=2, title="Book B", status="analyzed")
    kp1 = SimpleNamespace(id=11, chapter_id=101, title="KP1", description="", importance=3, estimated_minutes=10, order_index=0, book_id=1)
    kp2 = SimpleNamespace(id=12, chapter_id=102, title="KP2", description="", importance=3, estimated_minutes=10, order_index=0, book_id=2)
    db = DummyDB([book1, book2], [kp1, kp2])

    plan_service.create_plan(db, user_id=1, book_id=1, total_days=7, daily_minutes=30, book_ids=[1, 2])

    assert calls["legacy"] == 0
    assert calls["multi"] == 1


def test_effective_days_is_persisted_without_overwriting_total_days(monkeypatch):
    def fake_multi(*args, **kwargs):
        return [
            {"day": 1, "items": [], "total_minutes": 0},
            {"day": 2, "items": [], "total_minutes": 0},
            {"day": 3, "items": [], "total_minutes": 0},
        ]

    monkeypatch.setattr(plan_service, "generate_interleaved_plan", fake_multi)
    monkeypatch.setattr(plan_service, "_build_learning_metrics", lambda *args, **kwargs: {})

    book1 = SimpleNamespace(id=1, title="Book A", status="analyzed")
    book2 = SimpleNamespace(id=2, title="Book B", status="analyzed")
    kp1 = SimpleNamespace(id=11, chapter_id=101, title="KP1", description="", importance=3, estimated_minutes=10, order_index=0, book_id=1)
    kp2 = SimpleNamespace(id=12, chapter_id=102, title="KP2", description="", importance=3, estimated_minutes=10, order_index=0, book_id=2)
    db = DummyDB([book1, book2], [kp1, kp2])

    result = plan_service.create_plan(db, user_id=1, book_id=1, total_days=2, daily_minutes=30, book_ids=[1, 2])

    assert result.total_days == 2
    assert result.effective_days == 3
