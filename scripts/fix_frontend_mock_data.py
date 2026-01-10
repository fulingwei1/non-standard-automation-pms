#!/usr/bin/env python3
"""
批量修复前端页面中的 mock 数据和 demo 账号检查
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

FRONTEND_DIR = Path("/Users/flw/non-standard-automation-pm/frontend/src/pages")


def find_files_with_mock_data() -> List[Path]:
    """查找包含 mock 数据或 demo 账号检查的文件"""
    files_to_fix = []

    for file_path in FRONTEND_DIR.glob("*.jsx"):
        content = file_path.read_text(encoding='utf-8')

        # 检查是否包含这些模式
        patterns = [
            r'isDemoAccount',
            r'demo_token_',
            r'const mockData = ',
            r'const mock[A-Z]',
        ]

        for pattern in patterns:
            if re.search(pattern, content):
                files_to_fix.append(file_path)
                break

    return sorted(files_to_fix)


def analyze_file_issues(file_path: Path) -> Tuple[int, int, int]:
    """分析文件中的问题数量"""
    content = file_path.read_text(encoding='utf-8')

    demo_account_count = len(re.findall(r'isDemoAccount', content))
    demo_token_count = len(re.findall(r'demo_token_', content))
    mock_data_count = len(re.findall(r'const mock[A-Z]', content))

    return demo_account_count, demo_token_count, mock_data_count


def generate_fix_report(files: List[Path]) -> str:
    """生成修复报告"""
    report_lines = []
    report_lines.append("# 前端 Mock 数据修复报告\n")
    report_lines.append(f"生成时间: {os.popen('date').read().strip()}\n")
    report_lines.append(f"总计待修复文件: {len(files)}\n")
    report_lines.append("---\n")

    total_demo_account = 0
    total_demo_token = 0
    total_mock_data = 0

    for file_path in files:
        demo_account, demo_token, mock_data = analyze_file_issues(file_path)
        total_demo_account += demo_account
        total_demo_token += demo_token
        total_mock_data += mock_data

        relative_path = file_path.relative_to(FRONTEND_DIR.parent.parent)
        report_lines.append(f"## {file_path.name}")
        report_lines.append(f"路径: `{relative_path}`")
        report_lines.append(f"- isDemoAccount: {demo_account}")
        report_lines.append(f"- demo_token_: {demo_token}")
        report_lines.append(f"- const mock*: {mock_data}")
        report_lines.append("")

    report_lines.append("---\n")
    report_lines.append("## 统计汇总\n")
    report_lines.append(f"- isDemoAccount 检查: {total_demo_account} 处")
    report_lines.append(f"- demo_token_ 检查: {total_demo_token} 处")
    report_lines.append(f"- mock 数据定义: {total_mock_data} 处")

    return "\n".join(report_lines)


def main():
    """主函数"""
    print("🔍 扫描前端页面中的 mock 数据...")
    files = find_files_with_mock_data()

    if not files:
        print("✅ 没有发现需要修复的文件！")
        return

    print(f"📊 发现 {len(files)} 个文件需要修复")

    # 生成报告
    report = generate_fix_report(files)
    report_path = Path("/Users/flw/non-standard-automation-pm/FRONTEND_MOCK_FIX_REPORT.md")
    report_path.write_text(report, encoding='utf-8')
    print(f"📄 修复报告已生成: {report_path}")

    # 显示前10个文件
    print("\n📋 前10个待修复文件:")
    for i, file_path in enumerate(files[:10], 1):
        demo_account, demo_token, mock_data = analyze_file_issues(file_path)
        print(f"  {i}. {file_path.name} (isDemoAccount={demo_account}, mock={mock_data})")

    if len(files) > 10:
        print(f"  ... 还有 {len(files) - 10} 个文件")


if __name__ == "__main__":
    main()
