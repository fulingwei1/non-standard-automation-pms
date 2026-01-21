# -*- coding: utf-8 -*-
"""
测试验收报告生成服务 - 修正版
"""

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.services.acceptance_report_service import (
    generate_report_no,
    get_report_version,
)


# ===== Mock Classes =====

class MockAcceptanceReport:
    """Mock AcceptanceReport for testing"""
    def __init__(
        self,
        id: int,
        report_no: str,
        report_type: str,
        version: int
    ):
        self.id = id
        self.report_no = report_no
        self.report_type = report_type
        self.version = version


# ===== Tests for generate_report_no =====

class TestGenerateReportNo:
    """测试 generate_report_no 方法"""

    def test_generate_fat_report_no(self):
        """测试FAT报告编号生成（无历史记录）"""
        db_session = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.filter.return_value = mock_query

        result = generate_report_no(db_session, "FAT")

        assert result == "FAT-20250121-001"

    def test_generate_fat_report_no_with_history(self):
        """测试FAT报告编号生成（有2条历史记录）"""
        db_session = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 2
        mock_query.filter.return_value = mock_query

        result = generate_report_no(db_session, "FAT")

        assert result == "FAT-20250121-003"

    def test_generate_sat_report_no(self):
        """测试SAT报告编号生成（无历史记录）"""
        db_session = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.filter.return_value = mock_query

        result = generate_report_no(db_session, "SAT")

        assert result == "SAT-20250121-001"

    def test_generate_sat_report_no_with_history(self):
        """测试SAT报告编号生成（有5条历史记录）"""
        db_session = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 5
        mock_query.filter.return_value = mock_query

        result = generate_report_no(db_session, "SAT")

        assert result == "SAT-20250121-006"

    def test_generate_ar_report_no(self):
        """测试AR报告编号生成（无历史记录）"""
        db_session = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 10
        mock_query.filter.return_value = mock_query

        result = generate_report_no(db_session, "AR")

        assert result == "AR-20250121-011"

    def test_generate_ar_report_no_with_history(self):
        """测试AR报告编号生成（有11条历史记录）"""
        db_session = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 11
        mock_query.filter.return_value = mock_query

        result = generate_report_no(db_session, "AR")

        assert result == "AR-20250121-012"


# ===== Tests for get_report_version =====

class TestGetReportVersion:
    """测试 get_report_version 方法"""

    def test_get_version_first_fat_report(self):
        """测试首次FAT报告版本"""
        db_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None

        order_id = 1
        db_session.query.return_value = mock_query

        result = get_report_version(db_session, order_id, "FAT")

        assert result == 1

    def test_get_version_second_fat_report(self):
        """测试第二次FAT报告版本（version号递增）"""
        db_session = MagicMock()
        
        class MockReport:
            id: int = 1
            report_no: str = "FAT-20250121-001"
            report_type: str = "FAT"
            version: int = 1

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = MockReport()
        db_session.query.return_value = mock_query

        order_id = 2
        result = get_report_version(db_session, order_id, "FAT")

        assert result == 2

    def test_get_version_sat_report(self):
        """测试SAT报告版本"""
        db_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None

        order_id = 1
        db_session.query.return_value = mock_query

        result = get_report_version(db_session, order_id, "SAT")

        assert result == 1

    def test_get_version_first_ar_report(self):
        """测试首次AR报告版本"""
        db_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None

        order_id = 1
        db_session.query.return_value = mock_query

        result = get_report_version(db_session, order_id, "AR")

        assert result == 1
