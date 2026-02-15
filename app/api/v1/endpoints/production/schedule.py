# -*- coding: utf-8 -*-
"""
生产排程API
"""
import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.production import (
    ProductionSchedule,
    ResourceConflict,
    ScheduleAdjustmentLog,
    WorkOrder,
)
from app.models.user import User
from app.schemas.production_schedule import (
    AdjustmentLogResponse,
    ConflictCheckResponse,
    ConflictResponse,
    GanttDataResponse,
    GanttTask,
    ScheduleAdjustRequest,
    ScheduleComparisonRequest,
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
        
        # 开始计时
        start_time = datetime.now()
        
        # 生成排程
        plan_id, schedules, conflicts = service.generate_schedule(
            request,
            current_user.id
        )
        
        # 结束计时
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        # 获取工单信息
        work_orders = service._fetch_work_orders(request.work_orders)
        
        # 计算评估指标
        metrics = service.calculate_overall_metrics(schedules, work_orders)
        overall_score = metrics.calculate_overall_score()
        
        # 生成警告信息
        warnings = []
        if conflicts:
            warnings.append(f"检测到 {len(conflicts)} 个资源冲突")
        if metrics.completion_rate < 0.8:
            warnings.append(f"交期达成率较低: {metrics.completion_rate:.1%}")
        if elapsed_time > 5:
            warnings.append(f"排程耗时较长: {elapsed_time:.2f}秒")
        
        # 提交事务
        db.commit()
        
        # 转换响应
        schedule_responses = [ScheduleResponse.model_validate(s) for s in schedules]
        
        return ScheduleGenerateResponse(
            plan_id=plan_id,
            schedules=schedule_responses,
            total_count=len(request.work_orders),
            success_count=len(schedules),
            failed_count=len(request.work_orders) - len(schedules),
            conflicts_count=len(conflicts),
            score=overall_score,
            metrics={
                "completion_rate": metrics.completion_rate,
                "equipment_utilization": metrics.equipment_utilization,
                "worker_utilization": metrics.worker_utilization,
                "total_duration_hours": metrics.total_duration_hours,
                "skill_match_rate": metrics.skill_match_rate,
                "elapsed_time_seconds": elapsed_time
            },
            warnings=warnings
        )
    
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
        # 获取排程列表
        schedules = db.query(ProductionSchedule).filter(
            ProductionSchedule.schedule_plan_id == plan_id
        ).all()
        
        if not schedules:
            raise HTTPException(status_code=404, detail="排程方案不存在")
        
        # 获取冲突
        schedule_ids = [s.id for s in schedules]
        conflicts = db.query(ResourceConflict).filter(
            ResourceConflict.schedule_id.in_(schedule_ids),
            ResourceConflict.status == 'UNRESOLVED'
        ).all()
        
        # 统计信息
        service = ProductionScheduleService(db)
        work_order_ids = [s.work_order_id for s in schedules]
        work_orders = service._fetch_work_orders(work_order_ids)
        metrics = service.calculate_overall_metrics(schedules, work_orders)
        
        statistics = {
            "total_schedules": len(schedules),
            "pending": sum(1 for s in schedules if s.status == 'PENDING'),
            "confirmed": sum(1 for s in schedules if s.status == 'CONFIRMED'),
            "in_progress": sum(1 for s in schedules if s.status == 'IN_PROGRESS'),
            "completed": sum(1 for s in schedules if s.status == 'COMPLETED'),
            "total_duration_hours": metrics.total_duration_hours,
            "completion_rate": metrics.completion_rate,
            "equipment_utilization": metrics.equipment_utilization
        }
        
        # 优化建议
        optimization_suggestions = []
        if conflicts:
            optimization_suggestions.append("建议解决资源冲突后再确认排程")
        if metrics.completion_rate < 0.8:
            optimization_suggestions.append("部分工单可能延期，建议调整优先级或增加资源")
        if metrics.equipment_utilization < 0.6:
            optimization_suggestions.append("设备利用率较低，可以考虑安排更多工单")
        
        schedule_responses = [ScheduleResponse.model_validate(s) for s in schedules]
        conflict_responses = [ConflictResponse.model_validate(c) for c in conflicts]
        
        warnings = []
        if conflicts:
            warnings.append(f"存在 {len(conflicts)} 个未解决的冲突")
        
        return SchedulePreviewResponse(
            plan_id=plan_id,
            schedules=schedule_responses,
            statistics=statistics,
            conflicts=conflict_responses,
            warnings=warnings,
            is_optimizable=len(optimization_suggestions) > 0,
            optimization_suggestions=optimization_suggestions
        )
    
    except HTTPException:
        raise
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
        # 获取排程
        schedules = db.query(ProductionSchedule).filter(
            ProductionSchedule.schedule_plan_id == plan_id,
            ProductionSchedule.status == 'PENDING'
        ).all()
        
        if not schedules:
            raise HTTPException(status_code=404, detail="没有待确认的排程")
        
        # 检查是否有未解决的冲突
        schedule_ids = [s.id for s in schedules]
        unresolved_conflicts = db.query(ResourceConflict).filter(
            ResourceConflict.schedule_id.in_(schedule_ids),
            ResourceConflict.status == 'UNRESOLVED',
            ResourceConflict.severity.in_(['HIGH', 'CRITICAL'])
        ).count()
        
        if unresolved_conflicts > 0:
            raise HTTPException(
                status_code=400,
                detail=f"存在 {unresolved_conflicts} 个高优先级冲突，请先解决后再确认"
            )
        
        # 更新状态
        confirmed_at = datetime.now()
        for schedule in schedules:
            schedule.status = 'CONFIRMED'
            schedule.confirmed_by = current_user.id
            schedule.confirmed_at = confirmed_at
        
        db.commit()
        
        return {
            "success": True,
            "message": f"已确认 {len(schedules)} 个排程",
            "plan_id": plan_id,
            "confirmed_count": len(schedules),
            "confirmed_at": confirmed_at
        }
    
    except HTTPException:
        raise
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
        query = db.query(ResourceConflict)
        
        if plan_id:
            # 获取该方案的所有排程ID
            schedule_ids = db.query(ProductionSchedule.id).filter(
                ProductionSchedule.schedule_plan_id == plan_id
            ).all()
            schedule_ids = [sid[0] for sid in schedule_ids]
            query = query.filter(ResourceConflict.schedule_id.in_(schedule_ids))
        
        if schedule_id:
            query = query.filter(ResourceConflict.schedule_id == schedule_id)
        
        if status:
            query = query.filter(ResourceConflict.status == status)
        
        conflicts = query.all()
        
        # 按类型分组统计
        conflicts_by_type = {}
        for conflict in conflicts:
            conflict_type = conflict.conflict_type
            conflicts_by_type[conflict_type] = conflicts_by_type.get(conflict_type, 0) + 1
        
        # 按严重程度统计
        severity_summary = {}
        for conflict in conflicts:
            severity = conflict.severity
            severity_summary[severity] = severity_summary.get(severity, 0) + 1
        
        conflict_responses = [ConflictResponse.model_validate(c) for c in conflicts]
        
        return ConflictCheckResponse(
            has_conflicts=len(conflicts) > 0,
            total_conflicts=len(conflicts),
            conflicts_by_type=conflicts_by_type,
            conflicts=conflict_responses,
            severity_summary=severity_summary
        )
    
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
        # 获取排程
        schedule = db.query(ProductionSchedule).filter(
            ProductionSchedule.id == request.schedule_id
        ).first()
        
        if not schedule:
            raise HTTPException(status_code=404, detail="排程不存在")
        
        # 记录调整前的数据
        before_data = {
            "scheduled_start_time": schedule.scheduled_start_time.isoformat() if schedule.scheduled_start_time else None,
            "scheduled_end_time": schedule.scheduled_end_time.isoformat() if schedule.scheduled_end_time else None,
            "equipment_id": schedule.equipment_id,
            "worker_id": schedule.worker_id
        }
        
        # 应用调整
        changes = []
        if request.new_start_time:
            schedule.scheduled_start_time = request.new_start_time
            changes.append("开始时间")
        if request.new_end_time:
            schedule.scheduled_end_time = request.new_end_time
            changes.append("结束时间")
        if request.new_equipment_id is not None:
            schedule.equipment_id = request.new_equipment_id
            changes.append("设备")
        if request.new_worker_id is not None:
            schedule.worker_id = request.new_worker_id
            changes.append("工人")
        
        schedule.is_manually_adjusted = True
        schedule.adjustment_reason = request.reason
        schedule.adjusted_by = current_user.id
        schedule.adjusted_at = datetime.now()
        
        # 记录调整后的数据
        after_data = {
            "scheduled_start_time": schedule.scheduled_start_time.isoformat() if schedule.scheduled_start_time else None,
            "scheduled_end_time": schedule.scheduled_end_time.isoformat() if schedule.scheduled_end_time else None,
            "equipment_id": schedule.equipment_id,
            "worker_id": schedule.worker_id
        }
        
        # 创建调整日志
        adjustment_log = ScheduleAdjustmentLog(
            schedule_id=schedule.id,
            schedule_plan_id=schedule.schedule_plan_id,
            adjustment_type=request.adjustment_type,
            trigger_source='MANUAL',
            before_data=before_data,
            after_data=after_data,
            changes_summary=f"调整了: {', '.join(changes)}",
            reason=request.reason,
            adjusted_by=current_user.id,
            adjusted_at=datetime.now()
        )
        
        db.add(adjustment_log)
        
        # 如果需要自动解决冲突
        if request.auto_resolve_conflicts:
            service = ProductionScheduleService(db)
            conflicts = service._detect_conflicts([schedule])
            if conflicts:
                db.add_all(conflicts)
        
        db.commit()
        
        return {
            "success": True,
            "message": "排程调整成功",
            "schedule_id": schedule.id,
            "changes": changes,
            "adjustment_log_id": adjustment_log.id
        }
    
    except HTTPException:
        raise
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
        
        new_schedule, adjusted_schedules, conflicts = service.urgent_insert(
            work_order_id=request.work_order_id,
            insert_time=request.insert_time,
            max_delay_hours=request.max_delay_hours,
            auto_adjust=request.auto_adjust,
            user_id=current_user.id
        )
        
        # 保存
        db.add(new_schedule)
        if adjusted_schedules:
            db.add_all(adjusted_schedules)
        if conflicts:
            db.add_all(conflicts)
        
        # 创建调整日志
        for adj_schedule in adjusted_schedules:
            log = ScheduleAdjustmentLog(
                schedule_id=adj_schedule.id,
                adjustment_type='TIME_CHANGE',
                trigger_source='URGENT_ORDER',
                reason=f"紧急插单导致延后: 工单 {request.work_order_id}",
                adjusted_by=current_user.id,
                adjusted_at=datetime.now()
            )
            db.add(log)
        
        db.commit()
        
        schedule_response = ScheduleResponse.model_validate(new_schedule) if new_schedule else None
        adjusted_responses = [ScheduleResponse.model_validate(s) for s in adjusted_schedules]
        conflict_dicts = [{"type": c.conflict_type, "severity": c.severity} for c in conflicts]
        
        return UrgentInsertResponse(
            success=True,
            schedule=schedule_response,
            adjusted_schedules=adjusted_responses,
            conflicts=conflict_dicts,
            message=f"紧急插单成功，调整了 {len(adjusted_schedules)} 个排程"
        )
    
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
        # 解析方案ID
        plan_id_list = [int(pid.strip()) for pid in plan_ids.split(',')]
        
        if len(plan_id_list) < 2:
            raise HTTPException(status_code=400, detail="至少需要2个方案进行对比")
        if len(plan_id_list) > 5:
            raise HTTPException(status_code=400, detail="最多支持5个方案对比")
        
        service = ProductionScheduleService(db)
        results = []
        
        for plan_id in plan_id_list:
            schedules = db.query(ProductionSchedule).filter(
                ProductionSchedule.schedule_plan_id == plan_id
            ).all()
            
            if not schedules:
                continue
            
            # 获取工单
            work_order_ids = [s.work_order_id for s in schedules]
            work_orders = service._fetch_work_orders(work_order_ids)
            
            # 计算指标
            metrics = service.calculate_overall_metrics(schedules, work_orders)
            overall_score = metrics.calculate_overall_score()
            
            results.append({
                "plan_id": plan_id,
                "plan_name": f"方案 {plan_id}",
                "metrics": {
                    "overall_score": overall_score,
                    "completion_rate": metrics.completion_rate,
                    "equipment_utilization": metrics.equipment_utilization,
                    "worker_utilization": metrics.worker_utilization,
                    "total_duration_hours": metrics.total_duration_hours,
                    "conflict_count": metrics.conflict_count
                },
                "rank": 0,
                "recommendation": None
            })
        
        # 排序
        results.sort(key=lambda x: x["metrics"]["overall_score"], reverse=True)
        for i, result in enumerate(results):
            result["rank"] = i + 1
            if i == 0:
                result["recommendation"] = "推荐方案：综合评分最高"
        
        best_plan_id = results[0]["plan_id"] if results else 0
        
        return ScheduleComparisonResponse(
            comparison_time=datetime.now(),
            plans_compared=len(results),
            results=results,
            best_plan_id=best_plan_id,
            comparison_summary={
                "total_plans": len(results),
                "best_plan": best_plan_id,
                "score_range": {
                    "min": min(r["metrics"]["overall_score"] for r in results) if results else 0,
                    "max": max(r["metrics"]["overall_score"] for r in results) if results else 0
                }
            }
        )
    
    except HTTPException:
        raise
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
        schedules = db.query(ProductionSchedule).filter(
            ProductionSchedule.schedule_plan_id == plan_id
        ).all()
        
        if not schedules:
            raise HTTPException(status_code=404, detail="排程方案不存在")
        
        # 获取关联的工单
        work_order_ids = [s.work_order_id for s in schedules]
        work_orders_dict = {
            wo.id: wo for wo in db.query(WorkOrder).filter(
                WorkOrder.id.in_(work_order_ids)
            ).all()
        }
        
        # 构建甘特图任务
        tasks = []
        for schedule in schedules:
            work_order = work_orders_dict.get(schedule.work_order_id)
            if not work_order:
                continue
            
            # 确定颜色
            color_map = {
                'PENDING': '#9E9E9E',
                'CONFIRMED': '#2196F3',
                'IN_PROGRESS': '#FF9800',
                'COMPLETED': '#4CAF50',
                'CANCELLED': '#F44336'
            }
            
            task = GanttTask(
                id=schedule.id,
                name=work_order.task_name,
                work_order_no=work_order.work_order_no,
                start=schedule.scheduled_start_time,
                end=schedule.scheduled_end_time,
                duration=schedule.duration_hours,
                progress=work_order.progress / 100 if work_order.progress else 0,
                resource=f"设备{schedule.equipment_id}" if schedule.equipment_id else None,
                equipment=f"设备{schedule.equipment_id}" if schedule.equipment_id else None,
                worker=f"工人{schedule.worker_id}" if schedule.worker_id else None,
                status=schedule.status,
                priority=work_order.priority,
                dependencies=[],
                color=color_map.get(schedule.status, '#9E9E9E')
            )
            tasks.append(task)
        
        # 计算时间范围
        start_date = min(s.scheduled_start_time for s in schedules)
        end_date = max(s.scheduled_end_time for s in schedules)
        
        # 资源列表
        equipment_ids = set(s.equipment_id for s in schedules if s.equipment_id)
        worker_ids = set(s.worker_id for s in schedules if s.worker_id)
        
        resources = []
        for eq_id in equipment_ids:
            resources.append({"type": "equipment", "id": eq_id, "name": f"设备{eq_id}"})
        for w_id in worker_ids:
            resources.append({"type": "worker", "id": w_id, "name": f"工人{w_id}"})
        
        return GanttDataResponse(
            tasks=tasks,
            total_tasks=len(tasks),
            start_date=start_date,
            end_date=end_date,
            resources=resources,
            milestones=[]
        )
    
    except HTTPException:
        raise
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
        # 删除排程
        deleted_count = db.query(ProductionSchedule).filter(
            ProductionSchedule.schedule_plan_id == plan_id
        ).delete()
        
        # 删除相关冲突记录
        db.query(ResourceConflict).filter(
            ResourceConflict.schedule_id.in_(
                db.query(ProductionSchedule.id).filter(
                    ProductionSchedule.schedule_plan_id == plan_id
                )
            )
        ).delete(synchronize_session=False)
        
        # 删除调整日志
        db.query(ScheduleAdjustmentLog).filter(
            ScheduleAdjustmentLog.schedule_plan_id == plan_id
        ).delete()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"已重置方案 {plan_id}",
            "deleted_count": deleted_count
        }
    
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
        # 查询调整日志
        query = db.query(ScheduleAdjustmentLog)
        
        if schedule_id:
            query = query.filter(ScheduleAdjustmentLog.schedule_id == schedule_id)
        
        if plan_id:
            query = query.filter(ScheduleAdjustmentLog.schedule_plan_id == plan_id)
        
        total_count = query.count()
        
        adjustments = query.order_by(
            ScheduleAdjustmentLog.adjusted_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        # 获取关联的排程
        schedule_ids = list(set(a.schedule_id for a in adjustments))
        schedules = db.query(ProductionSchedule).filter(
            ProductionSchedule.id.in_(schedule_ids)
        ).all()
        
        adjustment_responses = [AdjustmentLogResponse.model_validate(a) for a in adjustments]
        schedule_responses = [ScheduleResponse.model_validate(s) for s in schedules]
        
        return ScheduleHistoryResponse(
            schedules=schedule_responses,
            adjustments=adjustment_responses,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        logger.error(f"获取排程历史失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取排程历史失败: {str(e)}")
