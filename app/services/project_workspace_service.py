# -*- coding: utf-8 -*-
"""
项目工作空间服务
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import inspect, or_
from sqlalchemy.orm import Session, joinedload

from app.models.acceptance import AcceptanceOrder
from app.models.ecn import Ecn
from app.models.issue import Issue
from app.models.material import BomHeader, BomItem, Material
from app.models.presale import PresaleSolution, PresaleSupportTicket
from app.models.production import ProductionPlan, QualityInspection, WorkOrder
from app.models.project import Project, ProjectDocument, ProjectMember
from app.models.project_delivery import ProjectDeliverySchedule, ProjectDeliveryTask
from app.models.sales import Contract, Opportunity, Quote, QuoteVersion
from app.models.task_center import TaskUnified
from app.models.technical_review import TechnicalReview
from app.services.bonus.project_bonus_service import ProjectBonusService
from app.services.project_meeting_service import ProjectMeetingService
from app.services.project_solution_service import ProjectSolutionService


def _num(value: Any) -> Optional[float]:
    """Return JSON-safe number values while preserving missing data as null."""
    return float(value) if value is not None else None


def _dec(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _model_table_exists(db: Session, model: Any) -> bool:
    try:
        return inspect(db.get_bind()).has_table(model.__tablename__)
    except Exception:
        return False


def build_project_basic_info(project: Project) -> Dict[str, Any]:
    """
    构建项目基本信息

    Returns:
        Dict[str, Any]: 项目基本信息字典
    """
    return {
        "id": project.id,
        "project_code": project.project_code,
        "project_name": project.project_name,
        "stage": project.stage,
        "status": project.status,
        "health": project.health,
        "progress_pct": float(project.progress_pct or 0),
        "contract_amount": float(project.contract_amount or 0),
        "pm_name": project.pm_name,
    }


def build_team_info(db: Session, project_id: int) -> List[Dict[str, Any]]:
    """
    构建团队信息

    Returns:
        List[Dict[str, Any]]: 团队成员信息列表
    """
    members = (
        db.query(ProjectMember)
        .options(joinedload(ProjectMember.user))
        .filter(ProjectMember.project_id == project_id, ProjectMember.is_active)
        .all()
    )

    return [
        {
            "user_id": m.user_id,
            "user_name": m.user.real_name or m.user.username if m.user else f"user_{m.user_id}",
            "role_code": m.role_code,
            "allocation_pct": float(m.allocation_pct or 100),
            "start_date": m.start_date.isoformat() if m.start_date else None,
            "end_date": m.end_date.isoformat() if m.end_date else None,
        }
        for m in members
    ]


def build_task_info(db: Session, project_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """
    构建任务信息

    Returns:
        List[Dict[str, Any]]: 任务信息列表
    """
    tasks = db.query(TaskUnified).filter(TaskUnified.project_id == project_id).limit(limit).all()

    return [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "assignee_name": t.assignee_name,
            "plan_end_date": t.plan_end_date.isoformat() if t.plan_end_date else None,
            "progress": float(t.progress or 0),
        }
        for t in tasks
    ]


def build_bonus_info(db: Session, project_id: int) -> Dict[str, Any]:
    """
    构建奖金信息（带错误处理）

    Returns:
        Dict[str, Any]: 奖金信息字典
    """
    try:
        bonus_service = ProjectBonusService(db)
        bonus_rules = bonus_service.get_project_bonus_rules(project_id) or []
        bonus_calculations = bonus_service.get_project_bonus_calculations(project_id) or []
        bonus_distributions = bonus_service.get_project_bonus_distributions(project_id) or []
        bonus_statistics = bonus_service.get_project_bonus_statistics(project_id) or {}
        bonus_member_summary = bonus_service.get_project_member_bonus_summary(project_id) or []

        return {
            "rules": [
                {
                    "id": r.id,
                    "rule_name": r.rule_name,
                    "bonus_type": r.bonus_type,
                    "coefficient": float(r.coefficient or 0),
                }
                for r in bonus_rules
            ],
            "calculations": [
                {
                    "id": c.id,
                    "calculation_code": c.calculation_code,
                    "user_name": (
                        getattr(c.user, "real_name", None) or getattr(c.user, "username", None)
                        if hasattr(c, "user") and c.user
                        else "Unknown"
                    ),
                    "calculated_amount": float(c.calculated_amount or 0),
                    "status": c.status,
                    "calculated_at": (
                        c.calculated_at.isoformat()
                        if hasattr(c, "calculated_at") and c.calculated_at
                        else None
                    ),
                }
                for c in bonus_calculations[:20]  # 限制返回数量
            ],
            "distributions": [
                {
                    "id": d.id,
                    "user_name": (
                        getattr(d.user, "real_name", None) or getattr(d.user, "username", None)
                        if hasattr(d, "user") and d.user
                        else "Unknown"
                    ),
                    "distributed_amount": float(d.distributed_amount or 0),
                    "status": d.status,
                    "distributed_at": (
                        d.distributed_at.isoformat()
                        if hasattr(d, "distributed_at") and d.distributed_at
                        else None
                    ),
                }
                for d in bonus_distributions[:20]
            ],
            "statistics": bonus_statistics,
            "member_summary": bonus_member_summary,
        }
    except Exception as e:
        import logging

        logging.error(f"获取项目奖金数据失败: {str(e)}")
        return {
            "rules": [],
            "calculations": [],
            "distributions": [],
            "statistics": {},
            "member_summary": [],
        }


def build_meeting_info(db: Session, project_id: int) -> Dict[str, Any]:
    """
    构建会议信息（带错误处理）

    Returns:
        Dict[str, Any]: 会议信息字典
    """
    try:
        meeting_service = ProjectMeetingService(db)
        meetings = meeting_service.get_project_meetings(project_id) or []
        meeting_statistics = meeting_service.get_project_meeting_statistics(project_id) or {}

        return {
            "meetings": [
                {
                    "id": m.id,
                    "meeting_name": getattr(m, "meeting_name", ""),
                    "meeting_date": (
                        m.meeting_date.isoformat()
                        if hasattr(m, "meeting_date") and m.meeting_date
                        else None
                    ),
                    "rhythm_level": getattr(m, "rhythm_level", ""),
                    "status": getattr(m, "status", ""),
                    "organizer_name": getattr(m, "organizer_name", ""),
                    "minutes": getattr(m, "minutes", ""),
                    "has_minutes": bool(getattr(m, "minutes", "")),
                }
                for m in meetings[:20]
            ],
            "statistics": meeting_statistics,
        }
    except Exception as e:
        import logging

        logging.error(f"获取项目会议数据失败: {str(e)}")
        return {
            "meetings": [],
            "statistics": {},
        }


def serialize_project_workspace_issue(issue: Issue) -> Dict[str, Any]:
    """Serialize project issues for both workspace summary and issue tab."""
    return {
        "id": issue.id,
        "issue_no": issue.issue_no,
        "category": issue.category,
        "issue_type": issue.issue_type,
        "title": issue.title,
        "description": issue.description,
        "status": issue.status,
        "severity": issue.severity,
        "priority": issue.priority,
        "solution": issue.solution,
        "has_solution": bool(issue.solution),
        "assignee_id": issue.assignee_id,
        "assignee_name": issue.assignee_name,
        "due_date": issue.due_date.isoformat() if issue.due_date else None,
        "report_date": issue.report_date.isoformat() if issue.report_date else None,
        "impact_scope": issue.impact_scope,
        "impact_level": issue.impact_level,
        "is_blocking": bool(issue.is_blocking),
        "verified_at": issue.verified_at.isoformat() if issue.verified_at else None,
        "verified_by": issue.verified_by,
        "verified_by_name": issue.verified_by_name,
        "verified_result": issue.verified_result,
    }


def build_issue_info(db: Session, project_id: int, limit: int = 50) -> Dict[str, Any]:
    """
    构建问题信息

    Returns:
        Dict[str, Any]: 问题信息字典
    """
    issues = (
        db.query(Issue)
        .filter(Issue.project_id == project_id)
        .order_by(Issue.report_date.desc())
        .limit(limit)
        .all()
    )

    return {
        "issues": [serialize_project_workspace_issue(i) for i in issues],
    }


def build_solution_info(db: Session, project_id: int) -> Dict[str, Any]:
    """
    构建解决方案信息（带错误处理）

    Returns:
        Dict[str, Any]: 解决方案信息字典
    """
    try:
        solution_service = ProjectSolutionService(db)
        solutions = solution_service.get_project_solutions(project_id) or []
        solution_statistics = solution_service.get_project_solution_statistics(project_id) or {}

        return {
            "solutions": solutions[:20] if isinstance(solutions, list) else [],
            "statistics": solution_statistics,
        }
    except Exception as e:
        import logging

        logging.error(f"获取项目解决方案数据失败: {str(e)}")
        return {
            "solutions": [],
            "statistics": {},
        }


def build_document_info(db: Session, project_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """
    构建文档信息

    Returns:
        List[Dict[str, Any]]: 文档信息列表
    """
    documents = (
        db.query(ProjectDocument)
        .filter(ProjectDocument.project_id == project_id)
        .order_by(ProjectDocument.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": d.id,
            "doc_name": d.doc_name,
            "doc_type": d.doc_type,
            "version": d.version,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in documents
    ]


def _resolve_contract(db: Session, project: Project) -> Optional[Contract]:
    contract = project.contract
    if contract:
        return contract

    query = db.query(Contract)
    filters = [Contract.project_id == project.id]
    if project.opportunity_id:
        filters.append(Contract.opportunity_id == project.opportunity_id)

    return query.filter(or_(*filters)).order_by(Contract.id.desc()).first()


def _resolve_opportunity(project: Project, contract: Optional[Contract]) -> Optional[Opportunity]:
    if project.opportunity:
        return project.opportunity
    if contract and contract.opportunity:
        return contract.opportunity
    return None


def _resolve_quote_context(
    opportunity: Optional[Opportunity],
    contract: Optional[Contract],
) -> tuple[Optional[Quote], Optional[QuoteVersion]]:
    quote_version = contract.quote_version if contract else None
    quote = quote_version.quote if quote_version and quote_version.quote else None
    if quote:
        return quote, quote_version

    if opportunity and opportunity.quotes:
        quote = next((item for item in opportunity.quotes if item.current_version), None)
        quote = quote or opportunity.quotes[-1]
        quote_version = quote.current_version or (
            quote.versions[-1] if quote.versions else None
        )
        return quote, quote_version

    return None, quote_version


def _build_contract_payload(contract: Optional[Contract]) -> Optional[Dict[str, Any]]:
    if not contract:
        return None

    return {
        "id": contract.id,
        "contract_code": contract.contract_code,
        "contract_name": contract.contract_name,
        "contract_type": contract.contract_type,
        "customer_contract_no": contract.customer_contract_no,
        "status": contract.status,
        "total_amount": _num(contract.total_amount),
        "received_amount": _num(contract.received_amount),
        "unreceived_amount": _num(contract.unreceived_amount),
        "signing_date": contract.signing_date.isoformat() if contract.signing_date else None,
        "delivery_terms": contract.delivery_terms,
        "payment_terms": contract.payment_terms,
        "sales_owner_id": contract.sales_owner_id,
    }


def _build_opportunity_payload(opportunity: Optional[Opportunity]) -> Optional[Dict[str, Any]]:
    if not opportunity:
        return None

    return {
        "id": opportunity.id,
        "opp_code": opportunity.opp_code,
        "opp_name": opportunity.opp_name,
        "stage": opportunity.stage,
        "probability": opportunity.probability,
        "est_amount": _num(opportunity.est_amount),
        "est_margin": _num(opportunity.est_margin),
        "project_type": opportunity.project_type,
        "equipment_type": opportunity.equipment_type,
        "expected_close_date": (
            opportunity.expected_close_date.isoformat()
            if opportunity.expected_close_date
            else None
        ),
        "delivery_window": opportunity.delivery_window,
        "acceptance_basis": opportunity.acceptance_basis,
        "owner_id": opportunity.owner_id,
    }


def _build_quote_payload(
    quote: Optional[Quote],
    quote_version: Optional[QuoteVersion],
) -> Optional[Dict[str, Any]]:
    if not quote and not quote_version:
        return None

    payload = {
        "id": quote.id if quote else None,
        "quote_code": quote.quote_code if quote else None,
        "status": quote.status if quote else None,
        "valid_until": quote.valid_until.isoformat() if quote and quote.valid_until else None,
        "delivery_date": quote.delivery_date.isoformat() if quote and quote.delivery_date else None,
        "owner_id": quote.owner_id if quote else None,
        "version": None,
    }

    if quote_version:
        payload["version"] = {
            "id": quote_version.id,
            "version_no": quote_version.version_no,
            "total_price": _num(quote_version.total_price),
            "cost_total": _num(quote_version.cost_total),
            "gross_margin": _num(quote_version.gross_margin),
            "binding_status": quote_version.binding_status,
            "binding_warning": quote_version.binding_warning,
            "cost_breakdown_complete": bool(quote_version.cost_breakdown_complete),
            "margin_warning": bool(quote_version.margin_warning),
        }

    return payload


def _build_presale_solution_payload(solution: PresaleSolution) -> Dict[str, Any]:
    return {
        "id": solution.id,
        "solution_no": solution.solution_no,
        "name": solution.name,
        "solution_type": solution.solution_type,
        "industry": solution.industry,
        "test_type": solution.test_type,
        "ticket_id": solution.ticket_id,
        "project_id": solution.project_id,
        "customer_id": solution.customer_id,
        "opportunity_id": solution.opportunity_id,
        "status": solution.status,
        "review_status": solution.review_status,
        "requirement_summary": solution.requirement_summary,
        "solution_overview": solution.solution_overview,
        "technical_spec": solution.technical_spec,
        "estimated_cost": _num(solution.estimated_cost),
        "suggested_price": _num(solution.suggested_price),
        "estimated_hours": solution.estimated_hours,
        "estimated_duration": solution.estimated_duration,
        "author_name": solution.author_name,
        "updated_at": solution.updated_at.isoformat() if solution.updated_at else None,
    }


def _build_presale_ticket_payload(ticket: PresaleSupportTicket) -> Dict[str, Any]:
    pm_involvement_checked_at = getattr(ticket, "pm_involvement_checked_at", None)
    pm_assigned_at = getattr(ticket, "pm_assigned_at", None)

    return {
        "id": ticket.id,
        "ticket_no": ticket.ticket_no,
        "title": ticket.title,
        "ticket_type": ticket.ticket_type,
        "urgency": ticket.urgency,
        "status": ticket.status,
        "customer_id": ticket.customer_id,
        "customer_name": ticket.customer_name,
        "opportunity_id": ticket.opportunity_id,
        "project_id": ticket.project_id,
        "applicant_name": ticket.applicant_name,
        "assignee_name": ticket.assignee_name,
        "actual_hours": _num(ticket.actual_hours),
        "expected_date": ticket.expected_date.isoformat() if ticket.expected_date else None,
        "deadline": ticket.deadline.isoformat() if ticket.deadline else None,
        "complete_time": ticket.complete_time.isoformat() if ticket.complete_time else None,
        "satisfaction_score": ticket.satisfaction_score,
        "pm_involvement_required": bool(getattr(ticket, "pm_involvement_required", False)),
        "pm_involvement_risk_level": getattr(ticket, "pm_involvement_risk_level", None),
        "pm_involvement_risk_factors": getattr(ticket, "pm_involvement_risk_factors", None) or [],
        "pm_involvement_checked_at": (
            pm_involvement_checked_at.isoformat() if pm_involvement_checked_at else None
        ),
        "pm_assigned": bool(getattr(ticket, "pm_assigned", False)),
        "pm_user_id": getattr(ticket, "pm_user_id", None),
        "pm_assigned_at": pm_assigned_at.isoformat() if pm_assigned_at else None,
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
    }


def _get_presale_solutions(db: Session, project: Project, limit: int = 10) -> List[PresaleSolution]:
    ticket_ids = [
        row[0]
        for row in db.query(PresaleSupportTicket.id)
        .filter(PresaleSupportTicket.project_id == project.id)
        .all()
    ]

    filters = []
    filters.append(PresaleSolution.project_id == project.id)
    if project.opportunity_id:
        filters.append(PresaleSolution.opportunity_id == project.opportunity_id)
    if ticket_ids:
        filters.append(PresaleSolution.ticket_id.in_(ticket_ids))

    return (
        db.query(PresaleSolution)
        .filter(or_(*filters))
        .order_by(PresaleSolution.updated_at.desc(), PresaleSolution.id.desc())
        .limit(limit)
        .all()
    )


def _get_presale_tickets(
    db: Session,
    project: Project,
    presale_solutions: List[PresaleSolution],
    limit: int = 10,
) -> List[PresaleSupportTicket]:
    filters = [PresaleSupportTicket.project_id == project.id]
    if project.opportunity_id:
        filters.append(PresaleSupportTicket.opportunity_id == project.opportunity_id)

    solution_ticket_ids = {
        solution.ticket_id
        for solution in presale_solutions
        if getattr(solution, "ticket_id", None)
    }
    if solution_ticket_ids:
        filters.append(PresaleSupportTicket.id.in_(solution_ticket_ids))

    return (
        db.query(PresaleSupportTicket)
        .filter(or_(*filters))
        .order_by(PresaleSupportTicket.updated_at.desc(), PresaleSupportTicket.id.desc())
        .limit(limit)
        .all()
    )


def build_project_handover_context(db: Session, project: Project) -> Dict[str, Any]:
    """
    构建项目工作台上游交接上下文。

    这份数据是项目、采购、生产、验收、售后继续往下跑的共同入口，
    避免各后续模块重复拼销售/售前数据。
    """
    contract = _resolve_contract(db, project)
    opportunity = _resolve_opportunity(project, contract)
    quote, quote_version = _resolve_quote_context(opportunity, contract)
    presale_solutions = _get_presale_solutions(db, project)
    presale_tickets = _get_presale_tickets(db, project, presale_solutions)
    primary_solution = presale_solutions[0] if presale_solutions else None

    quote_cost_total = _num(quote_version.cost_total) if quote_version else None
    quote_total_price = _num(quote_version.total_price) if quote_version else None
    baseline_cost = {
        "project_budget_amount": _num(project.budget_amount),
        "project_contract_amount": _num(project.contract_amount),
        "contract_total_amount": _num(contract.total_amount) if contract else None,
        "quote_total_price": quote_total_price,
        "quote_cost_total": quote_cost_total,
        "quote_gross_margin": _num(quote_version.gross_margin) if quote_version else None,
        "presale_estimated_cost": _num(primary_solution.estimated_cost) if primary_solution else None,
        "presale_suggested_price": _num(primary_solution.suggested_price) if primary_solution else None,
        "source": (
            "quote_version"
            if quote_cost_total is not None
            else "presale_solution"
            if primary_solution and primary_solution.estimated_cost is not None
            else "project_budget"
            if project.budget_amount is not None
            else None
        ),
    }

    missing = []
    if not contract:
        missing.append("contract")
    if not opportunity:
        missing.append("opportunity")
    if not presale_solutions:
        missing.append("presale_solution")
    if (
        baseline_cost["quote_cost_total"] is None
        and baseline_cost["presale_estimated_cost"] is None
        and baseline_cost["project_budget_amount"] is None
    ):
        missing.append("baseline_cost")

    return {
        "project": build_project_basic_info(project),
        "contract": _build_contract_payload(contract),
        "opportunity": _build_opportunity_payload(opportunity),
        "quote": _build_quote_payload(quote, quote_version),
        "presale_tickets": [
            _build_presale_ticket_payload(ticket) for ticket in presale_tickets
        ],
        "presale_solutions": [
            _build_presale_solution_payload(solution) for solution in presale_solutions
        ],
        "baseline_cost": baseline_cost,
        "handover_status": {
            "ready": not missing,
            "missing": missing,
        },
    }


def _build_technical_review_payload(review: TechnicalReview) -> Dict[str, Any]:
    return {
        "id": review.id,
        "review_no": review.review_no,
        "review_type": review.review_type,
        "review_name": review.review_name,
        "status": review.status,
        "scheduled_date": review.scheduled_date.isoformat() if review.scheduled_date else None,
        "actual_date": review.actual_date.isoformat() if review.actual_date else None,
        "conclusion": review.conclusion,
        "conclusion_summary": review.conclusion_summary,
        "issue_count": {
            "a": review.issue_count_a or 0,
            "b": review.issue_count_b or 0,
            "c": review.issue_count_c or 0,
            "d": review.issue_count_d or 0,
        },
    }


def _build_ecn_payload(ecn: Ecn) -> Dict[str, Any]:
    return {
        "id": ecn.id,
        "ecn_no": ecn.ecn_no,
        "ecn_title": ecn.ecn_title,
        "ecn_type": ecn.ecn_type,
        "priority": ecn.priority,
        "urgency": ecn.urgency,
        "status": ecn.status,
        "cost_impact": _num(ecn.cost_impact),
        "schedule_impact_days": ecn.schedule_impact_days or 0,
        "approval_result": ecn.approval_result,
        "applied_at": ecn.applied_at.isoformat() if ecn.applied_at else None,
        "approved_at": ecn.approved_at.isoformat() if ecn.approved_at else None,
    }


def _build_bom_payload(bom: BomHeader) -> Dict[str, Any]:
    return {
        "id": bom.id,
        "bom_no": bom.bom_no,
        "bom_name": bom.bom_name,
        "version": bom.version,
        "is_latest": bool(bom.is_latest),
        "status": bom.status,
        "machine_id": bom.machine_id,
        "total_items": bom.total_items or 0,
        "total_amount": _num(bom.total_amount),
        "approved_at": bom.approved_at.isoformat() if bom.approved_at else None,
    }


def _calculate_project_kitting(db: Session, project_id: int) -> Dict[str, Any]:
    bom_items = (
        db.query(
            BomItem.id,
            BomItem.material_id,
            BomItem.material_code,
            BomItem.material_name,
            BomItem.specification,
            BomItem.quantity,
            BomItem.received_qty,
            BomItem.purchased_qty,
            BomItem.is_key_item,
        )
        .join(BomHeader, BomItem.bom_id == BomHeader.id)
        .filter(
            BomHeader.project_id == project_id,
            BomHeader.status != "DRAFT",
            BomHeader.is_latest.is_(True),
        )
        .all()
    )

    if not bom_items:
        return {
            "kitting_rate": 0.0,
            "total_items": 0,
            "kitted_items": 0,
            "shortage_items": 0,
            "shortage_details": [],
        }

    material_ids = {item.material_id for item in bom_items if item.material_id}
    stock_map: Dict[int, Decimal] = {}
    if material_ids:
        stock_rows = (
            db.query(Material.id, Material.current_stock)
            .filter(Material.id.in_(material_ids))
            .all()
        )
        stock_map = {row[0]: _dec(row[1]) for row in stock_rows}

    kitted_count = 0
    shortage_details: List[Dict[str, Any]] = []
    for item in bom_items:
        required_qty = _dec(item.quantity)
        received_qty = _dec(item.received_qty)
        stock_qty = stock_map.get(item.material_id, Decimal("0")) if item.material_id else Decimal("0")
        available_qty = received_qty + stock_qty

        if available_qty >= required_qty:
            kitted_count += 1
            continue

        purchased_qty = _dec(item.purchased_qty)
        shortage_qty = max(Decimal("0"), required_qty - available_qty)
        in_transit_qty = max(Decimal("0"), purchased_qty - received_qty)
        shortage_details.append(
            {
                "bom_item_id": item.id,
                "material_id": item.material_id,
                "material_code": item.material_code,
                "material_name": item.material_name,
                "specification": item.specification,
                "required_qty": float(required_qty),
                "received_qty": float(received_qty),
                "available_qty": float(available_qty),
                "shortage_qty": float(shortage_qty),
                "in_transit_qty": float(in_transit_qty),
                "is_key_item": bool(item.is_key_item),
                "expected_arrival_date": None,
            }
        )

    total_items = len(bom_items)
    kitting_rate = round(kitted_count / total_items * 100, 1) if total_items else 0.0
    shortage_details.sort(
        key=lambda item: (not item["is_key_item"], -item["shortage_qty"], item["material_code"])
    )
    return {
        "kitting_rate": kitting_rate,
        "total_items": total_items,
        "kitted_items": kitted_count,
        "shortage_items": total_items - kitted_count,
        "shortage_details": shortage_details,
    }


def _build_production_plan_payload(plan: ProductionPlan) -> Dict[str, Any]:
    return {
        "id": plan.id,
        "plan_no": plan.plan_no,
        "plan_name": plan.plan_name,
        "plan_type": plan.plan_type,
        "status": plan.status,
        "progress": float(plan.progress or 0),
        "plan_start_date": plan.plan_start_date.isoformat() if plan.plan_start_date else None,
        "plan_end_date": plan.plan_end_date.isoformat() if plan.plan_end_date else None,
        "approved_at": plan.approved_at.isoformat() if plan.approved_at else None,
    }


def _build_work_order_payload(order: WorkOrder) -> Dict[str, Any]:
    return {
        "id": order.id,
        "work_order_no": order.work_order_no,
        "task_name": order.task_name,
        "task_type": order.task_type,
        "status": order.status,
        "priority": order.priority,
        "progress": float(order.progress or 0),
        "plan_qty": order.plan_qty or 0,
        "completed_qty": order.completed_qty or 0,
        "qualified_qty": order.qualified_qty or 0,
        "defect_qty": order.defect_qty or 0,
        "plan_start_date": order.plan_start_date.isoformat() if order.plan_start_date else None,
        "plan_end_date": order.plan_end_date.isoformat() if order.plan_end_date else None,
    }


def _build_quality_inspection_payload(inspection: QualityInspection) -> Dict[str, Any]:
    return {
        "id": inspection.id,
        "inspection_no": inspection.inspection_no,
        "work_order_id": inspection.work_order_id,
        "inspection_type": inspection.inspection_type,
        "inspection_date": (
            inspection.inspection_date.isoformat() if inspection.inspection_date else None
        ),
        "inspection_qty": inspection.inspection_qty or 0,
        "qualified_qty": inspection.qualified_qty or 0,
        "defect_qty": inspection.defect_qty or 0,
        "inspection_result": inspection.inspection_result,
        "defect_rate": _num(inspection.defect_rate),
        "defect_type": inspection.defect_type,
        "defect_description": inspection.defect_description,
        "handling_result": inspection.handling_result,
    }


def _build_acceptance_order_payload(order: AcceptanceOrder) -> Dict[str, Any]:
    return {
        "id": order.id,
        "order_no": order.order_no,
        "acceptance_type": order.acceptance_type,
        "status": order.status,
        "planned_date": order.planned_date.isoformat() if order.planned_date else None,
        "actual_start_date": (
            order.actual_start_date.isoformat() if order.actual_start_date else None
        ),
        "actual_end_date": order.actual_end_date.isoformat() if order.actual_end_date else None,
        "total_items": order.total_items or 0,
        "passed_items": order.passed_items or 0,
        "failed_items": order.failed_items or 0,
        "pass_rate": _num(order.pass_rate),
        "overall_result": order.overall_result,
        "is_officially_completed": bool(order.is_officially_completed),
        "officially_completed_at": (
            order.officially_completed_at.isoformat()
            if order.officially_completed_at
            else None
        ),
    }


def _build_delivery_schedule_payload(schedule: ProjectDeliverySchedule) -> Dict[str, Any]:
    return {
        "id": schedule.id,
        "schedule_no": schedule.schedule_no,
        "schedule_name": schedule.schedule_name,
        "version": schedule.version,
        "status": schedule.status,
        "usage_type": schedule.usage_type,
        "is_active": bool(schedule.is_active),
        "is_pre_contract": bool(schedule.is_pre_contract),
        "confirmed_at": schedule.confirmed_at.isoformat() if schedule.confirmed_at else None,
    }


def _build_delivery_task_payload(task: ProjectDeliveryTask) -> Dict[str, Any]:
    return {
        "id": task.id,
        "task_no": task.task_no,
        "task_type": task.task_type,
        "task_name": task.task_name,
        "machine_name": task.machine_name,
        "module_name": task.module_name,
        "assigned_engineer_name": task.assigned_engineer_name,
        "planned_start": task.planned_start.isoformat() if task.planned_start else None,
        "planned_end": task.planned_end.isoformat() if task.planned_end else None,
        "status": task.status,
        "progress_pct": _num(task.progress_pct),
        "has_conflict": bool(task.has_conflict),
        "conflict_details": task.conflict_details,
    }


def build_project_downstream_context(db: Session, project: Project) -> Dict[str, Any]:
    """构建项目进入工程、供应链、生产、交付、验收后的最小上下文。"""
    review_query = db.query(TechnicalReview).filter(TechnicalReview.project_id == project.id)
    reviews = (
        review_query.order_by(TechnicalReview.scheduled_date.desc(), TechnicalReview.id.desc())
        .limit(10)
        .all()
    )
    open_review_count = sum(
        1
        for status, in review_query.with_entities(TechnicalReview.status).all()
        if str(status or "").upper() not in {"COMPLETED", "CANCELLED", "CLOSED"}
    )

    ecn_query = db.query(Ecn).filter(Ecn.project_id == project.id)
    ecns = ecn_query.order_by(Ecn.created_at.desc(), Ecn.id.desc()).limit(10).all()
    open_ecn_count = sum(
        1
        for status, in ecn_query.with_entities(Ecn.status).all()
        if str(status or "").upper() not in {"CLOSED", "CANCELLED", "REJECTED"}
    )

    bom_query = db.query(BomHeader).filter(BomHeader.project_id == project.id)
    boms = bom_query.order_by(BomHeader.is_latest.desc(), BomHeader.id.desc()).limit(10).all()
    kitting = _calculate_project_kitting(db, project.id)

    if _model_table_exists(db, ProductionPlan):
        plan_query = db.query(ProductionPlan).filter(ProductionPlan.project_id == project.id)
        production_plans = (
            plan_query.order_by(ProductionPlan.plan_start_date.desc(), ProductionPlan.id.desc())
            .limit(10)
            .all()
        )
        plan_total = plan_query.count()
        open_plan_count = sum(
            1
            for status, in plan_query.with_entities(ProductionPlan.status).all()
            if str(status or "").upper() not in {"COMPLETED", "CLOSED", "CANCELLED"}
        )
    else:
        production_plans = []
        plan_total = 0
        open_plan_count = 0

    if _model_table_exists(db, WorkOrder):
        work_order_query = db.query(WorkOrder).filter(WorkOrder.project_id == project.id)
        work_orders = (
            work_order_query.order_by(WorkOrder.plan_end_date.asc(), WorkOrder.id.desc())
            .limit(10)
            .all()
        )
        work_order_total = work_order_query.count()
        all_work_order_statuses = work_order_query.with_entities(
            WorkOrder.status,
            WorkOrder.progress,
        ).all()
        open_work_order_count = sum(
            1
            for status, _progress in all_work_order_statuses
            if str(status or "").upper() not in {"COMPLETED", "CLOSED", "CANCELLED"}
        )
        completed_work_order_count = sum(
            1
            for status, _progress in all_work_order_statuses
            if str(status or "").upper() == "COMPLETED"
        )
        avg_work_order_progress = (
            round(
                sum(float(progress or 0) for _status, progress in all_work_order_statuses)
                / len(all_work_order_statuses),
                1,
            )
            if all_work_order_statuses
            else 0.0
        )
    else:
        work_orders = []
        work_order_total = 0
        open_work_order_count = 0
        completed_work_order_count = 0
        avg_work_order_progress = 0.0

    if _model_table_exists(db, QualityInspection) and _model_table_exists(db, WorkOrder):
        quality_query = (
            db.query(QualityInspection)
            .join(WorkOrder, QualityInspection.work_order_id == WorkOrder.id)
            .filter(WorkOrder.project_id == project.id)
        )
        inspections = (
            quality_query.order_by(
                QualityInspection.inspection_date.desc(),
                QualityInspection.id.desc(),
            )
            .limit(10)
            .all()
        )
        quality_total = quality_query.count()
        quality_rows = quality_query.with_entities(
            QualityInspection.inspection_result,
            QualityInspection.defect_qty,
        ).all()
        failed_inspection_count = sum(
            1 for result, _defect_qty in quality_rows if str(result or "").upper() == "FAIL"
        )
        pending_inspection_count = sum(
            1 for result, _defect_qty in quality_rows if str(result or "").upper() == "PENDING"
        )
        total_defect_qty = sum(int(defect_qty or 0) for _result, defect_qty in quality_rows)
    else:
        inspections = []
        quality_total = 0
        failed_inspection_count = 0
        pending_inspection_count = 0
        total_defect_qty = 0

    if _model_table_exists(db, ProjectDeliverySchedule):
        delivery_schedule_query = db.query(ProjectDeliverySchedule).filter(
            ProjectDeliverySchedule.project_id == project.id
        )
        delivery_schedules = (
            delivery_schedule_query.order_by(
                ProjectDeliverySchedule.is_active.desc(),
                ProjectDeliverySchedule.id.desc(),
            )
            .limit(10)
            .all()
        )
        delivery_schedule_total = delivery_schedule_query.count()
        active_delivery_count = sum(
            1
            for is_active, in delivery_schedule_query.with_entities(
                ProjectDeliverySchedule.is_active
            ).all()
            if is_active
        )
    else:
        delivery_schedules = []
        delivery_schedule_total = 0
        active_delivery_count = 0

    delivery_schedule_ids = [schedule.id for schedule in delivery_schedules]
    if delivery_schedule_ids and _model_table_exists(db, ProjectDeliveryTask):
        delivery_task_query = db.query(ProjectDeliveryTask).filter(
            ProjectDeliveryTask.schedule_id.in_(delivery_schedule_ids)
        )
        delivery_tasks = (
            delivery_task_query.order_by(
                ProjectDeliveryTask.planned_end.asc(),
                ProjectDeliveryTask.id.desc(),
            )
            .limit(10)
            .all()
        )
        all_delivery_tasks = delivery_task_query.with_entities(
            ProjectDeliveryTask.status,
            ProjectDeliveryTask.progress_pct,
            ProjectDeliveryTask.has_conflict,
        ).all()
    else:
        delivery_tasks = []
        all_delivery_tasks = []
    open_delivery_task_count = sum(
        1
        for status, _progress, _has_conflict in all_delivery_tasks
        if str(status or "").upper() not in {"COMPLETED", "CLOSED", "CANCELLED"}
    )
    conflict_delivery_task_count = sum(
        1 for _status, _progress, has_conflict in all_delivery_tasks if has_conflict
    )
    avg_delivery_progress = (
        round(
            sum(float(progress or 0) for _status, progress, _has_conflict in all_delivery_tasks)
            / len(all_delivery_tasks),
            1,
        )
        if all_delivery_tasks
        else 0.0
    )

    if _model_table_exists(db, AcceptanceOrder):
        acceptance_query = db.query(AcceptanceOrder).filter(
            AcceptanceOrder.project_id == project.id
        )
        acceptance_orders = (
            acceptance_query.order_by(
                AcceptanceOrder.planned_date.asc(),
                AcceptanceOrder.id.desc(),
            )
            .limit(10)
            .all()
        )
        acceptance_total = acceptance_query.count()
        acceptance_rows = acceptance_query.with_entities(
            AcceptanceOrder.status,
            AcceptanceOrder.failed_items,
            AcceptanceOrder.is_officially_completed,
        ).all()
        open_acceptance_count = sum(
            1
            for status, _failed_items, is_officially_completed in acceptance_rows
            if not is_officially_completed
            and str(status or "").upper() not in {"COMPLETED", "CLOSED", "CANCELLED"}
        )
        failed_acceptance_item_count = sum(
            int(failed_items or 0) for _status, failed_items, _official in acceptance_rows
        )
    else:
        acceptance_orders = []
        acceptance_total = 0
        open_acceptance_count = 0
        failed_acceptance_item_count = 0

    next_actions: List[Dict[str, Any]] = []
    if kitting["shortage_items"] > 0:
        key_shortage_count = sum(1 for item in kitting["shortage_details"] if item["is_key_item"])
        next_actions.append(
            {
                "domain": "supply_chain",
                "priority": "HIGH" if key_shortage_count else "MEDIUM",
                "title": "处理项目缺料",
                "href": f"/material-analysis?project_id={project.id}",
                "description": (
                    f"当前齐套率 {kitting['kitting_rate']}%，"
                    f"{kitting['shortage_items']} 项缺料"
                    + (f"，其中 {key_shortage_count} 项关键物料" if key_shortage_count else "")
                ),
            }
        )
    if open_ecn_count > 0:
        next_actions.append(
            {
                "domain": "engineering",
                "priority": "HIGH",
                "title": "关闭未完成 ECN",
                "href": f"/ecn?project_id={project.id}",
                "description": f"项目仍有 {open_ecn_count} 个 ECN 未关闭",
            }
        )
    if open_review_count > 0:
        next_actions.append(
            {
                "domain": "engineering",
                "priority": "MEDIUM",
                "title": "推进技术评审闭环",
                "href": f"/technical-reviews?project_id={project.id}",
                "description": f"项目仍有 {open_review_count} 个技术评审未完成",
            }
        )
    if open_work_order_count > 0:
        next_actions.append(
            {
                "domain": "production",
                "priority": "HIGH" if avg_work_order_progress < 50 else "MEDIUM",
                "title": "推进生产/装配工单",
                "href": f"/work-orders?project_id={project.id}",
                "description": (
                    f"项目仍有 {open_work_order_count} 个生产/装配工单未完成，"
                    f"平均进度 {avg_work_order_progress}%"
                ),
            }
        )
    if failed_inspection_count > 0:
        next_actions.append(
            {
                "domain": "quality",
                "priority": "HIGH",
                "title": "处理质检不合格项",
                "href": f"/quality/inspections?project_id={project.id}",
                "description": (
                    f"项目有 {failed_inspection_count} 条质检不合格记录，"
                    f"不良数量 {total_defect_qty}"
                ),
            }
        )
    if conflict_delivery_task_count > 0:
        next_actions.append(
            {
                "domain": "delivery",
                "priority": "HIGH",
                "title": "解决交付排产冲突",
                "href": f"/projects/{project.id}/delivery",
                "description": f"项目交付计划中有 {conflict_delivery_task_count} 个任务存在冲突",
            }
        )
    elif open_delivery_task_count > 0:
        next_actions.append(
            {
                "domain": "delivery",
                "priority": "MEDIUM",
                "title": "推进交付计划任务",
                "href": f"/projects/{project.id}/delivery",
                "description": f"项目仍有 {open_delivery_task_count} 个交付任务未完成",
            }
        )
    if open_acceptance_count > 0:
        next_actions.append(
            {
                "domain": "acceptance",
                "priority": "HIGH" if failed_acceptance_item_count else "MEDIUM",
                "title": "推进验收闭环",
                "href": f"/quality/acceptance?project_id={project.id}",
                "description": (
                    f"项目仍有 {open_acceptance_count} 个验收单未完成"
                    + (
                        f"，存在 {failed_acceptance_item_count} 个未通过检查项"
                        if failed_acceptance_item_count
                        else ""
                    )
                ),
            }
        )

    return {
        "project": build_project_basic_info(project),
        "engineering": {
            "technical_reviews": {
                "items": [_build_technical_review_payload(review) for review in reviews],
                "total": review_query.count(),
                "open_count": open_review_count,
            },
            "ecns": {
                "items": [_build_ecn_payload(ecn) for ecn in ecns],
                "total": ecn_query.count(),
                "open_count": open_ecn_count,
            },
        },
        "supply_chain": {
            "bom": {
                "items": [_build_bom_payload(bom) for bom in boms],
                "total": bom_query.count(),
                "latest_count": sum(1 for bom in boms if bom.is_latest),
            },
            "kitting": kitting,
        },
        "production": {
            "plans": {
                "items": [_build_production_plan_payload(plan) for plan in production_plans],
                "total": plan_total,
                "open_count": open_plan_count,
            },
            "work_orders": {
                "items": [_build_work_order_payload(order) for order in work_orders],
                "total": work_order_total,
                "completed_count": completed_work_order_count,
                "open_count": open_work_order_count,
                "avg_progress": avg_work_order_progress,
            },
        },
        "quality": {
            "inspections": {
                "items": [
                    _build_quality_inspection_payload(inspection)
                    for inspection in inspections
                ],
                "total": quality_total,
                "failed_count": failed_inspection_count,
                "pending_count": pending_inspection_count,
                "defect_qty": total_defect_qty,
            },
        },
        "delivery": {
            "schedules": {
                "items": [
                    _build_delivery_schedule_payload(schedule)
                    for schedule in delivery_schedules
                ],
                "total": delivery_schedule_total,
                "active_count": active_delivery_count,
            },
            "tasks": {
                "items": [_build_delivery_task_payload(task) for task in delivery_tasks],
                "total": len(all_delivery_tasks),
                "open_count": open_delivery_task_count,
                "conflict_count": conflict_delivery_task_count,
                "avg_progress": avg_delivery_progress,
            },
        },
        "acceptance": {
            "orders": {
                "items": [
                    _build_acceptance_order_payload(order)
                    for order in acceptance_orders
                ],
                "total": acceptance_total,
                "open_count": open_acceptance_count,
                "failed_items": failed_acceptance_item_count,
            },
        },
        "next_actions": next_actions,
    }
