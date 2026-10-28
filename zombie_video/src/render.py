import json, math, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
AUDIO_END = 34.35
SCREAM_AT = 34.7
TOTAL = 38.6
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FONT_B = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
f_sub = ImageFont.truetype(FONT, 84)
f_head = ImageFont.truetype(FONT, 76)
f_small = ImageFont.truetype(FONT_B, 40)
f_phone = ImageFont.truetype(FONT, 46)
f_big = ImageFont.truetype(FONT, 150)

# ---------------- subtitles ----------------
words = json.load(open(sys.argv[1]))
fix = {2: "Дима,", 11: "ТикТока,", 13: "по рации", 16: "зомби-апокалипсис!", 18: "паникуют.",
       20: "единственный...", 21: "Первые", 23: "советов.", 24: "Первое:", 25: "забаррикадируйте",
       27: "двери.", 30: "водитель —", 31: "сам", 32: "забаррикадируй", 34: "двери.", 35: "Второе:",
       38: "оружие,", 44: "купе,", 46: "оружие.", 47: "Третье:", 50: "прорвались —",
       52: "защищайтесь!", 53: "Четвёртое:", 55: "спасения.", 60: "ты."}
for i, w in enumerate(words):
    w["t"] = fix.get(i, w["w"]).upper()
for i, w in enumerate(words):
    nxt = words[i + 1]["s"] if i + 1 < len(words) else AUDIO_END
    w["e"] = min(nxt, w["s"] + 0.95)
words.append({"t": "ПЯТОЕ:", "s": SCREAM_AT - 0.4, "e": SCREAM_AT + 0.6})
words.append({"t": "СЛЫШЕН КРИК...", "s": SCREAM_AT + 0.6, "e": TOTAL})

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


# ---------------- compartment background ----------------
def compartment(t, alarm=0.0, door_state=0.0, planks=0, shake=0.0):
    img = Image.new("RGB", (W, H), (25, 25, 30))
    d = ImageDraw.Draw(img)
    # wall
    d.rectangle([0, 230, W, 1330], fill=(214, 196, 160))
    d.rectangle([0, 1330, W, 1420], fill=(100, 72, 52))
    for k in range(0, W, 90):
        d.line([(k, 1330), (k - 40, 1420)], fill=(85, 60, 44), width=4)
    # window with moving landscape
    wx0, wy0, wx1, wy1 = 230, 340, 820, 720
    sky = (120, 170, 220) if alarm < 0.5 else (90, 60, 80)
    d.rectangle([wx0, wy0, wx1, wy1], fill=sky)
    d.rectangle([wx0, 610, wx1, wy1], fill=(70, 120, 60))
    off = (t * 900) % 260
    for k in range(-1, 4):
        tx = wx1 - off - k * 260 + 260
        if wx0 - 60 < tx < wx1 + 60:
            d.polygon([(tx, 470), (tx - 50, 610), (tx + 50, 610)], fill=(30, 90, 40))
            d.rectangle([tx - 8, 610, tx + 8, 640], fill=(80, 50, 30))
    off2 = (t * 1800) % 700
    px = wx1 - off2 + 100
    if wx0 < px < wx1:
        d.rectangle([px, 380, px + 14, 720], fill=(60, 60, 60))
    d.rectangle([wx0 - 18, wy0 - 18, wx1 + 18, wy1 + 18], outline=(90, 90, 100), width=22)
    d.line([(525, wy0), (525, wy1)], fill=(90, 90, 100), width=10)
    # curtains
    d.polygon([(wx0 - 30, wy0 - 30), (wx0 + 70, wy0 - 30), (wx0 + 20, wy1 + 30), (wx0 - 30, wy1 + 30)], fill=(180, 40, 50))
    d.polygon([(wx1 + 30, wy0 - 30), (wx1 - 70, wy0 - 30), (wx1 - 20, wy1 + 30), (wx1 + 30, wy1 + 30)], fill=(180, 40, 50))
    # table
    d.rectangle([380, 800, 700, 835], fill=(150, 110, 70))
    d.rectangle([520, 835, 560, 1330], fill=(110, 80, 50))
    d.rectangle([450, 770, 470, 800], fill=(230, 230, 240))  # glass
    # upper bunk (left)
    d.rectangle([0, 600, 330, 650], fill=(140, 40, 45))
    d.rectangle([0, 650, 330, 670], fill=(90, 70, 50))
    # lower bunk (left)
    d.rectangle([0, 1040, 360, 1110], fill=(160, 45, 50))
    d.rectangle([0, 1110, 360, 1330], fill=(110, 80, 55))
    # door (right)
    dx0, dy0, dx1, dy1 = 790, 520, 1060, 1330
    d.rectangle([dx0 - 12, dy0 - 12, dx1 + 12, dy1], fill=(70, 70, 80))
    if door_state < 1:
        d.rectangle([dx0, dy0, dx1, dy1], fill=(150, 110, 75))
        d.rectangle([dx0 + 40, dy0 + 60, dx1 - 40, dy0 + 330], fill=(200, 210, 220))
        d.text((dx0 + 95, dy0 + 150), "5", font=f_big, fill=(80, 80, 90))
        d.rectangle([dx0 + 20, 930, dx0 + 40, 1010], fill=(200, 190, 60))
        # cracks when breaking
        if door_state > 0:
            rnd = random.Random(3)
            for _ in range(int(door_state * 14)):
                a = (rnd.randint(dx0, dx1), rnd.randint(dy0, dy1))
                b = (a[0] + rnd.randint(-120, 120), a[1] + rnd.randint(-120, 120))
                d.line([a, b], fill=(40, 25, 15), width=6)
    else:
        d.rectangle([dx0, dy0, dx1, dy1], fill=(15, 15, 18))
        d.polygon([(dx0, dy0), (dx0 + 70, dy0 + 40), (dx0 + 70, dy1 - 40), (dx0, dy1)], fill=(120, 85, 60))
    # planks
    rnd = random.Random(7)
    for k in range(planks):
        y = dy0 + 90 + k * 150
        tilt = rnd.uniform(-60, 60)
        fall = 0
        if door_state >= 1:
            fall = 1
        if fall:
            y2 = 1300 - k * 20
            d.polygon([(dx0 - 60 - k * 30, y2), (dx1 + 20 - k * 30, y2 + 10), (dx1 + 20 - k * 30, y2 + 50), (dx0 - 60 - k * 30, y2 + 40)], fill=(170, 120, 60))
        else:
            d.polygon([(dx0 - 40, y - tilt), (dx1 + 40, y + tilt), (dx1 + 40, y + tilt + 55), (dx0 - 40, y - tilt + 55)],
                      fill=(175, 125, 65), outline=(110, 70, 30))
            for nx in (dx0 - 10, dx1 + 10):
                d.ellipse([nx - 7, y + 20 - 7, nx + 7, y + 20 + 7], fill=(70, 70, 70))
    # lamp
    lamp_col = (255, 245, 200)
    if alarm > 0 and int(t * 4) % 2 == 0:
        lamp_col = (255, 30, 30)
    d.rounded_rectangle([420, 250, 660, 290], 15, fill=lamp_col)
    return img


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


def big_phone(img, t, alert_t):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 290, 330, 790, 1330
    d.rounded_rectangle([x0 - 4, y0 - 4, x1 + 4, y1 + 4], 60, fill=(80, 80, 90))
    d.rounded_rectangle([x0, y0, x1, y1], 56, fill=(10, 10, 12))
    sx0, sy0, sx1, sy1 = x0 + 24, y0 + 70, x1 - 24, y1 - 50
    # tiktok-like feed scrolling
    scroll = (t * 500) % 900
    cols = [(255, 80, 120), (60, 200, 220), (250, 190, 50), (130, 90, 230)]
    for k in range(4):
        yy = sy0 - scroll + k * 900
        d.rectangle([sx0, max(sy0, yy), sx1, min(sy1, yy + 880)], fill=cols[k % 4]) if yy + 880 > sy0 and yy < sy1 else None
    d.text((sx0 + 30, sy1 - 120), "@dima_vagon5", font=f_small, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
    for k in range(3):
        d.ellipse([sx1 - 90, sy0 + 280 + k * 130, sx1 - 30, sy0 + 340 + k * 130], fill=(255, 255, 255))
    d.rounded_rectangle([x0 + 190, y0 + 22, x1 - 190, y0 + 46], 12, fill=(0, 0, 0))
    if t >= alert_t:
        a = ease((t - alert_t) / 0.3)
        bx0, by0 = sx0 + 20, sy0 + 220 - (1 - a) * 300
        flash = int(t * 5) % 2 == 0
        d.rounded_rectangle([bx0, by0, sx1 - 20, by0 + 420], 30, fill=(220, 0, 0) if flash else (170, 0, 0),
                            outline=(255, 255, 255), width=6)
        d.polygon([(W / 2, by0 + 30), (W / 2 - 55, by0 + 125), (W / 2 + 55, by0 + 125)], fill=(255, 220, 0))
        d.text((W / 2 - 10, by0 + 50), "!", font=f_phone, fill=(0, 0, 0))
        for i, line in enumerate(["ТРЕВОГА!", "НАЧАЛСЯ", "ЗОМБИ-", "АПОКАЛИПСИС"]):
            lw = d.textlength(line, font=f_phone)
            d.text(((W - lw) / 2, by0 + 145 + i * 62), line, font=f_phone, fill=(255, 255, 255))


def radio_bubble(img, t):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([60, 1360, 520, 1480], 30, fill=(255, 255, 255), outline=(0, 0, 0), width=6)
    d.polygon([(120, 1360), (160, 1360), (110, 1320)], fill=(255, 255, 255))
    # radio icon
    d.rounded_rectangle([85, 1385, 155, 1460], 10, fill=(40, 40, 40))
    d.line([(140, 1385), (150, 1335)], fill=(40, 40, 40), width=8)
    for k in range(3):
        if int(t * 6 + k) % 3 != 0:
            d.arc([160 - k * 0 + k * 18, 1395 - k * 12, 200 + k * 30, 1455 + k * 12], -50, 50, fill=(220, 0, 0), width=5)
    d.text((285, 1390), "РАЦИЯ:", font=f_small, fill=(0, 0, 0))
    d.text((285, 1432), "ш-ш-ш...", font=f_small, fill=(120, 120, 120))


# ---------------- scene timeline ----------------
T_ALERT = 5.3      # "по рации"
T_PANIC = 8.8      # "все паникуют"
T_TITLE = 10.1     # "ты единственный ... пять советов"
T_S1 = 13.45       # первое
T_S2 = 19.85       # второе
T_CLIMB = 22.4     # заберитесь
T_S3 = 25.95       # третье
T_BREAK = 27.4     # прорвались
T_S4 = 29.8        # четвёртое


def frame(t):
    if t < T_PANIC:
        if t < T_ALERT:
            img = compartment(t)
            d = ImageDraw.Draw(img)
            hands, _ = person(d, (200, 1035), sitting=True, arm_l=60, arm_r=40, fore_l=-40, fore_r=-30)
            phone_small(d, (hands[0][0] + 20, hands[0][1] - 40), t=t)
            header(img, "ВАГОН №5", "Дима листает ТикТок")
        else:
            img = compartment(t, alarm=1.0)
            img = tint(img, (0, 0, 0), 0.45)
            big_phone(img, t, T_ALERT + 0.9)
            radio_bubble(img, t)
            header(img, "ВНИМАНИЕ!", None, col=(255, 60, 60))
    elif t < T_TITLE:
        img = compartment(t, alarm=1.0)
        d = ImageDraw.Draw(img)
        jump = abs(math.sin(t * 10)) * 30
        person(d, (200, 1035 - jump), sitting=True, arm_l=-120, arm_r=-60, fore_l=-120, fore_r=-60, face="scared")
        img = tint(img, (255, 0, 0), 0.25 + 0.15 * math.sin(t * 20))
        img = shake_img(img, 18, t)
        header(img, "ВСЕ ПАНИКУЮТ!", None, col=(255, 60, 60))
    elif t < T_S1:
        img = compartment(t, alarm=1.0)
        img = tint(img, (0, 0, 0), 0.6)
        d = ImageDraw.Draw(img)
        a = ease((t - T_TITLE - 1.3) / 0.4)
        if t > T_TITLE + 1.3:
            s = 0.6 + 0.4 * a
            fnt = ImageFont.truetype(FONT, int(300 * s))
            tw = d.textlength("5", font=fnt)
            d.text(((W - tw) / 2, 380), "5", font=fnt, fill=(255, 40, 40), stroke_width=12, stroke_fill=(0, 0, 0))
            for i, line in enumerate(["СОВЕТОВ", "КАК ВЫЖИТЬ"]):
                lw = d.textlength(line, font=f_head)
                d.text(((W - lw) / 2, 760 + i * 100), line, font=f_head, fill=(255, 255, 255), stroke_width=6, stroke_fill=(0, 0, 0))
        else:
            hands, _ = person(d, (540, 1130), s=1.2, arm_l=100, arm_r=80, face="angry")
            lw = d.textlength("ТЫ ОДИН", font=f_head)
            d.text(((W - lw) / 2, 380), "ТЫ ОДИН", font=f_head, fill=(255, 210, 0), stroke_width=6, stroke_fill=(0, 0, 0))
    elif t < T_S2:
        p = (t - T_S1) / (T_S2 - T_S1)
        planks = min(5, int(p * 6.5))
        img = compartment(t, planks=planks)
        d = ImageDraw.Draw(img)
        hammer = math.sin(t * 14) * 35
        person(d, (650, 1130), arm_l=200, arm_r=-30 + hammer, fore_r=-80 + hammer, face="angry")
        hd = pt(pt(pt((650, 1130), -90, 170), 90, 20), -30 + hammer, 70)
        hd = pt(hd, -80 + hammer, 65)
        hx, hy = hd
        d.line([(hx, hy), (hx + 30, hy - 40)], fill=(110, 70, 30), width=12)
        d.rectangle([hx + 10, hy - 60, hx + 60, hy - 35], fill=(90, 90, 100))
        header(img, "СОВЕТ №1", "Забаррикадируй все двери")
    elif t < T_S3:
        img = compartment(t, planks=5)
        d = ImageDraw.Draw(img)
        if t < T_CLIMB:
            # grabbing the hockey stick
            g = ease((t - T_S2) / 1.0)
            hands, _ = person(d, (420, 1130), arm_l=120, arm_r=-60 * g + 60, fore_r=-100 * g + 60, face="angry")
            hockey_stick(d, hands[1], -100 + 60 * (1 - g))
        else:
            c = ease((t - T_CLIMB) / 1.0)
            hip = (420 - 230 * c, 1130 - (1130 - 600) * c)
            if c < 1:
                hands, _ = person(d, hip, arm_l=-100, arm_r=-80, face="angry")
                hockey_stick(d, hands[1], -60)
            else:
                hands, _ = person(d, (170, 598), sitting=True, arm_l=40, arm_r=20, fore_l=-10, fore_r=-30, face="angry")
                hockey_stick(d, hands[1], -20 + math.sin(t * 3) * 6)
        # mattress / blanket barricade on the bunk edge
        header(img, "СОВЕТ №2", "Бери оружие и лезь наверх")
    elif t < T_S4:
        broke = ease((t - (T_BREAK - 0.6)) / 0.6)
        door_state = 1.0 if t >= T_BREAK else broke * 0.9
        img = compartment(t, planks=5, door_state=door_state, alarm=1.0 if t >= T_BREAK else 0)
        d = ImageDraw.Draw(img)
        swing = 0.5 + 0.5 * math.sin(t * 9)
        if t >= T_BREAK:
            for k, (zx, ph) in enumerate(((760, 0), (920, 2.0), (640, 4.0))):
                enter = ease((t - T_BREAK - k * 0.35) / 0.8)
                if enter <= 0: continue
                x = 1150 - (1150 - zx) * enter
                hit = max(0.0, math.sin(t * 9 + ph)) if k == 2 else 0.0
                zombie(d, (x, 1130), 1.0, t, ph, hit)
        hands, _ = person(d, (170, 598), sitting=True, arm_l=-60 + 120 * swing, arm_r=-80 + 120 * swing,
                          fore_l=-60 + 120 * swing, fore_r=-80 + 120 * swing, face="angry")
        hockey_stick(d, hands[1], -80 + 130 * swing)
        if t >= T_BREAK and swing > 0.85:
            d.text((560, 820), "БАМ!", font=f_head, fill=(255, 230, 0), stroke_width=8, stroke_fill=(200, 0, 0))
        if t >= T_BREAK:
            img = shake_img(img, 10 * swing, t)
        header(img, "СОВЕТ №3", "Зомби прорвались — защищайся!", col=(255, 60, 60))
    elif t < AUDIO_END + 0.3:
        img = compartment(t, planks=5, door_state=1.0)
        d = ImageDraw.Draw(img)
        for k, x in enumerate((700, 880, 560)):
            person(d, (x, 1350 - k * 15), lying=True, s=0.8, skin=(130, 180, 110), shirt=(90, 80, 70), pants=(50, 60, 80))
        hands, _ = person(d, (380, 1130), arm_l=-120, arm_r=60, face="happy")
        hockey_stick(d, hands[0], -100)
        # clock: waiting
        cx, cy = 900, 420
        d.ellipse([cx - 80, cy - 80, cx + 80, cy + 80], fill=(255, 255, 255), outline=(0, 0, 0), width=8)
        d.line([(cx, cy), pt((cx, cy), -90 + t * 360, 60)], fill=(0, 0, 0), width=6)
        d.line([(cx, cy), pt((cx, cy), -90 + t * 30, 40)], fill=(0, 0, 0), width=8)
        header(img, "СОВЕТ №4", "Жди спасения. Ты — один живой", col=(80, 255, 120))
    else:
        img = compartment(t, planks=5, door_state=1.0)
        d = ImageDraw.Draw(img)
        person(d, (380, 1130), arm_l=-120, arm_r=-60, face="scared")
        dark = ease((t - AUDIO_END - 0.3) / 0.4)
        img = tint(img, (0, 0, 0), 0.88 * dark)
        if t >= SCREAM_AT:
            d = ImageDraw.Draw(img)
            k = (t - SCREAM_AT)
            s = 1 + 0.08 * math.sin(t * 40)
            fnt = ImageFont.truetype(FONT, int(170 * s))
            txt = "А" * min(6, 1 + int(k * 4)) + "!"
            tw = d.textlength(txt, font=fnt)
            d.text(((W - tw) / 2, 650), txt, font=fnt, fill=(230, 0, 0), stroke_width=10, stroke_fill=(0, 0, 0))
            img = tint(img, (255, 0, 0), 0.2 * abs(math.sin(t * 15)))
            img = shake_img(img, 22, t)
        header(img, "СОВЕТ №5", "Слышен крик...", col=(255, 60, 60))
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
