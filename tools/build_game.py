"""Собирает игру «Блок Рояль: Захват» в один HTML-файл со встроенными моделями: Block_Royale_Capture.html."""
import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
NEEDED = {"Ranger", "BoltRobot", "ShadowNinja", "Astronaut", "Pistol", "AssaultRifle", "SMG_Uzi", "PumpShotgun",
          "SniperRifle", "RocketLauncher", "Tank", "Chest", "ChestRare", "AmmoBox", "SupplyDrop", "BuildWall",
          "BuildFloor", "PineTree", "OakTree", "Rock", "Bush"}

manifest = json.load(open(os.path.join(ROOT, "models", "manifest.json"), encoding="utf-8"))
models = []
for e in manifest:
    if e["name"] in NEEDED:
        with open(os.path.join(ROOT, "models", e["file"]), "rb") as f:
            models.append({"name": e["name"], "data": base64.b64encode(f.read()).decode("ascii")})
html = open(os.path.join(HERE, "game_template.html"), encoding="utf-8").read()
html = html.replace("/*MODELS*/", json.dumps(models))
with open(os.path.join(ROOT, "Block_Royale_Capture.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("Block_Royale_Capture.html", len(html) // 1024, "KB")
