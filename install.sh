#!/bin/bash
# Install chlz-parse skill for Claude Code
# Usage: bash install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

# Ensure target directories exist
mkdir -p "$CLAUDE_DIR/commands"
mkdir -p "$CLAUDE_DIR/scripts"

# Symlink command
ln -sf "$SCRIPT_DIR/commands/chlz-parse.md" "$CLAUDE_DIR/commands/chlz-parse.md"

# Symlink script
ln -sf "$SCRIPT_DIR/scripts/chlz_parse.py" "$CLAUDE_DIR/scripts/chlz_parse.py"

echo "chlz-parse skill installed."
echo "  command: $CLAUDE_DIR/commands/chlz-parse.md -> $(readlink "$CLAUDE_DIR/commands/chlz-parse.md")"
echo "  script:  $CLAUDE_DIR/scripts/chlz_parse.py -> $(readlink "$CLAUDE_DIR/scripts/chlz_parse.py")"
echo ""
echo "Restart Claude Code to use /chlz-parse."
