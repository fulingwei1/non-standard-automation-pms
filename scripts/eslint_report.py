#!/usr/bin/env python3
"""
生成 eslint 报告摘要，方便逐步清理 lint 错误。

默认执行 `npx eslint src --format json`，解析结果后打印：
  1. 错误/警告总数
  2. Top N 文件（按错误+警告数排序）
  3. 每个文件的详细问题列表（按行号/规则排序）

使用示例：
    python scripts/eslint_report.py                            # 扫描 frontend/src
    python scripts/eslint_report.py src/pages/TaskCenter.jsx   # 指定路径
    python scripts/eslint_report.py --limit 5                  # 只显示前 5 个文件
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_TARGET = "src"


def run_eslint(paths: List[str]) -> List[Dict[str, Any]]:
    """执行 eslint，返回解析后的 JSON 列表。"""
    cmd = ["npx", "eslint", *paths, "--format", "json"]
    try:
        completed = subprocess.run(
            cmd,
            cwd=Path(__file__).resolve().parents[1] / "frontend",
            check=False,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise SystemExit(f"[ERROR] 无法运行 eslint：{exc}") from exc

    stdout = completed.stdout.strip()
    if not stdout:
        print(completed.stderr)
        raise SystemExit("[ERROR] eslint 输出为空，可能执行失败。")

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        print(stdout[:2000])
        raise SystemExit(f"[ERROR] 解析 eslint JSON 失败：{exc}") from exc

    return data


def summarize(results: List[Dict[str, Any]], top_n: int) -> None:
    """打印摘要。"""
    total_errors = sum(file["errorCount"] for file in results)
    total_warnings = sum(file["warningCount"] for file in results)
    print(f"Total Errors: {total_errors}, Warnings: {total_warnings}")

    # 统计每个文件问题数
    file_stats = []
    for file_result in results:
        issue_count = file_result["errorCount"] + file_result["warningCount"]
        if issue_count:
            rel_path = file_result["filePath"].split("/front end/")[-1]
            file_stats.append((issue_count, rel_path, file_result))

    file_stats.sort(reverse=True, key=lambda item: item[0])
    print("\nTop problematic files:")
    for issue_count, rel_path, _ in file_stats[:top_n]:
        print(f"  {issue_count:4d}  {rel_path}")

    print("\nDetailed breakdown:")
    for _, rel_path, file_result in file_stats[:top_n]:
        print(f"\n>>> {rel_path}")
        # 按行号+规则排序
        messages = sorted(
            file_result["messages"],
            key=lambda msg: (msg.get("line", 0), msg.get("ruleId") or ""),
        )
        for msg in messages:
            line = msg.get("line", "?")
            column = msg.get("column", "?")
            rule = msg.get("ruleId") or "internal"
            severity = "E" if msg.get("severity") == 2 else "W"
            print(f"  [{severity}] L{line}:{column} {rule} - {msg.get('message')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="生成 eslint 清理报告")
    parser.add_argument(
        "paths",
        nargs="*",
        default=[DEFAULT_TARGET],
        help="要检查的相对路径，默认 frontend/src",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="显示 Top N 问题文件（默认 10）",
    )
    args = parser.parse_args()

    results = run_eslint(args.paths)
    summarize(results, args.limit)


if __name__ == "__main__":
    main()
