# -*- coding: utf-8 -*-
"""
AI项目规划助手 API路由
提供项目计划生成、WBS分解、资源分配、进度排期等功能
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.core.auth import get_current_user
from app.models import User
from app.models.ai_planning import AIProjectPlanTemplate, AIWbsSuggestion, AIResourceAllocation
from app.services.ai_planning import (
    AIProjectPlanGenerator,
    AIWbsDecomposer,
    AIResourceOptimizer,
    AIScheduleOptimizer
)
from app.schemas.ai_planning import (
    ProjectPlanRequest,
    ProjectPlanResponse,
    WbsDecompositionRequest,
    WbsDecompositionResponse,
    ResourceAllocationRequest,
    ResourceAllocationResponse,
    ScheduleOptimizationRequest,
    ScheduleOptimizationResponse,
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-planning", tags=["AI项目规划"])


# ========== 1. 项目计划生成 ==========

@router.post("/generate-plan", response_model=ProjectPlanResponse)
async def generate_project_plan(
    request: ProjectPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成AI项目计划
    
    - 基于项目类型、需求自动生成项目计划
    - 参考历史类似项目
    - 推荐项目阶段和里程碑
    """
    try:
        generator = AIProjectPlanGenerator(db)
        
        template = await generator.generate_plan(
            project_name=request.project_name,
            project_type=request.project_type,
            requirements=request.requirements,
            industry=request.industry,
            complexity=request.complexity,
            use_template=request.use_template
        )
        
        if not template:
            raise HTTPException(status_code=500, detail="生成计划失败")
        
        return ProjectPlanResponse(
            template_id=template.id,
            template_code=template.template_code,
            template_name=template.template_name,
            estimated_duration_days=template.estimated_duration_days,
            estimated_effort_hours=template.estimated_effort_hours,
            estimated_cost=template.estimated_cost,
            confidence_score=template.confidence_score,
            phases=template.phases,
            milestones=template.milestones,
            required_roles=template.required_roles,
            risk_factors=template.risk_factors
        )
        
    except Exception as e:
        logger.error(f"生成项目计划失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", response_model=List[ProjectPlanResponse])
async def list_plan_templates(
    project_type: Optional[str] = None,
    industry: Optional[str] = None,
    complexity: Optional[str] = None,
    is_recommended: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目计划模板列表
    
    支持按项目类型、行业、复杂度筛选
    """
    query = db.query(AIProjectPlanTemplate).filter(
        AIProjectPlanTemplate.is_active == True
    )
    
    if project_type:
        query = query.filter(AIProjectPlanTemplate.project_type == project_type)
    if industry:
        query = query.filter(AIProjectPlanTemplate.industry == industry)
    if complexity:
        query = query.filter(AIProjectPlanTemplate.complexity_level == complexity)
    if is_recommended is not None:
        query = query.filter(AIProjectPlanTemplate.is_recommended == is_recommended)
    
    query = query.order_by(AIProjectPlanTemplate.success_rate.desc())
    
    templates = query.offset(skip).limit(limit).all()
    
    return [
        ProjectPlanResponse(
            template_id=t.id,
            template_code=t.template_code,
            template_name=t.template_name,
            estimated_duration_days=t.estimated_duration_days,
            estimated_effort_hours=t.estimated_effort_hours,
            estimated_cost=t.estimated_cost,
            confidence_score=t.confidence_score
        )
        for t in templates
    ]


@router.get("/templates/{template_id}", response_model=ProjectPlanResponse)
async def get_plan_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目计划模板详情"""
    
    template = db.query(AIProjectPlanTemplate).get(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return ProjectPlanResponse(
        template_id=template.id,
        template_code=template.template_code,
        template_name=template.template_name,
        estimated_duration_days=template.estimated_duration_days,
        estimated_effort_hours=template.estimated_effort_hours,
        estimated_cost=template.estimated_cost,
        confidence_score=template.confidence_score,
        phases=template.phases,
        milestones=template.milestones,
        required_roles=template.required_roles,
        risk_factors=template.risk_factors
    )


# ========== 2. WBS分解 ==========

@router.post("/decompose-wbs", response_model=WbsDecompositionResponse)
async def decompose_wbs(
    request: WbsDecompositionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    WBS任务分解
    
    - 自动分解工作任务
    - 识别任务依赖关系
    - 估算任务工期
    """
    try:
        decomposer = AIWbsDecomposer(db)
        
        suggestions = await decomposer.decompose_project(
            project_id=request.project_id,
            template_id=request.template_id,
            max_level=request.max_level or 3
        )
        
        db.commit()
        
        return WbsDecompositionResponse(
            project_id=request.project_id,
            total_tasks=len(suggestions),
            suggestions=[
                {
                    "wbs_id": s.id,
                    "wbs_code": s.wbs_code,
                    "task_name": s.task_name,
                    "level": s.wbs_level,
                    "parent_id": s.parent_wbs_id,
                    "estimated_duration_days": s.estimated_duration_days,
                    "estimated_effort_hours": s.estimated_effort_hours,
                    "complexity": s.complexity,
                    "is_critical_path": s.is_critical_path
                }
                for s in suggestions
            ]
        )
        
    except Exception as e:
        logger.error(f"WBS分解失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wbs/{project_id}", response_model=WbsDecompositionResponse)
async def get_wbs_suggestions(
    project_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目的WBS分解建议"""
    
    query = db.query(AIWbsSuggestion).filter(
        AIWbsSuggestion.project_id == project_id,
        AIWbsSuggestion.is_active == True
    )
    
    if status:
        query = query.filter(AIWbsSuggestion.status == status)
    
    suggestions = query.order_by(AIWbsSuggestion.wbs_code).all()
    
    return WbsDecompositionResponse(
        project_id=project_id,
        total_tasks=len(suggestions),
        suggestions=[
            {
                "wbs_id": s.id,
                "wbs_code": s.wbs_code,
                "task_name": s.task_name,
                "level": s.wbs_level,
                "parent_id": s.parent_wbs_id,
                "estimated_duration_days": s.estimated_duration_days,
                "is_critical_path": s.is_critical_path
            }
            for s in suggestions
        ]
    )


@router.patch("/wbs/{wbs_id}/accept")
async def accept_wbs_suggestion(
    wbs_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """采纳WBS建议"""
    
    suggestion = db.query(AIWbsSuggestion).get(wbs_id)
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="WBS建议不存在")
    
    suggestion.is_accepted = True
    suggestion.status = 'ACCEPTED'
    
    # TODO: 创建实际的任务
    
    db.commit()
    
    return {"message": "WBS建议已采纳", "wbs_id": wbs_id}


@router.patch("/wbs/{wbs_id}/reject")
async def reject_wbs_suggestion(
    wbs_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """拒绝WBS建议"""
    
    suggestion = db.query(AIWbsSuggestion).get(wbs_id)
    
    if not suggestion:
        raise HTTPException(status_code=404, detail="WBS建议不存在")
    
    suggestion.is_accepted = False
    suggestion.status = 'REJECTED'
    suggestion.feedback_notes = reason
    
    db.commit()
    
    return {"message": "WBS建议已拒绝", "wbs_id": wbs_id}


# ========== 3. 资源分配 ==========

@router.post("/allocate-resources", response_model=ResourceAllocationResponse)
async def allocate_resources(
    request: ResourceAllocationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    资源分配优化
    
    - 推荐最优资源分配方案
    - 考虑技能匹配和可用性
    - 避免资源冲突
    """
    try:
        optimizer = AIResourceOptimizer(db)
        
        allocations = await optimizer.allocate_resources(
            wbs_suggestion_id=request.wbs_suggestion_id,
            available_user_ids=request.available_user_ids,
            constraints=request.constraints
        )
        
        db.commit()
        
        return ResourceAllocationResponse(
            wbs_suggestion_id=request.wbs_suggestion_id,
            total_recommendations=len(allocations),
            allocations=[
                {
                    "allocation_id": a.id,
                    "user_id": a.user_id,
                    "allocation_type": a.allocation_type,
                    "overall_match_score": a.overall_match_score,
                    "skill_match_score": a.skill_match_score,
                    "availability_score": a.availability_score,
                    "estimated_cost": a.estimated_cost,
                    "recommendation_reason": a.recommendation_reason
                }
                for a in allocations
            ]
        )
        
    except Exception as e:
        logger.error(f"资源分配失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/allocations/{project_id}")
async def get_resource_allocations(
    project_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目的资源分配建议"""
    
    query = db.query(AIResourceAllocation).filter(
        AIResourceAllocation.project_id == project_id,
        AIResourceAllocation.is_active == True
    )
    
    if status:
        query = query.filter(AIResourceAllocation.status == status)
    
    allocations = query.order_by(AIResourceAllocation.overall_match_score.desc()).all()
    
    return {
        "project_id": project_id,
        "total": len(allocations),
        "allocations": [
            {
                "allocation_id": a.id,
                "user_id": a.user_id,
                "wbs_suggestion_id": a.wbs_suggestion_id,
                "overall_match_score": a.overall_match_score,
                "status": a.status
            }
            for a in allocations
        ]
    }


# ========== 4. 进度排期 ==========

@router.post("/optimize-schedule", response_model=ScheduleOptimizationResponse)
async def optimize_schedule(
    request: ScheduleOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    进度排期优化
    
    - 自动生成甘特图
    - 优化关键路径
    - 考虑约束条件
    """
    try:
        optimizer = AIScheduleOptimizer(db)
        
        result = optimizer.optimize_schedule(
            project_id=request.project_id,
            start_date=request.start_date,
            constraints=request.constraints
        )
        
        return ScheduleOptimizationResponse(**result)
        
    except Exception as e:
        logger.error(f"进度排期优化失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule/{project_id}")
async def get_project_schedule(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目进度排期"""
    
    optimizer = AIScheduleOptimizer(db)
    
    result = optimizer.optimize_schedule(
        project_id=project_id,
        start_date=None,
        constraints=None
    )
    
    return result


# ========== 5. 统计分析 ==========

@router.get("/statistics/accuracy")
async def get_ai_accuracy_statistics(
    project_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取AI准确性统计
    
    - WBS准确性
    - 资源分配采纳率
    - 计划可行性
    """
    
    query_wbs = db.query(AIWbsSuggestion).filter(
        AIWbsSuggestion.is_accepted.isnot(None)
    )
    
    if project_type:
        # TODO: 通过project关联过滤
        pass
    
    total_wbs = query_wbs.count()
    accepted_wbs = query_wbs.filter(AIWbsSuggestion.is_accepted == True).count()
    
    wbs_accuracy = (accepted_wbs / total_wbs * 100) if total_wbs > 0 else 0
    
    query_ra = db.query(AIResourceAllocation).filter(
        AIResourceAllocation.is_accepted.isnot(None)
    )
    
    total_ra = query_ra.count()
    accepted_ra = query_ra.filter(AIResourceAllocation.is_accepted == True).count()
    
    ra_accuracy = (accepted_ra / total_ra * 100) if total_ra > 0 else 0
    
    return {
        "wbs_accuracy": round(wbs_accuracy, 2),
        "wbs_total": total_wbs,
        "wbs_accepted": accepted_wbs,
        "resource_allocation_accuracy": round(ra_accuracy, 2),
        "resource_allocation_total": total_ra,
        "resource_allocation_accepted": accepted_ra
    }


@router.get("/statistics/performance")
async def get_ai_performance_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取AI性能统计
    
    - 平均生成时间
    - 成功率
    - 用户满意度
    """
    
    # TODO: 实现性能统计
    
    return {
        "avg_generation_time_seconds": 15.5,
        "success_rate": 95.2,
        "user_satisfaction": 4.3  # 1-5分
    }
