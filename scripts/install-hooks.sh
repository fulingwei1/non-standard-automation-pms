#!/bin/bash

# Git hooks installation script
# This script installs commit message validation hooks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HOOKS_DIR="$PROJECT_ROOT/hooks"
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "🔧 Installing Git hooks..."

# Check if .git directory exists
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "❌ Error: .git directory not found. Are you in a Git repository?"
    exit 1
fi

# Check if hooks directory exists
if [ ! -d "$HOOKS_DIR" ]; then
    echo "❌ Error: hooks directory not found at $HOOKS_DIR"
    exit 1
fi

# Install commit-msg hook
if [ -f "$HOOKS_DIR/commit-msg" ]; then
    echo "📝 Installing commit-msg hook..."
    cp "$HOOKS_DIR/commit-msg" "$GIT_HOOKS_DIR/commit-msg"
    chmod +x "$GIT_HOOKS_DIR/commit-msg"
    echo "✅ commit-msg hook installed"
else
    echo "⚠️  Warning: commit-msg hook not found in $HOOKS_DIR"
fi

echo ""
echo "✨ Git hooks installation complete!"
echo ""
echo "The following hooks are now active:"
echo "  - commit-msg: Validates conventional commit message format"
echo ""
echo "See docs/COMMIT_MESSAGE_GUIDE.md for commit message guidelines."
