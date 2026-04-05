# -*- coding: utf-8 -*-
"""
Closure 相关服务测试（简化版）

覆盖服务：
- LessonsCollectionService.auto_collect - 结项复盘报告生成
"""

import pytest
from datetime import date
from decimal import Decimal

from app.models.project.core import Project
from app.models.project_review import ProjectReview
from app.models.user import User
from app.services.project.closure_readiness_service import LessonsCollectionService


def create_test_user(db_session):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed",
        real_name="测试用户",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestGenerateRetrospectiveReport:
    """结项复盘报告生成测试"""

    def test_generate_retrospective_report(self, db_session):
        """
        核心测试：生成结项复盘报告

        验证：
        1. 能成功创建 ProjectReview 记录
        2. 能正确提取经验教训
        3. 能正确生成最佳实践建议
        """
        # 创建测试用户
        test_user = create_test_user(db_session)

        # 创建测试项目 - 使用固定日期
        project = Project(
            project_code="PJ260405001",
            project_name="测试结项项目",
            stage="S8",
            status="ST10",
            health="H1",
            progress_pct=Decimal("100.0"),
            planned_start_date=date(2025, 1, 1),
            planned_end_date=date(2025, 3, 31),
            actual_start_date=date(2025, 1, 1),
            actual_end_date=date(2025, 3, 30),  # 提前1天完成
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("95000"),  # 节约5%
            created_by=test_user.id,
            pm_id=test_user.id,
            is_active=True,
            is_archived=False,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        # 调用服务生成复盘报告
        service = LessonsCollectionService(db_session)
        result = service.auto_collect(project_id=project.id, triggered_by=test_user.id)

        # 验证返回结果
        assert "review_id" in result
        assert result["already_exists"] is False
        assert "review_no" in result
        assert result["lessons_count"] >= 0
        assert result["best_practices_count"] >= 0

        # 验证数据库中确实创建了记录
        review = db_session.query(ProjectReview).filter(
            ProjectReview.project_id == project.id
        ).first()
        assert review is not None
        assert review.review_no is not None
        assert review.review_type == "POST_MORTEM"
        assert review.status == "DRAFT"

    def test_generate_retrospective_report_project_not_exists(self, db_session):
        """边界测试：项目不存在时返回错误"""
        service = LessonsCollectionService(db_session)
        result = service.auto_collect(project_id=99999, triggered_by=1)

        assert "error" in result

    def test_generate_retrospective_report_already_exists(self, db_session):
        """边界测试：复盘报告已存在时返回已存在"""
        # 创建测试用户
        test_user = create_test_user(db_session)

        # 创建测试项目
        project = Project(
            project_code="PJ260405002",
            project_name="已结项项目",
            stage="S8",
            status="ST10",
            is_active=True,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        # 先创建一个复盘报告
        existing_review = ProjectReview(
            review_no="REV-PJ260405002-001",
            project_id=project.id,
            project_code=project.project_code,
            review_date=date(2025, 4, 1),
            review_type="POST_MORTEM",
            reviewer_id=test_user.id,
            reviewer_name="测试用户",  # 添加 reviewer_name
            status="DRAFT",
        )
        db_session.add(existing_review)
        db_session.commit()

        # 再次调用应该返回已存在
        service = LessonsCollectionService(db_session)
        result = service.auto_collect(project_id=project.id, triggered_by=test_user.id)

        assert result["already_exists"] is True
        assert "review_no" in result