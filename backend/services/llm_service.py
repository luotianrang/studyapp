from .local_ai_analyzer import analyze_content


def extract_knowledge_points(chapter_title, chapter_content, max_chars=8000):
    analysis = analyze_content(chapter_title, (chapter_content or "")[:max_chars])
    return analysis.get("knowledge_points", [])
