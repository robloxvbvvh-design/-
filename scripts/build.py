"""Собирает караоке-субтитры: words.json, subtitles.ass, subtitles.srt.

Тайминги слов берутся из words_raw.json (распознавание GigaAM v2 через sherpa-onnx),
а отображаемый текст с пунктуацией — из SCRIPT ниже (слово в слово, "|" = новая строка).
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

SCRIPT = """
Ты Тимофей, и ты попал | в девяностые. | Сразу говоришь: | «Это моя старая квартира… | Где я?» |
Приходит мама и говорит: | «Привет! Иди за хлебом». |
Тимофей офигел: | «Где я?!» | Окей. | Видишь своих старых друзей. |
Видишь фото, что президент — | Борис Ельцин. |
Ты идёшь за хлебом, | отдаёшь копейку | и ты говоришь: | «Где я? В девяностых?!» |
И сразу забежишь… | Вы играете с друзьями. | Ты говоришь: «Я~ху! | Классно!» |
Говорят, что через два дня, | в третий день | откроется портал. |
Ты заходишь в компьютер, | играешь в змейку. | Тебе нравится это время. |
СССР только распался… | Ты спишь.
"""

# 1080x1920 (вертикальное видео)
W, H = 1080, 1920


def load():
    raw = json.loads((ROOT / "words_raw.json").read_text())
    lines, cur = [], []
    for tok in SCRIPT.split():
        if tok == "|":
            lines.append(cur)
            cur = []
        elif tok in ("—",):
            cur[-1] += " —"
        else:
            cur.append(tok)
    if cur:
        lines.append(cur)
    # "~" склеивает два распознанных слова в одно отображаемое ("Я~ху!" -> "Я-ху!")
    flat = [w for l in lines for w in l]
    assert sum(1 + w.count("~") for w in flat) == len(raw), (len(flat), len(raw))
    out, i = [], 0
    for l in lines:
        words = []
        for text in l:
            n = 1 + text.count("~")
            words.append({"text": text.replace("~", "-"), "start": raw[i]["s"], "end": raw[i + n - 1]["e"]})
            i += n
        out.append({"start": words[0]["start"], "end": words[-1]["end"], "words": words})
    # строка держится на экране до начала следующей (но не дольше 0.6 с после конца)
    for a, b in zip(out, out[1:]):
        a["end"] = round(min(b["start"], a["end"] + 0.6), 2)
    out[-1]["end"] = round(out[-1]["end"] + 1.0, 2)
    return out


def ts_ass(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02}:{cs // 100 % 60:02}.{cs % 100:02}"


def ts_srt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def build_ass(lines):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Russo One,78,&H00FFFFFF,&H000000FF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,6,4,5,70,70,0,204

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    pos = rf"\an5\pos({W // 2},{int(H * 0.62)})"
    for line in lines:
        ws = line["words"]
        # момент до первого слова (если строка появилась раньше) — всё белым
        for k, w in enumerate(ws):
            s = line["start"] if k == 0 else w["start"]
            e = ws[k + 1]["start"] if k + 1 < len(ws) else line["end"]
            parts = []
            for j, x in enumerate(ws):
                if j == k:
                    # активное слово: красное, с «вспышкой» масштаба и свечением
                    parts.append(
                        r"{\c&H2A2AFF&\3c&H00002A&\fscx118\fscy118"
                        r"\t(0,120,\fscx108\fscy108)}" + x["text"] + r"{\r}"
                    )
                else:
                    parts.append(x["text"])
            text = "{" + pos + r"\fad(0,0)}" + " ".join(parts)
            ev.append(f"Dialogue: 0,{ts_ass(s)},{ts_ass(e)},Sub,,0,0,0,,{text}")
    return head + "\n".join(ev) + "\n"


def build_srt(lines):
    out = []
    for n, line in enumerate(lines, 1):
        text = " ".join(w["text"] for w in line["words"])
        out.append(f"{n}\n{ts_srt(line['start'])} --> {ts_srt(line['end'])}\n{text}\n")
    return "\n".join(out)


if __name__ == "__main__":
    lines = load()
    (ROOT / "words.json").write_text(json.dumps(lines, ensure_ascii=False, indent=1))
    (ROOT / "subtitles.ass").write_text(build_ass(lines))
    (ROOT / "subtitles.srt").write_text(build_srt(lines))
    print(f"{len(lines)} строк, {sum(len(l['words']) for l in lines)} слов")
