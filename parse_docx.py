import docx, json, re

doc = docx.Document(r'C:\Users\28618\Desktop\高数考点\高等数学上册_知识图谱.docx')

chapters = []
current_chapter = None
current_section = None

for p in doc.paragraphs:
    text = p.text.strip()
    if not text:
        continue
    ch_match = re.match(r"^第(\d+)章\s+(.+)$", text)
    if ch_match:
        if current_chapter:
            chapters.append(current_chapter)
        current_chapter = {"title": f"第{ch_match.group(1)}章 {ch_match.group(2)}", "sections": []}
        current_section = None
        continue
    if not current_chapter:
        continue
    sec_match = re.match(r"^(\d+\.\d+)\s+(.+)$", text)
    if sec_match:
        current_section = {"title": f"{sec_match.group(1)} {sec_match.group(2)}", "kps": []}
        current_chapter["sections"].append(current_section)
        continue
    kp_match = re.match(r"^[\u2022\u25cf\*\-]\s+(.+?)\s*(?:[\u3010【]难度[：:](.+)[\u3011】])?\s*$", text)
    if kp_match and current_section:
        kp_title = kp_match.group(1)
        difficulty = kp_match.group(2) or "中等"
        current_section["kps"].append({"title": kp_title, "difficulty": difficulty})

if current_chapter:
    chapters.append(current_chapter)

difficulty_map = {"简单": 2, "中等": 3, "较难": 4}
minutes_map = {"简单": 8, "中等": 12, "较难": 16}

import_data = {"chapters": []}
for ch in chapters:
    m = re.match(r"第(\d+)章", ch["title"])
    num = int(m.group(1)) if m else 0
    ch_entry = {
        "title": ch["title"],
        "chapter_number": num,
        "content": "",
        "knowledge_points": []
    }
    order = 0
    for sec in ch["sections"]:
        for kp in sec["kps"]:
            diff = kp["difficulty"]
            imp = difficulty_map.get(diff, 3)
            mins = minutes_map.get(diff, 10)
            ch_entry["knowledge_points"].append({
                "title": kp["title"],
                "description": f"所属小节：{sec['title']}  难度：{diff}",
                "importance": imp,
                "estimated_minutes": mins,
                "order_index": order
            })
            order += 1
    import_data["chapters"].append(ch_entry)

out_path = r"C:\Users\28618\Desktop\学习app\gaoshu_import.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(import_data, f, ensure_ascii=False, indent=2)

total_kps = sum(len(ch["knowledge_points"]) for ch in import_data["chapters"])
print(f"Parsed {len(chapters)} chapters, {total_kps} knowledge points")
for ch in import_data["chapters"]:
    print(f"  {ch['title']}: {len(ch['knowledge_points'])} KPs")
