#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术评审模块功能测试脚本
演示：创建评审、添加参与人、上传材料、创建检查项、创建问题
"""

import sys
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

# 添加项目路径
sys.path.insert(0, '.')

from app.models.base import get_db_session
from app.models.technical_review import (
    TechnicalReview, ReviewParticipant, ReviewMaterial,
    ReviewChecklistRecord, ReviewIssue
)
from app.models.project import Project
from app.models.user import User


def generate_review_no(db: Session, review_type: str) -> str:
    """生成评审编号"""
    from sqlalchemy import desc
    today = datetime.now().strftime("%y%m%d")
    prefix = f"RV-{review_type}-{today}-"
    max_review = (
        db.query(TechnicalReview)
        .filter(TechnicalReview.review_no.like(f"{prefix}%"))
        .order_by(desc(TechnicalReview.review_no))
        .first()
    )
    if max_review:
        seq = int(max_review.review_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def generate_issue_no(db: Session) -> str:
    """生成问题编号"""
    from sqlalchemy import desc
    today = datetime.now().strftime("%y%m%d")
    prefix = f"RV-ISSUE-{today}-"
    max_issue = (
        db.query(ReviewIssue)
        .filter(ReviewIssue.issue_no.like(f"{prefix}%"))
        .order_by(desc(ReviewIssue.issue_no))
        .first()
    )
    if max_issue:
        seq = int(max_issue.issue_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def main():
    print("=" * 70)
    print("技术评审模块功能测试")
    print("=" * 70)
    
    with get_db_session() as db:
        # 1. 获取测试数据
        print("\n[步骤1] 获取测试数据...")
        project = db.query(Project).filter(Project.project_code == "DEMO001").first()
        if not project:
            print("❌ 未找到测试项目，请先创建项目")
            return
        
        users = db.query(User).limit(5).all()
        if len(users) < 3:
            print("❌ 用户数据不足，至少需要3个用户")
            return
        
        host = users[0]
        presenter = users[1]
        recorder = users[2]
        expert1 = users[3] if len(users) > 3 else users[0]
        expert2 = users[4] if len(users) > 4 else users[1]
        
        print(f"✓ 项目: {project.project_code} - {project.project_name}")
        print(f"✓ 主持人: {host.real_name or host.username}")
        print(f"✓ 汇报人: {presenter.real_name or presenter.username}")
        print(f"✓ 记录人: {recorder.real_name or recorder.username}")
        
        # 2. 创建技术评审
        print("\n[步骤2] 创建技术评审...")
        review_no = generate_review_no(db, "PDR")
        review = TechnicalReview(
            review_no=review_no,
            review_type="PDR",
            review_name="DEMO001项目方案设计评审",
            project_id=project.id,
            project_no=project.project_code,
            status="PENDING",
            scheduled_date=datetime.now() + timedelta(days=3),
            location="会议室A",
            meeting_type="ONSITE",
            host_id=host.id,
            presenter_id=presenter.id,
            recorder_id=recorder.id,
            created_by=host.id,
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        print(f"✓ 评审已创建: {review.review_no}")
        print(f"  - 类型: {review.review_type}")
        print(f"  - 名称: {review.review_name}")
        print(f"  - 状态: {review.status}")
        print(f"  - 计划时间: {review.scheduled_date}")
        
        # 3. 添加参与人
        print("\n[步骤3] 添加评审参与人...")
        participants_data = [
            {"user": host, "role": "HOST", "required": True},
            {"user": presenter, "role": "PRESENTER", "required": True},
            {"user": recorder, "role": "RECORDER", "required": True},
            {"user": expert1, "role": "EXPERT", "required": True},
            {"user": expert2, "role": "EXPERT", "required": False},
        ]
        
        participants = []
        for p_data in participants_data:
            participant = ReviewParticipant(
                review_id=review.id,
                user_id=p_data["user"].id,
                role=p_data["role"],
                is_required=p_data["required"],
                attendance="PENDING",
            )
            db.add(participant)
            participants.append(participant)
            print(f"✓ 添加参与人: {p_data['user'].real_name or p_data['user'].username} ({p_data['role']})")
        
        db.commit()
        print(f"✓ 共添加 {len(participants)} 位参与人")
        
        # 4. 上传评审材料
        print("\n[步骤4] 上传评审材料...")
        materials_data = [
            {
                "type": "DRAWING",
                "name": "设备总装图V1.0.pdf",
                "path": "/uploads/reviews/demo001/总装图.pdf",
                "size": 2048576,
                "required": True,
            },
            {
                "type": "BOM",
                "name": "物料清单V1.0.xlsx",
                "path": "/uploads/reviews/demo001/BOM清单.xlsx",
                "size": 512000,
                "required": True,
            },
            {
                "type": "REPORT",
                "name": "技术方案报告V1.0.docx",
                "path": "/uploads/reviews/demo001/技术方案.docx",
                "size": 1024000,
                "required": True,
            },
            {
                "type": "DOCUMENT",
                "name": "参考标准.pdf",
                "path": "/uploads/reviews/demo001/参考标准.pdf",
                "size": 307200,
                "required": False,
            },
        ]
        
        materials = []
        for m_data in materials_data:
            material = ReviewMaterial(
                review_id=review.id,
                material_type=m_data["type"],
                material_name=m_data["name"],
                file_path=m_data["path"],
                file_size=m_data["size"],
                is_required=m_data["required"],
                upload_by=host.id,
            )
            db.add(material)
            materials.append(material)
            required_str = "必需" if m_data["required"] else "可选"
            print(f"✓ 上传材料: {m_data['name']} ({m_data['type']}, {required_str})")
        
        db.commit()
        print(f"✓ 共上传 {len(materials)} 份材料")
        
        # 5. 创建检查项记录
        print("\n[步骤5] 创建评审检查项记录...")
        checklist_data = [
            {
                "category": "机械设计",
                "item": "结构设计是否合理，是否存在干涉",
                "result": "PASS",
                "checker": expert1,
            },
            {
                "category": "电气设计",
                "item": "电气原理图是否正确，接线是否规范",
                "result": "PASS",
                "checker": expert2,
            },
            {
                "category": "安全设计",
                "item": "安全防护措施是否完善",
                "result": "FAIL",
                "checker": expert1,
                "issue_level": "B",
                "issue_desc": "缺少急停按钮的二次确认机制",
            },
            {
                "category": "工艺可行性",
                "item": "加工工艺是否成熟，是否便于装配",
                "result": "PASS",
                "checker": expert2,
            },
            {
                "category": "成本控制",
                "item": "物料成本是否在预算范围内",
                "result": "FAIL",
                "checker": expert1,
                "issue_level": "C",
                "issue_desc": "部分进口物料成本偏高，建议寻找替代方案",
            },
        ]
        
        checklist_records = []
        for c_data in checklist_data:
            record = ReviewChecklistRecord(
                review_id=review.id,
                category=c_data["category"],
                check_item=c_data["item"],
                result=c_data["result"],
                issue_level=c_data.get("issue_level"),
                issue_desc=c_data.get("issue_desc"),
                checker_id=c_data["checker"].id,
                remark=None,
            )
            db.add(record)
            db.flush()  # 获取ID
            
            # 如果不通过，自动创建问题
            if c_data["result"] == "FAIL" and c_data.get("issue_level") and c_data.get("issue_desc"):
                issue_no = generate_issue_no(db)
                issue = ReviewIssue(
                    review_id=review.id,
                    issue_no=issue_no,
                    issue_level=c_data["issue_level"],
                    category=c_data["category"],
                    description=c_data["issue_desc"],
                    assignee_id=c_data["checker"].id,
                    deadline=date.today() + timedelta(days=7),
                    status="OPEN",
                )
                db.add(issue)
                db.flush()
                record.issue_id = issue.id
                print(f"✓ 检查项: {c_data['category']} - {c_data['item']}")
                print(f"  → 结果: {c_data['result']} (自动创建问题: {issue_no})")
            else:
                print(f"✓ 检查项: {c_data['category']} - {c_data['item']} ({c_data['result']})")
            
            checklist_records.append(record)
        
        db.commit()
        print(f"✓ 共创建 {len(checklist_records)} 条检查项记录")
        
        # 6. 手动创建问题
        print("\n[步骤6] 手动创建评审问题...")
        manual_issue = ReviewIssue(
            review_id=review.id,
            issue_no=generate_issue_no(db),
            issue_level="A",
            category="设计缺陷",
            description="关键部件选型不当，可能导致设备寿命缩短",
            suggestion="建议更换为更高规格的部件，并重新进行寿命计算",
            assignee_id=presenter.id,
            deadline=date.today() + timedelta(days=5),
            status="OPEN",
        )
        db.add(manual_issue)
        db.commit()
        db.refresh(manual_issue)
        print(f"✓ 问题已创建: {manual_issue.issue_no}")
        print(f"  - 等级: {manual_issue.issue_level}")
        print(f"  - 描述: {manual_issue.description}")
        print(f"  - 责任人: {presenter.real_name or presenter.username}")
        print(f"  - 期限: {manual_issue.deadline}")
        
        # 7. 更新问题统计
        print("\n[步骤7] 更新问题统计...")
        issues = db.query(ReviewIssue).filter(ReviewIssue.review_id == review.id).all()
        review.issue_count_a = sum(1 for i in issues if i.issue_level == 'A')
        review.issue_count_b = sum(1 for i in issues if i.issue_level == 'B')
        review.issue_count_c = sum(1 for i in issues if i.issue_level == 'C')
        review.issue_count_d = sum(1 for i in issues if i.issue_level == 'D')
        db.commit()
        print(f"✓ 问题统计更新:")
        print(f"  - A类: {review.issue_count_a} 个")
        print(f"  - B类: {review.issue_count_b} 个")
        print(f"  - C类: {review.issue_count_c} 个")
        print(f"  - D类: {review.issue_count_d} 个")
        
        # 8. 模拟问题处理流程
        print("\n[步骤8] 模拟问题处理流程...")
        # 处理B类问题
        b_issues = [i for i in issues if i.issue_level == 'B']
        if b_issues:
            issue = b_issues[0]
            issue.status = "PROCESSING"
            issue.solution = "已添加急停按钮二次确认功能，修改电气原理图"
            db.commit()
            print(f"✓ 问题 {issue.issue_no} 状态更新为: 处理中")
            print(f"  - 解决方案: {issue.solution}")
            
            # 验证问题
            issue.status = "RESOLVED"
            issue.verify_result = "PASS"
            issue.verifier_id = expert1.id
            issue.verify_time = datetime.now()
            db.commit()
            print(f"✓ 问题 {issue.issue_no} 已验证通过")
        
        # 9. 完成评审
        print("\n[步骤9] 完成评审...")
        review.status = "IN_PROGRESS"
        review.actual_date = datetime.now()
        review.conclusion = "PASS_WITH_CONDITION"
        review.conclusion_summary = "评审通过，但需要整改发现的问题后才能进入下一阶段"
        review.condition_deadline = date.today() + timedelta(days=7)
        db.commit()
        print(f"✓ 评审状态更新为: {review.status}")
        print(f"✓ 评审结论: {review.conclusion}")
        print(f"✓ 结论说明: {review.conclusion_summary}")
        print(f"✓ 整改期限: {review.condition_deadline}")
        
        # 10. 汇总信息
        print("\n" + "=" * 70)
        print("测试完成 - 数据汇总")
        print("=" * 70)
        print(f"\n评审信息:")
        print(f"  - 评审编号: {review.review_no}")
        print(f"  - 评审名称: {review.review_name}")
        print(f"  - 评审状态: {review.status}")
        print(f"  - 评审结论: {review.conclusion}")
        
        print(f"\n参与人: {len(participants)} 位")
        print(f"材料: {len(materials)} 份")
        print(f"检查项: {len(checklist_records)} 条")
        print(f"问题: {len(issues)} 个")
        print(f"  - A类: {review.issue_count_a}")
        print(f"  - B类: {review.issue_count_b}")
        print(f"  - C类: {review.issue_count_c}")
        print(f"  - D类: {review.issue_count_d}")
        
        print("\n" + "=" * 70)
        print("✓ 所有功能测试完成！")
        print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)






