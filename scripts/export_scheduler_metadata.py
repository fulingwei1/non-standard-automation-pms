#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出调度器任务元数据到 YAML 和 CSV 格式
用于代码审查、文档生成和运维管理
"""

import csv
import json

# 添加项目根目录到路径
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.scheduler_config import SCHEDULER_TASKS


def export_to_yaml(output_path: Path) -> None:
    """导出元数据到 YAML 格式"""
    metadata = {
        "version": "1.0",
        "export_date": __import__("datetime").datetime.now().isoformat(),
        "total_tasks": len(SCHEDULER_TASKS),
        "tasks": SCHEDULER_TASKS,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(metadata, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"✅ YAML 元数据已导出到: {output_path}")


def export_to_csv(output_path: Path) -> None:
    """导出元数据到 CSV 格式（扁平化）"""
    fieldnames = [
        "id",
        "name",
        "module",
        "callable",
        "cron",
        "owner",
        "category",
        "description",
        "enabled",
        "dependencies_tables",
        "risk_level",
        "sla_max_execution_time_seconds",
        "sla_retry_on_failure",
    ]

    rows = []
    for task in SCHEDULER_TASKS:
        row = {
            "id": task.get("id", ""),
            "name": task.get("name", ""),
            "module": task.get("module", ""),
            "callable": task.get("callable", ""),
            "cron": json.dumps(task.get("cron", {}), ensure_ascii=False),
            "owner": task.get("owner", ""),
            "category": task.get("category", ""),
            "description": task.get("description", ""),
            "enabled": task.get("enabled", True),
            "dependencies_tables": ", ".join(task.get("dependencies_tables", [])),
            "risk_level": task.get("risk_level", "UNKNOWN"),
            "sla_max_execution_time_seconds": task.get("sla", {}).get(
                "max_execution_time_seconds", ""
            ),
            "sla_retry_on_failure": task.get("sla", {}).get("retry_on_failure", ""),
        }
        rows.append(row)

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ CSV 元数据已导出到: {output_path}")


def export_dependencies_matrix(output_path: Path) -> None:
    """导出依赖表矩阵（用于评估表结构变更影响）"""
    # 收集所有表
    all_tables = set()
    for task in SCHEDULER_TASKS:
        all_tables.update(task.get("dependencies_tables", []))

    # 构建矩阵
    matrix = []
    for table in sorted(all_tables):
        affected_tasks = [
            task["id"] for task in SCHEDULER_TASKS if table in task.get("dependencies_tables", [])
        ]
        matrix.append(
            {
                "table": table,
                "affected_tasks_count": len(affected_tasks),
                "affected_tasks": ", ".join(affected_tasks),
            }
        )

    # 导出为 CSV
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["table", "affected_tasks_count", "affected_tasks"])
        writer.writeheader()
        writer.writerows(matrix)

    print(f"✅ 依赖表矩阵已导出到: {output_path}")


def export_risk_summary(output_path: Path) -> None:
    """导出风险级别汇总"""
    risk_summary = {}
    for task in SCHEDULER_TASKS:
        risk_level = task.get("risk_level", "UNKNOWN")
        if risk_level not in risk_summary:
            risk_summary[risk_level] = []
        risk_summary[risk_level].append(
            {
                "id": task["id"],
                "name": task["name"],
                "owner": task.get("owner", ""),
                "category": task.get("category", ""),
            }
        )

    # 导出为 YAML
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(risk_summary, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"✅ 风险级别汇总已导出到: {output_path}")


def main():
    """主函数"""
    output_dir = Path(__file__).parent.parent / "docs" / "scheduler_metadata"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("📊 开始导出调度器任务元数据...\n")

    # 导出 YAML
    export_to_yaml(output_dir / "scheduler_tasks_metadata.yaml")

    # 导出 CSV
    export_to_csv(output_dir / "scheduler_tasks_metadata.csv")

    # 导出依赖表矩阵
    export_dependencies_matrix(output_dir / "dependencies_matrix.csv")

    # 导出风险级别汇总
    export_risk_summary(output_dir / "risk_summary.yaml")

    print(f"\n✅ 所有元数据已导出到: {output_dir}")
    print("\n文件说明：")
    print("  - scheduler_tasks_metadata.yaml: 完整元数据（YAML 格式）")
    print("  - scheduler_tasks_metadata.csv: 完整元数据（CSV 格式，便于 Excel 查看）")
    print("  - dependencies_matrix.csv: 依赖表矩阵（用于评估表结构变更影响）")
    print("  - risk_summary.yaml: 风险级别汇总（按风险级别分组）")


if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("提示: 请确保已安装 pyyaml: pip install pyyaml")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
