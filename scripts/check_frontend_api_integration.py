#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查前端API集成情况
- 统计使用Mock数据的页面
- 统计已集成API的页面
- 生成集成状态报告
"""

import re
from pathlib import Path
from typing import Dict

frontend_pages_dir = Path(__file__).parent.parent / "frontend" / "src" / "pages"


def analyze_page_integration(file_path: Path) -> Dict:
    """分析单个页面的API集成情况"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        lines = content.split("\n")

    result = {
        "file": file_path.name,
        "has_api_import": False,
        "has_api_call": False,
        "has_mock_data": False,
        "has_fallback": False,
        "api_calls": [],
        "mock_patterns": [],
    }

    # 检查API导入
    api_import_patterns = [
        r"from ['\"]\.\./services/api['\"]",
        r"from ['\"]@/services/api['\"]",
        r"import.*api.*from",
    ]
    for pattern in api_import_patterns:
        if re.search(pattern, content):
            result["has_api_import"] = True
            break

    # 检查API调用
    api_call_patterns = [
        r"api\.(get|post|put|delete|patch)\(",
        r"(\w+Api)\.(\w+)\(",
        r"await.*api\.",
    ]
    for pattern in api_call_patterns:
        matches = re.findall(pattern, content)
        if matches:
            result["has_api_call"] = True
            result["api_calls"].extend(matches)

    # 检查Mock数据
    mock_patterns = [
        r"mock\w+\s*=",
        r"const\s+mock\w+\s*=",
        r"Mock\w+\s*=",
        r"//\s*Mock",
        r"fallback.*mock",
    ]
    for pattern in mock_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            result["has_mock_data"] = True
            result["mock_patterns"].append(pattern)

    # 检查fallback逻辑
    fallback_patterns = [
        r"catch.*mock",
        r"catch.*fallback",
        r"setData\(mock",
        r"setState\(mock",
        r"using mock",
        r"use mock",
    ]
    for pattern in fallback_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            result["has_fallback"] = True
            break

    return result


def analyze_all_pages():
    """分析所有页面"""
    results = {
        "fully_integrated": [],  # 有API调用，无Mock数据
        "partially_integrated": [],  # 有API调用，但有Mock数据或fallback
        "not_integrated": [],  # 无API调用，有Mock数据
        "unknown": [],  # 无API调用，无Mock数据（可能是简单页面）
    }

    stats = {
        "total": 0,
        "has_api": 0,
        "has_mock": 0,
        "has_fallback": 0,
    }

    for file_path in sorted(frontend_pages_dir.rglob("*.jsx")):
        if file_path.name.startswith("_"):
            continue

        result = analyze_page_integration(file_path)
        stats["total"] += 1

        if result["has_api_call"]:
            stats["has_api"] += 1
        if result["has_mock_data"]:
            stats["has_mock"] += 1
        if result["has_fallback"]:
            stats["has_fallback"] += 1

        # 分类
        if result["has_api_call"] and not result["has_mock_data"] and not result["has_fallback"]:
            results["fully_integrated"].append(result)
        elif result["has_api_call"] and (result["has_mock_data"] or result["has_fallback"]):
            results["partially_integrated"].append(result)
        elif not result["has_api_call"] and result["has_mock_data"]:
            results["not_integrated"].append(result)
        else:
            results["unknown"].append(result)

    return results, stats


def print_report(results: Dict, stats: Dict):
    """打印报告"""
    print("=" * 80)
    print("前端API集成情况检查报告")
    print("=" * 80)
    print()

    print(f"📊 总体统计:")
    print(f"  总页面数: {stats['total']}")
    print(f"  有API调用: {stats['has_api']} ({stats['has_api']/stats['total']*100:.1f}%)")
    print(f"  有Mock数据: {stats['has_mock']} ({stats['has_mock']/stats['total']*100:.1f}%)")
    print(
        f"  有Fallback逻辑: {stats['has_fallback']} ({stats['has_fallback']/stats['total']*100:.1f}%)"
    )
    print()

    print(f"✅ 完全集成（有API，无Mock，无Fallback）:")
    print(
        f"  数量: {len(results['fully_integrated'])} ({len(results['fully_integrated'])/stats['total']*100:.1f}%)"
    )
    if results["fully_integrated"]:
        for item in results["fully_integrated"][:10]:
            print(f"    - {item['file']}")
        if len(results["fully_integrated"]) > 10:
            print(f"    ... 还有 {len(results['fully_integrated']) - 10} 个")
    print()

    print(f"⚠️  部分集成（有API，但有Mock或Fallback）:")
    print(
        f"  数量: {len(results['partially_integrated'])} ({len(results['partially_integrated'])/stats['total']*100:.1f}%)"
    )
    if results["partially_integrated"]:
        for item in results["partially_integrated"][:20]:
            issues = []
            if item["has_mock_data"]:
                issues.append("有Mock数据")
            if item["has_fallback"]:
                issues.append("有Fallback")
            print(f"    - {item['file']:40} ({', '.join(issues)})")
        if len(results["partially_integrated"]) > 20:
            print(f"    ... 还有 {len(results['partially_integrated']) - 20} 个")
    print()

    print(f"❌ 未集成（无API调用，有Mock数据）:")
    print(
        f"  数量: {len(results['not_integrated'])} ({len(results['not_integrated'])/stats['total']*100:.1f}%)"
    )
    if results["not_integrated"]:
        for item in results["not_integrated"][:20]:
            print(f"    - {item['file']}")
        if len(results["not_integrated"]) > 20:
            print(f"    ... 还有 {len(results['not_integrated']) - 20} 个")
    print()

    print(f"❓ 未知状态（无API，无Mock，可能是简单页面）:")
    print(f"  数量: {len(results['unknown'])} ({len(results['unknown'])/stats['total']*100:.1f}%)")
    if results["unknown"]:
        for item in results["unknown"][:10]:
            print(f"    - {item['file']}")
        if len(results["unknown"]) > 10:
            print(f"    ... 还有 {len(results['unknown']) - 10} 个")
    print()

    # 集成度计算
    fully_integrated_count = len(results["fully_integrated"])
    integration_rate = fully_integrated_count / stats["total"] * 100

    print("=" * 80)
    print("💡 总结:")
    print("=" * 80)
    print()
    print(f"1. 完全集成率: {integration_rate:.1f}%")
    print(f"   - 完全集成: {fully_integrated_count} 个页面")
    print(f"   - 部分集成: {len(results['partially_integrated'])} 个页面（需要移除Mock/Fallback）")
    print(f"   - 未集成: {len(results['not_integrated'])} 个页面（需要实现API调用）")
    print()
    print("2. 建议:")
    print("   🔴 高优先级：移除部分集成页面的Mock数据和Fallback逻辑")
    print("   🟡 中优先级：为未集成页面实现API调用")
    print("   🟢 低优先级：检查未知状态页面是否需要API集成")
    print()


if __name__ == "__main__":
    results, stats = analyze_all_pages()
    print_report(results, stats)
