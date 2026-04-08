import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from decimal import Decimal

# Import models from the actual app structure
from app.models.service import ServiceTicket
from app.models.sla import SLAMonitor, SLAPolicy
from app.services.sla_service import (
    match_sla_policy,
    create_sla_monitor,
    update_sla_monitor_status,
    sync_ticket_to_sla_monitor,
    check_sla_warnings,
    mark_warning_sent
)


class TestSLAService:
    """SLA服务单元测试"""

    def test_match_sla_policy_exact_match(self, db_session):
        """测试精确匹配SLA策略"""
        # 创建测试数据
        policy = SLAPolicy(
            problem_type="硬件故障",
            urgency="紧急",
            response_time_hours=2,
            resolve_time_hours=24,
            priority=1,
            is_active=True
        )
        db_session.add(policy)
        db_session.commit()

        # 测试精确匹配
        result = match_sla_policy(db_session, "硬件故障", "紧急")
        assert result is not None
        assert result.problem_type == "硬件故障"
        assert result.urgency == "紧急"

    def test_match_sla_policy_problem_type_match(self, db_session):
        """测试问题类型匹配SLA策略"""
        # 创建仅匹配问题类型的策略
        policy = SLAPolicy(
            problem_type="软件问题",
            urgency=None,
            response_time_hours=4,
            resolve_time_hours=48,
            priority=1,
            is_active=True
        )
        db_session.add(policy)
        db_session.commit()

        # 测试问题类型匹配
        result = match_sla_policy(db_session, "软件问题", "普通")
        assert result is not None
        assert result.problem_type == "软件问题"
        assert result.urgency is None

    def test_match_sla_policy_urgency_match(self, db_session):
        """测试紧急程度匹配SLA策略"""
        # 创建仅匹配紧急程度的策略
        policy = SLAPolicy(
            problem_type=None,
            urgency="紧急",
            response_time_hours=1,
            resolve_time_hours=12,
            priority=1,
            is_active=True
        )
        db_session.add(policy)
        db_session.commit()

        # 测试紧急程度匹配
        result = match_sla_policy(db_session, "其他问题", "紧急")
        assert result is not None
        assert result.problem_type is None
        assert result.urgency == "紧急"

    def test_match_sla_policy_generic_match(self, db_session):
        """测试通用策略匹配"""
        # 创建通用策略
        policy = SLAPolicy(
            problem_type=None,
            urgency=None,
            response_time_hours=8,
            resolve_time_hours=96,
            priority=1,
            is_active=True
        )
        db_session.add(policy)
        db_session.commit()

        # 测试通用匹配
        result = match_sla_policy(db_session, "未知问题", "未知紧急程度")
        assert result is not None
        assert result.problem_type is None
        assert result.urgency is None

    def test_match_sla_policy_no_match(self, db_session):
        """测试无匹配策略的情况"""
        # 创建一个不匹配的策略
        policy = SLAPolicy(
            problem_type="特定问题",
            urgency="特定紧急",
            response_time_hours=8,
            resolve_time_hours=96,
            priority=1,
            is_active=True
        )
        db_session.add(policy)
        db_session.commit()

        # 测试无匹配情况
        result = match_sla_policy(db_session, "完全不同问题", "完全不同紧急")
        assert result is None

    def test_match_sla_policy_inactive_policy(self, db_session):
        """测试非激活策略不被匹配"""
        # 创建非激活策略
        policy = SLAPolicy(
            problem_type="硬件故障",
            urgency="紧急",
            response_time_hours=2,
            resolve_time_hours=24,
            priority=1,
            is_active=False  # 非激活
        )
        db_session.add(policy)
        db_session.commit()

        # 测试非激活策略不会被匹配
        result = match_sla_policy(db_session, "硬件故障", "紧急")
        assert result is None

    def test_create_sla_monitor(self, db_session):
        """测试创建SLA监控记录"""
        # 创建策略
        policy = SLAPolicy(
            problem_type="硬件故障",
            urgency="紧急",
            response_time_hours=2,
            resolve_time_hours=24,
            priority=1,
            is_active=True
        )
        db_session.add(policy)
        db_session.commit()

        # 创建工单
        ticket = ServiceTicket(
            title="测试工单",
            problem_type="硬件故障",
            urgency="紧急",
            reported_time=datetime(2023, 1, 1, 10, 0, 0)
        )
        db_session.add(ticket)
        db_session.commit()

        # 创建SLA监控记录
        monitor = create_sla_monitor(db_session, ticket, policy)

        # 验证监控记录
        assert monitor is not None
        assert monitor.ticket_id == ticket.id
        assert monitor.policy_id == policy.id
        expected_response_deadline = datetime(2023, 1, 1, 12, 0, 0)  # 10:00 + 2小时
        expected_resolve_deadline = datetime(2023, 1, 2, 10, 0, 0)   # 10:00 + 24小时
        assert monitor.response_deadline == expected_response_deadline
        assert monitor.resolve_deadline == expected_resolve_deadline
        assert monitor.response_status == "ON_TIME"
        assert monitor.resolve_status == "ON_TIME"

    def test_update_sla_monitor_status_response_on_time(self, db_session):
        """测试更新SLA监控状态 - 响应按时"""
        # 创建策略
        policy = SLAPolicy(
            problem_type="硬件故障",
            urgency="紧急",
            response_time_hours=2,
            resolve_time_hours=24,
            priority=1,
            is_active=True
        )
        db_session.add(policy)
        db_session.commit()

        # 创建工单
        ticket = ServiceTicket(
            title="测试工单",
            problem_type="硬件故障",
            urgency="紧急",
            reported_time=datetime(2023, 1, 1, 10, 0, 0)
        )
        db_session.add(ticket)
        db_session.commit()

        # 创建监控记录
        monitor = SLAMonitor(
            ticket_id=ticket.id,
            policy_id=policy.id,
            response_deadline=datetime(2023, 1, 1, 12, 0, 0),
            resolve_deadline=datetime(2023, 1, 2, 10, 0, 0),
            actual_response_time=datetime(2023, 1, 1, 11, 0, 0),  # 在截止时间前响应
            response_status="PENDING"
        )
        db_session.add(monitor)
        db_session.commit()

        # 更新状态
        update_sla_monitor_status(db_session, monitor, datetime(2023, 1, 1, 13, 0, 0))

        # 验证状态
        assert monitor.response_status == "ON_TIME"
        assert monitor.response_time_diff_hours == Decimal("-1")  # 提前1小时

    def test_update_sla_monitor_status_response_overdue(self, db_session):
        """测试更新SLA监控状态 - 响应超时"""
        # 创建策略
        policy = SLAPolicy(
            problem_type="硬件故障",
            urgency="紧急",
            response_time_hours=2,
            resolve_time_hours=24,
            priority=1,
            is_active=True,
            warning_threshold_percent=80  # 设置预警阈值
        )
        db_session.add(policy)
        db_session.commit()

        # 创建工单
        ticket = ServiceTicket(
            title="测试工单",
            problem_type="硬件故障",
            urgency="紧急",
            reported_time=datetime(2023, 1, 1, 10, 0, 0)
        )
        db_session.add(ticket)
        db_session.commit()

        # 创建监控记录
        monitor = SLAMonitor(
            ticket_id=ticket.id,
            policy_id=policy.id,
            response_deadline=datetime(2023, 1, 1, 12, 0, 0),
            resolve_deadline=datetime(2023, 1, 2, 10, 0, 0),
            actual_response_time=datetime(2023, 1, 1, 13, 0, 0),  # 超时1小时
            response_status="PENDING"
        )
        db_session.add(monitor)
        db_session.commit()

        # 更新状态
        update_sla_monitor_status(db_session, monitor, datetime(2023, 1, 1, 14, 0, 0))

        # 验证状态
        assert monitor.response_status == "OVERDUE"
        assert monitor.response_time_diff_hours == Decimal("1")  # 超时1小时

    def test_update_sla_monitor_status_resolve_on_time(self, db_session):
        """测试更新SLA监控状态 - 解决按时"""
        # 创建策略
        policy = SLAPolicy(
            problem_type="硬件故障",
            urgency="紧急",
            response_time_hours=2,
            resolve_time_hours=24,
            priority=1,
            is_active=True
        )
        db_session.add(policy)
        db_session.commit()

        # 创建工单
        ticket = ServiceTicket(
            title="测试工单",
            problem_type="硬件故障",
            urgency="紧急",
            reported_time=datetime(2023, 1, 1, 10, 0, 0)
        )
        db_session.add(ticket)
        db_session.commit()

        # 创建监控记录
        monitor = SLAMonitor(
            ticket_id=ticket.id,
            policy_id=policy.id,
            response_deadline=datetime(2023, 1, 1, 12, 0, 0),
            resolve_deadline=datetime(2023, 1, 2, 10, 0, 0),
            actual_resolve_time=datetime(2023, 1, 2, 9, 0, 0),  # 在截止时间前解决
            resolve_status="PENDING"
        )
        db_session.add(monitor)
        db_session.commit()

        # 更新状态
        update_sla_monitor_status(db_session, monitor, datetime(2023, 1, 2, 11, 0, 0))

        # 验证状态
        assert monitor.resolve_status == "ON_TIME"
        assert monitor.resolve_time_diff_hours == Decimal("-1")  # 提前1小时

    def test_update_sla_monitor_status_resolve_overdue(self, db_session):
        """测试更新SLA监控状态 - 解决超时"""
        # 创建策略
        policy = SLAPolicy(
            problem_type="硬件故障",
            urgency="紧急",
            response_time_hours=2,
            resolve_time_hours=24,
            priority=1,
            is_active=True,
            warning_threshold_percent=80  # 设置预警阈值
        )
        db_session.add(policy)
        db_session.commit()

        # 创建工单
        ticket = ServiceTicket(
            title="测试工单",
            problem_type="硬件故障",
            urgency="紧急",
            reported_time=datetime(2023, 1, 1, 10, 0, 0)
        )
        db_session.add(ticket)
        db_session.commit()

        # 创建监控记录
        monitor = SLAMonitor(
            ticket_id=ticket.id,
            policy_id=policy.id,
            response_deadline=datetime(2023, 1, 1, 12, 0, 0),
            resolve_deadline=datetime(2023, 1, 2, 10, 0, 0),
            actual_resolve_time=datetime(2023, 1, 2, 11, 0, 0),  # 超时1小时
            resolve_status="PENDING"
        )
        db_session.add(monitor)
        db_session.commit()

        # 更新状态
        update_sla_monitor_status(db_session, monitor, datetime(2023, 1, 2, 12, 0, 0))

        # 验证状态
        assert monitor.resolve_status == "OVERDUE"
        assert monitor.resolve_time_diff_hours == Decimal("1")  # 超时1小时

    def test_sync_ticket_to_sla_monitor_with_existing_monitor(self, db_session):
        """测试同步工单到SLA监控 - 存在监控记录"""
        # 创建策略
        policy = SLAPolicy(
            problem_type="硬件故障",
            urgency="紧急",
            response_time_hours=2,
            resolve_time_hours=24,
            priority=1,
            is_active=True
        )
        db_session.add(policy)
        db_session.commit()

        # 创建工单
        ticket = ServiceTicket(
            title="测试工单",
            problem_type="硬件故障",
            urgency="紧急",
            reported_time=datetime(2023, 1, 1, 10, 0, 0),
            response_time=datetime(2023, 1, 1, 11, 0, 0),
            resolved_time=datetime(2023, 1, 1, 15, 0, 0)
        )
        db_session.add(ticket)
        db_session.commit()

        # 创建监控记录
        monitor = SLAMonitor(
            ticket_id=ticket.id,
            policy_id=policy.id,
            response_deadline=datetime(2023, 1, 1, 12, 0, 0),
            resolve_deadline=datetime(2023, 1, 2, 10, 0, 0),
            actual_response_time=None,  # 尚未设置
            actual_resolve_time=None,   # 尚未设置
            response_status="PENDING",
            resolve_status="PENDING"
        )
        db_session.add(monitor)
        db_session.commit()

        # 同步工单到监控
        result = sync_ticket_to_sla_monitor(db_session, ticket)

        # 验证同步结果
        assert result is not None
        assert result.actual_response_time == datetime(2023, 1, 1, 11, 0, 0)
        assert result.actual_resolve_time == datetime(2023, 1, 1, 15, 0, 0)

    def test_sync_ticket_to_sla_monitor_without_monitor(self, db_session):
        """测试同步工单到SLA监控 - 不存在监控记录"""
        # 创建策略
        policy = SLAPolicy(
            problem_type="硬件故障",
            urgency="紧急",
            response_time_hours=2,
            resolve_time_hours=24,
            priority=1,
            is_active=True
        )
        db_session.add(policy)
        db_session.commit()

        # 创建工单
        ticket = ServiceTicket(
            title="测试工单",
            problem_type="硬件故障",
            urgency="紧急",
            reported_time=datetime(2023, 1, 1, 10, 0, 0),
            response_time=datetime(2023, 1, 1, 11, 0, 0)
        )
        db_session.add(ticket)
        db_session.commit()

        # 同步工单到监控（此时还没有对应的监控记录）
        result = sync_ticket_to_sla_monitor(db_session, ticket)

        # 验证创建了新的监控记录
        assert result is not None
        assert result.ticket_id == ticket.id
        assert result.actual_response_time == datetime(2023, 1, 1, 11, 0, 0)

    def test_check_sla_warnings(self, db_session):
        """测试检查SLA预警"""
        # 创建策略
        policy = SLAPolicy(
            problem_type="硬件故障",
            urgency="紧急",
            response_time_hours=2,
            resolve_time_hours=24,
            priority=1,
            is_active=True,
            warning_threshold_percent=80  # 设置预警阈值
        )
        db_session.add(policy)
        db_session.commit()

        # 创建工单
        ticket = ServiceTicket(
            title="测试工单",
            problem_type="硬件故障",
            urgency="紧急",
            reported_time=datetime(2023, 1, 1, 10, 0, 0)
        )
        db_session.add(ticket)
        db_session.commit()

        # 创建处于预警状态的监控记录
        monitor = SLAMonitor(
            ticket_id=ticket.id,
            policy_id=policy.id,
            response_deadline=datetime(2023, 1, 1, 12, 0, 0),
            resolve_deadline=datetime(2023, 1, 2, 10, 0, 0),
            actual_response_time=None,
            actual_resolve_time=None,
            response_status="WARNING",  # 处于预警状态
            resolve_status="ON_TIME",
            response_warning_sent=False,  # 未发送预警
            resolve_warning_sent=False
        )
        db_session.add(monitor)
        db_session.commit()

        # 检查预警
        warnings = check_sla_warnings(db_session, datetime(2023, 1, 1, 11, 30, 0))

        # 验证返回了预警记录
        assert len(warnings) == 1
        assert warnings[0].id == monitor.id

    def test_mark_warning_sent_response(self, db_session):
        """测试标记响应预警已发送"""
        # 创建策略
        policy = SLAPolicy(
            problem_type="硬件故障",
            urgency="紧急",
            response_time_hours=2,
            resolve_time_hours=24,
            priority=1,
            is_active=True
        )
        db_session.add(policy)
        db_session.commit()

        # 创建工单
        ticket = ServiceTicket(
            title="测试工单",
            problem_type="硬件故障",
            urgency="紧急",
            reported_time=datetime(2023, 1, 1, 10, 0, 0)
        )
        db_session.add(ticket)
        db_session.commit()

        # 创建监控记录
        monitor = SLAMonitor(
            ticket_id=ticket.id,
            policy_id=policy.id,
            response_deadline=datetime(2023, 1, 1, 12, 0, 0),
            resolve_deadline=datetime(2023, 1, 2, 10, 0, 0),
            response_warning_sent=False,
            resolve_warning_sent=False
        )
        db_session.add(monitor)
        db_session.commit()

        # 标记响应预警已发送
        mark_warning_sent(db_session, monitor, "response")

        # 验证标记成功
        assert monitor.response_warning_sent is True
        assert monitor.response_warning_sent_at is not None
        assert monitor.resolve_warning_sent is False

    def test_mark_warning_sent_resolve(self, db_session):
        """测试标记解决预警已发送"""
        # 创建策略
        policy = SLAPolicy(
            problem_type="硬件故障",
            urgency="紧急",
            response_time_hours=2,
            resolve_time_hours=24,
            priority=1,
            is_active=True
        )
        db_session.add(policy)
        db_session.commit()

        # 创建工单
        ticket = ServiceTicket(
            title="测试工单",
            problem_type="硬件故障",
            urgency="紧急",
            reported_time=datetime(2023, 1, 1, 10, 0, 0)
        )
        db_session.add(ticket)
        db_session.commit()

        # 创建监控记录
        monitor = SLAMonitor(
            ticket_id=ticket.id,
            policy_id=policy.id,
            response_deadline=datetime(2023, 1, 1, 12, 0, 0),
            resolve_deadline=datetime(2023, 1, 2, 10, 0, 0),
            response_warning_sent=False,
            resolve_warning_sent=False
        )
        db_session.add(monitor)
        db_session.commit()

        # 标记解决预警已发送
        mark_warning_sent(db_session, monitor, "resolve")

        # 验证标记成功
        assert monitor.resolve_warning_sent is True
        assert monitor.resolve_warning_sent_at is not None
        assert monitor.response_warning_sent is False