#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速检查已有测试的覆盖率
只检查测试文件是否存在，不运行测试
"""

import json
from pathlib import Path
from typing import Dict, List


def load_zero_coverage_services() -> List[Dict]:
    """加载零覆盖率服务列表"""
    json_file = Path("reports/zero_coverage_services.json")
    if not json_file.exists():
        print("❌ 请先运行: python3 scripts/analyze_zero_coverage_services.py")
        return []

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("services", [])


def find_test_file(service_name: str) -> Path:
    """查找测试文件"""
    # 可能的测试文件路径
    possible_paths = [
        Path(f"tests/unit/test_{service_name}.py"),
        Path(f"tests/unit/test_{service_name.replace('/', '_')}.py"),
    ]

    # 如果是子目录服务，尝试不同的路径
    if "/" in service_name:
        parts = service_name.split("/")
        possible_paths.append(Path(f"tests/unit/test_{parts[-1]}.py"))
        possible_paths.append(Path(f"tests/unit/{'/'.join(parts[:-1])}/test_{parts[-1]}.py"))

    for path in possible_paths:
        if path.exists():
            return path

    return None


def main():
    """主函数"""
    print("🔍 快速检查已有测试文件...")
    print("=" * 70)
    print()

    # 加载零覆盖率服务列表
    services = load_zero_coverage_services()
    if not services:
        print("❌ 无法加载服务列表")
        return

    # 前30个最大服务
    top_services = services[:30]

    results = []
    has_test_count = 0
    no_test_count = 0

    print(f"📋 检查前 {len(top_services)} 个最大服务...")
    print()

    for i, service_info in enumerate(top_services, 1):
        service_name = service_info["service_name"]
        statements = service_info["statements"]

        # 查找测试文件
        test_file = find_test_file(service_name)

        if test_file:
            has_test_count += 1
            status_icon = "✅"
            results.append(
                {
                    "service_name": service_name,
                    "statements": statements,
                    "test_file": str(test_file),
                    "has_test": True,
                }
            )
        else:
            no_test_count += 1
            status_icon = "❌"
            results.append(
                {
                    "service_name": service_name,
                    "statements": statements,
                    "test_file": None,
                    "has_test": False,
                }
            )

        test_file_name = Path(test_file).name if test_file else "无"
        print(
            f"[{i:2d}/{len(top_services)}] {status_icon} {service_name:40s} ({statements:4d}行) - {test_file_name}"
        )

    print()
    print("=" * 70)
    print("📊 统计结果:")
    print(f"   总服务数: {len(top_services)}")
    print(f"   ✅ 有测试文件: {has_test_count} ({has_test_count/len(top_services)*100:.1f}%)")
    print(f"   ❌ 无测试文件: {no_test_count} ({no_test_count/len(top_services)*100:.1f}%)")
    print()

    # 生成报告
    report_file = Path("reports/已有测试文件检查报告.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# 已有测试文件检查报告\n\n")
        f.write("## 📊 总体统计\n\n")
        f.write(f"- 总服务数: {len(top_services)}\n")
        f.write(f"- 有测试文件: {has_test_count} ({has_test_count/len(top_services)*100:.1f}%)\n")
        f.write(f"- 无测试文件: {no_test_count} ({no_test_count/len(top_services)*100:.1f}%)\n\n")

        f.write("## ✅ 有测试文件的服务\n\n")
        has_test_services = [r for r in results if r["has_test"]]
        if has_test_services:
            f.write("| # | 服务名称 | 代码行数 | 测试文件 |\n")
            f.write("|---|---------|---------|----------|\n")
            for i, r in enumerate(has_test_services, 1):
                f.write(
                    f"| {i} | {r['service_name']} | {r['statements']} | {Path(r['test_file']).name} |\n"
                )
        else:
            f.write("无\n\n")

        f.write("\n## ❌ 无测试文件的服务\n\n")
        no_test_services = [r for r in results if not r["has_test"]]
        if no_test_services:
            f.write("| # | 服务名称 | 代码行数 | 优先级 |\n")
            f.write("|---|---------|---------|--------|\n")
            for i, r in enumerate(no_test_services, 1):
                priority = "P0" if i <= 10 else "P1" if i <= 30 else "P2"
                f.write(f"| {i} | {r['service_name']} | {r['statements']} | {priority} |\n")
        else:
            f.write("无\n\n")

        f.write("\n## 📋 完整列表\n\n")
        f.write("| # | 服务名称 | 代码行数 | 测试文件 | 状态 |\n")
        f.write("|---|---------|---------|----------|------|\n")
        for i, r in enumerate(results, 1):
            test_file_name = Path(r["test_file"]).name if r.get("test_file") else "无"
            status = "✅ 有测试" if r["has_test"] else "❌ 无测试"
            f.write(
                f"| {i} | {r['service_name']} | {r['statements']} | {test_file_name} | {status} |\n"
            )

    print(f"📄 报告已保存到: {report_file}")
    print()

    # 保存JSON数据
    json_file = Path("reports/test_file_check_data.json")
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "total": len(top_services),
                "has_test": has_test_count,
                "no_test": no_test_count,
                "results": results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"💾 数据已保存到: {json_file}")
    print()

    # 提示下一步
    if has_test_count > 0:
        print("💡 下一步:")
        print("   运行以下命令检查这些服务的实际覆盖率:")
        print()
        for r in has_test_services[:5]:  # 只显示前5个
            service_name = r["service_name"]
            print(f"   pytest tests/unit/test_{service_name}.py \\")
            print(f"       --cov=app/services/{service_name} \\")
            print(f"       --cov-report=term-missing")
            print()


if __name__ == "__main__":
    main()
