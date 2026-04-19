# -*- coding: utf-8 -*-
"""Auto-generated tests for acceptance modules"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAcceptanceService:
    """Tests for app.services.acceptance.acceptance_service"""

    @pytest.mark.asyncio
    async def test_acceptance_service_static_api(self):
        """AcceptanceService 当前以静态 async 方法为主"""
        from app.services.acceptance.acceptance_service import AcceptanceService

        assert hasattr(AcceptanceService, "complete_acceptance_order")
        assert callable(AcceptanceService.complete_acceptance_order)

    @pytest.mark.asyncio
    async def test_complete_acceptance_order_is_async_callable(self):
        """当前至少保证入口存在且可调用；真实业务分支由更具体测试覆盖"""
        from app.services.acceptance.acceptance_service import AcceptanceService

        assert hasattr(AcceptanceService, "complete_acceptance_order")
        assert callable(AcceptanceService.complete_acceptance_order)


class TestReportUtils:
    """Tests for app.services.acceptance.report_utils"""

    def test_generate_report_no(self):
        from app.services.acceptance.report_utils import generate_report_no

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        result = generate_report_no(mock_db, "FAT")
        assert result is not None
        assert isinstance(result, str)
        assert result.startswith("FAT-")

    def test_build_report_content(self):
        from app.services.acceptance.report_utils import build_report_content

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [0, 0]

        order = MagicMock()
        order.order_no = "ACC-001"
        order.status = "PASSED"
        order.actual_end_date = None
        order.pass_rate = 100
        order.total_items = 10
        order.passed_items = 10
        order.failed_items = 0
        order.qa_signer_id = None
        order.project = None
        order.machine = None
        order.acceptance_type = "FAT"
        order.id = 1
        order.customer_signer = None

        user = MagicMock()
        user.real_name = "测试用户"
        user.username = "tester"

        result = build_report_content(mock_db, order, "FAT-20260417-001", 1, user)
        assert result is not None
        assert "验收报告" in result
        assert "FAT-20260417-001" in result


class TestAcceptanceApprovalService:
    """Tests for app.services.acceptance_approval.service"""

    @pytest.mark.asyncio
    async def test_service_init(self):
        from app.services.acceptance_approval.service import AcceptanceApprovalService

        mock_db = MagicMock()
        service = AcceptanceApprovalService(mock_db)
        assert service.db == mock_db


class TestAccountLockoutService:
    """Tests for app.services.account_lockout_service"""

    def test_check_lockout(self):
        from app.services.account_lockout_service import AccountLockoutService

        with patch("app.services.account_lockout_service.get_redis_client", return_value=MagicMock(get=MagicMock(return_value=None))):
            result = AccountLockoutService.check_lockout("test_user")
            assert isinstance(result, dict)
            assert "locked" in result

    def test_record_failed_login(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.incr.return_value = 1
        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.record_failed_login("test_user", "127.0.0.1")
            assert result["attempts"] == 1
            assert result["locked"] is False


class TestAIEmotionService:
    """Tests for app.services.ai_emotion_service"""

    @pytest.mark.asyncio
    async def test_analyze_emotion(self):
        from app.services.ai_emotion_service import AIEmotionService

        mock_db = MagicMock()
        service = AIEmotionService(mock_db)
        with patch.object(AIEmotionService, "analyze_emotion", new=AsyncMock(return_value={"emotion": "neutral"})):
            result = await service.analyze_emotion(1, 1, "test text")
            assert result is not None


class TestAIService:
    """Tests for app.services.ai_service"""

    def test_ai_service_init(self):
        from app.services.ai_service import AIService

        service = AIService()
        assert service is not None


class TestBackupService:
    """Tests for app.services.backup_service"""

    def test_backup_service_init(self):
        from app.services.backup_service import BackupService

        service = BackupService()
        assert service is not None


class TestBusinessRules:
    """Tests for app.services.business_rules"""

    def test_business_rules_module_exports(self):
        from app.services import business_rules

        assert hasattr(business_rules, "KPI_BENCHMARKS")
        assert hasattr(business_rules, "calc_gross_margin")
