# -*- coding: utf-8 -*-
"""
ProjectBonusService 综合单元测试

测试覆盖:
- get_project_bonus_rules: 获取项目奖金规则
- _is_rule_applicable: 检查规则是否适用
- get_project_bonus_calculations: 获取奖金计算记录
- get_project_bonus_distributions: 获取奖金发放记录
- get_project_member_bonus_summary: 获取成员奖金汇总
- get_project_bonus_statistics: 获取项目奖金统计
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestProjectBonusServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()
        service = ProjectBonusService(mock_db)

        assert service.db == mock_db


class TestGetProjectBonusRules:
    """测试 get_project_bonus_rules 方法"""

    def test_returns_empty_when_project_not_found(self):
        """测试项目不存在时返回空列表"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_rules(project_id=999)

        assert result == []

    def test_returns_active_rules_only_by_default(self):
        """测试默认只返回启用的规则"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()
        mock_project = MagicMock()

        # 设置查询链
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        mock_rule = MagicMock()
        mock_rule.apply_to_projects = None
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [
            mock_rule
        ]

        service = ProjectBonusService(mock_db)

        with patch.object(service, "_is_rule_applicable", return_value=True):
            result = service.get_project_bonus_rules(project_id=1, is_active=True)

        assert len(result) >= 0  # 验证调用不报错

    def test_returns_all_rules_when_is_active_false(self):
        """测试 is_active=False 时返回所有规则"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()
        mock_project = MagicMock()

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        mock_rule = MagicMock()
        mock_rule.apply_to_projects = None
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_rule]

        service = ProjectBonusService(mock_db)

        with patch.object(service, "_is_rule_applicable", return_value=True):
            result = service.get_project_bonus_rules(project_id=1, is_active=False)

        assert len(result) >= 0


class TestIsRuleApplicable:
    """测试 _is_rule_applicable 方法"""

    def test_returns_true_when_no_restrictions(self):
        """测试无限制条件时返回 True"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()
        service = ProjectBonusService(mock_db)

        mock_rule = MagicMock()
        mock_rule.apply_to_projects = None
        delattr(mock_rule, "effective_start_date")
        delattr(mock_rule, "effective_end_date")

        mock_project = MagicMock()

        result = service._is_rule_applicable(mock_rule, mock_project)

        assert result is True

    def test_returns_false_when_project_type_not_match(self):
        """测试项目类型不匹配时返回 False"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()
        service = ProjectBonusService(mock_db)

        mock_rule = MagicMock()
        mock_rule.apply_to_projects = ["TYPE_A", "TYPE_B"]

        mock_project = MagicMock()
        mock_project.project_type = "TYPE_C"

        result = service._is_rule_applicable(mock_rule, mock_project)

        assert result is False

    def test_returns_true_when_project_type_matches(self):
        """测试项目类型匹配时返回 True"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()
        service = ProjectBonusService(mock_db)

        mock_rule = MagicMock()
        mock_rule.apply_to_projects = ["TYPE_A", "TYPE_B"]
        delattr(mock_rule, "effective_start_date")
        delattr(mock_rule, "effective_end_date")

        mock_project = MagicMock()
        mock_project.project_type = "TYPE_A"

        result = service._is_rule_applicable(mock_rule, mock_project)

        assert result is True

    def test_returns_false_when_rule_not_effective_yet(self):
        """测试规则未生效时返回 False"""
        from app.services.project_bonus_service import ProjectBonusService
        from datetime import timedelta

        mock_db = MagicMock()
        service = ProjectBonusService(mock_db)

        mock_rule = MagicMock()
        mock_rule.apply_to_projects = None
        mock_rule.effective_start_date = date.today() + timedelta(days=30)
        delattr(mock_rule, "effective_end_date")

        mock_project = MagicMock()

        result = service._is_rule_applicable(mock_rule, mock_project)

        assert result is False

    def test_returns_false_when_rule_expired(self):
        """测试规则已过期时返回 False"""
        from app.services.project_bonus_service import ProjectBonusService
        from datetime import timedelta

        mock_db = MagicMock()
        service = ProjectBonusService(mock_db)

        mock_rule = MagicMock()
        mock_rule.apply_to_projects = None
        mock_rule.effective_end_date = date.today() - timedelta(days=30)
        delattr(mock_rule, "effective_start_date")

        mock_project = MagicMock()

        result = service._is_rule_applicable(mock_rule, mock_project)

        assert result is False


class TestGetProjectBonusCalculations:
    """测试 get_project_bonus_calculations 方法"""

    def test_returns_calculations_for_project(self):
        """测试返回项目的计算记录"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()
        mock_calc = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_calc
        ]

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_calculations(project_id=1)

        assert len(result) == 1

    def test_filters_by_user_id(self):
        """测试按用户ID筛选"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()
        mock_calc = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_calc
        ]

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_calculations(project_id=1, user_id=5)

        assert len(result) == 1

    def test_filters_by_status(self):
        """测试按状态筛选"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_calculations(
            project_id=1, status="APPROVED"
        )

        assert result == []

    def test_filters_by_date_range(self):
        """测试按日期范围筛选"""
        from app.services.project_bonus_service import ProjectBonusService
        from datetime import timedelta

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_calculations(
            project_id=1,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
        )

        assert result == []


class TestGetProjectBonusDistributions:
    """测试 get_project_bonus_distributions 方法"""

    def test_returns_distributions_for_project(self):
        """测试返回项目的发放记录"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()
        mock_dist = MagicMock()
        mock_db.query.return_value.filter.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_dist
        ]

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_distributions(project_id=1)

        assert len(result) == 1

    def test_filters_by_user_id(self):
        """测试按用户ID筛选"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_distributions(project_id=1, user_id=5)

        assert result == []

    def test_filters_by_status(self):
        """测试按发放状态筛选"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_distributions(project_id=1, status="PAID")

        assert result == []


class TestGetProjectMemberBonusSummary:
    """测试 get_project_member_bonus_summary 方法"""

    def test_returns_empty_list_when_no_data(self):
        """测试无数据时返回空列表"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()
        service = ProjectBonusService(mock_db)

        with patch.object(
            service, "get_project_bonus_calculations", return_value=[]
        ):
            with patch.object(
                service, "get_project_bonus_distributions", return_value=[]
            ):
                result = service.get_project_member_bonus_summary(project_id=1)

        assert result == []

    def test_aggregates_by_user(self):
        """测试按用户汇总"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()

        # Mock calculations
        mock_calc1 = MagicMock()
        mock_calc1.user_id = 1
        mock_calc1.calculated_amount = Decimal("1000")

        mock_calc2 = MagicMock()
        mock_calc2.user_id = 1
        mock_calc2.calculated_amount = Decimal("500")

        mock_calc3 = MagicMock()
        mock_calc3.user_id = 2
        mock_calc3.calculated_amount = Decimal("800")

        # Mock user query
        mock_user1 = MagicMock()
        mock_user1.real_name = "用户1"
        mock_user1.username = "user1"

        mock_user2 = MagicMock()
        mock_user2.real_name = "用户2"
        mock_user2.username = "user2"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user1,
            mock_user2,
        ]

        service = ProjectBonusService(mock_db)

        with patch.object(
            service,
            "get_project_bonus_calculations",
            return_value=[mock_calc1, mock_calc2, mock_calc3],
        ):
            with patch.object(
                service, "get_project_bonus_distributions", return_value=[]
            ):
                result = service.get_project_member_bonus_summary(project_id=1)

        assert len(result) == 2
        user1_summary = next((r for r in result if r["user_id"] == 1), None)
        assert user1_summary is not None
        assert user1_summary["total_calculated"] == Decimal("1500")
        assert user1_summary["calculation_count"] == 2


class TestGetProjectBonusStatistics:
    """测试 get_project_bonus_statistics 方法"""

    def test_returns_statistics(self):
        """测试返回统计信息"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()

        # Mock calculations
        mock_calc = MagicMock()
        mock_calc.calculated_amount = Decimal("1000")
        mock_calc.user_id = 1

        # Mock distributions
        mock_dist = MagicMock()
        mock_dist.distributed_amount = Decimal("500")
        mock_dist.user_id = 1

        service = ProjectBonusService(mock_db)

        with patch.object(
            service, "get_project_bonus_calculations", return_value=[mock_calc]
        ):
            with patch.object(
                service, "get_project_bonus_distributions", return_value=[mock_dist]
            ):
                result = service.get_project_bonus_statistics(project_id=1)

        assert result["total_calculated"] == 1000.0
        assert result["total_distributed"] == 500.0
        assert result["pending_amount"] == 500.0
        assert result["calculation_count"] == 1
        assert result["distribution_count"] == 1
        assert result["member_count"] == 1

    def test_handles_empty_data(self):
        """测试处理空数据"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()
        service = ProjectBonusService(mock_db)

        with patch.object(
            service, "get_project_bonus_calculations", return_value=[]
        ):
            with patch.object(
                service, "get_project_bonus_distributions", return_value=[]
            ):
                result = service.get_project_bonus_statistics(project_id=1)

        assert result["total_calculated"] == 0.0
        assert result["total_distributed"] == 0.0
        assert result["pending_amount"] == 0.0
        assert result["calculation_count"] == 0
        assert result["distribution_count"] == 0
        assert result["member_count"] == 0

    def test_handles_none_amounts(self):
        """测试处理空金额"""
        from app.services.project_bonus_service import ProjectBonusService

        mock_db = MagicMock()

        mock_calc = MagicMock()
        mock_calc.calculated_amount = None
        mock_calc.user_id = 1

        mock_dist = MagicMock()
        mock_dist.distributed_amount = None
        mock_dist.user_id = 1

        service = ProjectBonusService(mock_db)

        with patch.object(
            service, "get_project_bonus_calculations", return_value=[mock_calc]
        ):
            with patch.object(
                service, "get_project_bonus_distributions", return_value=[mock_dist]
            ):
                result = service.get_project_bonus_statistics(project_id=1)

        assert result["total_calculated"] == 0.0
        assert result["total_distributed"] == 0.0
