# -*- coding: utf-8 -*-
"""
方案版本和绑定验证 API路由
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_db
from app.models.sales.quotes import QuoteVersion
from app.models.sales.solution_version import SolutionVersion
from app.models.user import User
from app.schemas.sales.solution_version import (
    ApprovalRequest,
    BindingValidationResponse,
    CostSyncResponse,
    ImpactCheckResponse,
    SolutionVersionCreate,
    SolutionVersionListResponse,
    SolutionVersionResponse,
    SolutionVersionUpdate,
    VersionCompareResponse,
)
from app.services.sales.binding_validation_service import BindingValidationService
from app.services.sales.solution_version_service import SolutionVersionService

router = APIRouter(prefix="/sales", tags=["方案版本管理"])


# ==================== 方案版本管理 ====================


@router.post(
    "/solutions/{solution_id}/versions",
    response_model=SolutionVersionResponse,
    summary="创建方案版本",
)
async def create_solution_version(
    solution_id: int,
    request: SolutionVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建方案新版本

    **版本号规则**：
    - 首个版本：V1.0
    - 基于 draft 状态修改：V1.1, V1.2, ...
    - 基于 approved 状态创建：V2.0, V3.0, ...

    **参数**：
    - solution_id: 方案ID
    - request: 版本内容
    """
    try:
        service = SolutionVersionService(db)
        version = await service.create_version(
            solution_id=solution_id,
            content=request.model_dump(exclude_none=True),
            created_by=current_user.id,
            change_reason=request.change_reason,
        )
        return version
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建版本失败: {str(e)}",
        )


@router.get(
    "/solutions/{solution_id}/versions",
    response_model=List[SolutionVersionListResponse],
    summary="获取版本历史",
)
async def get_version_history(
    solution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取方案的版本历史列表

    返回按创建时间降序排列的版本列表。
    """
    service = SolutionVersionService(db)
    versions = await service.get_version_history(solution_id)
    return versions


@router.get(
    "/solution-versions/{version_id}",
    response_model=SolutionVersionResponse,
    summary="获取版本详情",
)
async def get_solution_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取方案版本详细信息"""
    version = db.query(SolutionVersion).get(version_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="版本不存在")
    return version


@router.put(
    "/solution-versions/{version_id}",
    response_model=SolutionVersionResponse,
    summary="更新版本内容",
)
async def update_solution_version(
    version_id: int,
    request: SolutionVersionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新方案版本内容

    **注意**：仅 draft 状态的版本可以更新
    """
    version = db.query(SolutionVersion).get(version_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="版本不存在")

    if version.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"只能更新 draft 状态的版本，当前状态：{version.status}",
        )

    # 更新字段
    update_data = request.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(version, key, value)

    version.updated_at = datetime.now()
    db.commit()
    db.refresh(version)

    return version


@router.post(
    "/solution-versions/{version_id}/submit",
    response_model=SolutionVersionResponse,
    summary="提交审核",
)
async def submit_for_review(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    提交版本审核

    将版本状态从 draft 改为 pending_review。
    """
    try:
        service = SolutionVersionService(db)
        version = await service.submit_for_review(version_id)
        return version
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/solution-versions/{version_id}/approve",
    response_model=SolutionVersionResponse,
    summary="审批版本",
)
async def approve_solution_version(
    version_id: int,
    request: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    审批方案版本

    **审批动作**：
    - approve：审批通过，版本生效
    - reject：驳回，需要修改

    审批通过后，会自动更新方案的 current_version_id。
    """
    try:
        service = SolutionVersionService(db)

        if request.action == "approve":
            version = await service.approve_version(
                version_id=version_id,
                approved_by=current_user.id,
                comments=request.comments,
            )
        elif request.action == "reject":
            if not request.comments:
                raise ValueError("驳回必须填写原因")
            version = await service.reject_version(
                version_id=version_id,
                rejected_by=current_user.id,
                comments=request.comments,
            )
        else:
            raise ValueError(f"无效的审批动作：{request.action}")

        return version
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/solution-versions/compare",
    response_model=VersionCompareResponse,
    summary="版本对比",
)
async def compare_versions(
    version_id_1: int,
    version_id_2: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    对比两个版本的差异

    返回两个版本的关键字段差异。
    """
    try:
        service = SolutionVersionService(db)
        result = await service.compare_versions(version_id_1, version_id_2)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==================== 绑定验证 ====================


@router.post(
    "/quote-versions/{version_id}/validate-binding",
    response_model=BindingValidationResponse,
    summary="验证报价绑定",
)
async def validate_quote_binding(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    验证报价版本的绑定状态

    **检查项**：
    1. 方案版本是否已绑定
    2. 方案版本是否已审批
    3. 成本估算是否已绑定
    4. 成本估算是否已审批
    5. 成本估算是否绑定正确的方案版本
    6. 报价金额是否与成本一致

    **返回状态**：
    - valid：绑定有效
    - outdated：绑定有警告（如方案版本不是最新）
    - invalid：绑定无效（存在严重问题）
    """
    try:
        service = BindingValidationService(db)
        result = await service.validate_quote_binding(version_id)

        return BindingValidationResponse(
            quote_version_id=result.quote_version_id,
            status=result.status,
            issues=[
                {
                    "level": issue.level.value,
                    "code": issue.code.value,
                    "message": issue.message,
                    "details": issue.details,
                }
                for issue in result.issues
            ],
            validated_at=result.validated_at,
            is_valid=result.is_valid,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/quote-versions/{version_id}/sync-cost",
    response_model=CostSyncResponse,
    summary="同步成本到报价",
)
async def sync_cost_to_quote(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    同步成本到报价

    从绑定的成本估算同步 cost_total 到报价版本，
    并重新计算毛利率。

    **前置条件**：报价必须已绑定成本估算
    """
    try:
        service = BindingValidationService(db)
        qv = await service.sync_cost_to_quote(version_id)

        return CostSyncResponse(
            quote_version_id=qv.id,
            cost_total=qv.cost_total,
            gross_margin=qv.gross_margin,
            binding_status=qv.binding_status,
            synced_at=qv.binding_validated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/solution-versions/{version_id}/impact",
    response_model=ImpactCheckResponse,
    summary="检查更新影响",
)
async def check_solution_update_impact(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    检查方案版本更新的影响

    返回绑定此方案版本的成本估算和报价列表，
    用于在更新前评估影响范围。
    """
    service = BindingValidationService(db)
    affected = await service.check_solution_update_impact(version_id)

    return ImpactCheckResponse(
        affected_items=affected,
        total_count=len(affected),
    )


# ==================== 报价绑定管理 ====================


@router.post(
    "/quote-versions/{version_id}/bind",
    summary="绑定方案和成本",
)
async def bind_quote_version(
    version_id: int,
    solution_version_id: int,
    cost_estimation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    为报价版本绑定方案版本和成本估算

    **绑定规则**：
    1. 成本估算必须绑定到指定的方案版本
    2. 绑定后会自动同步 cost_total
    """
    from app.models.sales.presale_ai_cost import PresaleAICostEstimation

    # 获取报价版本
    qv = db.query(QuoteVersion).get(version_id)
    if not qv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="报价版本不存在")

    # 获取成本估算
    ce = db.query(PresaleAICostEstimation).get(cost_estimation_id)
    if not ce:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成本估算不存在")

    # 验证成本估算绑定的方案版本
    if ce.solution_version_id != solution_version_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"成本估算绑定的方案版本({ce.solution_version_id})与指定的方案版本({solution_version_id})不一致",
        )

    # 执行绑定
    qv.solution_version_id = solution_version_id
    qv.cost_estimation_id = cost_estimation_id
    qv.cost_total = ce.total_cost
    qv.binding_status = "valid"
    qv.binding_validated_at = datetime.now()
    qv.binding_warning = None

    # 重新计算毛利率
    if qv.total_price and qv.cost_total and qv.total_price > 0:
        from decimal import Decimal

        margin = (qv.total_price - qv.cost_total) / qv.total_price * Decimal("100")
        qv.gross_margin = margin.quantize(Decimal("0.01"))

    # 更新成本估算的绑定标记
    ce.is_bound_to_quote = True
    ce.bound_quote_version_id = qv.id

    db.commit()

    return {
        "message": "绑定成功",
        "quote_version_id": qv.id,
        "solution_version_id": solution_version_id,
        "cost_estimation_id": cost_estimation_id,
        "cost_total": float(qv.cost_total) if qv.cost_total else None,
        "gross_margin": float(qv.gross_margin) if qv.gross_margin else None,
    }
