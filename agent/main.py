"""Ночной агент: залетевшие видео → сценарии и раскадровка → озвучка.

Запуск: python -m agent.main
Результат: output/ГГГГ-ММ-ДД/
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic
import yaml

from agent import trends, voice, writer

ROOT = Path(__file__).resolve().parent.parent


def slug(text: str) -> str:
    return re.sub(r"[^\w]+", "-", text.lower()).strip("-")[:50] or "idea"


def cell(text: str) -> str:
    return str(text).replace("|", "/").replace("\n", " ")


def render_idea(i: int, idea: dict, audio: str | None) -> str:
    lines = [
        f"# {i}. {idea['title']}", "",
        f"**Хук:** {idea['hook']}", "",
        f"**Почему залетит:** {idea['why_it_works']}", "",
    ]
    if idea["inspired_by"]:
        lines += ["**Вдохновлено:** " + ", ".join(idea["inspired_by"]), ""]
    if audio:
        lines += [f"**Озвучка:** [{audio}]({audio})", ""]
    lines += ["## Раскадровка", "",
              "| # | Время | Кадр | Текст на экране | Голос | Звук |",
              "|---|---|---|---|---|---|"]
    for s in idea["storyboard"]:
        lines.append(f"| {s['n']} | {cell(s['seconds'])} | {cell(s['visual'])} | "
                     f"{cell(s['on_screen_text'])} | {cell(s['voiceover'])} | {cell(s['sound'])} |")
    lines += ["", "## Текст озвучки целиком", "", voice.voiceover_text(idea), "",
              "## Описание к публикации", "", idea["caption"], "",
              " ".join("#" + h.lstrip("#") for h in idea["hashtags"]), ""]
    return "\n".join(lines)


def main() -> int:
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    client = anthropic.Anthropic()
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = ROOT / "output" / day
    out.mkdir(parents=True, exist_ok=True)

    # 1. Ищем залетевшие видео
    yt_key = os.environ.get("YOUTUBE_API_KEY")
    if yt_key:
        print("Ищу залетевшие видео на YouTube…")
        videos = trends.fetch_youtube(cfg, yt_key)
        (out / "videos.json").write_text(json.dumps(videos, ensure_ascii=False, indent=2), "utf-8")
        research = json.dumps(videos, ensure_ascii=False, indent=1)
        print(f"Найдено {len(videos)} видео")
    else:
        print("YOUTUBE_API_KEY не задан — ищу через веб-поиск Claude…")
        research = trends.fetch_via_web_search(cfg, client)
        (out / "videos.md").write_text(research, "utf-8")

    # 2. Сценарии и раскадровка
    print("Пишу сценарии и раскадровку…")
    result = writer.write_scripts(cfg, client, research)
    (out / "scripts.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")

    # 3. Озвучка
    index = [f"# Идеи на {day}", "", "## Что сейчас залетает", "", result["trend_summary"], "",
             "## Сценарии", ""]
    for i, idea in enumerate(result["ideas"], 1):
        name = f"{i:02d}-{slug(idea['title'])}"
        audio = f"{name}.mp3"
        print(f"Озвучиваю: {idea['title']}")
        try:
            voice.synthesize(voice.voiceover_text(idea), out / audio, cfg["voice"], cfg["voice_rate"])
        except Exception as e:  # озвучка не должна ронять всю ночь работы
            print(f"  озвучка не удалась: {e}", file=sys.stderr)
            audio = None
        (out / f"{name}.md").write_text(render_idea(i, idea, audio), "utf-8")
        index.append(f"{i}. [{idea['title']}]({name}.md)" + (f" — 🔊 [{audio}]({audio})" if audio else ""))

    (out / "README.md").write_text("\n".join(index) + "\n", "utf-8")
    print(f"Готово: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
