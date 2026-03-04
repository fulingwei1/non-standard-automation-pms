#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查项目数据质量
检查指定项目的数据是否有重复、不真实等问题
"""

import os
import sys
from collections import Counter

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import get_db_session
from app.models.issue import Issue
from app.models.progress import Task
from app.models.project import (
    Machine,
    Project,
    ProjectCost,
    ProjectDocument,
    ProjectMilestone,
    ProjectStage,
)


def check_project_data_quality(project_code: str = "PJ250114"):
    """检查项目数据质量"""
    print("\n" + "=" * 60)
    print(f"检查项目数据质量: {project_code}")
    print("=" * 60)

    with get_db_session() as db:
        # 查找项目
        project = db.query(Project).filter(Project.project_code == project_code).first()
        if not project:
            print(f"❌ 项目 {project_code} 不存在")
            return

        print(f"\n📋 项目: {project.project_name} (ID: {project.id})")

        # 1. 检查文档重复
        print("\n" + "-" * 60)
        print("1. 文档数据检查")
        print("-" * 60)
        documents = db.query(ProjectDocument).filter(ProjectDocument.project_id == project.id).all()

        print(f"   总文档数: {len(documents)}")

        # 检查重复的文档名称
        doc_names = [doc.doc_name for doc in documents]
        doc_name_counts = Counter(doc_names)
        duplicates = {name: count for name, count in doc_name_counts.items() if count > 1}

        if duplicates:
            print(f"   ⚠️  发现重复的文档名称:")
            for name, count in duplicates.items():
                print(f"      - {name}: {count} 次")
        else:
            print("   ✓ 没有重复的文档名称")

        # 检查文档文件路径
        fake_paths = [
            doc
            for doc in documents
            if doc.file_path.startswith("/documents/") or doc.file_path.startswith("/docs/")
        ]
        print(f"   ⚠️  测试数据文档: {len(fake_paths)} 个（文件路径不存在）")

        # 2. 检查成本数据重复
        print("\n" + "-" * 60)
        print("2. 成本数据检查")
        print("-" * 60)
        costs = db.query(ProjectCost).filter(ProjectCost.project_id == project.id).all()

        print(f"   总成本记录数: {len(costs)}")

        # 检查重复的成本记录（相同类型、相同金额、相同描述）
        cost_keys = []
        for cost in costs:
            key = (cost.cost_type, str(cost.amount), cost.description or "")
            cost_keys.append(key)

        cost_key_counts = Counter(cost_keys)
        duplicate_costs = {key: count for key, count in cost_key_counts.items() if count > 1}

        if duplicate_costs:
            print(f"   ⚠️  发现重复的成本记录:")
            for key, count in list(duplicate_costs.items())[:10]:  # 只显示前10个
                cost_type, amount, desc = key
                print(
                    f"      - {cost_type}: {formatCurrency(amount)} - {desc[:30]}... ({count} 次)"
                )
        else:
            print("   ✓ 没有重复的成本记录")

        # 检查成本金额分布
        amounts = [float(cost.amount or 0) for cost in costs]
        if amounts:
            print(f"   成本金额范围: {min(amounts):,.2f} ~ {max(amounts):,.2f}")
            print(f"   总成本: {sum(amounts):,.2f}")

        # 3. 检查里程碑重复
        print("\n" + "-" * 60)
        print("3. 里程碑数据检查")
        print("-" * 60)
        milestones = (
            db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project.id).all()
        )

        print(f"   总里程碑数: {len(milestones)}")

        # 检查重复的里程碑名称
        milestone_names = [m.milestone_name for m in milestones]
        milestone_name_counts = Counter(milestone_names)
        duplicate_milestones = {
            name: count for name, count in milestone_name_counts.items() if count > 1
        }

        if duplicate_milestones:
            print(f"   ⚠️  发现重复的里程碑名称:")
            for name, count in duplicate_milestones.items():
                print(f"      - {name}: {count} 次")
        else:
            print("   ✓ 没有重复的里程碑名称")

        # 4. 检查阶段重复
        print("\n" + "-" * 60)
        print("4. 阶段数据检查")
        print("-" * 60)
        stages = db.query(ProjectStage).filter(ProjectStage.project_id == project.id).all()

        print(f"   总阶段数: {len(stages)}")

        # 检查重复的阶段代码
        stage_codes = [s.stage_code for s in stages]
        stage_code_counts = Counter(stage_codes)
        duplicate_stages = {code: count for code, count in stage_code_counts.items() if count > 1}

        if duplicate_stages:
            print(f"   ⚠️  发现重复的阶段代码:")
            for code, count in duplicate_stages.items():
                print(f"      - {code}: {count} 次")
        else:
            print("   ✓ 没有重复的阶段代码")

        # 5. 检查任务重复
        print("\n" + "-" * 60)
        print("5. 任务数据检查")
        print("-" * 60)
        tasks = db.query(Task).filter(Task.project_id == project.id).all()

        print(f"   总任务数: {len(tasks)}")

        # 检查重复的任务名称
        task_names = [t.task_name for t in tasks if t.task_name]
        task_name_counts = Counter(task_names)
        duplicate_tasks = {name: count for name, count in task_name_counts.items() if count > 1}

        if duplicate_tasks:
            print(f"   ⚠️  发现重复的任务名称:")
            for name, count in list(duplicate_tasks.items())[:10]:  # 只显示前10个
                print(f"      - {name[:50]}... ({count} 次)")
        else:
            print("   ✓ 没有重复的任务名称")

        # 6. 检查问题重复
        print("\n" + "-" * 60)
        print("6. 问题数据检查")
        print("-" * 60)
        issues = db.query(Issue).filter(Issue.project_id == project.id).all()

        print(f"   总问题数: {len(issues)}")

        # 检查重复的问题标题
        issue_titles = [i.title for i in issues if i.title]
        issue_title_counts = Counter(issue_titles)
        duplicate_issues = {
            title: count for title, count in issue_title_counts.items() if count > 1
        }

        if duplicate_issues:
            print(f"   ⚠️  发现重复的问题标题:")
            for title, count in duplicate_issues.items():
                print(f"      - {title[:50]}... ({count} 次)")
        else:
            print("   ✓ 没有重复的问题标题")

        # 7. 检查机台
        print("\n" + "-" * 60)
        print("7. 机台数据检查")
        print("-" * 60)
        machines = db.query(Machine).filter(Machine.project_id == project.id).all()

        print(f"   总机台数: {len(machines)}")

        # 检查重复的机台编码
        machine_codes = [m.machine_code for m in machines if m.machine_code]
        machine_code_counts = Counter(machine_codes)
        duplicate_machines = {
            code: count for code, count in machine_code_counts.items() if count > 1
        }

        if duplicate_machines:
            print(f"   ⚠️  发现重复的机台编码:")
            for code, count in duplicate_machines.items():
                print(f"      - {code}: {count} 次")
        else:
            print("   ✓ 没有重复的机台编码")

        # 总结
        print("\n" + "=" * 60)
        print("数据质量总结")
        print("=" * 60)
        total_duplicates = (
            len(duplicates)
            + len(duplicate_costs)
            + len(duplicate_milestones)
            + len(duplicate_stages)
            + len(duplicate_tasks)
            + len(duplicate_issues)
            + len(duplicate_machines)
        )

        if total_duplicates > 0:
            print(f"⚠️  发现 {total_duplicates} 类重复数据")
            print("   建议清理重复数据或检查数据生成脚本")
        else:
            print("✓ 未发现明显的重复数据")

        print(f"\n测试数据统计:")
        print(f"   - 测试文档: {len(fake_paths)} 个")


def formatCurrency(amount):
    """格式化货币"""
    try:
        return f"¥{float(amount):,.2f}"
    except (ValueError, TypeError):
        return str(amount)


if __name__ == "__main__":
    project_code = sys.argv[1] if len(sys.argv) > 1 else "PJ250114"
    check_project_data_quality(project_code)
