#!/bin/bash

# Git hooks installation script
# 使用符号链接安装 hooks，更新 hooks/ 目录下的文件后无需重新运行

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
HOOKS_DIR="$PROJECT_ROOT/hooks"
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "Installing Git hooks..."

# Check if .git directory exists
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "Error: .git directory not found. Are you in a Git repository?"
    exit 1
fi

# Check if hooks directory exists
if [ ! -d "$HOOKS_DIR" ]; then
    echo "Error: hooks directory not found at $HOOKS_DIR"
    exit 1
fi

# 确保 .git/hooks 目录存在
mkdir -p "$GIT_HOOKS_DIR"

# install_hook: 为单个 hook 创建符号链接（幂等，已有同链接则跳过）
install_hook() {
    local hook_name="$1"
    local source="$HOOKS_DIR/$hook_name"
    local target="$GIT_HOOKS_DIR/$hook_name"

    if [ ! -f "$source" ]; then
        echo "Warning: $hook_name not found in $HOOKS_DIR, skipping"
        return
    fi

    # 确保源文件可执行
    chmod +x "$source"

    # 如果目标已经是指向正确位置的符号链接，跳过
    if [ -L "$target" ] && [ "$(readlink "$target")" = "$source" ]; then
        echo "  $hook_name: already linked, skipping"
        return
    fi

    # 如果目标已存在（普通文件或指向其他位置的链接），备份后替换
    if [ -e "$target" ] || [ -L "$target" ]; then
        local backup="${target}.bak.$(date +%Y%m%d%H%M%S)"
        mv "$target" "$backup"
        echo "  $hook_name: backed up existing hook to $(basename "$backup")"
    fi

    ln -s "$source" "$target"
    echo "  $hook_name: linked"
}

echo "Installing hooks via symlinks..."
# 安装 hooks/ 目录下所有可执行 hook 文件
for hook_file in "$HOOKS_DIR"/*; do
    [ -f "$hook_file" ] || continue
    install_hook "$(basename "$hook_file")"
done

echo ""
echo "Git hooks installation complete!"
echo ""
echo "The following hooks are now active:"
echo "  - commit-msg: Validates conventional commit message format"
echo ""
echo "Hooks are symlinked from hooks/ directory."
echo "Edits to hooks/ take effect immediately without re-running this script."
echo ""
echo "See docs/COMMIT_MESSAGE_GUIDE.md for commit message guidelines."
