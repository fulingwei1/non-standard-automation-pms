#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术评审数据查询示例脚本
演示如何查询评审、参与人、材料、检查项、问题等数据
"""

import sys

sys.path.insert(0, '.')

from sqlalchemy.orm import Session

from app.models.base import get_db_session
from app.models.technical_review import (
    ReviewIssue,
    TechnicalReview,
)
from app.models.user import User


def query_review_list(db: Session, project_id: int = None):
    """查询评审列表"""
    query = db.query(TechnicalReview)
    if project_id:
        query = query.filter(TechnicalReview.project_id == project_id)

    reviews = query.order_by(TechnicalReview.created_at.desc()).limit(10).all()

    print("\n" + "=" * 70)
    print("技术评审列表")
    print("=" * 70)
    for review in reviews:
        print(f"\n评审编号: {review.review_no}")
        print(f"  类型: {review.review_type} | 名称: {review.review_name}")
        print(f"  项目: {review.project_no}")
        print(f"  状态: {review.status} | 结论: {review.conclusion or '未完成'}")
        print(f"  计划时间: {review.scheduled_date}")
        print(f"  问题统计: A类{review.issue_count_a} B类{review.issue_count_b} "
              f"C类{review.issue_count_c} D类{review.issue_count_d}")


def query_review_detail(db: Session, review_no: str):
    """查询评审详情（包含所有关联数据）"""
    review = db.query(TechnicalReview).filter(
        TechnicalReview.review_no == review_no
    ).first()

    if not review:
        print(f"❌ 未找到评审: {review_no}")
        return

    print("\n" + "=" * 70)
    print(f"评审详情: {review.review_no}")
    print("=" * 70)

    print(f"\n基本信息:")
    print(f"  评审编号: {review.review_no}")
    print(f"  评审类型: {review.review_type}")
    print(f"  评审名称: {review.review_name}")
    print(f"  项目编号: {review.project_no}")
    print(f"  状态: {review.status}")
    print(f"  计划时间: {review.scheduled_date}")
    print(f"  实际时间: {review.actual_date or '未开始'}")
    print(f"  地点: {review.location or '未设置'}")
    print(f"  会议形式: {review.meeting_type}")

    if review.conclusion:
        print(f"\n评审结论:")
        print(f"  结论: {review.conclusion}")
        print(f"  说明: {review.conclusion_summary or '无'}")
        if review.condition_deadline:
            print(f"  整改期限: {review.condition_deadline}")
        if review.next_review_date:
            print(f"  下次复审: {review.next_review_date}")

    # 参与人
    participants = review.participants.all()
    print(f"\n参与人 ({len(participants)} 位):")
    for p in participants:
        user = db.query(User).filter(User.id == p.user_id).first()
        name = user.real_name or user.username if user else f"用户{p.user_id}"
        required = "必需" if p.is_required else "可选"
        attendance = p.attendance or "待确认"
        print(f"  - {name} ({p.role}, {required}, {attendance})")

    # 材料
    materials = review.materials.all()
    print(f"\n评审材料 ({len(materials)} 份):")
    for m in materials:
        uploader = db.query(User).filter(User.id == m.upload_by).first()
        uploader_name = uploader.real_name or uploader.username if uploader else f"用户{m.upload_by}"
        size_mb = m.file_size / 1024 / 1024
        required = "必需" if m.is_required else "可选"
        print(f"  - [{m.material_type}] {m.material_name}")
        print(f"    大小: {size_mb:.2f}MB | {required} | 上传人: {uploader_name}")

    # 检查项
    checklist = review.checklist_records.all()
    print(f"\n检查项记录 ({len(checklist)} 条):")
    pass_count = sum(1 for c in checklist if c.result == 'PASS')
    fail_count = sum(1 for c in checklist if c.result == 'FAIL')
    na_count = sum(1 for c in checklist if c.result == 'NA')
    print(f"  统计: 通过 {pass_count} | 不通过 {fail_count} | 不适用 {na_count}")

    for c in checklist:
        checker = db.query(User).filter(User.id == c.checker_id).first()
        checker_name = checker.real_name or checker.username if checker else f"用户{c.checker_id}"
        result_icon = "✓" if c.result == "PASS" else "✗" if c.result == "FAIL" else "-"
        issue_info = f" (问题: {c.issue_level}类)" if c.issue_level else ""
        print(f"  {result_icon} [{c.category}] {c.check_item}{issue_info}")
        if c.remark:
            print(f"    备注: {c.remark}")

    # 问题
    issues = review.issues.all()
    print(f"\n评审问题 ({len(issues)} 个):")
    for i in issues:
        assignee = db.query(User).filter(User.id == i.assignee_id).first()
        assignee_name = assignee.real_name or assignee.username if assignee else f"用户{i.assignee_id}"
        verifier_name = None
        if i.verifier_id:
            verifier = db.query(User).filter(User.id == i.verifier_id).first()
            verifier_name = verifier.real_name or verifier.username if verifier else f"用户{i.verifier_id}"

        print(f"\n  [{i.issue_level}类] {i.issue_no}")
        print(f"    类别: {i.category}")
        print(f"    描述: {i.description}")
        if i.suggestion:
            print(f"    建议: {i.suggestion}")
        print(f"    状态: {i.status}")
        print(f"    责任人: {assignee_name}")
        print(f"    期限: {i.deadline}")
        if i.solution:
            print(f"    解决方案: {i.solution}")
        if i.verify_result:
            print(f"    验证结果: {i.verify_result} (验证人: {verifier_name})")


def query_issues_by_status(db: Session, status: str = None):
    """按状态查询问题"""
    query = db.query(ReviewIssue)
    if status:
        query = query.filter(ReviewIssue.status == status)

    issues = query.order_by(ReviewIssue.deadline).all()

    print("\n" + "=" * 70)
    print(f"评审问题列表 ({len(issues)} 个)")
    print("=" * 70)

    # 按等级分组
    by_level = {}
    for issue in issues:
        level = issue.issue_level
        if level not in by_level:
            by_level[level] = []
        by_level[level].append(issue)

    for level in ['A', 'B', 'C', 'D']:
        if level in by_level:
            print(f"\n{level}类问题 ({len(by_level[level])} 个):")
            for issue in by_level[level]:
                review = db.query(TechnicalReview).filter(
                    TechnicalReview.id == issue.review_id
                ).first()
                review_name = review.review_name if review else f"评审{issue.review_id}"
                print(f"  - {issue.issue_no} [{issue.status}] {issue.description[:50]}...")
                print(f"    评审: {review_name} | 期限: {issue.deadline}")


def main():
    with get_db_session() as db:
        # 1. 查询评审列表
        query_review_list(db)

        # 2. 查询最新评审的详情
        latest_review = db.query(TechnicalReview).order_by(
            TechnicalReview.created_at.desc()
        ).first()

        if latest_review:
            query_review_detail(db, latest_review.review_no)

        # 3. 查询所有开放状态的问题
        query_issues_by_status(db, status='OPEN')

        print("\n" + "=" * 70)
        print("查询完成")
        print("=" * 70)


if __name__ == "__main__":
    main()






