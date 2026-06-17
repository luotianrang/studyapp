import json
import os
import re
from collections import Counter
from typing import Any
from urllib import request

from ..core.logger import get_logger

logger = get_logger(__name__)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434")
OLLAMA_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "20"))
PREFERRED_MODELS = [
    os.environ.get("LOCAL_AI_MODEL", "").strip(),
    "llama3",
    "qwen2.5",
    "mistral",
]


def analyze_content(title: str, content: str) -> dict[str, Any]:
    clean_title = (title or "").strip() or "未命名章节"
    clean_content = _normalize_text(content)
    if not clean_content:
        return _build_empty_result(clean_title)

    ollama_result = _analyze_with_ollama(clean_title, clean_content)
    if ollama_result:
        return ollama_result

    logger.info("Using rules fallback analyzer for title=%s", clean_title[:80])
    return _analyze_with_rules(clean_title, clean_content)


def summarize_book(title: str, chapters: list[dict[str, Any]]) -> dict[str, Any]:
    joined_text = "\n".join(
        f"{chapter.get('title', '')}\n{chapter.get('content', '')}" for chapter in chapters if chapter.get("content")
    )
    summary = analyze_content(title, joined_text[:20000])
    summary["chapter_count"] = len(chapters)
    summary["knowledge_point_total"] = sum(len(chapter.get("knowledge_points", [])) for chapter in chapters)
    return summary


def _analyze_with_ollama(title: str, content: str) -> dict[str, Any] | None:
    for model in [item for item in PREFERRED_MODELS if item]:
        try:
            response_text = _call_ollama(model, title, content)
            result = _parse_model_result(response_text)
            if result:
                result["engine"] = f"ollama:{model}"
                return result
        except Exception as exc:
            logger.warning("Ollama unavailable for model=%s: %s", model, exc)
    return None


def _call_ollama(model: str, title: str, content: str) -> str:
    prompt = (
        "你是教材结构化分析助手。"
        "请只输出 JSON。"
        '格式为 {"summary":"", "knowledge_points":[{"title":"","description":"","importance":3,"estimated_minutes":10,"order_index":0}],'
        ' "tags":[""], "difficulty_estimation":{"level":"easy|medium|hard","score":1,"reason":""}}。'
        "知识点控制在 3 到 8 个。"
        f"\n章节标题：{title}\n"
        f"章节内容：\n{content[:12000]}"
    )
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
    ).encode("utf-8")
    req = request.Request(
        f"{OLLAMA_HOST.rstrip('/')}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("response", "")


def _parse_model_result(response_text: str) -> dict[str, Any] | None:
    raw = (response_text or "").strip()
    if not raw:
        return None
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    parsed = json.loads(raw.strip())
    return _normalize_result(parsed)


def _normalize_result(result: dict[str, Any]) -> dict[str, Any]:
    knowledge_points = []
    for index, kp in enumerate(result.get("knowledge_points", [])):
        title = str(kp.get("title", "")).strip()
        if not title:
            continue
        knowledge_points.append(
            {
                "title": title[:255],
                "description": str(kp.get("description", "")).strip()[:1000],
                "importance": _clamp_int(kp.get("importance", 3), 1, 5, 3),
                "estimated_minutes": _clamp_int(kp.get("estimated_minutes", 10), 5, 120, 10),
                "order_index": index,
            }
        )
    if not knowledge_points and not str(result.get("summary", "")).strip():
        return {}
    difficulty = result.get("difficulty_estimation") or {}
    return {
        "summary": str(result.get("summary", "")).strip()[:1000],
        "knowledge_points": knowledge_points,
        "tags": [str(tag).strip() for tag in result.get("tags", []) if str(tag).strip()][:12],
        "difficulty_estimation": {
            "level": str(difficulty.get("level", "medium")).strip() or "medium",
            "score": _clamp_int(difficulty.get("score", 3), 1, 5, 3),
            "reason": str(difficulty.get("reason", "")).strip()[:500],
        },
    }


def _analyze_with_rules(title: str, content: str) -> dict[str, Any]:
    sentences = _extract_sentences(content)
    summary = "；".join(sentences[:3])[:300] if sentences else content[:300]
    knowledge_points = []
    seen = set()
    for index, sentence in enumerate(sentences[:8]):
        point_title = _derive_point_title(sentence, title)
        dedupe_key = point_title[:30]
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        knowledge_points.append(
            {
                "title": point_title[:255],
                "description": sentence[:300],
                "importance": max(2, 5 - index // 2),
                "estimated_minutes": min(15 + index * 5, 60),
                "order_index": len(knowledge_points),
            }
        )
    if not knowledge_points:
        knowledge_points.append(
            {
                "title": title[:255],
                "description": summary or "已自动生成基础分析结果。",
                "importance": 3,
                "estimated_minutes": 15,
                "order_index": 0,
            }
        )
    score = _estimate_difficulty_score(content, knowledge_points)
    return {
        "summary": summary or "已自动生成基础分析结果。",
        "knowledge_points": knowledge_points,
        "tags": _extract_tags(title, content),
        "difficulty_estimation": {
            "level": _difficulty_level(score),
            "score": score,
            "reason": f"基于文本长度、术语密度和知识点数量估算，当前分值为 {score}/5。",
        },
        "engine": "rules",
    }


def _build_empty_result(title: str) -> dict[str, Any]:
    return {
        "summary": f"{title} 已自动生成空白分析结果，等待补充内容。",
        "knowledge_points": [],
        "tags": [title[:20]] if title else [],
        "difficulty_estimation": {"level": "easy", "score": 1, "reason": "章节内容为空。"},
        "engine": "rules",
    }


def _normalize_text(text: str) -> str:
    normalized = re.sub(r"\r\n?", "\n", text or "")
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _extract_sentences(content: str) -> list[str]:
    return [
        re.sub(r"\s+", " ", item).strip()
        for item in re.split(r"[。！？；\n]+", content)
        if len(re.sub(r"\s+", "", item)) >= 12
    ]


def _derive_point_title(sentence: str, fallback_title: str) -> str:
    title = sentence[:36].rstrip("，,：:、 ")
    return title or fallback_title or "核心知识点"


def _extract_tags(title: str, content: str) -> list[str]:
    words = re.findall(r"[\u4e00-\u9fff]{2,8}", f"{title}\n{content}")
    stop_words = {"我们", "你们", "可以", "一个", "这个", "以及", "进行", "学习", "章节", "内容", "知识点"}
    counts = Counter(word for word in words if word not in stop_words)
    tags = [word for word, _ in counts.most_common(6)]
    if title and title not in tags:
        tags.insert(0, title[:12])
    return tags[:8]


def _estimate_difficulty_score(content: str, knowledge_points: list[dict[str, Any]]) -> int:
    length_score = min(len(content) // 1200 + 1, 3)
    tags_score = min(len(_extract_tags("", content)) // 2 + 1, 2)
    kp_score = 1 if len(knowledge_points) >= 5 else 0
    return max(1, min(5, length_score + tags_score + kp_score))


def _difficulty_level(score: int) -> str:
    if score <= 2:
        return "easy"
    if score == 3:
        return "medium"
    return "hard"


def _clamp_int(value: Any, minimum: int, maximum: int, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))
