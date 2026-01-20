#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件大小检查脚本

用于pre-commit hooks和CI检查
检查Python和JavaScript文件是否超过行数限制
"""

import os
import sys
from pathlib import Path


# 文件大小限制配置
LIMITS = {
    ".py": 500,  # Python文件最大500行
    ".js": 500,  # JavaScript文件最大500行
    ".jsx": 500,  # JSX文件最大500行
    ".ts": 500,  # TypeScript文件最大500行
    ".tsx": 500,  # TSX文件最大500行
    ".css": 300,  # CSS文件最大300行
}

# 排除的目录
EXCLUDE_DIRS = {
    "node_modules",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    ".git",
    "dist",
    "build",
    ".next",
    "migrations",
    "alembic",
}

# 排除的文件
EXCLUDE_FILES = {
    "__init__.py",  # 初始化文件可能较大（模型导出等）
}


def count_lines(file_path: Path) -> int:
    """计算文件行数"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def should_check(file_path: Path) -> bool:
    """判断是否应该检查该文件"""
    # 检查文件扩展名
    if file_path.suffix not in LIMITS:
        return False

    # 检查是否在排除目录中
    for part in file_path.parts:
        if part in EXCLUDE_DIRS:
            return False

    # 检查是否是排除的文件
    if file_path.name in EXCLUDE_FILES:
        return False

    return True


def check_files(root_dir: str, strict: bool = False) -> list:
    """检查所有文件"""
    violations = []

    for root, dirs, files in os.walk(root_dir):
        # 跳过排除的目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            file_path = Path(root) / file

            if not should_check(file_path):
                continue

            line_count = count_lines(file_path)
            limit = LIMITS.get(file_path.suffix, 500)

            if line_count > limit:
                violations.append(
                    {
                        "path": str(file_path),
                        "lines": line_count,
                        "limit": limit,
                        "over": line_count - limit,
                    }
                )

    return violations


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="检查文件大小限制")
    parser.add_argument(
        "--strict", action="store_true", help="严格模式，发现违规则退出"
    )
    parser.add_argument("--dir", default=".", help="检查目录")
    args = parser.parse_args()

    print("📏 检查文件大小限制...")
    print(f"   限制: Python/JS/JSX {LIMITS['.py']}行, CSS {LIMITS['.css']}行\n")

    violations = check_files(args.dir, args.strict)

    if violations:
        print(f"❌ 发现 {len(violations)} 个文件超过行数限制:\n")

        # 按超出行数排序
        violations.sort(key=lambda x: x["over"], reverse=True)

        for v in violations:
            print(f"  📄 {v['path']}")
            print(f"     行数: {v['lines']} (限制: {v['limit']}, 超出: +{v['over']}行)")
            print()

        print("💡 建议: 请参考 docs/CODE_STANDARDS.md 进行重构\n")

        if args.strict:
            sys.exit(1)
        else:
            return 1
    else:
        print("✅ 所有文件都在行数限制内\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
