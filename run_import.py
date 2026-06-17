import urllib.request, json

with open(r"C:\Users\28618\Desktop\学习app\gaoshu_import.json", "r", encoding="utf-8") as f:
    data = json.load(f)

url = "http://localhost:8899/api/admin/books/2/import"
req_data = json.dumps(data, ensure_ascii=False).encode("utf-8")
req = urllib.request.Request(url, data=req_data, method="POST")
req.add_header("Content-Type", "application/json")

try:
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode("utf-8"))
    print(result["message"])
    print(f"Chapters created: {len(result['chapters'])}")
except Exception as e:
    print(f"Error: {e}")
