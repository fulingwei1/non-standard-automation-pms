# -*- coding: utf-8 -*-
"""
交期准时率分析器测试
目标覆盖率: 60%+
测试用例数: 5个
"""
import pytest
from datetime import date
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.services.procurement_analysis.delivery_performance import DeliveryPerformanceAnalyzer


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return Mock(spec=Session)


@pytest.fixture
def sample_delivery_data():
    """创建示例交期数据"""
    # 模拟数据库查询结果
    data = []
    
    # 供应商1 - 准时交货
    for i in range(5):
        row = Mock()
        row.supplier_id = 1
        row.supplier_name = "供应商A"
        row.supplier_code = "SUP001"
        row.receipt_id = 100 + i
        row.receipt_date = date(2024, 1, 15)
        row.receipt_no = f"REC-{100+i}"
        row.promised_date = date(2024, 1, 20)  # 承诺日期晚于实际
        row.order_no = f"PO-{100+i}"
        row.order_id = 1000 + i
        data.append(row)
    
    # 供应商2 - 延期交货
    for i in range(3):
        row = Mock()
        row.supplier_id = 2
        row.supplier_name = "供应商B"
        row.supplier_code = "SUP002"
        row.receipt_id = 200 + i
        row.receipt_date = date(2024, 1, 25)
        row.receipt_no = f"REC-{200+i}"
        row.promised_date = date(2024, 1, 20)  # 承诺日期早于实际
        row.order_no = f"PO-{200+i}"
        row.order_id = 2000 + i
        data.append(row)
    
    # 供应商3 - 混合情况
    for i in range(4):
        row = Mock()
        row.supplier_id = 3
        row.supplier_name = "供应商C"
        row.supplier_code = "SUP003"
        row.receipt_id = 300 + i
        row.receipt_date = date(2024, 1, 15 + i * 3)
        row.receipt_no = f"REC-{300+i}"
        row.promised_date = date(2024, 1, 18) if i % 2 == 0 else date(2024, 1, 12 + i * 3)
        row.order_no = f"PO-{300+i}"
        row.order_id = 3000 + i
        data.append(row)
    
    return data


class TestDeliveryPerformanceAnalyzer:
    """交期准时率分析器测试类"""
    
    def test_get_delivery_performance_data_all_suppliers(self, mock_db, sample_delivery_data):
        """测试获取所有供应商交期数据"""
        # 设置mock查询
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_delivery_data
        mock_db.query.return_value = mock_query
        
        # 调用方法
        result = DeliveryPerformanceAnalyzer.get_delivery_performance_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证返回结果结构
        assert 'supplier_performance' in result
        assert 'delayed_orders' in result
        assert 'summary' in result
        
        # 验证供应商数量
        assert len(result['supplier_performance']) == 3
        
        # 验证汇总数据
        summary = result['summary']
        assert summary['total_suppliers'] == 3
        assert summary['avg_on_time_rate'] >= 0
        assert summary['total_delayed_orders'] >= 0
        
    def test_supplier_on_time_rate_calculation(self, mock_db, sample_delivery_data):
        """测试供应商准时率计算"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_delivery_data[:5]  # 只用供应商A的数据
        mock_db.query.return_value = mock_query
        
        result = DeliveryPerformanceAnalyzer.get_delivery_performance_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 供应商A的所有订单都是准时的
        supplier_a = result['supplier_performance'][0]
        assert supplier_a['supplier_name'] == "供应商A"
        assert supplier_a['total_deliveries'] == 5
        assert supplier_a['on_time_deliveries'] == 5
        assert supplier_a['delayed_deliveries'] == 0
        assert supplier_a['on_time_rate'] == 100.0
        
    def test_delayed_orders_tracking(self, mock_db, sample_delivery_data):
        """测试延期订单追踪"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_delivery_data[5:8]  # 供应商B的延期数据
        mock_db.query.return_value = mock_query
        
        result = DeliveryPerformanceAnalyzer.get_delivery_performance_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证延期订单记录
        delayed_orders = result['delayed_orders']
        assert len(delayed_orders) == 3
        
        # 验证延期天数计算
        for order in delayed_orders:
            assert order['delay_days'] == 5  # 1月25日 - 1月20日 = 5天
            assert 'order_no' in order
            assert 'receipt_no' in order
            
    def test_filter_by_supplier(self, mock_db, sample_delivery_data):
        """测试按供应商筛选"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_delivery_data[:5]  # 只返回供应商A
        mock_db.query.return_value = mock_query
        
        result = DeliveryPerformanceAnalyzer.get_delivery_performance_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            supplier_id=1
        )
        
        # 验证只有一个供应商
        assert len(result['supplier_performance']) == 1
        assert result['supplier_performance'][0]['supplier_id'] == 1
        
    def test_empty_delivery_data(self, mock_db):
        """测试空数据情况"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        result = DeliveryPerformanceAnalyzer.get_delivery_performance_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证空数据处理
        assert len(result['supplier_performance']) == 0
        assert len(result['delayed_orders']) == 0
        assert result['summary']['total_suppliers'] == 0
        assert result['summary']['avg_on_time_rate'] == 0
