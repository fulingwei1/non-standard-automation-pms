#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
函数大小检查脚本

检查Python函数是否超过行数限制
用于pre-commit hooks
"""

import ast
import os
import sys
from pathlib import Path


# 函数行数限制
MAX_FUNCTION_LINES = 50

# 排除的目录
EXCLUDE_DIRS = {
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    ".git",
    "migrations",
    "alembic",
}


class FunctionVisitor(ast.NodeVisitor):
    """AST访问器，用于分析函数"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.violations = []

    def visit_FunctionDef(self, node):
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._check_function(node)
        self.generic_visit(node)

    def _check_function(self, node):
        """检查函数大小"""
        # 计算函数行数
        if hasattr(node, "end_lineno"):
            lines = node.end_lineno - node.lineno + 1
        else:
            # 估算行数
            lines = len(ast.unparse(node).split("\n"))

        if lines > MAX_FUNCTION_LINES:
            self.violations.append(
                {
                    "file": self.file_path,
                    "function": node.name,
                    "lines": lines,
                    "line_no": node.lineno,
                    "over": lines - MAX_FUNCTION_LINES,
                }
            )


def check_file(file_path: Path) -> list:
    """检查单个文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        visitor = FunctionVisitor(str(file_path))
        visitor.visit(tree)
        return visitor.violations
    except SyntaxError:
        return []
    except Exception as e:
        print(f"警告: 无法解析 {file_path}: {e}")
        return []


def main():
    """主函数"""
    print(f"🔍 检查函数大小限制 (最大{MAX_FUNCTION_LINES}行)...\n")

    all_violations = []

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = Path(root) / file
            violations = check_file(file_path)
            all_violations.extend(violations)

    if all_violations:
        # 按超出行数排序
        all_violations.sort(key=lambda x: x["over"], reverse=True)

        print(f"⚠️ 发现 {len(all_violations)} 个函数超过限制:\n")

        # 只显示前20个
        for v in all_violations[:20]:
            print(f"  📄 {v['file']}:{v['line_no']}")
            print(f"     函数: {v['function']}()")
            print(f"     行数: {v['lines']} (超出: +{v['over']}行)")
            print()

        if len(all_violations) > 20:
            print(f"  ... 还有 {len(all_violations) - 20} 个函数\n")

        print("💡 建议: 将大函数拆分为多个小函数\n")

        # 不阻断提交，只是警告
        return 0
    else:
        print("✅ 所有函数都在行数限制内\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
