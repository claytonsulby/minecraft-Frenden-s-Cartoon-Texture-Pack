#!/usr/bin/env bash
set -euo pipefail

PACK_NAME=${1:-Frenden-Remix-1.21.11}
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RESOURCE_DIR="$HOME/Library/Application Support/minecraft/resourcepacks"
TARGET_DIR="$RESOURCE_DIR/$PACK_NAME"

mkdir -p "$RESOURCE_DIR"
rm -rf "$TARGET_DIR"
mkdir -p "$TARGET_DIR"

entries=(
  assets
  pack.mcmeta
  pack.png
)

for entry in "${entries[@]}"; do
  SOURCE_PATH="$ROOT_DIR/$entry"
  DEST_PATH="$TARGET_DIR/$entry"

  if [ -d "$SOURCE_PATH" ]; then
    mkdir -p "$DEST_PATH"
    rsync -a --delete "$SOURCE_PATH/" "$DEST_PATH/"
  elif [ -f "$SOURCE_PATH" ]; then
    mkdir -p "$(dirname "$DEST_PATH")"
    cp "$SOURCE_PATH" "$DEST_PATH"
  fi
done

echo "Deployed pack '$PACK_NAME' to $TARGET_DIR"
