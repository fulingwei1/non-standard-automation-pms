#!/usr/bin/env python3
"""
自动拆分 api.js 文件为模块化结构
"""
import json
import re
from pathlib import Path


def extract_api_modules(api_js_path):
    """从api.js中提取所有API模块定义"""
    with open(api_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 匹配 export const xxxApi = { ... }
    pattern = r"export const (\w+) = \{([^}]+)\}"
    matches = re.finditer(pattern, content, re.DOTALL)

    modules = {}
    for match in matches:
        name = match.group(1)
        body = match.group(2)
        modules[name] = body

    return modules, content


def categorize_module(module_name):
    """根据模块名称分类"""
    if (
        "auth" in module_name
        or "user" in module_name
        or "role" in module_name
        or "org" in module_name
    ):
        return "auth"
    elif (
        "project" in module_name
        or "machine" in module_name
        or "stage" in module_name
        or "milestone" in module_name
        or "member" in module_name
        or "cost" in module_name
        or "settlement" in module_name
        or "document" in module_name
        or "workspace" in module_name
        or "contribution" in module_name
    ):
        return "project"
    elif (
        "sales" in module_name
        or "lead" in module_name
        or "opportunity" in module_name
        or "quote" in module_name
        or "contract" in module_name
        or "invoice" in module_name
        or "payment" in module_name
        or "receivable" in module_name
        or "dispute" in module_name
    ):
        return "sales"
    elif (
        "purchase" in module_name
        or "material" in module_name
        or "supplier" in module_name
        or "bom" in module_name
        or "shortage" in module_name
        or "production" in module_name
        or "kit" in module_name
    ):
        return "operations"
    elif (
        "acceptance" in module_name
        or "issue" in module_name
        or "ecn" in module_name
        or "alert" in module_name
    ):
        return "quality"
    elif (
        "employee" in module_name
        or "performance" in module_name
        or "timesheet" in module_name
        or "bonus" in module_name
        or "hr" in module_name
    ):
        return "hr"
    elif (
        "notification" in module_name
        or "report" in module_name
        or "file" in module_name
        or "export" in module_name
        or "import" in module_name
        or "task" in module_name
        or "workload" in module_name
    ):
        return "shared"
    else:
        return "other"


def main():
    base_path = Path("/Users/flw/non-standard-automation-pm/frontend/src/services")
    api_js_path = base_path / "api.js"

    print("📖 读取 api.js...")
    modules, full_content = extract_api_modules(api_js_path)

    print(f"✅ 找到 {len(modules)} 个API模块")

    # 分类模块
    categorized = {}
    for name, body in modules.items():
        category = categorize_module(name)
        if category not in categorized:
            categorized[category] = {}
        categorized[category][name] = body

    # 打印分类统计
    print("\n📊 模块分类统计:")
    for category, mods in categorized.items():
        print(f"  {category}: {len(mods)} 个模块")

    # 生成JSON供后续处理
    output = {
        "total": len(modules),
        "categories": {k: list(v.keys()) for k, v in categorized.items()},
    }

    output_path = base_path / "_split_analysis.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 分析结果已保存到 {output_path}")


if __name__ == "__main__":
    main()
