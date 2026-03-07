#!/usr/bin/env python3
"""
拆分 service.py 为模块化结构
"""
import re
from pathlib import Path


def read_file_lines(file_path):
    """读取文件所有行"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.readlines()


def extract_imports(lines):
    """提取导入语句"""
    imports = []
    for i, line in enumerate(lines):
        if line.strip().startswith("from ") or line.strip().startswith("import "):
            imports.append((i, line))
        elif imports and i > imports[-1][0] + 5:
            break
    return [line for _, line in imports]


def main():
    source_file = Path("/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/service.py")
    output_dir = Path("/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/service")

    print("📖 读取 service.py...")
    lines = read_file_lines(source_file)

    # 提取导入
    imports = extract_imports(lines)
    imports_str = "\n".join(imports)

    # 定义各个模块的范围（基于章节注释）
    modules = {
        "statistics.py": {
            "start": 123,
            "end": 218,
            "prefix": "/service/statistics",
            "name": "客服统计",
        },
        "tickets.py": {"start": 219, "end": 710, "prefix": "/service/tickets", "name": "服务工单"},
        "records.py": {
            "start": 711,
            "end": 998,
            "prefix": "/service/records",
            "name": "现场服务记录",
        },
        "communications.py": {
            "start": 999,
            "end": 1189,
            "prefix": "/service/communications",
            "name": "客户沟通",
        },
        "surveys.py": {
            "start": 1190,
            "end": 1398,
            "prefix": "/service/surveys",
            "name": "满意度调查",
        },
        "survey_templates.py": {
            "start": 1399,
            "end": 1464,
            "prefix": "/service/survey-templates",
            "name": "满意度调查模板",
        },
        "knowledge.py": {
            "start": 1465,
            "end": 1937,
            "prefix": "/service/knowledge",
            "name": "知识库",
        },
        "knowledge_features.py": {
            "start": 1938,
            "end": 2208,
            "prefix": "/service/knowledge-features",
            "name": "知识库特定功能",
        },
    }

    # 创建输出目录
    output_dir.mkdir(exist_ok=True)

    # 为每个模块创建文件
    for module_name, config in modules.items():
        print(f"📝 生成 {module_name}...")

        start = config["start"] - 1  # 转换为0索引
        end = config["end"]

        # 提取模块代码
        if start >= len(lines):
            print(f"  ⚠️ 跳过 {module_name}: 起始行超出范围")
            continue

        if end > len(lines):
            end = len(lines)

        module_code = "".join(lines[start:end])

        # 统计路由数量
        routes = len(re.findall(r"@router\.", module_code))

        # 生成模块文件内容
        module_content = f'''# -*- coding: utf-8 -*-
"""
{config['name']} API
自动生成，从 service.py 拆分
"""

{imports_str}

from fastapi import APIRouter

router = APIRouter(
    prefix="{config['prefix']}",
    tags=["{module_name.replace('.py', '')}"]
)

# ==================== 路由定义 ====================
# 共 {routes} 个路由

{module_code}
'''

        # 写入文件
        output_path = output_dir / module_name
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(module_content)

        print(f"  ✅ {module_name}: {routes} 个路由")

    # 创建__init__.py
    init_content = '''# -*- coding: utf-8 -*-
"""
售后服务 API - 模块化结构
"""

from fastapi import APIRouter

from .statistics import router as statistics_router
from .tickets import router as tickets_router
from .records import router as records_router
from .communications import router as communications_router
from .surveys import router as surveys_router
from .survey_templates import router as survey_templates_router
from .knowledge import router as knowledge_router
from .knowledge_features import router as knowledge_features_router

router = APIRouter()

router.include_router(statistics_router)
router.include_router(tickets_router)
router.include_router(records_router)
router.include_router(communications_router)
router.include_router(surveys_router)
router.include_router(survey_templates_router)
router.include_router(knowledge_router)
router.include_router(knowledge_features_router)

__all__ = ['router']
'''

    with open(output_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write(init_content)

    print("\n✅ service.py 拆分完成！")
    print(f"总计: {len(modules)} 个模块")


if __name__ == "__main__":
    main()
