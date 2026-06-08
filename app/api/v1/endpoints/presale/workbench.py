# -*- coding: utf-8 -*-
"""售前工作台聚合接口。"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.api.v1.endpoints.presale.bids import build_tender_response
from app.api.v1.endpoints.presale.proposals import build_solution_response
from app.api.v1.endpoints.presale.tickets.utils import build_ticket_response
from app.core import security
from app.models.presale import (
    PresaleSolution,
    PresaleSupportTicket,
    PresaleTenderRecord,
    TechnicalParameterTemplate,
)
from app.models.sales import (
    AIClarification,
    AssessmentRisk,
    AssessmentTemplate,
    AssessmentVersion,
    Contract,
    Lead,
    OpenItem,
    Opportunity,
    Quote,
    RequirementFreeze,
    TechnicalAssessment,
)
from app.models.enums import OpenItemStatusEnum
from app.models.sales.sales_funnel import (
    FunnelTransitionLog,
    GateTypeEnum,
    SalesFunnelStage,
    StageDwellTimeAlert,
    StageGateConfig,
)
from app.models.sales.technical_assessment import LeadRequirementDetail
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.sales.gate_validators import GateValidatorFactory

router = APIRouter()


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def _model_to_dict(model: Any, *, only: Optional[list[str]] = None) -> dict[str, Any]:
    if model is None:
        return {}

    column_names = [column.name for column in model.__table__.columns]
    if only is not None:
        column_names = [name for name in only if name in column_names]

    return {name: _json_value(getattr(model, name, None)) for name in column_names}


def _page_payload(items: list[Any], total: int, page: int = 1, page_size: int = 20) -> dict:
    pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


def _dump_response(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return model.dict()


def _ticket_payload(ticket: PresaleSupportTicket) -> dict[str, Any]:
    return _dump_response(build_ticket_response(ticket))


def _solution_payload(db: Session, solution: PresaleSolution) -> dict[str, Any]:
    return _dump_response(build_solution_response(db, solution))


def _tender_payload(tender: PresaleTenderRecord) -> dict[str, Any]:
    return _dump_response(build_tender_response(tender))


def _opportunity_payload(opportunity: Opportunity) -> dict[str, Any]:
    data = _model_to_dict(
        opportunity,
        only=[
            "id",
            "opp_code",
            "lead_id",
            "customer_id",
            "opp_name",
            "project_type",
            "equipment_type",
            "stage",
            "probability",
            "est_amount",
            "est_margin",
            "expected_close_date",
            "budget_range",
            "decision_chain",
            "delivery_window",
            "acceptance_basis",
            "score",
            "risk_level",
            "owner_id",
            "updated_by",
            "gate_status",
            "gate_passed_at",
            "assessment_id",
            "requirement_maturity",
            "assessment_status",
            "priority_score",
            "created_at",
            "updated_at",
        ],
    )
    customer = getattr(opportunity, "customer", None)
    owner = getattr(opportunity, "owner", None)
    updater = getattr(opportunity, "updater", None)
    data["customer_name"] = getattr(customer, "customer_name", None) if customer else None
    data["owner_name"] = (
        getattr(owner, "real_name", None) or getattr(owner, "username", None)
        if owner
        else None
    )
    data["updated_by_name"] = (
        getattr(updater, "real_name", None) or getattr(updater, "username", None)
        if updater
        else None
    )
    return data


def _quote_version_payload(version: Any) -> Optional[dict[str, Any]]:
    if version is None:
        return None

    return _model_to_dict(
        version,
        only=[
            "id",
            "quote_id",
            "version_no",
            "total_price",
            "cost_total",
            "gross_margin",
            "lead_time_days",
            "delivery_date",
            "binding_status",
            "binding_warning",
            "created_at",
            "updated_at",
        ],
    )


def _quote_payload(quote: Quote) -> dict[str, Any]:
    data = _model_to_dict(
        quote,
        only=[
            "id",
            "quote_code",
            "opportunity_id",
            "customer_id",
            "status",
            "current_version_id",
            "valid_until",
            "delivery_date",
            "owner_id",
            "created_at",
            "updated_at",
        ],
    )
    owner = getattr(quote, "owner", None)
    data["owner_name"] = (
        getattr(owner, "real_name", None) or getattr(owner, "username", None)
        if owner
        else None
    )
    data["current_version"] = _quote_version_payload(getattr(quote, "current_version", None))
    return data


def _costing_payload(solutions: list[PresaleSolution]) -> dict[str, Any]:
    baseline_solution = next(
        (
            solution
            for solution in solutions
            if solution.estimated_cost is not None or solution.suggested_price is not None
        ),
        None,
    )
    if baseline_solution is None:
        return {"baseline": None}

    estimated_cost = baseline_solution.estimated_cost
    suggested_price = baseline_solution.suggested_price
    gross_margin_rate = None
    if estimated_cost is not None and suggested_price:
        gross_margin_rate = float((Decimal(suggested_price) - Decimal(estimated_cost)) / Decimal(suggested_price))

    return {
        "baseline": {
            "source": "solution",
            "solution_id": baseline_solution.id,
            "solution_no": baseline_solution.solution_no,
            "solution_name": baseline_solution.name,
            "estimated_cost": _json_value(estimated_cost),
            "suggested_price": _json_value(suggested_price),
            "cost_breakdown": _json_value(baseline_solution.cost_breakdown),
            "gross_margin_rate": gross_margin_rate,
        }
    }


def _assessment_payload(assessment: TechnicalAssessment) -> dict[str, Any]:
    data = _model_to_dict(
        assessment,
        only=[
            "id",
            "source_type",
            "source_id",
            "evaluator_id",
            "status",
            "total_score",
            "dimension_scores",
            "veto_triggered",
            "veto_rules",
            "decision",
            "risks",
            "similar_cases",
            "ai_analysis",
            "conditions",
            "evaluated_at",
            "presale_ticket_id",
            "template_id",
            "version_no",
            "is_latest",
            "created_at",
            "updated_at",
        ],
    )
    evaluator = getattr(assessment, "evaluator", None)
    data["evaluator_name"] = (
        (getattr(evaluator, "real_name", None) or getattr(evaluator, "username", None))
        if evaluator
        else None
    )
    return data


def _prioritize_ticket_assessment(
    db: Session,
    assessments: list[TechnicalAssessment],
    ticket: Optional[PresaleSupportTicket],
) -> list[TechnicalAssessment]:
    """让工作台当前评估跟随当前售前工单，而不是同源对象的最新评估。"""
    if not ticket:
        return assessments

    preferred_assessment = None
    current_assessment_id = getattr(ticket, "current_assessment_id", None)
    if current_assessment_id:
        preferred_assessment = next(
            (item for item in assessments if item.id == current_assessment_id),
            None,
        )
        if preferred_assessment is None:
            preferred_assessment = (
                db.query(TechnicalAssessment)
                .filter(TechnicalAssessment.id == current_assessment_id)
                .first()
            )

    if preferred_assessment is None:
        preferred_assessment = next(
            (
                item
                for item in assessments
                if getattr(item, "presale_ticket_id", None) == ticket.id
            ),
            None,
        )

    if preferred_assessment is None:
        return assessments

    return [preferred_assessment] + [
        item for item in assessments if item.id != preferred_assessment.id
    ]


def _context_source_scopes(
    *,
    source_type: str,
    source_id: int,
    source: Any,
    ticket: Optional[PresaleSupportTicket] = None,
) -> list[tuple[str, int]]:
    scopes: list[tuple[str, int]] = [(source_type.upper(), source_id)]
    lead_id = None
    opportunity_id = None

    if source_type == "lead":
        lead_id = source_id
    elif source_type == "opportunity":
        opportunity_id = source_id
        lead_id = getattr(source, "lead_id", None)

    if ticket:
        lead_id = lead_id or getattr(ticket, "lead_id", None)
        opportunity_id = opportunity_id or getattr(ticket, "opportunity_id", None)

    if lead_id:
        scopes.append(("LEAD", lead_id))
    if opportunity_id:
        scopes.append(("OPPORTUNITY", opportunity_id))

    seen = set()
    unique_scopes = []
    for scope in scopes:
        if scope not in seen:
            seen.add(scope)
            unique_scopes.append(scope)
    return unique_scopes


def _source_scope_filter(model: Any, scopes: list[tuple[str, int]]) -> Any:
    return or_(
        *[
            and_(model.source_type == source_type, model.source_id == source_id)
            for source_type, source_id in scopes
        ]
    )


def _open_item_payload(item: OpenItem) -> dict[str, Any]:
    responsible_person = getattr(item, "responsible_person", None)
    data = _model_to_dict(item)
    data["responsible_person_name"] = (
        getattr(responsible_person, "real_name", None)
        or getattr(responsible_person, "username", None)
        if responsible_person
        else None
    )
    return data


def _requirement_freeze_payload(freeze: RequirementFreeze) -> dict[str, Any]:
    frozen_by_user = getattr(freeze, "frozen_by_user", None)
    data = _model_to_dict(freeze)
    data["frozen_by_name"] = (
        getattr(frozen_by_user, "real_name", None)
        or getattr(frozen_by_user, "username", None)
        if frozen_by_user
        else None
    )
    return data


def _build_collaboration_context(
    db: Session,
    *,
    source_type: str,
    source_id: int,
    source: Any,
    ticket: Optional[PresaleSupportTicket] = None,
    limit: int = 10,
) -> dict[str, Any]:
    scopes = _context_source_scopes(
        source_type=source_type,
        source_id=source_id,
        source=source,
        ticket=ticket,
    )
    if not scopes:
        return {
            "openItems": {"items": [], "total": 0, "blocking_count": 0},
            "requirementFreezes": {"items": [], "total": 0},
            "aiClarifications": {"items": [], "total": 0},
        }

    closed_statuses = (
        OpenItemStatusEnum.CLOSED.value,
        OpenItemStatusEnum.CANCELLED.value,
        OpenItemStatusEnum.RESOLVED.value,
    )
    open_item_query = (
        db.query(OpenItem)
        .options(joinedload(OpenItem.responsible_person))
        .filter(
            _source_scope_filter(OpenItem, scopes),
            or_(OpenItem.status.is_(None), OpenItem.status.notin_(closed_statuses)),
        )
    )
    open_items = (
        open_item_query.order_by(
            desc(OpenItem.blocks_quotation),
            desc(OpenItem.updated_at),
            desc(OpenItem.id),
        )
        .limit(limit)
        .all()
    )

    freeze_query = (
        db.query(RequirementFreeze)
        .options(joinedload(RequirementFreeze.frozen_by_user))
        .filter(_source_scope_filter(RequirementFreeze, scopes))
    )
    freezes = (
        freeze_query.order_by(desc(RequirementFreeze.freeze_time), desc(RequirementFreeze.id))
        .limit(limit)
        .all()
    )

    clarification_query = db.query(AIClarification).filter(
        _source_scope_filter(AIClarification, scopes)
    )
    clarifications = (
        clarification_query.order_by(desc(AIClarification.round), desc(AIClarification.id))
        .limit(limit)
        .all()
    )

    return {
        "openItems": {
            "items": [_open_item_payload(item) for item in open_items],
            "total": open_item_query.count(),
            "blocking_count": open_item_query.filter(OpenItem.blocks_quotation.is_(True)).count(),
        },
        "requirementFreezes": {
            "items": [_requirement_freeze_payload(freeze) for freeze in freezes],
            "total": freeze_query.count(),
        },
        "aiClarifications": {
            "items": [_model_to_dict(clarification) for clarification in clarifications],
            "total": clarification_query.count(),
        },
    }


def _assessment_template_payload(template: AssessmentTemplate) -> dict[str, Any]:
    return _model_to_dict(
        template,
        only=[
            "id",
            "template_code",
            "template_name",
            "category",
            "description",
            "dimension_weights",
            "veto_rules",
            "score_thresholds",
            "version",
            "is_active",
            "is_default",
            "created_by",
            "created_at",
            "updated_at",
        ],
    )


def _technical_template_payload(template: TechnicalParameterTemplate) -> dict[str, Any]:
    return _model_to_dict(
        template,
        only=[
            "id",
            "name",
            "code",
            "industry",
            "test_type",
            "description",
            "parameters",
            "cost_factors",
            "typical_labor_hours",
            "reference_docs",
            "sample_images",
            "use_count",
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
        ],
    )


def _active_assessment_templates(db: Session, *, limit: int = 50) -> dict:
    query = db.query(AssessmentTemplate).filter(AssessmentTemplate.is_active == True)
    total = query.count()
    items = [
        _assessment_template_payload(template)
        for template in query.order_by(desc(AssessmentTemplate.updated_at), desc(AssessmentTemplate.id))
        .limit(limit)
        .all()
    ]
    return {"items": items, "total": total}


def _active_technical_templates(db: Session, *, page: int = 1, page_size: int = 20) -> dict:
    query = db.query(TechnicalParameterTemplate).filter(TechnicalParameterTemplate.is_active == True)
    total = query.count()
    offset = max(page - 1, 0) * page_size
    templates = (
        query.order_by(desc(TechnicalParameterTemplate.updated_at), desc(TechnicalParameterTemplate.id))
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return _page_payload([_technical_template_payload(item) for item in templates], total, page, page_size)


def _funnel_summary(db: Session) -> dict[str, int]:
    return {
        "leads": db.query(Lead).count(),
        "opportunities": db.query(Opportunity).count(),
        "quotes": db.query(Quote).count(),
        "contracts": db.query(Contract).count(),
    }


def _funnel_health(db: Session) -> dict[str, Any]:
    active_tickets = (
        db.query(PresaleSupportTicket)
        .filter(~PresaleSupportTicket.status.in_(["COMPLETED", "CLOSED", "CANCELLED"]))
        .count()
    )
    approved_solutions = (
        db.query(PresaleSolution).filter(PresaleSolution.status == "APPROVED").count()
    )
    completed_assessments = (
        db.query(func.count(TechnicalAssessment.id))
        .filter(TechnicalAssessment.status == "COMPLETED")
        .scalar()
        or 0
    )
    score = max(0, min(100, 70 + min(approved_solutions, 10) * 2 - min(active_tickets, 10)))
    return {
        "dashboard_date": date.today().isoformat(),
        "overall_health": {
            "score": score,
            "level": "GOOD" if score >= 70 else "WARNING",
        },
        "key_metrics": {
            "active_presale_tickets": active_tickets,
            "approved_solutions": approved_solutions,
            "completed_assessments": completed_assessments,
        },
        "alerts": [],
    }


def _conversion_payload(summary: dict[str, int]) -> dict[str, Any]:
    return {
        "stages": [
            {"stage": "LEAD", "count": summary["leads"]},
            {"stage": "OPPORTUNITY", "count": summary["opportunities"]},
            {"stage": "QUOTE", "count": summary["quotes"]},
            {"stage": "CONTRACT", "count": summary["contracts"]},
        ],
        "overall_metrics": {
            "total_leads": summary["leads"],
            "total_won": summary["contracts"],
        },
    }


def _dwell_alert_payload(alert: StageDwellTimeAlert) -> dict[str, Any]:
    return _model_to_dict(
        alert,
        only=[
            "id",
            "entity_type",
            "entity_id",
            "stage_id",
            "alert_code",
            "severity",
            "alert_message",
            "entered_stage_at",
            "dwell_hours",
            "threshold_hours",
            "amount",
            "owner_id",
            "owner_name",
            "status",
            "created_at",
            "updated_at",
        ],
    )


def _active_dwell_alerts(
    db: Session,
    *,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    limit: int = 10,
) -> dict:
    query = db.query(StageDwellTimeAlert).filter(StageDwellTimeAlert.status == "ACTIVE")
    if entity_type:
        query = query.filter(StageDwellTimeAlert.entity_type == entity_type)
    if entity_id:
        query = query.filter(StageDwellTimeAlert.entity_id == entity_id)
    total = query.count()
    alerts = query.order_by(desc(StageDwellTimeAlert.created_at), desc(StageDwellTimeAlert.id)).limit(limit).all()
    return {"items": [_dwell_alert_payload(alert) for alert in alerts], "total": total}


def _gate_configs(db: Session) -> dict:
    configs = (
        db.query(StageGateConfig)
        .filter(StageGateConfig.is_active == True)
        .order_by(StageGateConfig.gate_type)
        .all()
    )
    return {
        "items": [
            _model_to_dict(
                config,
                only=[
                    "id",
                    "gate_type",
                    "gate_name",
                    "description",
                    "validation_rules",
                    "required_fields",
                    "requires_approval",
                    "can_be_waived",
                    "version",
                ],
            )
            for config in configs
        ],
        "total": len(configs),
    }


def _stages(db: Session, entity_type: Optional[str]) -> dict:
    query = db.query(SalesFunnelStage).filter(SalesFunnelStage.is_active == True)
    if entity_type:
        query = query.filter(SalesFunnelStage.entity_type == entity_type)
    stages = query.order_by(SalesFunnelStage.sequence, SalesFunnelStage.id).all()
    return {
        "items": [
            _model_to_dict(
                stage,
                only=[
                    "id",
                    "stage_code",
                    "stage_name",
                    "entity_type",
                    "sequence",
                    "description",
                    "color",
                    "icon",
                    "default_probability",
                    "required_gate",
                    "is_active",
                    "is_terminal",
                    "is_won",
                    "is_lost",
                ],
            )
            for stage in stages
        ],
        "total": len(stages),
    }


def _transition_logs(db: Session, entity_type: Optional[str], entity_id: Optional[int], limit: int) -> dict:
    query = db.query(FunnelTransitionLog)
    if entity_type:
        query = query.filter(FunnelTransitionLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(FunnelTransitionLog.entity_id == entity_id)
    total = query.count()
    logs = query.order_by(desc(FunnelTransitionLog.transitioned_at), desc(FunnelTransitionLog.id)).limit(limit).all()
    return {
        "items": [
            _model_to_dict(
                log,
                only=[
                    "id",
                    "entity_type",
                    "entity_id",
                    "entity_code",
                    "from_stage",
                    "to_stage",
                    "gate_type",
                    "gate_result_id",
                    "transition_reason",
                    "transitioned_by",
                    "transitioned_at",
                    "extra_data",
                    "dwell_hours",
                ],
            )
            for log in logs
        ],
        "total": total,
    }


def _gate_payload(gate_type: GateTypeEnum, result: Any) -> dict[str, Any]:
    return {
        "gate_type": gate_type.value,
        "is_valid": result.passed,
        "passed": result.passed,
        "errors": result.failed_rules,
        "failed_rules": result.failed_rules,
        "warnings": result.warnings,
        "checked_items": result.passed_rules,
        "passed_rules": result.passed_rules,
        "score": result.score,
        "threshold": result.threshold,
        "details": result.details,
    }


def _validate_gate_status(
    db: Session,
    *,
    entity_type: Optional[str],
    entity_id: Optional[int],
    current_user: User,
) -> Optional[dict[str, Any]]:
    if not entity_type or not entity_id:
        return None

    gate_by_entity = {
        "LEAD": GateTypeEnum.G1,
        "OPPORTUNITY": GateTypeEnum.G2,
        "QUOTE": GateTypeEnum.G3,
        "CONTRACT": GateTypeEnum.G4,
    }
    gate_type = gate_by_entity.get(entity_type)
    if gate_type is None:
        return None

    result, _ = GateValidatorFactory.validate_gate(
        gate_type=gate_type,
        entity_id=entity_id,
        db=db,
        validated_by=current_user.id,
        save_result=False,
    )
    return _gate_payload(gate_type, result)


def _normalize_source_type(source_type: str) -> str:
    normalized = str(source_type or "").strip().lower()
    if normalized not in {"lead", "opportunity"}:
        raise HTTPException(status_code=400, detail="source_type 仅支持 lead/opportunity")
    return normalized


def _normalize_entity_type(entity_type: Optional[str], fallback_source_type: str) -> str:
    raw = entity_type or fallback_source_type
    normalized = str(raw or "").strip().upper()
    mapping = {
        "LEAD": "LEAD",
        "OPPORTUNITY": "OPPORTUNITY",
        "QUOTE": "QUOTE",
        "CONTRACT": "CONTRACT",
    }
    if normalized not in mapping:
        raise HTTPException(status_code=400, detail="entity_type 无效")
    return mapping[normalized]


def _ensure_source_exists(db: Session, source_type: str, source_id: int) -> Any:
    model = Lead if source_type == "lead" else Opportunity
    source = db.query(model).filter(model.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="来源对象不存在")
    return source


@router.get("/overview", response_model=ResponseModel)
def get_workbench_overview(
    *,
    db: Session = Depends(deps.get_db),
    ticket_page: int = Query(1, ge=1),
    ticket_page_size: int = Query(6, ge=1, le=50),
    ticket_status: Optional[str] = Query(None),
    solution_page: int = Query(1, ge=1),
    solution_page_size: int = Query(6, ge=1, le=100),
    tender_page: int = Query(1, ge=1),
    tender_page_size: int = Query(6, ge=1, le=50),
    opportunity_page: int = Query(1, ge=1),
    opportunity_page_size: int = Query(6, ge=1, le=50),
    opportunity_stage: Optional[str] = Query(None),
    current_user: User = Depends(security.get_current_active_user),
) -> ResponseModel:
    """聚合售前工作台首页所需数据，避免前端拼散接口。"""
    ticket_query = db.query(PresaleSupportTicket)
    if ticket_status:
        statuses = [item.strip() for item in ticket_status.split(",") if item.strip()]
        if statuses:
            ticket_query = ticket_query.filter(PresaleSupportTicket.status.in_(statuses))
    ticket_total = ticket_query.count()
    ticket_offset = (ticket_page - 1) * ticket_page_size
    tickets = (
        ticket_query.order_by(desc(PresaleSupportTicket.created_at), desc(PresaleSupportTicket.id))
        .offset(ticket_offset)
        .limit(ticket_page_size)
        .all()
    )

    solution_query = db.query(PresaleSolution)
    solution_total = solution_query.count()
    solution_offset = (solution_page - 1) * solution_page_size
    solutions = (
        solution_query.order_by(desc(PresaleSolution.created_at), desc(PresaleSolution.id))
        .offset(solution_offset)
        .limit(solution_page_size)
        .all()
    )

    tender_query = db.query(PresaleTenderRecord)
    tender_total = tender_query.count()
    tender_offset = (tender_page - 1) * tender_page_size
    tenders = (
        tender_query.order_by(desc(PresaleTenderRecord.created_at), desc(PresaleTenderRecord.id))
        .offset(tender_offset)
        .limit(tender_page_size)
        .all()
    )

    opportunity_query = db.query(Opportunity).options(
        joinedload(Opportunity.customer),
        joinedload(Opportunity.owner),
        joinedload(Opportunity.updater),
    )
    if opportunity_stage:
        stages = [item.strip() for item in opportunity_stage.split(",") if item.strip()]
        if stages:
            opportunity_query = opportunity_query.filter(Opportunity.stage.in_(stages))
    opportunity_total = opportunity_query.count()
    opportunity_offset = (opportunity_page - 1) * opportunity_page_size
    opportunities = (
        opportunity_query.order_by(desc(Opportunity.created_at), desc(Opportunity.id))
        .offset(opportunity_offset)
        .limit(opportunity_page_size)
        .all()
    )

    summary = _funnel_summary(db)
    return ResponseModel(
        message="查询成功",
        data={
            "tickets": _page_payload(
                [_ticket_payload(ticket) for ticket in tickets],
                ticket_total,
                ticket_page,
                ticket_page_size,
            ),
            "solutions": _page_payload(
                [_solution_payload(db, solution) for solution in solutions],
                solution_total,
                solution_page,
                solution_page_size,
            ),
            "tenders": _page_payload(
                [_tender_payload(tender) for tender in tenders],
                tender_total,
                tender_page,
                tender_page_size,
            ),
            "opportunities": _page_payload(
                [_opportunity_payload(opportunity) for opportunity in opportunities],
                opportunity_total,
                opportunity_page,
                opportunity_page_size,
            ),
            "templates": {
                "assessment": _active_assessment_templates(db, limit=20),
                "technical": _active_technical_templates(db, page=1, page_size=20),
            },
            "funnel": {
                "summary": summary,
                "health": _funnel_health(db),
                "conversion": _conversion_payload(summary),
                "dwellAlerts": _active_dwell_alerts(db, limit=8),
            },
            "meta": {"failures": []},
        },
    )


@router.get("/context", response_model=ResponseModel)
def get_workbench_context(
    *,
    db: Session = Depends(deps.get_db),
    source_type: str = Query(...),
    source_id: int = Query(...),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    presale_ticket_id: Optional[int] = Query(None),
    ticket_id: Optional[int] = Query(None),
    transition_log_limit: int = Query(20, ge=1, le=100),
    active_alert_limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(security.get_current_active_user),
) -> ResponseModel:
    """聚合单个线索/商机售前上下文。"""
    normalized_source_type = _normalize_source_type(source_type)
    source = _ensure_source_exists(db, normalized_source_type, source_id)

    resolved_entity_type = _normalize_entity_type(entity_type, normalized_source_type)
    resolved_entity_id = entity_id or source_id
    resolved_ticket_id = presale_ticket_id or ticket_id

    ticket = None
    if resolved_ticket_id:
        ticket = (
            db.query(PresaleSupportTicket)
            .filter(PresaleSupportTicket.id == resolved_ticket_id)
            .first()
        )
        if not ticket:
            raise HTTPException(status_code=404, detail="售前工单不存在")
    elif normalized_source_type == "opportunity":
        ticket = (
            db.query(PresaleSupportTicket)
            .filter(PresaleSupportTicket.opportunity_id == source_id)
            .order_by(desc(PresaleSupportTicket.created_at), desc(PresaleSupportTicket.id))
            .first()
        )
    elif normalized_source_type == "lead":
        ticket = (
            db.query(PresaleSupportTicket)
            .filter(PresaleSupportTicket.lead_id == source_id)
            .order_by(desc(PresaleSupportTicket.created_at), desc(PresaleSupportTicket.id))
            .first()
        )

    assessments = (
        db.query(TechnicalAssessment)
        .filter(
            TechnicalAssessment.source_type == normalized_source_type.upper(),
            TechnicalAssessment.source_id == source_id,
        )
        .order_by(
            desc(TechnicalAssessment.evaluated_at),
            desc(TechnicalAssessment.updated_at),
            desc(TechnicalAssessment.id),
        )
        .all()
    )
    assessments = _prioritize_ticket_assessment(db, assessments, ticket)

    current_assessment = assessments[0] if assessments else None
    risks = {"items": [], "total": 0}
    versions = {"items": [], "total": 0}
    if current_assessment:
        risk_items = (
            db.query(AssessmentRisk)
            .filter(AssessmentRisk.assessment_id == current_assessment.id)
            .order_by(desc(AssessmentRisk.created_at), desc(AssessmentRisk.id))
            .all()
        )
        version_items = (
            db.query(AssessmentVersion)
            .filter(AssessmentVersion.assessment_id == current_assessment.id)
            .order_by(desc(AssessmentVersion.evaluated_at), desc(AssessmentVersion.id))
            .all()
        )
        risks = {"items": [_model_to_dict(risk) for risk in risk_items], "total": len(risk_items)}
        versions = {
            "items": [_model_to_dict(version) for version in version_items],
            "total": len(version_items),
        }

    requirement_detail = None
    requirement_lead_id = None
    if normalized_source_type == "lead":
        requirement_lead_id = source_id
    elif normalized_source_type == "opportunity":
        requirement_lead_id = getattr(source, "lead_id", None) or getattr(ticket, "lead_id", None)

    if requirement_lead_id:
        requirement_detail = (
            db.query(LeadRequirementDetail)
            .filter(LeadRequirementDetail.lead_id == requirement_lead_id)
            .first()
        )

    solution_query = db.query(PresaleSolution)
    if ticket:
        solution_query = solution_query.filter(PresaleSolution.ticket_id == ticket.id)
    elif normalized_source_type == "opportunity":
        solution_query = solution_query.filter(PresaleSolution.opportunity_id == source_id)
    else:
        solution_query = solution_query.filter(False)
    solution_total = solution_query.count()
    solution_items = (
        solution_query.order_by(desc(PresaleSolution.created_at), desc(PresaleSolution.id)).all()
    )

    opportunity_context_id = source_id if normalized_source_type == "opportunity" else None
    if ticket and ticket.opportunity_id:
        opportunity_context_id = ticket.opportunity_id

    quote_query = db.query(Quote).options(
        joinedload(Quote.current_version),
        joinedload(Quote.owner),
    )
    if opportunity_context_id:
        quote_query = quote_query.filter(Quote.opportunity_id == opportunity_context_id)
    else:
        quote_query = quote_query.filter(False)
    quote_total = quote_query.count()
    quote_items = quote_query.order_by(desc(Quote.created_at), desc(Quote.id)).all()

    tender_query = db.query(PresaleTenderRecord)
    if ticket and opportunity_context_id:
        tender_query = tender_query.filter(
            or_(
                PresaleTenderRecord.ticket_id == ticket.id,
                PresaleTenderRecord.opportunity_id == opportunity_context_id,
            )
        )
    elif ticket:
        tender_query = tender_query.filter(PresaleTenderRecord.ticket_id == ticket.id)
    elif opportunity_context_id:
        tender_query = tender_query.filter(PresaleTenderRecord.opportunity_id == opportunity_context_id)
    else:
        tender_query = tender_query.filter(False)
    tender_total = tender_query.count()
    tender_items = tender_query.order_by(desc(PresaleTenderRecord.created_at), desc(PresaleTenderRecord.id)).all()

    gate_status = _validate_gate_status(
        db,
        entity_type=resolved_entity_type,
        entity_id=resolved_entity_id,
        current_user=current_user,
    )

    return ResponseModel(
        message="查询成功",
        data={
            "source": {
                "type": normalized_source_type,
                "id": source_id,
            },
            "ticket": _ticket_payload(ticket) if ticket else None,
            "assessment": {
                "items": [_assessment_payload(assessment) for assessment in assessments],
                "total": len(assessments),
                "current": _assessment_payload(current_assessment)
                if current_assessment
                else None,
                "requirementDetail": _model_to_dict(requirement_detail)
                if requirement_detail
                else None,
                "risks": risks,
                "versions": versions,
            },
            "templates": {
                "assessment": _active_assessment_templates(db, limit=50),
                "technical": _active_technical_templates(db, page=1, page_size=20),
            },
            "solutions": {
                "items": [_solution_payload(db, solution) for solution in solution_items],
                "total": solution_total,
            },
            "costing": _costing_payload(solution_items),
            "quotes": {
                "items": [_quote_payload(quote) for quote in quote_items],
                "total": quote_total,
            },
            "tenders": {
                "items": [_tender_payload(tender) for tender in tender_items],
                "total": tender_total,
            },
            "collaboration": _build_collaboration_context(
                db,
                source_type=normalized_source_type,
                source_id=source_id,
                source=source,
                ticket=ticket,
            ),
            "funnel": {
                "entityType": resolved_entity_type,
                "entityId": resolved_entity_id,
                "gateConfigs": _gate_configs(db),
                "stages": _stages(db, resolved_entity_type),
                "transitionLogs": _transition_logs(
                    db,
                    resolved_entity_type,
                    resolved_entity_id,
                    transition_log_limit,
                ),
                "dwellAlerts": _active_dwell_alerts(
                    db,
                    entity_type=resolved_entity_type,
                    entity_id=resolved_entity_id,
                    limit=active_alert_limit,
                ),
                "gateStatus": gate_status,
            },
            "meta": {"failures": []},
        },
    )
