# -*- coding: utf-8 -*-
"""
BOM 成本检查清单测试（对应手册 Sheet3）

验证：
- 12 项检查结构
- 无 BOM 时的提示
- 历史比价自动判定（偏差>15% → auto_failed）
- 同类项目对比自动判定
- 10 项 manual checklist
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.models.material import BomHeader, BomItem
from app.models.project import Project


def _make_project(db, code="BOMCHECK-001", category="ICT测试", **kw):
    defaults = dict(
        project_code=code,
        project_name=f"BOM检查 {code}",
        stage="S3",
        status="ST01",
        health="H1",
        progress_pct=30,
        is_active=True,
        contract_amount=Decimal("100000"),
        product_category=category,
        planned_start_date=date.today() - timedelta(days=90),
        planned_end_date=date.today() + timedelta(days=30),
    )
    defaults.update(kw)
    p = Project(**defaults)
    db.add(p)
    db.flush()
    return p


def _make_bom(db, project_id, total=50000, items=None):
    bom = BomHeader(
        bom_no=f"BOM-{project_id}-001",
        bom_name=f"BOM-{project_id}",
        project_id=project_id,
        version="1.0",
        status="APPROVED",
        total_amount=Decimal(str(total)),
    )
    db.add(bom)
    db.flush()
    if items:
        for i, it in enumerate(items, 1):
            db.add(
                BomItem(
                    bom_id=bom.id,
                    item_no=i,
                    material_code=it["code"],
                    material_name=it.get("name", it["code"]),
                    quantity=Decimal(str(it.get("qty", 1))),
                    unit_price=Decimal(str(it["price"])),
                    amount=Decimal(str(it.get("qty", 1) * it["price"])),
                )
            )
    db.flush()
    return bom


class TestBomCostCheck:
    def test_no_bom_returns_hint(self, db_session):
        """无 BOM 时返回提示，不崩。"""
        from app.services.dashboard.bom_cost_check_service import BomCostCheckService

        project = _make_project(db_session, "BOMCHECK-NOBOM")
        result = BomCostCheckService(db_session).get_check(project.id)
        assert result["has_bom"] is False
        assert "请先创建" in result["message"]

    def test_check_returns_12_items(self, db_session):
        """有 BOM 时返回 12 项检查。"""
        from app.services.dashboard.bom_cost_check_service import BomCostCheckService

        project = _make_project(db_session, "BOMCHECK-12")
        _make_bom(db_session, project.id, items=[{"code": "M001", "price": 100}])
        result = BomCostCheckService(db_session).get_check(project.id)
        assert result["has_bom"] is True
        assert len(result["items"]) == 12

    def test_manual_items_present(self, db_session):
        """10 项 manual 检查项存在。"""
        from app.services.dashboard.bom_cost_check_service import BomCostCheckService

        project = _make_project(db_session, "BOMCHECK-MANUAL")
        _make_bom(db_session, project.id, items=[{"code": "M001", "price": 100}])
        result = BomCostCheckService(db_session).get_check(project.id)
        manual = [i for i in result["items"] if not i.get("auto")]
        assert len(manual) == 10
        for m in manual:
            assert m["status"] == "manual"

    def test_historical_price_deviation(self, db_session):
        """历史比价：同物料单价偏差>15% → auto_failed。"""
        from app.services.dashboard.bom_cost_check_service import BomCostCheckService

        # 项目A：某物料 100 元
        proj_a = _make_project(db_session, "BOMCHECK-HP-A")
        _make_bom(
            db_session,
            proj_a.id,
            items=[{"code": "SHARE-MAT", "price": 100}],
        )

        # 项目B：同物料 130 元（偏差 30%，>15%）
        proj_b = _make_project(db_session, "BOMCHECK-HP-B")
        _make_bom(
            db_session,
            proj_b.id,
            items=[{"code": "SHARE-MAT", "price": 130}],
        )

        result = BomCostCheckService(db_session).get_check(proj_b.id)
        item5 = next(i for i in result["items"] if i["id"] == 5)
        assert item5["status"] == "auto_failed"
        assert item5["evidence"]["deviations"][0]["deviation_pct"] == 30.0

    def test_similar_project_comparison(self, db_session):
        """同类项目对比：BOM 总成本偏差>10% → auto_failed。"""
        from app.services.dashboard.bom_cost_check_service import BomCostCheckService

        # 同类项目A：BOM 总成本 50000
        proj_a = _make_project(db_session, "BOMCHECK-SIM-A", category="ICT测试")
        _make_bom(db_session, proj_a.id, total=50000)

        # 同类项目B：BOM 总成本 70000（偏差 40%，>10%）
        proj_b = _make_project(db_session, "BOMCHECK-SIM-B", category="ICT测试")
        _make_bom(db_session, proj_b.id, total=70000)

        result = BomCostCheckService(db_session).get_check(proj_b.id)
        item12 = next(i for i in result["items"] if i["id"] == 12)
        assert item12["status"] == "auto_failed"
        assert item12["evidence"]["deviation_pct"] == 40.0

    def test_project_not_found(self, db_session):
        from app.services.dashboard.bom_cost_check_service import BomCostCheckService

        result = BomCostCheckService(db_session).get_check(999999)
        assert "error" in result
