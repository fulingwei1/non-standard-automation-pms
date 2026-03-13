# -*- coding: utf-8 -*-
"""
contract_milestone_service 单元测试

测试合同里程碑提醒服务。
"""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.sales.contract_milestone_service import (
    ContractMilestoneService,
    MilestoneType,
    MilestoneUrgency,
    ContractMilestone,
    MILESTONE_CONFIG,
)


# ========== 测试夹具 ==========

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return ContractMilestoneService(mock_db)


@pytest.fixture
def mock_contract():
    """模拟合同"""
    contract = MagicMock()
    contract.id = 1
    contract.contract_code = "CT202603120001"
    contract.contract_name = "测试合同"
    contract.status = "ACTIVE"
    contract.sales_owner_id = 1
    contract.contract_amount = 500000
    contract.end_date = date.today() + timedelta(days=30)
    contract.warranty_end_date = None
    contract.payment_plans = []
    contract.deliverables = []
    contract.customer = MagicMock()
    contract.customer.customer_name = "测试客户"
    return contract


# ========== 紧急程度判定测试 ==========

class TestGetUrgency:
    """_get_urgency 测试"""

    def test_overdue_for_negative_days(self, service):
        """负数天数为已过期"""
        assert service._get_urgency(-1, MilestoneType.PAYMENT) == MilestoneUrgency.OVERDUE
        assert service._get_urgency(-30, MilestoneType.CONTRACT_END) == MilestoneUrgency.OVERDUE

    def test_urgent_within_urgent_days(self, service):
        """在紧急天数内为紧急"""
        # PAYMENT urgent_days = 7
        assert service._get_urgency(5, MilestoneType.PAYMENT) == MilestoneUrgency.URGENT
        assert service._get_urgency(7, MilestoneType.PAYMENT) == MilestoneUrgency.URGENT

        # CONTRACT_END urgent_days = 30
        assert service._get_urgency(25, MilestoneType.CONTRACT_END) == MilestoneUrgency.URGENT

    def test_warning_within_warning_days(self, service):
        """在预警天数内为预警"""
        # PAYMENT warning_days = 14
        assert service._get_urgency(10, MilestoneType.PAYMENT) == MilestoneUrgency.WARNING
        assert service._get_urgency(14, MilestoneType.PAYMENT) == MilestoneUrgency.WARNING

        # CONTRACT_END warning_days = 60
        assert service._get_urgency(45, MilestoneType.CONTRACT_END) == MilestoneUrgency.WARNING

    def test_upcoming_beyond_warning_days(self, service):
        """超过预警天数为即将到来"""
        assert service._get_urgency(20, MilestoneType.PAYMENT) == MilestoneUrgency.UPCOMING
        assert service._get_urgency(90, MilestoneType.CONTRACT_END) == MilestoneUrgency.UPCOMING


# ========== 建议生成测试 ==========

class TestGetSuggestion:
    """_get_suggestion 测试"""

    def test_overdue_suggestion(self, service):
        """已过期建议"""
        suggestion = service._get_suggestion(MilestoneType.PAYMENT, -5)
        assert "逾期" in suggestion or "立即" in suggestion

    def test_urgent_suggestion(self, service):
        """紧急建议"""
        suggestion = service._get_suggestion(MilestoneType.PAYMENT, 5)
        assert "临近" in suggestion or "确认" in suggestion

    def test_warning_suggestion(self, service):
        """预警建议"""
        suggestion = service._get_suggestion(MilestoneType.PAYMENT, 10)
        assert "提前" in suggestion or "确认" in suggestion

    def test_upcoming_suggestion(self, service):
        """即将到来建议"""
        suggestion = service._get_suggestion(MilestoneType.PAYMENT, 20)
        assert "关注" in suggestion or "跟进" in suggestion

    def test_different_type_suggestions(self, service):
        """不同类型的建议不同"""
        payment_sug = service._get_suggestion(MilestoneType.PAYMENT, -1)
        delivery_sug = service._get_suggestion(MilestoneType.DELIVERY, -1)
        warranty_sug = service._get_suggestion(MilestoneType.WARRANTY_END, -1)
        contract_sug = service._get_suggestion(MilestoneType.CONTRACT_END, -1)

        # 都应该有内容
        assert len(payment_sug) > 0
        assert len(delivery_sug) > 0
        assert len(warranty_sug) > 0
        assert len(contract_sug) > 0


# ========== 里程碑提取测试 ==========

class TestExtractMilestones:
    """_extract_milestones 测试"""

    def test_extracts_contract_end_milestone(self, service, mock_contract):
        """提取合同到期里程碑"""
        today = date.today()
        mock_contract.end_date = today + timedelta(days=30)

        milestones = service._extract_milestones(
            mock_contract,
            today,
            today - timedelta(days=90),
            today + timedelta(days=60),
        )

        contract_milestones = [m for m in milestones if m.milestone_type == MilestoneType.CONTRACT_END]
        assert len(contract_milestones) == 1
        assert contract_milestones[0].milestone_name == "合同到期"
        assert contract_milestones[0].days_until == 30

    def test_extracts_warranty_end_milestone(self, service, mock_contract):
        """提取质保到期里程碑"""
        today = date.today()
        mock_contract.warranty_end_date = today + timedelta(days=20)

        milestones = service._extract_milestones(
            mock_contract,
            today,
            today - timedelta(days=90),
            today + timedelta(days=60),
        )

        warranty_milestones = [m for m in milestones if m.milestone_type == MilestoneType.WARRANTY_END]
        assert len(warranty_milestones) == 1
        assert warranty_milestones[0].milestone_name == "质保到期"

    def test_extracts_payment_milestones(self, service, mock_contract):
        """提取付款节点里程碑"""
        today = date.today()

        # 模拟收款计划
        payment_plan = MagicMock()
        payment_plan.planned_date = today + timedelta(days=10)
        payment_plan.status = "PENDING"
        payment_plan.amount = 100000
        payment_plan.payment_name = "首期款"
        mock_contract.payment_plans = [payment_plan]

        milestones = service._extract_milestones(
            mock_contract,
            today,
            today - timedelta(days=90),
            today + timedelta(days=60),
        )

        payment_milestones = [m for m in milestones if m.milestone_type == MilestoneType.PAYMENT]
        assert len(payment_milestones) == 1
        assert payment_milestones[0].amount == 100000

    def test_extracts_delivery_milestones(self, service, mock_contract):
        """提取交付节点里程碑"""
        today = date.today()

        # 模拟交付物
        deliverable = MagicMock()
        deliverable.due_date = today + timedelta(days=15)
        deliverable.status = "IN_PROGRESS"
        deliverable.name = "系统上线"
        mock_contract.deliverables = [deliverable]

        milestones = service._extract_milestones(
            mock_contract,
            today,
            today - timedelta(days=90),
            today + timedelta(days=60),
        )

        delivery_milestones = [m for m in milestones if m.milestone_type == MilestoneType.DELIVERY]
        assert len(delivery_milestones) == 1
        assert delivery_milestones[0].milestone_name == "系统上线"

    def test_skips_paid_payment_plans(self, service, mock_contract):
        """跳过已付款的计划"""
        today = date.today()

        payment_plan = MagicMock()
        payment_plan.planned_date = today + timedelta(days=10)
        payment_plan.status = "PAID"
        payment_plan.amount = 100000
        mock_contract.payment_plans = [payment_plan]

        milestones = service._extract_milestones(
            mock_contract,
            today,
            today - timedelta(days=90),
            today + timedelta(days=60),
        )

        payment_milestones = [m for m in milestones if m.milestone_type == MilestoneType.PAYMENT]
        assert len(payment_milestones) == 0

    def test_skips_delivered_deliverables(self, service, mock_contract):
        """跳过已交付的交付物"""
        today = date.today()

        deliverable = MagicMock()
        deliverable.due_date = today + timedelta(days=15)
        deliverable.status = "DELIVERED"
        deliverable.name = "系统上线"
        mock_contract.deliverables = [deliverable]

        milestones = service._extract_milestones(
            mock_contract,
            today,
            today - timedelta(days=90),
            today + timedelta(days=60),
        )

        delivery_milestones = [m for m in milestones if m.milestone_type == MilestoneType.DELIVERY]
        assert len(delivery_milestones) == 0

    def test_handles_missing_customer(self, service, mock_contract):
        """处理缺失客户"""
        today = date.today()
        mock_contract.customer = None
        mock_contract.end_date = today + timedelta(days=30)

        milestones = service._extract_milestones(
            mock_contract,
            today,
            today - timedelta(days=90),
            today + timedelta(days=60),
        )

        assert len(milestones) >= 1
        assert milestones[0].customer_name == "未知客户"


# ========== 获取里程碑列表测试 ==========

class TestGetUpcomingMilestones:
    """get_upcoming_milestones 测试"""

    def test_returns_milestones_sorted_by_urgency(self, service, mock_db, mock_contract):
        """按紧急程度排序返回里程碑"""
        today = date.today()

        # 创建多个合同模拟不同紧急程度
        contract1 = MagicMock()
        contract1.id = 1
        contract1.contract_code = "CT001"
        contract1.contract_name = "合同1"
        contract1.end_date = today - timedelta(days=5)  # 已过期
        contract1.warranty_end_date = None
        contract1.payment_plans = []
        contract1.deliverables = []
        contract1.customer = MagicMock()
        contract1.customer.customer_name = "客户1"
        contract1.contract_amount = 100000

        contract2 = MagicMock()
        contract2.id = 2
        contract2.contract_code = "CT002"
        contract2.contract_name = "合同2"
        contract2.end_date = today + timedelta(days=50)  # 即将到来
        contract2.warranty_end_date = None
        contract2.payment_plans = []
        contract2.deliverables = []
        contract2.customer = MagicMock()
        contract2.customer.customer_name = "客户2"
        contract2.contract_amount = 200000

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [contract1, contract2]

        milestones = service.get_upcoming_milestones(user_id=1)

        # 已过期的应该排在前面
        assert len(milestones) >= 1
        if len(milestones) >= 2:
            assert milestones[0].urgency == MilestoneUrgency.OVERDUE

    def test_filters_by_type(self, service, mock_db, mock_contract):
        """按类型过滤"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_contract]

        milestones = service.get_upcoming_milestones(
            user_id=1,
            include_types=[MilestoneType.PAYMENT],
        )

        # 由于 mock_contract 没有 payment_plans，应该没有 PAYMENT 类型
        payment_milestones = [m for m in milestones if m.milestone_type == MilestoneType.PAYMENT]
        assert len(payment_milestones) == 0

    def test_respects_limit(self, service, mock_db, mock_contract):
        """遵守数量限制"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_contract]

        milestones = service.get_upcoming_milestones(
            user_id=1,
            limit=1,
        )

        assert len(milestones) <= 1


# ========== 汇总统计测试 ==========

class TestGetMilestoneSummary:
    """get_milestone_summary 测试"""

    def test_summary_structure(self, service, mock_db, mock_contract):
        """汇总结构正确"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_contract]

        summary = service.get_milestone_summary(user_id=1)

        assert "total_count" in summary
        assert "by_urgency" in summary
        assert "by_type" in summary
        assert "critical_items" in summary

        # 按紧急程度分类
        assert "overdue" in summary["by_urgency"]
        assert "urgent" in summary["by_urgency"]
        assert "warning" in summary["by_urgency"]
        assert "upcoming" in summary["by_urgency"]

        # 按类型分类
        assert "payment" in summary["by_type"]
        assert "delivery" in summary["by_type"]
        assert "warranty" in summary["by_type"]
        assert "contract" in summary["by_type"]

    def test_counts_by_urgency(self, service, mock_db):
        """按紧急程度统计"""
        today = date.today()

        # 创建过期合同
        overdue_contract = MagicMock()
        overdue_contract.id = 1
        overdue_contract.contract_code = "CT001"
        overdue_contract.contract_name = "过期合同"
        overdue_contract.end_date = today - timedelta(days=10)
        overdue_contract.warranty_end_date = None
        overdue_contract.payment_plans = []
        overdue_contract.deliverables = []
        overdue_contract.customer = MagicMock()
        overdue_contract.customer.customer_name = "客户1"
        overdue_contract.contract_amount = 100000

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [overdue_contract]

        summary = service.get_milestone_summary(user_id=1)

        assert summary["by_urgency"]["overdue"]["count"] >= 1

    def test_collects_critical_items(self, service, mock_db):
        """收集紧急项"""
        today = date.today()

        # 创建紧急合同
        urgent_contract = MagicMock()
        urgent_contract.id = 1
        urgent_contract.contract_code = "CT001"
        urgent_contract.contract_name = "紧急合同"
        urgent_contract.end_date = today + timedelta(days=5)  # 即将到期
        urgent_contract.warranty_end_date = None
        urgent_contract.payment_plans = []
        urgent_contract.deliverables = []
        urgent_contract.customer = MagicMock()
        urgent_contract.customer.customer_name = "客户1"
        urgent_contract.contract_amount = 100000

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [urgent_contract]

        summary = service.get_milestone_summary(user_id=1)

        # CONTRACT_END 的 urgent_days 是 30，所以 5 天内应该是 URGENT
        critical_items = summary["critical_items"]
        assert len(critical_items) >= 1

    def test_limits_critical_items_to_ten(self, service, mock_db):
        """紧急项最多10个"""
        today = date.today()

        # 创建15个过期合同
        contracts = []
        for i in range(15):
            contract = MagicMock()
            contract.id = i + 1
            contract.contract_code = f"CT{i+1:03d}"
            contract.contract_name = f"合同{i+1}"
            contract.end_date = today - timedelta(days=i + 1)
            contract.warranty_end_date = None
            contract.payment_plans = []
            contract.deliverables = []
            contract.customer = MagicMock()
            contract.customer.customer_name = f"客户{i+1}"
            contract.contract_amount = 100000
            contracts.append(contract)

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = contracts

        summary = service.get_milestone_summary(user_id=1)

        assert len(summary["critical_items"]) <= 10


# ========== 配置测试 ==========

class TestMilestoneConfig:
    """MILESTONE_CONFIG 测试"""

    def test_all_types_have_config(self):
        """所有类型都有配置"""
        for milestone_type in MilestoneType:
            assert milestone_type in MILESTONE_CONFIG
            assert "warning_days" in MILESTONE_CONFIG[milestone_type]
            assert "urgent_days" in MILESTONE_CONFIG[milestone_type]

    def test_warning_days_greater_than_urgent_days(self):
        """预警天数大于紧急天数"""
        for milestone_type in MilestoneType:
            config = MILESTONE_CONFIG[milestone_type]
            assert config["warning_days"] > config["urgent_days"]


# ========== 数据类测试 ==========

class TestContractMilestone:
    """ContractMilestone 数据类测试"""

    def test_creates_milestone_with_all_fields(self):
        """创建包含所有字段的里程碑"""
        milestone = ContractMilestone(
            contract_id=1,
            contract_code="CT001",
            contract_name="测试合同",
            customer_name="测试客户",
            milestone_type=MilestoneType.PAYMENT,
            milestone_name="首期款",
            due_date=date.today() + timedelta(days=10),
            days_until=10,
            urgency=MilestoneUrgency.WARNING,
            amount=100000.0,
            suggestion="提前与客户确认付款安排",
        )

        assert milestone.contract_id == 1
        assert milestone.contract_code == "CT001"
        assert milestone.milestone_type == MilestoneType.PAYMENT
        assert milestone.urgency == MilestoneUrgency.WARNING
        assert milestone.amount == 100000.0

    def test_creates_milestone_without_amount(self):
        """创建不含金额的里程碑"""
        milestone = ContractMilestone(
            contract_id=1,
            contract_code="CT001",
            contract_name="测试合同",
            customer_name="测试客户",
            milestone_type=MilestoneType.DELIVERY,
            milestone_name="系统上线",
            due_date=date.today() + timedelta(days=15),
            days_until=15,
            urgency=MilestoneUrgency.WARNING,
            amount=None,
            suggestion="检查交付准备情况",
        )

        assert milestone.amount is None
