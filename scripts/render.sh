#!/usr/bin/env bash
# Рендер вертикального видео 1080x1920 с караоке-субтитрами (нужен ffmpeg с libass).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/build.py
ffmpeg -loglevel error -y \
  -f lavfi -i "gradients=s=1080x1920:c0=0x1a0f2e:c1=0x3a0b12:x0=0:y0=0:x1=1080:y1=1920:d=42:speed=0.002,format=yuv420p" \
  -i audio.mp3 \
  -vf "vignette=PI/4,ass=subtitles.ass:fontsdir=fonts" \
  -c:v libx264 -preset medium -crf 23 -tune stillimage -r 30 \
  -c:a aac -b:a 160k -shortest -movflags +faststart video.mp4
echo "готово: video.mp4"
