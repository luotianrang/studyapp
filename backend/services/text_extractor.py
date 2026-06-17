import os
import re

from ..core.logger import get_logger

logger = get_logger(__name__)


def _clean_title(title: str) -> str:
    cleaned = []
    ascii_run = 0
    for ch in title:
        is_chinese = "\u4e00" <= ch <= "\u9fff" or "\u3400" <= ch <= "\u4dbf"
        if is_chinese:
            cleaned.append(ch)
            ascii_run = 0
        elif ch.isdigit() or ch in "()[]{}.,:;!?-_/\\ ":
            cleaned.append(ch)
            ascii_run = 0
        elif ord(ch) < 128 and ch.isalpha():
            if ascii_run < 3:
                cleaned.append(ch)
                ascii_run += 1
        else:
            cleaned.append(ch)
            ascii_run = 0
    result = "".join(cleaned).strip()
    result = re.sub(r"(.)\1{4,}$", r"\1", result)
    result = re.sub(r"(\s+[a-zA-Z]{1,4}){2,}\s*$", "", result)
    result = re.sub(r"\s+[a-zA-Z]{5,}\s*$", "", result)
    result = re.sub(r"\s+[A-Za-z\d]{1,4}$", "", result)
    result = re.sub(r"[\u4e00-\u9fff][A-Za-z\d]{2,6}$", lambda m: m.group(0)[0], result)
    return result.strip() if result.strip() else title


def _clean_ocr_text(text: str) -> str:
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        s = line.strip()
        if not s:
            cleaned.append("")
            continue
        chinese = sum(1 for c in s if "\u4e00" <= c <= "\u9fff" or "\u3400" <= c <= "\u4dbf")
        total = sum(1 for c in s if c.isprintable() and c != " ")
        if total > 5 and chinese == 0:
            words = s.split()
            if len(words) <= 2 or all(len(w) > 15 for w in words):
                continue
        if total > 10:
            repeats = sum(1 for j in range(1, len(s)) if s[j] == s[j - 1])
            if repeats > total * 0.6:
                continue
        if total <= 5 and all(c.isdigit() or c.isspace() for c in s):
            continue
        cleaned.append(s)
    result_lines = []
    prev_empty = False
    for line in cleaned:
        empty = line == ""
        if empty and prev_empty:
            continue
        result_lines.append(line)
        prev_empty = empty
    return "\n".join(result_lines)


def extract_text_from_txt(filepath: str) -> str:
    encodings = ["utf-8", "gb18030", "gbk", "gb2312", "latin-1"]
    for enc in encodings:
        try:
            with open(filepath, "r", encoding=enc, errors="strict") as f:
                text = f.read()
            if text.strip():
                return text
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError("Cannot decode text file. Tried: " + ", ".join(encodings))


def _normal_pdf_extraction(filepath: str) -> str:
    import fitz

    doc = fitz.open(filepath)
    text_parts = [page.get_text() for page in doc if page.get_text().strip()]
    doc.close()
    return "\n\n".join(text_parts)


def _ocr_pdf_extraction(filepath: str, max_pages: int = 400) -> str:
    try:
        import pytesseract
    except ImportError:
        raise ImportError("pytesseract required: pip install pytesseract")
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("Pillow required: pip install Pillow")

    if os.name == "nt":
        for tp in [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        ]:
            if os.path.exists(tp):
                pytesseract.pytesseract.tesseract_cmd = tp
                break

    import fitz

    doc = fitz.open(filepath)
    total_pages = min(len(doc), max_pages)
    logger.info(f"OCR: {total_pages} pages")
    text_parts = []
    for i in range(total_pages):
        try:
            page = doc[i]
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img, lang="chi_sim+eng")
            text = _clean_ocr_text(text)
            if text.strip():
                text_parts.append(text)
            if (i + 1) % 10 == 0 or i == total_pages - 1:
                logger.info(f"OCR progress: {i+1}/{total_pages} pages")
        except Exception as e:
            logger.warning(f"OCR failed page {i+1}: {e}")
    doc.close()
    result = "\n\n".join(text_parts)
    logger.info(f"OCR done: {len(text_parts)} pages, {len(result)} chars")
    return result


def extract_text_from_pdf(filepath: str) -> str:
    normal = _normal_pdf_extraction(filepath)
    if normal.strip():
        return normal
    logger.info("No text layer, switching to OCR")
    return _ocr_pdf_extraction(filepath)


def extract_text(filepath: str, file_type: str) -> str:
    if file_type == "txt":
        return extract_text_from_txt(filepath)
    if file_type == "pdf":
        return extract_text_from_pdf(filepath)
    raise ValueError(f"Unsupported type: {file_type}")


_MAIN_CHAPTER_RE = re.compile(r"^\s*(chapter\s+\d+|第[一二三四五六七八九十百千0-9]+章|\d+\s*章)", re.IGNORECASE)
_SUB_HEADING_RE = re.compile(
    r"^\s*(chapter\s+\d+\.\d+|第[一二三四五六七八九十百千0-9]+节|\d+\.\d+\s|\d+\s*[、.])",
    re.IGNORECASE,
)


def detect_chapters(text: str) -> list[dict]:
    lines = text.split("\n")
    chapters = []
    current = {"title": "", "content": "", "number": 0}

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current["content"] += "\n"
            continue
        if _MAIN_CHAPTER_RE.match(stripped):
            if current["content"].strip() and len(current["content"].strip()) > 50:
                if not current["title"]:
                    current["title"] = "前言"
                current["number"] = len(chapters) + 1
                chapters.append(current)
            current = {"title": _clean_title(stripped), "content": "", "number": 0}
        else:
            current["content"] += line + "\n"

    if current["content"].strip():
        if not current["title"]:
            current["title"] = "前言"
        current["number"] = len(chapters) + 1
        if len(current["content"].strip()) > 50:
            chapters.append(current)

    if len(chapters) <= 1:
        logger.info(f"Only {len(chapters)} main chapters, fallback to sub-headings")
        chapters = _fallback_chapter_split(text)

    chapters = _merge_small_chapters(chapters)
    logger.info(f"Final: {len(chapters)} chapters from {len(text)} chars")
    return chapters


def _fallback_chapter_split(text: str) -> list[dict]:
    lines = text.split("\n")
    chapters = []
    current = {"title": "前言", "content": "", "number": 0}
    for line in lines:
        stripped = line.strip()
        if not stripped:
            current["content"] += "\n"
            continue
        if _SUB_HEADING_RE.match(stripped) and len(current["content"].strip()) > 200:
            if len(current["content"].strip()) > 100:
                current["number"] = len(chapters) + 1
                chapters.append(current)
            current = {"title": _clean_title(stripped), "content": "", "number": 0}
        else:
            current["content"] += line + "\n"
    if current["content"].strip() and len(current["content"].strip()) > 50:
        current["number"] = len(chapters) + 1
        chapters.append(current)
    if len(chapters) <= 1:
        return [{"title": "全文内容", "content": text, "number": 1}]
    return chapters


def _merge_small_chapters(chapters: list[dict], min_content: int = 300) -> list[dict]:
    if len(chapters) <= 2:
        return chapters
    merged = []
    buffer = None
    for ch in chapters:
        if len(ch["content"].strip()) < min_content:
            if buffer is None:
                buffer = ch
            else:
                buffer["content"] += "\n\n" + ch["title"] + "\n" + ch["content"]
                buffer["title"] = buffer["title"] + " + " + _clean_title(ch["title"][:30])
        else:
            if buffer is not None:
                if len(buffer["content"].strip()) > 50:
                    merged.append(buffer)
                buffer = None
            merged.append(ch)
    if buffer is not None and len(buffer["content"].strip()) > 50:
        merged.append(buffer)
    return merged if merged else chapters
