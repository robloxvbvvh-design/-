import json, math, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
AUDIO_END = 32.91
SCREAM_AT = 33.0
TOTAL = 37.0
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FONT_B = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
f_sub = ImageFont.truetype(FONT, 84)
f_head = ImageFont.truetype(FONT, 76)
f_small = ImageFont.truetype(FONT_B, 40)
f_phone = ImageFont.truetype(FONT, 46)
f_big = ImageFont.truetype(FONT, 150)

# ---------------- subtitles ----------------
words = json.load(open(sys.argv[1]))
fix = {3: "крик —", 5: "советов.", 7: "глохнет.", 8: "Мутант!", 10: "совет:", 13: "оружие,", 15: "мутанта.",
       20: "дверь.", 22: "совет:", 25: "Витю,", 30: "выживание.", 32: "решаетесь", 35: "автобуса.",
       37: "совет:", 39: "лес,", 41: "нету —", 45: "ягодами.", 46: "Четвёртое:", 51: "экономьте",
       53: "разводите", 54: "костёр.", 55: "Но", 57: "пробрался...", 59: "крик!"}
for i, w in enumerate(words):
    w["t"] = fix.get(i, w["w"]).upper()
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else AUDIO_END
    w["e"] = min(nxt, w["s"] + 0.95)
groups, cur = [], []
for w in words:
    cur.append(w)
    if w["t"][-1] in ".:!…—," or len(cur) == 3:
        groups.append(cur); cur = []
if cur: groups.append(cur)
for gi, g in enumerate(groups):
    g_start = g[0]["s"] - 0.05
    g_end = groups[gi + 1][0]["s"] - 0.05 if gi + 1 < len(groups) else TOTAL
    g_end = min(g_end, g[-1]["e"] + 0.6) if gi + 1 < len(groups) else g_end
    groups[gi] = (g_start, g_end, g)



def draw_subs(img, t):
    d = ImageDraw.Draw(img)
    for gs, ge, g in groups:
        if not (gs <= t < ge):
            continue
        # lay out words, wrapping at 960px
        fnt = f_sub
        widest = max(d.textlength(w["t"], font=f_sub) for w in g)
        if widest > 980:
            fnt = ImageFont.truetype(FONT, int(84 * 980 / widest))
        lines, line, lw = [], [], 0
        sp = d.textlength(" ", font=fnt)
        for w in g:
            ww = d.textlength(w["t"], font=fnt)
            if line and lw + sp + ww > 980:
                lines.append((line, lw)); line, lw = [], 0
            lw = lw + (sp if line else 0) + ww
            line.append((w, ww))
        lines.append((line, lw))
        y = 1580 - (len(lines) - 1) * 50
        pop = min(1.0, (t - gs) / 0.12)
        for line, lw in lines:
            x = (W - lw) / 2
            for w, ww in line:
                active = w["s"] <= t < w["e"]
                col = (255, 40, 40) if active else (255, 255, 255)
                dy = -8 if active else 0
                d.text((x, y + dy + (1 - pop) * 30), w["t"], font=fnt, fill=col,
                       stroke_width=9, stroke_fill=(0, 0, 0))
                x += ww + sp
            y += 104


# ---------------- drawing helpers ----------------
def limb(d, a, b, w, col):
    d.line([a, b], fill=col, width=w)
    r = w // 2
    for p in (a, b):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)


def pt(o, ang, ln):
    return (o[0] + math.cos(math.radians(ang)) * ln, o[1] + math.sin(math.radians(ang)) * ln)


def person(d, hip, s=1.0, skin=(245, 200, 160), shirt=(40, 110, 220), pants=(40, 40, 60),
           hair=(70, 45, 25), sitting=False, arm_l=110, arm_r=70, fore_l=None, fore_r=None,
           zombie=False, lean=0, face="calm", lying=False):
    if lying:
        # lying on floor, horizontal
        x, y = hip
        limb(d, (x - 120 * s, y), (x + 60 * s, y), int(60 * s), shirt)
        limb(d, (x + 60 * s, y), (x + 200 * s, y + 5), int(34 * s), pants)
        d.ellipse([x - 200 * s, y - 40 * s, x - 120 * s, y + 40 * s], fill=skin)
        for k in (-1, 1):
            d.line([(x - 175 * s, y - 12 * s + k * 3), (x - 155 * s, y + 8 * s + k * 3)], fill=(0, 0, 0), width=5)
            d.line([(x - 175 * s, y + 8 * s), (x - 155 * s, y - 12 * s)], fill=(0, 0, 0), width=5)
        return
    neck = pt(hip, -90 + lean, 170 * s)
    shoulder = pt(neck, 90 + lean, 20 * s)
    # legs
    if sitting:
        knee = (hip[0] + 95 * s, hip[1])
        foot = (knee[0] + 5 * s, knee[1] + 110 * s)
        limb(d, hip, knee, int(40 * s), pants); limb(d, knee, foot, int(36 * s), pants)
        d.ellipse([foot[0] - 10 * s, foot[1] - 14 * s, foot[0] + 40 * s, foot[1] + 14 * s], fill=(30, 30, 30))
    else:
        for k in (-1, 1):
            knee = (hip[0] + k * 22 * s, hip[1] + 100 * s)
            foot = (hip[0] + k * 30 * s, hip[1] + 200 * s)
            limb(d, hip, knee, int(38 * s), pants); limb(d, knee, foot, int(34 * s), pants)
    # torso
    limb(d, hip, neck, int(78 * s), shirt)
    # arms: upper arm angle + forearm angle
    hands = []
    for ang, fang in ((arm_l, fore_l), (arm_r, fore_r)):
        el = pt(shoulder, ang, 70 * s)
        hd = pt(el, fang if fang is not None else ang, 65 * s)
        limb(d, shoulder, el, int(30 * s), shirt)
        limb(d, el, hd, int(26 * s), skin)
        hands.append(hd)
    # head
    hc = pt(neck, -90 + lean, 60 * s)
    r = 58 * s
    d.ellipse([hc[0] - r, hc[1] - r, hc[0] + r, hc[1] + r], fill=skin)
    if zombie:
        d.ellipse([hc[0] - 30 * s, hc[1] - 15 * s, hc[0] - 8 * s, hc[1] + 7 * s], fill=(255, 255, 210))
        d.ellipse([hc[0] + 8 * s, hc[1] - 15 * s, hc[0] + 30 * s, hc[1] + 7 * s], fill=(255, 255, 210))
        d.ellipse([hc[0] - 22 * s, hc[1] - 8 * s, hc[0] - 15 * s, hc[1] - 1 * s], fill=(160, 0, 0))
        d.ellipse([hc[0] + 15 * s, hc[1] - 8 * s, hc[0] + 22 * s, hc[1] - 1 * s], fill=(160, 0, 0))
        d.rectangle([hc[0] - 22 * s, hc[1] + 22 * s, hc[0] + 22 * s, hc[1] + 34 * s], fill=(60, 0, 0))
        for k in range(4):
            xx = hc[0] - 18 * s + k * 12 * s
            d.rectangle([xx, hc[1] + 22 * s, xx + 6 * s, hc[1] + 28 * s], fill=(240, 240, 200))
        d.line([(hc[0] - 40 * s, hc[1] - 35 * s), (hc[0] - 10 * s, hc[1] - 50 * s)], fill=(120, 20, 20), width=int(6 * s))
    else:
        d.chord([hc[0] - r, hc[1] - r - 6 * s, hc[0] + r, hc[1] + r * 0.4], 180, 360, fill=hair)
        for k in (-1, 1):
            ex = hc[0] + k * 20 * s
            d.ellipse([ex - 7 * s, hc[1] - 4 * s, ex + 7 * s, hc[1] + 10 * s], fill=(20, 20, 20))
        if face == "scared":
            d.ellipse([hc[0] - 12 * s, hc[1] + 20 * s, hc[0] + 12 * s, hc[1] + 44 * s], fill=(60, 0, 0))
            for k in (-1, 1):
                d.line([(hc[0] + k * 10 * s, hc[1] - 18 * s), (hc[0] + k * 32 * s, hc[1] - 26 * s)], fill=(20, 20, 20), width=int(5 * s))
        elif face == "angry":
            d.line([(hc[0] - 18 * s, hc[1] + 32 * s), (hc[0] + 18 * s, hc[1] + 32 * s)], fill=(60, 0, 0), width=int(6 * s))
            for k in (-1, 1):
                d.line([(hc[0] + k * 8 * s, hc[1] - 10 * s), (hc[0] + k * 32 * s, hc[1] - 20 * s)], fill=(20, 20, 20), width=int(6 * s))
        elif face == "happy":
            d.arc([hc[0] - 22 * s, hc[1] + 5 * s, hc[0] + 22 * s, hc[1] + 38 * s], 20, 160, fill=(60, 0, 0), width=int(6 * s))
        else:
            d.line([(hc[0] - 12 * s, hc[1] + 30 * s), (hc[0] + 12 * s, hc[1] + 30 * s)], fill=(60, 0, 0), width=int(5 * s))
    return hands, hc


def zombie(d, hip, s, t, phase=0.0, hit=0.0):
    sw = math.sin(t * 6 + phase) * 8
    lean = -12 * hit
    person(d, (hip[0] - hit * 40, hip[1]), s=s, skin=(130, 180, 110), shirt=(90, 80, 70), pants=(50, 60, 80),
           zombie=True, arm_l=180 + sw, arm_r=175 - sw, fore_l=185 + sw, fore_r=180 - sw, lean=lean)


def hockey_stick(d, hand, ang, ln=330):
    end = pt(hand, ang, ln)
    back = pt(hand, ang + 180, 60)
    limb(d, back, end, 16, (120, 70, 30))
    blade = pt(end, ang + 90, 70)
    limb(d, end, blade, 24, (30, 30, 30))
    d.line([back, pt(back, ang, 40)], fill=(20, 20, 20), width=18)


def phone_small(d, c, alert=False, t=0):
    x, y = c
    d.rounded_rectangle([x - 32, y - 55, x + 32, y + 55], 10, fill=(20, 20, 20))
    col = (255, 0, 0) if alert and int(t * 6) % 2 else (90, 200, 255)
    d.rounded_rectangle([x - 26, y - 46, x + 26, y + 46], 6, fill=col)


def tint(img, col, a):
    if a <= 0: return img
    ov = Image.new("RGB", img.size, col)
    return Image.blend(img, ov, a)


def shake_img(img, amt, t):
    if amt <= 0: return img
    dx = int(math.sin(t * 53) * amt); dy = int(math.cos(t * 41) * amt)
    out = Image.new("RGB", img.size, (0, 0, 0))
    out.paste(img, (dx, dy))
    return out


def header(img, text, sub=None, col=(255, 210, 0)):
    d = ImageDraw.Draw(img)
    tw = d.textlength(text, font=f_head)
    d.rounded_rectangle([(W - tw) / 2 - 40, 70, (W + tw) / 2 + 40, 180], 30, fill=(0, 0, 0))
    d.text(((W - tw) / 2, 82), text, font=f_head, fill=col)
    if sub:
        sw = d.textlength(sub, font=f_small)
        d.text(((W - sw) / 2, 188), sub, font=f_small, fill=(255, 255, 255), stroke_width=5, stroke_fill=(0, 0, 0))


def ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)



# ---------------- part 2: bus, mutant, forest ----------------
def mutant(d, cx, base, s, t, fall=0.0, glow_only=False):
    """Big hunched purple mutant; fall in [0,1] tips it over backwards."""
    if glow_only:
        for k, dx in enumerate((-40, 0, 40)):
            blink = int(t * 3 + k) % 7 != 0
            if blink:
                d.ellipse([cx + dx * s - 14 * s, base - 14 * s, cx + dx * s + 14 * s, base + 14 * s], fill=(255, 230, 0))
                d.ellipse([cx + dx * s - 5 * s, base - 8 * s, cx + dx * s + 5 * s, base + 8 * s], fill=(200, 0, 0))
        return
    body = (120, 50, 150)
    dark = (70, 25, 90)
    breath = math.sin(t * 5) * 6 * s
    lean = 25 * fall
    hip = (cx + 60 * fall * s, base - 220 * s * (1 - 0.6 * fall))
    top = pt(hip, -90 + lean + 15, 260 * s)
    for k in (-1, 1):  # legs
        knee = (hip[0] + k * 50 * s, hip[1] + 110 * s * (1 - 0.5 * fall))
        limb(d, hip, knee, int(60 * s), dark)
        limb(d, knee, (knee[0] + k * 10 * s, base - 10 * s), int(54 * s), dark)
    limb(d, hip, top, int(170 * s + breath), body)
    for k, ang in ((-1, 160 + math.sin(t * 7) * 15), (1, 200 - math.sin(t * 7) * 15)):  # long arms with claws
        sh = (top[0] + k * 60 * s, top[1] + 30 * s)
        el = pt(sh, ang - 70 * k + lean, 120 * s)
        hd = pt(el, ang + lean, 130 * s)
        limb(d, sh, el, int(50 * s), body)
        limb(d, el, hd, int(42 * s), body)
        for c in (-25, 0, 25):
            d.line([hd, pt(hd, ang + c + lean, 50 * s)], fill=(240, 240, 220), width=int(10 * s))
    hc = pt(top, -90 + lean, 70 * s)
    r = 80 * s
    d.ellipse([hc[0] - r, hc[1] - r, hc[0] + r, hc[1] + r], fill=body)
    for dx in (-35, 0, 35):
        d.ellipse([hc[0] + dx * s - 16 * s, hc[1] - 30 * s, hc[0] + dx * s + 16 * s, hc[1] + 2 * s], fill=(255, 230, 0))
        d.ellipse([hc[0] + dx * s - 6 * s, hc[1] - 24 * s, hc[0] + dx * s + 6 * s, hc[1] - 4 * s], fill=(150, 0, 0))
    d.chord([hc[0] - 55 * s, hc[1] + 5 * s, hc[0] + 55 * s, hc[1] + 70 * s], 0, 180, fill=(40, 0, 20))
    for k in range(6):
        x = hc[0] - 45 * s + k * 18 * s
        d.polygon([(x, hc[1] + 37 * s), (x + 14 * s, hc[1] + 37 * s), (x + 7 * s, hc[1] + 58 * s)], fill=(250, 250, 230))


def bus(t, moving=True, door_open=1.0, flicker=False, dark=0.0):
    img = Image.new("RGB", (W, H), (25, 25, 30))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 230, W, 1420], fill=(225, 225, 215))
    # windows with road outside
    off = (t * 1100) % 400 if moving else 0
    for k in range(3):
        x0 = 30 + k * 260
        d.rectangle([x0, 330, x0 + 220, 640], fill=(140, 190, 230))
        d.rectangle([x0, 560, x0 + 220, 640], fill=(90, 140, 70))
        for j in range(-1, 3):
            tx = x0 + 220 - ((off + j * 200) % 400) + 100
            if x0 + 20 < tx < x0 + 200:
                d.polygon([(tx, 470), (tx - 35, 570), (tx + 35, 570)], fill=(40, 100, 50))
        d.rectangle([x0, 330, x0 + 220, 640], outline=(110, 110, 120), width=12)
    # handrail + straps
    d.line([(0, 285), (W, 285)], fill=(170, 170, 180), width=12)
    for k in range(6):
        x = 80 + k * 170 + math.sin(t * 3 + k) * (6 if moving else 1)
        d.line([(80 + k * 170, 285), (x, 340)], fill=(160, 160, 170), width=6)
        d.ellipse([x - 18, 335, x + 18, 371], outline=(250, 200, 30), width=6)
    # seats
    for k in range(3):
        x0 = 40 + k * 260
        d.rounded_rectangle([x0, 820, x0 + 200, 1060], 25, fill=(40, 90, 170))
        d.rounded_rectangle([x0 - 10, 1040, x0 + 210, 1110], 20, fill=(50, 110, 200))
        d.rectangle([x0 + 90, 1110, x0 + 110, 1330], fill=(100, 100, 110))
    # floor
    d.rectangle([0, 1330, W, 1420], fill=(70, 70, 75))
    for k in range(0, W, 60):
        d.line([(k, 1330), (k, 1420)], fill=(60, 60, 65), width=3)
    # front folding door (right)
    dx0, dx1 = 830, 1060
    d.rectangle([dx0 - 12, 320, dx1 + 12, 1330], fill=(90, 90, 100))
    if door_open > 0:
        d.rectangle([dx0, 330, dx1, 1330], fill=(40, 60, 50))
        d.rectangle([dx0, 1150, dx1, 1330], fill=(110, 110, 110))
    wpanel = (dx1 - dx0) / 2 * (1 - door_open) + 12 * door_open
    for side in (0, 1):
        x0 = dx0 if side == 0 else dx1 - wpanel
        d.rectangle([x0, 330, x0 + wpanel, 1330], fill=(160, 165, 170), outline=(90, 90, 100), width=6)
        if wpanel > 40:
            d.rectangle([x0 + 18, 360, x0 + wpanel - 18, 1000], fill=(150, 200, 230))
    if door_open <= 0:
        d.rectangle([(dx0 + dx1) / 2 - 30, 900, (dx0 + dx1) / 2 + 30, 960], fill=(220, 0, 0))
        d.text(((dx0 + dx1) / 2 - 18, 898), "×", font=f_small, fill=(255, 255, 255))
    lamp = (255, 250, 220)
    if flicker and random.Random(int(t * 12)).random() < 0.5:
        lamp = (60, 60, 60)
        img = tint(img, (0, 0, 0), 0.0)
    d.rounded_rectangle([200, 240, 880, 268], 12, fill=lamp)
    if flicker and lamp == (60, 60, 60):
        img = tint(img, (0, 0, 0), 0.45)
    if dark:
        img = tint(img, (0, 0, 0), dark)
    return img


def forest(t, night=False):
    sky = (20, 25, 60) if night else (130, 190, 240)
    img = Image.new("RGB", (W, H), (25, 25, 30))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 230, W, 1420], fill=sky)
    if night:
        rnd = random.Random(5)
        for _ in range(60):
            x, y = rnd.randint(0, W), rnd.randint(240, 800)
            r = 2 + (int(t * 4 + x) % 3 == 0)
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 220))
        d.ellipse([820, 300, 940, 420], fill=(240, 240, 210))
    else:
        d.ellipse([820, 290, 960, 430], fill=(255, 220, 60))
    ground = (25, 60, 30) if night else (80, 150, 60)
    d.rectangle([0, 1050, W, 1420], fill=ground)
    rnd = random.Random(11)
    for layer, (y, sc, col) in enumerate(((1060, 0.8, (20, 50, 30) if night else (50, 110, 60)),
                                          (1120, 1.1, (10, 35, 20) if night else (30, 90, 45)))):
        for k in range(7):
            x = k * 170 + rnd.randint(-30, 30) + layer * 80
            h = 380 * sc
            d.rectangle([x - 14 * sc, y - 40, x + 14 * sc, y + 30], fill=(60, 40, 25) if not night else (35, 25, 15))
            for j in range(3):
                d.polygon([(x, y - h + j * 90 * sc), (x - 110 * sc + j * 10, y - h + 170 * sc + j * 100 * sc),
                           (x + 110 * sc - j * 10, y - h + 170 * sc + j * 100 * sc)], fill=col)
    return img


def berry_bush(d, cx, cy, s=1.0, eaten=0):
    for dx, dy, r in ((-60, 0, 70), (40, -10, 80), (0, -60, 70), (90, 20, 55), (-100, 25, 50)):
        d.ellipse([cx + dx * s - r * s, cy + dy * s - r * s, cx + dx * s + r * s, cy + dy * s + r * s], fill=(40, 120, 50))
    rnd = random.Random(int(cx))
    for i in range(14 - eaten):
        x, y = cx + rnd.randint(-130, 130) * s, cy + rnd.randint(-100, 60) * s
        d.ellipse([x - 13 * s, y - 13 * s, x + 13 * s, y + 13 * s], fill=(210, 20, 50))
        d.ellipse([x - 5 * s, y - 8 * s, x, y - 3 * s], fill=(255, 150, 160))


def campfire(img, cx, cy, t):
    glow = Image.new("RGB", img.size, (0, 0, 0))
    g = ImageDraw.Draw(glow)
    rr = 420 + math.sin(t * 9) * 25
    g.ellipse([cx - rr, cy - rr * 0.8, cx + rr, cy + rr * 0.6], fill=(120, 60, 10))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img = Image.fromarray(np.minimum(255, np.asarray(img, dtype=np.int16) + np.asarray(glow, dtype=np.int16)).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for a in (-20, 20):
        d.line([pt((cx, cy + 10), 180 + a, 110), pt((cx, cy + 10), a, 110)], fill=(90, 55, 25), width=26)
    for layer, (col, sc) in enumerate((((255, 90, 0), 1.0), ((255, 180, 0), 0.65), ((255, 245, 160), 0.35))):
        pts = []
        for k in range(9):
            ang = math.pi * k / 8
            r = 90 * sc
            h = (180 + 60 * math.sin(t * 13 + k * 1.7 + layer)) * sc if k % 2 else 40 * sc
            pts.append((cx - math.cos(ang) * r, cy - math.sin(ang) * h))
        d.polygon(pts, fill=col)
    for k in range(5):  # sparks
        ph = (t * 1.3 + k * 0.21) % 1
        x = cx + math.sin(k * 7 + t * 2) * 60
        y = cy - 150 - ph * 380
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(255, 200, 80))
    return img


def bubble(d, x, y, text, tail_left=True):
    tw = d.textlength(text, font=f_small)
    d.rounded_rectangle([x, y, x + tw + 50, y + 80], 30, fill=(255, 255, 255), outline=(0, 0, 0), width=5)
    tx = x + 50 if tail_left else x + tw
    d.polygon([(tx, y + 78), (tx + 30, y + 78), (tx + 5, y + 120)], fill=(255, 255, 255))
    d.text((x + 25, y + 16), text, font=f_small, fill=(0, 0, 0))


DIMA = dict(shirt=(40, 110, 220), hair=(70, 45, 25))
VITYA = dict(shirt=(50, 170, 80), hair=(230, 190, 60), pants=(90, 60, 40))

T_STALL = 2.5     # автобус заглохает
T_MUT = 3.85      # мутант
T_S1 = 4.75       # первый совет
T_THROW = 7.5     # кидай
T_RUN = 8.8       # беги, запери дверь
T_S2 = 11.3       # второй совет
T_TALK = 13.95    # говоришь про выживание
T_EXIT = 16.6     # решаетесь выйти
T_S3 = 19.05      # третий совет
T_S4 = 24.05      # четвёртое
T_SNEAK = 29.8    # но мутант пробрался
T_SCREAM = 32.9


def frame(t):
    if t < T_STALL:
        img = Image.new("RGB", (W, H), (10, 0, 0))
        d = ImageDraw.Draw(img)
        k = t / T_STALL
        fnt = ImageFont.truetype(FONT, 150)
        txt = "АААА!"
        tw = d.textlength(txt, font=fnt)
        d.text(((W - tw) / 2, 520), txt, font=fnt, fill=(int(140 * (1 - k)) + 60, 0, 0))
        a = ease((t - 1.4) / 0.4)
        if a > 0:
            fnt2 = ImageFont.truetype(FONT, int(260 * (0.7 + 0.3 * a)))
            tw = d.textlength("5", font=fnt2)
            d.text(((W - tw) / 2, 760), "5", font=fnt2, fill=(255, 40, 40), stroke_width=10, stroke_fill=(0, 0, 0))
            lw = d.textlength("СОВЕТОВ", font=f_head)
            d.text(((W - lw) / 2, 1100), "СОВЕТОВ", font=f_head, fill=(255, 255, 255), stroke_width=6, stroke_fill=(0, 0, 0))
        header(img, "ЧАСТЬ 2", "Ты услышал крик...", col=(255, 60, 60))
    elif t < T_S1:
        img = bus(t, moving=False, flicker=True)
        d = ImageDraw.Draw(img)
        person(d, (380, 1130), face="scared", arm_l=-120, arm_r=-60, **DIMA)
        if t >= T_MUT:
            e = ease((t - T_MUT) / 0.5)
            mutant(d, 1250 - 300 * e, 1330, 1.0, t)
        img = shake_img(img, 10 * max(0, 1 - (t - T_STALL) / 0.8), t)
        header(img, "АВТОБУС ЗАГЛОХ", "...и тут МУТАНТ!" if t >= T_MUT else None, col=(255, 60, 60))
    elif t < T_RUN:
        img = bus(t, moving=False)
        d = ImageDraw.Draw(img)
        fall = ease((t - T_THROW - 0.45) / 0.5)
        mutant(d, 950 + 250 * fall, 1330, 1.0, t, fall=fall)
        if t < T_THROW:
            g = ease((t - T_S1 - 1.0) / 0.8)  # grab the extinguisher off the floor
            hands, _ = person(d, (380, 1130), face="angry", arm_l=120, arm_r=60 - 180 * g, fore_r=60 - 200 * g, **DIMA)
            hx, hy = hands[1] if g > 0 else (470, 1300)
            d.rounded_rectangle([hx - 25, hy - 90, hx + 25, hy + 20], 15, fill=(220, 20, 20))
            d.rectangle([hx - 10, hy - 110, hx + 10, hy - 90], fill=(30, 30, 30))
        else:
            hands, _ = person(d, (380, 1130), face="angry", arm_l=120, arm_r=-10, fore_r=-10, **DIMA)
            p = min(1.0, (t - T_THROW) / 0.45)
            if p < 1:
                x = 470 + (870 - 470) * p
                y = 760 - math.sin(p * math.pi) * 200 + (520 - 760) * p
                d.rounded_rectangle([x - 25, y - 55, x + 25, y + 55], 15, fill=(220, 20, 20))
            elif t < T_THROW + 1.2:
                d.text((760, 450), "БУМ!", font=f_head, fill=(255, 230, 0), stroke_width=8, stroke_fill=(200, 0, 0))
        header(img, "СОВЕТ №1", "Бери оружие и кидай в мутанта")
        if T_THROW + 0.45 < t < T_THROW + 0.9:
            img = shake_img(img, 16, t)
    elif t < T_S2:
        p = (t - T_RUN) / (T_S2 - T_RUN)
        door = 1 - ease((p - 0.45) / 0.3)
        img = bus(t, moving=False, door_open=door)
        d = ImageDraw.Draw(img)
        x = 380 + 400 * ease(p / 0.45)
        run = math.sin(t * 16) * 40 if p < 0.45 else 0
        person(d, (x, 1130), face="angry", arm_l=90 + run, arm_r=90 - run, **DIMA)
        if door <= 0:
            d.text((560, 700), "ЩЁЛК!", font=f_head, fill=(255, 230, 0), stroke_width=8, stroke_fill=(0, 0, 0))
        header(img, "БЕГИ!", "Запри дверь")
    elif t < T_S3:
        exiting = ease((t - T_EXIT - 0.6) / 1.8)
        img = bus(t, moving=False, door_open=ease((t - T_EXIT) / 0.6))
        d = ImageDraw.Draw(img)
        vx = 160 + 600 * exiting
        if exiting < 1:
            if t < T_TALK:
                person(d, (160, 1035), sitting=True, face="scared", arm_l=60, arm_r=40, fore_l=-40, fore_r=-30, **VITYA)
            else:
                person(d, (vx, 1130), face="calm" if t < T_EXIT else "happy", arm_l=110, arm_r=70, **VITYA)
            person(d, (560 + 300 * exiting, 1130), face="calm" if t < T_EXIT else "happy",
                   arm_l=200 if t < T_TALK + 2 else 110, arm_r=60, fore_l=200, **DIMA)
        if t < T_TALK:
            if t > 12.6:
                bubble(d, 400, 560, "Витя! Ты живой?")
        elif t < T_EXIT:
            bubble(d, 330, 520, "Надо выживать!")
            if t > T_TALK + 1.0:
                bubble(d, 60, 680, "Согласен!")
        else:
            bubble(d, 330, 520, "Выходим из автобуса!")
        header(img, "СОВЕТ №2", "Найди Витю — выживайте вместе")
    elif t < T_S4:
        img = forest(t)
        d = ImageDraw.Draw(img)
        p = (t - T_S3) / (T_S4 - T_S3)
        walk = ease(p / 0.35)
        bush_eaten = int(max(0, p - 0.45) * 18)
        berry_bush(d, 560, 1190, 1.1, eaten=min(10, bush_eaten))
        chew = math.sin(t * 14) * 30 if p > 0.45 else 0
        person(d, (-150 + 400 * walk, 1180), face="happy", arm_l=110, arm_r=-40 + chew if p > 0.45 else 70,
               fore_r=-140 + chew if p > 0.45 else None, **DIMA)
        person(d, (-350 + 1200 * walk, 1180), face="happy", arm_l=200 + chew if p > 0.45 else 110,
               fore_l=230 + chew if p > 0.45 else None, arm_r=70, **VITYA)
        header(img, "СОВЕТ №3", "Найдите лес и ешьте ягоды", col=(80, 255, 120))
    elif t < T_SCREAM:
        img = forest(t, night=True)
        img = campfire(img, 540, 1250, t)
        d = ImageDraw.Draw(img)
        if t >= T_SNEAK:
            e = ease((t - T_SNEAK) / 2.0)
            if e < 0.5:
                mutant(d, 820, 950, 0.7, t, glow_only=True)
            else:
                mutant(d, 900 - 120 * (e - 0.5), 1280, 0.85, t)
        person(d, (240, 1235), sitting=True, face="happy" if t < T_SNEAK else "scared", arm_l=40, arm_r=20,
               fore_l=-10, fore_r=-30, **DIMA)
        person(d, (760, 1235), sitting=True, face="happy" if t < T_SNEAK else "scared", arm_l=40, arm_r=20,
               fore_l=-10, fore_r=-30, **VITYA) if t < T_SNEAK + 1.0 else None
        # food stock: berries left
        d.rounded_rectangle([60, 300, 400, 380], 25, fill=(0, 0, 0))
        left = max(3, 9 - int((t - T_S4) * 1.2))
        d.text((85, 314), "ЕДА:", font=f_small, fill=(255, 255, 255))
        for k in range(left):
            d.ellipse([190 + k * 22, 330, 210 + k * 22, 350], fill=(210, 20, 50))
        if t < T_SNEAK:
            header(img, "СОВЕТ №4", "Экономь еду и разведи костёр", col=(255, 170, 40))
        else:
            header(img, "НО...", "Мутант пробрался!", col=(255, 60, 60))
            img = tint(img, (255, 0, 0), 0.12 * abs(math.sin(t * 6)))
    else:
        img = forest(t, night=True)
        img = tint(img, (0, 0, 0), 0.85)
        d = ImageDraw.Draw(img)
        k = t - T_SCREAM
        s = 1 + 0.08 * math.sin(t * 40)
        fnt = ImageFont.truetype(FONT, int(170 * s))
        txt = "А" * min(6, 1 + int(k * 4)) + "!"
        tw = d.textlength(txt, font=fnt)
        d.text(((W - tw) / 2, 650), txt, font=fnt, fill=(230, 0, 0), stroke_width=10, stroke_fill=(0, 0, 0))
        if k > 2.2:
            lw = d.textlength("ПРОДОЛЖЕНИЕ СЛЕДУЕТ...", font=f_small)
            d.text(((W - lw) / 2, 1000), "ПРОДОЛЖЕНИЕ СЛЕДУЕТ...", font=f_small, fill=(255, 255, 255))
        img = tint(img, (255, 0, 0), 0.2 * abs(math.sin(t * 15)))
        img = shake_img(img, 22 if k < 2.5 else 0, t)
        header(img, "СЛЫШЕН КРИК", None, col=(255, 60, 60))
    draw_subs(img, t)
    return img


if __name__ == "__main__":
    out, audio = sys.argv[2], sys.argv[3]
    if len(sys.argv) > 4:  # preview stills
        for ts in sys.argv[4].split(","):
            frame(float(ts)).save(f"{out}_{ts}.png")
        sys.exit()
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio,
                          "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    n = int(TOTAL * FPS)
    for i in range(n):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()
