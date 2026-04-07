# -*- coding: utf-8 -*-
"""
ITR 流程服务
整合工单、问题、验收数据，提供端到端流程视图
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import and_, desc, exc, or_
from sqlalchemy.orm import Session

from app.common.query_filters import apply_keyword_filter
from app.core.config import settings
from app.models.acceptance import AcceptanceOrder
from app.models.issue import Issue
from app.models.service import ServiceTicket
from app.models.sla import SLAMonitor

logger = logging.getLogger(__name__)


def _apply_query_timeout(query):
    """
    为查询应用超时保护
    使用 statement_timeout 防止慢查询阻塞
    """
    try:
        return query.execution_options(statement_timeout=settings.ITR_QUERY_TIMEOUT_SECONDS * 1000)
    except Exception as e:
        logger.warning(f"无法设置查询超时：{e}")
        return query


def get_ticket_timeline(db: Session, ticket_id: int) -> Dict[str, Any]:
    """
    获取工单完整时间线
    整合工单、问题、验收、SLA 监控等数据
    """
    # 空指针检查
    if not db or not ticket_id:
        return None

    try:
        ticket = _apply_query_timeout(db.query(ServiceTicket)).filter(
            ServiceTicket.id == ticket_id
        ).first()
    except exc.SQLAlchemyError as e:
        logger.error(f"查询工单失败：{e}")
        return None
    if not ticket:
        return None

    timeline = []

    # 1. 工单时间线（从 timeline 字段）
    if ticket.timeline:
        for item in ticket.timeline:
            timeline.append(
                {
                    "type": "TICKET",
                    "event_type": item.get("type", "UNKNOWN"),
                    "timestamp": item.get("timestamp"),
                    "user": item.get("user"),
                    "description": item.get("description"),
                    "source": "service_ticket",
                }
            )

    # 2. 关联问题 - 限制查询数量并使用配置参数
    issue_filters = [and_(Issue.project_id == ticket.project_id, Issue.category == "CUSTOMER")]
    if ticket.ticket_no:
        description_query = apply_keyword_filter(
            db.query(Issue.id),
            Issue,
            ticket.ticket_no,
            "description",
            use_ilike=False,
        )
        issue_filters.append(Issue.id.in_(description_query))

    # 性能优化：限制查询数量 + 超时保护
    try:
        issues = (
            _apply_query_timeout(db.query(Issue))
            .filter(or_(*issue_filters))
            .order_by(Issue.report_date)
            .limit(settings.ITR_TIMELINE_ISSUE_LIMIT)
            .all()
        )
    except exc.SQLAlchemyError as e:
        logger.error(f"查询关联问题失败：{e}")
        issues = []

    for issue in issues:
        # 空指针检查
        if not issue:
            continue

        timeline.append(
            {
                "type": "ISSUE",
                "event_type": "ISSUE_CREATED",
                "timestamp": issue.report_date.isoformat() if issue.report_date else None,
                "user": issue.reporter_name,
                "description": f"问题：{issue.title}",
                "issue_no": issue.issue_no,
                "issue_id": issue.id,
                "source": "issue",
            }
        )

        if issue.resolved_at:
            timeline.append(
                {
                    "type": "ISSUE",
                    "event_type": "ISSUE_RESOLVED",
                    "timestamp": issue.resolved_at.isoformat() if issue.resolved_at else None,
                    "user": issue.resolved_by_name,
                    "description": f"问题已解决：{issue.title}",
                    "issue_no": issue.issue_no,
                    "issue_id": issue.id,
                    "source": "issue",
                }
            )

    # 3. 关联验收单 - 限制查询数量并使用配置参数 + 超时保护
    try:
        acceptance_orders = (
            _apply_query_timeout(db.query(AcceptanceOrder))
            .filter(AcceptanceOrder.project_id == ticket.project_id)
            .order_by(AcceptanceOrder.created_at)
            .limit(settings.ITR_TIMELINE_ACCEPTANCE_LIMIT)
            .all()
        )
    except exc.SQLAlchemyError as e:
        logger.error(f"查询验收单失败：{e}")
        acceptance_orders = []

    for order in acceptance_orders:
        # 空指针检查
        if not order:
            continue

        timeline.append(
            {
                "type": "ACCEPTANCE",
                "event_type": "ACCEPTANCE_CREATED",
                "timestamp": order.created_at.isoformat() if order.created_at else None,
                "user": None,
                "description": f"验收单：{order.order_no} ({order.acceptance_type})",
                "order_no": order.order_no,
                "order_id": order.id,
                "source": "acceptance",
            }
        )

        if order.customer_signed_at:
            timeline.append(
                {
                    "type": "ACCEPTANCE",
                    "event_type": "ACCEPTANCE_SIGNED",
                    "timestamp": (
                        order.customer_signed_at.isoformat() if order.customer_signed_at else None
                    ),
                    "user": order.customer_signer,
                    "description": f"客户签字确认：{order.order_no}",
                    "order_no": order.order_no,
                    "order_id": order.id,
                    "source": "acceptance",
                }
            )

    # 4. SLA 监控记录 + 超时保护
    try:
        sla_monitor = _apply_query_timeout(db.query(SLAMonitor)).filter(
            SLAMonitor.ticket_id == ticket_id
        ).first()
    except exc.SQLAlchemyError as e:
        logger.error(f"查询 SLA 监控失败：{e}")
        sla_monitor = None
    if sla_monitor:
        timeline.append(
            {
                "type": "SLA",
                "event_type": "SLA_MONITOR_CREATED",
                "timestamp": sla_monitor.created_at.isoformat() if sla_monitor.created_at else None,
                "user": None,
                "description": f"SLA 监控：响应截止 {sla_monitor.response_deadline.strftime('%Y-%m-%d %H:%M') if sla_monitor.response_deadline else None}，解决截止 {sla_monitor.resolve_deadline.strftime('%Y-%m-%d %H:%M') if sla_monitor.resolve_deadline else None}",
                "policy_name": sla_monitor.policy.policy_name if sla_monitor.policy else None,
                "source": "sla",
            }
        )

        if sla_monitor.actual_response_time:
            timeline.append(
                {
                    "type": "SLA",
                    "event_type": "SLA_RESPONSE",
                    "timestamp": (
                        sla_monitor.actual_response_time.isoformat()
                        if sla_monitor.actual_response_time
                        else None
                    ),
                    "user": None,
                    "description": f"SLA 响应：{'按时' if sla_monitor.response_status == 'ON_TIME' else '超时'}",
                    "status": sla_monitor.response_status,
                    "source": "sla",
                }
            )

        if sla_monitor.actual_resolve_time:
            timeline.append(
                {
                    "type": "SLA",
                    "event_type": "SLA_RESOLVE",
                    "timestamp": (
                        sla_monitor.actual_resolve_time.isoformat()
                        if sla_monitor.actual_resolve_time
                        else None
                    ),
                    "user": None,
                    "description": f"SLA 解决：{'按时' if sla_monitor.resolve_status == 'ON_TIME' else '超时'}",
                    "status": sla_monitor.resolve_status,
                    "source": "sla",
                }
            )

    # 按时间排序
    timeline.sort(key=lambda x: x.get("timestamp") or "", reverse=False)

    return {
        "ticket_id": ticket.id,
        "ticket_no": ticket.ticket_no,
        "timeline": timeline,
        "total_events": len(timeline),
    }


def get_issue_related_data(db: Session, issue_id: int) -> Dict[str, Any]:
    """
    获取问题关联数据（工单、验收单等）
    """
    # 空指针检查
    if not db or not issue_id:
        return None

    try:
        issue = _apply_query_timeout(db.query(Issue)).filter(Issue.id == issue_id).first()
    except exc.SQLAlchemyError as e:
        logger.error(f"查询问题失败：{e}")
        return None
    if not issue:
        return None

    related_data = {
        "issue": {
            "id": issue.id,
            "issue_no": issue.issue_no,
            "title": issue.title,
            "status": issue.status,
            "category": issue.category,
        },
        "related_tickets": [],
        "related_acceptance": [],
        "related_issues": [],
    }

    # 关联工单（通过项目 ID）- 使用配置参数限制数量 + 超时保护
    if issue.project_id:
        try:
            tickets = (
                _apply_query_timeout(db.query(ServiceTicket))
                .filter(ServiceTicket.project_id == issue.project_id)
                .order_by(desc(ServiceTicket.created_at))
                .limit(settings.ITR_RELATED_TICKET_LIMIT)
                .all()
            )
        except exc.SQLAlchemyError as e:
            logger.error(f"查询关联工单失败：{e}")
            tickets = []

        for ticket in tickets:
            # 空指针检查
            if not ticket:
                continue

            related_data["related_tickets"].append(
                {
                    "id": ticket.id,
                    "ticket_no": ticket.ticket_no,
                    "problem_type": ticket.problem_type,
                    "urgency": ticket.urgency,
                    "status": ticket.status,
                    "reported_time": (
                        ticket.reported_time.isoformat() if ticket.reported_time else None
                    ),
                }
            )

    # 关联验收单（通过项目 ID 或验收单 ID）- 使用配置参数限制数量 + 超时保护
    if issue.acceptance_order_id:
        try:
            order = _apply_query_timeout(db.query(AcceptanceOrder)).filter(
                AcceptanceOrder.id == issue.acceptance_order_id
            ).first()
        except exc.SQLAlchemyError as e:
            logger.error(f"查询验收单失败：{e}")
            order = None
        if order:
            related_data["related_acceptance"].append(
                {
                    "id": order.id,
                    "order_no": order.order_no,
                    "acceptance_type": order.acceptance_type,
                    "status": order.status,
                    "overall_result": order.overall_result,
                }
            )
    elif issue.project_id:
        try:
            orders = (
                _apply_query_timeout(db.query(AcceptanceOrder))
                .filter(AcceptanceOrder.project_id == issue.project_id)
                .order_by(desc(AcceptanceOrder.created_at))
                .limit(settings.ITR_RELATED_ACCEPTANCE_LIMIT)
                .all()
            )
        except exc.SQLAlchemyError as e:
            logger.error(f"查询关联验收单失败：{e}")
            orders = []

        for order in orders:
            # 空指针检查
            if not order:
                continue

            related_data["related_acceptance"].append(
                {
                    "id": order.id,
                    "order_no": order.order_no,
                    "acceptance_type": order.acceptance_type,
                    "status": order.status,
                    "overall_result": order.overall_result,
                }
            )

    # 关联问题（父子问题、同项目问题）- 空指针检查 + 超时保护
    if issue.related_issue_id:
        try:
            related_issue = _apply_query_timeout(db.query(Issue)).filter(
                Issue.id == issue.related_issue_id
            ).first()
        except exc.SQLAlchemyError as e:
            logger.error(f"查询关联问题失败：{e}")
            related_issue = None
        if related_issue:
            related_data["related_issues"].append(
                {
                    "id": related_issue.id,
                    "issue_no": related_issue.issue_no,
                    "title": related_issue.title,
                    "status": related_issue.status,
                    "relation": "parent",
                }
            )

    # 查找子问题 - 使用配置参数限制数量 + 超时保护
    try:
        child_issues = (
            _apply_query_timeout(db.query(Issue))
            .filter(Issue.related_issue_id == issue_id)
            .limit(settings.ITR_RELATED_ISSUE_LIMIT)
            .all()
        )
    except exc.SQLAlchemyError as e:
        logger.error(f"查询子问题失败：{e}")
        child_issues = []
    for child in child_issues:
        # 空指针检查
        if not child:
            continue

        related_data["related_issues"].append(
            {
                "id": child.id,
                "issue_no": child.issue_no,
                "title": child.title,
                "status": child.status,
                "relation": "child",
            }
        )

    return related_data


def get_itr_dashboard_data(
    db: Session,
    project_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    获取 ITR 流程看板数据
    """
    # 空指针检查
    if not db:
        return None

    # 工单统计
    ticket_query = db.query(ServiceTicket)
    if project_id:
        ticket_query = ticket_query.filter(ServiceTicket.project_id == project_id)
    if start_date:
        ticket_query = ticket_query.filter(ServiceTicket.created_at >= start_date)
    if end_date:
        ticket_query = ticket_query.filter(ServiceTicket.created_at <= end_date)

    total_tickets = ticket_query.count()
    pending_tickets = ticket_query.filter(ServiceTicket.status == "PENDING").count()
    in_progress_tickets = ticket_query.filter(ServiceTicket.status == "IN_PROGRESS").count()
    resolved_tickets = ticket_query.filter(ServiceTicket.status == "RESOLVED").count()
    closed_tickets = ticket_query.filter(ServiceTicket.status == "CLOSED").count()

    # 问题统计
    issue_query = db.query(Issue).filter(Issue.category == "CUSTOMER")
    if project_id:
        issue_query = issue_query.filter(Issue.project_id == project_id)
    if start_date:
        issue_query = issue_query.filter(Issue.report_date >= start_date)
    if end_date:
        issue_query = issue_query.filter(Issue.report_date <= end_date)

    total_issues = issue_query.count()
    open_issues = issue_query.filter(Issue.status == "OPEN").count()
    processing_issues = issue_query.filter(Issue.status == "PROCESSING").count()
    resolved_issues = issue_query.filter(Issue.status == "RESOLVED").count()
    closed_issues = issue_query.filter(Issue.status == "CLOSED").count()

    # 验收统计
    acceptance_query = db.query(AcceptanceOrder)
    if project_id:
        acceptance_query = acceptance_query.filter(AcceptanceOrder.project_id == project_id)
    if start_date:
        acceptance_query = acceptance_query.filter(AcceptanceOrder.created_at >= start_date)
    if end_date:
        acceptance_query = acceptance_query.filter(AcceptanceOrder.created_at <= end_date)

    total_acceptance = acceptance_query.count()
    passed_acceptance = acceptance_query.filter(AcceptanceOrder.overall_result == "PASSED").count()
    failed_acceptance = acceptance_query.filter(AcceptanceOrder.overall_result == "FAILED").count()

    # SLA 统计
    sla_query = db.query(SLAMonitor).join(ServiceTicket)
    if project_id:
        sla_query = sla_query.filter(ServiceTicket.project_id == project_id)
    if start_date:
        sla_query = sla_query.filter(SLAMonitor.created_at >= start_date)
    if end_date:
        sla_query = sla_query.filter(SLAMonitor.created_at <= end_date)

    total_sla_monitors = sla_query.count()
    response_on_time = sla_query.filter(SLAMonitor.response_status == "ON_TIME").count()
    response_overdue = sla_query.filter(SLAMonitor.response_status == "OVERDUE").count()
    resolve_on_time = sla_query.filter(SLAMonitor.resolve_status == "ON_TIME").count()
    resolve_overdue = sla_query.filter(SLAMonitor.resolve_status == "OVERDUE").count()

    return {
        "tickets": {
            "total": total_tickets,
            "pending": pending_tickets,
            "in_progress": in_progress_tickets,
            "resolved": resolved_tickets,
            "closed": closed_tickets,
        },
        "issues": {
            "total": total_issues,
            "open": open_issues,
            "processing": processing_issues,
            "resolved": resolved_issues,
            "closed": closed_issues,
        },
        "acceptance": {
            "total": total_acceptance,
            "passed": passed_acceptance,
            "failed": failed_acceptance,
        },
        "sla": {
            "total": total_sla_monitors,
            "response_on_time": response_on_time,
            "response_overdue": response_overdue,
            "resolve_on_time": resolve_on_time,
            "resolve_overdue": resolve_overdue,
            "response_rate": (
                (response_on_time / total_sla_monitors * 100) if total_sla_monitors > 0 else 0
            ),
            "resolve_rate": (
                (resolve_on_time / total_sla_monitors * 100) if total_sla_monitors > 0 else 0
            ),
        },
    }
