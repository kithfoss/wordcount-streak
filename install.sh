#!/usr/bin/env bash
# Install wordcount-streak as `wcs` on your PATH.
# Creates a symlink in ~/.local/bin (added to PATH on most systems).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL="$SCRIPT_DIR/wordcount_streak.py"
BIN_DIR="$HOME/.local/bin"
LINK="$BIN_DIR/wcs"

chmod +x "$TOOL"
mkdir -p "$BIN_DIR"

if [ -L "$LINK" ] || [ -f "$LINK" ]; then
    echo "Updating existing link at $LINK"
    rm "$LINK"
fi

ln -s "$TOOL" "$LINK"
echo "Installed: $LINK → $TOOL"
echo ""

# Check PATH
if echo "$PATH" | grep -q "$BIN_DIR"; then
    echo "✓ $BIN_DIR is already on your PATH."
    echo "  Run: wcs <file-or-dir>"
else
    echo "⚠  $BIN_DIR is not on your PATH."
    echo "   Add this to your shell profile (.bashrc or .zshrc):"
    echo ""
    echo '   export PATH="$HOME/.local/bin:$PATH"'
    echo ""
    echo "   Then reload: source ~/.bashrc (or ~/.zshrc)"
fi
