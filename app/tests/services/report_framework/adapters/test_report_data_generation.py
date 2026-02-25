# -*- coding: utf-8 -*-
"""
报表数据生成适配器测试
目标覆盖率: 60%+
测试用例数: 5个
"""
import pytest
from datetime import date
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.report_framework.adapters.report_data_generation import ReportDataGenerationAdapter


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return Mock(spec=Session)


@pytest.fixture
def adapter(mock_db):
    """创建适配器实例"""
    return ReportDataGenerationAdapter(db=mock_db, report_type="PROJECT_WEEKLY")


class TestReportDataGenerationAdapter:
    """报表数据生成适配器测试类"""
    
    def test_get_report_code(self, adapter):
        """测试获取报表代码"""
        # 测试已知报表类型
        assert adapter.get_report_code() == "PROJECT_WEEKLY"
        
        # 测试其他报表类型
        adapter2 = ReportDataGenerationAdapter(mock_db=Mock(), report_type="PROJECT_MONTHLY")
        assert adapter2.get_report_code() == "PROJECT_MONTHLY"
        
    def test_get_report_code_unknown_type(self, mock_db):
        """测试未知报表类型"""
        adapter = ReportDataGenerationAdapter(db=mock_db, report_type="UNKNOWN_TYPE")
        # 未知类型应该返回原样
        assert adapter.get_report_code() == "UNKNOWN_TYPE"
        
    @patch('app.services.report_framework.adapters.report_data_generation.ReportRouterMixin')
    def test_generate_data_project_weekly(self, mock_router, adapter):
        """测试生成项目周报数据"""
        # 设置mock
        mock_router.generate_report_by_type.return_value = {
            "project_id": 1,
            "start_date": "2024-01-01",
            "end_date": "2024-01-07",
            "summary": {
                "total_hours": 100,
                "completed_tasks": 10
            },
            "details": []
        }
        
        # 调用方法
        params = {
            "project_id": 1,
            "start_date": date(2024, 1, 1),
            "end_date": date(2024, 1, 7)
        }
        result = adapter.generate_data(params)
        
        # 验证结果
        assert "report_type" in result
        assert result["report_type"] == "PROJECT_WEEKLY"
        assert "title" in result
        assert result["title"] == "项目周报"
        assert "summary" in result
        
    @patch('app.services.report_framework.adapters.report_data_generation.ReportRouterMixin')
    def test_generate_data_with_default_dates(self, mock_router, adapter):
        """测试使用默认日期生成数据"""
        # 设置mock
        mock_router.generate_report_by_type.return_value = {
            "summary": {}
        }
        
        # 不传日期参数
        params = {
            "project_id": 1
        }
        adapter.generate_data(params)
        
        # 验证调用了默认日期
        mock_router.generate_report_by_type.assert_called_once()
        call_args = mock_router.generate_report_by_type.call_args
        assert call_args[1]['start_date'] is not None
        assert call_args[1]['end_date'] is not None
        
    @patch('app.services.report_framework.adapters.report_data_generation.ReportRouterMixin')
    def test_generate_data_with_error(self, mock_router, adapter):
        """测试生成数据时出错"""
        # 设置mock返回错误
        mock_router.generate_report_by_type.return_value = {
            "error": "数据生成失败"
        }
        
        # 调用方法应该抛出异常
        params = {
            "project_id": 1,
            "start_date": date(2024, 1, 1),
            "end_date": date(2024, 1, 7)
        }
        
        with pytest.raises(ValueError) as exc:
            adapter.generate_data(params)
        
        assert "数据生成失败" in str(exc.value)
        
    def test_report_type_mapping(self, mock_db):
        """测试报表类型映射"""
        # 测试所有支持的报表类型
        report_types = [
            "PROJECT_WEEKLY",
            "PROJECT_MONTHLY",
            "DEPT_WEEKLY",
            "DEPT_MONTHLY",
            "WORKLOAD_ANALYSIS",
            "COST_ANALYSIS",
        ]
        
        for report_type in report_types:
            adapter = ReportDataGenerationAdapter(db=mock_db, report_type=report_type)
            assert adapter.get_report_code() == report_type
