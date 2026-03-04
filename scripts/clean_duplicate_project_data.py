#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理项目重复数据
清理指定项目的重复和不真实的测试数据
"""

import os
import sys
from collections import defaultdict

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import get_db_session
from app.models.project import Project, ProjectCost, ProjectDocument, ProjectMilestone


def clean_duplicate_project_data(project_code: str = "PJ250114", dry_run: bool = True):
    """清理项目重复数据"""
    print("\n" + "=" * 60)
    print(f"清理项目重复数据: {project_code}")
    print(f"模式: {'预览模式（不会删除数据）' if dry_run else '执行模式（会删除数据）'}")
    print("=" * 60)

    with get_db_session() as db:
        # 查找项目
        project = db.query(Project).filter(Project.project_code == project_code).first()
        if not project:
            print(f"❌ 项目 {project_code} 不存在")
            return

        print(f"\n📋 项目: {project.project_name} (ID: {project.id})")

        # 1. 清理重复的成本记录
        print("\n" + "-" * 60)
        print("1. 清理重复的成本记录")
        print("-" * 60)
        costs = (
            db.query(ProjectCost)
            .filter(ProjectCost.project_id == project.id)
            .order_by(ProjectCost.created_at)
            .all()
        )

        # 按类型、金额、描述分组，保留最早的一条
        cost_groups = defaultdict(list)
        for cost in costs:
            key = (cost.cost_type, str(cost.amount), cost.description or "")
            cost_groups[key].append(cost)

        duplicate_costs = []
        for key, group in cost_groups.items():
            if len(group) > 1:
                # 保留第一条，删除其余的
                keep = group[0]
                duplicates = group[1:]
                duplicate_costs.extend(duplicates)
                print(
                    f"   保留: {keep.cost_type} - ¥{keep.amount} - {keep.description[:30] if keep.description else ''}"
                )
                for dup in duplicates:
                    print(
                        f"   删除: {dup.cost_type} - ¥{dup.amount} - {dup.description[:30] if dup.description else ''} (ID: {dup.id})"
                    )

        deleted_costs_count = len(duplicate_costs)
        if duplicate_costs:
            print(f"\n   将删除 {deleted_costs_count} 条重复的成本记录")
            if not dry_run:
                for cost in duplicate_costs:
                    db.delete(cost)
        else:
            print("   ✓ 没有重复的成本记录")

        # 2. 清理重复的里程碑
        print("\n" + "-" * 60)
        print("2. 清理重复的里程碑")
        print("-" * 60)
        milestones = (
            db.query(ProjectMilestone)
            .filter(ProjectMilestone.project_id == project.id)
            .order_by(ProjectMilestone.created_at)
            .all()
        )

        # 按名称分组，保留最早的一条
        milestone_groups = defaultdict(list)
        for milestone in milestones:
            key = milestone.milestone_name
            milestone_groups[key].append(milestone)

        duplicate_milestones = []
        for key, group in milestone_groups.items():
            if len(group) > 1:
                # 保留第一条，删除其余的
                keep = group[0]
                duplicates = group[1:]
                duplicate_milestones.extend(duplicates)
                print(f"   保留: {keep.milestone_name} (ID: {keep.id})")
                for dup in duplicates:
                    print(f"   删除: {dup.milestone_name} (ID: {dup.id})")

        deleted_milestones_count = len(duplicate_milestones)
        if duplicate_milestones:
            print(f"\n   将删除 {deleted_milestones_count} 个重复的里程碑")
            if not dry_run:
                for milestone in duplicate_milestones:
                    db.delete(milestone)
        else:
            print("   ✓ 没有重复的里程碑")

        # 3. 清理测试文档（可选）
        print("\n" + "-" * 60)
        print("3. 测试文档数据")
        print("-" * 60)
        documents = db.query(ProjectDocument).filter(ProjectDocument.project_id == project.id).all()

        test_docs = [
            doc
            for doc in documents
            if doc.file_path.startswith("/documents/") or doc.file_path.startswith("/docs/")
        ]

        deleted_docs_count = 0
        if test_docs:
            print(f"   发现 {len(test_docs)} 个测试文档（文件路径不存在）")
            print("   这些是脚本生成的测试数据，不是真实上传的文档")
            print("   是否删除这些测试文档？")
            print("   （建议：如果不需要演示数据，可以删除；如果需要保留演示效果，可以保留）")

            # 默认不删除测试文档，除非明确指定
            if not dry_run and "--delete-test-docs" in sys.argv:
                print(f"\n   删除 {len(test_docs)} 个测试文档...")
                for doc in test_docs:
                    print(f"   删除: {doc.doc_name} (ID: {doc.id})")
                    db.delete(doc)
                deleted_docs_count = len(test_docs)
        else:
            print("   ✓ 没有测试文档")

        # 统计总数
        total_deleted = deleted_costs_count + deleted_milestones_count + deleted_docs_count

        # 提交更改
        if not dry_run and total_deleted > 0:
            db.commit()
            print("\n" + "=" * 60)
            print(f"✅ 已删除 {total_deleted} 条重复数据")
            print(f"   - 成本记录: {deleted_costs_count} 条")
            print(f"   - 里程碑: {deleted_milestones_count} 个")
            print(f"   - 测试文档: {deleted_docs_count} 个")
            print("=" * 60)
        elif dry_run:
            print("\n" + "=" * 60)
            print(f"预览: 将删除 {total_deleted} 条重复数据")
            print(f"   - 成本记录: {deleted_costs_count} 条")
            print(f"   - 里程碑: {deleted_milestones_count} 个")
            print(f"   - 测试文档: {deleted_docs_count} 个（需要 --delete-test-docs 参数）")
            print("=" * 60)
            print("\n提示: 要执行删除，请运行:")
            print(f"  python3 scripts/clean_duplicate_project_data.py {project_code} --execute")
            print("\n如果要同时删除测试文档，请运行:")
            print(
                f"  python3 scripts/clean_duplicate_project_data.py {project_code} --execute --delete-test-docs"
            )
        else:
            print("\n" + "=" * 60)
            print("✓ 没有需要清理的数据")
            print("=" * 60)


if __name__ == "__main__":
    project_code = sys.argv[1] if len(sys.argv) > 1 else "PJ250114"
    dry_run = "--execute" not in sys.argv

    clean_duplicate_project_data(project_code, dry_run)
