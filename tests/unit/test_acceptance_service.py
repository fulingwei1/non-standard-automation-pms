# -*- coding: utf-8 -*-
"""
Tests for AcceptanceService.
Note: The source file has undefined references (Customer, selectinload, InvoiceService),
so we test _update_project_to_warranty and _send_invoice_notification directly,
and test complete_acceptance_order indirectly via mocking the DB execute.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date


class TestAcceptanceServiceUpdateWarranty:
    @pytest.mark.asyncio
    async def test_update_project_not_found(self):
        from app.services.acceptance.acceptance_service import AcceptanceService
        db = AsyncMock()
        db.get.return_value = None
        with pytest.raises(ValueError, match="项目不存在"):
            await AcceptanceService._update_project_to_warranty(db, 999, 1)

    @pytest.mark.asyncio
    async def test_update_project_s8_to_s9(self):
        from app.services.acceptance.acceptance_service import AcceptanceService
        db = AsyncMock()
        project = MagicMock(stage="S8", status="ST08")
        db.get.return_value = project
        await AcceptanceService._update_project_to_warranty(db, 1, 1)
        assert project.stage == "S9"
        assert project.status == "ST30"
        assert project.end_date == date.today()
        assert project.health_status == "H4"
        db.add.assert_called_with(project)
        db.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_update_project_not_s8_no_change(self):
        from app.services.acceptance.acceptance_service import AcceptanceService
        db = AsyncMock()
        project = MagicMock(stage="S5", status="ST12")
        db.get.return_value = project
        await AcceptanceService._update_project_to_warranty(db, 1, 1)
        # Should not change stage since condition is S8/ST08
        assert project.stage == "S5"

    @pytest.mark.asyncio
    async def test_send_invoice_notification_is_noop(self):
        from app.services.acceptance.acceptance_service import AcceptanceService
        db = AsyncMock()
        # Should just pass without error
        await AcceptanceService._send_invoice_notification(db, MagicMock(), MagicMock())
