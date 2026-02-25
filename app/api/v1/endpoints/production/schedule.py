# -*- coding: utf-8 -*-
"""
生产排程API
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.production_schedule import (
    ConflictCheckResponse,
    GanttDataResponse,
    ScheduleAdjustRequest,
    ScheduleComparisonResponse,
    ScheduleGenerateRequest,
    ScheduleGenerateResponse,
    ScheduleHistoryResponse,
    SchedulePreviewResponse,
    ScheduleResponse,
    UrgentInsertRequest,
    UrgentInsertResponse,
)
from app.services.production_schedule_service import ProductionScheduleService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate", response_model=ScheduleGenerateResponse)
async def generate_schedule(
    request: ScheduleGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成智能排程

    支持的算法:
    - GREEDY: 贪心算法，快速生成
    - HEURISTIC: 启发式算法，效果更优
    - GENETIC: 遗传算法(未实现)

    优化目标:
    - TIME: 最短完成时间
    - RESOURCE: 最高资源利用率
    - BALANCED: 平衡模式(推荐)
    """
    try:
        service = ProductionScheduleService(db)
        result = service.generate_and_evaluate_schedule(request, current_user.id)
        return ScheduleGenerateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"生成排程失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"生成排程失败: {str(e)}")


@router.get("/preview", response_model=SchedulePreviewResponse)
async def preview_schedule(
    plan_id: int = Query(..., description="排程方案ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """排程预览"""
    try:
        service = ProductionScheduleService(db)
        result = service.get_schedule_preview(plan_id)
        return SchedulePreviewResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"排程预览失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"排程预览失败: {str(e)}")


@router.post("/confirm")
async def confirm_schedule(
    plan_id: int = Query(..., description="排程方案ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """确认排程"""
    try:
        service = ProductionScheduleService(db)
        return service.confirm_schedule(plan_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"确认排程失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"确认排程失败: {str(e)}")


@router.get("/conflicts", response_model=ConflictCheckResponse)
async def check_conflicts(
    plan_id: int = Query(None, description="排程方案ID"),
    schedule_id: int = Query(None, description="排程ID"),
    status: str = Query(None, description="冲突状态"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """资源冲突检测"""
    try:
        service = ProductionScheduleService(db)
        result = service.get_conflict_summary(plan_id, schedule_id, status)
        return ConflictCheckResponse(**result)
    except Exception as e:
        logger.error(f"冲突检测失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"冲突检测失败: {str(e)}")


@router.post("/adjust")
async def adjust_schedule(
    request: ScheduleAdjustRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手动调整排程"""
    try:
        service = ProductionScheduleService(db)
        return service.adjust_schedule(request, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"调整排程失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"调整排程失败: {str(e)}")


@router.post("/urgent-insert", response_model=UrgentInsertResponse)
async def urgent_insert(
    request: UrgentInsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """紧急插单"""
    try:
        service = ProductionScheduleService(db)
        result = service.execute_urgent_insert_with_logging(
            work_order_id=request.work_order_id,
            insert_time=request.insert_time,
            max_delay_hours=request.max_delay_hours,
            auto_adjust=request.auto_adjust,
            user_id=current_user.id
        )
        return UrgentInsertResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"紧急插单失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"紧急插单失败: {str(e)}")


@router.get("/comparison", response_model=ScheduleComparisonResponse)
async def compare_schedules(
    plan_ids: str = Query(..., description="方案ID列表，逗号分隔"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """排程方案对比"""
    try:
        plan_id_list = [int(pid.strip()) for pid in plan_ids.split(',')]
        service = ProductionScheduleService(db)
        result = service.compare_schedule_plans(plan_id_list)
        return ScheduleComparisonResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"方案对比失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"方案对比失败: {str(e)}")


@router.get("/gantt", response_model=GanttDataResponse)
async def get_gantt_data(
    plan_id: int = Query(..., description="排程方案ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取甘特图数据"""
    try:
        service = ProductionScheduleService(db)
        result = service.generate_gantt_data(plan_id)
        return GanttDataResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取甘特图数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取甘特图数据失败: {str(e)}")


@router.delete("/reset")
async def reset_schedule(
    plan_id: int = Query(..., description="排程方案ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重置排程"""
    try:
        service = ProductionScheduleService(db)
        return service.reset_schedule_plan(plan_id)
    except Exception as e:
        logger.error(f"重置排程失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"重置排程失败: {str(e)}")


@router.get("/history", response_model=ScheduleHistoryResponse)
async def get_schedule_history(
    schedule_id: int = Query(None, description="排程ID"),
    plan_id: int = Query(None, description="方案ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """排程历史"""
    try:
        service = ProductionScheduleService(db)
        result = service.get_schedule_history(schedule_id, plan_id, page, page_size)

        # 序列化ORM对象
        from app.schemas.production_schedule import AdjustmentLogResponse
        return ScheduleHistoryResponse(
            schedules=[ScheduleResponse.model_validate(s) for s in result["schedules"]],
            adjustments=[AdjustmentLogResponse.model_validate(a) for a in result["adjustments"]],
            total_count=result["total_count"],
            page=result["page"],
            page_size=result["page_size"],
        )
    except Exception as e:
        logger.error(f"获取排程历史失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取排程历史失败: {str(e)}")
