# -*- coding: utf-8 -*-
"""
ECN物料影响跟踪端点

包含：
- POST /ecns/{ecn_id}/material-impact-analysis  物料影响分析
- GET  /ecns/{ecn_id}/execution-progress         执行进度跟踪
- GET  /ecns/{ecn_id}/stakeholders               相关人员可见性
- POST /ecns/{ecn_id}/notify-stakeholders         变更主动通知
- PUT  /ecns/{ecn_id}/material/{material_id}/disposition  物料处置
- PUT  /ecns/{ecn_id}/stakeholders/subscription   订阅管理
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.ecn_material_impact import (
    MaterialDispositionRequest,
    MaterialDispositionResponse,
    MaterialImpactAnalysisResponse,
    ExecutionProgressResponse,
    NotifyResultResponse,
    NotifyStakeholdersRequest,
    StakeholderListResponse,
    SubscriptionUpdateRequest,
)
from app.services.ecn_material_impact_service import EcnMaterialImpactService

router = APIRouter()


@router.post(
    "/ecns/{ecn_id}/material-impact-analysis",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def analyze_material_impact(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    ECN物料影响分析

    - 分析ECN变更影响的物料清单
    - 识别受影响物料的当前状态（未采购/已下单/在途/已入库）
    - 计算潜在损失金额
    - 识别影响的采购订单
    - 评估对项目交付的影响
    """
    try:
        service = EcnMaterialImpactService(db)
        result = service.analyze_material_impact(ecn_id, current_user.id)
        return ResponseModel(code=200, message="物料影响分析完成", data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"物料影响分析失败: {str(e)}",
        )


@router.get(
    "/ecns/{ecn_id}/execution-progress",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_execution_progress(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    ECN执行进度跟踪

    - ECN执行各阶段进度（通知供应商/采购变更/物料处理）
    - 每个受影响物料的处理状态
    - 预计完成日期
    - 阻塞问题跟踪
    """
    try:
        service = EcnMaterialImpactService(db)
        result = service.get_execution_progress(ecn_id)
        return ResponseModel(code=200, message="success", data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取执行进度失败: {str(e)}",
        )


@router.get(
    "/ecns/{ecn_id}/stakeholders",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_stakeholders(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    ECN相关人员可见性

    - 自动识别相关人员（项目经理/采购员/供应商/设计人员）
    - 根据影响范围自动添加相关人员
    - 相关人员可查看ECN详情和执行进度
    """
    try:
        service = EcnMaterialImpactService(db)
        result = service.get_stakeholders(ecn_id)
        return ResponseModel(code=200, message="success", data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取相关人员失败: {str(e)}",
        )


@router.post(
    "/ecns/{ecn_id}/notify-stakeholders",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def notify_stakeholders(
    ecn_id: int,
    request: NotifyStakeholdersRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    变更主动通知

    - ECN发布时自动通知相关人员
    - 物料处理状态变化时通知
    - 执行进度关键节点通知
    """
    try:
        service = EcnMaterialImpactService(db)
        result = service.notify_stakeholders(
            ecn_id=ecn_id,
            notification_type=request.notification_type,
            message=request.message,
            target_roles=request.target_roles,
            priority=request.priority,
            current_user_id=current_user.id,
        )
        return ResponseModel(code=200, message="通知发送完成", data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"通知发送失败: {str(e)}",
        )


@router.put(
    "/ecns/{ecn_id}/material/{material_id}/disposition",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def update_material_disposition(
    ecn_id: int,
    material_id: int,
    request: MaterialDispositionRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    ECN物料处置工作流

    - 物料处理决策（继续使用/返工/报废/退货）
    - 记录处理原因和成本
    - 更新执行进度
    - 触发通知
    """
    try:
        service = EcnMaterialImpactService(db)
        result = service.update_material_disposition(
            ecn_id=ecn_id,
            material_id=material_id,
            disposition=request.disposition,
            disposition_reason=request.disposition_reason,
            disposition_cost=request.disposition_cost,
            remark=request.remark,
            current_user_id=current_user.id,
        )
        return ResponseModel(code=200, message="物料处置更新成功", data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"物料处置更新失败: {str(e)}",
        )


@router.put(
    "/ecns/{ecn_id}/stakeholders/subscription",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def update_subscription(
    ecn_id: int,
    request: SubscriptionUpdateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新ECN通知订阅

    - 支持订阅/取消订阅
    - 可选择订阅的通知类型
    """
    try:
        service = EcnMaterialImpactService(db)
        result = service.update_subscription(
            ecn_id=ecn_id,
            user_id=current_user.id,
            is_subscribed=request.is_subscribed,
            subscription_types=request.subscription_types,
        )
        return ResponseModel(code=200, message="订阅更新成功", data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"订阅更新失败: {str(e)}",
        )
