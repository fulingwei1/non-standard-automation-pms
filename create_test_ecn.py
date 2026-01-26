#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建 ECN 测试数据脚本
用于 Phase 1 ECN 审批流程测试
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from app.models.base import get_db_session
from app.models.ecn import Ecn
from app.models.user import User
from app.models.project import Project


def create_test_ecn():
    """创建测试 ECN 数据"""

    with get_db_session() as session:
        # 检查是否已有测试用户
        test_users = session.query(User).limit(5).all()
        if not test_users:
            print("❌ 数据库中没有用户，无法创建测试 ECN")
            print("请先运行 init_db.py 初始化数据库")
            return None, None, None

        print(f"✅ 找到 {len(test_users)} 个用户:")
        for user in test_users:
            print(f"  - ID: {user.id}, Username: {user.username}, Email: {user.email}")

        # 检查是否已有项目
        test_projects = session.query(Project).limit(5).all()
        if not test_projects:
            print("❌ 数据库中没有项目，无法创建测试 ECN")
            return None, None, None

        print(f"\n✅ 找到 {len(test_projects)} 个项目:")
        for proj in test_projects:
            print(f"  - ID: {proj.id}, Name: {proj.project_name}")

        # 获取第一个用户作为申请人
        applicant = test_users[0]
        project = test_projects[0]

        # 创建测试 ECN
        test_ecn = Ecn(
            ecn_no=f"ECNTEST{datetime.now().strftime('%Y%m%d%H%M')}",
            ecn_title="Phase 1 测试 ECN 审批流程",
            ecn_type="MECHANICAL_STRUCTURE",
            source_type="MANUAL",
            source_no="TEST001",
            source_id=1,
            project_id=project.id,
            machine_id=1,
            change_reason="测试 ECN 审批流程功能",
            change_description="这是一个用于测试 Phase 1 ECN 审批流程和委托审批功能的测试 ECN。",
            change_scope="COMPONENT_LEVEL",
            priority="NORMAL",
            urgency="NORMAL",
            cost_impact=0.0,
            schedule_impact_days=0,
            quality_impact="NONE",
            status="DRAFT",  # 草稿状态，可以提交审批
            current_step="DRAFT",
            applicant_id=applicant.id,
            applicant_dept="研发部",
            applied_at=datetime.now(),
            created_by=applicant.id,
        )

        session.add(test_ecn)
        session.commit()

        # Save values before session closes
        ecn_id = test_ecn.id
        ecn_no = test_ecn.ecn_no
        ecn_title = test_ecn.ecn_title
        ecn_status = test_ecn.status
        username = applicant.username
        project_name = project.project_name

        print("\n✅ 成功创建测试 ECN:")
        print(f"  - ECN No: {ecn_no}")
        print(f"  - ECN ID: {ecn_id}")
        print(f"  - Title: {ecn_title}")
        print(f"  - Status: {ecn_status}")
        print(f"  - Applicant: {username}")
        print(f"  - Project: {project_name}")

        # Return a simple dict instead of detached object
        return (
            {"id": ecn_id, "ecn_no": ecn_no, "title": ecn_title, "status": ecn_status},
            applicant,
            test_users[1] if len(test_users) > 1 else applicant,
        )


def check_approval_template():
    """检查审批模板是否配置"""
    with get_db_session() as session:
        from app.models.approval import ApprovalTemplate

        templates = (
            session.query(ApprovalTemplate)
            .filter(ApprovalTemplate.entity_type == "ECN")
            .all()
        )

        print("\n📋 检查审批模板:")
        if templates:
            print(f"✅ 找到 {len(templates)} 个 ECN 审批模板:")
            for template in templates:
                print(
                    f"  - ID: {template.id}, Name: {template.template_name}, Version: {template.version}"
                )
        else:
            print("❌ 没有找到 ECN 审批模板")
            print("提示: 需要先创建 ECN 审批模板才能提交审批")


if __name__ == "__main__":
    print("=" * 60)
    print("ECN 测试数据创建脚本")
    print("=" * 60)

    # 检查审批模板
    check_approval_template()

    # 创建测试 ECN
    ecn, applicant, approver = create_test_ecn()

    if ecn:
        print("\n" + "=" * 60)
        print("🎉 测试数据创建成功！")
        print("=" * 60)
        print("\n📝 后续测试步骤:")
        print(f"1. 使用 ECN ID: {ecn['id']} 提交审批")
        print(f"2. 审批人: {applicant.username if applicant else 'N/A'}")
        print("3. 测试审批、拒绝、委托审批等功能")
        print("\n🔗 API 示例:")
        print("  POST /api/v1/approvals/submit")
        print(f'  {{"entity_type": "ECN", "entity_id": {ecn["id"]}}}')
    else:
        print("\n❌ 测试数据创建失败，请检查数据库初始化状态")
        sys.exit(1)
