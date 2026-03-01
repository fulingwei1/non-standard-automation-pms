#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描所有数据模型，识别缺少 tenant_id 的核心业务表（使用正则表达式）
"""

import os
import re
from pathlib import Path
from typing import List, Dict

# 工作目录
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "app" / "models"

# 排除列表（基础设施表、枚举表等不需要租户隔离的表）
EXCLUDE_TABLES = {
    "tenants",  # 租户表本身
    "sessions",  # 会话表
    "login_attempts",  # 登录尝试（全局）
    "two_factor_secrets",  # 2FA密钥
    "two_factor_backup_codes",  # 2FA备份码
    "scheduler_config",  # 调度器配置
    "alembic_version",  # 迁移版本
}

# 排除的文件模式
EXCLUDE_FILES = {
    "__init__.py",
    "base.py",
    "enums.py",
    "encrypted_types.py",
}


def scan_model_file(file_path: Path) -> List[Dict]:
    """扫描单个模型文件，提取表信息"""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"⚠️  无法读取文件 {file_path}: {e}")
        return []

    models = []

    # 查找所有类定义（继承自Base）
    class_pattern = r'class\s+(\w+)\s*\([^)]*Base[^)]*\)\s*:'
    for class_match in re.finditer(class_pattern, content):
        class_name = class_match.group(1)
        class_start = class_match.start()

        # 查找 __tablename__
        tablename_pattern = r'__tablename__\s*=\s*["\']([^"\']+)["\']'
        tablename_match = re.search(tablename_pattern, content[class_start:class_start+2000])

        if not tablename_match:
            continue

        table_name = tablename_match.group(1)

        # 检查是否在排除列表
        if table_name in EXCLUDE_TABLES:
            continue

        # 查找是否有 tenant_id 字段
        # 在类定义范围内查找（取接下来的5000个字符，覆盖大部分类定义）
        class_content = content[class_start:class_start+5000]

        # 检查下一个 class 定义的位置，避免跨类查找
        next_class_match = re.search(r'\nclass\s+\w+', class_content[100:])  # 跳过当前class的头
        if next_class_match:
            class_content = class_content[:100 + next_class_match.start()]

        # 查找 tenant_id 字段定义
        tenant_id_patterns = [
            r'tenant_id\s*=\s*Column',
            r'tenant_id:\s*Mapped',  # SQLAlchemy 2.0 风格
        ]

        has_tenant_id = any(re.search(pattern, class_content) for pattern in tenant_id_patterns)

        models.append({
            "class_name": class_name,
            "table_name": table_name,
            "file_path": str(file_path.relative_to(PROJECT_ROOT)),
            "has_tenant_id": has_tenant_id,
        })

    return models


def get_module_name(file_path: str) -> str:
    """根据文件路径提取模块名"""
    if "production/" in file_path:
        return "生产管理"
    elif "project/" in file_path:
        return "项目管理"
    elif "sales/" in file_path:
        return "销售管理"
    elif "approval/" in file_path:
        return "审批流程"
    elif "business_support/" in file_path:
        return "商务支撑"
    elif "performance/" in file_path:
        return "绩效管理"
    elif "service/" in file_path:
        return "售后服务"
    elif "shortage/" in file_path:
        return "缺料管理"
    elif "strategy/" in file_path:
        return "战略管理"
    elif "pmo/" in file_path:
        return "PMO管理"
    elif "ecn/" in file_path:
        return "工程变更"
    elif "engineer_performance/" in file_path:
        return "工程师绩效"
    elif "ai_planning/" in file_path:
        return "AI规划"
    else:
        return "核心模块"


def main():
    """主函数"""
    print("🔍 开始扫描数据模型...")

    all_models = []
    tables_with_tenant = set()
    tables_without_tenant = set()

    # 遍历所有模型文件
    for root, dirs, files in os.walk(MODELS_DIR):
        # 跳过 __pycache__ 和 exports
        dirs[:] = [d for d in dirs if not d.startswith("__") and d != "exports"]

        for file in files:
            if not file.endswith(".py"):
                continue
            if file in EXCLUDE_FILES:
                continue

            file_path = Path(root) / file
            models = scan_model_file(file_path)
            all_models.extend(models)

            for model in models:
                if model["has_tenant_id"]:
                    tables_with_tenant.add(model["table_name"])
                else:
                    tables_without_tenant.add(model["table_name"])

    print(f"📊 扫描完成，共发现 {len(all_models)} 个模型")
    print(f"✅ 已包含 tenant_id: {len(tables_with_tenant)}")
    print(f"❌ 缺少 tenant_id: {len(tables_without_tenant)}")

    # 生成报告
    lines = []
    lines.append("# 数据模型租户隔离扫描报告\n\n")
    lines.append(f"扫描时间: {os.popen('date').read().strip()}\n\n")
    lines.append("=" * 80 + "\n\n")

    # 统计
    total_tables = len(tables_with_tenant) + len(tables_without_tenant)
    lines.append(f"## 统计摘要\n\n")
    lines.append(f"- 总表数: {total_tables}\n")
    lines.append(f"- 已包含 tenant_id: {len(tables_with_tenant)}\n")
    lines.append(f"- 缺少 tenant_id: {len(tables_without_tenant)}\n\n")

    # 已包含 tenant_id 的表
    if tables_with_tenant:
        lines.append(f"## ✅ 已包含 tenant_id 的表 ({len(tables_with_tenant)})\n\n")
        for table in sorted(tables_with_tenant):
            lines.append(f"- {table}\n")
        lines.append("\n")

    # 缺少 tenant_id 的表（按模块分组）
    if tables_without_tenant:
        lines.append(f"## ⚠️  缺少 tenant_id 的核心业务表 ({len(tables_without_tenant)})\n\n")

        # 按模块分组
        models_by_module = {}
        for model in all_models:
            if not model["has_tenant_id"] and model["table_name"] in tables_without_tenant:
                module = get_module_name(model["file_path"])
                if module not in models_by_module:
                    models_by_module[module] = []
                models_by_module[module].append(model)

        # 输出分组结果
        for module in sorted(models_by_module.keys()):
            lines.append(f"### {module} ({len(models_by_module[module])})\n\n")
            for model in sorted(models_by_module[module], key=lambda x: x["table_name"]):
                lines.append(
                    f"- `{model['table_name']}` ({model['class_name']}) - {model['file_path']}\n"
                )
            lines.append("\n")

    # 详细模型清单
    lines.append(f"## 📊 完整模型清单\n\n")
    for model in sorted(all_models, key=lambda x: x["table_name"]):
        status = "✅" if model["has_tenant_id"] else "❌"
        lines.append(
            f"{status} `{model['table_name']}` - {model['class_name']} - {model['file_path']}\n"
        )

    report = "".join(lines)
    report_path = PROJECT_ROOT / "data" / "tenant_scan_report.md"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"\n📝 报告已保存: {report_path}")

    # 输出缺少 tenant_id 的表清单（用于后续处理）
    if tables_without_tenant:
        tables_file = PROJECT_ROOT / "data" / "tables_need_tenant_id.txt"
        tables_file.write_text("\n".join(sorted(tables_without_tenant)), encoding="utf-8")
        print(f"📋 待处理表清单: {tables_file}")

    # 返回数据供后续使用
    return {
        "all_models": all_models,
        "tables_with_tenant": tables_with_tenant,
        "tables_without_tenant": tables_without_tenant,
    }


if __name__ == "__main__":
    main()
