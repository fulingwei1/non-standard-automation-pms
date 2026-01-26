# -*- coding: utf-8 -*-
"""
ProjectContributionService 单元测试
测试项目贡献度计算服务的各项功能
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, PropertyMock

import pytest
from sqlalchemy.orm import Session

from app.models.issue import Issue
from app.models.project import (
    Project,
    ProjectDocument,
    ProjectMember,
    ProjectMemberContribution,
)
from app.models.task_center import TaskUnified
from app.models.user import User
from app.services.project_contribution_service import ProjectContributionService


class TestProjectContributionServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        mock_db = MagicMock(spec=Session)
        service = ProjectContributionService(mock_db)
        assert service.db == mock_db
        assert service.bonus_service is not None


class TestCalculateMemberContribution:
    """测试计算成员贡献度"""

    @patch("app.services.project_contribution_service.ProjectBonusService")
    def test_calculate_contribution_creates_new_record(self, mock_bonus_service_class):
        """测试创建新的贡献度记录"""
        mock_db = MagicMock(spec=Session)

        # 查询不到已有记录
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock 任务查询返回空
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # Mock bonus service
        mock_bonus_service = MagicMock()
        mock_bonus_service.get_project_bonus_calculations.return_value = []
        mock_bonus_service_class.return_value = mock_bonus_service

        service = ProjectContributionService(mock_db)
        service.bonus_service = mock_bonus_service

        # 执行计算
        result = service.calculate_member_contribution(
            project_id=1,
            user_id=1,
            period="2024-06"
        )

        # 验证添加了新记录
        assert mock_db.add.called

    @patch("app.services.project_contribution_service.ProjectBonusService")
    def test_calculate_contribution_updates_existing_record(self, mock_bonus_service_class):
        """测试更新已有的贡献度记录"""
        mock_db = MagicMock(spec=Session)

        # Mock 已有贡献度记录
        mock_contribution = Mock(spec=ProjectMemberContribution)
        mock_contribution.project_id = 1
        mock_contribution.user_id = 1
        mock_contribution.period = "2024-06"
        mock_contribution.task_count = 0
        mock_contribution.task_hours = 0
        mock_contribution.actual_hours = 0
        mock_contribution.deliverable_count = 0
        mock_contribution.issue_count = 0
        mock_contribution.issue_resolved = 0
        mock_contribution.bonus_amount = Decimal("0")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contribution
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # Mock bonus service
        mock_bonus_service = MagicMock()
        mock_bonus_service.get_project_bonus_calculations.return_value = []
        mock_bonus_service_class.return_value = mock_bonus_service

        service = ProjectContributionService(mock_db)
        service.bonus_service = mock_bonus_service

        result = service.calculate_member_contribution(
            project_id=1,
            user_id=1,
            period="2024-06"
        )

        # 不应该添加新记录
        assert not mock_db.add.called or mock_db.add.call_count == 0

    @patch("app.services.project_contribution_service.ProjectBonusService")
    def test_calculate_contribution_with_tasks(self, mock_bonus_service_class):
        """测试包含任务统计的贡献度计算"""
        mock_db = MagicMock(spec=Session)

        # 第一次查询返回 None (贡献度记录不存在)
        # 后续查询返回任务列表
        mock_contribution = None

        mock_task1 = Mock(spec=TaskUnified)
        mock_task1.status = "COMPLETED"
        mock_task1.estimated_hours = 8
        mock_task1.actual_hours = 10

        mock_task2 = Mock(spec=TaskUnified)
        mock_task2.status = "IN_PROGRESS"
        mock_task2.estimated_hours = 4
        mock_task2.actual_hours = 5

        # 配置查询行为
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = mock_contribution
        query_mock.filter.return_value.all.return_value = [mock_task1, mock_task2]
        mock_db.query.return_value = query_mock

        # Mock bonus service
        mock_bonus_service = MagicMock()
        mock_bonus_service.get_project_bonus_calculations.return_value = []
        mock_bonus_service_class.return_value = mock_bonus_service

        service = ProjectContributionService(mock_db)
        service.bonus_service = mock_bonus_service

        # 执行
        result = service.calculate_member_contribution(
            project_id=1,
            user_id=1,
            period="2024-06"
        )

        # 验证添加了新记录
        assert mock_db.add.called


class TestCalculateContributionScore:
    """测试贡献度评分计算"""

    def test_calculate_score_all_zeros(self):
        """测试所有指标为零时的评分"""
        mock_db = MagicMock(spec=Session)
        service = ProjectContributionService(mock_db)

        mock_contribution = Mock()
        mock_contribution.task_count = 0
        mock_contribution.actual_hours = 0
        mock_contribution.deliverable_count = 0
        mock_contribution.issue_resolved = 0
        mock_contribution.bonus_amount = Decimal("0")

        result = service._calculate_contribution_score(mock_contribution)

        assert result == Decimal("0")

    def test_calculate_score_with_tasks(self):
        """测试有任务完成时的评分"""
        mock_db = MagicMock(spec=Session)
        service = ProjectContributionService(mock_db)

        mock_contribution = Mock()
        mock_contribution.task_count = 10
        mock_contribution.actual_hours = 0
        mock_contribution.deliverable_count = 0
        mock_contribution.issue_resolved = 0
        mock_contribution.bonus_amount = Decimal("0")

        result = service._calculate_contribution_score(mock_contribution)

        # task_count * 0.3 = 10 * 0.3 = 3
        assert result == Decimal("3")

    def test_calculate_score_with_hours(self):
        """测试有工时时的评分"""
        mock_db = MagicMock(spec=Session)
        service = ProjectContributionService(mock_db)

        mock_contribution = Mock()
        mock_contribution.task_count = 0
        mock_contribution.actual_hours = 100
        mock_contribution.deliverable_count = 0
        mock_contribution.issue_resolved = 0
        mock_contribution.bonus_amount = Decimal("0")

        result = service._calculate_contribution_score(mock_contribution)

        # actual_hours * 0.2 / 10 = 100 * 0.2 / 10 = 2
        assert result == Decimal("2")

    def test_calculate_score_with_deliverables(self):
        """测试有交付物时的评分"""
        mock_db = MagicMock(spec=Session)
        service = ProjectContributionService(mock_db)

        mock_contribution = Mock()
        mock_contribution.task_count = 0
        mock_contribution.actual_hours = 0
        mock_contribution.deliverable_count = 5
        mock_contribution.issue_resolved = 0
        mock_contribution.bonus_amount = Decimal("0")

        result = service._calculate_contribution_score(mock_contribution)

        # deliverable_count * 0.2 = 5 * 0.2 = 1
        assert result == Decimal("1")

    def test_calculate_score_with_issues(self):
        """测试有解决问题时的评分"""
        mock_db = MagicMock(spec=Session)
        service = ProjectContributionService(mock_db)

        mock_contribution = Mock()
        mock_contribution.task_count = 0
        mock_contribution.actual_hours = 0
        mock_contribution.deliverable_count = 0
        mock_contribution.issue_resolved = 10
        mock_contribution.bonus_amount = Decimal("0")

        result = service._calculate_contribution_score(mock_contribution)

        # issue_resolved * 0.2 = 10 * 0.2 = 2
        assert result == Decimal("2")

    def test_calculate_score_with_bonus(self):
        """测试有奖金时的评分"""
        mock_db = MagicMock(spec=Session)
        service = ProjectContributionService(mock_db)

        mock_contribution = Mock()
        mock_contribution.task_count = 0
        mock_contribution.actual_hours = 0
        mock_contribution.deliverable_count = 0
        mock_contribution.issue_resolved = 0
        mock_contribution.bonus_amount = Decimal("50000")

        result = service._calculate_contribution_score(mock_contribution)

        # (bonus / 100000) * 10 * 0.1 = (50000/100000) * 10 * 0.1 = 0.5
        assert result == Decimal("0.5")

    def test_calculate_score_combined(self):
        """测试综合评分"""
        mock_db = MagicMock(spec=Session)
        service = ProjectContributionService(mock_db)

        mock_contribution = Mock()
        mock_contribution.task_count = 10
        mock_contribution.actual_hours = 100
        mock_contribution.deliverable_count = 5
        mock_contribution.issue_resolved = 10
        mock_contribution.bonus_amount = Decimal("50000")

        result = service._calculate_contribution_score(mock_contribution)

        # 3 + 2 + 1 + 2 + 0.5 = 8.5
        assert result == Decimal("8.5")


class TestGetProjectContributions:
    """测试获取项目贡献度列表"""

    def test_get_contributions_without_period(self):
        """测试不指定周期获取所有贡献度"""
        mock_db = MagicMock(spec=Session)

        mock_contribution = Mock(spec=ProjectMemberContribution)
        mock_contribution.project_id = 1
        mock_contribution.user_id = 1

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_contribution]

        service = ProjectContributionService(mock_db)
        result = service.get_project_contributions(project_id=1)

        assert len(result) == 1

    def test_get_contributions_with_period(self):
        """测试指定周期获取贡献度"""
        mock_db = MagicMock(spec=Session)

        mock_contribution = Mock(spec=ProjectMemberContribution)
        mock_contribution.project_id = 1
        mock_contribution.period = "2024-06"

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = [mock_contribution]
        mock_db.query.return_value = query_mock

        service = ProjectContributionService(mock_db)
        result = service.get_project_contributions(project_id=1, period="2024-06")

        assert len(result) == 1


class TestGetUserProjectContributions:
    """测试获取用户项目贡献汇总"""

    def test_get_user_contributions_basic(self):
        """测试基本获取用户贡献"""
        mock_db = MagicMock(spec=Session)

        mock_contribution = Mock(spec=ProjectMemberContribution)
        mock_contribution.user_id = 1

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_contribution]

        service = ProjectContributionService(mock_db)
        result = service.get_user_project_contributions(user_id=1)

        assert len(result) == 1

    def test_get_user_contributions_with_period_range(self):
        """测试指定周期范围获取用户贡献"""
        mock_db = MagicMock(spec=Session)

        mock_contribution = Mock(spec=ProjectMemberContribution)
        mock_contribution.user_id = 1
        mock_contribution.period = "2024-06"

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = [mock_contribution]
        mock_db.query.return_value = query_mock

        service = ProjectContributionService(mock_db)
        result = service.get_user_project_contributions(
            user_id=1,
            start_period="2024-01",
            end_period="2024-12"
        )

        assert len(result) == 1


class TestRateMemberContribution:
    """测试项目经理评分"""

    def test_rate_contribution_invalid_rating_too_low(self):
        """测试评分过低抛出异常"""
        mock_db = MagicMock(spec=Session)
        service = ProjectContributionService(mock_db)

        with pytest.raises(ValueError, match="评分必须在1-5之间"):
            service.rate_member_contribution(
                project_id=1,
                user_id=1,
                period="2024-06",
                pm_rating=0,
                rater_id=2
            )

    def test_rate_contribution_invalid_rating_too_high(self):
        """测试评分过高抛出异常"""
        mock_db = MagicMock(spec=Session)
        service = ProjectContributionService(mock_db)

        with pytest.raises(ValueError, match="评分必须在1-5之间"):
            service.rate_member_contribution(
                project_id=1,
                user_id=1,
                period="2024-06",
                pm_rating=6,
                rater_id=2
            )

    @patch.object(ProjectContributionService, 'calculate_member_contribution')
    def test_rate_contribution_creates_if_not_exists(self, mock_calculate):
        """测试贡献度不存在时先创建"""
        mock_db = MagicMock(spec=Session)

        mock_contribution = Mock(spec=ProjectMemberContribution)
        mock_contribution.contribution_score = Decimal("5")
        mock_contribution.pm_rating = None

        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_calculate.return_value = mock_contribution

        service = ProjectContributionService(mock_db)
        result = service.rate_member_contribution(
            project_id=1,
            user_id=1,
            period="2024-06",
            pm_rating=4,
            rater_id=2
        )

        mock_calculate.assert_called_once_with(1, 1, "2024-06")

    def test_rate_contribution_updates_existing(self):
        """测试更新已有贡献度的评分"""
        mock_db = MagicMock(spec=Session)

        mock_contribution = Mock(spec=ProjectMemberContribution)
        mock_contribution.contribution_score = Decimal("5")
        mock_contribution.pm_rating = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contribution

        service = ProjectContributionService(mock_db)
        result = service.rate_member_contribution(
            project_id=1,
            user_id=1,
            period="2024-06",
            pm_rating=4,
            rater_id=2
        )

        assert mock_contribution.pm_rating == 4
        mock_db.commit.assert_called()
        mock_db.refresh.assert_called_with(mock_contribution)


class TestGenerateContributionReport:
    """测试生成贡献度报告"""

    @patch.object(ProjectContributionService, 'get_project_contributions')
    def test_generate_report_empty(self, mock_get_contributions):
        """测试无贡献数据时的报告"""
        mock_db = MagicMock(spec=Session)
        mock_get_contributions.return_value = []

        service = ProjectContributionService(mock_db)
        result = service.generate_contribution_report(project_id=1)

        assert result['project_id'] == 1
        assert result['total_members'] == 0
        assert result['total_task_count'] == 0
        assert result['total_hours'] == 0.0
        assert result['total_bonus'] == 0.0
        assert result['contributions'] == []
        assert result['top_contributors'] == []

    @patch.object(ProjectContributionService, 'get_project_contributions')
    def test_generate_report_with_data(self, mock_get_contributions):
        """测试有贡献数据时的报告"""
        mock_db = MagicMock(spec=Session)

        # Mock 用户
        mock_user = Mock(spec=User)
        mock_user.username = "user1"
        mock_user.real_name = "用户1"

        # Mock 贡献记录
        mock_contribution = Mock(spec=ProjectMemberContribution)
        mock_contribution.user_id = 1
        mock_contribution.user = mock_user
        mock_contribution.task_count = 5
        mock_contribution.actual_hours = 40.0
        mock_contribution.deliverable_count = 3
        mock_contribution.issue_resolved = 2
        mock_contribution.bonus_amount = Decimal("1000")
        mock_contribution.contribution_score = Decimal("8.5")
        mock_contribution.pm_rating = 4

        mock_get_contributions.return_value = [mock_contribution]

        service = ProjectContributionService(mock_db)
        result = service.generate_contribution_report(project_id=1)

        assert result['project_id'] == 1
        assert result['total_members'] == 1
        assert result['total_task_count'] == 5
        assert result['total_hours'] == 40.0
        assert result['total_bonus'] == 1000.0
        assert len(result['contributions']) == 1
        assert len(result['top_contributors']) == 1

    @patch.object(ProjectContributionService, 'get_project_contributions')
    def test_generate_report_with_period(self, mock_get_contributions):
        """测试指定周期的报告"""
        mock_db = MagicMock(spec=Session)
        mock_get_contributions.return_value = []

        service = ProjectContributionService(mock_db)
        result = service.generate_contribution_report(project_id=1, period="2024-06")

        assert result['period'] == "2024-06"
        mock_get_contributions.assert_called_with(1, "2024-06")

    @patch.object(ProjectContributionService, 'get_project_contributions')
    def test_generate_report_top_10_contributors(self, mock_get_contributions):
        """测试只返回前10名贡献者"""
        mock_db = MagicMock(spec=Session)

        # 创建15个贡献记录
        contributions = []
        for i in range(15):
            mock_user = Mock()
            mock_user.username = f"user{i}"
            mock_user.real_name = f"用户{i}"

            mock_contribution = Mock()
            mock_contribution.user_id = i
            mock_contribution.user = mock_user
            mock_contribution.task_count = i
            mock_contribution.actual_hours = float(i * 10)
            mock_contribution.deliverable_count = 0
            mock_contribution.issue_resolved = 0
            mock_contribution.bonus_amount = Decimal("0")
            mock_contribution.contribution_score = Decimal(str(i))
            mock_contribution.pm_rating = None

            contributions.append(mock_contribution)

        mock_get_contributions.return_value = contributions

        service = ProjectContributionService(mock_db)
        result = service.generate_contribution_report(project_id=1)

        assert len(result['contributions']) == 15
        assert len(result['top_contributors']) == 10

    @patch.object(ProjectContributionService, 'get_project_contributions')
    def test_generate_report_handles_none_values(self, mock_get_contributions):
        """测试处理None值"""
        mock_db = MagicMock(spec=Session)

        mock_contribution = Mock()
        mock_contribution.user_id = 1
        mock_contribution.user = None
        mock_contribution.task_count = 0
        mock_contribution.actual_hours = None
        mock_contribution.deliverable_count = 0
        mock_contribution.issue_resolved = 0
        mock_contribution.bonus_amount = None
        mock_contribution.contribution_score = None
        mock_contribution.pm_rating = None

        mock_get_contributions.return_value = [mock_contribution]

        service = ProjectContributionService(mock_db)
        result = service.generate_contribution_report(project_id=1)

        assert result['total_hours'] == 0.0
        assert result['total_bonus'] == 0.0
