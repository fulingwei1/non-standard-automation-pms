#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码质量快速修复脚本
"""

import subprocess
from pathlib import Path


def fix_whitespace_issues(file_path: Path):
    """修复空白行空格问题"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 修复空白行包含空格的问题
        lines = content.split("\n")
        fixed_lines = []

        for line in lines:
            # 如果是空行或只包含空白字符，则完全清空
            if line.strip() == "":
                fixed_lines.append("")
            else:
                # 修复行尾空格
                fixed_lines.append(line.rstrip())

        # 确保文件以换行符结尾
        fixed_content = "\n".join(fixed_lines)
        if not fixed_content.endswith("\n"):
            fixed_content += "\n"

        # 写回文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(fixed_content)

        return True
    except Exception as e:
        print(f"修复文件 {file_path} 失败: {e}")
        return False


def remove_unused_imports(file_path: Path):
    """简单移除明显的未使用导入"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 移除常见的未使用导入
        unused_imports = [
            "from typing import Optional",
            "from typing import Any",
            "from typing import List, Dict",
            "from typing import Union",
        ]

        modified = False
        for unused in unused_imports:
            if unused in content:
                # 检查是否真的未使用
                import_name = unused.split(" import ")[1].strip()
                if import_name not in content.replace(unused, ""):
                    content = content.replace(unused + "\n", "")
                    modified = True

        if modified:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"修复导入 {file_path} 失败: {e}")
        return False


def fix_line_length(file_path: Path):
    """修复行长度问题"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        fixed_lines = []
        modified = False

        for line in lines:
            if len(line) > 120:
                # 简单的行长度修复：在逗号后换行
                if "," in line and not line.strip().startswith("#"):
                    # 分割长行
                    parts = line.split(",")
                    if len(parts) > 1:
                        indent = len(line) - len(line.lstrip())
                        new_lines = []
                        for i, part in enumerate(parts):
                            if i == 0:
                                new_lines.append(part.rstrip())
                            else:
                                new_lines.append(" " * (indent + 4) + part.strip())
                        fixed_lines.extend(new_lines)
                        modified = True
                        continue
            fixed_lines.append(line)

        if modified:
            content = "\n".join(fixed_lines)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False
    except Exception as e:
        print(f"修复行长度 {file_path} 失败: {e}")
        return False


def run_autopep8():
    """运行 autopep8 自动格式化"""
    try:
        # 安装 autopep8
        subprocess.run(["pip", "install", "autopep8"], capture_output=True, check=True)

        # 运行 autopep8
        result = subprocess.run(
            ["python3", "-m", "autopep8", "--in-place", "--max-line-length=120", "app/"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ autopep8 格式化完成")
            return True
        else:
            print(f"❌ autopep8 失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ autopep8 安装失败: {e}")
        return False


def main():
    """主函数"""
    print("🔧 开始快速修复...")

    project_root = Path(__file__).parent.parent
    app_dir = project_root / "app"

    fixed_files = 0

    # 修复所有Python文件
    for file_path in app_dir.rglob("*.py"):
        if "migrations" in str(file_path):
            continue

        # 修复空白行问题
        if fix_whitespace_issues(file_path):
            fixed_files += 1

        # 移除未使用导入
        if remove_unused_imports(file_path):
            fixed_files += 1

        # 修复行长度
        if fix_line_length(file_path):
            fixed_files += 1

    print(f"✅ 手动修复完成: {fixed_files} 个文件")

    # 运行 autopep8
    if run_autopep8():
        print("✅ 自动格式化完成")

    print("🎉 快速修复完成！")
    print("💡 建议运行 'python3 -m flake8 app/' 检查修复效果")


if __name__ == "__main__":
    main()
