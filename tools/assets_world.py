"""Техника и предметы мира: танк, сундуки, ящики, лечение, постройки, природа."""
import math

from gltf_builder import Model, box, tbox, cyl, sphere, prism, merge, xf


def tank():
    """Лёгкий танк ~6.4 м: гусеницы, вращающаяся башня, ствол, люк командира."""
    m = Model("Tank")
    m.mat("Armor", "#5d6b3a", metal=0.35, rough=0.6)
    m.mat("ArmorDark", "#434e2a", metal=0.35, rough=0.65)
    m.mat("Camo", "#8a7a4a", metal=0.2, rough=0.7)
    m.mat("Track", "#25262a", metal=0.4, rough=0.85)
    m.mat("Wheel", "#3a3d42", metal=0.6, rough=0.5)
    m.mat("Steel", "#8b9098", metal=0.85, rough=0.35)
    m.mat("Light", "#fff3c4", emissive="#ffe49a")
    m.mat("Mark", "#f2c230", rough=0.5)
    m.mat("Flash", "#ffd36b", emissive="#ffb020", alpha=0.85)

    m.node("Tank")
    m.node("Hull", "Tank")
    # корпус
    m.part("LowerHull", tbox(2.3, 5.6, 2.3, 6.0, 0.8), "ArmorDark", "Hull", t=(0, 0.85, 0))
    up = prism([(-1.8, 1.25, -3.15), (1.8, 1.25, -3.15), (1.8, 1.25, 3.3), (-1.8, 1.25, 3.3),
                (-1.7, 1.65, -3.0), (1.7, 1.65, -3.0), (1.7, 1.65, 2.0), (-1.7, 1.65, 2.0)])
    m.part("UpperHull", up, "Armor", "Hull")
    m.part("Glacis", prism([(-1.1, 0.5, 2.8), (1.1, 0.5, 2.8), (1.1, 0.95, 3.25), (-1.1, 0.95, 3.25),
                            (-1.1, 1.2, 2.8), (1.1, 1.2, 2.8), (1.1, 1.25, 3.3), (-1.1, 1.25, 3.3)]), "ArmorDark", "Hull")
    m.part("CamoPatches", merge(xf(box(1.0, 0.02, 1.4), t=(-0.8, 1.66, 0.4), r=(0, 20, 0)),
                                xf(box(0.8, 0.02, 1.1), t=(0.9, 1.66, -1.8), r=(0, -30, 0)),
                                xf(box(0.7, 0.02, 0.9), t=(0.6, 1.66, 1.4), r=(0, 50, 0))), "Camo", "Hull")
    m.part("Headlights", merge(xf(cyl(0.12, None, 0.1, 12, "z"), t=(1.4, 1.45, 2.65)), xf(cyl(0.12, None, 0.1, 12, "z"), t=(-1.4, 1.45, 2.65))),
           "Light", "Hull")
    m.part("LightHousings", merge(xf(cyl(0.15, None, 0.15, 12, "z"), t=(1.4, 1.45, 2.58)), xf(cyl(0.15, None, 0.15, 12, "z"), t=(-1.4, 1.45, 2.58))),
           "Steel", "Hull")
    m.part("Exhausts", merge(xf(cyl(0.11, None, 0.5, 10, "z"), t=(1.1, 1.4, -3.3)), xf(cyl(0.11, None, 0.5, 10, "z"), t=(-1.1, 1.4, -3.3))),
           "Steel", "Hull")
    m.part("EngineGrill", merge(*[xf(box(2.0, 0.04, 0.08), t=(0, 1.67, -2.7 + i * 0.2)) for i in range(5)]), "Track", "Hull")
    m.part("Hooks", merge(xf(box(0.12, 0.2, 0.2), t=(0.8, 0.75, 3.05)), xf(box(0.12, 0.2, 0.2), t=(-0.8, 0.75, 3.05))),
           "Steel", "Hull")
    m.part("Number", box(0.5, 0.25, 0.02), "Mark", "Hull", t=(0.55, 1.28, 3.31))
    # гусеницы и катки
    for side, sx in (("L", 1), ("R", -1)):
        x = 1.45 * sx
        tr = merge(xf(box(0.62, 0.09, 5.4), t=(0, 1.0, 0)), xf(box(0.62, 0.09, 4.8), t=(0, 0.045, 0)),
                   xf(box(0.62, 0.09, 0.95), t=(0, 0.25, 2.75), r=(-35, 0, 0)), xf(box(0.62, 0.09, 0.95), t=(0, 0.25, -2.75), r=(35, 0, 0)),
                   *[xf(box(0.64, 0.03, 0.06), t=(0, 1.05, z * 0.3)) for z in range(-9, 10)],
                   *[xf(box(0.64, 0.03, 0.06), t=(0, 0.0, z * 0.3)) for z in range(-8, 9)])
        m.part("Track_" + side, tr, "Track", "Hull", t=(x, 0, 0))
        m.part("Skirt_" + side, box(0.06, 0.45, 6.2), "Armor", "Hull", t=(x + 0.33 * sx, 0.95, 0.05))
        for i, z in enumerate((-2.2, -1.32, -0.44, 0.44, 1.32, 2.2)):
            n = "Wheel_%s%d" % (side, i)
            spokes = merge(cyl(0.4, None, 0.5, 18, "x"), xf(cyl(0.16, None, 0.54, 10, "x")),
                           *[xf(box(0.56, 0.06, 0.6), r=(a, 0, 0)) for a in (0, 60, 120)])
            m.part(n, spokes, "Wheel", "Hull", t=(x, 0.5, z))
        for n, z, r in (("Sprocket_" + side, -2.95, 0.42), ("Idler_" + side, 2.95, 0.38)):
            teeth = merge(cyl(r, None, 0.5, 16, "x"), *[xf(box(0.3, 0.12, 2 * r + 0.1), r=(a, 0, 0)) for a in (0, 30, 60, 90, 120, 150)])
            m.part(n, teeth, "Steel", "Hull", t=(x, 0.55, z))
    # башня
    m.node("Turret", "Hull", t=(0, 1.65, -0.3))
    m.part("TurretRing", cyl(1.1, None, 0.12, 24), "ArmorDark", "Turret", t=(0, 0.06, 0))
    m.part("TurretBody", prism([(-1.25, 0.1, -1.5), (1.25, 0.1, -1.5), (1.15, 0.1, 1.4), (-1.15, 0.1, 1.4),
                                (-1.0, 0.85, -1.3), (1.0, 0.85, -1.3), (0.8, 0.85, 0.9), (-0.8, 0.85, 0.9)]), "Armor", "Turret")
    m.part("TurretCamo", merge(xf(box(0.7, 0.02, 0.8), t=(-0.3, 0.86, -0.6), r=(0, 25, 0)),
                               xf(box(0.5, 0.02, 0.6), t=(0.45, 0.86, 0.3), r=(0, -40, 0))), "Camo", "Turret")
    m.part("Mantlet", tbox(1.0, 0.5, 0.8, 0.4, 0.6), "ArmorDark", "Turret", t=(0, 0.45, 1.45))
    m.part("Basket", merge(xf(box(2.0, 0.05, 0.6), t=(0, 0, 0)), xf(box(2.0, 0.35, 0.05), t=(0, 0.17, -0.3)),
                           xf(box(0.05, 0.35, 0.6), t=(1.0, 0.17, 0)), xf(box(0.05, 0.35, 0.6), t=(-1.0, 0.17, 0))),
           "Steel", "Turret", t=(0, 0.4, -1.75))
    m.part("Crates", merge(xf(box(0.5, 0.3, 0.45), t=(-0.5, 0, 0)), xf(cyl(0.18, None, 0.6, 12, "x"), t=(0.4, 0.0, 0))),
           "Camo", "Turret", t=(0, 0.6, -1.75))
    m.part("Antenna", merge(cyl(0.02, None, 2.2, 6), xf(sphere(0.04, seg=8, rings=5), t=(0, 1.1, 0))), "Steel", "Turret", t=(-0.8, 1.95, -1.1))
    m.part("Cupola", cyl(0.38, 0.42, 0.22, 18), "ArmorDark", "Turret", t=(0.45, 0.96, -0.35))
    m.node("Hatch", "Turret", t=(0.45, 1.08, -0.7))
    m.part("HatchLid", cyl(0.34, None, 0.06, 18), "Armor", "Hatch", t=(0, 0.0, 0.35))
    m.part("HatchHandle", box(0.2, 0.04, 0.04), "Steel", "Hatch", t=(0, 0.05, 0.5))
    m.node("MG", "Turret", t=(-0.35, 1.0, -0.2))
    m.part("MGMount", cyl(0.05, None, 0.25, 8), "Steel", "MG", t=(0, 0.0, 0))
    m.part("MGBody", merge(xf(box(0.12, 0.14, 0.45), t=(0, 0.16, 0.05)), xf(cyl(0.025, None, 0.6, 8, "z"), t=(0, 0.16, 0.55)),
                           xf(box(0.08, 0.14, 0.12), t=(0.1, 0.1, 0.0))), "Track", "MG")
    m.part("Scope", merge(box(0.22, 0.2, 0.3), xf(box(0.18, 0.08, 0.02), t=(0, 0.02, 0.16))), "ArmorDark", "Turret", t=(-0.6, 0.95, 0.5))
    # ствол
    m.node("GunPivot", "Turret", t=(0, 0.45, 1.6))
    m.node("Barrel", "GunPivot")
    m.part("BarrelSleeve", cyl(0.2, 0.22, 0.9, 16, "z"), "ArmorDark", "Barrel", t=(0, 0, 0.3))
    m.part("BarrelTube", cyl(0.11, 0.13, 3.4, 16, "z"), "Armor", "Barrel", t=(0, 0, 2.3))
    m.part("Evacuator", cyl(0.17, None, 0.45, 16, "z"), "Armor", "Barrel", t=(0, 0, 2.0))
    m.part("MuzzleBrake", merge(cyl(0.18, None, 0.4, 14, "z"), xf(box(0.42, 0.14, 0.16), t=(0, 0, 0.05))), "Steel", "Barrel", t=(0, 0, 4.05))
    m.part("Flash", merge(cyl(0.0, 0.45, 1.3, 10, "z"), xf(cyl(0.0, 0.3, 0.9, 8, "x"), t=(0, 0, -0.3)), xf(cyl(0.0, 0.3, 0.9, 8, "y"), t=(0, 0, -0.3))),
           "Flash", "Barrel", t=(0, 0, 4.9), s=(0.001,) * 3, obj=False)

    wheels = [n["name"] for n in m.nodes if n["name"].startswith(("Wheel_", "Sprocket_", "Idler_"))]
    t = [0, 0.25, 0.5, 0.75, 1.0]
    m.anim("Drive", [(w, "rotation", [(ti, (a, 0, 0)) for ti, a in zip(t, (0, 90, 180, 270, 360))]) for w in wheels] + [
        ("Hull", "translation", [(0, (0, 0, 0)), (0.25, (0, 0.025, 0)), (0.5, (0, 0, 0)), (0.75, (0, 0.025, 0)), (1, (0, 0, 0))]),
        ("Hull", "rotation", [(0, (0, 0, 0)), (0.5, (0.6, 0, 0)), (1, (0, 0, 0))]),
        ("Antenna", "rotation", [(0, (0, 0, 0)), (0.25, (-6, 0, 0)), (0.5, (2, 0, 0)), (0.75, (-6, 0, 0)), (1, (0, 0, 0))]),
    ])
    m.anim("TurretRotate", [
        ("Turret", "rotation", [(i, (0, a, 0)) for i, a in zip((0, 2, 4, 6, 8), (0, 90, 180, 270, 360))]),
        ("GunPivot", "rotation", [(0, (0, 0, 0)), (2, (-8, 0, 0)), (4, (0, 0, 0)), (6, (-8, 0, 0)), (8, (0, 0, 0))]),
    ])
    m.anim("Fire", [
        ("GunPivot", "rotation", [(0, (0, 0, 0)), (0.6, (-6, 0, 0)), (0.7, (-9, 0, 0)), (1.4, (-6, 0, 0)), (2.2, (0, 0, 0))]),
        ("Barrel", "translation", [(0, (0, 0, 0)), (0.6, (0, 0, 0)), (0.65, (0, 0, -0.5)), (1.3, (0, 0, 0)), (2.2, (0, 0, 0))]),
        ("Flash", "scale", [(0, (0.001,) * 3), (0.6, (0.001,) * 3), (0.62, (1, 1, 1)), (0.72, (1.4, 1.4, 1.4)),
                            (0.8, (0.001,) * 3), (2.2, (0.001,) * 3)]),
        ("Hull", "rotation", [(0, (0, 0, 0)), (0.6, (0, 0, 0)), (0.7, (-2.5, 0, 0)), (1.0, (0.8, 0, 0)), (1.3, (0, 0, 0)), (2.2, (0, 0, 0))]),
    ])
    m.anim("HatchOpen", [("Hatch", "rotation", [(0, (0, 0, 0)), (0.8, (-115, 0, 0)), (2.0, (-115, 0, 0)), (2.8, (0, 0, 0))])])
    return m


def _chest(name, wood, trim, glow, size=1.0):
    m = Model(name)
    m.mat("Wood", wood, rough=0.75)
    m.mat("WoodDark", "#4a2d16", rough=0.85)
    m.mat("Trim", trim, metal=0.9, rough=0.3)
    m.mat("Glow", glow, emissive=glow)
    m.mat("Keyhole", "#111111")
    w, h, d = 0.9 * size, 0.5 * size, 0.55 * size
    m.node("Chest")
    m.part("Body", box(w, h, d), "Wood", "Chest", t=(0, h / 2, 0))
    m.part("Planks", merge(*[xf(box(w + 0.004, 0.012, d + 0.004), t=(0, y * h, 0)) for y in (0.33, 0.66)]), "WoodDark", "Chest")
    m.part("Bands", merge(*[xf(box(0.06 * size, h + 0.01, d + 0.02), t=(x * w, h / 2, 0)) for x in (-0.33, 0.33)],
                          xf(box(w + 0.02, 0.05 * size, d + 0.02), t=(0, 0.025 * size, 0)),
                          *[xf(box(0.05 * size, h + 0.012, 0.05 * size), t=(sx * w / 2, h / 2, sz * d / 2)) for sx in (-1, 1) for sz in (-1, 1)]),
           "Trim", "Chest")
    m.part("Treasure", merge(xf(box(w - 0.06, 0.02, d - 0.06), t=(0, 0, 0)),
                             *[xf(cyl(0.05 * size, None, 0.015, 12), t=(math.cos(i * 2.4) * 0.25 * w, 0.02 + 0.01 * (i % 3), math.sin(i * 2.4) * 0.25 * d))
                               for i in range(9)]), "Glow", "Chest", t=(0, h - 0.02, 0))
    m.node("Lid", "Chest", t=(0, h, -d / 2))
    lid_h = 0.12 * size
    m.part("LidBase", box(w, lid_h, d), "Wood", "Lid", t=(0, lid_h / 2, d / 2))
    m.part("LidTop", xf(cyl(d / 2, None, w, 16, "x"), s=(1, 0.42, 1)), "Wood", "Lid", t=(0, lid_h, d / 2))
    m.part("LidBands", merge(*[xf(cyl(d / 2 + 0.012, None, 0.06 * size, 16, "x"), t=(x * w, 0, 0), s=(1, 0.45, 1)) for x in (-0.33, 0.33)],
                             *[xf(box(0.06 * size, lid_h, d + 0.02), t=(x * w, -lid_h / 2, 0)) for x in (-0.33, 0.33)]),
           "Trim", "Lid", t=(0, lid_h, d / 2))
    m.part("Lock", box(0.13 * size, 0.16 * size, 0.04), "Trim", "Lid", t=(0, 0.0, d + 0.02))
    m.part("KeyholeMesh", box(0.025 * size, 0.05 * size, 0.01), "Keyhole", "Lid", t=(0, -0.01, d + 0.042))
    # искры вокруг сундука
    m.node("Sparkles", "Chest", t=(0, h * 0.9, 0))
    for i in range(6):
        a = i / 6 * 2 * math.pi
        m.part("Sparkle%d" % i, merge(box(0.03, 0.08, 0.03), box(0.08, 0.03, 0.03)), "Glow", "Sparkles",
               t=(math.cos(a) * 0.65 * size, 0.15 * math.sin(3 * a), math.sin(a) * 0.5 * size), r=(0, 0, 45), obj=False)
    m.anim("Idle", [
        ("Sparkles", "rotation", [(i, (0, a, 0)) for i, a in zip((0, 1, 2, 3, 4), (0, 90, 180, 270, 360))]),
        ("Sparkles", "translation", [(0, (0, 0, 0)), (1, (0, 0.06, 0)), (2, (0, 0, 0)), (3, (0, 0.06, 0)), (4, (0, 0, 0))]),
        ("Lid", "rotation", [(0, (0, 0, 0)), (1.8, (0, 0, 0)), (1.9, (-4, 0, 0)), (2.0, (0, 0, 0)), (2.1, (-3, 0, 0)), (2.2, (0, 0, 0)), (4, (0, 0, 0))]),
        ("Chest", "scale", [(0, (1, 1, 1)), (1.9, (1, 1, 1)), (2.0, (1.02, 0.98, 1.02)), (2.15, (1, 1, 1)), (4, (1, 1, 1))]),
    ])
    m.anim("Open", [
        ("Lid", "rotation", [(0, (0, 0, 0)), (0.15, (-6, 0, 0)), (0.3, (0, 0, 0)), (0.7, (-115, 0, 0)), (0.85, (-100, 0, 0)), (1.6, (-105, 0, 0))]),
        ("Chest", "scale", [(0, (1, 1, 1)), (0.25, (1.05, 0.93, 1.05)), (0.55, (0.97, 1.05, 0.97)), (0.8, (1, 1, 1)), (1.6, (1, 1, 1))]),
        ("Sparkles", "scale", [(0, (1, 1, 1)), (0.6, (1.6, 2.5, 1.6)), (1.6, (0.001,) * 3)]),
    ])
    return m


def chest():
    return _chest("Chest", "#9a5b2c", "#e8b923", "#ffe066")


def rare_chest():
    return _chest("ChestRare", "#2e3f8f", "#cfd6e6", "#7ad7ff", 1.1)


def ammo_box():
    m = Model("AmmoBox")
    m.mat("Green", "#4b5a2e", metal=0.4, rough=0.6)
    m.mat("Metal", "#9aa1ab", metal=0.85, rough=0.3)
    m.mat("Label", "#f2c230")
    m.mat("Bullet", "#d4a43a", metal=0.9, rough=0.25)
    m.node("Box")
    m.part("Body", box(0.7, 0.4, 0.4), "Green", "Box", t=(0, 0.2, 0))
    m.part("Ribs", merge(*[xf(box(0.71, 0.03, 0.41), t=(0, y, 0)) for y in (0.08, 0.32)]), "Green", "Box")
    m.part("Label", box(0.3, 0.12, 0.01), "Label", "Box", t=(0, 0.22, 0.205))
    m.part("Bullets", merge(*[xf(merge(cyl(0.02, None, 0.08, 8), xf(cyl(0.0, 0.02, 0.04, 8), t=(0, 0.06, 0))), t=(-0.25 + i * 0.07, 0, 0))
                              for i in range(8)]), "Bullet", "Box", t=(0, 0.42, 0.05))
    m.node("Lid", "Box", t=(0, 0.4, -0.2))
    m.part("LidPlate", box(0.72, 0.04, 0.42), "Green", "Lid", t=(0, 0.02, 0.2))
    m.part("Handle", merge(box(0.22, 0.03, 0.03), xf(box(0.03, 0.05, 0.03), t=(0.1, -0.03, 0)), xf(box(0.03, 0.05, 0.03), t=(-0.1, -0.03, 0))),
           "Metal", "Lid", t=(0, 0.08, 0.2))
    m.part("Latch", box(0.08, 0.1, 0.03), "Metal", "Lid", t=(0, -0.03, 0.42))
    m.anim("Open", [("Lid", "rotation", [(0, (0, 0, 0)), (0.5, (-110, 0, 0)), (1.5, (-110, 0, 0)), (2.0, (0, 0, 0))])])
    return m


def supply_drop():
    m = Model("SupplyDrop")
    m.mat("Crate", "#2f6fec", metal=0.3, rough=0.5)
    m.mat("Frame", "#e9eef5", metal=0.6, rough=0.4)
    m.mat("Canopy", "#ff5a36", rough=0.8, double=True)
    m.mat("Rope", "#d9cfb5")
    m.mat("Beacon", "#7aff8a", emissive="#3aff5a")
    m.node("Drop")
    m.node("Crate", "Drop")
    m.part("CrateBody", box(1.0, 1.0, 1.0), "Crate", "Crate", t=(0, 0.5, 0))
    edges = []
    for a in (-0.5, 0.5):
        for b in (-0.5, 0.5):
            edges += [xf(box(1.06, 0.08, 0.08), t=(0, 0.5 + a, b)), xf(box(0.08, 1.06, 0.08), t=(a, 0.5, b)),
                      xf(box(0.08, 0.08, 1.06), t=(a, 0.5 + b, 0))]
    m.part("CrateFrame", merge(*edges), "Frame", "Crate")
    m.part("CrateX", merge(xf(box(0.06, 1.3, 0.04), t=(0, 0.5, 0.52), r=(0, 0, 45)), xf(box(0.06, 1.3, 0.04), t=(0, 0.5, 0.52), r=(0, 0, -45)),
                           xf(box(0.06, 1.3, 0.04), t=(0, 0.5, -0.52), r=(0, 0, 45)), xf(box(0.06, 1.3, 0.04), t=(0, 0.5, -0.52), r=(0, 0, -45))),
           "Frame", "Crate")
    m.part("Beacon", merge(cyl(0.08, None, 0.12, 12), xf(sphere(0.08, seg=12, rings=6, phi_max=1.6), t=(0, 0.06, 0))), "Beacon", "Crate", t=(0, 1.08, 0))
    m.node("Chute", "Drop", t=(0, 1.0, 0))
    m.part("Canopy", sphere(1.6, 0.9, 1.6, 16, 6, 1.3), "Canopy", "Chute", t=(0, 2.4, 0))
    ropes = []
    for i in range(8):
        a = i / 8 * 2 * math.pi
        x, z = math.cos(a) * 1.5, math.sin(a) * 1.5
        L = math.sqrt(x * x + 2.5 ** 2 + z * z)
        tilt = math.degrees(math.atan2(math.sqrt(x * x + z * z), 2.5))
        yaw = math.degrees(math.atan2(x, z))
        ropes.append(xf(xf(cyl(0.012, None, L, 4), t=(0, L / 2, 0), r=(tilt, 0, 0)), r=(0, yaw, 0)))
    m.part("Ropes", merge(*ropes), "Rope", "Chute", t=(0, 0.1, 0))
    m.anim("Descend", [
        ("Drop", "translation", [(0, (0, 6, 0)), (6, (0, 0, 0)), (6.5, (0, 0, 0))]),
        ("Drop", "rotation", [(0, (0, 0, 6)), (1.5, (4, 30, -5)), (3, (-4, 60, 5)), (4.5, (3, 90, -4)), (6, (0, 120, 0)), (6.5, (0, 120, 0))]),
        ("Chute", "scale", [(0, (1, 1, 1)), (5.9, (1, 1, 1)), (6.3, (1.2, 0.2, 1.2)), (6.5, (0.001,) * 3)]),
    ])
    m.anim("Beacon", [("Beacon", "scale", [(0, (1, 1, 1)), (0.5, (1.4, 1.4, 1.4)), (1, (1, 1, 1))])])
    return m


def medkit():
    m = Model("Medkit")
    m.mat("White", "#f4f4f4", rough=0.4)
    m.mat("Red", "#e23131", rough=0.5)
    m.mat("Strap", "#3b3b3b")
    m.node("Item")
    m.part("Case", box(0.5, 0.32, 0.18), "White", "Item", t=(0, 0.16, 0))
    m.part("Rim", box(0.52, 0.04, 0.2), "Red", "Item", t=(0, 0.24, 0))
    m.part("Cross", merge(box(0.16, 0.05, 0.02), box(0.05, 0.16, 0.02), xf(box(0.16, 0.05, 0.02), t=(0, 0, -0.2)), xf(box(0.05, 0.16, 0.02), t=(0, 0, -0.2))),
           "Red", "Item", t=(0, 0.13, 0.1))
    m.part("Handle", merge(box(0.18, 0.03, 0.04), xf(box(0.03, 0.05, 0.04), t=(0.08, -0.03, 0)), xf(box(0.03, 0.05, 0.04), t=(-0.08, -0.03, 0))),
           "Strap", "Item", t=(0, 0.37, 0))
    _float(m)
    return m


def bandage():
    m = Model("Bandage")
    m.mat("Cloth", "#f2ece0", rough=0.9)
    m.mat("Red", "#e23131")
    m.node("Item")
    m.part("Roll", cyl(0.07, None, 0.1, 18, "x"), "Cloth", "Item", t=(0, 0.07, 0))
    m.part("Core", cyl(0.025, None, 0.102, 12, "x"), "Red", "Item", t=(0, 0.07, 0))
    m.part("Tail", box(0.09, 0.005, 0.14), "Cloth", "Item", t=(0, 0.003, 0.07))
    _float(m)
    return m


def shield_potion():
    m = Model("ShieldPotion")
    m.mat("Glass", "#cdeeff", metal=0.1, rough=0.05, alpha=0.35)
    m.mat("Liquid", "#2e8bff", rough=0.2, emissive="#0b4dcc")
    m.mat("Cap", "#d8dde5", metal=0.85, rough=0.3)
    m.mat("Label", "#ffffff", emissive="#404040")
    m.node("Item")
    m.part("Liquid", merge(sphere(0.085, 0.08, 0.085, 16, 10), xf(cyl(0.03, None, 0.05, 12), t=(0, 0.08, 0))), "Liquid", "Item", t=(0, 0.1, 0))
    m.part("Bottle", merge(sphere(0.1, 0.095, 0.1, 18, 12), xf(cyl(0.035, 0.04, 0.12, 14), t=(0, 0.12, 0))), "Glass", "Item", t=(0, 0.1, 0))
    m.part("Cap", cyl(0.045, None, 0.04, 14), "Cap", "Item", t=(0, 0.29, 0))
    m.part("Label", merge(box(0.025, 0.06, 0.006), box(0.06, 0.025, 0.006)), "Label", "Item", t=(0, 0.1, 0.098))
    _float(m)
    return m


def _float(m):
    m.anim("Float", [
        ("Item", "translation", [(0, (0, 0.15, 0)), (1, (0, 0.25, 0)), (2, (0, 0.15, 0))]),
        ("Item", "rotation", [(i * 0.5, (0, a, 0)) for i, a in enumerate((0, 90, 180, 270, 360))]),
    ])


# -------------------------------------------------------------- постройки

def _planks(m, name, w, h, horizontal=True):
    planks = []
    n = 5
    for i in range(n):
        if horizontal:
            planks.append(xf(box(w, h / n - 0.02, 0.06), t=(0, -h / 2 + (i + 0.5) * h / n, 0)))
        else:
            planks.append(xf(box(w / n - 0.02, h, 0.06), t=(-w / 2 + (i + 0.5) * w / n, 0, 0)))
    return merge(*planks)


def build_wall():
    m = Model("BuildWall")
    m.mat("Wood", "#b07a43", rough=0.8)
    m.mat("Beam", "#6e4422", rough=0.85)
    m.node("Piece")
    m.part("Planks", _planks(m, "w", 3.9, 3.9), "Wood", "Piece", t=(0, 2.0, 0))
    m.part("Frame", merge(xf(box(4.0, 0.15, 0.12), t=(0, 0.075, 0)), xf(box(4.0, 0.15, 0.12), t=(0, 3.925, 0)),
                          xf(box(0.15, 4.0, 0.12), t=(1.925, 2.0, 0)), xf(box(0.15, 4.0, 0.12), t=(-1.925, 2.0, 0)),
                          xf(box(0.12, 5.4, 0.1), t=(0, 2.0, 0.03), r=(0, 0, 45))), "Beam", "Piece")
    _build_anim(m)
    return m


def build_floor():
    m = Model("BuildFloor")
    m.mat("Wood", "#b07a43", rough=0.8)
    m.mat("Beam", "#6e4422", rough=0.85)
    m.node("Piece")
    m.part("Planks", xf(_planks(m, "f", 3.9, 3.9, False), r=(-90, 0, 0)), "Wood", "Piece", t=(0, 0.03, 0))
    m.part("Frame", merge(xf(box(4.0, 0.12, 0.15), t=(0, 0, 1.925)), xf(box(4.0, 0.12, 0.15), t=(0, 0, -1.925)),
                          xf(box(0.15, 0.12, 4.0), t=(1.925, 0, 0)), xf(box(0.15, 0.12, 4.0), t=(-1.925, 0, 0))), "Beam", "Piece", t=(0, 0.05, 0))
    _build_anim(m)
    return m


def build_ramp():
    m = Model("BuildRamp")
    m.mat("Wood", "#b07a43", rough=0.8)
    m.mat("Beam", "#6e4422", rough=0.85)
    m.node("Piece")
    ang = math.degrees(math.atan2(4.0, 4.0))
    m.part("Planks", xf(_planks(m, "r", 3.9, 5.5, False), r=(-90 + ang, 0, 0)), "Wood", "Piece", t=(0, 2.0, 0))
    m.part("Steps", merge(*[xf(box(3.9, 0.06, 0.1), t=(0, -2.0 + i * 0.5, 2.0 - i * 0.5)) for i in range(1, 8)]), "Beam", "Piece", t=(0, 2.06, 0))
    m.part("Supports", merge(xf(box(0.15, 4.0, 0.15), t=(1.9, 2.0, -1.9)), xf(box(0.15, 4.0, 0.15), t=(-1.9, 2.0, -1.9)),
                             xf(box(0.15, 0.15, 4.0), t=(1.9, 0.075, 0)), xf(box(0.15, 0.15, 4.0), t=(-1.9, 0.075, 0))), "Beam", "Piece")
    _build_anim(m)
    return m


def _build_anim(m):
    m.anim("Build", [("Piece", "scale", [(0, (0.001, 0.001, 0.001)), (0.25, (1.05, 1.05, 1.05)), (0.4, (1, 1, 1)), (1.0, (1, 1, 1))])])


# -------------------------------------------------------------- природа

def pine_tree():
    m = Model("PineTree")
    m.mat("Bark", "#6b4426", rough=0.9)
    m.mat("Needles", "#2f7d3a", rough=0.8)
    m.mat("NeedlesLight", "#3f9a48", rough=0.8)
    m.node("Tree")
    m.part("Trunk", cyl(0.22, 0.32, 2.4, 10), "Bark", "Tree", t=(0, 1.2, 0))
    m.node("Crown", "Tree", t=(0, 1.6, 0))
    for i, (r, y, mt) in enumerate(((2.0, 0.8, "Needles"), (1.6, 2.1, "NeedlesLight"), (1.15, 3.3, "Needles"), (0.7, 4.3, "NeedlesLight"))):
        m.part("Layer%d" % i, cyl(0.0, r, 1.8, 9), mt, "Crown", t=(0, y, 0), r=(0, i * 20, 0))
    m.anim("Sway", [("Crown", "rotation", [(0, (0, 0, 0)), (1.5, (2, 0, 2.5)), (3, (0, 0, 0)), (4.5, (-2, 0, -1.5)), (6, (0, 0, 0))])])
    return m


def oak_tree():
    m = Model("OakTree")
    m.mat("Bark", "#7a5230", rough=0.9)
    m.mat("Leaves", "#4e9a3a", rough=0.8)
    m.mat("LeavesDark", "#3a7d2c", rough=0.8)
    m.node("Tree")
    m.part("Trunk", merge(cyl(0.3, 0.42, 2.6, 10), xf(cyl(0.12, 0.18, 1.4, 8), t=(0.5, 1.6, 0), r=(0, 0, -40)),
                          xf(cyl(0.12, 0.18, 1.2, 8), t=(-0.45, 1.5, 0.2), r=(15, 0, 40))), "Bark", "Tree", t=(0, 1.3, 0))
    m.node("Crown", "Tree", t=(0, 2.6, 0))
    for i, (x, y, z, r, mt) in enumerate(((0, 1.4, 0, 1.6, "Leaves"), (1.2, 0.9, 0.3, 1.1, "LeavesDark"), (-1.1, 1.0, -0.2, 1.2, "Leaves"),
                                         (0.2, 1.1, 1.0, 1.0, "LeavesDark"), (-0.3, 2.2, -0.3, 1.0, "LeavesDark"))):
        m.part("Blob%d" % i, sphere(r, r * 0.85, r, 10, 7), mt, "Crown", t=(x, y, z))
    m.anim("Sway", [("Crown", "rotation", [(0, (0, 0, 0)), (2, (1.5, 0, 2)), (4, (0, 0, 0)), (6, (-1.5, 0, -2)), (8, (0, 0, 0))])])
    return m


def rock():
    m = Model("Rock")
    m.mat("Stone", "#8a8d91", rough=0.95)
    m.mat("Moss", "#5f7d3a", rough=0.95)
    P, N, I = sphere(1.2, 0.8, 1.0, 9, 6)
    jag = [(p[0] * (1 + 0.18 * math.sin(i * 2.7)), p[1] * (1 + 0.15 * math.cos(i * 1.9)), p[2] * (1 + 0.15 * math.sin(i * 3.3)))
           for i, p in enumerate(P)]
    # сварим шов сферы, чтобы шум не рвал поверхность
    seam = {}
    for i, p in enumerate(P):
        seam.setdefault((round(p[0], 4), round(p[1], 4), round(p[2], 4)), jag[i])
    jag = [seam[(round(p[0], 4), round(p[1], 4), round(p[2], 4))] for p in P]
    tris = [(jag[I[k]], jag[I[k + 1]], jag[I[k + 2]]) for k in range(0, len(I), 3)]
    flatP, flatN, flatI = [], [], []
    for a, b, c in tris:
        u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        v = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        ln = math.sqrt(sum(x * x for x in n))
        if ln < 1e-9:
            continue
        n = tuple(x / ln for x in n)
        if sum(n[i] * (a[i] + b[i] + c[i]) for i in range(3)) < 0:
            b, c, n = c, b, tuple(-x for x in n)
        base = len(flatP)
        flatP += [a, b, c]
        flatN += [n, n, n]
        flatI += [base, base + 1, base + 2]
    m.node("RockRoot")
    m.part("Stone", (flatP, flatN, flatI), "Stone", "RockRoot", t=(0, 0.45, 0))
    m.part("MossCap", sphere(0.8, 0.25, 0.7, 9, 4, 1.4), "Moss", "RockRoot", t=(-0.1, 1.05, 0.05))
    return m


def bush():
    m = Model("Bush")
    m.mat("Leaves", "#4f9e3c", rough=0.85)
    m.mat("LeavesDark", "#3b7f2d", rough=0.85)
    m.mat("Berry", "#e2334a", rough=0.4)
    m.node("Bush")
    m.part("Blobs", merge(xf(sphere(0.6, 0.5, 0.6, 10, 7), t=(0, 0.45, 0)), xf(sphere(0.45, 0.4, 0.45, 10, 6), t=(0.5, 0.35, 0.1))),
           "Leaves", "Bush")
    m.part("BlobsDark", merge(xf(sphere(0.45, 0.4, 0.45, 10, 6), t=(-0.5, 0.35, -0.1)), xf(sphere(0.35, 0.3, 0.35, 10, 6), t=(0.1, 0.3, 0.5))),
           "LeavesDark", "Bush")
    m.part("Berries", merge(*[xf(sphere(0.05, seg=8, rings=5), t=(math.cos(i * 1.7) * 0.55, 0.5 + 0.2 * math.sin(i), math.sin(i * 1.7) * 0.5))
                              for i in range(10)]), "Berry", "Bush")
    m.anim("Rustle", [("Bush", "scale", [(0, (1, 1, 1)), (0.15, (1.06, 0.94, 1.06)), (0.3, (0.97, 1.04, 0.97)), (0.5, (1, 1, 1)), (2, (1, 1, 1))])])
    return m


VEHICLES = [tank]
PROPS = [chest, rare_chest, ammo_box, supply_drop, medkit, bandage, shield_potion,
         build_wall, build_floor, build_ramp, pine_tree, oak_tree, rock, bush]
