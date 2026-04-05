# -*- coding: utf-8 -*-
"""
毛利率预警管理 API

提供毛利率预警的配置、检查和审批功能：
- 预警配置 CRUD
- 毛利率检查
- 预警记录管理
- 审批流程
- 统计分析
"""

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.services.sales.margin_alert_service import MarginAlertService

router = APIRouter(prefix="/margin-alerts", tags=["sales-margin-alerts"])


# ==================== Schema ====================


class MarginAlertConfigCreate(BaseModel):
    """创建预警配置请求"""

    name: str = Field(..., description="配置名称")
    code: str = Field(..., description="配置编码")
    description: Optional[str] = None
    customer_level: Optional[str] = Field(None, description="客户等级（A/B/C/D）")
    project_type: Optional[str] = None
    industry: Optional[str] = None
    standard_margin: float = Field(25.0, description="标准毛利率(%)")
    warning_margin: float = Field(20.0, description="警告阈值(%)")
    alert_margin: float = Field(15.0, description="警报阈值(%)")
    minimum_margin: float = Field(10.0, description="最低毛利率(%)")
    is_default: bool = False


class MarginAlertConfigUpdate(BaseModel):
    """更新预警配置请求"""

    name: Optional[str] = None
    description: Optional[str] = None
    standard_margin: Optional[float] = None
    warning_margin: Optional[float] = None
    alert_margin: Optional[float] = None
    minimum_margin: Optional[float] = None
    is_active: Optional[bool] = None


class MarginAlertConfigResponse(BaseModel):
    """预警配置响应"""

    id: int
    name: str
    code: str
    description: Optional[str] = None
    customer_level: Optional[str] = None
    project_type: Optional[str] = None
    industry: Optional[str] = None
    standard_margin: float
    warning_margin: float
    alert_margin: float
    minimum_margin: float
    is_active: bool
    is_default: bool


class MarginCheckResponse(BaseModel):
    """毛利率检查响应"""

    quote_id: int
    quote_version_id: Optional[int] = None
    total_price: float
    total_cost: float
    gross_margin: float
    alert_level: str
    alert_required: bool
    below_minimum: Optional[bool] = None
    thresholds: Optional[dict] = None
    message: Optional[str] = None


class CreateAlertRecordRequest(BaseModel):
    """创建预警记录请求"""

    justification: str = Field(..., description="申请理由")
    quote_version_id: Optional[int] = None


class MarginAlertRecordResponse(BaseModel):
    """预警记录响应"""

    id: int
    quote_id: int
    quote_version_id: Optional[int] = None
    alert_level: str
    gross_margin: float
    margin_gap: float
    status: str
    justification: Optional[str] = None
    requested_at: datetime
    approval_comment: Optional[str] = None
    approved_at: Optional[datetime] = None


class ApproveRequest(BaseModel):
    """审批请求"""

    comment: str = Field(..., description="审批意见")
    valid_days: int = Field(30, ge=1, le=365, description="有效天数")


class RejectRequest(BaseModel):
    """驳回请求"""

    comment: str = Field(..., description="驳回原因")


class StatisticsResponse(BaseModel):
    """统计响应"""

    pending_count: int
    approved_count: int
    rejected_count: int
    avg_margin_gap: float


# ==================== 配置管理 ====================


@router.get(
    "/configs",
    response_model=List[MarginAlertConfigResponse],
    summary="获取预警配置列表",
)
def list_configs(
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取所有毛利率预警配置"""
    service = MarginAlertService(db)
    configs = service.list_configs(is_active=is_active)

    return [
        MarginAlertConfigResponse(
            id=c.id,
            name=c.name,
            code=c.code,
            description=c.description,
            customer_level=c.customer_level,
            project_type=c.project_type,
            industry=c.industry,
            standard_margin=float(c.standard_margin or 0),
            warning_margin=float(c.warning_margin or 0),
            alert_margin=float(c.alert_margin or 0),
            minimum_margin=float(c.minimum_margin or 0),
            is_active=c.is_active,
            is_default=c.is_default,
        )
        for c in configs
    ]


@router.post(
    "/configs",
    response_model=MarginAlertConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建预警配置",
)
def create_config(
    data: MarginAlertConfigCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建毛利率预警配置"""
    service = MarginAlertService(db)

    config = service.create_config(
        name=data.name,
        code=data.code,
        created_by=current_user.id,
        customer_level=data.customer_level,
        project_type=data.project_type,
        industry=data.industry,
        standard_margin=data.standard_margin,
        warning_margin=data.warning_margin,
        alert_margin=data.alert_margin,
        minimum_margin=data.minimum_margin,
        is_default=data.is_default,
    )

    return MarginAlertConfigResponse(
        id=config.id,
        name=config.name,
        code=config.code,
        description=config.description,
        customer_level=config.customer_level,
        project_type=config.project_type,
        industry=config.industry,
        standard_margin=float(config.standard_margin or 0),
        warning_margin=float(config.warning_margin or 0),
        alert_margin=float(config.alert_margin or 0),
        minimum_margin=float(config.minimum_margin or 0),
        is_active=config.is_active,
        is_default=config.is_default,
    )


@router.get(
    "/configs/{config_id}",
    response_model=MarginAlertConfigResponse,
    summary="获取配置详情",
)
def get_config(
    config_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取指定配置详情"""
    from app.models.sales import MarginAlertConfig

    config = db.query(MarginAlertConfig).filter(MarginAlertConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    return MarginAlertConfigResponse(
        id=config.id,
        name=config.name,
        code=config.code,
        description=config.description,
        customer_level=config.customer_level,
        project_type=config.project_type,
        industry=config.industry,
        standard_margin=float(config.standard_margin or 0),
        warning_margin=float(config.warning_margin or 0),
        alert_margin=float(config.alert_margin or 0),
        minimum_margin=float(config.minimum_margin or 0),
        is_active=config.is_active,
        is_default=config.is_default,
    )


@router.put(
    "/configs/{config_id}",
    response_model=MarginAlertConfigResponse,
    summary="更新配置",
)
def update_config(
    config_id: int,
    data: MarginAlertConfigUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新预警配置"""
    from app.models.sales import MarginAlertConfig

    config = db.query(MarginAlertConfig).filter(MarginAlertConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)

    return MarginAlertConfigResponse(
        id=config.id,
        name=config.name,
        code=config.code,
        description=config.description,
        customer_level=config.customer_level,
        project_type=config.project_type,
        industry=config.industry,
        standard_margin=float(config.standard_margin or 0),
        warning_margin=float(config.warning_margin or 0),
        alert_margin=float(config.alert_margin or 0),
        minimum_margin=float(config.minimum_margin or 0),
        is_active=config.is_active,
        is_default=config.is_default,
    )


@router.delete(
    "/configs/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除配置",
)
def delete_config(
    config_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> None:
    """删除预警配置（软删除）"""
    from app.models.sales import MarginAlertConfig

    config = db.query(MarginAlertConfig).filter(MarginAlertConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    config.is_active = False
    db.commit()


# ==================== 毛利率检查 ====================


@router.get(
    "/check/{quote_id}",
    response_model=MarginCheckResponse,
    summary="检查报价毛利率",
)
def check_margin(
    quote_id: int,
    version_id: Optional[int] = Query(None, description="报价版本ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """检查报价毛利率是否触发预警"""
    service = MarginAlertService(db)

    try:
        result = service.check_margin_alert(quote_id, version_id)
        return MarginCheckResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 预警记录管理 ====================


@router.get(
    "/records",
    response_model=List[MarginAlertRecordResponse],
    summary="获取预警记录列表",
)
def list_records(
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取预警记录列表"""
    from app.models.sales import MarginAlertRecord

    query = db.query(MarginAlertRecord)

    if status_filter:
        query = query.filter(MarginAlertRecord.status == status_filter)

    records = (
        query.order_by(MarginAlertRecord.requested_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return [
        MarginAlertRecordResponse(
            id=r.id,
            quote_id=r.quote_id,
            quote_version_id=r.quote_version_id,
            alert_level=r.alert_level,
            gross_margin=float(r.gross_margin or 0),
            margin_gap=float(r.margin_gap or 0),
            status=r.status,
            justification=r.justification,
            requested_at=r.requested_at,
            approval_comment=r.approval_comment,
            approved_at=r.approved_at,
        )
        for r in records
    ]


@router.post(
    "/records",
    response_model=MarginAlertRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建预警记录",
)
def create_record(
    quote_id: int = Query(..., description="报价ID"),
    data: CreateAlertRecordRequest = ...,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建毛利率预警记录（申请低毛利率审批）"""
    service = MarginAlertService(db)

    try:
        record = service.create_alert_record(
            quote_id=quote_id,
            requested_by=current_user.id,
            justification=data.justification,
            quote_version_id=data.quote_version_id,
        )
        return MarginAlertRecordResponse(
            id=record.id,
            quote_id=record.quote_id,
            quote_version_id=record.quote_version_id,
            alert_level=record.alert_level,
            gross_margin=float(record.gross_margin or 0),
            margin_gap=float(record.margin_gap or 0),
            status=record.status,
            justification=record.justification,
            requested_at=record.requested_at,
            approval_comment=record.approval_comment,
            approved_at=record.approved_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/records/{record_id}",
    response_model=MarginAlertRecordResponse,
    summary="获取预警记录详情",
)
def get_record(
    record_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取预警记录详情"""
    from app.models.sales import MarginAlertRecord

    record = db.query(MarginAlertRecord).filter(MarginAlertRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    return MarginAlertRecordResponse(
        id=record.id,
        quote_id=record.quote_id,
        quote_version_id=record.quote_version_id,
        alert_level=record.alert_level,
        gross_margin=float(record.gross_margin or 0),
        margin_gap=float(record.margin_gap or 0),
        status=record.status,
        justification=record.justification,
        requested_at=record.requested_at,
        approval_comment=record.approval_comment,
        approved_at=record.approved_at,
    )


@router.get(
    "/pending",
    response_model=List[MarginAlertRecordResponse],
    summary="获取待审批列表",
)
def list_pending(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取待审批的预警记录"""
    service = MarginAlertService(db)
    records = service.list_pending_alerts()

    return [
        MarginAlertRecordResponse(
            id=r.id,
            quote_id=r.quote_id,
            quote_version_id=r.quote_version_id,
            alert_level=r.alert_level,
            gross_margin=float(r.gross_margin or 0),
            margin_gap=float(r.margin_gap or 0),
            status=r.status,
            justification=r.justification,
            requested_at=r.requested_at,
            approval_comment=r.approval_comment,
            approved_at=r.approved_at,
        )
        for r in records
    ]


@router.post(
    "/records/{record_id}/approve",
    response_model=MarginAlertRecordResponse,
    summary="审批通过",
)
def approve_record(
    record_id: int,
    data: ApproveRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """审批通过预警记录"""
    service = MarginAlertService(db)

    try:
        record = service.approve_alert(
            record_id=record_id,
            approved_by=current_user.id,
            comment=data.comment,
            valid_days=data.valid_days,
        )
        return MarginAlertRecordResponse(
            id=record.id,
            quote_id=record.quote_id,
            quote_version_id=record.quote_version_id,
            alert_level=record.alert_level,
            gross_margin=float(record.gross_margin or 0),
            margin_gap=float(record.margin_gap or 0),
            status=record.status,
            justification=record.justification,
            requested_at=record.requested_at,
            approval_comment=record.approval_comment,
            approved_at=record.approved_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/records/{record_id}/reject",
    response_model=MarginAlertRecordResponse,
    summary="驳回",
)
def reject_record(
    record_id: int,
    data: RejectRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """驳回预警记录"""
    service = MarginAlertService(db)

    try:
        record = service.reject_alert(
            record_id=record_id,
            rejected_by=current_user.id,
            comment=data.comment,
        )
        return MarginAlertRecordResponse(
            id=record.id,
            quote_id=record.quote_id,
            quote_version_id=record.quote_version_id,
            alert_level=record.alert_level,
            gross_margin=float(record.gross_margin or 0),
            margin_gap=float(record.margin_gap or 0),
            status=record.status,
            justification=record.justification,
            requested_at=record.requested_at,
            approval_comment=record.approval_comment,
            approved_at=record.approved_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/history/{quote_id}",
    response_model=List[MarginAlertRecordResponse],
    summary="获取报价预警历史",
)
def get_quote_history(
    quote_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取报价的预警历史记录"""
    service = MarginAlertService(db)
    records = service.get_quote_alert_history(quote_id)

    return [
        MarginAlertRecordResponse(
            id=r.id,
            quote_id=r.quote_id,
            quote_version_id=r.quote_version_id,
            alert_level=r.alert_level,
            gross_margin=float(r.gross_margin or 0),
            margin_gap=float(r.margin_gap or 0),
            status=r.status,
            justification=r.justification,
            requested_at=r.requested_at,
            approval_comment=r.approval_comment,
            approved_at=r.approved_at,
        )
        for r in records
    ]


# ==================== 统计分析 ====================


@router.get(
    "/statistics",
    response_model=StatisticsResponse,
    summary="获取预警统计",
)
def get_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取预警统计数据"""
    from sqlalchemy import func

    from app.models.sales import MarginAlertRecord

    # 统计各状态数量
    pending_count = (
        db.query(func.count(MarginAlertRecord.id))
        .filter(MarginAlertRecord.status == "PENDING")
        .scalar()
        or 0
    )

    approved_count = (
        db.query(func.count(MarginAlertRecord.id))
        .filter(MarginAlertRecord.status == "APPROVED")
        .scalar()
        or 0
    )

    rejected_count = (
        db.query(func.count(MarginAlertRecord.id))
        .filter(MarginAlertRecord.status == "REJECTED")
        .scalar()
        or 0
    )

    # 计算平均毛利率差距
    avg_margin_gap = (
        db.query(func.avg(MarginAlertRecord.margin_gap)).scalar() or 0
    )

    return StatisticsResponse(
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        avg_margin_gap=float(avg_margin_gap),
    )
