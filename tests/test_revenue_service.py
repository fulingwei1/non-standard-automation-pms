# -*- coding: utf-8 -*-
"""
营业收入服务测试
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestRevenueService:
    """营业收入服务测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return MagicMock()

    def test_get_project_revenue_contract(self, mock_db):
        """测试获取合同金额"""
        from app.services.revenue_service import RevenueService
        
        # Mock项目
        mock_project = MagicMock()
        mock_project.contract_amount = 100000
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        result = RevenueService.get_project_revenue(mock_db, 1, "CONTRACT")
        
        assert result == Decimal("100000")

    def test_get_project_revenue_no_project(self, mock_db):
        """测试项目不存在时返回0"""
        from app.services.revenue_service import RevenueService
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = RevenueService.get_project_revenue(mock_db, 999, "CONTRACT")
        
        assert result == Decimal("0")

    def test_get_project_revenue_invoiced(self, mock_db):
        """测试获取已开票金额"""
        from app.services.revenue_service import RevenueService
        
        mock_project = MagicMock()
        mock_project.contract_amount = 100000
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # Mock发票
        mock_invoice = MagicMock()
        mock_invoice.amount = Decimal("50000")
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_invoice]
        
        result = RevenueService.get_project_revenue(mock_db, 1, "INVOICED")
        
        assert result == Decimal("50000")

    def test_get_project_revenue_received(self, mock_db):
        """测试获取已收款金额"""
        from app.services.revenue_service import RevenueService
        
        mock_project = MagicMock()
        mock_project.contract_amount = 100000
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # Mock发票（已支付）
        mock_invoice = MagicMock()
        mock_invoice.paid_amount = Decimal("30000")
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_invoice]
        
        result = RevenueService.get_project_revenue(mock_db, 1, "RECEIVED")
        
        assert result == Decimal("30000")


class TestRevenueAggregation:
    """营业收入聚合测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return MagicMock()

    def test_get_total_revenue_by_customer(self, mock_db):
        """测试按客户汇总营业收入"""
        from app.services.revenue_service import RevenueService
        
        # Mock项目
        mock_projects = []
        for i in range(3):
            proj = MagicMock()
            proj.id = i + 1
            proj.contract_amount = 10000 * (i + 1)
            mock_projects.append(proj)
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_projects
        
        result = RevenueService.get_total_revenue_by_customer(mock_db, 1)
        
        assert result == Decimal("60000")

    def test_get_revenue_by_period(self, mock_db):
        """测试按时间段获取营收"""
        from app.services.revenue_service import RevenueService
        from datetime import date
        
        mock_projects = []
        for i in range(2):
            proj = MagicMock()
            proj.id = i + 1
            proj.contract_amount = 50000
            proj.sign_date = date(2026, 1, 1)
            mock_projects.append(proj)
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_projects
        
        result = RevenueService.get_revenue_by_period(
            mock_db, 
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31)
        )
        
        assert result == Decimal("100000")