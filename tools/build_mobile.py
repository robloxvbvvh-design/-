"""Собирает один самодостаточный HTML со всеми моделями внутри (для телефона): Block_Royale_3D.html."""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")

manifest = json.load(open(os.path.join(ROOT, "models", "manifest.json"), encoding="utf-8"))
models = []
for e in manifest:
    with open(os.path.join(ROOT, "models", e["file"]), "rb") as f:
        models.append({"name": e["name"], "group": e["group"], "doc": e["doc"],
                       "data": base64.b64encode(f.read()).decode("ascii")})
html = open(os.path.join(HERE, "mobile_template.html"), encoding="utf-8").read()
html = html.replace("/*MODELS*/", json.dumps(models, ensure_ascii=False))
with open(os.path.join(ROOT, "Block_Royale_3D.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("Block_Royale_3D.html", len(html) // 1024, "KB")
