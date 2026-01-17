# -*- coding: utf-8 -*-
"""
全链条健康度监控 API endpoints
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.pipeline_health_service import PipelineHealthService

router = APIRouter()


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
        lead_id=lead_id,
        opportunity_id=opportunity_id,
        quote_id=quote_id,
        contract_id=contract_id
    )
    return ResponseModel(code=200, message="查询成功", data=result)


@router.get("/alerts/health-warnings", response_model=ResponseModel)
def get_health_warnings(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取健康度预警列表"""
    # 这里可以查询健康度为H2或H3的线索/商机/报价/合同
    warnings = []
    # 实现逻辑...
    return ResponseModel(code=200, message="查询成功", data={'warnings': warnings})
