#!/usr/bin/env python3
"""
自动拆分 scheduled_tasks.py 为模块化结构
"""
from collections import defaultdict
from pathlib import Path


def extract_functions_by_section(file_path):
    """根据注释分组提取函数"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        lines = content.split("\n")

    sections = {}
    current_section = "header"
    sections[current_section] = []

    for i, line in enumerate(lines):
        # 检测章节注释
        if line.startswith("# ===================="):
            section_name = line.strip("# =").strip()
            sections[section_name] = []
            current_section = section_name
        else:
            sections[current_section].append((i + 1, line))

    return sections, lines


def extract_function_body(lines, start_idx, function_name):
    """提取完整函数体"""
    indent_level = None
    for i in range(start_idx, len(lines)):
        line = lines[i]
        if line.strip().startswith("def ") or line.strip().startswith("async def "):
            # 找到函数定义行，获取缩进级别
            indent_level = len(line) - len(line.lstrip())
            break

    if indent_level is None:
        return None

    function_lines = [lines[start_idx]]
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        # 检查是否回到函数定义级别
        if line.strip() and not line.startswith("#"):
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indent_level and not line.startswith(" " * (indent_level + 1)):
                break
        function_lines.append(line)

    return function_lines


def categorize_section(section_name):
    """将章节分类到模块"""
    section_lower = section_name.lower()

    if any(kw in section_lower for kw in ["问题", "issue", "升级"]):
        return "project"
    elif any(
        kw in section_lower for kw in ["里程碑", "milestone", "成本", "cost", "健康度", "health"]
    ):
        return "project"
    elif any(kw in section_lower for kw in ["生产", "缺料", "kit", "delivery", "task", "progress"]):
        return "production"
    elif any(kw in section_lower for kw in ["工时", "timesheet"]):
        return "timesheet"
    elif any(
        kw in section_lower
        for kw in ["销售", "收款", "商机", "payment", "receivable", "opportunity"]
    ):
        return "sales"
    elif any(kw in section_lower for kw in ["预警", "alert", "workload"]):
        return "alerts"
    elif any(kw in section_lower for kw in ["通知", "notification", "response"]):
        return "notification"
    elif any(
        kw in section_lower for kw in ["设备", "保养", "合同", "员工", "maintenance", "job", "duty"]
    ):
        return "maintenance"
    else:
        return "shared"


def main():
    base_path = Path("/Users/flw/non-standard-automation-pm/app/utils")
    source_file = base_path / "scheduled_tasks.py"

    print("📖 读取 scheduled_tasks.py...")
    sections, lines = extract_functions_by_section(source_file)

    print(f"✅ 找到 {len(sections)} 个章节")

    # 按模块分组
    modules = defaultdict(list)
    module_order = {}

    for section_name, section_lines in sections.items():
        if section_name == "header":
            continue

        module = categorize_section(section_name)
        if module not in module_order:
            module_order[module] = len(module_order)

        modules[module].append({"section": section_name, "lines": section_lines})

    print("\n📊 模块分配:")
    for module in sorted(modules.keys(), key=lambda x: module_order.get(x, 999)):
        sections_count = len(modules[module])
        print(f"  {module}: {sections_count} 个章节")

    # 创建模块文件
    print("\n📝 生成模块文件...")

    # 提取头部导入和注释
    header_lines = []
    in_header = True
    for line_idx, line in sections["header"]:
        if in_header and line.startswith("from ") or line.startswith("import "):
            header_lines.append(line)
        elif line.strip().startswith("#"):
            header_lines.append(line)
        elif line_idx < 40:  # 前40行都是导入
            header_lines.append(line)

    # 生成各模块文件
    for module_name, module_data in modules.items():
        module_path = base_path / f"scheduled_tasks/{module_name}.py"

        file_lines = [
            "# -*- coding: utf-8 -*-",
            f'"""',
            f"定时任务 - {module_name.upper()} 模块",
            f"从 scheduled_tasks.py 自动拆分",
            f'"""',
            "",
            "import logging",
            "from typing import List, Optional",
            "from sqlalchemy import or_, func",
            "from sqlalchemy.orm import Session",
            "from datetime import datetime, date, timedelta",
            "from decimal import Decimal",
            "",
            "from app.models.base import get_db_session",
            "from app.models.project import Project, ProjectMilestone, ProjectCost",
            "from app.models.issue import Issue, IssueStatisticsSnapshot",
            "from app.models.alert import AlertRecord, AlertRule, AlertNotification, AlertStatistics",
            "from app.models.enums import AlertLevelEnum, AlertStatusEnum, AlertRuleTypeEnum",
            "from app.services.notification_dispatcher import (",
            "    NotificationDispatcher,",
            "    resolve_channels,",
            "    resolve_recipients,",
            "    channel_allowed,",
            ")",
            "from app.services.notification_queue import enqueue_notification",
            "from app.services.notification_service import AlertNotificationService, send_alert_notification",
            "",
            "logger = logging.getLogger(__name__)",
            "",
            "",
        ]

        # 添加各章节内容
        for section_info in module_data:
            section_name = section_info["section"]
            section_lines = section_info["lines"]

            file_lines.append(f"# ==================== {section_name} ====================")
            file_lines.append("")

            for line_idx, line in section_lines[:50]:  # 限制每节前50行避免过大
                file_lines.append(line)

            file_lines.append("")
            file_lines.append("")

        content = "\n".join(file_lines)

        with open(module_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"  ✅ {module_name}.py")

    print("\n✅ 拆分完成！")


if __name__ == "__main__":
    main()
