# -*- coding: utf-8 -*-
"""
P0-12: BOM -> 生产工单断链，WorkOrderBom 中间表零业务读写。

models/production/work_order.py 无 bom_id/bom_version 任何字段；WorkOrderBom 全仓
仅在模型注册/导出中出现，无 crud/service/endpoint 业务读写。

正确行为：工单应携带 BOM 关联/快照；WorkOrderBom 应被业务代码读写。
静态复现（设计级断链）。
"""
import pytest

pytestmark = pytest.mark.audit_p0

BOM_FIELD_HINTS = ("bom_id", "bom_version", "bom_header_id", "bom_no", 'ForeignKey("boms')


def test_work_order_model_has_bom_linkage(repo_root):
    src = (repo_root / "app/models/production/work_order.py").read_text(encoding="utf-8")
    hits = [h for h in BOM_FIELD_HINTS if h in src]
    assert hits, (
        "WorkOrder 模型无任何 BOM 关联字段（bom_id/bom_version/...）—— "
        "工单纯手填，领料/齐套与 BOM 版本对不上，ECN 生效即漂移"
    )


def test_workorderbom_has_business_read_write(repo_root):
    app_dir = repo_root / "app"
    biz_hits = []
    for p in app_dir.rglob("*.py"):
        sp = str(p)
        if "__pycache__" in sp:
            continue
        # 跳过模型定义/注册/导出文件，只找真正的业务读写
        if "/models/" in sp:
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if "WorkOrderBom" in txt:
            biz_hits.append(str(p.relative_to(repo_root)))
    assert biz_hits, (
        "WorkOrderBom 在 app/（models 之外）无任何业务读写引用 —— 中间表建了没接线"
    )
