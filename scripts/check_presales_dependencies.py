#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查对 presales-project 的依赖情况
"""

from pathlib import Path

project_root = Path(__file__).parent.parent

# 检查的引用
dependencies = {
    "scripts/seed_scoring_rules.py": {
        "file": "presales-project/presales-evaluation-system/scoring_rules_v2.0.json",
        "required": False,  # 如果不存在会使用默认规则
        "description": "评分规则JSON文件（可选，已有默认规则）"
    },
    "scripts/migrate_presales_data.py": {
        "file": "presales-project/presales-evaluation-system/prisma/dev.db",
        "required": False,  # 仅用于数据迁移
        "description": "presales-project数据库（仅用于历史数据迁移）"
    }
}

print("="*60)
print("presales-project 依赖检查")
print("="*60)

all_optional = True
for script, info in dependencies.items():
    file_path = project_root / info["file"]
    exists = file_path.exists()
    status = "✅" if exists else "⚠️"

    print(f"\n{status} {script}")
    print(f"   引用文件: {info['file']}")
    print(f"   是否必需: {'否（可选）' if not info['required'] else '是'}")
    print(f"   文件存在: {'是' if exists else '否'}")
    print(f"   说明: {info['description']}")

    if info["required"] and not exists:
        all_optional = False

print("\n" + "="*60)
print("总结")
print("="*60)

if all_optional:
    print("✅ 所有依赖都是可选的")
    print("\n可以安全删除 presales-project 文件夹，因为：")
    print("1. 评分规则已导入到数据库（可独立运行）")
    print("2. 数据迁移脚本仅用于一次性迁移历史数据")
    print("3. 如果已迁移完成，不再需要 presales-project")
else:
    print("⚠️  存在必需的依赖，删除前请先处理")

print("\n建议操作：")
print("1. 如果已完成数据迁移，可以删除 presales-project")
print("2. 如果需要保留评分规则JSON，可以复制到项目内")
print("3. 更新 scripts/seed_scoring_rules.py 使用项目内的文件")






