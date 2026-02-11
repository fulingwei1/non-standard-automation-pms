# -*- coding: utf-8 -*-
"""Tests for wechat_alert_service.py"""
from unittest.mock import MagicMock, patch
from datetime import date


class TestWeChatAlertService:
    def setup_method(self):
        self.db = MagicMock()

    @patch("app.services.wechat_alert_service.WeChatAlertService._send_wechat_message", return_value=True)
    @patch("app.services.wechat_alert_service.WeChatAlertService._get_notify_users")
    @patch("app.services.wechat_alert_service.WeChatAlertService._build_alert_message")
    def test_send_shortage_alert_success(self, mock_build, mock_users, mock_send):
        from app.services.wechat_alert_service import WeChatAlertService

        readiness = MagicMock(id=1, project_id=1, machine_id=None)
        project = MagicMock(id=1, project_no="P001", name="测试项目")
        user = MagicMock(id=1, username="user1")

        self.db.query.return_value.filter.return_value.first.side_effect = [
            readiness, project, None  # readiness, project, rule
        ]
        mock_build.return_value = {"msgtype": "template_card"}
        mock_users.return_value = [user]

        shortage = MagicMock(readiness_id=1)
        result = WeChatAlertService.send_shortage_alert(self.db, shortage, "L1")
        assert result is True

    def test_send_shortage_alert_no_readiness(self):
        from app.services.wechat_alert_service import WeChatAlertService
        self.db.query.return_value.filter.return_value.first.return_value = None
        shortage = MagicMock(readiness_id=1)
        result = WeChatAlertService.send_shortage_alert(self.db, shortage, "L1")
        assert result is False

    def test_build_alert_message(self):
        from app.services.wechat_alert_service import WeChatAlertService
        shortage = MagicMock(
            material_name="物料A", material_code="M001",
            shortage_qty=5, unit="个", assembly_stage="MECH",
            expected_arrival=None
        )
        readiness = MagicMock(id=1, stage_kit_rates={}, current_workable_stage="FRAME")
        project = MagicMock(project_no="P001", name="项目A", planned_start_date=date(2025, 6, 1))
        machine = None
        rule = None

        msg = WeChatAlertService._build_alert_message(
            self.db, shortage, readiness, project, machine, "L2", rule
        )
        assert msg["msgtype"] == "template_card"
        assert "紧急预警" in msg["template_card"]["main_title"]["title"]

    def test_get_notify_users_default(self):
        from app.services.wechat_alert_service import WeChatAlertService
        project = MagicMock(project_manager_id=1)
        pm = MagicMock(id=1)
        self.db.query.return_value.filter.return_value.first.return_value = pm
        users = WeChatAlertService._get_notify_users(self.db, None, project)
        assert len(users) == 1

    def test_get_notify_users_no_rule_no_pm(self):
        from app.services.wechat_alert_service import WeChatAlertService
        project = MagicMock(project_manager_id=None)
        users = WeChatAlertService._get_notify_users(self.db, None, project)
        assert users == []

    def test_batch_send_alerts(self):
        from app.services.wechat_alert_service import WeChatAlertService
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = WeChatAlertService.batch_send_alerts(self.db)
        assert result['total'] == 0
