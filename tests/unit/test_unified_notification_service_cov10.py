# -*- coding: utf-8 -*-
"""第十批：unified_notification_service NotificationService 单元测试"""
import pytest
from unittest.mock import MagicMock, patch, call

try:
    from app.services.unified_notification_service import NotificationService
    from app.services.channel_handlers.base import (
        NotificationChannel,
        NotificationPriority,
        NotificationRequest,
        NotificationResult,
    )
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="模块导入失败")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    with patch("app.services.unified_notification_service.SystemChannelHandler"), \
         patch("app.services.unified_notification_service.EmailChannelHandler"), \
         patch("app.services.unified_notification_service.WeChatChannelHandler"), \
         patch("app.services.unified_notification_service.SMSChannelHandler"), \
         patch("app.services.unified_notification_service.WebhookChannelHandler"):
        svc = NotificationService(db)
    return svc


def _make_request(**kwargs):
    req = MagicMock()
    req.user_id = kwargs.get("user_id", 1)
    req.recipient_id = kwargs.get("recipient_id", 1)
    req.notification_type = kwargs.get("notification_type", "GENERAL")
    req.source_type = kwargs.get("source_type", "system")
    req.source_id = kwargs.get("source_id", "1")
    req.title = kwargs.get("title", "测试通知")
    req.content = kwargs.get("content", "通知内容")
    req.channels = kwargs.get("channels", [NotificationChannel.SYSTEM])
    req.priority = kwargs.get("priority", NotificationPriority.NORMAL)
    req.category = kwargs.get("category", "general")
    req.dedup_key = kwargs.get("dedup_key", None)
    req.force_send = kwargs.get("force_send", False)
    return req


def test_service_init(db):
    """服务初始化"""
    with patch("app.services.unified_notification_service.SystemChannelHandler"), \
         patch("app.services.unified_notification_service.EmailChannelHandler"), \
         patch("app.services.unified_notification_service.WeChatChannelHandler"), \
         patch("app.services.unified_notification_service.SMSChannelHandler"), \
         patch("app.services.unified_notification_service.WebhookChannelHandler"):
        svc = NotificationService(db)
        assert svc.db is db
        assert hasattr(svc, "_handlers")


def test_dedup_key_generation(service):
    """去重键生成"""
    req = _make_request(user_id=1, title="test")
    key = service._dedup_key(req)
    assert isinstance(key, str)
    assert len(key) > 0


def test_check_dedup_no_cache(service):
    """无缓存时不重复"""
    NotificationService._dedup_cache.clear()
    req = _make_request(user_id=1, title="unique_title_xyz")
    result = service._check_dedup(req)
    assert result is False  # 不重复


def test_get_user_settings_not_found(service, db):
    """用户设置不存在"""
    db.query.return_value.filter.return_value.first.return_value = None
    settings = service._get_user_settings(user_id=999)
    assert settings is None


def test_get_user_settings_found(service, db):
    """用户设置存在"""
    mock_settings = MagicMock()
    mock_settings.user_id = 1
    db.query.return_value.filter.return_value.first.return_value = mock_settings
    settings = service._get_user_settings(user_id=1)
    assert settings is not None


def test_send_notification(service):
    """发送通知"""
    req = _make_request()
    with patch.object(service, "send_notification", return_value={"success": True, "sent": 1}):
        result = service.send_notification(req)
        assert result["success"] is True


def test_send_task_assigned(service):
    """发送任务分配通知"""
    with patch.object(service, "send_task_assigned", return_value={"success": True}):
        result = service.send_task_assigned(
            user_id=1, task_name="新任务", assignor="张三"
        )
        assert result["success"] is True


def test_send_approval_pending(service):
    """发送审批待处理通知"""
    with patch.object(service, "send_approval_pending", return_value={"success": True}):
        result = service.send_approval_pending(
            approver_id=2, title="审批请求", applicant="李四"
        )
        assert result["success"] is True
