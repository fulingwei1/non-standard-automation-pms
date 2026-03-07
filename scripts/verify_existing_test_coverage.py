#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证已有测试的覆盖率
检查哪些服务已有测试文件，并验证它们的实际覆盖率
"""

import json
import re
import subprocess
import sys
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


def get_service_module_path(service_name: str) -> str:
    """获取服务的模块路径"""
    # 处理子目录服务
    if "/" in service_name:
        return f"app/services/{service_name}"
    return f"app/services/{service_name}"


def run_coverage_check(service_name: str, test_file: Path) -> Dict:
    """运行覆盖率检查"""
    service_path = get_service_module_path(service_name)

    # 检查服务文件是否存在
    service_file = Path(f"app/services/{service_name}.py")
    if not service_file.exists():
        # 尝试子目录
        if "/" in service_name:
            parts = service_name.split("/")
            service_file = Path(f"app/services/{'/'.join(parts)}.py")
            if service_file.exists():
                service_path = f"app/services/{'/'.join(parts[:-1])}"
        else:
            return {"status": "error", "message": f"服务文件不存在: app/services/{service_name}.py"}

    try:
        # 运行pytest覆盖率检查
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(test_file),
            "--cov",
            service_path,
            "--cov-report",
            "term-missing",
            "--cov-report",
            "json:coverage_temp.json",
            "-q",
            "--tb=no",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # 解析覆盖率结果
        coverage_data = {}
        if Path("coverage_temp.json").exists():
            with open("coverage_temp.json", "r") as f:
                coverage_data = json.load(f)
            Path("coverage_temp.json").unlink()

        # 从输出中提取覆盖率
        coverage_percent = 0.0
        if coverage_data:
            files = coverage_data.get("files", {})
            for filepath, info in files.items():
                if service_name in filepath or service_path in filepath:
                    summary = info.get("summary", {})
                    coverage_percent = summary.get("percent_covered", 0.0)
                    break

        # 从标准输出中提取覆盖率（备用方法）
        if coverage_percent == 0.0:
            output_lines = result.stdout.split("\n")
            for line in output_lines:
                if "TOTAL" in line or service_path in line:
                    # 尝试提取百分比
                    match = re.search(r"(\d+)%", line)
                    if match:
                        coverage_percent = float(match.group(1))
                        break

        return {
            "status": "success" if result.returncode == 0 else "failed",
            "coverage": coverage_percent,
            "returncode": result.returncode,
            "stdout": result.stdout[-500:] if result.stdout else "",  # 只保留最后500字符
            "stderr": result.stderr[-500:] if result.stderr else "",
        }

    except subprocess.TimeoutExpired:
        return {"status": "timeout", "message": "测试运行超时"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    """主函数"""
    print("🔍 验证已有测试的覆盖率...")
    print("=" * 60)
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
            print(
                f"[{i:2d}/{len(top_services)}] ✅ {service_name:40s} ({statements:4d}行) - 测试文件存在"
            )
            print(f"     测试文件: {test_file}")

            # 运行覆盖率检查
            print(f"     正在检查覆盖率...", end="", flush=True)
            coverage_result = run_coverage_check(service_name, test_file)

            if coverage_result["status"] == "success":
                coverage = coverage_result.get("coverage", 0.0)
                status_icon = "✅" if coverage > 50 else "⚠️" if coverage > 0 else "❌"
                print(f" {status_icon} {coverage:.1f}%")

                results.append(
                    {
                        "service_name": service_name,
                        "statements": statements,
                        "test_file": str(test_file),
                        "coverage": coverage,
                        "status": "success",
                    }
                )
            elif coverage_result["status"] == "failed":
                print(f" ❌ 测试失败")
                results.append(
                    {
                        "service_name": service_name,
                        "statements": statements,
                        "test_file": str(test_file),
                        "coverage": 0.0,
                        "status": "failed",
                        "error": coverage_result.get("stderr", "")[:200],
                    }
                )
            else:
                print(f" ⚠️  {coverage_result.get('message', '未知错误')}")
                results.append(
                    {
                        "service_name": service_name,
                        "statements": statements,
                        "test_file": str(test_file),
                        "coverage": 0.0,
                        "status": coverage_result["status"],
                        "error": coverage_result.get("message", ""),
                    }
                )
        else:
            no_test_count += 1
            print(
                f"[{i:2d}/{len(top_services)}] ❌ {service_name:40s} ({statements:4d}行) - 无测试文件"
            )
            results.append(
                {
                    "service_name": service_name,
                    "statements": statements,
                    "test_file": None,
                    "coverage": 0.0,
                    "status": "no_test",
                }
            )

    print()
    print("=" * 60)
    print("📊 统计结果:")
    print(f"   总服务数: {len(top_services)}")
    print(f"   有测试文件: {has_test_count}")
    print(f"   无测试文件: {no_test_count}")
    print()

    # 按覆盖率分组
    high_coverage = [r for r in results if r.get("coverage", 0) >= 50]
    medium_coverage = [r for r in results if 0 < r.get("coverage", 0) < 50]
    low_coverage = [r for r in results if r.get("coverage", 0) == 0 and r.get("test_file")]
    no_test = [r for r in results if not r.get("test_file")]

    print("📈 覆盖率分布:")
    print(f"   ✅ 高覆盖率 (≥50%): {len(high_coverage)} 个")
    print(f"   ⚠️  中覆盖率 (1-49%): {len(medium_coverage)} 个")
    print(f"   ❌ 低覆盖率 (0%): {len(low_coverage)} 个")
    print(f"   📝 无测试文件: {len(no_test)} 个")
    print()

    # 生成详细报告
    report_file = Path("reports/已有测试覆盖率验证报告.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# 已有测试覆盖率验证报告\n\n")
        f.write(f"**生成时间**: {Path(__file__).stat().st_mtime}\n\n")
        f.write("## 📊 总体统计\n\n")
        f.write(f"- 总服务数: {len(top_services)}\n")
        f.write(f"- 有测试文件: {has_test_count}\n")
        f.write(f"- 无测试文件: {no_test_count}\n")
        f.write(f"- 高覆盖率 (≥50%): {len(high_coverage)}\n")
        f.write(f"- 中覆盖率 (1-49%): {len(medium_coverage)}\n")
        f.write(f"- 低覆盖率 (0%): {len(low_coverage)}\n\n")

        f.write("## ✅ 高覆盖率服务 (≥50%)\n\n")
        if high_coverage:
            f.write("| # | 服务名称 | 代码行数 | 覆盖率 | 测试文件 |\n")
            f.write("|---|---------|---------|--------|----------|\n")
            for i, r in enumerate(
                sorted(high_coverage, key=lambda x: x.get("coverage", 0), reverse=True), 1
            ):
                f.write(
                    f"| {i} | {r['service_name']} | {r['statements']} | {r['coverage']:.1f}% | {Path(r['test_file']).name} |\n"
                )
        else:
            f.write("无\n\n")

        f.write("\n## ⚠️ 中覆盖率服务 (1-49%)\n\n")
        if medium_coverage:
            f.write("| # | 服务名称 | 代码行数 | 覆盖率 | 测试文件 |\n")
            f.write("|---|---------|---------|--------|----------|\n")
            for i, r in enumerate(
                sorted(medium_coverage, key=lambda x: x.get("coverage", 0), reverse=True), 1
            ):
                f.write(
                    f"| {i} | {r['service_name']} | {r['statements']} | {r['coverage']:.1f}% | {Path(r['test_file']).name} |\n"
                )
        else:
            f.write("无\n\n")

        f.write("\n## ❌ 低覆盖率服务 (0%)\n\n")
        if low_coverage:
            f.write("| # | 服务名称 | 代码行数 | 状态 | 测试文件 |\n")
            f.write("|---|---------|---------|------|----------|\n")
            for i, r in enumerate(low_coverage, 1):
                status = r.get("status", "unknown")
                f.write(
                    f"| {i} | {r['service_name']} | {r['statements']} | {status} | {Path(r['test_file']).name} |\n"
                )
        else:
            f.write("无\n\n")

        f.write("\n## 📝 无测试文件服务\n\n")
        if no_test:
            f.write("| # | 服务名称 | 代码行数 | 优先级 |\n")
            f.write("|---|---------|---------|--------|\n")
            for i, r in enumerate(sorted(no_test, key=lambda x: x["statements"], reverse=True), 1):
                priority = "P0" if i <= 10 else "P1" if i <= 30 else "P2"
                f.write(f"| {i} | {r['service_name']} | {r['statements']} | {priority} |\n")
        else:
            f.write("无\n\n")

        f.write("\n## 📋 详细列表\n\n")
        f.write("| # | 服务名称 | 代码行数 | 测试文件 | 覆盖率 | 状态 |\n")
        f.write("|---|---------|---------|----------|--------|------|\n")
        for i, r in enumerate(results, 1):
            test_file_name = Path(r["test_file"]).name if r.get("test_file") else "无"
            coverage = f"{r['coverage']:.1f}%" if r.get("coverage", 0) > 0 else "0%"
            status = r.get("status", "unknown")
            f.write(
                f"| {i} | {r['service_name']} | {r['statements']} | {test_file_name} | {coverage} | {status} |\n"
            )

    print(f"📄 详细报告已保存到: {report_file}")
    print()

    # 保存JSON数据
    json_file = Path("reports/existing_test_coverage_data.json")
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "total": len(top_services),
                "has_test": has_test_count,
                "no_test": no_test_count,
                "high_coverage": len(high_coverage),
                "medium_coverage": len(medium_coverage),
                "low_coverage": len(low_coverage),
                "results": results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"💾 数据已保存到: {json_file}")


if __name__ == "__main__":
    main()
