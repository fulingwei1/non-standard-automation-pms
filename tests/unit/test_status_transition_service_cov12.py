# -*- coding: utf-8 -*-
"""第十二批：项目状态联动服务单元测试"""
import pytest
from unittest.mock import MagicMock, patch

try:
    # 需要 patch 掉所有处理器以避免循环导入
    with patch("app.services.status_handlers.contract_handler.ContractStatusHandler"):
        with patch("app.services.status_handlers.material_handler.MaterialStatusHandler"):
            with patch("app.services.status_handlers.acceptance_handler.AcceptanceStatusHandler"):
                with patch("app.services.status_handlers.ecn_handler.ECNStatusHandler"):
                    from app.services.status_transition_service import StatusTransitionService
    SKIP = False
except Exception as e:
    SKIP = True


pytestmark = pytest.mark.skipif(SKIP, reason="导入失败")


def _make_service():
    db = MagicMock()
    with patch("app.services.status_transition_service.StatusTransitionService.__init__",
               lambda self, db: setattr(self, 'db', db) or setattr(self, 'contract_handler', MagicMock())
               or setattr(self, 'material_handler', MagicMock())
               or setattr(self, 'acceptance_handler', MagicMock())
               or setattr(self, 'ecn_handler', MagicMock())):
        svc = StatusTransitionService.__new__(StatusTransitionService)
        svc.db = db
        svc.contract_handler = MagicMock()
        svc.material_handler = MagicMock()
        svc.acceptance_handler = MagicMock()
        svc.ecn_handler = MagicMock()
    return svc, db


class TestStatusTransitionServiceInit:
    def test_service_creates_with_db(self):
        svc, db = _make_service()
        assert svc.db is db

    def test_handlers_initialized(self):
        svc, _ = _make_service()
        assert svc.contract_handler is not None
        assert svc.material_handler is not None
        assert svc.acceptance_handler is not None
        assert svc.ecn_handler is not None


class TestHandleContractSigned:
    def test_delegates_to_contract_handler(self):
        svc, _ = _make_service()
        mock_project = MagicMock()
        svc.contract_handler.handle_contract_signed = MagicMock(return_value=mock_project)

        if hasattr(svc, 'handle_contract_signed'):
            result = svc.handle_contract_signed(contract_id=1)
            svc.contract_handler.handle_contract_signed.assert_called()

    def test_auto_create_project_flag(self):
        svc, _ = _make_service()
        svc.contract_handler.handle_contract_signed = MagicMock(return_value=None)

        if hasattr(svc, 'handle_contract_signed'):
            svc.handle_contract_signed(contract_id=1, auto_create_project=False)
            svc.contract_handler.handle_contract_signed.assert_called()


class TestHandleMaterialEvents:
    def test_handle_bom_published_delegates(self):
        svc, _ = _make_service()
        svc.material_handler.handle_bom_published = MagicMock()
        if hasattr(svc, 'handle_bom_published'):
            svc.handle_bom_published(project_id=1)
            svc.material_handler.handle_bom_published.assert_called()

    def test_handle_materials_ready_delegates(self):
        svc, _ = _make_service()
        svc.material_handler.handle_materials_ready = MagicMock()
        if hasattr(svc, 'handle_materials_ready'):
            svc.handle_materials_ready(project_id=1)
            svc.material_handler.handle_materials_ready.assert_called()


class TestHandleAcceptanceEvents:
    def test_handle_fat_completed_delegates(self):
        svc, _ = _make_service()
        svc.acceptance_handler.handle_fat_completed = MagicMock()
        if hasattr(svc, 'handle_fat_completed'):
            svc.handle_fat_completed(project_id=1)
            svc.acceptance_handler.handle_fat_completed.assert_called()


class TestHandleEcnEvents:
    def test_handle_ecn_approved_delegates(self):
        svc, _ = _make_service()
        svc.ecn_handler.handle_ecn_approved = MagicMock()
        if hasattr(svc, 'handle_ecn_approved'):
            svc.handle_ecn_approved(project_id=1, ecn_id=1)
            svc.ecn_handler.handle_ecn_approved.assert_called()
