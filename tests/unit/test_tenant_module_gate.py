# -*- coding: utf-8 -*-
"""P1 立规：租户模块开通闸门（tenant_modules）行为测试。"""

import shutil
import subprocess
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.tenant import Tenant
from app.models.tenant_module import TenantModule, TenantModuleStatus
from app.services.tenant_module_service import TenantModuleService


@pytest.fixture
def tenant(db_session: Session) -> Tenant:
    t = Tenant(tenant_code=f"T-{uuid.uuid4().hex[:8]}", tenant_name="闸门测试租户", status="ACTIVE")
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t


class TestGatingModes:
    def test_grandfather_missing_row_is_enabled(self, db_session, tenant, monkeypatch):
        monkeypatch.setattr(settings, "MODULE_GATING_MODE", "grandfather")
        svc = TenantModuleService(db_session)
        assert svc.is_module_enabled(tenant.id, "presale") is True

    def test_strict_missing_row_is_disabled(self, db_session, tenant, monkeypatch):
        monkeypatch.setattr(settings, "MODULE_GATING_MODE", "strict")
        svc = TenantModuleService(db_session)
        assert svc.is_module_enabled(tenant.id, "presale") is False

    def test_off_mode_allows_everything(self, db_session, tenant, monkeypatch):
        monkeypatch.setattr(settings, "MODULE_GATING_MODE", "off")
        svc = TenantModuleService(db_session)
        db_session.add(TenantModule(tenant_id=tenant.id, module_key="presale", status="DISABLED"))
        db_session.commit()
        assert svc.is_module_enabled(tenant.id, "presale") is True

    def test_explicit_disabled_blocks_in_grandfather(self, db_session, tenant, monkeypatch):
        monkeypatch.setattr(settings, "MODULE_GATING_MODE", "grandfather")
        db_session.add(TenantModule(tenant_id=tenant.id, module_key="presale", status="DISABLED"))
        db_session.commit()
        assert TenantModuleService(db_session).is_module_enabled(tenant.id, "presale") is False

    def test_expired_trial_blocks(self, db_session, tenant, monkeypatch):
        monkeypatch.setattr(settings, "MODULE_GATING_MODE", "grandfather")
        db_session.add(
            TenantModule(
                tenant_id=tenant.id,
                module_key="presale",
                status=TenantModuleStatus.TRIAL.value,
                expires_at=datetime.utcnow() - timedelta(days=1),
            )
        )
        db_session.commit()
        assert TenantModuleService(db_session).is_module_enabled(tenant.id, "presale") is False

    def test_platform_module_always_on_even_strict(self, db_session, tenant, monkeypatch):
        monkeypatch.setattr(settings, "MODULE_GATING_MODE", "strict")
        assert TenantModuleService(db_session).is_module_enabled(tenant.id, "platform-auth") is True

    def test_unknown_module_key_rejected(self, db_session, tenant, monkeypatch):
        monkeypatch.setattr(settings, "MODULE_GATING_MODE", "grandfather")
        assert TenantModuleService(db_session).is_module_enabled(tenant.id, "no-such-module") is False

    def test_no_tenant_context_allows(self, db_session, monkeypatch):
        monkeypatch.setattr(settings, "MODULE_GATING_MODE", "strict")
        assert TenantModuleService(db_session).is_module_enabled(None, "presale") is True


class TestSetModule:
    def test_enable_requires_dependencies_in_strict(self, db_session, tenant, monkeypatch):
        monkeypatch.setattr(settings, "MODULE_GATING_MODE", "strict")
        svc = TenantModuleService(db_session)
        # presale 依赖 sales：strict 下 sales 缺行=未开通，应拒绝
        with pytest.raises(ValueError, match="依赖模块未开通"):
            svc.set_module(tenant.id, "presale", "ENABLED")
        svc.set_module(tenant.id, "sales", "ENABLED")
        row = svc.set_module(tenant.id, "presale", "ENABLED")
        assert row.status == "ENABLED"

    def test_disable_blocked_by_dependents(self, db_session, tenant, monkeypatch):
        monkeypatch.setattr(settings, "MODULE_GATING_MODE", "strict")
        svc = TenantModuleService(db_session)
        svc.set_module(tenant.id, "sales", "ENABLED")
        svc.set_module(tenant.id, "presale", "ENABLED")
        with pytest.raises(ValueError, match="依赖本模块"):
            svc.set_module(tenant.id, "sales", "DISABLED")
        svc.set_module(tenant.id, "presale", "DISABLED")
        row = svc.set_module(tenant.id, "sales", "DISABLED")
        assert row.status == "DISABLED"

    def test_platform_module_not_manageable(self, db_session, tenant):
        with pytest.raises(ValueError, match="平台模块"):
            TenantModuleService(db_session).set_module(tenant.id, "platform-auth", "DISABLED")

    def test_list_effective_modules_snapshot(self, db_session, tenant, monkeypatch):
        monkeypatch.setattr(settings, "MODULE_GATING_MODE", "grandfather")
        svc = TenantModuleService(db_session)
        svc.set_module(tenant.id, "production", "DISABLED")
        snapshot = {m["key"]: m for m in svc.list_effective_modules(tenant.id)}
        assert snapshot["production"]["enabled"] is False
        assert snapshot["sales"]["enabled"] is True  # grandfather 缺行=开
        assert snapshot["platform-auth"]["always_on"] is True


class TestImportBoundaries:
    def test_import_linter_contracts_kept(self):
        """边界合同必须保持 KEPT；新增跨层 import 会让本测试失败。"""
        exe = shutil.which("lint-imports") or ".venv/bin/lint-imports"
        try:
            result = subprocess.run([exe], capture_output=True, text=True, timeout=300)
        except FileNotFoundError:
            pytest.skip("import-linter 未安装（requirements-dev.txt）")
        assert "0 broken" in result.stdout, result.stdout[-2000:]
