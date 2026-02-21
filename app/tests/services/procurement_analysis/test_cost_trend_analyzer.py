# -*- coding: utf-8 -*-
"""
成本趋势分析器测试
目标覆盖率: 60%+
测试用例数: 6个
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from app.services.procurement_analysis.cost_trend import CostTrendAnalyzer
from app.models.purchase import PurchaseOrder


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return Mock(spec=Session)


@pytest.fixture
def sample_orders():
    """创建示例订单数据"""
    orders = []
    # 2024年1月订单
    for i in range(3):
        order = Mock(spec=PurchaseOrder)
        order.order_date = date(2024, 1, 10 + i)
        order.amount_with_tax = Decimal(str(1000 + i * 100))
        order.status = 'APPROVED'
        order.project_id = 1
        orders.append(order)
    
    # 2024年2月订单
    for i in range(2):
        order = Mock(spec=PurchaseOrder)
        order.order_date = date(2024, 2, 15 + i)
        order.amount_with_tax = Decimal(str(2000 + i * 200))
        order.status = 'CONFIRMED'
        order.project_id = 1
        orders.append(order)
    
    # 2024年3月订单
    for i in range(4):
        order = Mock(spec=PurchaseOrder)
        order.order_date = date(2024, 3, 5 + i)
        order.amount_with_tax = Decimal(str(1500 + i * 150))
        order.status = 'RECEIVED'
        order.project_id = 1
        orders.append(order)
    
    return orders


class TestCostTrendAnalyzer:
    """成本趋势分析器测试类"""
    
    def test_get_cost_trend_data_by_month(self, mock_db, sample_orders):
        """测试按月统计成本趋势"""
        # 设置mock查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_orders
        mock_db.query.return_value = mock_query
        
        # 调用方法
        result = CostTrendAnalyzer.get_cost_trend_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            group_by="month"
        )
        
        # 验证返回结果结构
        assert 'summary' in result
        assert 'trend_data' in result
        assert len(result['trend_data']) == 3  # 3个月
        
        # 验证汇总数据
        summary = result['summary']
        assert summary['total_orders'] == 9
        assert summary['total_amount'] > 0
        assert summary['avg_monthly_amount'] > 0
        
        # 验证趋势数据
        trend_data = result['trend_data']
        assert trend_data[0]['period'] == '2024-01'
        assert trend_data[1]['period'] == '2024-02'
        assert trend_data[2]['period'] == '2024-03'
        
        # 验证每个月的数据
        assert trend_data[0]['order_count'] == 3
        assert trend_data[1]['order_count'] == 2
        assert trend_data[2]['order_count'] == 4
        
    def test_get_cost_trend_data_by_quarter(self, mock_db, sample_orders):
        """测试按季度统计成本趋势"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_orders
        mock_db.query.return_value = mock_query
        
        result = CostTrendAnalyzer.get_cost_trend_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            group_by="quarter"
        )
        
        # 验证季度分组
        assert len(result['trend_data']) == 1  # Q1
        assert result['trend_data'][0]['period'] == '2024-Q1'
        assert result['trend_data'][0]['order_count'] == 9
        
    def test_get_cost_trend_data_by_year(self, mock_db, sample_orders):
        """测试按年统计成本趋势"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_orders
        mock_db.query.return_value = mock_query
        
        result = CostTrendAnalyzer.get_cost_trend_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            group_by="year"
        )
        
        # 验证年度分组
        assert len(result['trend_data']) == 1  # 2024
        assert result['trend_data'][0]['period'] == '2024'
        assert result['trend_data'][0]['order_count'] == 9
        
    def test_get_cost_trend_data_with_project_filter(self, mock_db, sample_orders):
        """测试按项目筛选成本趋势"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_orders[:3]  # 只返回1月的订单
        mock_db.query.return_value = mock_query
        
        result = CostTrendAnalyzer.get_cost_trend_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            group_by="month",
            project_id=1
        )
        
        # 验证调用了项目筛选
        assert result['summary']['total_orders'] == 3
        
    def test_get_cost_trend_data_empty_orders(self, mock_db):
        """测试空订单情况"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        result = CostTrendAnalyzer.get_cost_trend_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            group_by="month"
        )
        
        # 验证空数据处理
        assert result['summary']['total_amount'] == 0
        assert result['summary']['total_orders'] == 0
        assert len(result['trend_data']) == 1
        assert result['trend_data'][0]['order_count'] == 0
        
    def test_mom_rate_calculation(self, mock_db, sample_orders):
        """测试环比增长率计算"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_orders
        mock_db.query.return_value = mock_query
        
        result = CostTrendAnalyzer.get_cost_trend_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            group_by="month"
        )
        
        # 验证环比增长率
        trend_data = result['trend_data']
        assert trend_data[0]['mom_rate'] == 0  # 第一个月没有环比
        assert trend_data[1]['mom_rate'] != 0  # 第二个月有环比
        assert trend_data[2]['mom_rate'] != 0  # 第三个月有环比
