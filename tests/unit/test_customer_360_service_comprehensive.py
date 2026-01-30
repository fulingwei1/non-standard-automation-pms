# -*- coding: utf-8 -*-
"""
Customer360Service 综合单元测试

测试覆盖:
- _decimal: 安全Decimal转换
- build_overview: 构建客户360度视图
- _build_summary: 构建汇总统计
"""

from datetime import datetime, date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestDecimalConversion:
    """测试 _decimal 函数"""

    def test_converts_none_to_zero(self):
        """测试None转换为0"""
        from app.services.customer_360_service import _decimal

        result = _decimal(None)

        assert result == Decimal("0")

    def test_returns_decimal_unchanged(self):
        """测试Decimal值不变"""
        from app.services.customer_360_service import _decimal

        value = Decimal("123.45")
        result = _decimal(value)

        assert result == Decimal("123.45")

    def test_converts_int_to_decimal(self):
        """测试int转换为Decimal"""
        from app.services.customer_360_service import _decimal

        result = _decimal(100)

        assert result == Decimal("100")

    def test_converts_float_to_decimal(self):
        """测试float转换为Decimal"""
        from app.services.customer_360_service import _decimal

        result = _decimal(99.99)

        assert result == Decimal("99.99")

    def test_converts_string_to_decimal(self):
        """测试字符串转换为Decimal"""
        from app.services.customer_360_service import _decimal

        result = _decimal("50.25")

        assert result == Decimal("50.25")

    def test_handles_invalid_value(self):
        """测试无效值返回0"""
        from app.services.customer_360_service import _decimal

        result = _decimal("invalid")

        assert result == Decimal("0")


class TestBuildOverview:
    """测试 build_overview 方法"""

    def test_raises_error_when_customer_not_found(self):
        """测试客户不存在时抛出错误"""
        from app.services.customer_360_service import Customer360Service

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = Customer360Service(mock_db)

        with pytest.raises(ValueError, match="客户不存在"):
            service.build_overview(999)

    def test_returns_overview_with_all_sections(self):
        """测试返回包含所有部分的视图"""
        from app.services.customer_360_service import Customer360Service

        mock_db = MagicMock()

        mock_customer = MagicMock()
        mock_customer.id = 1
        mock_customer.customer_name = "测试客户"

        # Setup query chain
        def query_side_effect(model):
            result = MagicMock()
            if model.__name__ == "Customer":
                result.filter.return_value.first.return_value = mock_customer
            else:
                result.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
                result.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
            return result

        mock_db.query = MagicMock(side_effect=query_side_effect)

        service = Customer360Service(mock_db)

        with patch.object(service, '_build_summary', return_value={}):
            result = service.build_overview(1)

        assert "basic_info" in result
        assert "summary" in result
        assert "projects" in result
        assert "opportunities" in result
        assert "quotes" in result
        assert "contracts" in result
        assert "invoices" in result
        assert "payment_plans" in result
        assert "communications" in result

    def test_queries_projects_limited_to_8(self):
        """测试项目查询限制为8条"""
        from app.services.customer_360_service import Customer360Service

        mock_db = MagicMock()
        mock_customer = MagicMock()
        mock_customer.id = 1
        mock_customer.customer_name = "测试客户"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_customer
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        service = Customer360Service(mock_db)

        with patch.object(service, '_build_summary', return_value={}):
            service.build_overview(1)

        # 验证limit(8)被调用
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.assert_called()


class TestBuildSummary:
    """测试 _build_summary 方法"""

    def test_calculates_total_contract_amount(self):
        """测试计算合同总金额"""
        from app.services.customer_360_service import Customer360Service

        mock_db = MagicMock()
        service = Customer360Service(mock_db)

        mock_customer = MagicMock()
        mock_contract1 = MagicMock()
        mock_contract1.contract_amount = Decimal("100000")
        mock_contract2 = MagicMock()
        mock_contract2.contract_amount = Decimal("50000")

        result = service._build_summary(
            mock_customer,
            projects=[],
            opportunities=[],
            quotes=[],
            contracts=[mock_contract1, mock_contract2],
            payment_plans=[],
            communications=[]
        )

        assert result['total_contract_amount'] == Decimal("150000")

    def test_calculates_open_receivables(self):
        """测试计算未收款金额"""
        from app.services.customer_360_service import Customer360Service

        mock_db = MagicMock()
        service = Customer360Service(mock_db)

        mock_customer = MagicMock()

        mock_plan1 = MagicMock()
        mock_plan1.status = "PENDING"
        mock_plan1.planned_amount = Decimal("10000")
        mock_plan1.actual_amount = Decimal("0")

        mock_plan2 = MagicMock()
        mock_plan2.status = "INVOICED"
        mock_plan2.planned_amount = Decimal("20000")
        mock_plan2.actual_amount = Decimal("5000")

        result = service._build_summary(
            mock_customer,
            projects=[],
            opportunities=[],
            quotes=[],
            contracts=[],
            payment_plans=[mock_plan1, mock_plan2],
            communications=[]
        )

        # 10000 + (20000 - 5000) = 25000
        assert result['open_receivables'] == Decimal("25000")

    def test_calculates_win_rate(self):
        """测试计算赢单率"""
        from app.services.customer_360_service import Customer360Service

        mock_db = MagicMock()
        service = Customer360Service(mock_db)

        mock_customer = MagicMock()

        mock_opp1 = MagicMock()
        mock_opp1.stage = "WON"
        mock_opp1.est_amount = Decimal("50000")

        mock_opp2 = MagicMock()
        mock_opp2.stage = "LOST"
        mock_opp2.est_amount = Decimal("30000")

        mock_opp3 = MagicMock()
        mock_opp3.stage = "QUALIFIED"
        mock_opp3.est_amount = Decimal("40000")

        mock_opp4 = MagicMock()
        mock_opp4.stage = "WON"
        mock_opp4.est_amount = Decimal("20000")

        result = service._build_summary(
            mock_customer,
            projects=[],
            opportunities=[mock_opp1, mock_opp2, mock_opp3, mock_opp4],
            quotes=[],
            contracts=[],
            payment_plans=[],
            communications=[]
        )

        # 2 won out of 4 = 50%
        assert result['win_rate'] == 50.0

    def test_calculates_pipeline_amount(self):
        """测试计算商机管道金额"""
        from app.services.customer_360_service import Customer360Service

        mock_db = MagicMock()
        service = Customer360Service(mock_db)

        mock_customer = MagicMock()

        mock_opp1 = MagicMock()
        mock_opp1.stage = "QUALIFIED"
        mock_opp1.est_amount = Decimal("100000")

        mock_opp2 = MagicMock()
        mock_opp2.stage = "WON"  # 不计入管道
        mock_opp2.est_amount = Decimal("50000")

        mock_opp3 = MagicMock()
        mock_opp3.stage = "PROPOSAL"
        mock_opp3.est_amount = Decimal("80000")

        result = service._build_summary(
            mock_customer,
            projects=[],
            opportunities=[mock_opp1, mock_opp2, mock_opp3],
            quotes=[],
            contracts=[],
            payment_plans=[],
            communications=[]
        )

        assert result['pipeline_amount'] == Decimal("180000")

    def test_calculates_active_projects(self):
        """测试计算活跃项目数"""
        from app.services.customer_360_service import Customer360Service

        mock_db = MagicMock()
        service = Customer360Service(mock_db)

        mock_customer = MagicMock()

        mock_proj1 = MagicMock()
        mock_proj1.status = "IN_PROGRESS"
        mock_proj1.updated_at = datetime.now()

        mock_proj2 = MagicMock()
        mock_proj2.status = "CLOSED"
        mock_proj2.updated_at = datetime.now()

        mock_proj3 = MagicMock()
        mock_proj3.status = "ACTIVE"
        mock_proj3.updated_at = datetime.now()

        result = service._build_summary(
            mock_customer,
            projects=[mock_proj1, mock_proj2, mock_proj3],
            opportunities=[],
            quotes=[],
            contracts=[],
            payment_plans=[],
            communications=[]
        )

        assert result['total_projects'] == 3
        assert result['active_projects'] == 2

    def test_calculates_average_margin(self):
        """测试计算平均毛利率"""
        from app.services.customer_360_service import Customer360Service

        mock_db = MagicMock()
        service = Customer360Service(mock_db)

        mock_customer = MagicMock()

        mock_quote1 = MagicMock()
        mock_version1 = MagicMock()
        mock_version1.gross_margin = Decimal("30")
        mock_quote1.current_version = mock_version1

        mock_quote2 = MagicMock()
        mock_version2 = MagicMock()
        mock_version2.gross_margin = Decimal("40")
        mock_quote2.current_version = mock_version2

        result = service._build_summary(
            mock_customer,
            projects=[],
            opportunities=[],
            quotes=[mock_quote1, mock_quote2],
            contracts=[],
            payment_plans=[],
            communications=[]
        )

        assert result['avg_margin'] == Decimal("35")

    def test_handles_zero_opportunities(self):
        """测试处理零商机情况"""
        from app.services.customer_360_service import Customer360Service

        mock_db = MagicMock()
        service = Customer360Service(mock_db)

        mock_customer = MagicMock()

        result = service._build_summary(
            mock_customer,
            projects=[],
            opportunities=[],
            quotes=[],
            contracts=[],
            payment_plans=[],
            communications=[]
        )

        assert result['win_rate'] == 0.0
        assert result['pipeline_amount'] == Decimal("0")

    def test_finds_last_activity(self):
        """测试查找最后活动时间"""
        from app.services.customer_360_service import Customer360Service

        mock_db = MagicMock()
        service = Customer360Service(mock_db)

        mock_customer = MagicMock()

        now = datetime.now()
        mock_project = MagicMock()
        mock_project.updated_at = now

        result = service._build_summary(
            mock_customer,
            projects=[mock_project],
            opportunities=[],
            quotes=[],
            contracts=[],
            payment_plans=[],
            communications=[]
        )

        assert result['last_activity'] == now
