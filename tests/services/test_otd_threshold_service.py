# -*- coding: utf-8 -*-
"""
OTD 阈值配置服务测试

验证：
- DB 无配置时返回代码默认值（fallback）
- update_default_config 持久化
- scan 真的读配置而非硬编码（改阈值→severity 变）
"""

from datetime import date, timedelta

import pytest

from app.models.otd_threshold_config import OtdThresholdConfig
from app.models.project import Project
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.schemas.otd_threshold import OtdThresholdConfigUpdate


class TestThresholdServiceLoad:
    """配置加载与 fallback。"""

    def test_get_active_config_returns_default_when_empty(self, db_session):
        """DB 无配置行时，返回代码默认值（内存实例，不报错）。"""
        from app.services.otd.threshold_service import get_active_config

        config = get_active_config(db_session)
        # 关键默认值正确
        assert config.scan_limit == 200
        assert config.procurement_overdue_high_days == 15
        assert config.open_items_high_count == 10
        # 是内存实例（无 id），不是 DB 行
        assert config.id is None
        assert config.is_default is True

    def test_get_active_config_reads_from_db(self, db_session):
        """DB 有配置行时，返回 DB 行（优先于代码默认值）。"""
        from app.services.otd.threshold_service import (
            DEFAULT_CONFIG_CODE,
            get_active_config,
        )

        # 建一条 DB 配置行，改一个阈值
        cfg = OtdThresholdConfig(
            name="测试配置",
            code=DEFAULT_CONFIG_CODE,
            is_active=True,
            is_default=True,
            scan_limit=150,
            procurement_overdue_high_days=999,  # 改个特殊值
        )
        db_session.add(cfg)
        db_session.commit()

        loaded = get_active_config(db_session)
        assert loaded.id is not None  # 是 DB 行
        assert loaded.procurement_overdue_high_days == 999
        assert loaded.scan_limit == 150


class TestThresholdServiceUpdate:
    """配置更新。"""

    def test_update_creates_when_missing(self, db_session):
        """DB 无配置时，update 自动从默认值创建。"""
        from app.services.otd.threshold_service import (
            DEFAULT_CONFIG_CODE,
            get_active_config,
            update_default_config,
        )

        # 先清理可能存在的配置行（避免其他测试污染）
        db_session.query(OtdThresholdConfig).filter(
            OtdThresholdConfig.code == DEFAULT_CONFIG_CODE
        ).delete()
        db_session.commit()

        payload = OtdThresholdConfigUpdate(procurement_overdue_high_days=5)
        config = update_default_config(db_session, payload, user_id=1)

        assert config.id is not None  # 持久化了
        assert config.procurement_overdue_high_days == 5  # 改了
        # 其他字段保持默认值
        assert config.procurement_overdue_medium_days == 7
        assert config.scan_limit == 200

        # 再读，确认能读到新值
        loaded = get_active_config(db_session)
        assert loaded.procurement_overdue_high_days == 5

    def test_update_partial(self, db_session):
        """部分更新：只改一个字段，其他保持。"""
        from app.services.otd.threshold_service import update_default_config

        # 先建一条
        update_default_config(
            db_session, OtdThresholdConfigUpdate(procurement_overdue_high_days=10), 1
        )
        # 再改另一个字段
        update_default_config(
            db_session, OtdThresholdConfigUpdate(open_items_high_count=20), 1
        )

        from app.services.otd.threshold_service import get_active_config

        config = get_active_config(db_session)
        assert config.procurement_overdue_high_days == 10  # 第一次的还在
        assert config.open_items_high_count == 20  # 第二次改的


class TestScanReadsConfig:
    """验证 scan 真的读配置而非硬编码。"""

    def _make_project_with_overdue_po(self, db, overdue_days):
        """建一个有逾期采购的项目，逾期天数可控。"""
        project = Project(
            project_code=f"OTD-CFG-{overdue_days}",
            project_name="配置测试项目",
            stage="S3",
            status="ST01",
            health="H1",
            progress_pct=30,
            is_active=True,
            is_archived=False,
            planned_start_date=date.today() - timedelta(days=60),
            planned_end_date=date.today() + timedelta(days=60),
        )
        db.add(project)
        db.flush()
        po = PurchaseOrder(
            order_no=f"PO-CFG-{overdue_days}",
            supplier_id=1,
            project_id=project.id,
            status="APPROVED",
            promised_date=date.today() - timedelta(days=overdue_days),
        )
        db.add(po)
        db.flush()
        db.add(
            PurchaseOrderItem(
                order_id=po.id,
                item_no=1,
                material_code="M001",
                material_name="物料",
                quantity=100,
                promised_date=date.today() - timedelta(days=overdue_days),
                received_qty=0,
            )
        )
        db.flush()
        return project

    def test_scan_uses_config_threshold(self, db_session):
        """改阈值后扫描 severity 变化：证明 scan 读 config 而非硬编码。

        默认阈值：逾期 15 天 → HIGH。
        把 high_days 改成 5，原本 MEDIUM(逾期 10 天) 的应升 HIGH。
        """
        from app.services.otd import OTDScanService
        from app.services.otd.threshold_service import update_default_config

        # 建一个逾期 10 天的项目（默认阈值下是 MEDIUM，因为 7 < 10 < 15）
        project = self._make_project_with_overdue_po(db_session, overdue_days=10)

        # 默认配置下扫描
        svc = OTDScanService(db_session)
        profile = svc.scan_project(project.id)
        proc = next(
            it for it in profile["risk_items"] if it["dim"] == "procurement_delay"
        )
        assert proc["severity"] == "MEDIUM"  # 10 天在 7-15 区间

        # 改阈值：high_days 从 15 改成 5
        update_default_config(
            db_session,
            OtdThresholdConfigUpdate(procurement_overdue_high_days=5),
            user_id=1,
        )

        # 重新扫描（新 service 实例会重新加载 config）
        svc2 = OTDScanService(db_session)
        profile2 = svc2.scan_project(project.id)
        proc2 = next(
            it for it in profile2["risk_items"] if it["dim"] == "procurement_delay"
        )
        assert proc2["severity"] == "HIGH"  # 10 天 > 5，升 HIGH
