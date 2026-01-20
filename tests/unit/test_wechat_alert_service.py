# -*- coding: utf-8 -*-
"""
Tests for wechat_alert_service
Covers: app/services/wechat_alert_service.py
Coverage Target: 0% -> 60%+
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, Mock
from sqlalchemy.orm import Session


class TestWeChatAlertService:
    """企业微信预警消息服务测试"""

    @pytest.fixture
    def mock_shortage_detail(self):
        """模拟缺料明细"""
        mock = MagicMock()
        mock.id = 1
        mock.material_code = "MAT001"
        mock.material_name = "测试物料"
        mock.required_quantity = Decimal("100")
        mock.current_quantity = Decimal("20")
        mock.shortage_quantity = Decimal("80")
        mock.readiness_id = 1
        return mock

    @pytest.fixture
    def mock_readiness(self):
        """模拟物料准备度"""
        mock = MagicMock()
        mock.id = 1
        mock.project_id = 1
        mock.machine_id = 1
        return mock

    @pytest.fixture
    def mock_project(self):
        """模拟项目"""
        mock = MagicMock()
        mock.id = 1
        mock.project_code = "PJ001"
        mock.project_name = "测试项目"
        return mock

    @pytest.fixture
    def mock_machine(self):
        """模拟机台"""
        mock = MagicMock()
        mock.id = 1
        mock.machine_code = "M001"
        mock.machine_name = "测试设备"
        return mock

    @pytest.fixture
    def mock_rule(self):
        """模拟预警规则"""
        mock = MagicMock()
        mock.id = 1
        mock.alert_level = "L1"
        mock.rule_name = "一级预警"
        mock.notification_channels = ["wechat"]
        return mock

    @pytest.fixture
    def mock_user(self):
        """模拟用户"""
        mock = MagicMock()
        mock.id = 1
        mock.username = "testuser"
        mock.real_name = "测试用户"
        mock.department = "研发部"
        return mock

    def test_send_shortage_alert_success(
        self, db_session: Session, mock_shortage_detail, mock_readiness,
        mock_project, mock_machine, mock_rule, mock_user
    ):
        """测试缺料预警发送成功"""
        from app.services.wechat_alert_service import WeChatAlertService

        db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_readiness, mock_project, mock_machine, mock_rule, [mock_user]
        ]

        with patch.object(WeChatAlertService, '_build_alert_message', return_value={"type": "alert"}):
            with patch.object(WeChatAlertService, '_get_notify_users', return_value=[mock_user]):
                with patch.object(WeChatAlertService, '_send_wechat_message', return_value=True):
                    result = WeChatAlertService.send_shortage_alert(
                        db_session, mock_shortage_detail, "L1"
                    )
                    assert result is True

    def test_send_shortage_alert_no_readiness(
        self, db_session: Session, mock_shortage_detail
    ):
        """测试缺料预警 - 找不到准备度记录"""
        from app.services.wechat_alert_service import WeChatAlertService

        db_session.query.return_value.filter.return_value.first.return_value = None

        result = WeChatAlertService.send_shortage_alert(
            db_session, mock_shortage_detail, "L1"
        )
        assert result is False

    def test_send_shortage_alert_no_project(
        self, db_session: Session, mock_shortage_detail, mock_readiness
    ):
        """测试缺料预警 - 找不到项目"""
        from app.services.wechat_alert_service import WeChatAlertService

        db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_readiness, None
        ]

        result = WeChatAlertService.send_shortage_alert(
            db_session, mock_shortage_detail, "L1"
        )
        assert result is False

    def test_send_shortage_alert_no_machine(
        self, db_session: Session, mock_shortage_detail, mock_readiness, mock_project
    ):
        """测试缺料预警 - 无机台信息时仍能成功"""
        from app.services.wechat_alert_service import WeChatAlertService

        mock_readiness.machine_id = None

        db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_readiness, mock_project, None, None, []
        ]

        result = WeChatAlertService.send_shortage_alert(
            db_session, mock_shortage_detail, "L1"
        )
        # 无通知用户时返回 False
        assert result is False

    def test_build_alert_message(
        self, db_session: Session, mock_shortage_detail, mock_readiness,
        mock_project, mock_machine, mock_rule
    ):
        """测试预警消息构建"""
        from app.services.wechat_alert_service import WeChatAlertService

        message = WeChatAlertService._build_alert_message(
            db_session, mock_shortage_detail, mock_readiness,
            mock_project, mock_machine, "L1", mock_rule
        )

        assert message is not None
        assert "alert_level" in message

    def test_get_notify_users_with_rule(self, db_session: Session, mock_rule, mock_project, mock_user):
        """测试获取通知用户（带规则）"""
        from app.services.wechat_alert_service import WeChatAlertService

        db_session.query.return_value.filter.return_value.first.return_value = mock_rule

        with patch.object(WeChatAlertService, '_get_project_managers', return_value=[mock_user]):
            result = WeChatAlertService._get_notify_users(db_session, mock_rule, mock_project)
            assert result == [mock_user]

    def test_get_notify_users_no_rule(self, db_session: Session, mock_project, mock_user):
        """测试获取通知用户（无规则）"""
        from app.services.wechat_alert_service import WeChatAlertService

        with patch.object(WeChatAlertService, '_get_project_managers', return_value=[mock_user]):
            result = WeChatAlertService._get_notify_users(db_session, None, mock_project)
            assert result == [mock_user]

    def test_send_wechat_message_success(self, mock_user):
        """测试微信消息发送成功"""
        from app.services.wechat_alert_service import WeChatAlertService

        message = {"type": "alert", "content": "测试消息"}

        with patch('httpx.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"errcode": 0}

            result = WeChatAlertService._send_wechat_message(mock_user, message)
            assert result is True

    def test_send_wechat_message_failure(self, mock_user):
        """测试微信消息发送失败"""
        from app.services.wechat_alert_service import WeChatAlertService

        message = {"type": "alert", "content": "测试消息"}

        with patch('httpx.post') as mock_post:
            mock_post.return_value.status_code = 500

            result = WeChatAlertService._send_wechat_message(mock_user, message)
            assert result is False

    def test_get_project_managers(self, db_session: Session, mock_project, mock_user):
        """测试获取项目经理"""
        from app.services.wechat_alert_service import WeChatAlertService

        db_session.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_user]

        result = WeChatAlertService._get_project_managers(db_session, mock_project)
        assert result == [mock_user]

    def test_send_batch_alerts(self, db_session: Session, mock_shortage_detail, mock_readiness,
                               mock_project, mock_machine, mock_rule, mock_user):
        """测试批量预警发送"""
        from app.services.wechat_alert_service import WeChatAlertService

        alerts = [mock_shortage_detail, mock_shortage_detail]

        db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_readiness, mock_project, mock_machine, mock_rule, [mock_user]
        ]

        with patch.object(WeChatAlertService, '_build_alert_message', return_value={"type": "alert"}):
            with patch.object(WeChatAlertService, '_get_notify_users', return_value=[mock_user]):
                with patch.object(WeChatAlertService, '_send_wechat_message', return_value=True):
                    results = WeChatAlertService.send_batch_alerts(db_session, alerts)

                    assert len(results) == 2
                    assert all(r for r in results)
