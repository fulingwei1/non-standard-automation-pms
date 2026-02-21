# -*- coding: utf-8 -*-
"""
质量合格率分析器测试
目标覆盖率: 60%+
测试用例数: 5个
"""
import pytest
from datetime import date
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.services.procurement_analysis.quality_analysis import QualityAnalyzer


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return Mock(spec=Session)


@pytest.fixture
def sample_quality_data():
    """创建示例质量数据"""
    data = []
    
    # 供应商1 - 高质量（98%+）
    materials_sup1 = [
        ("MAT-001", "物料A", 980, 20),
        ("MAT-002", "物料B", 1000, 0),
        ("MAT-003", "物料C", 950, 50),
    ]
    for mat_code, mat_name, qualified, rejected in materials_sup1:
        row = Mock()
        row.supplier_id = 1
        row.supplier_name = "优质供应商"
        row.material_code = mat_code
        row.material_name = mat_name
        row.total_qualified = qualified
        row.total_rejected = rejected
        row.total_inspected = qualified + rejected
        data.append(row)
    
    # 供应商2 - 中等质量（90-95%）
    materials_sup2 = [
        ("MAT-004", "物料D", 900, 100),
        ("MAT-005", "物料E", 920, 80),
    ]
    for mat_code, mat_name, qualified, rejected in materials_sup2:
        row = Mock()
        row.supplier_id = 2
        row.supplier_name = "普通供应商"
        row.material_code = mat_code
        row.material_name = mat_name
        row.total_qualified = qualified
        row.total_rejected = rejected
        row.total_inspected = qualified + rejected
        data.append(row)
    
    # 供应商3 - 低质量（<90%）
    materials_sup3 = [
        ("MAT-006", "物料F", 800, 200),
        ("MAT-007", "物料G", 850, 150),
    ]
    for mat_code, mat_name, qualified, rejected in materials_sup3:
        row = Mock()
        row.supplier_id = 3
        row.supplier_name = "问题供应商"
        row.material_code = mat_code
        row.material_name = mat_name
        row.total_qualified = qualified
        row.total_rejected = rejected
        row.total_inspected = qualified + rejected
        data.append(row)
    
    return data


class TestQualityAnalyzer:
    """质量合格率分析器测试类"""
    
    def test_get_quality_rate_data_all_suppliers(self, mock_db, sample_quality_data):
        """测试获取所有供应商质量数据"""
        # 设置mock查询
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = sample_quality_data
        mock_db.query.return_value = mock_query
        
        # 调用方法
        result = QualityAnalyzer.get_quality_rate_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证返回结果结构
        assert 'supplier_quality' in result
        assert 'summary' in result
        
        # 验证供应商数量
        assert len(result['supplier_quality']) == 3
        
        # 验证汇总数据
        summary = result['summary']
        assert summary['total_suppliers'] == 3
        assert summary['avg_pass_rate'] >= 0
        assert summary['high_quality_suppliers'] >= 0
        assert summary['low_quality_suppliers'] >= 0
        
    def test_high_quality_supplier(self, mock_db, sample_quality_data):
        """测试高质量供应商识别"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = sample_quality_data[:3]  # 供应商1
        mock_db.query.return_value = mock_query
        
        result = QualityAnalyzer.get_quality_rate_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证供应商1是高质量供应商
        supplier1 = result['supplier_quality'][0]
        assert supplier1['supplier_name'] == "优质供应商"
        assert supplier1['overall_pass_rate'] >= 98.0
        assert supplier1['material_count'] == 3
        
        # 验证物料明细
        for material in supplier1['materials']:
            assert 'material_code' in material
            assert 'qualified_qty' in material
            assert 'rejected_qty' in material
            assert 'pass_rate' in material
            
    def test_low_quality_supplier(self, mock_db, sample_quality_data):
        """测试低质量供应商识别"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = sample_quality_data[5:]  # 供应商3
        mock_db.query.return_value = mock_query
        
        result = QualityAnalyzer.get_quality_rate_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证供应商3是低质量供应商
        supplier3 = result['supplier_quality'][0]
        assert supplier3['supplier_name'] == "问题供应商"
        assert supplier3['overall_pass_rate'] < 90.0
        
    def test_filter_by_supplier(self, mock_db, sample_quality_data):
        """测试按供应商筛选"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = sample_quality_data[:3]  # 只返回供应商1
        mock_db.query.return_value = mock_query
        
        result = QualityAnalyzer.get_quality_rate_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            supplier_id=1
        )
        
        # 验证只有一个供应商
        assert len(result['supplier_quality']) == 1
        assert result['supplier_quality'][0]['supplier_id'] == 1
        
    def test_empty_quality_data(self, mock_db):
        """测试空数据情况"""
        mock_query = Mock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        result = QualityAnalyzer.get_quality_rate_data(
            db=mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证空数据处理
        assert len(result['supplier_quality']) == 0
        assert result['summary']['total_suppliers'] == 0
        assert result['summary']['avg_pass_rate'] == 0
        assert result['summary']['high_quality_suppliers'] == 0
        assert result['summary']['low_quality_suppliers'] == 0
