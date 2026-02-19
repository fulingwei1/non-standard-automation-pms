# -*- coding: utf-8 -*-
"""
第三十三批覆盖率测试 - 验收服务 (AcceptanceService)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

try:
    from app.services.acceptance.acceptance_service import AcceptanceService
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="acceptance_service 导入失败")


class TestCompleteAcceptanceOrder:
    """测试 AcceptanceService.complete_acceptance_order"""

    @pytest.mark.asyncio
    async def test_order_not_found_raises(self):
        """验收单不存在时抛出 ValueError"""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match="验收单不存在"):
            await AcceptanceService.complete_acceptance_order(db, order_id=999, completed_by=1)

    @pytest.mark.asyncio
    async def test_wrong_status_raises(self):
        """验收单状态非PASSED时抛出 ValueError"""
        db = AsyncMock()

        mock_order = MagicMock()
        mock_order.status = "DRAFT"

        mock_result = MagicMock()
        mock_result.first.return_value = (mock_order, MagicMock(), MagicMock(), MagicMock())
        db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match="状态不是PASSED"):
            await AcceptanceService.complete_acceptance_order(db, order_id=1, completed_by=1)

    @pytest.mark.asyncio
    async def test_open_issues_returns_failure(self):
        """存在未解决验收问题时返回 success=False"""
        db = AsyncMock()

        mock_order = MagicMock()
        mock_order.status = "PASSED"

        order_result = MagicMock()
        order_result.first.return_value = (mock_order, MagicMock(), MagicMock(), MagicMock())

        issue1 = MagicMock()
        issues_result = MagicMock()
        issues_result.scalars.return_value.all.return_value = [issue1, issue1]

        db.execute = AsyncMock(side_effect=[order_result, issues_result])

        result = await AcceptanceService.complete_acceptance_order(db, order_id=1, completed_by=1)

        assert result["success"] is False
        assert result["open_issues_count"] == 2

    @pytest.mark.asyncio
    async def test_success_creates_invoice(self):
        """无问题时成功创建发票并返回 success=True"""
        db = AsyncMock()

        mock_order = MagicMock()
        mock_order.status = "PASSED"
        mock_order.acceptance_type = "FAT"
        mock_order.project_id = 10
        mock_order.customer_id = 5
        mock_order.contract_id = 3
        mock_order.total_amount = 100000
        mock_order.id = 1

        mock_project = MagicMock()
        mock_project.code = "PJ250101001"

        order_result = MagicMock()
        order_result.first.return_value = (mock_order, MagicMock(), mock_project, MagicMock())

        issues_result = MagicMock()
        issues_result.scalars.return_value.all.return_value = []

        db.execute = AsyncMock(side_effect=[order_result, issues_result])

        with patch(
            "app.services.acceptance.acceptance_service.InvoiceService.generate_code",
            new=AsyncMock(return_value="INV-2026-001")
        ):
            result = await AcceptanceService.complete_acceptance_order(
                db, order_id=1, completed_by=2, completion_notes="顺利完成"
            )

        assert result["success"] is True
        assert result["invoice_code"] == "INV-2026-001"
        assert result["project_code"] == "PJ250101001"

    @pytest.mark.asyncio
    async def test_sat_acceptance_triggers_warranty_update(self):
        """SAT验收类型完成后触发项目质保阶段更新"""
        db = AsyncMock()

        mock_order = MagicMock()
        mock_order.status = "PASSED"
        mock_order.acceptance_type = "SAT"
        mock_order.project_id = 10
        mock_order.customer_id = 5
        mock_order.contract_id = 3
        mock_order.total_amount = 50000
        mock_order.id = 1

        mock_project = MagicMock()
        mock_project.code = "PJ001"

        order_result = MagicMock()
        order_result.first.return_value = (mock_order, MagicMock(), mock_project, MagicMock())

        issues_result = MagicMock()
        issues_result.scalars.return_value.all.return_value = []

        db.execute = AsyncMock(side_effect=[order_result, issues_result])

        with patch(
            "app.services.acceptance.acceptance_service.InvoiceService.generate_code",
            new=AsyncMock(return_value="INV-001")
        ), patch.object(
            AcceptanceService,
            "_update_project_to_warranty",
            new=AsyncMock()
        ) as mock_warranty:
            result = await AcceptanceService.complete_acceptance_order(db, order_id=1, completed_by=2)

        assert result["success"] is True
        mock_warranty.assert_called_once()


class TestUpdateProjectToWarranty:
    """测试 AcceptanceService._update_project_to_warranty"""

    @pytest.mark.asyncio
    async def test_project_not_found_raises(self):
        """项目不存在时抛出 ValueError"""
        db = AsyncMock()
        db.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="项目不存在"):
            await AcceptanceService._update_project_to_warranty(db, project_id=999, completed_by=1)

    @pytest.mark.asyncio
    async def test_stage_s8_updates_to_s9(self):
        """S8阶段项目更新到S9质保阶段"""
        db = AsyncMock()

        mock_project = MagicMock()
        mock_project.stage = "S8"
        mock_project.status = "ST08"

        db.get = AsyncMock(return_value=mock_project)

        await AcceptanceService._update_project_to_warranty(db, project_id=1, completed_by=2)

        assert mock_project.stage == "S9"
        assert mock_project.status == "ST30"
        assert mock_project.health_status == "H4"
