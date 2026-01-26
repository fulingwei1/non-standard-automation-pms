# -*- coding: utf-8 -*-
"""
ProjectBonusService 单元测试
测试项目奖金查询服务的各项功能
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.bonus import BonusCalculation, BonusDistribution, BonusRule
from app.models.project import Project
from app.models.user import User
from app.services.project_bonus_service import ProjectBonusService


class TestProjectBonusServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        mock_db = MagicMock(spec=Session)
        service = ProjectBonusService(mock_db)
        assert service.db == mock_db


class TestGetProjectBonusRules:
    """测试获取项目奖金规则"""

    def test_get_rules_project_not_found(self):
        """测试项目不存在时返回空列表"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_rules(project_id=999)

        assert result == []

    def test_get_rules_with_active_filter(self):
        """测试获取激活的奖金规则"""
        mock_db = MagicMock(spec=Session)

        mock_project = Mock(spec=Project)
        mock_project.id = 1
        mock_project.project_type = "STANDARD"

        mock_rule = Mock(spec=BonusRule)
        mock_rule.bonus_type = "PROJECT_BASED"
        mock_rule.is_active = True
        # 设置日期限制为None，表示无日期限制
        mock_rule.effective_start_date = None
        mock_rule.effective_end_date = None
        mock_rule.apply_to_projects = None

        # 第一次查询返回项目
        mock_query1 = MagicMock()
        mock_query1.filter.return_value.first.return_value = mock_project

        # 第二次查询返回规则
        mock_query2 = MagicMock()
        mock_query2.filter.return_value.filter.return_value.all.return_value = [mock_rule]

        mock_db.query.side_effect = [mock_query1, mock_query2]

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_rules(project_id=1, is_active=True)

        # 验证规则被过滤检查
        assert isinstance(result, list)

    def test_get_rules_including_inactive(self):
        """测试获取包括未激活的规则"""
        mock_db = MagicMock(spec=Session)

        mock_project = Mock(spec=Project)
        mock_project.id = 1

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_rules(project_id=1, is_active=False)

        assert isinstance(result, list)


class TestIsRuleApplicable:
    """测试规则适用性检查"""

    def test_rule_applicable_no_restrictions(self):
        """测试无限制条件的规则始终适用"""
        mock_db = MagicMock(spec=Session)
        service = ProjectBonusService(mock_db)

        mock_rule = Mock(spec=BonusRule)
        # 无 apply_to_projects 和日期限制 - 需要显式设置为None
        mock_rule.apply_to_projects = None
        mock_rule.effective_start_date = None
        mock_rule.effective_end_date = None

        mock_project = Mock(spec=Project)
        mock_project.project_type = "STANDARD"

        result = service._is_rule_applicable(mock_rule, mock_project)
        assert result is True

    def test_rule_not_applicable_project_type_mismatch(self):
        """测试项目类型不匹配时规则不适用"""
        mock_db = MagicMock(spec=Session)
        service = ProjectBonusService(mock_db)

        mock_rule = Mock(spec=BonusRule)
        mock_rule.apply_to_projects = ["TYPE_A", "TYPE_B"]
        mock_rule.effective_start_date = None
        mock_rule.effective_end_date = None

        mock_project = Mock(spec=Project)
        mock_project.project_type = "TYPE_C"

        result = service._is_rule_applicable(mock_rule, mock_project)
        assert result is False

    def test_rule_applicable_project_type_match(self):
        """测试项目类型匹配时规则适用"""
        mock_db = MagicMock(spec=Session)
        service = ProjectBonusService(mock_db)

        mock_rule = Mock(spec=BonusRule)
        mock_rule.apply_to_projects = ["TYPE_A", "TYPE_B"]
        mock_rule.effective_start_date = None
        mock_rule.effective_end_date = None

        mock_project = Mock(spec=Project)
        mock_project.project_type = "TYPE_A"

        result = service._is_rule_applicable(mock_rule, mock_project)
        assert result is True

    def test_rule_not_applicable_before_effective_date(self):
        """测试在生效日期之前规则不适用"""
        mock_db = MagicMock(spec=Session)
        service = ProjectBonusService(mock_db)

        mock_rule = Mock(spec=BonusRule)
        mock_rule.apply_to_projects = None
        mock_rule.effective_start_date = date(2099, 1, 1)  # 未来日期
        mock_rule.effective_end_date = None

        mock_project = Mock(spec=Project)

        result = service._is_rule_applicable(mock_rule, mock_project)
        assert result is False

    def test_rule_not_applicable_after_end_date(self):
        """测试在结束日期之后规则不适用"""
        mock_db = MagicMock(spec=Session)
        service = ProjectBonusService(mock_db)

        mock_rule = Mock(spec=BonusRule)
        mock_rule.apply_to_projects = None
        mock_rule.effective_start_date = None
        mock_rule.effective_end_date = date(2000, 1, 1)  # 过去日期

        mock_project = Mock(spec=Project)

        result = service._is_rule_applicable(mock_rule, mock_project)
        assert result is False


class TestGetProjectBonusCalculations:
    """测试获取项目奖金计算记录"""

    def test_get_calculations_basic(self):
        """测试基本获取计算记录"""
        mock_db = MagicMock(spec=Session)

        mock_calc = Mock(spec=BonusCalculation)
        mock_calc.id = 1
        mock_calc.project_id = 1
        mock_calc.calculated_amount = Decimal("1000")

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_calc]

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_calculations(project_id=1)

        assert len(result) == 1
        assert result[0].calculated_amount == Decimal("1000")

    def test_get_calculations_with_user_filter(self):
        """测试按用户筛选计算记录"""
        mock_db = MagicMock(spec=Session)

        mock_calc = Mock(spec=BonusCalculation)
        mock_calc.user_id = 5

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = [mock_calc]
        mock_db.query.return_value = query_mock

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_calculations(project_id=1, user_id=5)

        assert len(result) == 1

    def test_get_calculations_with_status_filter(self):
        """测试按状态筛选计算记录"""
        mock_db = MagicMock(spec=Session)

        mock_calc = Mock(spec=BonusCalculation)
        mock_calc.status = "APPROVED"

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = [mock_calc]
        mock_db.query.return_value = query_mock

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_calculations(project_id=1, status="APPROVED")

        assert len(result) == 1

    def test_get_calculations_with_date_range(self):
        """测试按日期范围筛选计算记录"""
        mock_db = MagicMock(spec=Session)

        mock_calc = Mock(spec=BonusCalculation)
        mock_calc.calculated_at = datetime(2024, 6, 15)

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value.all.return_value = [mock_calc]
        mock_db.query.return_value = query_mock

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_calculations(
            project_id=1,
            start_date=date(2024, 6, 1),
            end_date=date(2024, 6, 30)
        )

        assert len(result) == 1


class TestGetProjectBonusDistributions:
    """测试获取项目奖金发放记录"""

    @patch("app.services.project_bonus_service.BonusDistribution")
    def test_get_distributions_basic(self, mock_distribution_class):
        """测试基本获取发放记录"""
        mock_db = MagicMock(spec=Session)

        mock_dist = Mock()
        mock_dist.id = 1
        mock_dist.distributed_amount = Decimal("500")

        # 设置类属性mock
        mock_distribution_class.distributed_at = MagicMock()
        mock_distribution_class.calculation_id = MagicMock()

        # 第一个查询 - calculation_ids 子查询
        mock_calc_query = MagicMock()
        mock_subquery = MagicMock()
        mock_calc_query.filter.return_value.subquery.return_value = mock_subquery

        # 第二个查询 - distribution 查询
        mock_dist_query = MagicMock()
        mock_dist_query.filter.return_value.order_by.return_value.all.return_value = [mock_dist]

        mock_db.query.side_effect = [mock_calc_query, mock_dist_query]

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_distributions(project_id=1)

        # 验证返回列表类型
        assert isinstance(result, list)

    @patch("app.services.project_bonus_service.BonusDistribution")
    def test_get_distributions_with_user_filter(self, mock_distribution_class):
        """测试按用户筛选发放记录"""
        mock_db = MagicMock(spec=Session)

        mock_dist = Mock()
        mock_dist.user_id = 5

        # 设置类属性mock
        mock_distribution_class.distributed_at = MagicMock()
        mock_distribution_class.calculation_id = MagicMock()
        mock_distribution_class.user_id = MagicMock()

        # 第一个查询 - calculation_ids 子查询
        mock_calc_query = MagicMock()
        mock_subquery = MagicMock()
        mock_calc_query.filter.return_value.subquery.return_value = mock_subquery

        # 第二个查询 - distribution 查询
        mock_dist_query = MagicMock()
        mock_dist_query.filter.return_value = mock_dist_query
        mock_dist_query.order_by.return_value.all.return_value = [mock_dist]

        mock_db.query.side_effect = [mock_calc_query, mock_dist_query]

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_distributions(project_id=1, user_id=5)

        assert isinstance(result, list)

    @patch("app.services.project_bonus_service.BonusDistribution")
    def test_get_distributions_with_status_filter(self, mock_distribution_class):
        """测试按状态筛选发放记录"""
        mock_db = MagicMock(spec=Session)

        mock_dist = Mock()
        mock_dist.status = "COMPLETED"

        # 设置类属性mock
        mock_distribution_class.distributed_at = MagicMock()
        mock_distribution_class.calculation_id = MagicMock()
        mock_distribution_class.status = MagicMock()

        # 第一个查询 - calculation_ids 子查询
        mock_calc_query = MagicMock()
        mock_subquery = MagicMock()
        mock_calc_query.filter.return_value.subquery.return_value = mock_subquery

        # 第二个查询 - distribution 查询
        mock_dist_query = MagicMock()
        mock_dist_query.filter.return_value = mock_dist_query
        mock_dist_query.order_by.return_value.all.return_value = [mock_dist]

        mock_db.query.side_effect = [mock_calc_query, mock_dist_query]

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_distributions(project_id=1, status="COMPLETED")

        assert isinstance(result, list)


class TestGetProjectMemberBonusSummary:
    """测试获取项目成员奖金汇总"""

    @patch.object(ProjectBonusService, 'get_project_bonus_calculations')
    @patch.object(ProjectBonusService, 'get_project_bonus_distributions')
    def test_get_member_summary_empty(self, mock_distributions, mock_calculations):
        """测试无奖金记录时返回空列表"""
        mock_db = MagicMock(spec=Session)
        mock_calculations.return_value = []
        mock_distributions.return_value = []

        service = ProjectBonusService(mock_db)
        result = service.get_project_member_bonus_summary(project_id=1)

        assert result == []

    @patch.object(ProjectBonusService, 'get_project_bonus_calculations')
    @patch.object(ProjectBonusService, 'get_project_bonus_distributions')
    def test_get_member_summary_with_calculations(self, mock_distributions, mock_calculations):
        """测试有计算记录时的汇总"""
        mock_db = MagicMock(spec=Session)

        mock_calc = Mock()
        mock_calc.user_id = 1
        mock_calc.calculated_amount = Decimal("1000")
        mock_calculations.return_value = [mock_calc]
        mock_distributions.return_value = []

        mock_user = Mock(spec=User)
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = ProjectBonusService(mock_db)
        result = service.get_project_member_bonus_summary(project_id=1)

        assert len(result) == 1
        assert result[0]['user_id'] == 1
        assert result[0]['total_calculated'] == Decimal("1000")

    @patch.object(ProjectBonusService, 'get_project_bonus_calculations')
    @patch.object(ProjectBonusService, 'get_project_bonus_distributions')
    def test_get_member_summary_with_distributions(self, mock_distributions, mock_calculations):
        """测试有发放记录时的汇总"""
        mock_db = MagicMock(spec=Session)

        mock_calc = Mock()
        mock_calc.user_id = 1
        mock_calc.calculated_amount = Decimal("1000")
        mock_calculations.return_value = [mock_calc]

        mock_dist = Mock()
        mock_dist.user_id = 1
        mock_dist.distributed_amount = Decimal("800")
        mock_distributions.return_value = [mock_dist]

        mock_user = Mock(spec=User)
        mock_user.real_name = "张三"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = ProjectBonusService(mock_db)
        result = service.get_project_member_bonus_summary(project_id=1)

        assert len(result) == 1
        assert result[0]['total_calculated'] == Decimal("1000")
        assert result[0]['total_distributed'] == Decimal("800")


class TestGetProjectBonusStatistics:
    """测试获取项目奖金统计"""

    @patch.object(ProjectBonusService, 'get_project_bonus_calculations')
    @patch.object(ProjectBonusService, 'get_project_bonus_distributions')
    def test_get_statistics_empty(self, mock_distributions, mock_calculations):
        """测试无奖金记录时的统计"""
        mock_db = MagicMock(spec=Session)
        mock_calculations.return_value = []
        mock_distributions.return_value = []

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_statistics(project_id=1)

        assert result['total_calculated'] == 0.0
        assert result['total_distributed'] == 0.0
        assert result['pending_amount'] == 0.0
        assert result['calculation_count'] == 0
        assert result['distribution_count'] == 0
        assert result['member_count'] == 0

    @patch.object(ProjectBonusService, 'get_project_bonus_calculations')
    @patch.object(ProjectBonusService, 'get_project_bonus_distributions')
    def test_get_statistics_with_data(self, mock_distributions, mock_calculations):
        """测试有奖金记录时的统计"""
        mock_db = MagicMock(spec=Session)

        mock_calc1 = Mock()
        mock_calc1.user_id = 1
        mock_calc1.calculated_amount = Decimal("1000")

        mock_calc2 = Mock()
        mock_calc2.user_id = 2
        mock_calc2.calculated_amount = Decimal("2000")

        mock_calculations.return_value = [mock_calc1, mock_calc2]

        mock_dist = Mock()
        mock_dist.user_id = 1
        mock_dist.distributed_amount = Decimal("800")
        mock_distributions.return_value = [mock_dist]

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_statistics(project_id=1)

        assert result['total_calculated'] == 3000.0
        assert result['total_distributed'] == 800.0
        assert result['pending_amount'] == 2200.0
        assert result['calculation_count'] == 2
        assert result['distribution_count'] == 1
        assert result['member_count'] == 2

    @patch.object(ProjectBonusService, 'get_project_bonus_calculations')
    @patch.object(ProjectBonusService, 'get_project_bonus_distributions')
    def test_get_statistics_with_none_amounts(self, mock_distributions, mock_calculations):
        """测试金额为None时的处理"""
        mock_db = MagicMock(spec=Session)

        mock_calc = Mock()
        mock_calc.user_id = 1
        mock_calc.calculated_amount = None
        mock_calculations.return_value = [mock_calc]

        mock_dist = Mock()
        mock_dist.user_id = 1
        mock_dist.distributed_amount = None
        mock_distributions.return_value = [mock_dist]

        service = ProjectBonusService(mock_db)
        result = service.get_project_bonus_statistics(project_id=1)

        assert result['total_calculated'] == 0.0
        assert result['total_distributed'] == 0.0
