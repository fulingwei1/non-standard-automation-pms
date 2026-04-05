# -*- coding: utf-8 -*-
"""
collection_priority_service 单元测试

测试催款优先级排序服务。
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.sales.collection_priority_service import (
    CollectionPriorityService,
    CollectionUrgency,
    CollectionRisk,
    OVERDUE_WEIGHTS,
    AMOUNT_THRESHOLDS,
    CREDIT_WEIGHTS,
)


# ========== 测试夹具 ==========

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return CollectionPriorityService(mock_db)


@pytest.fixture
def mock_invoice():
    """模拟发票"""
    invoice = MagicMock()
    invoice.id = 1
    invoice.invoice_code = "INV202603120001"
    invoice.status = "ISSUED"
    invoice.payment_status = "OVERDUE"
    invoice.total_amount = 100000
    invoice.amount = 100000
    invoice.paid_amount = 0
    invoice.due_date = date.today() - timedelta(days=45)  # 45天前到期
    invoice.issue_date = date.today() - timedelta(days=75)
    # 合同关联
    invoice.contract = MagicMock()
    invoice.contract.id = 1
    invoice.contract.contract_code = "CT202603120001"
    invoice.contract.customer_id = 1
    invoice.contract.customer = MagicMock()
    invoice.contract.customer.customer_name = "测试客户"
    invoice.contract.customer.credit_level = "B"
    return invoice


# ========== 优先级得分计算测试 ==========

class TestCalculatePriorityScore:
    """_calculate_priority_score 测试"""

    def test_high_amount_high_score(self, service):
        """高金额高得分"""
        # 100万以上 = 30分 + 0天逾期 = 30分
        score = service._calculate_priority_score(
            unpaid_amount=1500000,  # 150万
            overdue_days=0,
            credit_level="B",
            historical_rate=80,
        )
        assert score >= 30

    def test_long_overdue_high_score(self, service):
        """长期逾期高得分"""
        # 10万 = 15分 + 90天以上逾期 = 80分
        score = service._calculate_priority_score(
            unpaid_amount=100000,
            overdue_days=100,
            credit_level="B",
            historical_rate=80,
        )
        assert score >= 80

    def test_poor_credit_increases_score(self, service):
        """差信用提高得分"""
        score_good = service._calculate_priority_score(
            unpaid_amount=100000,
            overdue_days=30,
            credit_level="A",  # 优质客户
            historical_rate=80,
        )
        score_bad = service._calculate_priority_score(
            unpaid_amount=100000,
            overdue_days=30,
            credit_level="D",  # 高风险客户
            historical_rate=80,
        )
        assert score_bad > score_good

    def test_low_payment_rate_increases_score(self, service):
        """低付款率提高得分"""
        score_high_rate = service._calculate_priority_score(
            unpaid_amount=100000,
            overdue_days=30,
            credit_level="B",
            historical_rate=90,
        )
        score_low_rate = service._calculate_priority_score(
            unpaid_amount=100000,
            overdue_days=30,
            credit_level="B",
            historical_rate=40,
        )
        assert score_low_rate > score_high_rate


# ========== 紧急程度判定测试 ==========

class TestDetermineUrgency:
    """_determine_urgency 测试"""

    def test_critical_for_high_score(self, service):
        """高分为紧急"""
        urgency = service._determine_urgency(
            overdue_days=30,
            unpaid_amount=50000,
            priority_score=75,
        )
        assert urgency == CollectionUrgency.CRITICAL

    def test_critical_for_high_amount_long_overdue(self, service):
        """高金额+长期逾期为紧急"""
        urgency = service._determine_urgency(
            overdue_days=65,
            unpaid_amount=150000,  # 15万
            priority_score=50,
        )
        assert urgency == CollectionUrgency.CRITICAL

    def test_high_for_medium_score(self, service):
        """中等分为高优先"""
        urgency = service._determine_urgency(
            overdue_days=35,
            unpaid_amount=50000,
            priority_score=55,
        )
        assert urgency == CollectionUrgency.HIGH

    def test_medium_for_low_overdue(self, service):
        """轻微逾期为中优先"""
        urgency = service._determine_urgency(
            overdue_days=15,
            unpaid_amount=30000,
            priority_score=35,
        )
        assert urgency == CollectionUrgency.MEDIUM

    def test_low_for_not_overdue(self, service):
        """未逾期为低优先"""
        urgency = service._determine_urgency(
            overdue_days=0,
            unpaid_amount=20000,
            priority_score=20,
        )
        assert urgency == CollectionUrgency.LOW


# ========== 风险等级判定测试 ==========

class TestDetermineRisk:
    """_determine_risk 测试"""

    def test_high_risk_for_multiple_factors(self, service):
        """多因素高风险"""
        risk = service._determine_risk(
            overdue_days=100,
            historical_rate=40,
            credit_level="D",
        )
        assert risk == CollectionRisk.HIGH

    def test_medium_risk_for_some_factors(self, service):
        """部分因素中风险"""
        # 逾期70天(+1) + 历史付款率60%(+1) = 2个风险因素 = MEDIUM
        risk = service._determine_risk(
            overdue_days=70,
            historical_rate=60,
            credit_level="B",
        )
        assert risk == CollectionRisk.MEDIUM

    def test_low_risk_for_good_customer(self, service):
        """优质客户低风险"""
        risk = service._determine_risk(
            overdue_days=20,
            historical_rate=90,
            credit_level="A",
        )
        assert risk == CollectionRisk.LOW


# ========== 建议生成测试 ==========

class TestGenerateSuggestion:
    """_generate_suggestion 测试"""

    def test_critical_suggestion(self, service):
        """紧急催款建议"""
        suggestion, action_points = service._generate_suggestion(
            urgency=CollectionUrgency.CRITICAL,
            risk=CollectionRisk.HIGH,
            overdue_days=90,
            unpaid_amount=100000,
            customer_name="测试客户",
            historical_rate=40,
        )
        assert "紧急" in suggestion
        assert len(action_points) >= 2
        assert any("电话" in point for point in action_points)

    def test_high_suggestion(self, service):
        """高优先催款建议"""
        suggestion, action_points = service._generate_suggestion(
            urgency=CollectionUrgency.HIGH,
            risk=CollectionRisk.MEDIUM,
            overdue_days=45,
            unpaid_amount=50000,
            customer_name="测试客户",
            historical_rate=70,
        )
        assert "高优先" in suggestion
        assert len(action_points) >= 1

    def test_low_historical_rate_adds_suggestion(self, service):
        """低历史付款率添加建议"""
        suggestion, action_points = service._generate_suggestion(
            urgency=CollectionUrgency.MEDIUM,
            risk=CollectionRisk.MEDIUM,
            overdue_days=30,
            unpaid_amount=30000,
            customer_name="测试客户",
            historical_rate=40,
        )
        assert any("历史付款率" in point for point in action_points)


# ========== 发票列表测试 ==========

class TestGetPrioritizedCollections:
    """get_prioritized_collections 测试"""

    def test_returns_sorted_list(self, service, mock_db, mock_invoice):
        """返回排序列表"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_invoice]

        # Mock 历史付款率查询，避免额外的 DB 调用
        with patch.object(service, '_get_historical_payment_rate', return_value=70.0):
            items = service.get_prioritized_collections(user_id=1)

        assert len(items) == 1
        assert items[0].invoice_code == "INV202603120001"
        assert items[0].overdue_days == 45

    def test_empty_when_no_invoices(self, service, mock_db):
        """无发票返回空列表"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        items = service.get_prioritized_collections(user_id=1)

        assert len(items) == 0


# ========== 汇总统计测试 ==========

class TestGetCollectionSummary:
    """get_collection_summary 测试"""

    def test_summary_structure(self, service, mock_db):
        """汇总结构正确"""
        with patch.object(service, 'get_prioritized_collections', return_value=[]):
            summary = service.get_collection_summary(user_id=1)

        assert "total_count" in summary
        assert "total_unpaid" in summary
        assert "by_urgency" in summary
        assert "by_risk" in summary
        assert "overdue_aging" in summary
        assert "top_priority_items" in summary

    def test_counts_by_urgency(self, service, mock_db, mock_invoice):
        """按紧急程度统计"""
        from app.services.sales.collection_priority_service import CollectionItem

        mock_item = CollectionItem(
            invoice_id=1,
            invoice_code="INV001",
            contract_id=1,
            contract_code="CT001",
            customer_id=1,
            customer_name="测试客户",
            invoice_amount=100000,
            paid_amount=0,
            unpaid_amount=100000,
            due_date=date.today() - timedelta(days=45),
            overdue_days=45,
            issue_date=None,
            urgency=CollectionUrgency.HIGH,
            risk=CollectionRisk.MEDIUM,
            priority_score=60,
            customer_credit_level="B",
            historical_payment_rate=70,
            suggestion="测试建议",
            action_points=["行动1"],
        )

        with patch.object(service, 'get_prioritized_collections', return_value=[mock_item]):
            summary = service.get_collection_summary(user_id=1)

        assert summary["total_count"] == 1
        assert summary["by_urgency"]["high"]["count"] == 1
        assert summary["by_urgency"]["high"]["amount"] == 100000


# ========== 历史付款率测试 ==========

class TestGetHistoricalPaymentRate:
    """_get_historical_payment_rate 测试"""

    def test_default_for_no_customer(self, service):
        """无客户返回默认值"""
        rate = service._get_historical_payment_rate(0)
        assert rate == 50.0

    def test_calculates_from_invoices(self, service, mock_db):
        """根据发票计算"""
        mock_result = MagicMock()
        mock_result.total = 10
        mock_result.paid_count = 8

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result

        rate = service._get_historical_payment_rate(1)

        assert rate == 80.0
