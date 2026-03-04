#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行测试并生成覆盖率报告

使用方法：
  python3 run_tests.py              # 运行所有测试
  python3 run_tests.py --unit-only  # 只运行单元测试
  python3 run_tests.py --integration-only  # 只运行集成测试
  python3 run_tests.py --no-slow  # 跳过慢速测试
  python3 run_tests.py --cov-only  # 只生成覆盖率报告
"""

import argparse
import subprocess
import sys


def run_command(command, description):
    """运行命令并输出结果"""
    print(f"\n{'=' * 60}")
    print(f"运行: {description}")
    print(f"命令: {' '.join(command)}")
    print(f"{'=' * 60}\n")

    result = subprocess.run(command, capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("错误输出:")
        print(result.stderr)

    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="运行测试并生成覆盖率报告")
    parser.add_argument("--unit-only", action="store_true", help="只运行单元测试")
    parser.add_argument("--integration-only", action="store_true", help="只运行集成测试")
    parser.add_argument("--no-slow", action="store_true", help="跳过慢速测试")
    parser.add_argument("--cov-only", action="store_true", help="只生成覆盖率报告，不运行测试")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    args = parser.parse_args()

    # 构建命令
    command = ["python3", "-m", "pytest"]

    if args.unit_only:
        command.append("--unit-only")
    elif args.integration_only:
        command.append("--integration-only")

    if args.no_slow:
        command.append("--no-slow")

    if args.verbose:
        command.append("-vv")

    if not args.cov_only:
        # 运行测试
        returncode = run_command(command, "运行测试")

        if returncode != 0:
            print(f"\n❌ 测试失败，退出码: {returncode}")
            sys.exit(1)

    # 生成覆盖率报告
    cov_command = [
        "python3",
        "-m",
        "pytest",
        "--cov=app",
        "--cov-report=term",
        "--cov-report=html",
    ]

    returncode = run_command(cov_command, "生成覆盖率报告")

    # 输出报告位置
    print(f"\n{'=' * 60}")
    print("📊 覆盖率报告已生成:")
    print("   - 终端输出: 查看上面的统计")
    print("   - HTML 报告: htmlcov/index.html")
    print(f"{'=' * 60}\n")

    if returncode != 0:
        print("⚠️  部分测试可能被跳过")
        sys.exit(0)

    # 检查覆盖率是否达标

    # 从输出中提取覆盖率
    if result := subprocess.run(
        ["python3", "-m", "pytest", "--cov=app", "--cov-report=json"],
        capture_output=True,
        text=True,
    ):
        try:
            import json

            cov_data = json.loads(result.stdout)
            total = cov_data.get("totals", {})
            line_coverage = total.get("percent_covered", 0)
            branch_coverage = total.get("percent_covered_display", "0%")

            print("\n📊 总体覆盖率统计:")
            print(f"   行覆盖率: {line_coverage:.2f}%")
            print(f"   分支覆盖率: {branch_coverage}")
            print()

            # 检查是否达到 70%
            target = 70.0
            if line_coverage >= target:
                print(f"✅ 恭喜！覆盖率已达到 {target}%+ 目标！")
            else:
                print(f"⚠️  覆盖率未达到 {target}% 目标，当前为 {line_coverage:.2f}%")

            sys.exit(0 if line_coverage >= target else 1)

        except Exception:
            print("无法解析覆盖率数据")


if __name__ == "__main__":
    main()
