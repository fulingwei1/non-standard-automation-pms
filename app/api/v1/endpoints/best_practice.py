# -*- coding: utf-8 -*-
"""
行业最佳实践 P0 级优化 API 端点

端点：
- POST /api/v1/material/abc-classification     ABC 物料自动分级
- POST /api/v1/suppliers/auto-reclassify        供应商动态升降级
- POST /api/v1/material/shortage-escalation     缺料自动升级通知
- PUT  /api/v1/projects/{id}/kitting-targets    齐套率阶段目标配置
"""

from typing import Any

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.api import deps
from app.core.schemas.response import SuccessResponse, success_response
from app.schemas.best_practice import (
    ABCClassificationRequest,
    ABCClassificationResponse,
    KittingTargetsRequest,
    KittingTargetsResponse,
    ShortageEscalationRequest,
    ShortageEscalationResponse,
    SupplierReclassifyRequest,
    SupplierReclassifyResponse,
)
from app.services.best_practice_service import BestPracticeService

# 三个不同 prefix 的路由器，在 api.py 中分别挂载
material_router = APIRouter()
supplier_router = APIRouter()
project_router = APIRouter()


# ------------------------------------------------------------------
# 1. ABC 物料自动分级
# ------------------------------------------------------------------
@material_router.post(
    "/abc-classification",
    response_model=SuccessResponse[ABCClassificationResponse],
    summary="ABC 物料自动分级",
    description=(
        "按年消耗金额自动分级（A>100万/B>10万/C<10万），"
        "同时考虑采购周期（>60天自动A类）和供应商数量（单一来源自动A类）。"
        "输出分级结果和建议管理策略。"
    ),
)
def abc_classification(
    request: ABCClassificationRequest = None,
    db: Session = Depends(deps.get_db),
) -> Any:
    if request is None:
        request = ABCClassificationRequest()
    service = BestPracticeService(db)
    result = service.abc_classification(
        config=request.config,
        material_ids=request.material_ids,
    )
    return success_response(
        data=result,
        message=f"ABC 分级完成，共 {result.total} 个物料",
    )


# ------------------------------------------------------------------
# 2. 供应商动态升降级
# ------------------------------------------------------------------
@supplier_router.post(
    "/auto-reclassify",
    response_model=SuccessResponse[SupplierReclassifyResponse],
    summary="供应商动态升降级",
    description=(
        "基于季度绩效自动升降级。"
        "连续2季度≥90分→升级；连续2季度<60分→降级；"
        "重大质量问题→直接淘汰。"
    ),
)
def supplier_auto_reclassify(
    request: SupplierReclassifyRequest = None,
    db: Session = Depends(deps.get_db),
) -> Any:
    if request is None:
        request = SupplierReclassifyRequest()
    service = BestPracticeService(db)
    result = service.supplier_reclassify(
        config=request.config,
        supplier_ids=request.supplier_ids,
        quarter_scores=request.quarter_scores,
    )
    return success_response(
        data=result,
        message=(
            f"供应商评估完成：升级 {result.upgraded}、"
            f"降级 {result.downgraded}、淘汰 {result.eliminated}、"
            f"维持 {result.unchanged}"
        ),
    )


# ------------------------------------------------------------------
# 3. 缺料自动升级通知
# ------------------------------------------------------------------
@material_router.post(
    "/shortage-escalation",
    response_model=SuccessResponse[ShortageEscalationResponse],
    summary="缺料自动升级通知",
    description=(
        "检查所有 OPEN 状态缺料记录，按延期天数自动分级通知。"
        "1-3天→采购员；4-7天→采购经理；>7天→总经理+项目经理。"
        "记录升级历史。"
    ),
)
def shortage_escalation(
    request: ShortageEscalationRequest = None,
    db: Session = Depends(deps.get_db),
) -> Any:
    if request is None:
        request = ShortageEscalationRequest()
    service = BestPracticeService(db)
    result = service.shortage_escalation(
        config=request.config,
        project_id=request.project_id,
    )
    return success_response(
        data=result,
        message=f"缺料升级检查完成，{result.escalated_count} 条需要升级通知",
    )


# ------------------------------------------------------------------
# 4. 齐套率阶段目标配置
# ------------------------------------------------------------------
@project_router.put(
    "/{project_id}/kitting-targets",
    response_model=SuccessResponse[KittingTargetsResponse],
    summary="齐套率阶段目标配置",
    description=(
        "配置各阶段齐套率目标（S3/S4/S5/S6），"
        "实际齐套率 vs 目标对比，未达标自动预警。"
    ),
)
def set_kitting_targets(
    request: KittingTargetsRequest,
    project_id: int = Path(..., description="项目 ID"),
    db: Session = Depends(deps.get_db),
) -> Any:
    service = BestPracticeService(db)
    try:
        result = service.set_kitting_targets(
            project_id=project_id,
            request=request,
        )
    except ValueError as e:
        from app.core.schemas.response import error_response

        return error_response(message=str(e), code=404)

    alert_count = sum(1 for s in result.stages if s.alert)
    msg = "齐套率目标配置成功"
    if alert_count:
        msg += f"，{alert_count} 个阶段未达标"
    return success_response(data=result, message=msg)
