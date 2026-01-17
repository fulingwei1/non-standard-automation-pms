#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查项目文档数据
查看数据库中是否有真实的文档记录，以及它们是如何生成的
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import get_db_session
from app.models.project import Project, ProjectDocument


def check_project_documents(project_code: str = None):
    """检查项目文档数据"""
    print("\n" + "=" * 60)
    print("检查项目文档数据")
    print("=" * 60)

    with get_db_session() as db:
        # 如果指定了项目编码，只检查该项目
        if project_code:
            project = db.query(Project).filter(Project.project_code == project_code).first()
            if not project:
                print(f"❌ 项目 {project_code} 不存在")
                return

            print(f"\n📋 项目: {project.project_name} ({project.project_code})")
            print(f"   项目ID: {project.id}")

            # 查询该项目的文档
            documents = db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project.id
            ).order_by(ProjectDocument.created_at.desc()).all()

            print(f"\n   文档数量: {len(documents)}")

            if documents:
                print("\n   文档列表:")
                for i, doc in enumerate(documents, 1):
                    print(f"   {i}. {doc.doc_name}")
                    print(f"      类型: {doc.doc_type}")
                    print(f"      版本: {doc.version}")
                    print(f"      状态: {doc.status}")
                    print(f"      文件: {doc.file_name}")
                    print(f"      路径: {doc.file_path}")
                    print(f"      创建时间: {doc.created_at}")
                    print()
            else:
                print("\n   ⚠️  该项目没有文档记录")
        else:
            # 统计所有项目的文档
            total_docs = db.query(ProjectDocument).count()
            print(f"\n📊 数据库统计:")
            print(f"   总文档数: {total_docs}")

            # 按项目统计
            projects_with_docs = db.query(Project).join(ProjectDocument).distinct().all()
            print(f"   有文档的项目数: {len(projects_with_docs)}")

            # 显示前10个有文档的项目
            print("\n   有文档的项目列表:")
            for project in projects_with_docs[:10]:
                doc_count = db.query(ProjectDocument).filter(
                    ProjectDocument.project_id == project.id
                ).count()
                print(f"   - {project.project_code}: {project.project_name} ({doc_count} 个文档)")

            # 检查是否有文档但没有名称
            docs_without_name = db.query(ProjectDocument).filter(
                (ProjectDocument.doc_name == None) | (ProjectDocument.doc_name == '')
            ).count()
            if docs_without_name > 0:
                print(f"\n   ⚠️  有 {docs_without_name} 个文档没有名称")

            # 检查文档的文件路径是否真实存在
            print("\n   文档文件路径检查:")
            docs_with_fake_path = db.query(ProjectDocument).filter(
                ProjectDocument.file_path.like('/documents/%')
            ).count()
            docs_with_docs_path = db.query(ProjectDocument).filter(
                ProjectDocument.file_path.like('/docs/%')
            ).count()
            print(f"   使用 /documents/ 路径: {docs_with_fake_path} 个")
            print(f"   使用 /docs/ 路径: {docs_with_docs_path} 个")
            print(f"   (这些路径通常是测试数据，不是真实上传的文件)")

    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)

if __name__ == "__main__":
    # 检查特定项目（从命令行参数获取）
    project_code = None
    if len(sys.argv) > 1:
        project_code = sys.argv[1]

    check_project_documents(project_code)
