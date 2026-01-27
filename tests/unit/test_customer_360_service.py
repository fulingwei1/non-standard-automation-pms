# -*- coding: utf-8 -*-
"""
customer_360_service 单元测试

测试客户360度视图服务的各个方法：
- 视图概览构建
- 汇总计算
- 辅助函数
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.customer_360_service import Customer360Service, _decimal


def create_mock_db_session():
    """创建模拟的数据库会话"""
    return MagicMock()


def create_mock_customer(
    customer_id=1,
    customer_name="测试客户",
    customer_code="CUST-001",
    contact_person="张三",
):
    """创建模拟的客户对象"""
    mock_customer = MagicMock()
    mock_customer.id = customer_id
    mock_customer.customer_name = customer_name
    mock_customer.customer_code = customer_code
    mock_customer.contact_person = contact_person
    return mock_customer


def create_mock_project(
    project_id=1,
    project_name="测试项目",
    status="ACTIVE",
    updated_at=None,
):
    """创建模拟的项目对象"""
    mock_project = MagicMock()
    mock_project.id = project_id
    mock_project.project_name = project_name
    mock_project.status = status
    mock_project.updated_at = updated_at or datetime.now()
    return mock_project


def create_mock_opportunity(
    opp_id=1,
    name="测试商机",
    stage="QUALIFIED",
    est_amount=Decimal("100000"),
    updated_at=None,
):
    """创建模拟的商机对象"""
    mock_opp = MagicMock()
    mock_opp.id = opp_id
    mock_opp.name = name
    mock_opp.stage = stage
    mock_opp.est_amount = est_amount
    mock_opp.updated_at = updated_at or datetime.now()
    return mock_opp


def create_mock_quote(
    quote_id=1,
    quote_no="Q-001",
    gross_margin=Decimal("25.0"),
    updated_at=None,
):
    """创建模拟的报价对象"""
    mock_quote = MagicMock()
    mock_quote.id = quote_id
    mock_quote.quote_no = quote_no
    mock_quote.updated_at = updated_at or datetime.now()
    # 模拟 current_version
    mock_version = MagicMock()
    mock_version.gross_margin = gross_margin
    mock_quote.current_version = mock_version
    return mock_quote


def create_mock_contract(
    contract_id=1,
    contract_no="C-001",
    contract_amount=Decimal("500000"),
    updated_at=None,
):
    """创建模拟的合同对象"""
    mock_contract = MagicMock()
    mock_contract.id = contract_id
    mock_contract.contract_no = contract_no
    mock_contract.contract_amount = contract_amount
    mock_contract.updated_at = updated_at or datetime.now()
    return mock_contract


def create_mock_payment_plan(
    plan_id=1,
    planned_amount=Decimal("100000"),
    actual_amount=Decimal("0"),
    status="PENDING",
    planned_date=None,
):
    """创建模拟的回款计划"""
    mock_plan = MagicMock()
    mock_plan.id = plan_id
    mock_plan.planned_amount = planned_amount
    mock_plan.actual_amount = actual_amount
    mock_plan.status = status
    mock_plan.planned_date = planned_date or date.today()
    return mock_plan


def create_mock_communication(
    comm_id=1,
    customer_name="测试客户",
    communication_date=None,
):
    """创建模拟的沟通记录"""
    mock_comm = MagicMock()
    mock_comm.id = comm_id
    mock_comm.customer_name = customer_name
    mock_comm.communication_date = communication_date or date.today()
    return mock_comm


@pytest.mark.unit
class TestDecimalHelper:
    """测试 _decimal 辅助函数"""

    def test_handles_none(self):
        """测试 None 值转换为 0"""
        assert _decimal(None) == Decimal("0")

    def test_handles_decimal(self):
        """测试 Decimal 值直接返回"""
        value = Decimal("123.45")
        assert _decimal(value) == value

    def test_handles_int(self):
        """测试整数转换"""
        assert _decimal(100) == Decimal("100")

    def test_handles_float(self):
        """测试浮点数转换"""
        result = _decimal(99.99)
        assert result == Decimal("99.99")

    def test_handles_string(self):
        """测试字符串转换"""
        assert _decimal("500.00") == Decimal("500.00")

    def test_handles_invalid_value(self):
        """测试无效值转换为 0"""
        assert _decimal("invalid") == Decimal("0")
        assert _decimal([1, 2, 3]) == Decimal("0")


@pytest.mark.unit
class TestBuildOverview:
    """测试 build_overview 方法"""

    def test_raises_error_for_nonexistent_customer(self):
        """测试客户不存在时抛出错误"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.first.return_value = None

        service = Customer360Service(db)

        with pytest.raises(ValueError, match="客户不存在"):
            service.build_overview(999)

    def test_returns_overview_structure(self):
        """测试返回的概览结构"""
        db = create_mock_db_session()
        customer = create_mock_customer()

        # 配置链式调用返回
        def configure_query_chain(query_mock, result):
            query_mock.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            result
            )
            return query_mock

            call_count = [0]

        def query_side_effect(model):
            mock_query = MagicMock()
            model_name = str(model)

            if call_count[0] == 0:  # Customer
            mock_query.filter.return_value.first.return_value = customer
        elif call_count[0] == 1:  # Project
        configure_query_chain(mock_query, [create_mock_project()])
        elif call_count[0] == 2:  # Opportunity
        configure_query_chain(mock_query, [])
        elif call_count[0] == 3:  # Quote
        configure_query_chain(mock_query, [])
        elif call_count[0] == 4:  # Contract
        configure_query_chain(mock_query, [])
        elif call_count[0] == 5:  # Invoice (join query)
        mock_query.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        elif call_count[0] == 6:  # PaymentPlan (join query)
        mock_query.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        elif call_count[0] == 7:  # Communication
        configure_query_chain(mock_query, [])

        call_count[0] += 1
        return mock_query

        db.query.side_effect = query_side_effect

        service = Customer360Service(db)
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


@pytest.mark.unit
class TestBuildSummary:
    """测试 _build_summary 方法"""

    def test_calculates_total_contract_amount(self):
        """测试合同总额计算"""
        db = create_mock_db_session()
        service = Customer360Service(db)

        customer = create_mock_customer()
        contracts = [
        create_mock_contract(contract_amount=Decimal("100000")),
        create_mock_contract(contract_amount=Decimal("200000")),
        ]

        summary = service._build_summary(
        customer=customer,
        projects=[],
        opportunities=[],
        quotes=[],
        contracts=contracts,
        payment_plans=[],
        communications=[],
        )

        assert summary["total_contract_amount"] == Decimal("300000")

    def test_calculates_open_receivables(self):
        """测试应收账款计算"""
        db = create_mock_db_session()
        service = Customer360Service(db)

        customer = create_mock_customer()
        payment_plans = [
        create_mock_payment_plan(
        planned_amount=Decimal("100000"),
        actual_amount=Decimal("30000"),
        status="PENDING",
        ),
        create_mock_payment_plan(
        planned_amount=Decimal("50000"),
        actual_amount=Decimal("50000"),
        status="PAID",  # 已付清，不计入应收
        ),
        ]

        summary = service._build_summary(
        customer=customer,
        projects=[],
        opportunities=[],
        quotes=[],
        contracts=[],
        payment_plans=payment_plans,
        communications=[],
        )

        # 只计算 PENDING 状态的差额：100000 - 30000 = 70000
        assert summary["open_receivables"] == Decimal("70000")

    def test_calculates_pipeline_amount(self):
        """测试管道金额计算"""
        db = create_mock_db_session()
        service = Customer360Service(db)

        customer = create_mock_customer()
        opportunities = [
        create_mock_opportunity(stage="QUALIFIED", est_amount=Decimal("100000")),
        create_mock_opportunity(stage="PROPOSAL", est_amount=Decimal("200000")),
        create_mock_opportunity(stage="WON", est_amount=Decimal("300000")),  # 不计入管道
        create_mock_opportunity(stage="LOST", est_amount=Decimal("400000")),  # 不计入管道
        ]

        summary = service._build_summary(
        customer=customer,
        projects=[],
        opportunities=opportunities,
        quotes=[],
        contracts=[],
        payment_plans=[],
        communications=[],
        )

        # 管道金额：100000 + 200000 = 300000
        assert summary["pipeline_amount"] == Decimal("300000")

    def test_calculates_win_rate(self):
        """测试赢单率计算"""
        db = create_mock_db_session()
        service = Customer360Service(db)

        customer = create_mock_customer()
        opportunities = [
        create_mock_opportunity(stage="WON"),
        create_mock_opportunity(stage="WON"),
        create_mock_opportunity(stage="LOST"),
        create_mock_opportunity(stage="QUALIFIED"),
        ]

        summary = service._build_summary(
        customer=customer,
        projects=[],
        opportunities=opportunities,
        quotes=[],
        contracts=[],
        payment_plans=[],
        communications=[],
        )

        # 赢单率：2/4 = 50%
        assert summary["win_rate"] == 50.0

    def test_calculates_avg_margin(self):
        """测试平均毛利率计算"""
        db = create_mock_db_session()
        service = Customer360Service(db)

        customer = create_mock_customer()
        quotes = [
        create_mock_quote(gross_margin=Decimal("20.0")),
        create_mock_quote(gross_margin=Decimal("30.0")),
        create_mock_quote(gross_margin=Decimal("25.0")),
        ]

        summary = service._build_summary(
        customer=customer,
        projects=[],
        opportunities=[],
        quotes=quotes,
        contracts=[],
        payment_plans=[],
        communications=[],
        )

        # 平均毛利率：(20+30+25)/3 = 25
        assert summary["avg_margin"] == Decimal("25")

    def test_counts_active_projects(self):
        """测试活跃项目计数"""
        db = create_mock_db_session()
        service = Customer360Service(db)

        customer = create_mock_customer()
        projects = [
        create_mock_project(status="ACTIVE"),
        create_mock_project(status="IN_PROGRESS"),
        create_mock_project(status="CLOSED"),  # 不计入活跃
        create_mock_project(status="CANCELLED"),  # 不计入活跃
        ]

        summary = service._build_summary(
        customer=customer,
        projects=projects,
        opportunities=[],
        quotes=[],
        contracts=[],
        payment_plans=[],
        communications=[],
        )

        assert summary["total_projects"] == 4
        assert summary["active_projects"] == 2

    def test_handles_empty_data(self):
        """测试空数据处理"""
        db = create_mock_db_session()
        service = Customer360Service(db)

        customer = create_mock_customer()

        summary = service._build_summary(
        customer=customer,
        projects=[],
        opportunities=[],
        quotes=[],
        contracts=[],
        payment_plans=[],
        communications=[],
        )

        assert summary["total_projects"] == 0
        assert summary["active_projects"] == 0
        assert summary["pipeline_amount"] == Decimal("0")
        assert summary["total_contract_amount"] == Decimal("0")
        assert summary["open_receivables"] == Decimal("0")
        assert summary["win_rate"] == 0
        assert summary["avg_margin"] is None
        assert summary["last_activity"] is None

    def test_finds_last_activity(self):
        """测试最后活动时间查找"""
        db = create_mock_db_session()
        service = Customer360Service(db)

        customer = create_mock_customer()
        older_time = datetime(2024, 1, 1, 10, 0, 0)
        newer_time = datetime(2024, 6, 15, 14, 30, 0)

        projects = [create_mock_project(updated_at=older_time)]
        opportunities = [create_mock_opportunity(updated_at=newer_time)]

        summary = service._build_summary(
        customer=customer,
        projects=projects,
        opportunities=opportunities,
        quotes=[],
        contracts=[],
        payment_plans=[],
        communications=[],
        )

        assert summary["last_activity"] == newer_time

    def test_handles_none_gross_margin(self):
        """测试报价无毛利率的情况"""
        db = create_mock_db_session()
        service = Customer360Service(db)

        customer = create_mock_customer()
        quote_with_none = create_mock_quote()
        quote_with_none.current_version.gross_margin = None

        quotes = [
        quote_with_none,
        create_mock_quote(gross_margin=Decimal("30.0")),
        ]

        summary = service._build_summary(
        customer=customer,
        projects=[],
        opportunities=[],
        quotes=quotes,
        contracts=[],
        payment_plans=[],
        communications=[],
        )

        # 只计算有毛利率的报价
        assert summary["avg_margin"] == Decimal("30")
