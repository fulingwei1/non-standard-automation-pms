# -*- coding: utf-8 -*-
"""
OTD 风险快照与趋势测试

验证：
- 快照写入（batch_scan create_snapshot=True）
- 同项目同日幂等去重
- 单项目趋势返回结构（连续日期 + severity 序列 + 维度命中）
- 全局趋势返回结构（每日各等级项目数）
- 不存在的项目趋势返回 error
"""

from datetime import date, timedelta

import pytest

from app.models.otd_risk_snapshot import OTDRiskSnapshot
from app.models.project import Project


def _make_project(db, code="OTD-SNAP-001", stage="S3", **overrides):
    defaults = dict(
        project_code=code,
        project_name=f"快照测试 {code}",
        stage=stage,
        status="ST01",
        health="H1",
        progress_pct=30,
        is_active=True,
        is_archived=False,
        planned_start_date=date.today() - timedelta(days=10),
        planned_end_date=date.today() + timedelta(days=120),
    )
    defaults.update(overrides)
    p = Project(**defaults)
    db.add(p)
    db.flush()
    return p


# ============================================================
# 快照写入
# ============================================================


class TestSnapshotCreation:
    def test_snapshot_created_on_scan(self, db_session):
        """batch_scan(create_snapshot=True) 落一条快照。"""
        from app.services.otd import OTDScanService

        project = _make_project(db_session)
        OTDScanService(db_session).batch_scan(
            project_ids=[project.id], create_alerts=False, create_snapshot=True
        )

        snap = (
            db_session.query(OTDRiskSnapshot)
            .filter(OTDRiskSnapshot.project_id == project.id)
            .first()
        )
        assert snap is not None
        assert snap.snapshot_date == date.today()
        assert snap.severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        assert isinstance(snap.risk_items_count, int)

    def test_snapshot_not_created_when_flag_false(self, db_session):
        """create_snapshot=False 时不落快照。"""
        from app.services.otd import OTDScanService

        project = _make_project(db_session)
        OTDScanService(db_session).batch_scan(
            project_ids=[project.id], create_alerts=False, create_snapshot=False
        )
        cnt = (
            db_session.query(OTDRiskSnapshot)
            .filter(OTDRiskSnapshot.project_id == project.id)
            .count()
        )
        assert cnt == 0

    def test_same_day_dedup(self, db_session):
        """同项目同日重复扫描只存一条快照。"""
        from app.services.otd import OTDScanService

        project = _make_project(db_session)
        svc = OTDScanService(db_session)
        svc.batch_scan(
            project_ids=[project.id], create_alerts=False, create_snapshot=True
        )
        svc.batch_scan(
            project_ids=[project.id], create_alerts=False, create_snapshot=True
        )

        cnt = (
            db_session.query(OTDRiskSnapshot)
            .filter(
                OTDRiskSnapshot.project_id == project.id,
                OTDRiskSnapshot.snapshot_date == date.today(),
            )
            .count()
        )
        assert cnt == 1

    def test_batch_scan_returns_snapshots_created_count(self, db_session):
        """返回值含 snapshots_created 字段。"""
        from app.services.otd import OTDScanService

        project = _make_project(db_session)
        result = OTDScanService(db_session).batch_scan(
            project_ids=[project.id], create_alerts=False, create_snapshot=True
        )
        assert "snapshots_created" in result
        assert result["snapshots_created"] == 1

    def test_hit_flags_populated(self, db_session):
        """命中维度的 *_hit 列式标记被正确填充。"""
        from app.models.purchase import PurchaseOrder, PurchaseOrderItem
        from app.services.otd import OTDScanService

        project = _make_project(db_session, stage="S3")
        # 造采购延期（命中维度1）
        po = PurchaseOrder(
            order_no="PO-SNAP-001",
            supplier_id=1,
            project_id=project.id,
            status="APPROVED",
            promised_date=date.today() - timedelta(days=20),
        )
        db_session.add(po)
        db_session.flush()
        db_session.add(
            PurchaseOrderItem(
                order_id=po.id,
                item_no=1,
                material_code="M001",
                material_name="物料",
                quantity=100,
                promised_date=date.today() - timedelta(days=20),
                received_qty=0,
            )
        )
        db_session.flush()

        OTDScanService(db_session).batch_scan(
            project_ids=[project.id], create_alerts=False, create_snapshot=True
        )
        snap = (
            db_session.query(OTDRiskSnapshot)
            .filter(OTDRiskSnapshot.project_id == project.id)
            .first()
        )
        assert snap.procurement_delay_hit is True
        assert snap.risk_items_count >= 1


# ============================================================
# 单项目趋势
# ============================================================


class TestProjectTrend:
    def test_trend_returns_continuous_dates(self, db_session):
        """趋势返回连续日期序列（无空洞），即使只有 1 条快照。"""
        from app.services.otd.trend_service import OTDTrendService

        project = _make_project(db_session)
        # 手动插一条 3 天前的快照
        db_session.add(
            OTDRiskSnapshot(
                project_id=project.id,
                snapshot_date=date.today() - timedelta(days=3),
                severity="HIGH",
                risk_items_count=2,
                procurement_delay_hit=True,
            )
        )
        db_session.flush()

        result = OTDTrendService(db_session).get_project_trend(project.id, days=7)
        assert "dates" in result
        assert len(result["dates"]) == 8  # 7 天 = 8 个日期（含起止）
        # severity 序列长度与 dates 一致
        assert len(result["severity"]) == len(result["dates"])
        # 有快照的那天有值，无快照的那天为 None
        assert "HIGH" in result["severity"]
        assert None in result["severity"]

    def test_trend_dimensions_structure(self, db_session):
        """返回各维度的命中序列。"""
        from app.services.otd.trend_service import OTDTrendService

        project = _make_project(db_session)
        result = OTDTrendService(db_session).get_project_trend(project.id, days=5)
        assert "dimensions" in result
        # 11 个维度都有
        assert "采购延期" in result["dimensions"]
        assert "毛利偏差" in result["dimensions"]
        # 每个维度序列长度 = 日期数
        for label, series in result["dimensions"].items():
            assert len(series) == len(result["dates"])

    def test_trend_project_not_found(self, db_session):
        """不存在的项目返回 error。"""
        from app.services.otd.trend_service import OTDTrendService

        result = OTDTrendService(db_session).get_project_trend(999999, days=7)
        assert "error" in result


# ============================================================
# 全局趋势
# ============================================================


class TestGlobalTrend:
    def test_global_trend_structure(self, db_session):
        """全局趋势返回 severity_trend + heatmap。"""
        from app.services.otd.trend_service import OTDTrendService

        project = _make_project(db_session)
        db_session.add(
            OTDRiskSnapshot(
                project_id=project.id,
                snapshot_date=date.today(),
                severity="CRITICAL",
                risk_items_count=3,
                procurement_delay_hit=True,
                margin_deviation_hit=True,
            )
        )
        db_session.flush()

        result = OTDTrendService(db_session).get_global_trend(days=7)
        assert "dates" in result
        assert "severity_trend" in result
        assert "heatmap" in result
        assert len(result["severity_trend"]) == len(result["dates"])

        # 今天的 CRITICAL 应该被统计到
        today_entry = next(
            e for e in result["severity_trend"] if e["date"] == date.today().isoformat()
        )
        assert today_entry["CRITICAL"] >= 1

        # heatmap 今天的采购延期命中数 >= 1
        today_heat = next(
            h for h in result["heatmap"] if h["date"] == date.today().isoformat()
        )
        assert today_heat["采购延期"] >= 1

    def test_global_trend_no_snapshots(self, db_session):
        """无快照时返回空结构（不报错）。"""
        from app.services.otd.trend_service import OTDTrendService

        result = OTDTrendService(db_session).get_global_trend(days=3)
        assert len(result["dates"]) == 4
        assert result["total_snapshots"] == 0
