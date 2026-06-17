import json
import re

from ..core.logger import get_logger

logger = get_logger(__name__)
_dynamic_api_key = None
_dynamic_model = None


def _get_api_key():
    global _dynamic_api_key
    if _dynamic_api_key:
        return _dynamic_api_key
    from ..config import DEEPSEEK_API_KEY
    return DEEPSEEK_API_KEY


def _get_deepseek_client():
    from openai import OpenAI
    from ..config import DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
    global _dynamic_model
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY not configured")
    model = _dynamic_model or DEEPSEEK_MODEL
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


def _call_llm(system_prompt, user_prompt, max_tokens=4000):
    from ..config import DEEPSEEK_MODEL
    global _dynamic_model
    client = _get_deepseek_client()
    model = _dynamic_model or DEEPSEEK_MODEL
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return response.choices[0].message.content or ""


ANALYSIS_SYSTEM_PROMPT = """你是一个专业的教材分析助手。你的任务是从教材章节中提取知识点。
对于每个章节，分析并提取出核心知识点。每个知识点需要包含：
1. 知识点标题（简洁明了）
2. 知识点描述（解释该知识点的核心内容）
3. 重要程度（1-5，5为最重要）
4. 建议学习时长（分钟）

请以JSON格式输出，格式为：
{
  "knowledge_points": [
    {
      "title": "知识点标题",
      "description": "知识点描述",
      "importance": 3,
      "estimated_minutes": 15
    }
  ]
}
"""


def extract_knowledge_points(chapter_title, chapter_content, max_chars=8000):
    # Strip OCR noise from content before analyzing
    chapter_content = _strip_ocr_noise(chapter_content)
    truncated = chapter_content[:max_chars] if len(chapter_content) > max_chars else chapter_content

    if not _get_api_key():
        logger.warning("No DeepSeek API key. Using fallback KP extraction.")
        return _fallback_knowledge_points(chapter_title, chapter_content)

    user_prompt = f"""请分析以下章节的内容，提取出核心知识点。

章节标题：{chapter_title}

章节内容：
{truncated}

请提取该章节的3-8个核心知识点，以JSON格式输出。"""

    try:
        result = _call_llm(ANALYSIS_SYSTEM_PROMPT, user_prompt, max_tokens=4000)
        result_clean = result.strip()
        if result_clean.startswith("```json"):
            result_clean = result_clean[7:]
        if result_clean.startswith("```"):
            result_clean = result_clean[3:]
        if result_clean.endswith("```"):
            result_clean = result_clean[:-3]
        result_clean = result_clean.strip()

        data = json.loads(result_clean)
        kps = data.get("knowledge_points", [])
        for i, kp in enumerate(kps):
            kp["order_index"] = i
            kp.setdefault("importance", 3)
            kp.setdefault("estimated_minutes", 10)
            kp.setdefault("description", "")
        return kps
    except json.JSONDecodeError as e:
        logger.warning(f"LLM JSON parse failed: {e}. Using fallback.")
        return _fallback_knowledge_points(chapter_title, chapter_content)
    except Exception as e:
        logger.error(f"LLM call failed: {e}. Using fallback.")
        return _fallback_knowledge_points(chapter_title, chapter_content)


def _strip_ocr_noise(text: str) -> str:
    """Aggressively strip OCR garbage from text before analysis."""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        s = line.strip()
        if not s:
            cleaned.append("")
            continue
        chinese = sum(1 for c in s if "\u4e00" <= c <= "\u9fff")
        total = sum(1 for c in s if c.isprintable() and c != " ")
        ratio = chinese / total if total > 0 else 0
        if ratio > 0.1 or (total < 20 and ratio > 0):
            s = re.sub(r"[a-zA-Z]{5,}(?![a-zA-Z])", "", s)
            s = re.sub(r"(.)\1{4,}$", r"\1", s)
            cleaned.append(s)
        elif total > 5 and chinese == 0:
            cleaned.append("")
    return "\n".join(cleaned)


def _fallback_knowledge_points(chapter_title, chapter_content):
    chapter_title = re.sub(r"[a-zA-Z]{5,}", "", chapter_title).strip()
    if not chapter_title:
        chapter_title = "未命名章节"

    content = _strip_ocr_noise(chapter_content)

    if len(content.strip()) < 50:
        return [{
            "title": chapter_title[:40] or "本章要点",
            "description": "请配置 DeepSeek API Key 以获得更精准的知识点提取",
            "importance": 3,
            "estimated_minutes": 15,
            "order_index": 0
        }]

    sentences = re.split(r"[。！？；\n]+", content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 12]

    kps = []
    seen = set()
    for i, sent in enumerate(sentences[:10]):
        s = sent[:60].rstrip("，。、；：,.;: ")
        if len(s) < 8:
            continue
        key = s[:20]
        if key in seen:
            continue
        seen.add(key)

        title = re.sub(r"[a-zA-Z]{4,}", "", s).strip()[:40]
        if not title:
            continue

        kps.append({
            "title": title,
            "description": sent[:250],
            "importance": max(2, 5 - i // 3),
            "estimated_minutes": 10 + min(i * 5, 40),
            "order_index": i
        })

    if len(kps) < 2:
        kps = [{
            "title": chapter_title[:40] or "本章要点",
            "description": content[:300] + ("..." if len(content) > 300 else ""),
            "importance": 3,
            "estimated_minutes": 25,
            "order_index": 0
        }]

    logger.info(f"Fallback KPs: {len(kps)} for {chapter_title[:30]}")
    return kps
