#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"

OUT="game-updates.mbp"

if command -v mbc >/dev/null 2>&1; then
  echo "Using mbc build..."
  if mbc build; then
    exit 0
  fi
  echo "mbc build failed; building game-updates.mbp manually." >&2
fi

for f in maubot.yaml bot.py; do
  if [ ! -f "$f" ]; then
    echo "Missing required file: $f" >&2
    exit 1
  fi
done

rm -f "$OUT"
zip -9 -q "$OUT" maubot.yaml bot.py
echo "Built: $(pwd)/$OUT"
