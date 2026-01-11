# -*- coding: utf-8 -*-
"""
报价管理 API endpoints
"""

from typing import Any, List, Optional
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.sales import (
    Opportunity, Quote, QuoteVersion, QuoteItem,
    QuoteCostTemplate, QuoteCostApproval,
    QuoteApproval, PurchaseMaterialCost,
    ApprovalRecord
)
from app.schemas.sales import (
    QuoteCreate, QuoteUpdate, QuoteResponse,
    QuoteVersionCreate, QuoteVersionResponse,
    QuoteItemCreate, QuoteItemUpdate, QuoteItemBatchUpdate, QuoteItemResponse,
    QuoteApproveRequest, QuoteApprovalResponse,
    QuoteCostApprovalCreate, QuoteCostApprovalResponse, QuoteCostApprovalAction,
    CostCheckResponse, CostComparisonResponse,
    CostMatchSuggestionsResponse, ApplyCostSuggestionsRequest,
    ApprovalStartRequest, ApprovalActionRequest, ApprovalStatusResponse,
    ApprovalRecordResponse, ApprovalHistoryResponse
)
from app.schemas.common import PaginatedResponse, ResponseModel
from app.services.approval_workflow_service import ApprovalWorkflowService
from app.models.enums import (
    WorkflowTypeEnum, ApprovalRecordStatusEnum, ApprovalActionEnum,
    QuoteStatusEnum
)
from .utils import (
    get_entity_creator_id,
    generate_quote_code,
    validate_g2_opportunity_to_quote
)

router = APIRouter()


# ==================== 报价基础CRUD ====================


@router.get("/quotes", response_model=PaginatedResponse[QuoteResponse])
def read_quotes(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    opportunity_id: Optional[int] = Query(None, description="商机ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价列表
    Issue 7.1: 已集成数据权限过滤
    """
    query = db.query(Quote).options(
        joinedload(Quote.opportunity),
        joinedload(Quote.customer),
        joinedload(Quote.owner)
    )

    # Issue 7.1: 应用数据权限过滤
    query = security.filter_sales_data_by_scope(query, current_user, db, Quote, 'owner_id')

    if keyword:
        query = query.filter(Quote.quote_code.contains(keyword))

    if status:
        query = query.filter(Quote.status == status)

    if opportunity_id:
        query = query.filter(Quote.opportunity_id == opportunity_id)

    total = query.count()
    offset = (page - 1) * page_size
    quotes = query.order_by(desc(Quote.created_at)).offset(offset).limit(page_size).all()

    quote_responses = []
    for quote in quotes:
        versions = db.query(QuoteVersion).options(
            joinedload(QuoteVersion.creator),
            joinedload(QuoteVersion.approver)
        ).filter(QuoteVersion.quote_id == quote.id).all()
        quote_dict = {
            **{c.name: getattr(quote, c.name) for c in quote.__table__.columns},
            "opportunity_code": quote.opportunity.opp_code if quote.opportunity else None,
            "customer_name": quote.customer.customer_name if quote.customer else None,
            "owner_name": quote.owner.real_name if quote.owner else None,
            "versions": [],
        }
        for v in versions:
            items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == v.id).all()
            v_dict = {
                **{c.name: getattr(v, c.name) for c in v.__table__.columns},
                "created_by_name": v.creator.real_name if v.creator else None,
                "approved_by_name": v.approver.real_name if v.approver else None,
                "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
            }
            quote_dict["versions"].append(QuoteVersionResponse(**v_dict))
        quote_responses.append(QuoteResponse(**quote_dict))

    return PaginatedResponse(
        items=quote_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/quotes", response_model=QuoteResponse, status_code=201)
def create_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_in: QuoteCreate,
    skip_g2_validation: bool = Query(False, description="跳过G2验证"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建报价（G2阶段门验证）
    """
    # 检查商机是否存在
    opportunity = db.query(Opportunity).filter(Opportunity.id == quote_in.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="商机不存在")

    # G2验证
    if not skip_g2_validation:
        is_valid, errors = validate_g2_opportunity_to_quote(opportunity)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"G2阶段门验证失败: {', '.join(errors)}"
            )

    quote_data = quote_in.model_dump(exclude={"version"})

    # 如果没有提供编码，自动生成
    if not quote_data.get("quote_code"):
        quote_data["quote_code"] = generate_quote_code(db)
    else:
        existing = db.query(Quote).filter(Quote.quote_code == quote_data["quote_code"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="报价编码已存在")

    if not quote_data.get("owner_id"):
        quote_data["owner_id"] = current_user.id

    quote = Quote(**quote_data)
    db.add(quote)
    db.flush()

    # 创建报价版本
    if quote_in.version:
        version_data = quote_in.version.model_dump(exclude={"items"})
        version_data["quote_id"] = quote.id
        version_data["created_by"] = current_user.id
        version = QuoteVersion(**version_data)
        db.add(version)
        db.flush()

        quote.current_version_id = version.id

        # 创建报价明细
        if quote_in.version.items:
            for item_data in quote_in.version.items:
                item_dict = item_data.model_dump()
                item_dict["quote_version_id"] = version.id
                item = QuoteItem(**item_dict)
                db.add(item)

    db.commit()
    db.refresh(quote)

    version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first() if quote.current_version_id else None
    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all() if version else []

    quote_dict = {
        **{c.name: getattr(quote, c.name) for c in quote.__table__.columns},
        "opportunity_code": opportunity.opp_code if opportunity else None,
        "customer_name": quote.customer.customer_name if quote.customer else None,
        "owner_name": quote.owner.real_name if quote.owner else None,
        "versions": [],
    }

    if version:
        version_dict = {
            **{c.name: getattr(version, c.name) for c in version.__table__.columns},
            "created_by_name": version.creator.real_name if version.creator else None,
            "approved_by_name": version.approver.real_name if version.approver else None,
            "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
        }
        quote_dict["versions"] = [QuoteVersionResponse(**version_dict)]

    return QuoteResponse(**quote_dict)


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
def read_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价详情
    """
    quote = db.query(Quote).options(joinedload(Quote.opportunity), joinedload(Quote.customer)).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    versions = db.query(QuoteVersion).filter(QuoteVersion.quote_id == quote.id).all()
    quote_dict = {
        **{c.name: getattr(quote, c.name) for c in quote.__table__.columns},
        "opportunity_code": quote.opportunity.opp_code if quote.opportunity else None,
        "customer_name": quote.customer.customer_name if quote.customer else None,
        "owner_name": quote.owner.real_name if quote.owner else None,
        "versions": [],
    }
    for v in versions:
        items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == v.id).all()
        v_dict = {
            **{c.name: getattr(v, c.name) for c in v.__table__.columns},
            "created_by_name": v.creator.real_name if v.creator else None,
            "approved_by_name": v.approver.real_name if v.approver else None,
            "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
        }
        quote_dict["versions"].append(QuoteVersionResponse(**v_dict))
        if v.id == quote.current_version_id:
            quote_dict["current_version"] = QuoteVersionResponse(**v_dict)

    return QuoteResponse(**quote_dict)


@router.put("/quotes/{quote_id}", response_model=QuoteResponse)
def update_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    quote_in: QuoteUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新报价
    Issue 7.2: 已集成操作权限检查
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    # Issue 7.2: 检查编辑权限
    if not security.check_sales_edit_permission(
        current_user,
        db,
        get_entity_creator_id(quote),
        quote.owner_id,
    ):
        raise HTTPException(status_code=403, detail="您没有权限编辑此报价")

    update_data = quote_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(quote, field, value)

    db.commit()
    db.refresh(quote)

    versions = db.query(QuoteVersion).filter(QuoteVersion.quote_id == quote.id).all()
    quote_dict = {
        **{c.name: getattr(quote, c.name) for c in quote.__table__.columns},
        "opportunity_code": quote.opportunity.opp_code if quote.opportunity else None,
        "customer_name": quote.customer.customer_name if quote.customer else None,
        "owner_name": quote.owner.real_name if quote.owner else None,
        "versions": [],
    }
    for v in versions:
        items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == v.id).all()
        v_dict = {
            **{c.name: getattr(v, c.name) for c in v.__table__.columns},
            "created_by_name": v.creator.real_name if v.creator else None,
            "approved_by_name": v.approver.real_name if v.approver else None,
            "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
        }
        quote_dict["versions"].append(QuoteVersionResponse(**v_dict))
        if v.id == quote.current_version_id:
            quote_dict["current_version"] = QuoteVersionResponse(**v_dict)

    return QuoteResponse(**quote_dict)


# ==================== 报价版本管理 ====================


@router.get("/quotes/{quote_id}/versions", response_model=List[QuoteVersionResponse])
def get_quote_versions(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价的所有版本
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    versions = db.query(QuoteVersion).filter(QuoteVersion.quote_id == quote_id).order_by(desc(QuoteVersion.created_at)).all()

    version_responses = []
    for v in versions:
        items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == v.id).all()
        v_dict = {
            **{c.name: getattr(v, c.name) for c in v.__table__.columns},
            "created_by_name": v.creator.real_name if v.creator else None,
            "approved_by_name": v.approver.real_name if v.approver else None,
            "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
        }
        version_responses.append(QuoteVersionResponse(**v_dict))

    return version_responses


@router.post("/quotes/{quote_id}/versions", response_model=QuoteVersionResponse, status_code=201)
def create_quote_version(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_in: QuoteVersionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建报价版本
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    version_data = version_in.model_dump()
    version_data["quote_id"] = quote_id
    version_data["created_by"] = current_user.id
    version = QuoteVersion(**version_data)
    db.add(version)
    db.flush()

    # 创建报价明细
    if version_in.items:
        for item_data in version_in.items:
            item = QuoteItem(quote_version_id=version.id, **item_data.model_dump())
            db.add(item)

    db.commit()
    db.refresh(version)

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all()
    version_dict = {
        **{c.name: getattr(version, c.name) for c in version.__table__.columns},
        "created_by_name": version.creator.real_name if version.creator else None,
        "approved_by_name": version.approver.real_name if version.approver else None,
        "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
    }
    return QuoteVersionResponse(**version_dict)


# ==================== 报价明细管理 ====================


@router.get("/quotes/{quote_id}/items", response_model=List[QuoteItemResponse])
def get_quote_items(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_id: Optional[int] = Query(None, description="版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价明细列表
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    target_version_id = version_id or quote.current_version_id
    if not target_version_id:
        raise HTTPException(status_code=400, detail="报价没有指定版本")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == target_version_id).all()
    return [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items]


@router.post("/quotes/{quote_id}/items", response_model=QuoteItemResponse, status_code=201)
def create_quote_item(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    item_in: QuoteItemCreate,
    version_id: Optional[int] = Query(None, description="版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加报价明细
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    target_version_id = version_id or quote.current_version_id
    if not target_version_id:
        raise HTTPException(status_code=400, detail="报价没有指定版本")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == target_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    item = QuoteItem(quote_version_id=target_version_id, **item_in.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)

    return QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns})


@router.put("/quotes/{quote_id}/items/{item_id}", response_model=QuoteItemResponse)
def update_quote_item(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    item_id: int,
    item_in: QuoteItemUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新报价明细
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    item = db.query(QuoteItem).filter(
        QuoteItem.id == item_id,
        QuoteItem.quote_version_id.in_([v.id for v in quote.versions])
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="报价明细不存在")

    # 更新字段
    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(item, field):
            setattr(item, field, value)

    db.add(item)
    db.commit()
    db.refresh(item)

    return QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns})


@router.delete("/quotes/{quote_id}/items/{item_id}", status_code=200)
def delete_quote_item(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    item_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除报价明细
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    item = db.query(QuoteItem).filter(
        QuoteItem.id == item_id,
        QuoteItem.quote_version_id.in_([v.id for v in quote.versions])
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="报价明细不存在")

    db.delete(item)
    db.commit()

    return ResponseModel(code=200, message="删除成功")


@router.put("/quotes/{quote_id}/items/batch", response_model=ResponseModel)
def batch_update_quote_items(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    batch_data: QuoteItemBatchUpdate,
    version_id: Optional[int] = Query(None, description="版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量更新报价明细
    支持更新、新增、删除操作
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    target_version_id = version_id or quote.current_version_id
    if not target_version_id:
        raise HTTPException(status_code=400, detail="报价没有指定版本")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == target_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    updated_count = 0
    created_count = 0

    # 处理批量更新
    for item_data in batch_data.items:
        item_dict = item_data.model_dump(exclude_unset=True)
        item_id = item_dict.pop('id', None)

        if item_id:
            # 更新现有明细
            item = db.query(QuoteItem).filter(
                QuoteItem.id == item_id,
                QuoteItem.quote_version_id == target_version_id
            ).first()

            if item:
                for field, value in item_dict.items():
                    if hasattr(item, field) and field != 'id':
                        setattr(item, field, value)
                db.add(item)
                updated_count += 1
        else:
            # 创建新明细
            item = QuoteItem(quote_version_id=target_version_id, **item_dict)
            db.add(item)
            created_count += 1

    db.commit()

    # 重新计算成本和毛利率
    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == target_version_id).all()
    total_price = sum([float(item.qty or 0) * float(item.unit_price or 0) for item in items])
    total_cost = sum([float(item.cost or 0) * float(item.qty or 0) for item in items])
    gross_margin = ((total_price - total_cost) / total_price * 100) if total_price > 0 else 0

    version.total_price = total_price
    version.cost_total = total_cost
    version.gross_margin = gross_margin
    db.add(version)
    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量更新完成，新增 {created_count} 条，更新 {updated_count} 条",
        data={
            "created": created_count,
            "updated": updated_count,
            "total_price": total_price,
            "total_cost": total_cost,
            "gross_margin": gross_margin
        }
    )


# ==================== 成本分解 ====================


@router.get("/quotes/{quote_id}/cost-breakdown", response_model=ResponseModel)
def get_quote_cost_breakdown(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_id: Optional[int] = Query(None, description="版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    报价成本拆解
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    target_version_id = version_id or quote.current_version_id
    if not target_version_id:
        raise HTTPException(status_code=400, detail="报价没有指定版本")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == target_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == target_version_id).all()

    total_price = float(version.total_price or 0)
    total_cost = float(version.cost_total or 0)
    gross_margin = float(version.gross_margin or 0) if version.gross_margin else (total_price - total_cost) / total_price * 100 if total_price > 0 else 0

    cost_breakdown = []
    for item in items:
        item_price = float(item.qty or 0) * float(item.unit_price or 0)
        item_cost = float(item.cost or 0) * float(item.qty or 0)
        item_margin = (item_price - item_cost) / item_price * 100 if item_price > 0 else 0
        cost_breakdown.append({
            "item_name": item.item_name,
            "item_type": item.item_type,
            "qty": float(item.qty or 0),
            "unit_price": float(item.unit_price or 0),
            "total_price": item_price,
            "unit_cost": float(item.cost or 0),
            "total_cost": item_cost,
            "margin": round(item_margin, 2)
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_price": total_price,
            "total_cost": total_cost,
            "gross_margin": round(gross_margin, 2),
            "breakdown": cost_breakdown
        }
    )


# ==================== 状态变更 ====================


@router.put("/quotes/{quote_id}/submit", response_model=ResponseModel)
def submit_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交审批
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if not quote.current_version_id:
        raise HTTPException(status_code=400, detail="报价没有当前版本")

    quote.status = "PENDING_APPROVAL"
    db.commit()

    return ResponseModel(code=200, message="报价已提交审批")


@router.put("/quotes/{quote_id}/reject", response_model=ResponseModel)
def reject_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    reason: Optional[str] = Query(None, description="驳回原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批驳回
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    quote.status = "REJECTED"
    db.commit()

    return ResponseModel(code=200, message="报价已驳回")


@router.put("/quotes/{quote_id}/send", response_model=ResponseModel)
def send_quote_to_customer(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    send_method: Optional[str] = Query("EMAIL", description="发送方式：EMAIL/PRINT/OTHER"),
    send_to: Optional[str] = Query(None, description="发送对象（邮箱/联系人等）"),
    remark: Optional[str] = Query(None, description="发送备注"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    发送报价给客户
    只有已审批通过的报价才能发送给客户
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if quote.status != QuoteStatusEnum.APPROVED:
        raise HTTPException(status_code=400, detail="只有已审批通过的报价才能发送给客户")

    # 更新报价状态为已发送（如果有SENT状态，否则保持APPROVED）
    # 这里简化处理，不改变状态，只记录发送操作

    # 可选：记录发送日志或通知

    return ResponseModel(
        code=200,
        message="报价已发送给客户",
        data={
            "quote_id": quote_id,
            "send_method": send_method,
            "send_to": send_to,
            "sent_at": datetime.now().isoformat()
        }
    )


# ==================== 单级审批（兼容旧接口） ====================


@router.post("/quotes/{quote_id}/approve", response_model=ResponseModel)
def approve_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    approve_request: QuoteApproveRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批报价（单级审批，兼容旧接口）
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if not quote.current_version_id:
        raise HTTPException(status_code=400, detail="报价没有当前版本")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    if approve_request.approved:
        quote.status = "APPROVED"
        version.approved_by = current_user.id
        version.approved_at = datetime.now()
    else:
        quote.status = "REJECTED"

    db.commit()

    return ResponseModel(
        code=200,
        message="报价审批完成" if approve_request.approved else "报价已驳回"
    )


@router.get("/quotes/{quote_id}/approvals", response_model=List[QuoteApprovalResponse])
def get_quote_approvals(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价审批记录列表
    """
    approvals = db.query(QuoteApproval).filter(QuoteApproval.quote_id == quote_id).order_by(QuoteApproval.approval_level).all()

    result = []
    for approval in approvals:
        approver_name = None
        if approval.approver_id:
            approver = db.query(User).filter(User.id == approval.approver_id).first()
            approver_name = approver.real_name if approver else None

        result.append(QuoteApprovalResponse(
            id=approval.id,
            quote_id=approval.quote_id,
            approval_level=approval.approval_level,
            approval_role=approval.approval_role,
            approver_id=approval.approver_id,
            approver_name=approver_name,
            approval_result=approval.approval_result,
            approval_opinion=approval.approval_opinion,
            status=approval.status,
            approved_at=approval.approved_at,
            due_date=approval.due_date,
            is_overdue=approval.is_overdue or False,
            created_at=approval.created_at,
            updated_at=approval.updated_at
        ))

    return result


# ==================== 多级审批 ====================


@router.put("/quote-approvals/{approval_id}/approve", response_model=QuoteApprovalResponse)
def approve_quote_approval(
    *,
    db: Session = Depends(deps.get_db),
    approval_id: int,
    approval_opinion: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批通过（多级审批）
    """
    approval = db.query(QuoteApproval).filter(QuoteApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审批状态的记录")

    # 检查审批权限
    if not security.check_sales_approval_permission(current_user, approval, db):
        raise HTTPException(
            status_code=403,
            detail="您没有权限审批此记录"
        )

    approval.approval_result = "APPROVED"
    approval.approval_opinion = approval_opinion
    approval.approved_at = datetime.now()
    approval.status = "COMPLETED"
    approval.approver_id = current_user.id
    approver = db.query(User).filter(User.id == current_user.id).first()
    if approver:
        approval.approver_name = approver.real_name

    # 检查是否所有审批都已完成
    quote = db.query(Quote).filter(Quote.id == approval.quote_id).first()
    if quote:
        pending_approvals = db.query(QuoteApproval).filter(
            QuoteApproval.quote_id == approval.quote_id,
            QuoteApproval.status == "PENDING"
        ).count()

        if pending_approvals == 0:
            # 所有审批都已完成，更新报价状态
            quote.status = "APPROVED"
            version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
            if version:
                version.approved_by = current_user.id
                version.approved_at = datetime.now()

    db.commit()
    db.refresh(approval)

    approver_name = approval.approver_name
    return QuoteApprovalResponse(
        id=approval.id,
        quote_id=approval.quote_id,
        approval_level=approval.approval_level,
        approval_role=approval.approval_role,
        approver_id=approval.approver_id,
        approver_name=approver_name,
        approval_result=approval.approval_result,
        approval_opinion=approval.approval_opinion,
        status=approval.status,
        approved_at=approval.approved_at,
        due_date=approval.due_date,
        is_overdue=approval.is_overdue or False,
        created_at=approval.created_at,
        updated_at=approval.updated_at
    )


@router.put("/quote-approvals/{approval_id}/reject", response_model=QuoteApprovalResponse)
def reject_quote_approval(
    *,
    db: Session = Depends(deps.get_db),
    approval_id: int,
    rejection_reason: str = Query(..., description="驳回原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批驳回（多级审批）
    """
    approval = db.query(QuoteApproval).filter(QuoteApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审批状态的记录")

    # 检查审批权限
    if not security.check_sales_approval_permission(current_user, approval, db):
        raise HTTPException(
            status_code=403,
            detail="您没有权限审批此记录"
        )

    approval.approval_result = "REJECTED"
    approval.approval_opinion = rejection_reason
    approval.approved_at = datetime.now()
    approval.status = "COMPLETED"
    approval.approver_id = current_user.id
    approver = db.query(User).filter(User.id == current_user.id).first()
    if approver:
        approval.approver_name = approver.real_name

    # 驳回后，报价状态变为被拒
    quote = db.query(Quote).filter(Quote.id == approval.quote_id).first()
    if quote:
        quote.status = "REJECTED"

    db.commit()
    db.refresh(approval)

    approver_name = approval.approver_name
    return QuoteApprovalResponse(
        id=approval.id,
        quote_id=approval.quote_id,
        approval_level=approval.approval_level,
        approval_role=approval.approval_role,
        approver_id=approval.approver_id,
        approver_name=approver_name,
        approval_result=approval.approval_result,
        approval_opinion=approval.approval_opinion,
        status=approval.status,
        approved_at=approval.approved_at,
        due_date=approval.due_date,
        is_overdue=approval.is_overdue or False,
        created_at=approval.created_at,
        updated_at=approval.updated_at
    )


# ==================== 审批工作流 ====================


@router.post("/quotes/{quote_id}/approval/start", response_model=ResponseModel)
def start_quote_approval(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    approval_request: ApprovalStartRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    启动报价审批流程
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if quote.status != QuoteStatusEnum.IN_REVIEW:
        raise HTTPException(status_code=400, detail="只有待审批状态的报价才能启动审批流程")

    # 获取报价金额用于路由
    version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
    routing_params = {
        "amount": float(version.total_price or 0) if version else 0
    }

    # 启动审批流程
    workflow_service = ApprovalWorkflowService(db)
    try:
        record = workflow_service.start_approval(
            entity_type=WorkflowTypeEnum.QUOTE,
            entity_id=quote_id,
            initiator_id=current_user.id,
            workflow_id=approval_request.workflow_id,
            routing_params=routing_params,
            comment=approval_request.comment
        )

        # 更新报价状态
        quote.status = QuoteStatusEnum.IN_REVIEW

        db.commit()

        return ResponseModel(
            code=200,
            message="审批流程已启动",
            data={"approval_record_id": record.id}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quotes/{quote_id}/approval-status", response_model=ApprovalStatusResponse)
def get_quote_approval_status(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价审批状态
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.QUOTE,
        entity_id=quote_id
    )

    if not record:
        return ApprovalStatusResponse(
            record=None,
            current_step_info=None,
            can_approve=False,
            can_reject=False,
            can_delegate=False,
            can_withdraw=False
        )

    # 获取当前步骤信息
    current_step_info = workflow_service.get_current_step(record.id)

    # 判断当前用户的操作权限
    can_approve = False
    can_reject = False
    can_delegate = False
    can_withdraw = False

    if record.status == ApprovalRecordStatusEnum.PENDING:
        if current_step_info:
            # 检查是否是当前审批人
            if current_step_info.get("approver_id") == current_user.id:
                can_approve = True
                can_reject = True
                if current_step_info.get("can_delegate"):
                    can_delegate = True

        # 检查是否可以撤回（只有发起人可以撤回）
        if record.initiator_id == current_user.id:
            can_withdraw = True

    # 构建响应
    record_dict = {
        **{c.name: getattr(record, c.name) for c in record.__table__.columns},
        "workflow_name": record.workflow.workflow_name if record.workflow else None,
        "initiator_name": record.initiator.real_name if record.initiator else None,
        "history": []
    }

    # 获取审批历史
    history_list = workflow_service.get_approval_history(record.id)
    for h in history_list:
        history_dict = {
            **{c.name: getattr(h, c.name) for c in h.__table__.columns},
            "approver_name": h.approver.real_name if h.approver else None,
            "delegate_to_name": h.delegate_to.real_name if h.delegate_to else None
        }
        record_dict["history"].append(ApprovalHistoryResponse(**history_dict))

    return ApprovalStatusResponse(
        record=ApprovalRecordResponse(**record_dict),
        current_step_info=current_step_info,
        can_approve=can_approve,
        can_reject=can_reject,
        can_delegate=can_delegate,
        can_withdraw=can_withdraw
    )


@router.post("/quotes/{quote_id}/approval/action", response_model=ResponseModel)
def quote_approval_action(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    action_request: ApprovalActionRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    报价审批操作（通过/驳回/委托/撤回）
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.QUOTE,
        entity_id=quote_id
    )

    if not record:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    try:
        if action_request.action == ApprovalActionEnum.APPROVE:
            record = workflow_service.approve_step(
                record_id=record.id,
                approver_id=current_user.id,
                comment=action_request.comment
            )

            # 如果审批完成，更新报价状态
            if record.status == ApprovalRecordStatusEnum.APPROVED:
                quote.status = QuoteStatusEnum.APPROVED
                version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
                if version:
                    version.approved_by = current_user.id
                    version.approved_at = datetime.now()

            message = "审批通过"

        elif action_request.action == ApprovalActionEnum.REJECT:
            record = workflow_service.reject_step(
                record_id=record.id,
                approver_id=current_user.id,
                comment=action_request.comment or "审批驳回"
            )

            # 驳回后更新报价状态
            quote.status = QuoteStatusEnum.REJECTED
            message = "审批已驳回"

        elif action_request.action == ApprovalActionEnum.DELEGATE:
            if not action_request.delegate_to_id:
                raise HTTPException(status_code=400, detail="委托操作需要指定委托给的用户ID")

            record = workflow_service.delegate_step(
                record_id=record.id,
                approver_id=current_user.id,
                delegate_to_id=action_request.delegate_to_id,
                comment=action_request.comment
            )
            message = "审批已委托"

        elif action_request.action == ApprovalActionEnum.WITHDRAW:
            record = workflow_service.withdraw_approval(
                record_id=record.id,
                initiator_id=current_user.id,
                comment=action_request.comment
            )

            # 撤回后恢复报价状态
            quote.status = QuoteStatusEnum.DRAFT
            message = "审批已撤回"

        else:
            raise HTTPException(status_code=400, detail=f"不支持的审批操作: {action_request.action}")

        db.commit()

        return ResponseModel(
            code=200,
            message=message,
            data={"approval_record_id": record.id, "status": record.status}
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quotes/{quote_id}/approval-history", response_model=List[ApprovalHistoryResponse])
def get_quote_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价审批历史
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.QUOTE,
        entity_id=quote_id
    )

    if not record:
        return []

    history_list = workflow_service.get_approval_history(record.id)
    result = []
    for h in history_list:
        history_dict = {
            **{c.name: getattr(h, c.name) for c in h.__table__.columns},
            "approver_name": h.approver.real_name if h.approver else None,
            "delegate_to_name": h.delegate_to.real_name if h.delegate_to else None
        }
        result.append(ApprovalHistoryResponse(**history_dict))

    return result


# ==================== 模板应用 ====================


@router.post("/quotes/{quote_id}/apply-template", response_model=QuoteVersionResponse)
def apply_cost_template_to_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    template_id: int = Query(..., description="成本模板ID"),
    version_id: Optional[int] = Query(None, description="报价版本ID，不指定则使用当前版本或创建新版本"),
    adjustments: Optional[str] = Query(None, description="调整项JSON"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    应用成本模板到报价
    """
    import json

    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    template = db.query(QuoteCostTemplate).filter(QuoteCostTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="成本模板不存在")

    if not template.is_active:
        raise HTTPException(status_code=400, detail="成本模板未启用")

    # 获取或创建报价版本
    if version_id:
        version = db.query(QuoteVersion).filter(QuoteVersion.id == version_id).first()
        if not version or version.quote_id != quote_id:
            raise HTTPException(status_code=404, detail="报价版本不存在")
    elif quote.current_version_id:
        version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
    else:
        # 创建新版本
        version_no = f"V{len(quote.versions) + 1}"
        version = QuoteVersion(
            quote_id=quote_id,
            version_no=version_no,
            created_by=current_user.id
        )
        db.add(version)
        db.flush()
        quote.current_version_id = version.id

    # 解析模板成本结构
    cost_structure = template.cost_structure if isinstance(template.cost_structure, dict) else json.loads(template.cost_structure) if template.cost_structure else {}

    # 解析调整项
    adj_dict = json.loads(adjustments) if isinstance(adjustments, str) and adjustments else {}

    # 应用模板成本项
    total_cost = Decimal('0')
    total_price = Decimal('0')

    for category in cost_structure.get('categories', []):
        for item_template in category.get('items', []):
            item_name = item_template.get('item_name', '')

            # 检查是否有调整
            if item_name in adj_dict:
                adj = adj_dict[item_name]
                qty = Decimal(str(adj.get('qty', item_template.get('default_qty', 0))))
                unit_price = Decimal(str(adj.get('unit_price', item_template.get('default_unit_price', 0))))
                cost = Decimal(str(adj.get('cost', item_template.get('default_cost', 0))))
            else:
                qty = Decimal(str(item_template.get('default_qty', 0)))
                unit_price = Decimal(str(item_template.get('default_unit_price', 0)))
                cost = Decimal(str(item_template.get('default_cost', 0)))

            # 创建报价明细
            item = QuoteItem(
                quote_version_id=version.id,
                item_type=item_template.get('item_type', category.get('category', '')),
                item_name=item_name,
                specification=item_template.get('specification'),
                unit=item_template.get('unit'),
                qty=float(qty),
                unit_price=float(unit_price),
                cost=float(cost),
                cost_category=category.get('category', ''),
                cost_source='TEMPLATE',
                lead_time_days=item_template.get('lead_time_days')
            )
            db.add(item)

            total_cost += cost * qty
            total_price += unit_price * qty

    # 更新版本信息
    version.cost_template_id = template_id
    version.total_price = float(total_price)
    version.cost_total = float(total_cost)
    if total_price > 0:
        version.gross_margin = float((total_price - total_cost) / total_price * 100)

    # 更新模板使用次数
    template.usage_count = (template.usage_count or 0) + 1

    db.commit()
    db.refresh(version)

    # 返回版本信息
    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all()
    version_dict = {
        **{c.name: getattr(version, c.name) for c in version.__table__.columns},
        "created_by_name": version.creator.real_name if version.creator else None,
        "approved_by_name": version.approver.real_name if version.approver else None,
        "items": [QuoteItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns}) for item in items],
    }
    return QuoteVersionResponse(**version_dict)


# ==================== 成本计算与检查 ====================


@router.post("/quotes/{quote_id}/calculate-cost", response_model=ResponseModel)
def calculate_quote_cost(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_id: Optional[int] = Query(None, description="报价版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    自动计算报价成本
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    target_version_id = version_id or quote.current_version_id
    if not target_version_id:
        raise HTTPException(status_code=400, detail="报价没有指定版本")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == target_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == target_version_id).all()

    total_cost = Decimal('0')
    total_price = Decimal(str(version.total_price or 0))

    for item in items:
        item_cost = Decimal(str(item.cost or 0)) * Decimal(str(item.qty or 0))
        total_cost += item_cost

    # 更新版本成本
    version.cost_total = float(total_cost)

    # 计算毛利率
    if total_price > 0:
        gross_margin = ((total_price - total_cost) / total_price * 100)
        version.gross_margin = float(gross_margin)
    else:
        version.gross_margin = None

    db.commit()
    db.refresh(version)

    return ResponseModel(
        code=200,
        message="成本计算完成",
        data={
            "total_price": float(total_price),
            "total_cost": float(total_cost),
            "gross_margin": float(version.gross_margin) if version.gross_margin else None
        }
    )


@router.get("/quotes/{quote_id}/cost-check", response_model=CostCheckResponse)
def check_quote_cost(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_id: Optional[int] = Query(None, description="报价版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    成本完整性检查
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    target_version_id = version_id or quote.current_version_id
    if not target_version_id:
        raise HTTPException(status_code=400, detail="报价没有指定版本")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == target_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == target_version_id).all()

    checks = []

    # 检查1：是否有成本明细
    if not items:
        checks.append({
            "check_item": "成本明细",
            "status": "FAIL",
            "message": "未添加任何成本明细"
        })
    else:
        checks.append({
            "check_item": "成本明细",
            "status": "PASS",
            "message": f"已添加{len(items)}项成本明细"
        })

    # 检查2：成本项是否完整
    incomplete_items = []
    for item in items:
        if not item.cost or item.cost == 0:
            incomplete_items.append(item.item_name or f"项目{item.id}")

    if incomplete_items:
        checks.append({
            "check_item": "成本项完整性",
            "status": "FAIL",
            "message": f"以下成本项未填写成本：{', '.join(incomplete_items[:5])}{'...' if len(incomplete_items) > 5 else ''}"
        })
    else:
        checks.append({
            "check_item": "成本项完整性",
            "status": "PASS",
            "message": "所有成本项已填写"
        })

    # 检查3：毛利率检查
    margin_threshold = Decimal('20.0')  # 默认阈值20%
    current_margin = version.gross_margin or 0

    if current_margin < margin_threshold:
        checks.append({
            "check_item": "毛利率检查",
            "status": "WARNING" if current_margin >= 15 else "FAIL",
            "message": f"毛利率{current_margin:.2f}%，低于阈值{margin_threshold}%",
            "current_margin": float(current_margin),
            "threshold": float(margin_threshold)
        })
    else:
        checks.append({
            "check_item": "毛利率检查",
            "status": "PASS",
            "message": f"毛利率{current_margin:.2f}%，符合要求"
        })

    # 检查4：交期检查
    items_without_leadtime = []
    for item in items:
        if not item.lead_time_days and item.item_type in ['硬件', '外购件', '标准件']:
            items_without_leadtime.append(item.item_name or f"项目{item.id}")

    if items_without_leadtime:
        checks.append({
            "check_item": "交期校验",
            "status": "WARNING",
            "message": f"以下关键物料未填写交期：{', '.join(items_without_leadtime[:5])}{'...' if len(items_without_leadtime) > 5 else ''}"
        })
    else:
        checks.append({
            "check_item": "交期校验",
            "status": "PASS",
            "message": "关键物料交期已填写"
        })

    is_complete = all(check["status"] == "PASS" for check in checks)

    return CostCheckResponse(
        is_complete=is_complete,
        checks=checks,
        total_price=Decimal(str(version.total_price or 0)),
        total_cost=Decimal(str(version.cost_total or 0)),
        gross_margin=Decimal(str(current_margin))
    )


# ==================== 交期验证 ====================


@router.get("/quotes/{quote_id}/delivery-validation", response_model=ResponseModel)
def validate_quote_delivery(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_id: Optional[int] = Query(None, description="报价版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    交期校验API

    验证报价交期的合理性，包括：
    - 物料交期查询
    - 项目周期估算
    - 交期合理性分析
    - 优化建议
    """
    from app.services.delivery_validation_service import delivery_validation_service

    # 获取报价单
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    # 获取版本
    if version_id:
        version = db.query(QuoteVersion).filter(
            QuoteVersion.id == version_id,
            QuoteVersion.quote_id == quote_id
        ).first()
    else:
        version = db.query(QuoteVersion).filter(
            QuoteVersion.quote_id == quote_id,
            QuoteVersion.is_current == True
        ).first()

    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    # 获取报价明细
    items = db.query(QuoteItem).filter(
        QuoteItem.quote_version_id == version.id
    ).all()

    # 执行交期校验
    validation_result = delivery_validation_service.validate_delivery_date(
        db, quote, version, items
    )

    return ResponseModel(
        code=200,
        message="交期校验完成",
        data=validation_result
    )


@router.get("/quotes/project-cycle-estimate", response_model=ResponseModel)
def estimate_project_cycle(
    *,
    contract_amount: Optional[float] = Query(None, description="合同金额（用于估算）"),
    project_type: Optional[str] = Query(None, description="项目类型"),
    complexity_level: str = Query("MEDIUM", description="复杂度：SIMPLE/MEDIUM/COMPLEX"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目周期估算API

    根据项目类型、金额、复杂度估算项目周期
    返回各阶段工期建议
    """
    from app.services.delivery_validation_service import DeliveryValidationService

    cycle_estimate = DeliveryValidationService.estimate_project_cycle(
        db=None,  # 不需要数据库
        contract_amount=contract_amount,
        project_type=project_type,
        complexity_level=complexity_level
    )

    return ResponseModel(
        code=200,
        message="项目周期估算完成",
        data=cycle_estimate
    )


# ==================== 成本审批 ====================


@router.post("/quotes/{quote_id}/cost-approval/submit", response_model=QuoteCostApprovalResponse, status_code=201)
def submit_cost_approval(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    approval_in: QuoteCostApprovalCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交成本审批
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == approval_in.quote_version_id).first()
    if not version or version.quote_id != quote_id:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    # 执行成本检查
    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all()
    total_cost = sum([float(item.cost or 0) * float(item.qty or 0) for item in items])
    total_price = float(version.total_price or 0)
    gross_margin = float(version.gross_margin or 0) if version.gross_margin else ((total_price - total_cost) / total_price * 100 if total_price > 0 else 0)

    # 判断毛利率状态
    margin_threshold = 20.0 if approval_in.approval_level == 1 else 15.0
    if gross_margin >= margin_threshold:
        margin_status = "PASS"
    elif gross_margin >= 15.0:
        margin_status = "WARNING"
    else:
        margin_status = "FAIL"

    # 创建审批记录
    approval = QuoteCostApproval(
        quote_id=quote_id,
        quote_version_id=approval_in.quote_version_id,
        approval_status="PENDING",
        approval_level=approval_in.approval_level,
        current_approver_id=None,  # 根据审批层级确定审批人
        total_price=total_price,
        total_cost=total_cost,
        gross_margin=gross_margin,
        margin_threshold=margin_threshold,
        margin_status=margin_status,
        cost_complete=len(items) > 0 and all(item.cost and item.cost > 0 for item in items),
        delivery_check=all(item.lead_time_days for item in items if item.item_type in ['硬件', '外购件']),
        risk_terms_check=bool(version.risk_terms),
        approval_comment=approval_in.comment
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)

    approval_dict = {
        **{c.name: getattr(approval, c.name) for c in approval.__table__.columns},
        "current_approver_name": approval.current_approver.real_name if approval.current_approver else None,
        "approved_by_name": approval.approver.real_name if approval.approver else None
    }
    return QuoteCostApprovalResponse(**approval_dict)


@router.post("/quotes/{quote_id}/cost-approval/{approval_id}/approve", response_model=QuoteCostApprovalResponse)
def approve_cost(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    approval_id: int,
    action: QuoteCostApprovalAction,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批通过
    """
    approval = db.query(QuoteCostApproval).filter(
        QuoteCostApproval.id == approval_id,
        QuoteCostApproval.quote_id == quote_id
    ).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.approval_status != "PENDING":
        raise HTTPException(status_code=400, detail="审批记录不是待审批状态")

    approval.approval_status = "APPROVED"
    approval.approved_by = current_user.id
    approval.approved_at = datetime.now()
    approval.approval_comment = action.comment

    # 如果是最低层级审批通过，更新报价版本状态
    if approval.approval_level == 1:
        version = db.query(QuoteVersion).filter(QuoteVersion.id == approval.quote_version_id).first()
        if version:
            version.cost_breakdown_complete = approval.cost_complete
            version.margin_warning = approval.margin_status in ["WARNING", "FAIL"]

    db.commit()
    db.refresh(approval)

    approval_dict = {
        **{c.name: getattr(approval, c.name) for c in approval.__table__.columns},
        "current_approver_name": approval.current_approver.real_name if approval.current_approver else None,
        "approved_by_name": approval.approver.real_name if approval.approver else None
    }
    return QuoteCostApprovalResponse(**approval_dict)


@router.post("/quotes/{quote_id}/cost-approval/{approval_id}/reject", response_model=QuoteCostApprovalResponse)
def reject_cost(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    approval_id: int,
    action: QuoteCostApprovalAction,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批驳回
    """
    if not action.reason:
        raise HTTPException(status_code=400, detail="驳回原因不能为空")

    approval = db.query(QuoteCostApproval).filter(
        QuoteCostApproval.id == approval_id,
        QuoteCostApproval.quote_id == quote_id
    ).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    if approval.approval_status != "PENDING":
        raise HTTPException(status_code=400, detail="审批记录不是待审批状态")

    approval.approval_status = "REJECTED"
    approval.approved_by = current_user.id
    approval.approved_at = datetime.now()
    approval.rejected_reason = action.reason
    approval.approval_comment = action.comment

    db.commit()
    db.refresh(approval)

    approval_dict = {
        **{c.name: getattr(approval, c.name) for c in approval.__table__.columns},
        "current_approver_name": approval.current_approver.real_name if approval.current_approver else None,
        "approved_by_name": approval.approver.real_name if approval.approver else None
    }
    return QuoteCostApprovalResponse(**approval_dict)


@router.get("/quotes/{quote_id}/cost-approval/history", response_model=List[QuoteCostApprovalResponse])
def get_cost_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取成本审批历史
    """
    approvals = db.query(QuoteCostApproval).filter(
        QuoteCostApproval.quote_id == quote_id
    ).order_by(desc(QuoteCostApproval.created_at)).all()

    result = []
    for approval in approvals:
        approval_dict = {
            **{c.name: getattr(approval, c.name) for c in approval.__table__.columns},
            "current_approver_name": approval.current_approver.real_name if approval.current_approver else None,
            "approved_by_name": approval.approver.real_name if approval.approver else None
        }
        result.append(QuoteCostApprovalResponse(**approval_dict))

    return result


# ==================== 成本对比 ====================


@router.get("/quotes/{quote_id}/cost-comparison", response_model=CostComparisonResponse)
def compare_quote_costs(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_ids: Optional[str] = Query(None, description="版本ID列表（逗号分隔），对比多个版本"),
    compare_quote_id: Optional[int] = Query(None, description="对比报价ID（与其他报价对比）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    报价成本对比分析
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    # 获取当前版本
    current_version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
    if not current_version:
        raise HTTPException(status_code=400, detail="报价没有当前版本")

    current_items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == current_version.id).all()
    current_total_price = float(current_version.total_price or 0)
    current_total_cost = float(current_version.cost_total or 0)
    current_margin = float(current_version.gross_margin or 0)

    current_version_data = {
        "version_no": current_version.version_no,
        "total_price": current_total_price,
        "total_cost": current_total_cost,
        "gross_margin": current_margin
    }

    # 对比数据
    previous_version_data = None
    comparison = None
    breakdown_comparison = []

    # 如果指定了版本ID列表
    if version_ids:
        version_id_list = [int(vid) for vid in version_ids.split(',') if vid.strip()]
        if len(version_id_list) > 0:
            prev_version = db.query(QuoteVersion).filter(QuoteVersion.id == version_id_list[0]).first()
            if prev_version:
                prev_items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == prev_version.id).all()
                prev_total_price = float(prev_version.total_price or 0)
                prev_total_cost = float(prev_version.cost_total or 0)
                prev_margin = float(prev_version.gross_margin or 0)

                previous_version_data = {
                    "version_no": prev_version.version_no,
                    "total_price": prev_total_price,
                    "total_cost": prev_total_cost,
                    "gross_margin": prev_margin
                }

                # 计算对比
                price_change = current_total_price - prev_total_price
                price_change_pct = (price_change / prev_total_price * 100) if prev_total_price > 0 else 0
                cost_change = current_total_cost - prev_total_cost
                cost_change_pct = (cost_change / prev_total_cost * 100) if prev_total_cost > 0 else 0
                margin_change = current_margin - prev_margin
                margin_change_pct = (margin_change / prev_margin * 100) if prev_margin > 0 else 0

                comparison = {
                    "price_change": round(price_change, 2),
                    "price_change_pct": round(price_change_pct, 2),
                    "cost_change": round(cost_change, 2),
                    "cost_change_pct": round(cost_change_pct, 2),
                    "margin_change": round(margin_change, 2),
                    "margin_change_pct": round(margin_change_pct, 2)
                }

                # 按分类对比
                current_by_category = {}
                for item in current_items:
                    category = item.cost_category or "其他"
                    if category not in current_by_category:
                        current_by_category[category] = 0
                    current_by_category[category] += float(item.cost or 0) * float(item.qty or 0)

                prev_by_category = {}
                for item in prev_items:
                    category = item.cost_category or "其他"
                    if category not in prev_by_category:
                        prev_by_category[category] = 0
                    prev_by_category[category] += float(item.cost or 0) * float(item.qty or 0)

                all_categories = set(list(current_by_category.keys()) + list(prev_by_category.keys()))
                for category in all_categories:
                    v1_amount = prev_by_category.get(category, 0)
                    v2_amount = current_by_category.get(category, 0)
                    change = v2_amount - v1_amount
                    change_pct = (change / v1_amount * 100) if v1_amount > 0 else 0
                    breakdown_comparison.append({
                        "category": category,
                        "v1_amount": round(v1_amount, 2),
                        "v2_amount": round(v2_amount, 2),
                        "change": round(change, 2),
                        "change_pct": round(change_pct, 2)
                    })

    return CostComparisonResponse(
        current_version=current_version_data,
        previous_version=previous_version_data,
        comparison=comparison,
        breakdown_comparison=breakdown_comparison if breakdown_comparison else None
    )


# ==================== 成本匹配建议 ====================


@router.post("/quotes/{quote_id}/items/auto-match-cost-suggestions", response_model=CostMatchSuggestionsResponse)
def get_cost_match_suggestions(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_id: Optional[int] = Query(None, description="版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取成本匹配建议（AI生成建议，不直接更新）
    根据物料名称和规格，从采购物料成本清单中生成匹配建议，包含异常检查
    """
    from app.services.cost_match_suggestion_service import (
        process_cost_match_suggestions,
        check_overall_anomalies,
        calculate_summary
    )

    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    target_version_id = version_id or quote.current_version_id
    if not target_version_id:
        raise HTTPException(status_code=400, detail="报价没有指定版本")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == target_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == target_version_id).all()

    # 获取成本清单查询
    cost_query = db.query(PurchaseMaterialCost).filter(
        PurchaseMaterialCost.is_active == True,
        PurchaseMaterialCost.is_standard_part == True
    )

    # 处理成本匹配建议
    suggestions, matched_count, unmatched_count, _, current_total_cost = process_cost_match_suggestions(
        db, items, cost_query
    )

    # 计算当前总价格
    current_total_price = float(version.total_price or 0)

    # 计算建议总成本
    suggested_total_cost = sum([
        float(s.suggested_cost or s.current_cost or 0) *
        float(next((item.qty for item in items if item.id == s.item_id), 0) or 0)
        for s in suggestions
    ])

    # 整体异常检查
    warnings = check_overall_anomalies(
        current_total_price, current_total_cost, suggested_total_cost, items, suggestions
    )

    # 计算汇总
    summary = calculate_summary(current_total_cost, current_total_price, items, suggestions)

    return CostMatchSuggestionsResponse(
        suggestions=suggestions,
        total_items=len(items),
        matched_count=matched_count,
        unmatched_count=unmatched_count,
        warnings=warnings if warnings else None,
        summary=summary
    )


@router.post("/quotes/{quote_id}/items/apply-cost-suggestions", response_model=ResponseModel)
def apply_cost_suggestions(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_id: Optional[int] = Query(None, description="版本ID，不指定则使用当前版本"),
    request: ApplyCostSuggestionsRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    应用成本匹配建议（人工确认后应用）
    将用户确认（可能修改过）的建议应用到报价明细中
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    target_version_id = version_id or quote.current_version_id
    if not target_version_id:
        raise HTTPException(status_code=400, detail="报价没有指定版本")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == target_version_id).all()
    item_dict = {item.id: item for item in items}

    applied_count = 0
    updated_cost_records = set()  # 记录已更新的成本记录，避免重复更新使用次数

    for suggestion_data in request.suggestions:
        item_id = suggestion_data.get("item_id")
        if not item_id:
            continue

        item = item_dict.get(item_id)
        if not item:
            continue

        # 应用建议（用户可能已修改）
        if "cost" in suggestion_data:
            item.cost = Decimal(str(suggestion_data["cost"]))
            item.cost_source = "HISTORY"

        if "specification" in suggestion_data:
            item.specification = suggestion_data["specification"]

        if "unit" in suggestion_data:
            item.unit = suggestion_data["unit"]

        if "lead_time_days" in suggestion_data:
            item.lead_time_days = suggestion_data["lead_time_days"]

        if "cost_category" in suggestion_data:
            item.cost_category = suggestion_data["cost_category"]

        db.add(item)
        applied_count += 1

        # 如果应用了成本建议，更新对应的成本记录使用次数
        # 注意：这里需要根据item_name匹配，因为suggestion_data中可能没有cost_record_id
        if "cost" in suggestion_data and item.item_name:
            matched_cost = db.query(PurchaseMaterialCost).filter(
                PurchaseMaterialCost.is_active == True,
                PurchaseMaterialCost.material_name.like(f"%{item.item_name}%")
            ).order_by(desc(PurchaseMaterialCost.match_priority), desc(PurchaseMaterialCost.purchase_date)).first()

            if matched_cost and matched_cost.id not in updated_cost_records:
                matched_cost.usage_count = (matched_cost.usage_count or 0) + 1
                matched_cost.last_used_at = datetime.now()
                db.add(matched_cost)
                updated_cost_records.add(matched_cost.id)

    db.commit()

    # 重新计算总成本
    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == target_version_id).all()
    total_cost = sum([float(item.cost or 0) * float(item.qty or 0) for item in items])
    version = db.query(QuoteVersion).filter(QuoteVersion.id == target_version_id).first()
    if version:
        version.cost_total = total_cost
        total_price = float(version.total_price or 0)
        if total_price > 0:
            version.gross_margin = ((total_price - total_cost) / total_price * 100)
        db.add(version)
        db.commit()

    return ResponseModel(
        code=200,
        message=f"已应用 {applied_count} 项成本建议",
        data={
            "applied_count": applied_count,
            "total_cost": total_cost
        }
    )


# ==================== 导出 ====================


@router.get("/quotes/export")
def export_quotes(
    *,
    db: Session = Depends(deps.get_db),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    include_items: bool = Query(False, description="是否包含明细"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.3: 导出报价列表（Excel）
    支持导出报价主表和明细（多 Sheet）
    """
    from app.services.excel_export_service import ExcelExportService, create_excel_response

    query = db.query(Quote)
    if keyword:
        query = query.filter(or_(Quote.quote_code.contains(keyword), Quote.opportunity.has(Opportunity.opp_name.contains(keyword))))
    if status:
        query = query.filter(Quote.status == status)
    if customer_id:
        query = query.filter(Quote.customer_id == customer_id)
    if owner_id:
        query = query.filter(Quote.owner_id == owner_id)

    quotes = query.order_by(Quote.created_at.desc()).all()
    export_service = ExcelExportService()

    if include_items:
        sheets = []
        quote_data = []
        for quote in quotes:
            version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
            quote_data.append({
                "quote_code": quote.quote_code,
                "opp_code": quote.opportunity.opp_code if quote.opportunity else '',
                "customer_name": quote.customer.customer_name if quote.customer else '',
                "status": quote.status,
                "total_price": float(version.total_price) if version and version.total_price else 0,
                "total_cost": float(version.total_cost) if version and version.total_cost else 0,
                "gross_margin": float(version.gross_margin) if version and version.gross_margin else 0,
                "valid_until": version.valid_until if version and version.valid_until else None,
                "owner_name": quote.owner.real_name if quote.owner else '',
                "created_at": quote.created_at,
            })
        sheets.append({
            "name": "报价列表",
            "data": quote_data,
            "columns": [
                {"key": "quote_code", "label": "报价编码", "width": 15},
                {"key": "opp_code", "label": "商机编码", "width": 15},
                {"key": "customer_name", "label": "客户名称", "width": 25},
                {"key": "status", "label": "状态", "width": 12},
                {"key": "total_price", "label": "报价金额", "width": 15, "format": export_service.format_currency},
                {"key": "total_cost", "label": "成本金额", "width": 15, "format": export_service.format_currency},
                {"key": "gross_margin", "label": "毛利率", "width": 12, "format": export_service.format_percentage},
                {"key": "valid_until", "label": "有效期至", "width": 12, "format": export_service.format_date},
                {"key": "owner_name", "label": "负责人", "width": 12},
                {"key": "created_at", "label": "创建时间", "width": 18, "format": export_service.format_date},
            ],
            "title": "报价列表"
        })
        item_data = []
        for quote in quotes:
            version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
            if version:
                items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all()
                for item in items:
                    item_data.append({
                        "quote_code": quote.quote_code,
                        "item_name": item.item_name or '',
                        "specification": item.specification or '',
                        "qty": float(item.qty) if item.qty else 0,
                        "unit": item.unit or '',
                        "unit_price": float(item.unit_price) if item.unit_price else 0,
                        "total_price": float(item.total_price) if item.total_price else 0,
                        "cost": float(item.cost) if item.cost else 0,
                        "item_type": item.item_type or '',
                    })
        sheets.append({
            "name": "报价明细",
            "data": item_data,
            "columns": [
                {"key": "quote_code", "label": "报价编码", "width": 15},
                {"key": "item_name", "label": "物料名称", "width": 30},
                {"key": "specification", "label": "规格型号", "width": 25},
                {"key": "qty", "label": "数量", "width": 10},
                {"key": "unit", "label": "单位", "width": 8},
                {"key": "unit_price", "label": "单价", "width": 12, "format": export_service.format_currency},
                {"key": "total_price", "label": "总价", "width": 12, "format": export_service.format_currency},
                {"key": "cost", "label": "成本", "width": 12, "format": export_service.format_currency},
                {"key": "item_type", "label": "类型", "width": 12},
            ],
            "title": "报价明细"
        })
        excel_data = export_service.export_multisheet(sheets)
    else:
        quote_data = []
        for quote in quotes:
            version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
            quote_data.append({
                "quote_code": quote.quote_code,
                "opp_code": quote.opportunity.opp_code if quote.opportunity else '',
                "customer_name": quote.customer.customer_name if quote.customer else '',
                "status": quote.status,
                "total_price": float(version.total_price) if version and version.total_price else 0,
                "total_cost": float(version.total_cost) if version and version.total_cost else 0,
                "gross_margin": float(version.gross_margin) if version and version.gross_margin else 0,
                "valid_until": version.valid_until if version and version.valid_until else None,
                "owner_name": quote.owner.real_name if quote.owner else '',
                "created_at": quote.created_at,
            })
        columns = [
            {"key": "quote_code", "label": "报价编码", "width": 15},
            {"key": "opp_code", "label": "商机编码", "width": 15},
            {"key": "customer_name", "label": "客户名称", "width": 25},
            {"key": "status", "label": "状态", "width": 12},
            {"key": "total_price", "label": "报价金额", "width": 15, "format": export_service.format_currency},
            {"key": "total_cost", "label": "成本金额", "width": 15, "format": export_service.format_currency},
            {"key": "gross_margin", "label": "毛利率", "width": 12, "format": export_service.format_percentage},
            {"key": "valid_until", "label": "有效期至", "width": 12, "format": export_service.format_date},
            {"key": "owner_name", "label": "负责人", "width": 12},
            {"key": "created_at", "label": "创建时间", "width": 18, "format": export_service.format_date},
        ]
        excel_data = export_service.export_to_excel(data=quote_data, columns=columns, sheet_name="报价列表", title="报价列表")

    filename = f"报价列表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return create_excel_response(excel_data, filename)


@router.get("/quotes/{quote_id}/pdf")
def export_quote_pdf(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.5: 导出报价单 PDF
    """
    from app.services.pdf_export_service import PDFExportService, create_pdf_response

    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
    if not version:
        raise HTTPException(status_code=400, detail="报价没有当前版本")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all()

    # 准备数据
    quote_data = {
        "quote_code": quote.quote_code,
        "customer_name": quote.customer.customer_name if quote.customer else '',
        "created_at": quote.created_at,
        "valid_until": version.valid_until,
        "total_price": float(version.total_price) if version.total_price else 0,
        "status": quote.status,
    }

    quote_items = [{
        "item_name": item.item_name or '',
        "specification": item.specification or '',
        "qty": float(item.qty) if item.qty else 0,
        "unit": item.unit or '',
        "unit_price": float(item.unit_price) if item.unit_price else 0,
        "total_price": float(item.total_price) if item.total_price else 0,
        "remark": item.remark or '',
    } for item in items]

    pdf_service = PDFExportService()
    pdf_data = pdf_service.export_quote_to_pdf(quote_data, quote_items)

    filename = f"报价单_{quote.quote_code}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return create_pdf_response(pdf_data, filename)
