# -*- coding: utf-8 -*-
"""
全链条健康度监控 API endpoints
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import Contract, Lead, Opportunity, Quote
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.pipeline_health_service import PipelineHealthService

router = APIRouter()


HEALTH_WARNING_LEVELS = {"H2", "H3"}
HEALTH_WARNING_CONFIGS = {
    "LEAD": {
        "model": Lead,
        "owner_field": "owner_id",
        "calculator": "calculate_lead_health",
        "code_field": "lead_code",
        "name_field": "customer_name",
    },
    "OPPORTUNITY": {
        "model": Opportunity,
        "owner_field": "owner_id",
        "calculator": "calculate_opportunity_health",
        "code_field": "opp_code",
        "name_field": "opp_name",
    },
    "QUOTE": {
        "model": Quote,
        "owner_field": "owner_id",
        "calculator": "calculate_quote_health",
        "code_field": "quote_code",
        "name_field": "quote_code",
    },
    "CONTRACT": {
        "model": Contract,
        "owner_field": "sales_owner_id",
        "calculator": "calculate_contract_health",
        "code_field": "contract_code",
        "name_field": "contract_name",
    },
}


def _serialize_health_warning(entity_type: str, entity: Any, health_data: dict) -> dict:
    config = HEALTH_WARNING_CONFIGS[entity_type]
    code = health_data.get(f"{entity_type.lower()}_code") or getattr(entity, config["code_field"], None)
    name = getattr(entity, config["name_field"], None)

    customer_name = None
    if entity_type == "OPPORTUNITY":
        customer_name = getattr(getattr(entity, "customer", None), "customer_name", None)
    elif entity_type == "LEAD":
        customer_name = getattr(entity, "customer_name", None)

    return {
        "entityType": entity_type,
        "entityId": entity.id,
        "entityCode": code,
        "entityName": name,
        "customerName": customer_name,
        "healthStatus": health_data.get("health_status"),
        "healthScore": health_data.get("health_score"),
        "riskFactors": health_data.get("risk_factors", []),
        "summary": (
            (health_data.get("risk_factors") or [None])[0]
            or health_data.get("description")
            or "存在健康风险"
        ),
    }


def _collect_health_warnings(
    db: Session,
    current_user: User,
    level: Optional[str],
    entity_type: Optional[str],
    limit: int,
) -> list[dict]:
    service = PipelineHealthService(db)
    target_level = level.strip().upper() if level else None
    target_entity_type = entity_type.strip().upper() if entity_type else None

    warnings = []
    per_type_limit = max(limit, 20)

    for current_type, config in HEALTH_WARNING_CONFIGS.items():
        if target_entity_type and current_type != target_entity_type:
            continue

        model = config["model"]
        query = security.filter_sales_data_by_scope(
            db.query(model),
            current_user,
            db,
            model,
            config["owner_field"],
        )
        query = query.order_by(model.updated_at.asc()).limit(per_type_limit)

        for entity in query.all():
            health_data = getattr(service, config["calculator"])(entity.id)
            health_status = str(health_data.get("health_status") or "").upper()
            if health_status not in HEALTH_WARNING_LEVELS:
                continue
            if target_level and health_status != target_level:
                continue
            warnings.append(_serialize_health_warning(current_type, entity, health_data))

    warnings.sort(key=lambda item: (item["healthScore"], item["entityType"], item["entityId"]))
    return warnings[:limit]


@router.get("/health/lead/{lead_id}", response_model=ResponseModel)
def get_lead_health(
    lead_id: int = Path(..., description="线索ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取线索健康度"""
    service = PipelineHealthService(db)
    try:
        result = service.calculate_lead_health(lead_id)
        return ResponseModel(code=200, message="查询成功", data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/health/opportunity/{opp_id}", response_model=ResponseModel)
def get_opportunity_health(
    opp_id: int = Path(..., description="商机ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取商机健康度"""
    service = PipelineHealthService(db)
    try:
        result = service.calculate_opportunity_health(opp_id)
        return ResponseModel(code=200, message="查询成功", data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/health/quote/{quote_id}", response_model=ResponseModel)
def get_quote_health(
    quote_id: int = Path(..., description="报价ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取报价健康度"""
    service = PipelineHealthService(db)
    try:
        result = service.calculate_quote_health(quote_id)
        return ResponseModel(code=200, message="查询成功", data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/health/contract/{contract_id}", response_model=ResponseModel)
def get_contract_health(
    contract_id: int = Path(..., description="合同ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取合同健康度"""
    service = PipelineHealthService(db)
    try:
        result = service.calculate_contract_health(contract_id)
        return ResponseModel(code=200, message="查询成功", data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/health/payment/{invoice_id}", response_model=ResponseModel)
def get_payment_health(
    invoice_id: int = Path(..., description="发票ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取回款健康度"""
    service = PipelineHealthService(db)
    try:
        result = service.calculate_payment_health(invoice_id)
        return ResponseModel(code=200, message="查询成功", data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/health/pipeline", response_model=ResponseModel)
def get_pipeline_health(
    lead_id: Optional[int] = Query(None, description="线索ID"),
    opportunity_id: Optional[int] = Query(None, description="商机ID"),
    quote_id: Optional[int] = Query(None, description="报价ID"),
    contract_id: Optional[int] = Query(None, description="合同ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取全链条健康度"""
    service = PipelineHealthService(db)
    result = service.calculate_pipeline_health(
        lead_id=lead_id, opportunity_id=opportunity_id, quote_id=quote_id, contract_id=contract_id
    )
    return ResponseModel(code=200, message="查询成功", data=result)


@router.get("/alerts/health-warnings", response_model=ResponseModel)
def get_health_warnings(
    level: Optional[str] = Query(None, description="预警等级过滤：H2/H3"),
    entity_type: Optional[str] = Query(
        None,
        description="实体类型过滤：LEAD/OPPORTUNITY/QUOTE/CONTRACT",
    ),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取健康度预警列表"""
    warnings = _collect_health_warnings(
        db=db,
        current_user=current_user,
        level=level,
        entity_type=entity_type,
        limit=limit,
    )
    summary = {
        "H2": sum(1 for item in warnings if item["healthStatus"] == "H2"),
        "H3": sum(1 for item in warnings if item["healthStatus"] == "H3"),
    }
    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "warnings": warnings,
            "total": len(warnings),
            "summary": summary,
        },
    )
