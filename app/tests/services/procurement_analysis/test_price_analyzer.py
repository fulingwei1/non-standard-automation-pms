# -*- coding: utf-8 -*-
"""
价格波动分析器测试
目标覆盖率: 60%+
测试用例数: 6个
"""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.services.procurement_analysis.price_analysis import PriceAnalyzer


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return Mock(spec=Session)


@pytest.fixture
def sample_price_data():
    """创建示例价格数据"""
    data = []
    
    # 物料A - 价格波动大
    prices_a = [100, 120, 95, 130, 110]
    for i, price in enumerate(prices_a):
        row = Mock()
        row.material_code = "MAT-001"
        row.material_name = "物料A"
        row.unit_price = Decimal(str(price))
        row.order_date = date(2024, 1, 1 + i * 5)
        row.supplier_name = f"供应商{i % 2 + 1}"
        row.supplier_id = i % 2 + 1
        row.category_name = "分类1"
        row.standard_price = Decimal('110.00')
        data.append(row)
    
    # 物料B - 价格稳定
    for i in range(4):
        row = Mock()
        row.material_code = "MAT-002"
        row.material_name = "物料B"
        row.unit_price = Decimal('200.00')
        row.order_date = date(2024, 1, 1 + i * 7)
        row.supplier_name = "供应商1"
        row.supplier_id = 1
        row.category_name = "分类2"
        row.standard_price = Decimal('200.00')
        data.append(row)
    
    # 物料C - 价格持续上涨
    for i in range(3):
        row = Mock()
        row.material_code = "MAT-003"
        row.material_name = "物料C"
        row.unit_price = Decimal(str(150 + i * 20))
        row.order_date = date(2024, 1, 1 + i * 10)
        row.supplier_name = "供应商3"
        row.supplier_id = 3
        row.category_name = "分类1"
        row.standard_price = Decimal('160.00')
        data.append(row)
    
    return data


class TestPriceAnalyzer:
    """价格波动分析器测试类"""
    
    def test_get_price_fluctuation_data_all_materials(self, mock_db, sample_price_data):
        """测试获取所有物料价格波动数据"""
        # 设置mock查询
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_price_data
        mock_db.query.return_value = mock_query
        
        # 调用方法
        result = PriceAnalyzer.get_price_fluctuation_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证返回结果结构
        assert 'materials' in result
        assert 'summary' in result
        
        # 验证物料数量
        assert len(result['materials']) == 3
        
        # 验证汇总数据
        summary = result['summary']
        assert summary['total_materials'] == 3
        assert summary['high_volatility_count'] >= 0
        assert summary['avg_volatility'] >= 0
        
    def test_price_volatility_calculation(self, mock_db, sample_price_data):
        """测试价格波动率计算"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_price_data[:5]  # 物料A
        mock_db.query.return_value = mock_query
        
        result = PriceAnalyzer.get_price_fluctuation_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证物料A的价格统计
        material_a = result['materials'][0]
        assert material_a['material_code'] == "MAT-001"
        assert material_a['min_price'] == 95
        assert material_a['max_price'] == 130
        assert material_a['avg_price'] > 0
        assert material_a['price_volatility'] > 0
        
    def test_filter_by_material_code(self, mock_db, sample_price_data):
        """测试按物料编码筛选"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_price_data[:5]  # 只返回物料A
        mock_db.query.return_value = mock_query
        
        result = PriceAnalyzer.get_price_fluctuation_data(
            db=mock_db,
            material_code="MAT-001"
        )
        
        # 验证只有一个物料
        assert len(result['materials']) == 1
        assert result['materials'][0]['material_code'] == "MAT-001"
        
    def test_filter_by_category(self, mock_db, sample_price_data):
        """测试按分类筛选"""
        # 筛选分类1的物料（A和C）
        filtered_data = [d for d in sample_price_data if d.category_name == "分类1"]
        
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = filtered_data
        mock_db.query.return_value = mock_query
        
        result = PriceAnalyzer.get_price_fluctuation_data(
            db=mock_db,
            category_id=1
        )
        
        # 验证返回的物料都是分类1
        assert len(result['materials']) == 2
        for material in result['materials']:
            assert material['category_name'] == "分类1"
            
    def test_supplier_diversity(self, mock_db, sample_price_data):
        """测试供应商多样性统计"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_price_data[:5]  # 物料A有2个供应商
        mock_db.query.return_value = mock_query
        
        result = PriceAnalyzer.get_price_fluctuation_data(
            db=mock_db,
            material_code="MAT-001"
        )
        
        # 验证供应商数量
        material = result['materials'][0]
        assert len(material['suppliers']) == 2
        
    def test_empty_price_data(self, mock_db):
        """测试空数据情况"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        result = PriceAnalyzer.get_price_fluctuation_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证空数据处理
        assert len(result['materials']) == 0
        assert result['summary']['total_materials'] == 0
        assert result['summary']['avg_volatility'] == 0
