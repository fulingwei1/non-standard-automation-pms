# -*- coding: utf-8 -*-
"""
ProjectContributionService 综合单元测试

测试覆盖:
- calculate_member_contribution: 计算成员贡献度
- _calculate_contribution_score: 计算贡献度评分
- get_project_contributions: 获取项目贡献度列表
- get_user_project_contributions: 获取用户项目贡献汇总
- rate_member_contribution: 项目经理评分
- generate_contribution_report: 生成贡献度报告
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestProjectContributionServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        assert service.db == mock_db


class TestCalculateMemberContribution:
    """测试 calculate_member_contribution 方法"""

    def test_creates_new_contribution_when_not_exists(self):
        """测试不存在时创建新贡献度记录"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        # Mock no existing contribution
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        with patch("app.services.project_contribution_service.ProjectBonusService") as MockBonusService:
            mock_bonus_service = MagicMock()
            mock_bonus_service.get_project_bonus_calculations.return_value = []
            MockBonusService.return_value = mock_bonus_service

            service = ProjectContributionService(mock_db)

            with patch.object(service, "_calculate_contribution_score", return_value=Decimal("0")):
                result = service.calculate_member_contribution(
                    project_id=1,
                    user_id=1,
                    period="2026-01",
                )

        mock_db.add.assert_called_once()

    def test_updates_existing_contribution(self):
        """测试更新已存在的贡献度记录"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        mock_contribution = MagicMock()
        mock_contribution.task_count = 0
        mock_contribution.task_hours = 0
        mock_contribution.actual_hours = 0
        mock_contribution.deliverable_count = 0
        mock_contribution.issue_count = 0
        mock_contribution.issue_resolved = 0
        mock_contribution.bonus_amount = Decimal("0")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contribution
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        with patch("app.services.project_contribution_service.ProjectBonusService") as MockBonusService:
            mock_bonus_service = MagicMock()
            mock_bonus_service.get_project_bonus_calculations.return_value = []
            MockBonusService.return_value = mock_bonus_service

            service = ProjectContributionService(mock_db)

            with patch.object(service, "_calculate_contribution_score", return_value=Decimal("5.0")):
                result = service.calculate_member_contribution(
                    project_id=1,
                    user_id=1,
                    period="2026-01",
                )

        # 不应该再次添加
        mock_db.add.assert_not_called()

    def test_counts_completed_tasks(self):
        """测试统计已完成任务"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        mock_contribution = MagicMock()
        mock_contribution.task_count = 0

        # Mock tasks
        mock_task1 = MagicMock()
        mock_task1.status = "COMPLETED"
        mock_task1.estimated_hours = 10
        mock_task1.actual_hours = 12

        mock_task2 = MagicMock()
        mock_task2.status = "IN_PROGRESS"
        mock_task2.estimated_hours = 8
        mock_task2.actual_hours = 5

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contribution
        mock_db.query.return_value.filter.return_value.filter.return_value.all.side_effect = [
            [mock_task1, mock_task2],  # tasks
            [],  # documents
            [],  # issues
        ]

        with patch("app.services.project_contribution_service.ProjectBonusService") as MockBonusService:
            mock_bonus_service = MagicMock()
            mock_bonus_service.get_project_bonus_calculations.return_value = []
            MockBonusService.return_value = mock_bonus_service

            service = ProjectContributionService(mock_db)

            with patch.object(service, "_calculate_contribution_score", return_value=Decimal("0")):
                result = service.calculate_member_contribution(
                    project_id=1,
                    user_id=1,
                    period="2026-01",
                )

        assert mock_contribution.task_count == 1  # 只有一个COMPLETED

    def test_calculates_bonus_from_service(self):
        """测试从服务获取奖金数据"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        mock_contribution = MagicMock()

        mock_bonus_calc = MagicMock()
        mock_bonus_calc.calculated_amount = Decimal("5000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contribution
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        with patch("app.services.project_contribution_service.ProjectBonusService") as MockBonusService:
            mock_bonus_service = MagicMock()
            mock_bonus_service.get_project_bonus_calculations.return_value = [mock_bonus_calc]
            MockBonusService.return_value = mock_bonus_service

            service = ProjectContributionService(mock_db)

            with patch.object(service, "_calculate_contribution_score", return_value=Decimal("0")):
                result = service.calculate_member_contribution(
                    project_id=1,
                    user_id=1,
                    period="2026-01",
                )

        assert mock_contribution.bonus_amount == Decimal("5000")


class TestCalculateContributionScore:
    """测试 _calculate_contribution_score 方法"""

    def test_returns_zero_for_empty_contribution(self):
        """测试空贡献度返回零分"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        mock_contribution = MagicMock()
        mock_contribution.task_count = 0
        mock_contribution.actual_hours = 0
        mock_contribution.deliverable_count = 0
        mock_contribution.issue_resolved = 0
        mock_contribution.bonus_amount = Decimal("0")

        result = service._calculate_contribution_score(mock_contribution)

        assert result == Decimal("0")

    def test_calculates_task_weight(self):
        """测试任务权重计算"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        mock_contribution = MagicMock()
        mock_contribution.task_count = 10
        mock_contribution.actual_hours = 0
        mock_contribution.deliverable_count = 0
        mock_contribution.issue_resolved = 0
        mock_contribution.bonus_amount = Decimal("0")

        result = service._calculate_contribution_score(mock_contribution)

        # 任务权重30%: 10 * 0.3 = 3
        assert result == Decimal("3")

    def test_calculates_hours_weight(self):
        """测试工时权重计算"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        mock_contribution = MagicMock()
        mock_contribution.task_count = 0
        mock_contribution.actual_hours = 100
        mock_contribution.deliverable_count = 0
        mock_contribution.issue_resolved = 0
        mock_contribution.bonus_amount = Decimal("0")

        result = service._calculate_contribution_score(mock_contribution)

        # 工时权重20%归一化: 100 * 0.2 / 10 = 2
        assert result == Decimal("2")

    def test_calculates_deliverable_weight(self):
        """测试交付物权重计算"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        mock_contribution = MagicMock()
        mock_contribution.task_count = 0
        mock_contribution.actual_hours = 0
        mock_contribution.deliverable_count = 5
        mock_contribution.issue_resolved = 0
        mock_contribution.bonus_amount = Decimal("0")

        result = service._calculate_contribution_score(mock_contribution)

        # 交付物权重20%: 5 * 0.2 = 1
        assert result == Decimal("1")

    def test_calculates_issue_weight(self):
        """测试问题解决权重计算"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        mock_contribution = MagicMock()
        mock_contribution.task_count = 0
        mock_contribution.actual_hours = 0
        mock_contribution.deliverable_count = 0
        mock_contribution.issue_resolved = 10
        mock_contribution.bonus_amount = Decimal("0")

        result = service._calculate_contribution_score(mock_contribution)

        # 问题解决权重20%: 10 * 0.2 = 2
        assert result == Decimal("2")

    def test_calculates_bonus_weight(self):
        """测试奖金权重计算"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        mock_contribution = MagicMock()
        mock_contribution.task_count = 0
        mock_contribution.actual_hours = 0
        mock_contribution.deliverable_count = 0
        mock_contribution.issue_resolved = 0
        mock_contribution.bonus_amount = Decimal("50000")

        result = service._calculate_contribution_score(mock_contribution)

        # 奖金权重10%归一化: (50000/100000) * 10 * 0.1 = 0.5
        assert result == Decimal("0.5")


class TestGetProjectContributions:
    """测试 get_project_contributions 方法"""

    def test_returns_all_contributions_for_project(self):
        """测试返回项目所有贡献度"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        mock_contrib1 = MagicMock()
        mock_contrib1.contribution_score = Decimal("10")

        mock_contrib2 = MagicMock()
        mock_contrib2.contribution_score = Decimal("5")

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_contrib1,
            mock_contrib2,
        ]

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        result = service.get_project_contributions(project_id=1)

        assert len(result) == 2

    def test_filters_by_period(self):
        """测试按周期筛选"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        mock_contrib = MagicMock()

        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_contrib
        ]

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        result = service.get_project_contributions(project_id=1, period="2026-01")

        assert len(result) == 1


class TestGetUserProjectContributions:
    """测试 get_user_project_contributions 方法"""

    def test_returns_user_contributions(self):
        """测试返回用户贡献度"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        mock_contrib = MagicMock()

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_contrib
        ]

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        result = service.get_user_project_contributions(user_id=1)

        assert len(result) == 1

    def test_filters_by_period_range(self):
        """测试按周期范围筛选"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        result = service.get_user_project_contributions(
            user_id=1,
            start_period="2025-01",
            end_period="2026-01",
        )

        assert result == []


class TestRateMemberContribution:
    """测试 rate_member_contribution 方法"""

    def test_raises_error_for_invalid_rating(self):
        """测试无效评分抛出异常"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        with pytest.raises(ValueError) as exc_info:
            service.rate_member_contribution(
                project_id=1,
                user_id=1,
                period="2026-01",
                pm_rating=0,  # Invalid
                rater_id=2,
            )

        assert "评分必须在1-5之间" in str(exc_info.value)

    def test_raises_error_for_rating_above_5(self):
        """测试评分超过5抛出异常"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        with pytest.raises(ValueError):
            service.rate_member_contribution(
                project_id=1,
                user_id=1,
                period="2026-01",
                pm_rating=6,  # Invalid
                rater_id=2,
            )

    def test_updates_existing_contribution_rating(self):
        """测试更新已存在贡献度的评分"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        mock_contribution = MagicMock()
        mock_contribution.contribution_score = Decimal("10")
        mock_contribution.pm_rating = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contribution

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        result = service.rate_member_contribution(
            project_id=1,
            user_id=1,
            period="2026-01",
            pm_rating=4,
            rater_id=2,
        )

        assert mock_contribution.pm_rating == 4

    def test_calculates_weighted_score_with_pm_rating(self):
        """测试计算包含PM评分的加权分数"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        mock_contribution = MagicMock()
        mock_contribution.contribution_score = Decimal("10")
        mock_contribution.pm_rating = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contribution

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        result = service.rate_member_contribution(
            project_id=1,
            user_id=1,
            period="2026-01",
            pm_rating=5,  # Max rating
            rater_id=2,
        )

        # base_score * 0.7 + pm_score * 0.3
        # 10 * 0.7 + 10 * 0.3 = 7 + 3 = 10
        expected_score = (Decimal("10") * Decimal("0.7")) + (Decimal("10") * Decimal("0.3"))
        assert mock_contribution.contribution_score == expected_score

    def test_creates_contribution_if_not_exists(self):
        """测试不存在时先创建贡献度"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        # First query returns None (no existing contribution)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        with patch("app.services.project_contribution_service.ProjectBonusService") as MockBonusService:
            mock_bonus_service = MagicMock()
            mock_bonus_service.get_project_bonus_calculations.return_value = []
            MockBonusService.return_value = mock_bonus_service

            service = ProjectContributionService(mock_db)

            # Mock calculate_member_contribution to return a contribution
            mock_new_contribution = MagicMock()
            mock_new_contribution.contribution_score = Decimal("5")

            with patch.object(
                service,
                "calculate_member_contribution",
                return_value=mock_new_contribution,
            ):
                result = service.rate_member_contribution(
                    project_id=1,
                    user_id=1,
                    period="2026-01",
                    pm_rating=3,
                    rater_id=2,
                )


class TestGenerateContributionReport:
    """测试 generate_contribution_report 方法"""

    def test_generates_report_with_contributions(self):
        """测试生成贡献度报告"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        mock_user = MagicMock()
        mock_user.real_name = "测试用户"
        mock_user.username = "testuser"

        mock_contrib = MagicMock()
        mock_contrib.user_id = 1
        mock_contrib.user = mock_user
        mock_contrib.task_count = 5
        mock_contrib.actual_hours = 40
        mock_contrib.deliverable_count = 2
        mock_contrib.issue_resolved = 3
        mock_contrib.bonus_amount = Decimal("1000")
        mock_contrib.contribution_score = Decimal("10")
        mock_contrib.pm_rating = 4

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        with patch.object(
            service, "get_project_contributions", return_value=[mock_contrib]
        ):
            result = service.generate_contribution_report(project_id=1)

        assert result["project_id"] == 1
        assert result["total_members"] == 1
        assert result["total_task_count"] == 5
        assert result["total_hours"] == 40.0
        assert result["total_bonus"] == 1000.0
        assert len(result["contributions"]) == 1
        assert len(result["top_contributors"]) == 1

    def test_generates_empty_report_when_no_contributions(self):
        """测试无贡献度时生成空报告"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        with patch.object(service, "get_project_contributions", return_value=[]):
            result = service.generate_contribution_report(project_id=1)

        assert result["total_members"] == 0
        assert result["total_task_count"] == 0
        assert result["contributions"] == []

    def test_sorts_top_contributors_by_score(self):
        """测试按评分排序前10贡献者"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        # Create 15 mock contributions
        contributions = []
        for i in range(15):
            mock_user = MagicMock()
            mock_user.real_name = f"用户{i}"
            mock_user.username = f"user{i}"

            mock_contrib = MagicMock()
            mock_contrib.user_id = i
            mock_contrib.user = mock_user
            mock_contrib.task_count = i
            mock_contrib.actual_hours = i * 10
            mock_contrib.deliverable_count = 0
            mock_contrib.issue_resolved = 0
            mock_contrib.bonus_amount = Decimal("0")
            mock_contrib.contribution_score = Decimal(str(i))
            mock_contrib.pm_rating = None
            contributions.append(mock_contrib)

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        with patch.object(
            service, "get_project_contributions", return_value=contributions
        ):
            result = service.generate_contribution_report(project_id=1)

        # 应该只有前10名
        assert len(result["top_contributors"]) == 10
        # 应该按评分降序排列
        assert result["top_contributors"][0]["contribution_score"] == 14.0

    def test_handles_user_without_real_name(self):
        """测试处理无真实姓名的用户"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        mock_user = MagicMock()
        mock_user.real_name = None
        mock_user.username = "testuser"
        mock_user.employee = None

        mock_contrib = MagicMock()
        mock_contrib.user_id = 1
        mock_contrib.user = mock_user
        mock_contrib.task_count = 0
        mock_contrib.actual_hours = 0
        mock_contrib.deliverable_count = 0
        mock_contrib.issue_resolved = 0
        mock_contrib.bonus_amount = Decimal("0")
        mock_contrib.contribution_score = Decimal("0")
        mock_contrib.pm_rating = None

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        with patch.object(
            service, "get_project_contributions", return_value=[mock_contrib]
        ):
            result = service.generate_contribution_report(project_id=1)

        # 应该使用username作为备选
        assert result["contributions"][0]["user_name"] == "testuser"

    def test_filters_by_period(self):
        """测试按周期筛选报告"""
        from app.services.project_contribution_service import ProjectContributionService

        mock_db = MagicMock()

        with patch("app.services.project_contribution_service.ProjectBonusService"):
            service = ProjectContributionService(mock_db)

        with patch.object(
            service, "get_project_contributions", return_value=[]
        ) as mock_get:
            result = service.generate_contribution_report(
                project_id=1, period="2026-01"
            )

        mock_get.assert_called_once_with(1, "2026-01")
        assert result["period"] == "2026-01"
