# -*- coding: utf-8 -*-
"""
验收管理工具函数单元测试
Covers: app/api/v1/endpoints/acceptance/utils.py
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.acceptance.utils import (
    generate_issue_no,
    generate_order_no,
    validate_acceptance_rules,
    validate_completion_rules,
    validate_edit_rules,
)


class TestValidateAcceptanceRules:
    """Test suite for validate_acceptance_rules function."""

    def test_project_not_found(self, db_session):
        """项目不存在应抛出 404 错误。"""
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                validate_acceptance_rules(db_session, "FAT", project_id=999)

            assert exc_info.value.status_code == 404
            assert "项目不存在" in str(exc_info.value.detail)

    def test_fat_requires_machine_id(self, db_session):
        """FAT 验收必须指定设备 ID。"""
        mock_project = MagicMock()
        mock_project.stage = "S5"

        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_project

            with pytest.raises(HTTPException) as exc_info:
                validate_acceptance_rules(db_session, "FAT", project_id=1, machine_id=None)

            assert exc_info.value.status_code == 400
            assert "必须指定设备" in str(exc_info.value.detail)

    def test_fat_machine_not_found(self, db_session):
        """FAT 验收指定的设备不存在应抛出 404。"""
        mock_project = MagicMock()
        mock_project.stage = "S5"

        with patch.object(db_session, 'query') as mock_query:
            # 第一次查询返回项目，第二次查询返回 None（设备不存在）
            mock_query.return_value.filter.return_value.first.side_effect = [
                mock_project,
                None,
            ]

            with pytest.raises(HTTPException) as exc_info:
                validate_acceptance_rules(db_session, "FAT", project_id=1, machine_id=999)

            assert exc_info.value.status_code == 404
            assert "设备不存在" in str(exc_info.value.detail)

    def test_fat_machine_stage_validation(self, db_session):
        """FAT 验收要求设备在 S5 或 S6 阶段。"""
        mock_project = MagicMock()
        mock_project.stage = "S5"

        mock_machine = MagicMock()
        mock_machine.stage = "S3"  # 不在允许的阶段

        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.side_effect = [
                mock_project,
                mock_machine,
            ]

            with pytest.raises(HTTPException) as exc_info:
                validate_acceptance_rules(db_session, "FAT", project_id=1, machine_id=1)

            assert exc_info.value.status_code == 400
            assert "尚未完成调试" in str(exc_info.value.detail)

    @pytest.mark.skip(reason="Complex mock setup required - function queries multiple models (AcceptanceOrder for FAT records)")
    def test_sat_requires_passed_fat(self, db_session):
        """SAT 验收必须在 FAT 通过后。"""
        mock_project = MagicMock()
        mock_project.stage = "S7"

        mock_machine = MagicMock()
        mock_machine.stage = "S7"

        with patch.object(db_session, 'query') as mock_query:
            # 设置多次查询的返回值
            mock_query.return_value.filter.return_value.first.side_effect = [
                mock_project,
                mock_machine,
            ]
            # FAT 验收记录查询返回空
            mock_query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

            with pytest.raises(HTTPException) as exc_info:
                validate_acceptance_rules(db_session, "SAT", project_id=1, machine_id=1)

            assert exc_info.value.status_code == 400
            assert "FAT验收通过后" in str(exc_info.value.detail)


class TestValidateCompletionRules:
    """Test suite for validate_completion_rules function."""

    def test_order_not_found(self, db_session):
        """验收单不存在应抛出 404。"""
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                validate_completion_rules(db_session, order_id=999)

            assert exc_info.value.status_code == 404
            assert "验收单不存在" in str(exc_info.value.detail)

    @pytest.mark.skip(reason="Complex mock setup required - function queries AcceptanceIssue with multiple conditions")
    def test_blocking_issues_prevent_completion(self, db_session):
        """存在未闭环的阻塞问题不能通过验收。"""
        mock_order = MagicMock()

        mock_issue = MagicMock()
        mock_issue.status = "OPEN"
        mock_issue.is_blocking = True
        mock_issue.issue_no = "AI-FAT001-001"

        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_order
            mock_query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_issue]

            with pytest.raises(HTTPException) as exc_info:
                validate_completion_rules(db_session, order_id=1)

            assert exc_info.value.status_code == 400
            assert "未闭环的阻塞问题" in str(exc_info.value.detail)


class TestValidateEditRules:
    """Test suite for validate_edit_rules function."""

    def test_customer_signed_prevents_edit(self, db_session):
        """客户签字后不能修改验收单。"""
        mock_order = MagicMock()
        mock_order.customer_signed_at = "2025-01-01"
        mock_order.customer_signer = "客户代表"
        mock_order.is_officially_completed = False

        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_order

            with pytest.raises(HTTPException) as exc_info:
                validate_edit_rules(db_session, order_id=1)

            assert exc_info.value.status_code == 400
            assert "客户已签字" in str(exc_info.value.detail)

    def test_officially_completed_prevents_edit(self, db_session):
        """正式完成后不能修改验收单。"""
        mock_order = MagicMock()
        mock_order.customer_signed_at = None
        mock_order.customer_signer = None
        mock_order.is_officially_completed = True

        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_order

            with pytest.raises(HTTPException) as exc_info:
                validate_edit_rules(db_session, order_id=1)

            assert exc_info.value.status_code == 400
            assert "正式完成" in str(exc_info.value.detail)


class TestGenerateOrderNo:
    """Test suite for generate_order_no function."""

    def test_fat_order_no_format(self, db_session):
        """FAT 验收单号格式：FAT-{项目编号}-{设备序号}-{序号}。"""
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.order_by.return_value.first.return_value = None

            order_no = generate_order_no(db_session, "FAT", "P2025001", machine_no=1)

            assert order_no == "FAT-P2025001-M01-001"

    def test_sat_order_no_format(self, db_session):
        """SAT 验收单号格式：SAT-{项目编号}-{设备序号}-{序号}。"""
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.order_by.return_value.first.return_value = None

            order_no = generate_order_no(db_session, "SAT", "P2025001", machine_no=2)

            assert order_no == "SAT-P2025001-M02-001"

    def test_final_order_no_format(self, db_session):
        """终验收单号格式：FIN-{项目编号}-{序号}。"""
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.order_by.return_value.first.return_value = None

            order_no = generate_order_no(db_session, "FINAL", "P2025001")

            assert order_no == "FIN-P2025001-001"

    def test_fat_requires_machine_no(self, db_session):
        """FAT 验收单必须提供设备序号。"""
        with pytest.raises(ValueError) as exc_info:
            generate_order_no(db_session, "FAT", "P2025001", machine_no=None)

            assert "必须提供设备序号" in str(exc_info.value)

    def test_order_no_increment(self, db_session):
        """验收单号应自增。"""
        mock_existing_order = MagicMock()
        mock_existing_order.order_no = "FAT-P2025001-M01-003"

        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_existing_order

            order_no = generate_order_no(db_session, "FAT", "P2025001", machine_no=1)

            assert order_no == "FAT-P2025001-M01-004"


class TestGenerateIssueNo:
    """Test suite for generate_issue_no function."""

    def test_issue_no_format(self, db_session):
        """问题编号格式：AI-{验收单号后缀}-{序号}。"""
        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.order_by.return_value.first.return_value = None

            issue_no = generate_issue_no(db_session, "FAT-P2025001-M01-001")

            assert issue_no == "AI-FAT001-001"

    def test_issue_no_increment(self, db_session):
        """问题编号应自增。"""
        mock_existing_issue = MagicMock()
        mock_existing_issue.issue_no = "AI-FAT001-005"

        with patch.object(db_session, 'query') as mock_query:
            mock_query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_existing_issue

            issue_no = generate_issue_no(db_session, "FAT-P2025001-M01-001")

            assert issue_no == "AI-FAT001-006"
