#!/usr/bin/env python3
"""
快速拆分 sales/quotes.py 为模块化结构
"""
import re
from pathlib import Path


def read_file_lines(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


def main():
    source_file = Path("/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/quotes.py")
    output_dir = Path("/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales")

    print("📖 读取 quotes.py (2203行)...")
    lines = read_file_lines(source_file)

    # 提取导入
    imports = []
    docstring = False
    for i, line in enumerate(lines):
        if line.strip().startswith('"""') or line.strip().startswith("'''"):
            docstring = not docstring
        elif line.strip().startswith("from ") or line.strip().startswith("import "):
            if not docstring:
                imports.append(line)
        elif imports and i > len(imports) + 20:
            break
    imports_str = "\n".join(imports)

    # 根据章节注释定义模块
    modules = [
        {
            "name": "quotes_crud.py",
            "start": 51,
            "end": 301,
            "prefix": "/quotes",
            "routes": "报价CRUD",
        },
        {
            "name": "versions.py",
            "start": 302,
            "end": 375,
            "prefix": "/quotes/{quote_id}/versions",
            "routes": "报价版本",
        },
        {
            "name": "items.py",
            "start": 376,
            "end": 576,
            "prefix": "/quotes/{quote_id}/items",
            "routes": "报价明细",
        },
        {
            "name": "cost_breakdown.py",
            "start": 577,
            "end": 636,
            "prefix": "/quotes/{quote_id}/cost-breakdown",
            "routes": "成本分解",
        },
        {
            "name": "status.py",
            "start": 637,
            "end": 721,
            "prefix": "/quotes/{quote_id}",
            "routes": "状态变更",
        },
        {
            "name": "approvals_simple.py",
            "start": 722,
            "end": 803,
            "prefix": "/quotes/{quote_id}/approvals",
            "routes": "单级审批",
        },
        {
            "name": "approvals_multi.py",
            "start": 804,
            "end": 936,
            "prefix": "/quote-approvals",
            "routes": "多级审批",
        },
        {
            "name": "workflow.py",
            "start": 937,
            "end": 1156,
            "prefix": "/quotes/{quote_id}/approval",
            "routes": "审批工作流",
        },
        {
            "name": "templates.py",
            "start": 1157,
            "end": 1304,
            "prefix": "/quotes/{quote_id}/apply-template",
            "routes": "模板应用",
        },
        {
            "name": "cost_calculations.py",
            "start": 1305,
            "end": 1472,
            "prefix": "/quotes/{quote_id}",
            "routes": "成本计算",
        },
        {
            "name": "delivery.py",
            "start": 1473,
            "end": 1531,
            "prefix": "/quotes",
            "routes": "交期验证",
        },
        {
            "name": "cost_approvals.py",
            "start": 1532,
            "end": 1740,
            "prefix": "/quotes/{quote_id}/cost-approval",
            "routes": "成本审批",
        },
        {
            "name": "cost_analysis.py",
            "start": 1741,
            "end": 2021,
            "prefix": "/quotes/{quote_id}/cost",
            "routes": "成本分析",
        },
        {"name": "exports.py", "start": 2022, "end": 2203, "prefix": "/quotes", "routes": "导出"},
    ]

    output_dir.mkdir(exist_ok=True)

    for module in modules:
        print(f"📝 生成 {module['name']}...")

        start = module["start"] - 1
        end = min(module["end"], len(lines))

        module_code = "".join(lines[start:end])
        routes = len(re.findall(r"@router\.", module_code))

        if routes == 0:
            print(f"  ⚠️ 跳过: 没有找到路由")
            continue

        module_content = f'''# -*- coding: utf-8 -*-
"""
{module['routes']} - 自动生成
从 sales/quotes.py 拆分
"""

{imports_str}

from fastapi import APIRouter

router = APIRouter(
    prefix="{module['prefix']}",
    tags=["{module['name'].replace('.py', '')}"]
)

# 共 {routes} 个路由

{module_code}
'''

        output_path = output_dir / f'quote_{module["name"]}'
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(module_content)

        print(f"  ✅ {module['name']}: {routes} 个路由")

    print("\n✅ quotes.py 拆分完成！")
    print(f"总计: {len([m for m in modules if 'routes' in str(m)])} 个模块")


if __name__ == "__main__":
    main()
