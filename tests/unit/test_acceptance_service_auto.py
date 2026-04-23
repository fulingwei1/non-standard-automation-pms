# -*- coding: utf-8 -*-
"""Lightweight smoke tests for acceptance modules."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


pytestmark = pytest.mark.unit


class TestAcceptanceServiceSmoke:
    @pytest.mark.asyncio
    async def test_update_project_to_warranty_missing_project(self):
        from app.services.acceptance.acceptance_service import AcceptanceService

        db = AsyncMock()
        db.add = MagicMock()
        db.get.return_value = None

        with pytest.raises(ValueError, match="项目不存在"):
            await AcceptanceService._update_project_to_warranty(db, 999, 1)

    def test_acceptance_service_class_exists(self):
        from app.services.acceptance.acceptance_service import AcceptanceService

        assert AcceptanceService is not None


class TestReportUtilsSmoke:
    def test_generate_report_no_signature_current(self, monkeypatch: pytest.MonkeyPatch):
        from app.services.acceptance import report_utils

        count_query = MagicMock()
        count_query.scalar.return_value = 0
        monkeypatch.setattr(report_utils, "apply_like_filter", lambda *args, **kwargs: count_query)

        db = MagicMock()
        result = report_utils.generate_report_no(db, "FAT")

        assert result.startswith("FAT-")
        assert result.endswith("-001")

    def test_build_report_content_signature_current(self):
        from app.services.acceptance import report_utils

        db = MagicMock()
        total_query = MagicMock()
        total_query.filter.return_value.scalar.return_value = 0
        resolved_query = MagicMock()
        resolved_query.filter.return_value.scalar.return_value = 0
        db.query.side_effect = [total_query, resolved_query]

        order = SimpleNamespace(
            id=1,
            order_no="AO-001",
            acceptance_type="FAT",
            status="COMPLETED",
            actual_end_date=None,
            pass_rate=100,
            total_items=1,
            passed_items=1,
            failed_items=0,
            qa_signer_id=None,
            customer_signer="客户",
            project=None,
            machine=None,
        )
        user = SimpleNamespace(real_name="测试用户", username="tester")

        result = report_utils.build_report_content(db, order, "FAT-001", 1, user)

        assert "验收报告" in result
        assert "FAT-001" in result
        assert "生成人：测试用户" in result
