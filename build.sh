#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"

if [ ! -f maubot.yaml ]; then
  echo "Missing maubot.yaml" >&2
  exit 1
fi

id=$(grep -E '^[[:space:]]*id:' maubot.yaml | head -n1 | sed -E 's/^[[:space:]]*id:[[:space:]]*//')
version=$(grep -E '^[[:space:]]*version:' maubot.yaml | head -n1 | sed -E 's/^[[:space:]]*version:[[:space:]]*//')

if [ -z "$id" ] || [ -z "$version" ]; then
  echo "Could not read id and version from maubot.yaml" >&2
  exit 1
fi

mkdir -p build
OUT="build/${id}-v${version}.mbp"

if command -v mbc >/dev/null 2>&1; then
  echo "Using mbc build -> $OUT"
  if mbc build -o "$OUT"; then
    echo "Built: $(pwd)/$OUT"
    exit 0
  fi
  echo "mbc build failed; building $OUT manually." >&2
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
