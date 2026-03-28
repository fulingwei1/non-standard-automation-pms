#!/bin/bash

# Git hooks installation script
# Installs commit-msg and prepare-commit-msg hooks via symlink

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

# 安装单个 hook 的辅助函数：使用 symlink 而非 cp，已正确则跳过
install_hook() {
    local hook_name=$1
    local source="$HOOKS_DIR/$hook_name"
    local target="$GIT_HOOKS_DIR/$hook_name"

    if [ ! -f "$source" ]; then
        echo "⚠️  Warning: $hook_name not found in $HOOKS_DIR — skipped"
        return
    fi

    # 如果 symlink 已指向正确目标，跳过
    if [ -L "$target" ] && [ "$(readlink "$target")" = "$source" ]; then
        echo "✅ $hook_name already installed (symlink up to date)"
        return
    fi

    # 如果存在旧文件/symlink，先移除
    [ -e "$target" ] || [ -L "$target" ] && rm -f "$target"

    ln -s "$source" "$target"
    chmod +x "$source"
    echo "✅ $hook_name installed (symlinked)"
}

install_hook "prepare-commit-msg"
install_hook "commit-msg"

echo ""
echo "✨ Git hooks installation complete!"
echo ""
echo "The following hooks are now active:"
echo "  - prepare-commit-msg: Auto-normalizes commit message formatting"
echo "  - commit-msg: Validates conventional commit message format"
echo ""
echo "See docs/COMMIT_MESSAGE_GUIDE.md for commit message guidelines."
