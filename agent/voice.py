"""Озвучка сценариев через edge-tts (бесплатно, без ключей)."""

import asyncio
from pathlib import Path

import edge_tts


def voiceover_text(idea: dict) -> str:
    return "\n".join(s["voiceover"].strip() for s in idea["storyboard"] if s["voiceover"].strip())


async def _synth(text: str, path: Path, voice: str, rate: str) -> None:
    await edge_tts.Communicate(text, voice, rate=rate).save(str(path))


def synthesize(text: str, path: Path, voice: str, rate: str) -> None:
    asyncio.run(_synth(text, path, voice, rate))
