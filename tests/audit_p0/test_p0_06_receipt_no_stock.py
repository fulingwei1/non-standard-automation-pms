# -*- coding: utf-8 -*-
"""
P0-6: 收货 -> 库存断链。收货只回写 received_qty，从不入库。

purchase/receipts.py 全文无任何库存写入；inventory/inbound_service.py 的入库能力
零业务调用方（只在 facade/__init__ 里被 import/export，从不被收货流触发）。

正确行为：收货合格确认应触发库存入库（调用 InboundService / 写 MaterialStock /
增 current_stock）。修复前收货端点与入库服务无任何接线 -> 失败即证明断链。

采用源码接线断言（静态复现）：动态造 PO->收货->质检全链的前置成本极高，且即便
造出来也不会写库；核心缺陷在“收货代码根本不调入库”，源码接线检查更稳、更直指根因。
"""
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.audit_p0

RECEIPTS = "app/api/v1/endpoints/purchase/receipts.py"
INBOUND = "app/services/inventory/inbound_service.py"
# 任一入库接线信号
INBOUND_SIGNALS = [
    "InboundService",
    "receive_goods",
    "purchase_in",
    "MaterialStock",
    "current_stock",
    "InventoryManagementFacade",
]


def _read(repo_root, rel):
    return (repo_root / rel).read_text(encoding="utf-8")


def test_goods_receipt_triggers_inventory_inbound(repo_root):
    src = _read(repo_root, RECEIPTS)
    hits = [s for s in INBOUND_SIGNALS if s in src]
    assert hits, (
        f"{RECEIPTS} 全文无任何库存入库接线（未出现 {INBOUND_SIGNALS} 中任何一个），"
        f"收货合格后不入库 -> 齐套率/缺料/库存分析读到静态种子数。"
    )


def test_inbound_service_has_an_external_caller(repo_root):
    """入库服务应有真实调用方（收货/质检链）。当前只在 facade 内自引用，无收货侧调用。"""
    src_dir = repo_root / "app"
    callers = []
    for p in src_dir.rglob("*.py"):
        if p.name in ("inbound_service.py", "inventory_management_facade.py", "__init__.py"):
            continue
        if "__pycache__" in str(p):
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"\.receive_goods\(|\.purchase_in\(", txt):
            callers.append(str(p.relative_to(repo_root)))
    assert callers, (
        "InboundService.receive_goods/purchase_in 在 app/ 下无任何业务调用方 -> "
        "入库能力是死代码，收货永不入库。"
    )
