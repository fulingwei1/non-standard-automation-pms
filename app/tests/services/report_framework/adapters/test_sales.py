# -*- coding: utf-8 -*-
"""
销售报表适配器测试
目标覆盖率: 60%+
测试用例数: 5个
"""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from app.services.report_framework.adapters.sales import SalesReportAdapter


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = Mock(spec=Session)
    db.query = Mock(return_value=Mock())
    db.execute = Mock()
    return db


@pytest.fixture
def adapter(mock_db):
    """创建适配器实例"""
    return SalesReportAdapter(db=mock_db)


@pytest.fixture
def sample_contracts():
    """创建示例合同数据"""
    contracts = []
    for i in range(3):
        contract = Mock()
        contract.signed_date = date(2024, 1, 10 + i)
        contract.contract_amount = Decimal('100000.00') + Decimal(i * 10000)
        contract.status = 'SIGNED'
        contracts.append(contract)
    return contracts


@pytest.fixture
def sample_orders():
    """创建示例订单数据"""
    orders = []
    for i in range(2):
        order = Mock()
        order.created_at = date(2024, 1, 15 + i)
        order.order_amount = Decimal('50000.00') + Decimal(i * 5000)
        orders.append(order)
    return orders


class TestSalesReportAdapter:
    """销售报表适配器测试类"""
    
    def test_get_report_code(self, adapter):
        """测试获取报表代码"""
        assert adapter.get_report_code() == "SALES_MONTHLY"
        
    def test_generate_data_with_valid_month(self, adapter, sample_contracts, sample_orders, mock_db):
        """测试生成指定月份的销售报表数据"""
        # 设置mock查询
        mock_contract_query = Mock()
        mock_contract_query.filter.return_value = mock_contract_query
        mock_contract_query.all.return_value = sample_contracts
        
        mock_order_query = Mock()
        mock_order_query.filter.return_value = mock_order_query
        mock_order_query.all.return_value = sample_orders
        
        # 设置数据库execute的返回值
        mock_db.execute.side_effect = [
            Mock(fetchone=lambda: (Decimal('100000.00'),)),  # planned_receipt_amount
            Mock(fetchone=lambda: (Decimal('80000.00'),)),   # actual_receipt_amount
            Mock(fetchone=lambda: (Decimal('20000.00'),)),   # overdue_amount
            Mock(fetchone=lambda: (10,)),                     # total_needed for invoice
        ]
        
        # 模拟invoice查询
        mock_invoice_query = Mock()
        mock_invoice_query.filter.return_value = mock_invoice_query
        mock_invoice_query.all.return_value = []
        
        # 模拟bidding查询
        mock_bidding_query = Mock()
        mock_bidding_query.filter.return_value = mock_bidding_query
        mock_bidding_query.count.return_value = 5
        
        # 设置query的返回值根据不同的模型
        def query_side_effect(model):
            from app.models.sales import Contract, Invoice
            from app.models.business_support import BiddingProject, SalesOrder
            
            if model == Contract:
                return mock_contract_query
            elif model == SalesOrder:
                return mock_order_query
            elif model == Invoice:
                return mock_invoice_query
            elif model == BiddingProject:
                return mock_bidding_query
            return Mock()
        
        mock_db.query.side_effect = query_side_effect
        
        # 调用方法
        params = {"month": "2024-01"}
        result = adapter.generate_data(params)
        
        # 验证返回结果结构
        assert "report_date" in result
        assert result["report_date"] == "2024-01"
        assert "report_type" in result
        assert result["report_type"] == "monthly"
        assert "contract_statistics" in result
        assert "order_statistics" in result
        assert "receipt_statistics" in result
        assert "invoice_statistics" in result
        assert "bidding_statistics" in result
        
    def test_generate_data_with_default_month(self, adapter, mock_db):
        """测试使用默认月份生成报表"""
        # 设置mock查询返回空数据
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query
        
        # 设置execute返回值
        mock_db.execute.return_value = Mock(fetchone=lambda: (Decimal('0'),))
        
        # 不传month参数
        params = {}
        result = adapter.generate_data(params)
        
        # 验证使用了默认月份
        assert "report_date" in result
        assert result["report_type"] == "monthly"
        
    def test_generate_data_invalid_month_format(self, adapter):
        """测试无效的月份格式"""
        params = {"month": "invalid-format"}
        
        with pytest.raises(ValueError) as exc:
            adapter.generate_data(params)
        
        assert "月份格式错误" in str(exc.value)
        
    def test_contract_statistics(self, adapter, sample_contracts, mock_db):
        """测试合同统计计算"""
        # 设置mock
        mock_contract_query = Mock()
        mock_contract_query.filter.return_value = mock_contract_query
        mock_contract_query.all.return_value = sample_contracts
        mock_contract_query.count.return_value = len(sample_contracts)
        
        mock_empty_query = Mock()
        mock_empty_query.filter.return_value = mock_empty_query
        mock_empty_query.all.return_value = []
        mock_empty_query.count.return_value = 0
        
        def query_side_effect(model):
            from app.models.sales import Contract
            if model == Contract:
                return mock_contract_query
            return mock_empty_query
        
        mock_db.query.side_effect = query_side_effect
        mock_db.execute.return_value = Mock(fetchone=lambda: (Decimal('0'),))
        
        # 调用方法
        params = {"month": "2024-01"}
        result = adapter.generate_data(params)
        
        # 验证合同统计
        contract_stats = result["contract_statistics"]
        assert contract_stats["new_contracts_count"] == 3
        assert contract_stats["new_contracts_amount"] > 0
        
    def test_empty_data(self, adapter, mock_db):
        """测试空数据情况"""
        # 设置所有查询返回空
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.count.return_value = 0
        mock_db.query.return_value = mock_query
        
        mock_db.execute.return_value = Mock(fetchone=lambda: (Decimal('0'),))
        
        # 调用方法
        params = {"month": "2024-01"}
        result = adapter.generate_data(params)
        
        # 验证空数据处理
        assert result["contract_statistics"]["new_contracts_count"] == 0
        assert result["order_statistics"]["new_orders_count"] == 0
        assert result["bidding_statistics"]["new_bidding"] == 0
