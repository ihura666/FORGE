#!/usr/bin/env bash

set -euo pipefail

PROGRAM="FORGE"
VERSION="1.0.0"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_BINARY="$SOURCE_DIR/FORGE"
TARGET="$INSTALL_DIR/$PROGRAM"

if [[ ! -f "$SOURCE_BINARY" ]]; then
    echo "Error: FORGE binary not found."
    exit 1
fi

mkdir -p "$INSTALL_DIR"

cp "$SOURCE_BINARY" "$TARGET"
chmod 755 "$TARGET"

echo
echo "FORGE $VERSION installed."
echo "Location: $TARGET"
echo

if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo "NOTE: $INSTALL_DIR is not currently in PATH."
    echo "Add it with:"
    echo
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo
echo "Verify with:"
echo
echo "    $TARGET --version"
