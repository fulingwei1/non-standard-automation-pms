# -*- coding: utf-8 -*-
"""
售前工单管理 - 工具函数
"""
from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common.query_filters import apply_like_filter
from app.models.presale import PresaleSolution, PresaleSupportTicket, PresaleTenderRecord
from app.schemas.presale import TicketResponse


def generate_ticket_no(db: Session) -> str:
    """生成工单编号：TICKET-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_ticket_query = db.query(PresaleSupportTicket)
    max_ticket_query = apply_like_filter(
        max_ticket_query,
        PresaleSupportTicket,
        f"TICKET-{today}-%",
        "ticket_no",
        use_ilike=False,
    )
    max_ticket = max_ticket_query.order_by(desc(PresaleSupportTicket.ticket_no)).first()
    if max_ticket:
        seq = int(max_ticket.ticket_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"TICKET-{today}-{seq:03d}"


def generate_solution_no(db: Session) -> str:
    """生成方案编号：SOL-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_solution_query = db.query(PresaleSolution)
    max_solution_query = apply_like_filter(
        max_solution_query,
        PresaleSolution,
        f"SOL-{today}-%",
        "solution_no",
        use_ilike=False,
    )
    max_solution = max_solution_query.order_by(desc(PresaleSolution.solution_no)).first()
    if max_solution:
        seq = int(max_solution.solution_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"SOL-{today}-{seq:03d}"


def generate_tender_no(db: Session) -> str:
    """生成投标编号：TENDER-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_tender_query = db.query(PresaleTenderRecord)
    max_tender_query = apply_like_filter(
        max_tender_query,
        PresaleTenderRecord,
        f"TENDER-{today}-%",
        "tender_no",
        use_ilike=False,
    )
    max_tender = max_tender_query.order_by(desc(PresaleTenderRecord.tender_no)).first()
    if max_tender:
        seq = int(max_tender.tender_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"TENDER-{today}-{seq:03d}"


def build_ticket_response(ticket: PresaleSupportTicket) -> TicketResponse:
    """构建工单响应对象"""
    return TicketResponse(
        id=ticket.id,
        ticket_no=ticket.ticket_no,
        title=ticket.title,
        ticket_type=ticket.ticket_type,
        urgency=ticket.urgency,
        description=ticket.description,
        customer_id=ticket.customer_id,
        customer_name=ticket.customer_name,
        opportunity_id=ticket.opportunity_id,
        project_id=ticket.project_id,
        applicant_id=ticket.applicant_id,
        applicant_name=ticket.applicant_name,
        applicant_dept=ticket.applicant_dept,
        apply_time=ticket.apply_time,
        assignee_id=ticket.assignee_id,
        assignee_name=ticket.assignee_name,
        accept_time=ticket.accept_time,
        expected_date=ticket.expected_date,
        deadline=ticket.deadline,
        status=ticket.status,
        complete_time=ticket.complete_time,
        actual_hours=float(ticket.actual_hours) if ticket.actual_hours else None,
        satisfaction_score=ticket.satisfaction_score,
        feedback=ticket.feedback,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )
