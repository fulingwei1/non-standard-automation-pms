# -*- coding: utf-8 -*-
"""
物料管理优化 API 端点
P1: 齐套率定时/手动同步
P2: 缺料影响交付日期预测
P3: 项目优先级与齐套率联动
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.schemas import success_response
from app.models.user import User
from app.schemas.kitting_optimization import KittingRateSyncRequest
from app.services.kitting_optimization_service import KittingOptimizationService

logger = logging.getLogger(__name__)
router = APIRouter()


# ==================== P1: 齐套率同步 ====================


@router.post("/material/sync-kitting-rate-scheduler", summary="齐套率定时同步（调度器调用）")
def sync_kitting_rate_scheduler(
    threshold: float = Query(5.0, description="显著变化阈值(%)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    定时同步所有活跃项目的齐套率（每小时执行）。

    功能:
    - 自动计算所有活跃项目的齐套率
    - 识别齐套率变化超过阈值的项目
    - 自动更新项目健康度（齐套率<50%→红灯, <70%→黄灯）
    - 更新项目的物料状态和缺料项数量
    """
    try:
        svc = KittingOptimizationService(db)
        result = svc.sync_all_projects_kitting_rate(threshold=threshold)
        return success_response(
            data=result,
            message=f"已同步{result['total_synced']}个项目齐套率，"
                    f"{result['significant_count']}个项目发生显著变化",
        )
    except Exception as e:
        logger.exception("齐套率定时同步失败")
        raise HTTPException(status_code=500, detail=f"齐套率同步失败: {str(e)}")


@router.post("/material/sync-kitting-rate", summary="齐套率手动触发同步")
def sync_kitting_rate(
    request: KittingRateSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    手动触发单个或多个项目的齐套率同步。

    功能:
    - 指定项目ID列表，批量同步齐套率
    - 实时返回每个项目的同步结果
    - 包含旧齐套率、新齐套率、变化量
    """
    try:
        svc = KittingOptimizationService(db)
        results = []
        errors = []
        for pid in request.project_ids:
            try:
                result = svc.sync_project_kitting_rate(pid)
                results.append(result)
            except Exception as e:
                errors.append({"project_id": pid, "error": str(e)})

        db.commit()

        return success_response(
            data={
                "results": results,
                "total": len(results),
                "errors": errors,
                "error_count": len(errors),
            },
            message=f"已同步{len(results)}个项目齐套率",
        )
    except Exception as e:
        logger.exception("手动同步齐套率失败")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")


# ==================== P2: 缺料影响交付预测 ====================


@router.get("/projects/{project_id}/material-delay-forecast", summary="缺料影响交付预测")
def get_material_delay_forecast(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    基于缺料和供应商交期预测项目延期。

    功能:
    - 分析项目BOM中所有缺料物料
    - 结合在途采购订单和供应商交期
    - 识别关键路径物料
    - 计算预计延期天数
    - 给出缓解建议（加急/替代料/调整计划）
    """
    try:
        svc = KittingOptimizationService(db)
        result = svc.forecast_material_delay(project_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return success_response(data=result, message="交付预测生成成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("交付预测失败")
        raise HTTPException(status_code=500, detail=f"交付预测失败: {str(e)}")


# ==================== P3: 项目优先级自动调整 ====================


@router.post("/projects/priority-auto-adjust", summary="项目优先级自动调整")
def auto_adjust_priority(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    根据齐套率自动调整项目优先级。

    规则:
    - 齐套率 < 70% → 自动降低优先级（HIGH→NORMAL, NORMAL→LOW）
    - 齐套率 > 95% → 自动提高优先级（LOW→NORMAL, NORMAL→HIGH）
    - 保护机制：战略客户（合同金额≥100万）和 URGENT 级别不降级
    - 记录所有优先级调整历史
    """
    try:
        svc = KittingOptimizationService(db)
        result = svc.auto_adjust_project_priority()
        return success_response(
            data=result,
            message=f"已调整{result['total_adjusted']}个项目优先级，"
                    f"{result['protected_count']}个受保护项目未调整",
        )
    except Exception as e:
        logger.exception("优先级自动调整失败")
        raise HTTPException(status_code=500, detail=f"优先级调整失败: {str(e)}")
