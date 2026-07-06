# -*- coding: utf-8 -*-
"""租户模块开通服务：闸门判定 + 开通/停用管理。

闸门语义由 settings.MODULE_GATING_MODE 控制（沿用 TENANT_ENFORCE_MODE 的
灰度切换模式）：
- "off"        ：闸门不生效，全部放行（回滚开关）。
- "grandfather"：默认值。缺行=视为已开通（存量租户零感知），只有显式
                 DISABLED 或已过期才拦截；新租户接入后逐步转 strict。
- "strict"     ：缺行=未开通即拦截，只认显式 ENABLED/TRIAL 且未过期。
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.tenant_module import TenantModule, TenantModuleStatus
from app.modules.registry import MODULES, get_module, iter_business_modules


class TenantModuleService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- 闸门判定 ----------

    def is_module_enabled(self, tenant_id: Optional[int], module_key: str) -> bool:
        mode = getattr(settings, "MODULE_GATING_MODE", "grandfather")
        if mode == "off":
            return True
        manifest = get_module(module_key)
        if manifest is None:
            # 未注册的 key 一律拒绝，防止拼写错误静默放行
            return False
        if manifest.always_on:
            return True
        if tenant_id is None:
            # 无租户上下文（系统级/超管流程）不做模块拦截
            return True
        row = (
            self.db.query(TenantModule)
            .filter(TenantModule.tenant_id == tenant_id, TenantModule.module_key == module_key)
            .first()
        )
        if row is None:
            return mode != "strict"
        if row.status == TenantModuleStatus.DISABLED.value:
            return False
        if row.expires_at is not None and row.expires_at < datetime.utcnow():
            return False
        return row.status in (TenantModuleStatus.ENABLED.value, TenantModuleStatus.TRIAL.value)

    def list_effective_modules(self, tenant_id: Optional[int]) -> List[dict]:
        """给前端菜单/开通管理用：每个业务模块的生效状态快照。"""
        rows = {}
        if tenant_id is not None:
            rows = {
                r.module_key: r
                for r in self.db.query(TenantModule).filter(TenantModule.tenant_id == tenant_id)
            }
        out = []
        for m in MODULES.values():
            row = rows.get(m.key)
            out.append(
                {
                    "key": m.key,
                    "name": m.name,
                    "always_on": m.always_on,
                    "depends_on": list(m.depends_on),
                    "enabled": self.is_module_enabled(tenant_id, m.key),
                    "status": getattr(row, "status", None),
                    "expires_at": getattr(row, "expires_at", None),
                }
            )
        return out

    # ---------- 开通管理（超管） ----------

    def set_module(
        self,
        tenant_id: int,
        module_key: str,
        status: str,
        expires_at: Optional[datetime] = None,
        operator_id: Optional[int] = None,
    ) -> TenantModule:
        manifest = get_module(module_key)
        if manifest is None:
            raise ValueError(f"未知模块: {module_key}")
        if manifest.always_on:
            raise ValueError(f"平台模块 {module_key} 不参与租户开通")
        if status not in {s.value for s in TenantModuleStatus}:
            raise ValueError(f"非法状态: {status}")

        if status in (TenantModuleStatus.ENABLED.value, TenantModuleStatus.TRIAL.value):
            missing = [
                dep for dep in manifest.depends_on if not self.is_module_enabled(tenant_id, dep)
            ]
            if missing:
                raise ValueError(f"依赖模块未开通: {', '.join(missing)}")
        if status == TenantModuleStatus.DISABLED.value:
            dependents = [
                m.key
                for m in iter_business_modules()
                if module_key in m.depends_on and self.is_module_enabled(tenant_id, m.key)
            ]
            if dependents:
                raise ValueError(f"以下模块依赖本模块，需先停用: {', '.join(dependents)}")

        row = (
            self.db.query(TenantModule)
            .filter(TenantModule.tenant_id == tenant_id, TenantModule.module_key == module_key)
            .first()
        )
        if row is None:
            row = TenantModule(tenant_id=tenant_id, module_key=module_key)
            self.db.add(row)
        row.status = status
        row.expires_at = expires_at
        row.enabled_by = operator_id
        self.db.commit()
        self.db.refresh(row)
        return row
