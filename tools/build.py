"""Собирает все модели: python3 tools/build.py -> models/<категория>/<Имя>.glb (+ .obj/.mtl)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import assets_characters
import assets_weapons
import assets_world

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models")
GROUPS = {
    "weapons": assets_weapons.ALL,
    "characters": assets_characters.ALL,
    "vehicles": assets_world.VEHICLES,
    "props": assets_world.PROPS,
}


def main():
    manifest = []
    for group, makers in GROUPS.items():
        os.makedirs(os.path.join(ROOT, group), exist_ok=True)
        os.makedirs(os.path.join(ROOT, "obj", group), exist_ok=True)
        for make in makers:
            m = make()
            glb = os.path.join(ROOT, group, m.name + ".glb")
            m.to_glb(glb)
            m.to_obj(os.path.join(ROOT, "obj", group, m.name + ".obj"), m.name + ".mtl")
            tris = sum(len(g[2]) // 3 for _, g, _ in m.meshes)
            manifest.append({"name": m.name, "group": group, "file": "%s/%s.glb" % (group, m.name),
                             "doc": (make.__doc__ or "").strip(), "triangles": tris,
                             "animations": [a[0] for a in m.anims]})
            print("%-11s %-16s %6d tris  %s" % (group, m.name, tris, ", ".join(a[0] for a in m.anims)))
    with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
