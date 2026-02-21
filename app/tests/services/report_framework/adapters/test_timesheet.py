# -*- coding: utf-8 -*-
"""
工时报表适配器测试
目标覆盖率: 60%+
测试用例数: 3个
"""
import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.services.report_framework.adapters.timesheet import TimesheetReportAdapter


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return Mock(spec=Session)


@pytest.fixture
def adapter(mock_db):
    """创建适配器实例"""
    return TimesheetReportAdapter(db=mock_db)


class TestTimesheetReportAdapter:
    """工时报表适配器测试类"""
    
    def test_get_report_code(self, adapter):
        """测试获取报表代码"""
        assert adapter.get_report_code() == "TIMESHEET_WEEKLY"
        
    def test_generate_data_basic(self, adapter):
        """测试生成基本工时数据"""
        params = {
            "user_id": 1,
            "start_date": "2024-01-01",
            "end_date": "2024-01-07"
        }
        
        result = adapter.generate_data(params)
        
        # 验证返回基本结构
        assert "title" in result
        assert result["title"] == "工时报表"
        assert "summary" in result
        assert "details" in result
        
    def test_generate_data_with_user(self, adapter):
        """测试带用户信息的数据生成"""
        from app.models.user import User
        
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.username = "test_user"
        
        params = {
            "user_id": 1,
            "start_date": "2024-01-01",
            "end_date": "2024-01-07"
        }
        
        result = adapter.generate_data(params, user=mock_user)
        
        # 验证返回结果
        assert result is not None
        assert isinstance(result, dict)
