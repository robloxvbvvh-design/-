"""Персонажи: общий «скелет» из узлов-шарниров и общий набор анимаций.

Персонаж смотрит в +Z, левая рука на +X, ноги стоят на y = 0, рост ~1.85 м.
Узлы-шарниры (их же вращают анимации):
  Root > Hips > Spine > Neck, Shoulder_L/R > Elbow_L/R > Hand_L/R
              > Hip_L/R > Knee_L/R
Точки крепления: Hand_R (оружие), Spine/Back (рюкзак), Neck (шлем).
"""
from gltf_builder import Model, box, tbox, cyl, sphere, merge, xf


def skeleton(m, c):
    """c — словарь материалов: skin, shirt, pants, boots, gloves, sleeve."""
    m.node("Root")
    m.node("Hips", "Root", t=(0, 0.95, 0))
    m.part("Pelvis", box(0.36, 0.17, 0.22), c["pants"], "Hips", t=(0, 0.0, 0))
    m.part("Belt", box(0.38, 0.05, 0.24), c.get("belt", c["boots"]), "Hips", t=(0, 0.07, 0))
    m.node("Spine", "Hips", t=(0, 0.08, 0))
    m.part("Torso", tbox(0.38, 0.22, 0.44, 0.25, 0.5), c["shirt"], "Spine", t=(0, 0.27, 0))
    m.node("Neck", "Spine", t=(0, 0.53, 0))
    m.part("NeckMesh", cyl(0.06, None, 0.08, 10), c["skin"], "Neck", t=(0, 0.02, 0))
    for side, sx in (("L", 1), ("R", -1)):
        m.node("Shoulder_" + side, "Spine", t=(0.27 * sx, 0.47, 0))
        m.part("UpperArm_" + side, box(0.13, 0.32, 0.13), c.get("sleeve", c["shirt"]), "Shoulder_" + side, t=(0.01 * sx, -0.14, 0))
        m.node("Elbow_" + side, "Shoulder_" + side, t=(0.01 * sx, -0.3, 0))
        m.part("Forearm_" + side, box(0.115, 0.28, 0.115), c.get("forearm", c["skin"]), "Elbow_" + side, t=(0, -0.13, 0))
        m.node("Hand_" + side, "Elbow_" + side, t=(0, -0.29, 0))
        m.part("HandMesh_" + side, box(0.11, 0.12, 0.09), c["gloves"], "Hand_" + side, t=(0, -0.04, 0.0))
        m.node("Hip_" + side, "Hips", t=(0.1 * sx, -0.04, 0))
        m.part("Thigh_" + side, box(0.16, 0.44, 0.17), c["pants"], "Hip_" + side, t=(0, -0.2, 0))
        m.node("Knee_" + side, "Hip_" + side, t=(0, -0.43, 0))
        m.part("Shin_" + side, box(0.145, 0.38, 0.155), c.get("shin", c["pants"]), "Knee_" + side, t=(0, -0.2, 0))
        m.part("Foot_" + side, box(0.16, 0.09, 0.27), c["boots"], "Knee_" + side, t=(0, -0.435, 0.04))


def animations(m):
    L, R = "_L", "_R"
    sh, el, hp, kn = "Shoulder", "Elbow", "Hip", "Knee"

    def cyc(times, vals):
        return list(zip(times, vals))

    # Idle — дыхание и лёгкое покачивание
    t = [0, 1, 2]
    m.anim("Idle", [
        ("Spine", "rotation", cyc(t, [(0, 0, 0), (3, 0, 0), (0, 0, 0)])),
        ("Neck", "rotation", cyc([0, 1, 2], [(0, 0, 0), (-3, 4, 0), (0, 0, 0)])),
        (sh + L, "rotation", cyc(t, [(0, 0, 6), (-3, 0, 9), (0, 0, 6)])),
        (sh + R, "rotation", cyc(t, [(0, 0, -6), (-3, 0, -9), (0, 0, -6)])),
        (el + L, "rotation", cyc(t, [(-10, 0, 0), (-14, 0, 0), (-10, 0, 0)])),
        (el + R, "rotation", cyc(t, [(-10, 0, 0), (-14, 0, 0), (-10, 0, 0)])),
        ("Hips", "translation", cyc(t, [(0, 0, 0), (0, -0.01, 0), (0, 0, 0)])),
    ])

    def gait(name, dur, leg, knee, arm, elbow, bob, lean):
        t = [0, dur / 4, dur / 2, dur * 3 / 4, dur]
        a = [-leg, 0, leg, 0, -leg]
        b = [leg, 0, -leg, 0, leg]
        m.anim(name, [
            (hp + L, "rotation", [(ti, (v, 0, 0)) for ti, v in zip(t, a)]),
            (hp + R, "rotation", [(ti, (v, 0, 0)) for ti, v in zip(t, b)]),
            (kn + L, "rotation", cyc(t, [(knee * 0.2, 0, 0), (knee, 0, 0), (knee * 0.1, 0, 0), (knee * 0.3, 0, 0), (knee * 0.2, 0, 0)])),
            (kn + R, "rotation", cyc(t, [(knee * 0.1, 0, 0), (knee * 0.3, 0, 0), (knee * 0.2, 0, 0), (knee, 0, 0), (knee * 0.1, 0, 0)])),
            (sh + L, "rotation", [(ti, (-v * arm / leg, 0, 5)) for ti, v in zip(t, a)]),
            (sh + R, "rotation", [(ti, (-v * arm / leg, 0, -5)) for ti, v in zip(t, b)]),
            (el + L, "rotation", cyc(t, [(-elbow, 0, 0)] * 5)),
            (el + R, "rotation", cyc(t, [(-elbow, 0, 0)] * 5)),
            ("Spine", "rotation", cyc(t, [(lean, 6, 0), (lean, 0, 0), (lean, -6, 0), (lean, 0, 0), (lean, 6, 0)])),
            ("Hips", "translation", cyc(t, [(0, 0, 0), (0, bob, 0), (0, 0, 0), (0, bob, 0), (0, 0, 0)])),
        ])

    gait("Walk", 1.0, 25, 35, 22, 15, 0.03, 3)
    gait("Run", 0.6, 45, 80, 55, 70, 0.06, 14)

    # Jump — присед, толчок, полёт, приземление
    t = [0, 0.15, 0.3, 0.6, 0.85, 1.0, 1.2]
    m.anim("Jump", [
        ("Root", "translation", cyc(t, [(0, 0, 0), (0, 0, 0), (0, 0.5, 0), (0, 0.9, 0), (0, 0.3, 0), (0, 0, 0), (0, 0, 0)])),
        ("Hips", "translation", cyc(t, [(0, 0, 0), (0, -0.15, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, -0.12, 0), (0, 0, 0)])),
        (hp + L, "rotation", cyc(t, [(0, 0, 0), (-45, 0, 0), (5, 0, 0), (-50, 0, 0), (-20, 0, 0), (-40, 0, 0), (0, 0, 0)])),
        (hp + R, "rotation", cyc(t, [(0, 0, 0), (-45, 0, 0), (5, 0, 0), (-35, 0, 0), (-15, 0, 0), (-40, 0, 0), (0, 0, 0)])),
        (kn + L, "rotation", cyc(t, [(0, 0, 0), (80, 0, 0), (5, 0, 0), (90, 0, 0), (20, 0, 0), (75, 0, 0), (0, 0, 0)])),
        (kn + R, "rotation", cyc(t, [(0, 0, 0), (80, 0, 0), (5, 0, 0), (60, 0, 0), (20, 0, 0), (75, 0, 0), (0, 0, 0)])),
        (sh + L, "rotation", cyc(t, [(0, 0, 5), (30, 0, 10), (-150, 0, 20), (-120, 0, 40), (-40, 0, 30), (20, 0, 10), (0, 0, 5)])),
        (sh + R, "rotation", cyc(t, [(0, 0, -5), (30, 0, -10), (-150, 0, -20), (-120, 0, -40), (-40, 0, -30), (20, 0, -10), (0, 0, -5)])),
        ("Spine", "rotation", cyc(t, [(0, 0, 0), (20, 0, 0), (-8, 0, 0), (5, 0, 0), (0, 0, 0), (15, 0, 0), (0, 0, 0)])),
    ])

    # Crouch — приседание с оглядыванием
    t = [0, 0.3, 1.5, 1.8]
    m.anim("Crouch", [
        ("Hips", "translation", cyc(t, [(0, 0, 0), (0, -0.33, 0), (0, -0.33, 0), (0, 0, 0)])),
        (hp + L, "rotation", cyc(t, [(0, 0, 0), (-75, 0, 8), (-75, 0, 8), (0, 0, 0)])),
        (hp + R, "rotation", cyc(t, [(0, 0, 0), (-20, 0, -5), (-20, 0, -5), (0, 0, 0)])),
        (kn + L, "rotation", cyc(t, [(0, 0, 0), (100, 0, 0), (100, 0, 0), (0, 0, 0)])),
        (kn + R, "rotation", cyc(t, [(0, 0, 0), (110, 0, 0), (110, 0, 0), (0, 0, 0)])),
        ("Spine", "rotation", cyc(t, [(0, 0, 0), (25, 0, 0), (25, 0, 0), (0, 0, 0)])),
        ("Neck", "rotation", cyc([0, 0.3, 0.8, 1.2, 1.5, 1.8], [(0, 0, 0), (-20, 0, 0), (-20, 35, 0), (-20, -35, 0), (-20, 0, 0), (0, 0, 0)])),
    ])

    # Aim — прицеливание из винтовки (оружие крепится к Hand_R) с отдачей
    t = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    rr = [(-85, 0, 10), (-85, 0, 10), (-88, 0, 10), (-85, 0, 10), (-88, 0, 10), (-85, 0, 10), (-85, 0, 10)]
    m.anim("Aim", [
        (sh + R, "rotation", cyc(t, rr)),
        (el + R, "rotation", cyc(t, [(-30, 0, 0)] * 7)),
        (sh + L, "rotation", cyc(t, [(-80, 0, -25)] * 7)),
        (el + L, "rotation", cyc(t, [(-55, 0, 0), (-55, 0, 0), (-58, 0, 0), (-55, 0, 0), (-58, 0, 0), (-55, 0, 0), (-55, 0, 0)])),
        ("Spine", "rotation", cyc(t, [(5, -20, 0), (5, -20, 0), (2, -20, 0), (5, -20, 0), (2, -20, 0), (5, -20, 0), (5, -20, 0)])),
        ("Neck", "rotation", cyc(t, [(0, 20, 0)] * 7)),
        (hp + L, "rotation", cyc(t, [(-15, 0, 5)] * 7)),
        (hp + R, "rotation", cyc(t, [(10, 0, -5)] * 7)),
        (kn + L, "rotation", cyc(t, [(20, 0, 0)] * 7)),
    ])

    # Dance — оригинальный танец «Маятник»: качание бёдрами, руки-волны, кивки
    t = [0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]
    m.anim("Dance", [
        ("Hips", "translation", cyc(t, [(0, 0, 0), (0.06, -0.05, 0), (0, 0, 0), (-0.06, -0.05, 0), (0, 0, 0),
                                        (0.06, -0.05, 0), (0, 0, 0), (-0.06, -0.05, 0), (0, 0, 0)])),
        ("Hips", "rotation", cyc(t, [(0, 0, 0), (0, 15, 5), (0, 0, 0), (0, -15, -5), (0, 0, 0),
                                     (0, 15, 5), (0, 0, 0), (0, -15, -5), (0, 0, 0)])),
        ("Spine", "rotation", cyc(t, [(0, 0, 0), (0, -10, -8), (0, 0, 0), (0, 10, 8), (0, 0, 0),
                                      (0, -10, -8), (0, 0, 0), (0, 10, 8), (0, 0, 0)])),
        ("Neck", "rotation", cyc(t, [(0, 0, 0), (12, 0, 0), (0, 0, 0), (12, 0, 0), (0, 0, 0),
                                     (12, 0, 0), (0, 0, 0), (12, 0, 0), (0, 0, 0)])),
        (sh + L, "rotation", cyc(t, [(0, 0, 90), (0, 0, 120), (0, 0, 90), (0, 0, 60), (-160, 0, 20),
                                     (-170, 0, 10), (-160, 0, 20), (-90, 0, 40), (0, 0, 90)])),
        (sh + R, "rotation", cyc(t, [(0, 0, -60), (0, 0, -90), (0, 0, -120), (0, 0, -90), (-160, 0, -20),
                                     (-90, 0, -40), (-160, 0, -20), (-170, 0, -10), (0, 0, -60)])),
        (el + L, "rotation", cyc(t, [(0, 0, 0), (0, 0, 40), (0, 0, 0), (0, 0, -40), (-60, 0, 0),
                                     (-20, 0, 0), (-60, 0, 0), (-20, 0, 0), (0, 0, 0)])),
        (el + R, "rotation", cyc(t, [(0, 0, 40), (0, 0, 0), (0, 0, -40), (0, 0, 0), (-60, 0, 0),
                                     (-20, 0, 0), (-60, 0, 0), (-20, 0, 0), (0, 0, 40)])),
        (kn + L, "rotation", cyc(t, [(0, 0, 0), (25, 0, 0), (0, 0, 0), (5, 0, 0), (0, 0, 0),
                                     (25, 0, 0), (0, 0, 0), (5, 0, 0), (0, 0, 0)])),
        (kn + R, "rotation", cyc(t, [(0, 0, 0), (5, 0, 0), (0, 0, 0), (25, 0, 0), (0, 0, 0),
                                     (5, 0, 0), (0, 0, 0), (25, 0, 0), (0, 0, 0)])),
        (hp + L, "rotation", cyc(t, [(0, 0, 0), (-15, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
                                     (-15, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)])),
        (hp + R, "rotation", cyc(t, [(0, 0, 0), (0, 0, 0), (0, 0, 0), (-15, 0, 0), (0, 0, 0),
                                     (0, 0, 0), (0, 0, 0), (-15, 0, 0), (0, 0, 0)])),
    ])

    # Wave — помахать рукой
    t = [0, 0.3, 0.55, 0.8, 1.05, 1.3, 1.6]
    m.anim("Wave", [
        (sh + L, "rotation", cyc(t, [(0, 0, 5), (0, 0, 150), (0, 0, 150), (0, 0, 150), (0, 0, 150), (0, 0, 150), (0, 0, 5)])),
        (el + L, "rotation", cyc(t, [(0, 0, 0), (0, 0, 20), (0, 0, -30), (0, 0, 20), (0, 0, -30), (0, 0, 20), (0, 0, 0)])),
        ("Neck", "rotation", cyc(t, [(0, 0, 0), (0, 0, -8), (0, 0, -8), (0, 0, -8), (0, 0, -8), (0, 0, -8), (0, 0, 0)])),
        ("Spine", "rotation", cyc(t, [(0, 0, 0), (0, 0, -5), (0, 0, -5), (0, 0, -5), (0, 0, -5), (0, 0, -5), (0, 0, 0)])),
    ])

    # Death — падение на спину (не зацикливать)
    t = [0, 0.2, 0.6, 0.8, 1.6]
    m.anim("Death", [
        ("Root", "rotation", cyc(t, [(0, 0, 0), (-10, 0, 0), (-80, 0, 0), (-90, 0, 0), (-90, 0, 0)])),
        ("Root", "translation", cyc(t, [(0, 0, 0), (0, 0, 0), (0, 0.15, -0.3), (0, 0.18, -0.4), (0, 0.18, -0.4)])),
        (kn + L, "rotation", cyc(t, [(0, 0, 0), (40, 0, 0), (20, 0, 0), (10, 0, 0), (10, 0, 0)])),
        (kn + R, "rotation", cyc(t, [(0, 0, 0), (40, 0, 0), (40, 0, 0), (30, 0, 0), (30, 0, 0)])),
        (sh + L, "rotation", cyc(t, [(0, 0, 5), (-60, 0, 30), (-30, 0, 80), (0, 0, 85), (0, 0, 85)])),
        (sh + R, "rotation", cyc(t, [(0, 0, -5), (-60, 0, -30), (-30, 0, -80), (0, 0, -85), (0, 0, -85)])),
        ("Neck", "rotation", cyc(t, [(0, 0, 0), (20, 0, 0), (-20, 0, 0), (-5, 30, 0), (-5, 30, 0)])),
    ])


def _face(m, eye, parent="Neck", y=0.2, z=0.161, mouth=None):
    m.part("Eyes", merge(xf(box(0.05, 0.05, 0.01), t=(0.065, 0, 0)), xf(box(0.05, 0.05, 0.01), t=(-0.065, 0, 0))),
           eye, parent, t=(0, y, z))
    if mouth:
        m.part("Mouth", box(0.09, 0.02, 0.01), mouth, parent, t=(0, y - 0.1, z))


def ranger():
    """Рейнджер — солдат в шлеме, бронежилете и с рюкзаком."""
    m = Model("Ranger")
    m.mat("Skin", "#e0a878")
    m.mat("Shirt", "#5b6b3a")
    m.mat("Pants", "#3f4a2c")
    m.mat("Boots", "#2a211b", rough=0.9)
    m.mat("Gloves", "#1e1e1e")
    m.mat("Vest", "#2f3524")
    m.mat("Helmet", "#4b5732", rough=0.6)
    m.mat("Eye", "#1b1b1b")
    m.mat("Goggles", "#ff9d2e", metal=0.3, rough=0.1, emissive="#5a2a00")
    m.mat("Strap", "#8a6a3a")
    skeleton(m, {"skin": "Skin", "shirt": "Shirt", "pants": "Pants", "boots": "Boots", "gloves": "Gloves",
                 "forearm": "Shirt", "belt": "Strap"})
    m.part("Head", box(0.32, 0.32, 0.31), "Skin", "Neck", t=(0, 0.21, 0))
    _face(m, "Eye", mouth="Boots")
    m.part("Helmet", merge(sphere(0.21, 0.15, 0.2, 16, 8, 1.6), xf(cyl(0.23, None, 0.03, 16), t=(0, -0.0, 0.0))),
           "Helmet", "Neck", t=(0, 0.33, 0))
    m.part("Goggles", merge(xf(box(0.1, 0.06, 0.04), t=(0.06, 0, 0)), xf(box(0.1, 0.06, 0.04), t=(-0.06, 0, 0))),
           "Goggles", "Neck", t=(0, 0.42, 0.17), r=(-20, 0, 0))
    m.part("Vest", merge(tbox(0.42, 0.27, 0.46, 0.28, 0.36),
                         *[xf(box(0.09, 0.09, 0.05), t=(x, -0.08, 0.15)) for x in (-0.13, 0, 0.13)]),
           "Vest", "Spine", t=(0, 0.3, 0))
    m.part("Strap", box(0.06, 0.62, 0.3), "Strap", "Spine", t=(0, 0.27, 0), r=(0, 0, 35))
    m.node("Back", "Spine", t=(0, 0.3, -0.17))
    m.part("Backpack", merge(box(0.34, 0.4, 0.16), xf(cyl(0.07, None, 0.34, 12, "x"), t=(0, 0.23, -0.02)),
                             xf(box(0.24, 0.14, 0.05), t=(0, -0.08, -0.09))), "Shirt", "Back", t=(0, 0, -0.07))
    for side in ("L", "R"):
        m.part("KneePad_" + side, box(0.17, 0.12, 0.05), "Vest", "Knee_" + side, t=(0, -0.03, 0.09))
    animations(m)
    return m


def bolt_robot():
    """Болт — дружелюбный робот со светящимся визором и антенной."""
    m = Model("BoltRobot")
    m.mat("Chrome", "#c9d1db", metal=0.9, rough=0.25)
    m.mat("Plate", "#ff7a1a", metal=0.4, rough=0.4)
    m.mat("Dark", "#30343b", metal=0.7, rough=0.5)
    m.mat("Glow", "#5ff6ff", emissive="#36e7ff")
    skeleton(m, {"skin": "Dark", "shirt": "Plate", "pants": "Dark", "boots": "Plate", "gloves": "Chrome",
                 "sleeve": "Chrome", "forearm": "Chrome", "shin": "Chrome", "belt": "Chrome"})
    m.part("Head", merge(box(0.36, 0.3, 0.32), xf(box(0.3, 0.06, 0.3), t=(0, 0.17, 0))), "Chrome", "Neck", t=(0, 0.2, 0))
    m.part("Visor", box(0.3, 0.09, 0.02), "Glow", "Neck", t=(0, 0.22, 0.165))
    m.part("Ears", merge(xf(cyl(0.06, None, 0.04, 14, "x"), t=(0.2, 0, 0)), xf(cyl(0.06, None, 0.04, 14, "x"), t=(-0.2, 0, 0))),
           "Plate", "Neck", t=(0, 0.2, 0))
    m.node("Antenna", "Neck", t=(0.08, 0.4, -0.05))
    m.part("AntennaRod", cyl(0.01, None, 0.18, 6), "Dark", "Antenna", t=(0, 0.09, 0))
    m.part("AntennaTip", sphere(0.03, seg=10, rings=6), "Glow", "Antenna", t=(0, 0.2, 0))
    m.part("ChestCore", cyl(0.07, None, 0.03, 16, "z"), "Glow", "Spine", t=(0, 0.33, 0.13))
    m.part("ChestFrame", merge(box(0.3, 0.04, 0.03), xf(box(0.04, 0.24, 0.03), t=(0.13, -0.1, 0)), xf(box(0.04, 0.24, 0.03), t=(-0.13, -0.1, 0))),
           "Dark", "Spine", t=(0, 0.48, 0.125))
    m.part("ShoulderPads", merge(xf(sphere(0.1, 0.08, 0.1, 12, 6, 1.6), t=(0.28, 0, 0)), xf(sphere(0.1, 0.08, 0.1, 12, 6, 1.6), t=(-0.28, 0, 0))),
           "Plate", "Spine", t=(0, 0.48, 0))
    m.part("Jetpack", merge(xf(cyl(0.07, None, 0.32, 14), t=(0.09, 0, 0)), xf(cyl(0.07, None, 0.32, 14), t=(-0.09, 0, 0))),
           "Dark", "Spine", t=(0, 0.3, -0.2))
    m.part("JetGlow", merge(xf(cyl(0.05, 0.0, 0.08, 10), t=(0.09, 0, 0)), xf(cyl(0.05, 0.0, 0.08, 10), t=(-0.09, 0, 0))),
           "Glow", "Spine", t=(0, 0.1, -0.2))
    animations(m)
    m.anim("AntennaBlink", [("Antenna", "rotation", [(0, (0, 0, 0)), (0.5, (15, 0, 10)), (1.0, (0, 0, 0)), (1.5, (-15, 0, -10)), (2.0, (0, 0, 0))])])
    return m


def shadow_ninja():
    """Тень — ниндзя в маске с красной повязкой и катаной за спиной."""
    m = Model("ShadowNinja")
    m.mat("Cloth", "#23202b", rough=0.9)
    m.mat("ClothLight", "#3a3547", rough=0.9)
    m.mat("Skin", "#c98d63")
    m.mat("Red", "#d62839", rough=0.6)
    m.mat("Steel", "#d9dde3", metal=0.95, rough=0.15)
    m.mat("Eye", "#f2f2f2", emissive="#404040")
    m.mat("Wrap", "#bba98a", rough=0.8)
    skeleton(m, {"skin": "Cloth", "shirt": "Cloth", "pants": "ClothLight", "boots": "Cloth", "gloves": "Cloth",
                 "forearm": "Wrap", "shin": "Wrap", "belt": "Red"})
    m.part("Head", box(0.31, 0.32, 0.31), "Cloth", "Neck", t=(0, 0.21, 0))
    m.part("EyeSlit", box(0.27, 0.07, 0.01), "Skin", "Neck", t=(0, 0.24, 0.158))
    m.part("Eyes", merge(xf(box(0.06, 0.03, 0.01), t=(0.06, 0, 0)), xf(box(0.06, 0.03, 0.01), t=(-0.06, 0, 0))),
           "Eye", "Neck", t=(0, 0.24, 0.162))
    m.part("Headband", box(0.33, 0.05, 0.33), "Red", "Neck", t=(0, 0.32, 0))
    m.node("BandTails", "Neck", t=(0.05, 0.32, -0.17))
    m.part("BandTailMesh", merge(xf(box(0.04, 0.02, 0.28), t=(0.03, 0, -0.13), r=(-20, 15, 0)),
                                 xf(box(0.04, 0.02, 0.22), t=(-0.03, -0.02, -0.1), r=(-35, -10, 0))), "Red", "BandTails")
    m.part("Sash", box(0.06, 0.6, 0.3), "Red", "Spine", t=(0, 0.25, 0), r=(0, 0, -30))
    m.node("Katana", "Spine", t=(0, 0.3, -0.16), r=(0, 0, 40))
    m.part("Saya", box(0.04, 0.8, 0.025), "Cloth", "Katana", t=(0, -0.05, 0))
    m.part("Tsuba", box(0.09, 0.012, 0.06), "Steel", "Katana", t=(0, 0.36, 0))
    m.part("Tsuka", box(0.035, 0.2, 0.03), "Red", "Katana", t=(0, 0.47, 0))
    animations(m)
    m.anim("ScarfFlutter", [("BandTails", "rotation", [(0, (0, 0, 0)), (0.3, (15, 10, 0)), (0.6, (-5, -10, 0)), (0.9, (0, 0, 0))])])
    return m


def astronaut():
    """Космонавтка — скафандр с прозрачным шлемом-пузырём и ранцем."""
    m = Model("Astronaut")
    m.mat("Suit", "#f1f3f6", rough=0.6)
    m.mat("Trim", "#2f6fec", rough=0.5)
    m.mat("Skin", "#f0c4a0")
    m.mat("Hair", "#7a3d1c", rough=0.9)
    m.mat("Glass", "#bfe9ff", metal=0.1, rough=0.05, alpha=0.3)
    m.mat("Eye", "#1b1b1b")
    m.mat("Panel", "#ffcf3a", emissive="#6b4a00")
    skeleton(m, {"skin": "Skin", "shirt": "Suit", "pants": "Suit", "boots": "Trim", "gloves": "Trim",
                 "forearm": "Suit", "belt": "Trim"})
    m.part("Head", box(0.29, 0.3, 0.29), "Skin", "Neck", t=(0, 0.2, 0))
    m.part("Hair", merge(xf(box(0.31, 0.1, 0.31), t=(0, 0.13, 0)), xf(box(0.31, 0.22, 0.08), t=(0, 0.02, -0.12)),
                         xf(sphere(0.07, seg=10, rings=6), t=(0, 0.1, -0.2))), "Hair", "Neck", t=(0, 0.2, 0))
    _face(m, "Eye", y=0.2, z=0.146, mouth="Trim")
    m.part("HelmetRing", cyl(0.2, None, 0.05, 20), "Trim", "Neck", t=(0, 0.02, 0))
    m.part("HelmetBubble", sphere(0.27, seg=24, rings=14), "Glass", "Neck", t=(0, 0.22, 0))
    m.part("ChestPanel", box(0.2, 0.12, 0.03), "Panel", "Spine", t=(0, 0.33, 0.13))
    m.part("ChestStripe", box(0.46, 0.05, 0.255), "Trim", "Spine", t=(0, 0.15, 0))
    m.part("LifePack", merge(box(0.36, 0.44, 0.18), xf(cyl(0.05, None, 0.2, 10), t=(0.12, 0.3, 0)), xf(cyl(0.05, None, 0.2, 10), t=(-0.12, 0.3, 0))),
           "Suit", "Spine", t=(0, 0.28, -0.22))
    for side in ("L", "R"):
        m.part("Cuff_" + side, box(0.135, 0.05, 0.135), "Trim", "Elbow_" + side, t=(0, -0.24, 0))
    animations(m)
    return m


ALL = [ranger, bolt_robot, shadow_ninja, astronaut]
