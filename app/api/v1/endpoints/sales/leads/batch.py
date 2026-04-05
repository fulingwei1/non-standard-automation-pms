# -*- coding: utf-8 -*-
"""
线索批量操作 API

包含：批量转商机、批量更新状态、批量分配负责人
"""

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import LeadStatusEnum
from app.models.project import Customer
from app.models.sales import Lead, LeadFollowUp, Opportunity
from app.models.user import User

from ..utils import generate_opportunity_code, validate_g1_lead_to_opportunity

router = APIRouter()


# ==================== 请求模型 ====================


class BatchConvertRequest(BaseModel):
    """批量转商机请求"""

    lead_ids: List[int] = Field(..., min_length=1, max_length=100, description="线索ID列表")
    customer_id: int = Field(..., description="目标客户ID")
    skip_validation: bool = Field(False, description="跳过G1验证")


class BatchUpdateStatusRequest(BaseModel):
    """批量更新状态请求"""

    lead_ids: List[int] = Field(..., min_length=1, max_length=100, description="线索ID列表")
    status: str = Field(..., description="目标状态")
    reason: Optional[str] = Field(None, description="变更原因")


class BatchAssignRequest(BaseModel):
    """批量分配负责人请求"""

    lead_ids: List[int] = Field(..., min_length=1, max_length=100, description="线索ID列表")
    owner_id: int = Field(..., description="目标负责人ID")


# ==================== 响应模型 ====================


class BatchResultItem(BaseModel):
    """批量操作单项结果"""

    id: int
    success: bool
    message: Optional[str] = None
    result_id: Optional[int] = None  # 转商机时返回商机ID


class BatchOperationResponse(BaseModel):
    """批量操作响应"""

    total: int
    success_count: int
    failed_count: int
    results: List[BatchResultItem]


# ==================== API 端点 ====================


@router.post("/leads/batch/convert", response_model=BatchOperationResponse)
def batch_convert_leads(
    *,
    db: Session = Depends(deps.get_db),
    request: BatchConvertRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量线索转商机

    - 最多支持100条线索同时转换
    - 返回每条线索的转换结果
    - 部分失败不影响其他线索
    """
    # 验证客户存在
    customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 查询所有线索
    leads = db.query(Lead).filter(Lead.id.in_(request.lead_ids)).all()
    lead_map = {lead.id: lead for lead in leads}

    results: List[BatchResultItem] = []
    success_count = 0

    for lead_id in request.lead_ids:
        lead = lead_map.get(lead_id)

        # 线索不存在
        if not lead:
            results.append(BatchResultItem(id=lead_id, success=False, message="线索不存在"))
            continue

        # 已转商机
        if lead.status == LeadStatusEnum.CONVERTED:
            results.append(BatchResultItem(id=lead_id, success=False, message="线索已转商机"))
            continue

        # 无效线索
        if lead.status == LeadStatusEnum.INVALID:
            results.append(BatchResultItem(id=lead_id, success=False, message="无效线索不能转商机"))
            continue

        # G1验证
        if not request.skip_validation:
            is_valid, messages = validate_g1_lead_to_opportunity(lead, None, db)
            errors = [
                msg
                for msg in messages
                if not msg.startswith("技术评估") and not msg.startswith("存在")
            ]
            if errors:
                results.append(
                    BatchResultItem(
                        id=lead_id, success=False, message=f"G1验证失败: {errors[0]}"
                    )
                )
                continue

        try:
            # 生成商机
            opp_code = generate_opportunity_code(db)
            opportunity = Opportunity(
                opp_code=opp_code,
                lead_id=lead_id,
                customer_id=request.customer_id,
                opp_name=f"{lead.customer_name} - {lead.demand_summary[:50] if lead.demand_summary else '商机'}",
                owner_id=lead.owner_id,
                stage="DISCOVERY",
                gate_status="PASS" if not request.skip_validation else "PENDING",
                gate_passed_at=datetime.now() if not request.skip_validation else None,
            )
            db.add(opportunity)
            db.flush()

            # 更新线索状态
            lead.status = LeadStatusEnum.CONVERTED

            results.append(
                BatchResultItem(id=lead_id, success=True, result_id=opportunity.id)
            )
            success_count += 1

        except Exception as e:
            results.append(
                BatchResultItem(id=lead_id, success=False, message=f"转换失败: {str(e)}")
            )

    db.commit()

    return BatchOperationResponse(
        total=len(request.lead_ids),
        success_count=success_count,
        failed_count=len(request.lead_ids) - success_count,
        results=results,
    )


@router.post("/leads/batch/status", response_model=BatchOperationResponse)
def batch_update_status(
    *,
    db: Session = Depends(deps.get_db),
    request: BatchUpdateStatusRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量更新线索状态

    - 支持批量标记为无效、跟进中等状态
    - 已转商机的线索不能修改状态
    """
    # 验证状态值有效
    valid_statuses = [s.value for s in LeadStatusEnum]
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=400, detail=f"无效状态值，允许值: {', '.join(valid_statuses)}"
        )

    # 查询所有线索
    leads = db.query(Lead).filter(Lead.id.in_(request.lead_ids)).all()
    lead_map = {lead.id: lead for lead in leads}

    results: List[BatchResultItem] = []
    success_count = 0

    for lead_id in request.lead_ids:
        lead = lead_map.get(lead_id)

        if not lead:
            results.append(BatchResultItem(id=lead_id, success=False, message="线索不存在"))
            continue

        if lead.status == LeadStatusEnum.CONVERTED:
            results.append(
                BatchResultItem(id=lead_id, success=False, message="已转商机的线索不能修改状态")
            )
            continue

        try:
            old_status = lead.status
            lead.status = request.status

            # 记录跟进
            if request.reason:
                follow_up = LeadFollowUp(
                    lead_id=lead_id,
                    follow_up_type="OTHER",
                    content=f"状态变更：{old_status} → {request.status}。原因：{request.reason}",
                    created_by=current_user.id,
                )
                db.add(follow_up)

            results.append(BatchResultItem(id=lead_id, success=True))
            success_count += 1

        except Exception as e:
            results.append(
                BatchResultItem(id=lead_id, success=False, message=f"更新失败: {str(e)}")
            )

    db.commit()

    return BatchOperationResponse(
        total=len(request.lead_ids),
        success_count=success_count,
        failed_count=len(request.lead_ids) - success_count,
        results=results,
    )


@router.post("/leads/batch/assign", response_model=BatchOperationResponse)
def batch_assign_owner(
    *,
    db: Session = Depends(deps.get_db),
    request: BatchAssignRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量分配线索负责人

    - 可用于线索池分配或批量转移
    """
    # 验证目标负责人存在
    new_owner = db.query(User).filter(User.id == request.owner_id).first()
    if not new_owner:
        raise HTTPException(status_code=404, detail="目标负责人不存在")

    # 查询所有线索
    leads = db.query(Lead).filter(Lead.id.in_(request.lead_ids)).all()
    lead_map = {lead.id: lead for lead in leads}

    results: List[BatchResultItem] = []
    success_count = 0

    for lead_id in request.lead_ids:
        lead = lead_map.get(lead_id)

        if not lead:
            results.append(BatchResultItem(id=lead_id, success=False, message="线索不存在"))
            continue

        try:
            old_owner_name = lead.owner.real_name if lead.owner else "无"
            lead.owner_id = request.owner_id

            # 记录跟进
            follow_up = LeadFollowUp(
                lead_id=lead_id,
                follow_up_type="OTHER",
                content=f"负责人变更：{old_owner_name} → {new_owner.real_name}",
                created_by=current_user.id,
            )
            db.add(follow_up)

            results.append(BatchResultItem(id=lead_id, success=True))
            success_count += 1

        except Exception as e:
            results.append(
                BatchResultItem(id=lead_id, success=False, message=f"分配失败: {str(e)}")
            )

    db.commit()

    return BatchOperationResponse(
        total=len(request.lead_ids),
        success_count=success_count,
        failed_count=len(request.lead_ids) - success_count,
        results=results,
    )
