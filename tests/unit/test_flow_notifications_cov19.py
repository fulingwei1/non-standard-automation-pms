# -*- coding: utf-8 -*-
"""
第十九批 - 审批流程通知模块单元测试
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.approval_engine.notify.flow_notifications")


def make_service():
    from app.services.approval_engine.notify.flow_notifications import FlowNotificationsMixin

    class ConcreteService(FlowNotificationsMixin):
        def __init__(self):
            self._sent = []

        def _send_notification(self, notification):
            self._sent.append(notification)

    return ConcreteService()


def make_instance(title="测试审批", instance_id=1, urgency="NORMAL"):
    inst = MagicMock()
    inst.title = title
    inst.id = instance_id
    inst.urgency = urgency
    return inst


def make_task(assignee_id=10, task_id=100, instance=None):
    task = MagicMock()
    task.id = task_id
    task.assignee_id = assignee_id
    task.instance = instance or make_instance()
    return task


def test_notify_withdrawn_sends_to_all_users():
    """撤回通知发送给所有受影响用户"""
    svc = make_service()
    instance = make_instance()
    svc.notify_withdrawn(instance, affected_user_ids=[1, 2, 3])
    assert len(svc._sent) == 3
    receivers = [n['receiver_id'] for n in svc._sent]
    assert receivers == [1, 2, 3]


def test_notify_withdrawn_notification_type():
    """撤回通知类型正确"""
    svc = make_service()
    instance = make_instance(title="合同审批")
    svc.notify_withdrawn(instance, affected_user_ids=[5])
    n = svc._sent[0]
    assert n['type'] == 'APPROVAL_WITHDRAWN'
    assert '合同审批' in n['title']
    assert n['instance_id'] == instance.id


def test_notify_withdrawn_empty_users():
    """无受影响用户时不发通知"""
    svc = make_service()
    instance = make_instance()
    svc.notify_withdrawn(instance, affected_user_ids=[])
    assert len(svc._sent) == 0


def test_notify_transferred_basic():
    """转审通知包含必要字段"""
    svc = make_service()
    instance = make_instance(title="采购审批")
    task = make_task(assignee_id=7, task_id=42, instance=instance)
    svc.notify_transferred(task, from_user_id=3)
    assert len(svc._sent) == 1
    n = svc._sent[0]
    assert n['type'] == 'APPROVAL_TRANSFERRED'
    assert n['receiver_id'] == 7
    assert n['task_id'] == 42
    assert n['instance_id'] == instance.id


def test_notify_transferred_with_from_user_name():
    """转审通知包含原审批人姓名"""
    svc = make_service()
    instance = make_instance(title="费用审批")
    task = make_task(assignee_id=9, instance=instance)
    svc.notify_transferred(task, from_user_id=1, from_user_name="张三")
    n = svc._sent[0]
    assert '张三' in n['content']


def test_notify_delegated_basic():
    """代理通知包含必要字段"""
    svc = make_service()
    instance = make_instance(title="报销审批")
    task = make_task(assignee_id=15, instance=instance)
    svc.notify_delegated(task)
    assert len(svc._sent) == 1
    n = svc._sent[0]
    assert n['type'] == 'APPROVAL_DELEGATED'
    assert n['receiver_id'] == 15


def test_notify_delegated_with_original_user():
    """代理通知包含原审批人信息"""
    svc = make_service()
    instance = make_instance()
    task = make_task(instance=instance)
    svc.notify_delegated(task, original_user_name="李四")
    n = svc._sent[0]
    assert '李四' in n['content']


def test_notify_add_approver_after():
    """加签通知 - 后加签"""
    svc = make_service()
    instance = make_instance(title="变更审批")
    task = make_task(assignee_id=20, instance=instance)
    svc.notify_add_approver(task, added_by_name="王五", position="AFTER")
    n = svc._sent[0]
    assert n['type'] == 'APPROVAL_ADD_APPROVER'
    assert '后加签' in n['content']
    assert '王五' in n['content']
    assert n['receiver_id'] == 20


def test_notify_add_approver_before():
    """加签通知 - 前加签"""
    svc = make_service()
    instance = make_instance()
    task = make_task(instance=instance)
    svc.notify_add_approver(task, position="BEFORE")
    n = svc._sent[0]
    assert '前加签' in n['content']
