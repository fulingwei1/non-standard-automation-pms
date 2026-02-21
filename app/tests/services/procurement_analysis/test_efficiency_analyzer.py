# -*- coding: utf-8 -*-
"""
申请处理时效分析器测试
目标覆盖率: 60%+
测试用例数: 5个
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.services.procurement_analysis.request_efficiency import RequestEfficiencyAnalyzer


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return Mock(spec=Session)


@pytest.fixture
def sample_request_data():
    """创建示例采购申请数据"""
    data = []
    now = datetime.now()
    
    # 已处理的申请 - 24小时内
    for i in range(3):
        row = Mock()
        row.id = 100 + i
        row.request_no = f"REQ-{100+i}"
        row.requested_at = now - timedelta(hours=20)
        row.status = 'APPROVED'
        row.total_amount = Decimal('10000.00')
        row.source_type = 'MANUAL'
        row.order_created_at = now - timedelta(hours=4)
        data.append(row)
    
    # 已处理的申请 - 48小时内
    for i in range(2):
        row = Mock()
        row.id = 200 + i
        row.request_no = f"REQ-{200+i}"
        row.requested_at = now - timedelta(hours=40)
        row.status = 'APPROVED'
        row.total_amount = Decimal('20000.00')
        row.source_type = 'AUTO'
        row.order_created_at = now - timedelta(hours=2)
        data.append(row)
    
    # 已处理的申请 - 超过48小时
    for i in range(2):
        row = Mock()
        row.id = 300 + i
        row.request_no = f"REQ-{300+i}"
        row.requested_at = now - timedelta(hours=72)
        row.status = 'APPROVED'
        row.total_amount = Decimal('15000.00')
        row.source_type = 'MANUAL'
        row.order_created_at = now - timedelta(hours=12)
        data.append(row)
    
    # 未处理的申请
    for i in range(3):
        row = Mock()
        row.id = 400 + i
        row.request_no = f"REQ-{400+i}"
        row.requested_at = now - timedelta(hours=10)
        row.status = 'PENDING'
        row.total_amount = Decimal('8000.00')
        row.source_type = 'MANUAL'
        row.order_created_at = None
        data.append(row)
    
    return data


class TestRequestEfficiencyAnalyzer:
    """申请处理时效分析器测试类"""
    
    def test_get_request_efficiency_data_all_requests(self, mock_db, sample_request_data):
        """测试获取所有申请处理时效数据"""
        # 设置mock查询
        mock_query = Mock()
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = sample_request_data
        mock_db.query.return_value = mock_query
        
        # 调用方法
        result = RequestEfficiencyAnalyzer.get_request_efficiency_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证返回结果结构
        assert 'efficiency_data' in result
        assert 'summary' in result
        
        # 验证数据条数（最多返回50条）
        assert len(result['efficiency_data']) <= 50
        
        # 验证汇总数据
        summary = result['summary']
        assert summary['total_requests'] == 10
        assert summary['processed_count'] == 7  # 前7个是已处理的
        assert summary['pending_count'] == 3
        assert summary['avg_processing_hours'] >= 0
        
    def test_processing_time_calculation(self, mock_db, sample_request_data):
        """测试处理时长计算"""
        mock_query = Mock()
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = sample_request_data[:3]  # 只用24小时内的数据
        mock_db.query.return_value = mock_query
        
        result = RequestEfficiencyAnalyzer.get_request_efficiency_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证处理时长
        for item in result['efficiency_data']:
            assert 'processing_hours' in item
            assert 'processing_days' in item
            assert item['processing_hours'] > 0
            
    def test_within_24h_rate(self, mock_db, sample_request_data):
        """测试24小时内处理率统计"""
        mock_query = Mock()
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = sample_request_data[:7]  # 前7个已处理
        mock_db.query.return_value = mock_query
        
        result = RequestEfficiencyAnalyzer.get_request_efficiency_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证24小时内处理率
        summary = result['summary']
        assert summary['processed_within_24h'] == 3
        assert summary['processed_within_48h'] == 5
        assert summary['within_24h_rate'] > 0
        
    def test_pending_requests_tracking(self, mock_db, sample_request_data):
        """测试待处理申请追踪"""
        mock_query = Mock()
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = sample_request_data[7:]  # 只返回未处理的
        mock_db.query.return_value = mock_query
        
        result = RequestEfficiencyAnalyzer.get_request_efficiency_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证待处理申请标记
        for item in result['efficiency_data']:
            assert item.get('is_pending') == True
            assert item['order_created_at'] is None
            
    def test_empty_requests(self, mock_db):
        """测试空数据情况"""
        mock_query = Mock()
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        result = RequestEfficiencyAnalyzer.get_request_efficiency_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证空数据处理
        assert len(result['efficiency_data']) == 0
        assert result['summary']['total_requests'] == 0
        assert result['summary']['processed_count'] == 0
        assert result['summary']['pending_count'] == 0
        assert result['summary']['avg_processing_hours'] == 0
