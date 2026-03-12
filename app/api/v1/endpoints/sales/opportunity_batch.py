# -*- coding: utf-8 -*-
"""
商机批量操作 API

包含：批量更新阶段、批量更新负责人、批量标记赢单/输单
"""

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.sales_permissions import can_manage_sales_opportunity
from app.models.enums import OpportunityStageEnum
from app.models.sales import Opportunity
from app.models.user import User

router = APIRouter()


# ==================== 请求模型 ====================


class BatchUpdateStageRequest(BaseModel):
    """批量更新阶段请求"""

    opportunity_ids: List[int] = Field(
        ..., min_length=1, max_length=100, description="商机ID列表"
    )
    stage: str = Field(..., description="目标阶段")
    reason: Optional[str] = Field(None, description="变更原因")


class BatchUpdateOwnerRequest(BaseModel):
    """批量更新负责人请求"""

    opportunity_ids: List[int] = Field(
        ..., min_length=1, max_length=100, description="商机ID列表"
    )
    owner_id: int = Field(..., description="目标负责人ID")


class BatchWinLoseRequest(BaseModel):
    """批量赢单/输单请求"""

    opportunity_ids: List[int] = Field(
        ..., min_length=1, max_length=100, description="商机ID列表"
    )
    is_won: bool = Field(..., description="是否赢单，True为赢单，False为输单")
    reason: Optional[str] = Field(None, description="赢单/输单原因")


# ==================== 响应模型 ====================


class BatchResultItem(BaseModel):
    """批量操作单项结果"""

    id: int
    success: bool
    message: Optional[str] = None


class BatchOperationResponse(BaseModel):
    """批量操作响应"""

    total: int
    success_count: int
    failed_count: int
    results: List[BatchResultItem]


# ==================== API 端点 ====================


@router.post("/opportunities/batch/stage", response_model=BatchOperationResponse)
def batch_update_stage(
    *,
    db: Session = Depends(deps.get_db),
    request: BatchUpdateStageRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量更新商机阶段

    - 最多支持100条商机同时更新
    - 部分失败不影响其他商机
    - 阶段值需为有效的 OpportunityStageEnum
    """
    # 验证阶段值
    try:
        target_stage = OpportunityStageEnum(request.stage)
    except ValueError:
        valid_stages = [s.value for s in OpportunityStageEnum]
        raise HTTPException(
            status_code=400,
            detail=f"无效的阶段值，有效值为: {valid_stages}",
        )

    # 查询所有商机
    opportunities = (
        db.query(Opportunity).filter(Opportunity.id.in_(request.opportunity_ids)).all()
    )
    opp_map = {opp.id: opp for opp in opportunities}

    results: List[BatchResultItem] = []
    success_count = 0

    for opp_id in request.opportunity_ids:
        opp = opp_map.get(opp_id)

        if not opp:
            results.append(BatchResultItem(id=opp_id, success=False, message="商机不存在"))
            continue

        # 权限检查
        if not can_manage_sales_opportunity(db, current_user, opp):
            results.append(
                BatchResultItem(id=opp_id, success=False, message="无权限操作此商机")
            )
            continue

        # 检查是否已结束
        if opp.stage in [OpportunityStageEnum.WON, OpportunityStageEnum.LOST]:
            results.append(
                BatchResultItem(id=opp_id, success=False, message="已结束的商机无法更新阶段")
            )
            continue

        try:
            opp.stage = target_stage
            opp.updated_by = current_user.id
            opp.updated_at = datetime.utcnow()
            results.append(BatchResultItem(id=opp_id, success=True))
            success_count += 1
        except Exception as e:
            results.append(BatchResultItem(id=opp_id, success=False, message=str(e)))

    db.commit()

    return BatchOperationResponse(
        total=len(request.opportunity_ids),
        success_count=success_count,
        failed_count=len(request.opportunity_ids) - success_count,
        results=results,
    )


@router.post("/opportunities/batch/owner", response_model=BatchOperationResponse)
def batch_update_owner(
    *,
    db: Session = Depends(deps.get_db),
    request: BatchUpdateOwnerRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量更新商机负责人

    - 最多支持100条商机同时更新
    - 部分失败不影响其他商机
    """
    # 验证负责人存在
    new_owner = db.query(User).filter(User.id == request.owner_id).first()
    if not new_owner:
        raise HTTPException(status_code=404, detail="目标负责人不存在")

    # 查询所有商机
    opportunities = (
        db.query(Opportunity).filter(Opportunity.id.in_(request.opportunity_ids)).all()
    )
    opp_map = {opp.id: opp for opp in opportunities}

    results: List[BatchResultItem] = []
    success_count = 0

    for opp_id in request.opportunity_ids:
        opp = opp_map.get(opp_id)

        if not opp:
            results.append(BatchResultItem(id=opp_id, success=False, message="商机不存在"))
            continue

        # 权限检查
        if not can_manage_sales_opportunity(db, current_user, opp):
            results.append(
                BatchResultItem(id=opp_id, success=False, message="无权限操作此商机")
            )
            continue

        try:
            opp.owner_id = request.owner_id
            opp.updated_by = current_user.id
            opp.updated_at = datetime.utcnow()
            results.append(BatchResultItem(id=opp_id, success=True))
            success_count += 1
        except Exception as e:
            results.append(BatchResultItem(id=opp_id, success=False, message=str(e)))

    db.commit()

    return BatchOperationResponse(
        total=len(request.opportunity_ids),
        success_count=success_count,
        failed_count=len(request.opportunity_ids) - success_count,
        results=results,
    )


@router.post("/opportunities/batch/close", response_model=BatchOperationResponse)
def batch_close_opportunities(
    *,
    db: Session = Depends(deps.get_db),
    request: BatchWinLoseRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量关闭商机（赢单或输单）

    - 最多支持100条商机同时关闭
    - 部分失败不影响其他商机
    - is_won=True 标记为赢单，is_won=False 标记为输单
    """
    target_stage = OpportunityStageEnum.WON if request.is_won else OpportunityStageEnum.LOST

    # 查询所有商机
    opportunities = (
        db.query(Opportunity).filter(Opportunity.id.in_(request.opportunity_ids)).all()
    )
    opp_map = {opp.id: opp for opp in opportunities}

    results: List[BatchResultItem] = []
    success_count = 0

    for opp_id in request.opportunity_ids:
        opp = opp_map.get(opp_id)

        if not opp:
            results.append(BatchResultItem(id=opp_id, success=False, message="商机不存在"))
            continue

        # 权限检查
        if not can_manage_sales_opportunity(db, current_user, opp):
            results.append(
                BatchResultItem(id=opp_id, success=False, message="无权限操作此商机")
            )
            continue

        # 检查是否已结束
        if opp.stage in [OpportunityStageEnum.WON, OpportunityStageEnum.LOST]:
            results.append(
                BatchResultItem(id=opp_id, success=False, message="商机已关闭")
            )
            continue

        try:
            opp.stage = target_stage
            opp.closed_at = datetime.utcnow()
            if request.reason:
                opp.close_reason = request.reason
            opp.updated_by = current_user.id
            opp.updated_at = datetime.utcnow()
            results.append(BatchResultItem(id=opp_id, success=True))
            success_count += 1
        except Exception as e:
            results.append(BatchResultItem(id=opp_id, success=False, message=str(e)))

    db.commit()

    return BatchOperationResponse(
        total=len(request.opportunity_ids),
        success_count=success_count,
        failed_count=len(request.opportunity_ids) - success_count,
        results=results,
    )
