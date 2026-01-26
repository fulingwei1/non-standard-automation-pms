# -*- coding: utf-8 -*-
"""
项目贡献度服务单元测试

测试 ProjectContributionService 的核心功能:
- 计算成员贡献度
- 获取项目贡献度列表
- 获取用户项目贡献汇总
- 项目经理评分
- 生成贡献度报告
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.project_contribution_service import ProjectContributionService


class TestProjectContributionService:
    """项目贡献度服务测试"""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = ProjectContributionService(db_session)
        assert service.db == db_session
        assert service.bonus_service is not None


class TestCalculateMemberContribution:
    """计算成员贡献度测试"""

    def test_calculate_new_contribution(
        self, db_session: Session, mock_project, test_user
    ):
        """测试计算新的贡献度记录"""
        service = ProjectContributionService(db_session)
        period = date.today().strftime("%Y-%m")

        contribution = service.calculate_member_contribution(
            project_id=mock_project.id,
            user_id=test_user.id,
            period=period
        )

        assert contribution is not None
        assert contribution.project_id == mock_project.id
        assert contribution.user_id == test_user.id
        assert contribution.period == period

    def test_calculate_existing_contribution_update(
        self, db_session: Session, mock_project, test_user
    ):
        """测试更新已存在的贡献度记录"""
        service = ProjectContributionService(db_session)
        period = date.today().strftime("%Y-%m")

        # 第一次计算
        contribution1 = service.calculate_member_contribution(
            project_id=mock_project.id,
            user_id=test_user.id,
            period=period
        )
        contribution_id = contribution1.id

        # 第二次计算（应该更新而不是创建新记录）
        contribution2 = service.calculate_member_contribution(
            project_id=mock_project.id,
            user_id=test_user.id,
            period=period
        )

        assert contribution2.id == contribution_id

    def test_calculate_contribution_fields(
        self, db_session: Session, mock_project, test_user
    ):
        """测试贡献度记录的字段计算"""
        service = ProjectContributionService(db_session)
        period = date.today().strftime("%Y-%m")

        contribution = service.calculate_member_contribution(
            project_id=mock_project.id,
            user_id=test_user.id,
            period=period
        )

        # 验证字段存在
        assert hasattr(contribution, "task_count")
        assert hasattr(contribution, "task_hours")
        assert hasattr(contribution, "actual_hours")
        assert hasattr(contribution, "deliverable_count")
        assert hasattr(contribution, "issue_count")
        assert hasattr(contribution, "issue_resolved")
        assert hasattr(contribution, "bonus_amount")
        assert hasattr(contribution, "contribution_score")


class TestCalculateContributionScore:
    """贡献度评分计算测试"""

    def test_calculate_score_zero_values(self, db_session: Session):
        """测试所有值为零时的评分"""
        service = ProjectContributionService(db_session)

        mock_contribution = MagicMock()
        mock_contribution.task_count = 0
        mock_contribution.actual_hours = 0
        mock_contribution.deliverable_count = 0
        mock_contribution.issue_resolved = 0
        mock_contribution.bonus_amount = Decimal("0")

        score = service._calculate_contribution_score(mock_contribution)
        assert score == Decimal("0")

    def test_calculate_score_with_tasks(self, db_session: Session):
        """测试有任务完成时的评分"""
        service = ProjectContributionService(db_session)

        mock_contribution = MagicMock()
        mock_contribution.task_count = 10
        mock_contribution.actual_hours = 0
        mock_contribution.deliverable_count = 0
        mock_contribution.issue_resolved = 0
        mock_contribution.bonus_amount = Decimal("0")

        score = service._calculate_contribution_score(mock_contribution)
        assert score > Decimal("0")

    def test_calculate_score_with_all_factors(self, db_session: Session):
        """测试所有因素都有值时的评分"""
        service = ProjectContributionService(db_session)

        mock_contribution = MagicMock()
        mock_contribution.task_count = 10
        mock_contribution.actual_hours = 80
        mock_contribution.deliverable_count = 5
        mock_contribution.issue_resolved = 3
        mock_contribution.bonus_amount = Decimal("10000")

        score = service._calculate_contribution_score(mock_contribution)
        assert score > Decimal("0")


class TestGetProjectContributions:
    """获取项目贡献度列表测试"""

    def test_get_contributions_empty(self, db_session: Session, mock_project):
        """测试无贡献度数据时返回空列表"""
        service = ProjectContributionService(db_session)
        contributions = service.get_project_contributions(
            project_id=mock_project.id
        )
        assert contributions == []

    def test_get_contributions_with_period(
        self, db_session: Session, mock_project
    ):
        """测试按周期筛选贡献度"""
        service = ProjectContributionService(db_session)
        period = date.today().strftime("%Y-%m")

        contributions = service.get_project_contributions(
            project_id=mock_project.id,
            period=period
        )
        assert isinstance(contributions, list)

    def test_get_contributions_after_calculation(
        self, db_session: Session, mock_project, test_user
    ):
        """测试计算后能获取到贡献度记录"""
        service = ProjectContributionService(db_session)
        period = date.today().strftime("%Y-%m")

        # 先计算
        service.calculate_member_contribution(
            project_id=mock_project.id,
            user_id=test_user.id,
            period=period
        )

        # 然后获取
        contributions = service.get_project_contributions(
            project_id=mock_project.id,
            period=period
        )

        assert len(contributions) == 1
        assert contributions[0].user_id == test_user.id


class TestGetUserProjectContributions:
    """获取用户项目贡献汇总测试"""

    def test_get_user_contributions_empty(
        self, db_session: Session, test_user
    ):
        """测试用户无贡献度数据时返回空列表"""
        service = ProjectContributionService(db_session)
        contributions = service.get_user_project_contributions(
            user_id=test_user.id
        )
        assert contributions == []

    def test_get_user_contributions_with_period_range(
        self, db_session: Session, test_user
    ):
        """测试按周期范围筛选用户贡献度"""
        service = ProjectContributionService(db_session)
        start_period = "2024-01"
        end_period = "2024-12"

        contributions = service.get_user_project_contributions(
            user_id=test_user.id,
            start_period=start_period,
            end_period=end_period
        )
        assert isinstance(contributions, list)


class TestRateMemberContribution:
    """项目经理评分测试"""

    def test_rate_contribution_valid_rating(
        self, db_session: Session, mock_project, test_user, test_pm_user
    ):
        """测试有效的评分"""
        service = ProjectContributionService(db_session)
        period = date.today().strftime("%Y-%m")

        contribution = service.rate_member_contribution(
            project_id=mock_project.id,
            user_id=test_user.id,
            period=period,
            pm_rating=4,
            rater_id=test_pm_user.id
        )

        assert contribution.pm_rating == 4

    def test_rate_contribution_invalid_rating_too_low(
        self, db_session: Session, mock_project, test_user, test_pm_user
    ):
        """测试评分过低时抛出异常"""
        service = ProjectContributionService(db_session)
        period = date.today().strftime("%Y-%m")

        with pytest.raises(ValueError, match="评分必须在1-5之间"):
            service.rate_member_contribution(
                project_id=mock_project.id,
                user_id=test_user.id,
                period=period,
                pm_rating=0,
                rater_id=test_pm_user.id
            )

    def test_rate_contribution_invalid_rating_too_high(
        self, db_session: Session, mock_project, test_user, test_pm_user
    ):
        """测试评分过高时抛出异常"""
        service = ProjectContributionService(db_session)
        period = date.today().strftime("%Y-%m")

        with pytest.raises(ValueError, match="评分必须在1-5之间"):
            service.rate_member_contribution(
                project_id=mock_project.id,
                user_id=test_user.id,
                period=period,
                pm_rating=6,
                rater_id=test_pm_user.id
            )

    def test_rate_contribution_creates_if_not_exists(
        self, db_session: Session, mock_project, test_user, test_pm_user
    ):
        """测试评分时如果贡献度不存在则自动创建"""
        service = ProjectContributionService(db_session)
        period = date.today().strftime("%Y-%m")

        # 直接评分（不先计算）
        contribution = service.rate_member_contribution(
            project_id=mock_project.id,
            user_id=test_user.id,
            period=period,
            pm_rating=5,
            rater_id=test_pm_user.id
        )

        assert contribution is not None
        assert contribution.pm_rating == 5


class TestGenerateContributionReport:
    """生成贡献度报告测试"""

    def test_generate_report_empty_project(
        self, db_session: Session, mock_project
    ):
        """测试无贡献度数据项目的报告"""
        service = ProjectContributionService(db_session)
        report = service.generate_contribution_report(
            project_id=mock_project.id
        )

        assert report["project_id"] == mock_project.id
        assert report["total_members"] == 0
        assert report["total_task_count"] == 0
        assert report["total_hours"] == 0
        assert report["total_bonus"] == 0
        assert report["contributions"] == []
        assert report["top_contributors"] == []

    def test_generate_report_with_period(
        self, db_session: Session, mock_project
    ):
        """测试按周期生成报告"""
        service = ProjectContributionService(db_session)
        period = date.today().strftime("%Y-%m")

        report = service.generate_contribution_report(
            project_id=mock_project.id,
            period=period
        )

        assert report["period"] == period

    def test_generate_report_structure(
        self, db_session: Session, mock_project, test_user
    ):
        """测试报告数据结构"""
        service = ProjectContributionService(db_session)
        period = date.today().strftime("%Y-%m")

        # 先计算一个贡献度
        service.calculate_member_contribution(
            project_id=mock_project.id,
            user_id=test_user.id,
            period=period
        )

        report = service.generate_contribution_report(
            project_id=mock_project.id,
            period=period
        )

        # 验证报告结构
        assert "project_id" in report
        assert "period" in report
        assert "total_members" in report
        assert "total_task_count" in report
        assert "total_hours" in report
        assert "total_bonus" in report
        assert "contributions" in report
        assert "top_contributors" in report

        # 验证贡献度详情结构
        assert len(report["contributions"]) == 1
        contrib = report["contributions"][0]
        assert "user_id" in contrib
        assert "user_name" in contrib
        assert "task_count" in contrib
        assert "actual_hours" in contrib
        assert "deliverable_count" in contrib
        assert "issue_resolved" in contrib
        assert "bonus_amount" in contrib
        assert "contribution_score" in contrib
        assert "pm_rating" in contrib
