"""Claude разбирает залетевшие видео и пишет сценарии с раскадровкой."""

import json

SCENE = {
    "type": "object",
    "properties": {
        "n": {"type": "integer"},
        "seconds": {"type": "string", "description": "таймкод, например 0-3"},
        "visual": {"type": "string", "description": "что в кадре, ракурс, движение камеры"},
        "on_screen_text": {"type": "string"},
        "voiceover": {"type": "string", "description": "что говорит диктор в этой сцене"},
        "sound": {"type": "string", "description": "музыка / звуковые эффекты"},
    },
    "required": ["n", "seconds", "visual", "on_screen_text", "voiceover", "sound"],
    "additionalProperties": False,
}

SCHEMA = {
    "type": "object",
    "properties": {
        "trend_summary": {"type": "string", "description": "какие паттерны общие у залетевших видео"},
        "ideas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "hook": {"type": "string", "description": "первые 1-3 секунды"},
                    "why_it_works": {"type": "string"},
                    "inspired_by": {"type": "array", "items": {"type": "string"}},
                    "storyboard": {"type": "array", "items": SCENE},
                    "caption": {"type": "string", "description": "описание к публикации"},
                    "hashtags": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["title", "hook", "why_it_works", "inspired_by",
                             "storyboard", "caption", "hashtags"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["trend_summary", "ideas"],
    "additionalProperties": False,
}

SYSTEM = (
    "Ты — креативный продюсер коротких вертикальных видео. Ты изучаешь, почему ролики "
    "залетают (хук, тема, эмоция, темп, формат), и придумываешь ОРИГИНАЛЬНЫЕ ролики на тех же "
    "механиках — не копии. Текст диктора пишешь живым разговорным языком, без воды, "
    "чтобы его было удобно озвучить синтезатором речи: без эмодзи, хештегов и сокращений в тексте озвучки."
)


def write_scripts(cfg: dict, client, research: str) -> dict:
    prompt = (
        f"Ниша канала: {cfg['niche']}. Язык: {cfg['language']}.\n\n"
        f"Вот видео, которые сейчас залетают:\n\n{research}\n\n"
        f"1. Кратко опиши, что общего у залетевших видео.\n"
        f"2. Придумай {cfg['ideas_per_night']} идеи для новых роликов длиной около "
        f"{cfg['target_duration_sec']} секунд. Для каждой — сценарий в виде раскадровки по сценам "
        f"(обычно 6-12 сцен), сильный хук в первые 3 секунды, описание и хештеги. "
        f"В inspired_by укажи ссылки на видео, на механиках которых построена идея."
    )
    with client.beta.messages.stream(
        model=cfg["model"],
        max_tokens=64000,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        output_config={"effort": cfg["effort"],
                       "format": {"type": "json_schema", "schema": SCHEMA}},
        # Если модель откажется отвечать, API сам повторит запрос на запасной модели
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        response = stream.get_final_message()

    if response.stop_reason == "refusal":
        raise RuntimeError(f"Модель отказалась: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Ответ обрезан по max_tokens — уменьши ideas_per_night")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)
