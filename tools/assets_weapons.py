"""Оружие. Ствол смотрит в +Z, начало координат — у рукояти (точка хвата)."""
import math

from gltf_builder import Model, box, tbox, cyl, sphere, merge, xf


def _common(m, accent):
    m.mat("Metal", "#2b2f36", metal=0.8, rough=0.35)
    m.mat("MetalLight", "#6b7280", metal=0.85, rough=0.3)
    m.mat("Polymer", "#1c1d21", metal=0.0, rough=0.8)
    m.mat("Accent", accent, metal=0.3, rough=0.4)
    m.mat("Flash", "#ffd36b", emissive="#ffb020", alpha=0.85)


def _flash(m, parent, z, size=1.0):
    g = merge(cyl(0.0, 0.045 * size, 0.16 * size, 8, "z"),
              xf(cyl(0.0, 0.03 * size, 0.1 * size, 6, "x"), t=(0, 0, -0.02)),
              xf(cyl(0.0, 0.03 * size, 0.1 * size, 6, "y"), t=(0, 0, -0.02)))
    m.part("Flash", g, "Flash", parent, t=(0, 0, z), s=(0.001, 0.001, 0.001), obj=False)


def _fire(m, period, recoil=0.02, kick=3.0, extra=()):
    h = period / 2
    m.anim("Fire", [
        ("Gun", "translation", [(0, (0, 0, 0)), (h * 0.4, (0, 0, -recoil)), (period, (0, 0, 0))]),
        ("Gun", "rotation", [(0, (0, 0, 0)), (h * 0.4, (-kick, 0, 0)), (period, (0, 0, 0))]),
        ("Flash", "scale", [(0, (0.001,) * 3), (0.01, (1, 1, 1)), (h * 0.6, (1.2, 1.2, 1.2)),
                            (h, (0.001,) * 3), (period, (0.001,) * 3)]),
    ] + list(extra))


def _reload(m, mag_drop=(0, -0.25, 0), dur=1.6):
    m.anim("Reload", [
        ("Gun", "rotation", [(0, (0, 0, 0)), (0.25, (10, 0, 25)), (dur - 0.25, (10, 0, 25)), (dur, (0, 0, 0))]),
        ("Mag", "translation", [(0, (0, 0, 0)), (0.3, (0, 0, 0)), (0.55, mag_drop),
                                (0.9, mag_drop), (1.2, (0, 0, 0)), (dur, (0, 0, 0))]),
        ("Mag", "scale", [(0, (1, 1, 1)), (0.54, (1, 1, 1)), (0.56, (0.001,) * 3),
                          (0.88, (0.001,) * 3), (0.9, (1, 1, 1)), (dur, (1, 1, 1))]),
    ])


def smg_uzi():
    """Компактный пистолет-пулемёт: магазин внутри рукояти, складной приклад."""
    m = Model("SMG_Uzi")
    _common(m, "#4aa3ff")
    m.node("Gun")
    m.part("Receiver", tbox(0.062, 0.27, 0.058, 0.26, 0.085), "Metal", "Gun", t=(0, 0.055, 0.06))
    m.part("TopCover", box(0.056, 0.012, 0.22), "MetalLight", "Gun", t=(0, 0.103, 0.065))
    m.part("CockingKnob", cyl(0.009, None, 0.03, 8), "Accent", "Gun", t=(0, 0.118, 0.11))
    m.part("Barrel", cyl(0.012, None, 0.07, 12, "z"), "Metal", "Gun", t=(0, 0.06, 0.225))
    m.part("BarrelNut", cyl(0.02, None, 0.02, 12, "z"), "MetalLight", "Gun", t=(0, 0.06, 0.2))
    m.part("FrontSight", box(0.012, 0.03, 0.012), "Metal", "Gun", t=(0, 0.11, 0.18))
    m.part("RearSight", merge(xf(box(0.008, 0.025, 0.01), t=(-0.015, 0, 0)),
                              xf(box(0.008, 0.025, 0.01), t=(0.015, 0, 0))), "Metal", "Gun", t=(0, 0.11, -0.05))
    m.part("Grip", tbox(0.05, 0.065, 0.045, 0.06, 0.13), "Polymer", "Gun", t=(0, -0.045, 0.02), r=(-6, 0, 0))
    m.part("GripPanel", box(0.052, 0.07, 0.03), "Accent", "Gun", t=(0, -0.04, 0.0), r=(-6, 0, 0))
    m.part("TriggerGuard", merge(box(0.012, 0.008, 0.07), xf(box(0.012, 0.04, 0.008), t=(0, 0.02, 0.035))),
           "Metal", "Gun", t=(0, -0.012, 0.08))
    m.part("Trigger", box(0.006, 0.025, 0.006), "MetalLight", "Gun", t=(0, 0.0, 0.07), r=(15, 0, 0))
    m.part("Mag", box(0.035, 0.15, 0.045), "Metal", "Gun", t=(0, -0.13, 0.03), r=(-6, 0, 0))
    m.part("MagBase", box(0.042, 0.015, 0.055), "Polymer", "Mag", t=(0, -0.08, 0))
    stock = merge(xf(box(0.008, 0.008, 0.2), t=(-0.022, 0, 0)), xf(box(0.008, 0.008, 0.2), t=(0.022, 0, 0)),
                  xf(box(0.06, 0.05, 0.012), t=(0, -0.02, -0.1)))
    m.part("Stock", stock, "MetalLight", "Gun", t=(0, 0.035, -0.17))
    _flash(m, "Gun", 0.29, 0.8)
    _fire(m, 0.08, 0.012, 2.0)
    _reload(m, (0, -0.3, 0), 1.4)
    return m


def assault_rifle():
    m = Model("AssaultRifle")
    _common(m, "#9b5cff")
    m.mat("Lens", "#ff3b3b", emissive="#ff2020")
    m.node("Gun")
    m.part("Receiver", box(0.065, 0.09, 0.36), "Metal", "Gun", t=(0, 0.05, 0.03))
    m.part("Rail", box(0.03, 0.012, 0.34), "MetalLight", "Gun", t=(0, 0.101, 0.06))
    m.part("Handguard", tbox(0.07, 0.24, 0.06, 0.24, 0.075), "Polymer", "Gun", t=(0, 0.045, 0.33))
    m.part("HandguardStripe", box(0.072, 0.015, 0.2), "Accent", "Gun", t=(0, 0.06, 0.33))
    m.part("Barrel", cyl(0.012, None, 0.2, 12, "z"), "Metal", "Gun", t=(0, 0.05, 0.54))
    m.part("MuzzleBrake", cyl(0.02, None, 0.05, 8, "z"), "MetalLight", "Gun", t=(0, 0.05, 0.65))
    m.part("FrontPost", box(0.01, 0.05, 0.015), "Metal", "Gun", t=(0, 0.1, 0.43))
    m.part("Grip", tbox(0.04, 0.06, 0.038, 0.05, 0.12), "Polymer", "Gun", t=(0, -0.05, -0.05), r=(18, 0, 0))
    m.part("TriggerGuard", box(0.01, 0.008, 0.08), "Metal", "Gun", t=(0, -0.015, 0.02))
    m.part("Mag", merge(xf(box(0.032, 0.11, 0.06), t=(0, -0.04, 0)),
                        xf(box(0.032, 0.1, 0.06), t=(0, -0.13, 0.025), r=(-18, 0, 0))),
           "Metal", "Gun", t=(0, -0.0, 0.1))
    m.part("Stock", merge(tbox(0.05, 0.22, 0.045, 0.22, 0.07, top_dz=0.0),
                          xf(box(0.052, 0.13, 0.04), t=(0, -0.03, -0.09))), "Polymer", "Gun", t=(0, 0.04, -0.27))
    m.part("ButtPad", box(0.056, 0.14, 0.02), "Accent", "Gun", t=(0, 0.01, -0.39))
    # коллиматорный прицел
    m.part("SightBase", box(0.03, 0.025, 0.06), "Metal", "Gun", t=(0, 0.12, 0.06))
    m.part("SightTube", cyl(0.024, None, 0.07, 14, "z"), "Polymer", "Gun", t=(0, 0.155, 0.06))
    m.part("SightLens", cyl(0.018, None, 0.072, 14, "z"), "Lens", "Gun", t=(0, 0.155, 0.06))
    m.part("ChargingHandle", box(0.02, 0.012, 0.03), "MetalLight", "Gun", t=(0, 0.1, -0.13))
    _flash(m, "Gun", 0.72)
    _fire(m, 0.12, 0.02, 2.5)
    _reload(m, (0, -0.3, 0.02), 1.8)
    return m


def sniper_rifle():
    m = Model("SniperRifle")
    _common(m, "#ffb020")
    m.mat("Wood", "#7a4a26", rough=0.75)
    m.mat("Glass", "#5fd3ff", metal=0.2, rough=0.05, emissive="#0a4a66")
    m.node("Gun")
    m.part("Stock", merge(tbox(0.06, 0.55, 0.05, 0.5, 0.08),
                          xf(tbox(0.055, 0.28, 0.05, 0.3, 0.1), t=(0, -0.06, -0.38), r=(4, 0, 0)),
                          xf(box(0.04, 0.1, 0.05), t=(0, -0.08, -0.12), r=(20, 0, 0))),
           "Wood", "Gun", t=(0, 0.02, 0.02))
    m.part("ButtPad", box(0.058, 0.17, 0.025), "Polymer", "Gun", t=(0, -0.03, -0.54))
    m.part("Receiver", cyl(0.028, None, 0.26, 14, "z"), "Metal", "Gun", t=(0, 0.075, 0.05))
    m.part("Barrel", cyl(0.012, 0.018, 0.72, 12, "z"), "Metal", "Gun", t=(0, 0.075, 0.54))
    m.part("Suppressor", cyl(0.03, None, 0.16, 16, "z"), "Polymer", "Gun", t=(0, 0.075, 0.97))
    m.node("Bolt", "Gun", t=(0.03, 0.08, -0.04))
    m.part("BoltHandle", merge(xf(cyl(0.006, None, 0.06, 8, "x"), t=(0.03, 0, 0)), xf(sphere(0.014, seg=10, rings=6), t=(0.06, 0, 0))),
           "MetalLight", "Bolt")
    m.part("ScopeMount", merge(xf(box(0.025, 0.04, 0.025), t=(0, 0, -0.06)), xf(box(0.025, 0.04, 0.025), t=(0, 0, 0.1))),
           "Metal", "Gun", t=(0, 0.115, 0.06))
    m.part("ScopeTube", cyl(0.022, None, 0.34, 16, "z"), "Polymer", "Gun", t=(0, 0.16, 0.04))
    m.part("ScopeFront", cyl(0.036, 0.024, 0.08, 16, "z"), "Polymer", "Gun", t=(0, 0.16, 0.24))
    m.part("ScopeBack", cyl(0.024, 0.032, 0.06, 16, "z"), "Polymer", "Gun", t=(0, 0.16, -0.15))
    m.part("ScopeTurret", merge(cyl(0.014, None, 0.04, 10), xf(cyl(0.014, None, 0.04, 10, "x"), t=(0.03, -0.02, 0))),
           "Accent", "Gun", t=(0, 0.19, 0.05))
    m.part("LensFront", cyl(0.033, None, 0.005, 16, "z"), "Glass", "Gun", t=(0, 0.16, 0.282))
    m.part("LensBack", cyl(0.029, None, 0.005, 16, "z"), "Glass", "Gun", t=(0, 0.16, -0.182))
    m.part("Mag", box(0.04, 0.06, 0.08), "Metal", "Gun", t=(0, 0.0, 0.08))
    m.part("Bipod", merge(xf(cyl(0.007, None, 0.24, 6), t=(-0.03, -0.11, 0), r=(0, 0, -12)),
                          xf(cyl(0.007, None, 0.24, 6), t=(0.03, -0.11, 0), r=(0, 0, 12))),
           "MetalLight", "Gun", t=(0, 0.03, 0.62))
    _flash(m, "Gun", 1.07, 1.4)
    _fire(m, 0.4, 0.06, 7.0)
    m.anim("BoltCycle", [
        ("Bolt", "rotation", [(0, (0, 0, 0)), (0.15, (0, 0, 70)), (0.45, (0, 0, 70)), (0.6, (0, 0, 0)), (0.8, (0, 0, 0))]),
        ("Bolt", "translation", [(0, (0, 0, 0)), (0.15, (0, 0, 0)), (0.3, (0, 0, -0.08)),
                                 (0.45, (0, 0, 0)), (0.8, (0, 0, 0))]),
    ])
    _reload(m, (0, -0.2, 0), 1.6)
    return m


def shotgun():
    m = Model("PumpShotgun")
    _common(m, "#3ecf5a")
    m.mat("Wood", "#8a5a33", rough=0.7)
    m.node("Gun")
    m.part("Receiver", box(0.06, 0.08, 0.24), "Metal", "Gun", t=(0, 0.05, 0.05))
    m.part("Barrel", cyl(0.018, None, 0.56, 14, "z"), "Metal", "Gun", t=(0, 0.075, 0.45))
    m.part("Tube", cyl(0.014, None, 0.48, 12, "z"), "MetalLight", "Gun", t=(0, 0.035, 0.41))
    m.part("Bead", sphere(0.006, seg=8, rings=5), "Accent", "Gun", t=(0, 0.097, 0.72))
    m.node("Pump", "Gun", t=(0, 0.035, 0.33))
    m.part("PumpGrip", merge(cyl(0.03, None, 0.16, 14, "z"), *[xf(cyl(0.031, None, 0.008, 14, "z"), t=(0, 0, z)) for z in (-0.05, 0, 0.05)]),
           "Wood", "Pump")
    m.part("Stock", merge(xf(tbox(0.05, 0.3, 0.048, 0.3, 0.07), r=(-8, 0, 0)),
                          xf(tbox(0.05, 0.08, 0.05, 0.12, 0.16), t=(0, -0.05, -0.14), r=(-8, 0, 0))),
           "Wood", "Gun", t=(0, 0.02, -0.22))
    m.part("ButtPad", box(0.056, 0.17, 0.02), "Polymer", "Gun", t=(0, -0.02, -0.39), r=(-8, 0, 0))
    m.part("TriggerGuard", box(0.01, 0.008, 0.07), "Metal", "Gun", t=(0, -0.0, 0.02))
    m.part("Mag", box(0.04, 0.02, 0.06), "Accent", "Gun", t=(0, 0.01, 0.08))  # окно подачи
    _flash(m, "Gun", 0.76, 1.6)
    m.anim("Fire", [
        ("Gun", "translation", [(0, (0, 0, 0)), (0.05, (0, 0, -0.05)), (0.25, (0, 0, 0)), (0.9, (0, 0, 0))]),
        ("Gun", "rotation", [(0, (0, 0, 0)), (0.05, (-8, 0, 0)), (0.25, (0, 0, 0)), (0.9, (0, 0, 0))]),
        ("Flash", "scale", [(0, (0.001,) * 3), (0.01, (1, 1, 1)), (0.06, (1.3, 1.3, 1.3)),
                            (0.1, (0.001,) * 3), (0.9, (0.001,) * 3)]),
        ("Pump", "translation", [(0, (0, 0, 0)), (0.35, (0, 0, 0)), (0.5, (0, 0, -0.1)),
                                 (0.65, (0, 0, 0)), (0.9, (0, 0, 0))]),
    ])
    return m


def pistol():
    m = Model("Pistol")
    _common(m, "#b0b6c0")
    m.node("Gun")
    m.part("Frame", box(0.03, 0.03, 0.17), "Polymer", "Gun", t=(0, 0.03, 0.06))
    m.node("Slide", "Gun", t=(0, 0.06, 0.06))
    m.part("SlideBody", box(0.032, 0.035, 0.19), "Metal", "Slide")
    m.part("SlideSerrations", merge(*[xf(box(0.034, 0.03, 0.004), t=(0, 0, -0.08 + i * 0.008)) for i in range(4)]),
           "MetalLight", "Slide")
    m.part("Sights", merge(xf(box(0.006, 0.01, 0.008), t=(0, 0.022, 0.085)), xf(box(0.022, 0.01, 0.008), t=(0, 0.022, -0.085))),
           "Accent", "Slide")
    m.part("Barrel", cyl(0.008, None, 0.01, 10, "z"), "MetalLight", "Gun", t=(0, 0.06, 0.156))
    m.part("Grip", tbox(0.032, 0.05, 0.03, 0.045, 0.11), "Polymer", "Gun", t=(0, -0.03, -0.0), r=(14, 0, 0))
    m.part("Mag", box(0.024, 0.1, 0.035), "Metal", "Gun", t=(0, -0.035, 0.0), r=(14, 0, 0))
    m.part("TriggerGuard", merge(box(0.008, 0.006, 0.05), xf(box(0.008, 0.03, 0.006), t=(0, 0.015, 0.025))),
           "Polymer", "Gun", t=(0, -0.0, 0.05))
    _flash(m, "Gun", 0.17, 0.7)
    _fire(m, 0.25, 0.02, 9.0, extra=[
        ("Slide", "translation", [(0, (0, 0, 0)), (0.03, (0, 0, -0.04)), (0.1, (0, 0, 0)), (0.25, (0, 0, 0))])])
    _reload(m, (0, -0.2, -0.05), 1.3)
    return m


def rocket_launcher():
    m = Model("RocketLauncher")
    _common(m, "#ff4d6d")
    m.mat("Olive", "#4f5b2e", rough=0.8)
    m.mat("Warhead", "#c8202f", metal=0.2, rough=0.4)
    m.mat("Exhaust", "#ff8a1f", emissive="#ff6a00", alpha=0.8)
    m.node("Gun")
    m.part("Tube", cyl(0.07, None, 1.1, 20, "z"), "Olive", "Gun", t=(0, 0.1, 0.15))
    m.part("FrontRing", cyl(0.085, None, 0.08, 20, "z"), "Accent", "Gun", t=(0, 0.1, 0.68))
    m.part("BackFlare", cyl(0.075, 0.1, 0.12, 20, "z"), "Metal", "Gun", t=(0, 0.1, -0.44))
    m.part("Grips", merge(xf(box(0.035, 0.12, 0.05), t=(0, -0.03, 0), r=(12, 0, 0)),
                          xf(box(0.035, 0.11, 0.05), t=(0, -0.03, 0.3), r=(5, 0, 0))), "Polymer", "Gun", t=(0, 0.0, 0.0))
    m.part("SightBox", box(0.06, 0.06, 0.14), "Metal", "Gun", t=(-0.09, 0.17, 0.25))
    m.part("SightLens", cyl(0.02, None, 0.15, 12, "z"), "Accent", "Gun", t=(-0.09, 0.18, 0.25))
    m.part("ShoulderPad", box(0.1, 0.03, 0.2), "Polymer", "Gun", t=(0, 0.02, -0.15))
    m.node("Rocket", "Gun", t=(0, 0.1, 0.55))
    m.part("RocketBody", cyl(0.04, None, 0.3, 14, "z"), "MetalLight", "Rocket")
    m.part("RocketWarhead", merge(xf(cyl(0.0, 0.065, 0.2, 16, "z"), t=(0, 0, 0.25)), xf(cyl(0.065, None, 0.05, 16, "z"), t=(0, 0, 0.13))),
           "Warhead", "Rocket")
    fins = merge(*[xf(box(0.006, 0.08, 0.08), t=(0, 0.05, 0), r=(0, 0, a)) for a in (0, 90, 180, 270)])
    m.part("RocketFins", fins, "Metal", "Rocket", t=(0, 0, -0.13))
    m.part("RocketFlame", cyl(0.035, 0.0, 0.3, 10, "z"), "Exhaust", "Rocket", t=(0, 0, -0.32), s=(0.001,) * 3, obj=False)
    _flash(m, "Gun", 0.75, 2.2)
    m.anim("Fire", [
        ("Rocket", "translation", [(0, (0, 0, 0)), (0.05, (0, 0, 0)), (0.6, (0, 0, 6)), (2.0, (0, 0, 6)), (2.01, (0, 0, -0.3)),
                                   (2.4, (0, 0, 0)), (2.6, (0, 0, 0))]),
        ("Rocket", "scale", [(0, (1, 1, 1)), (0.59, (1, 1, 1)), (0.6, (0.001,) * 3), (2.0, (0.001,) * 3), (2.01, (1, 1, 1)),
                             (2.6, (1, 1, 1))]),
        ("RocketFlame", "scale", [(0, (0.001,) * 3), (0.05, (1, 1, 1)), (0.3, (1.3, 1.3, 1.6)), (0.6, (1, 1, 1)),
                                  (0.61, (0.001,) * 3), (2.6, (0.001,) * 3)]),
        ("Gun", "translation", [(0, (0, 0, 0)), (0.08, (0, 0, -0.08)), (0.4, (0, 0, 0)), (2.6, (0, 0, 0))]),
        ("Gun", "rotation", [(0, (0, 0, 0)), (0.08, (-6, 0, 0)), (0.4, (0, 0, 0)), (2.6, (0, 0, 0))]),
        ("Flash", "scale", [(0, (0.001,) * 3), (0.02, (1, 1, 1)), (0.12, (1.4, 1.4, 1.4)), (0.2, (0.001,) * 3),
                            (2.6, (0.001,) * 3)]),
    ])
    return m


def grenade():
    m = Model("Grenade")
    m.mat("Body", "#3d4a2a", rough=0.6)
    m.mat("Metal", "#9aa1ab", metal=0.85, rough=0.3)
    m.mat("Accent", "#ffcc00", rough=0.5)
    m.node("Gun")
    segs = merge(sphere(0.045, 0.055, 0.045, 14, 10),
                 *[xf(cyl(0.0465, None, 0.006, 14), t=(0, y, 0), s=(1, 1, 1)) for y in (-0.02, 0.0, 0.02)])
    m.part("Body", segs, "Body", "Gun")
    m.part("Stripe", cyl(0.047, None, 0.008, 14), "Accent", "Gun", t=(0, 0.035, 0), s=(0.8, 1, 0.8))
    m.part("Fuse", cyl(0.016, 0.018, 0.035, 12), "Metal", "Gun", t=(0, 0.065, 0))
    m.node("Lever", "Gun", t=(0.014, 0.08, 0))
    m.part("LeverBody", box(0.012, 0.01, 0.09), "Metal", "Lever", t=(0.0, 0, 0.0), r=(0, 90, -70))
    m.node("Pin", "Gun", t=(-0.025, 0.07, 0))
    m.part("PinRing", merge(*[xf(box(0.004, 0.015, 0.004), t=(0.018 * math.cos(a / 8 * 6.283), 0.018 * math.sin(a / 8 * 6.283), 0),
                                 r=(0, 0, a * 45)) for a in range(8)]), "Metal", "Pin", t=(-0.02, 0, 0), r=(90, 0, 0))
    m.anim("PullPin", [
        ("Pin", "translation", [(0, (0, 0, 0)), (0.3, (0, 0, 0)), (0.6, (-0.12, 0.03, 0)), (1.2, (-0.12, 0.03, 0))]),
        ("Pin", "scale", [(0, (1, 1, 1)), (0.9, (1, 1, 1)), (0.91, (0.001,) * 3), (1.2, (0.001,) * 3)]),
        ("Gun", "rotation", [(0, (0, 0, 0)), (0.6, (0, 0, 0)), (1.2, (0, 720, 0))]),
    ])
    return m


ALL = [smg_uzi, assault_rifle, sniper_rifle, shotgun, pistol, rocket_launcher, grenade]
