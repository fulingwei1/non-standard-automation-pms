# -*- coding: utf-8 -*-
"""dwell_time_monitor 深度测试"""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.models.sales.sales_funnel import AlertSeverityEnum, AlertStatusEnum, FunnelEntityTypeEnum
from app.services.sales.dwell_time_monitor import DwellTimeMonitorService


class FakeQuery:
    def __init__(self, first_value=None, all_value=None, count_value=0, update_value=0):
        self._first_value = first_value
        self._all_value = all_value or []
        self._count_value = count_value
        self._update_value = update_value

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self._all_value

    def first(self):
        return self._first_value

    def order_by(self, *args, **kwargs):
        return self

    def offset(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def count(self):
        return self._count_value

    def group_by(self, *args, **kwargs):
        return self

    def update(self, *args, **kwargs):
        return self._update_value


class TestDwellTimeMonitorDeep:
    def test_check_all_entities_aggregates_results(self):
        service = DwellTimeMonitorService(Mock())
        service._check_leads = Mock(return_value=[1])
        service._check_opportunities = Mock(return_value=[2, 3])
        service._check_quotes = Mock(return_value=[])
        service._check_contracts = Mock(return_value=[4])

        result = service.check_all_entities()

        assert result == [1, 2, 3, 4]

    def test_get_stage_enter_time_uses_last_log_or_default(self):
        db = Mock()
        service = DwellTimeMonitorService(db)
        log = SimpleNamespace(transitioned_at=datetime(2026, 4, 1, 10, 0, 0))
        db.query.return_value = FakeQuery(first_value=log)

        result = service._get_stage_enter_time(FunnelEntityTypeEnum.LEAD, 1, datetime(2026, 1, 1))
        assert result == log.transitioned_at

        db.query.return_value = FakeQuery(first_value=None)
        default = datetime(2026, 1, 1)
        assert service._get_stage_enter_time(FunnelEntityTypeEnum.LEAD, 1, default) == default

    def test_check_entity_dwell_time_creates_new_alert(self):
        db = Mock()
        stage = SimpleNamespace(id=9)
        config = SimpleNamespace(alert_enabled=True, expected_hours=1, warning_hours=2, critical_hours=4)
        db.query.side_effect = [FakeQuery(first_value=stage), FakeQuery(first_value=config), FakeQuery(first_value=None)]
        service = DwellTimeMonitorService(db)
        service._generate_alert_code = Mock(return_value="DWL202604120001")

        with patch(
            "app.services.sales.dwell_time_monitor.StageDwellTimeAlert",
            side_effect=lambda **kwargs: SimpleNamespace(**kwargs),
        ):
            alert = service._check_entity_dwell_time(
                FunnelEntityTypeEnum.LEAD, 1, "NEW", datetime.now() - timedelta(hours=3), None, 7, None
            )

        assert alert.alert_code == "DWL202604120001"
        assert alert.severity == AlertSeverityEnum.WARNING.value
        assert alert.status == AlertStatusEnum.ACTIVE
        assert db.add.called and db.commit.called and db.refresh.called

    def test_check_entity_dwell_time_escalates_existing_alert(self):
        db = Mock()
        stage = SimpleNamespace(id=9)
        config = SimpleNamespace(alert_enabled=True, expected_hours=1, warning_hours=2, critical_hours=4)
        existing = SimpleNamespace(severity=AlertSeverityEnum.INFO.value)
        db.query.side_effect = [FakeQuery(first_value=stage), FakeQuery(first_value=config), FakeQuery(first_value=existing)]
        service = DwellTimeMonitorService(db)

        alert = service._check_entity_dwell_time(
            FunnelEntityTypeEnum.LEAD, 1, "NEW", datetime.now() - timedelta(hours=5), None, 7, None
        )

        assert alert is None
        assert existing.severity == AlertSeverityEnum.CRITICAL.value
        assert db.commit.called

    def test_generate_alert_code_and_message(self):
        db = Mock()
        db.query.return_value = FakeQuery(first_value=SimpleNamespace(alert_code="DWL202604120009"))
        service = DwellTimeMonitorService(db)

        code = service._generate_alert_code()
        msg = service._generate_alert_message(FunnelEntityTypeEnum.OPPORTUNITY, 8, "QUALIFICATION", 72, 48)

        assert code.endswith("0010")
        assert "商机 #8" in msg
        assert "超过阈值 48 小时" in msg

    def test_acknowledge_resolve_ignore_alert(self):
        db = Mock()
        alert = SimpleNamespace(id=1, alert_code="A1")
        db.query.return_value = FakeQuery(first_value=alert)
        service = DwellTimeMonitorService(db)

        acknowledged = service.acknowledge_alert(1, 3)
        assert acknowledged.status == AlertStatusEnum.ACKNOWLEDGED

        resolved = service.resolve_alert(1, "done")
        assert resolved.status == AlertStatusEnum.RESOLVED
        assert resolved.resolution_note == "done"

        ignored = service.ignore_alert(1, "skip")
        assert ignored.status == AlertStatusEnum.IGNORED
        assert ignored.resolution_note == "skip"

    def test_auto_resolve_get_alerts_statistics_and_workload(self):
        db = Mock()
        service = DwellTimeMonitorService(db)
        db.query.side_effect = [
            FakeQuery(update_value=2),
            FakeQuery(count_value=3, all_value=[1, 2, 3]),
            FakeQuery(all_value=[("ACTIVE", 2), ("RESOLVED", 1)]),
            FakeQuery(all_value=[("CRITICAL", 1), ("WARNING", 1)]),
            FakeQuery(all_value=[("LEAD", 2)]),
            FakeQuery(all_value=[
                SimpleNamespace(id=1, alert_code="A1", entity_type="LEAD", entity_id=1, severity="CRITICAL", dwell_hours=10),
                SimpleNamespace(id=2, alert_code="A2", entity_type="LEAD", entity_id=2, severity="WARNING", dwell_hours=5),
            ]),
        ]

        resolved_count = service.auto_resolve_on_transition(FunnelEntityTypeEnum.LEAD, 1)
        alerts, total = service.get_alerts(limit=3)
        stats = service.get_alert_statistics()
        workload = service.get_owner_workload(7)

        assert resolved_count == 2
        assert total == 3
        assert alerts == [1, 2, 3]
        assert stats["by_status"]["ACTIVE"] == 2
        assert stats["by_severity"]["CRITICAL"] == 1
        assert workload["total_alerts"] == 2
        assert workload["critical"] == 1
        assert workload["warning"] == 1
