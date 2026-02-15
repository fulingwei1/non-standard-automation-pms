# -*- coding: utf-8 -*-
"""
资源冲突智能调度系统 - API端点
"""

import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.api import deps
from app.models.resource_scheduling import (
    ResourceConflictDetection,
    ResourceDemandForecast,
    ResourceSchedulingLog,
    ResourceSchedulingSuggestion,
    ResourceUtilizationAnalysis,
)
from app.models.user import User
from app.schemas.resource_scheduling import (
    AISchedulingSuggestionRequest,
    AISchedulingSuggestionResponse,
    ConflictDetectionRequest,
    ConflictDetectionResponse,
    DashboardSummary,
    ForecastRequest,
    ForecastResponse,
    ResourceConflictDetectionCreate,
    ResourceConflictDetectionInDB,
    ResourceConflictDetectionUpdate,
    ResourceDemandForecastCreate,
    ResourceDemandForecastInDB,
    ResourceDemandForecastUpdate,
    ResourceSchedulingLogCreate,
    ResourceSchedulingLogInDB,
    ResourceSchedulingSuggestionCreate,
    ResourceSchedulingSuggestionInDB,
    ResourceSchedulingSuggestionUpdate,
    ResourceUtilizationAnalysisCreate,
    ResourceUtilizationAnalysisInDB,
    ResourceUtilizationAnalysisUpdate,
    UtilizationAnalysisRequest,
    UtilizationAnalysisResponse,
)
from app.services.resource_scheduling_ai_service import ResourceSchedulingAIService


router = APIRouter()


# ============================================================================
# 1. 资源冲突检测 API (5个端点)
# ============================================================================

@router.post("/conflicts/detect", response_model=ConflictDetectionResponse, summary="检测资源冲突")
def detect_resource_conflicts(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    request: ConflictDetectionRequest,
) -> Any:
    """
    **检测资源冲突**
    
    - 实时扫描资源分配
    - 识别时间重叠和超负荷
    - 可选自动生成调度方案
    - AI评估严重程度
    """
    start_time = time.time()
    
    service = ResourceSchedulingAIService(db)
    
    # 检测冲突
    conflicts = service.detect_resource_conflicts(
        resource_id=request.resource_id,
        resource_type=request.resource_type or "PERSON",
        project_id=request.project_id,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    
    # 统计
    total_conflicts = len(conflicts)
    critical_conflicts = sum(1 for c in conflicts if c.severity == "CRITICAL")
    
    # 自动生成方案
    suggestions_generated = 0
    if request.auto_generate_suggestions and conflicts:
        for conflict in conflicts[:5]:  # 限制前5个
            try:
                service.generate_scheduling_suggestions(
                    conflict_id=conflict.id,
                    max_suggestions=2,
                )
                suggestions_generated += 1
            except Exception:
                pass
    
    # 记录日志
    _log_action(
        db=db,
        action_type="DETECT",
        action_desc=f"检测到{total_conflicts}个资源冲突",
        operator_id=current_user.id,
        operator_name=current_user.real_name,
        result="SUCCESS",
        execution_time_ms=int((time.time() - start_time) * 1000),
    )
    
    return ConflictDetectionResponse(
        total_conflicts=total_conflicts,
        new_conflicts=total_conflicts,  # 全部都是新的
        critical_conflicts=critical_conflicts,
        conflicts=[ResourceConflictDetectionInDB.model_validate(c) for c in conflicts],
        suggestions_generated=suggestions_generated,
        detection_time_ms=int((time.time() - start_time) * 1000),
    )


@router.get("/conflicts", response_model=List[ResourceConflictDetectionInDB], summary="查询资源冲突列表")
def list_conflicts(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="状态筛选"),
    severity: Optional[str] = Query(None, description="严重程度筛选"),
    resource_id: Optional[int] = Query(None, description="资源ID筛选"),
    is_resolved: Optional[bool] = Query(None, description="是否已解决"),
) -> Any:
    """
    **查询资源冲突列表**
    
    支持分页和多条件筛选
    """
    query = db.query(ResourceConflictDetection)
    
    if status:
        query = query.filter(ResourceConflictDetection.status == status)
    if severity:
        query = query.filter(ResourceConflictDetection.severity == severity)
    if resource_id:
        query = query.filter(ResourceConflictDetection.resource_id == resource_id)
    if is_resolved is not None:
        query = query.filter(ResourceConflictDetection.is_resolved == is_resolved)
    
    conflicts = query.order_by(desc(ResourceConflictDetection.priority_score)).offset(skip).limit(limit).all()
    
    return [ResourceConflictDetectionInDB.model_validate(c) for c in conflicts]


@router.get("/conflicts/{conflict_id}", response_model=ResourceConflictDetectionInDB, summary="获取冲突详情")
def get_conflict(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    conflict_id: int,
) -> Any:
    """获取指定冲突的详细信息"""
    conflict = db.query(ResourceConflictDetection).filter(ResourceConflictDetection.id == conflict_id).first()
    
    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conflict {conflict_id} not found",
        )
    
    return ResourceConflictDetectionInDB.model_validate(conflict)


@router.put("/conflicts/{conflict_id}", response_model=ResourceConflictDetectionInDB, summary="更新冲突状态")
def update_conflict(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    conflict_id: int,
    update_data: ResourceConflictDetectionUpdate,
) -> Any:
    """
    **更新冲突状态**
    
    - 标记为已解决
    - 修改严重程度
    - 添加解决说明
    """
    conflict = db.query(ResourceConflictDetection).filter(ResourceConflictDetection.id == conflict_id).first()
    
    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conflict {conflict_id} not found",
        )
    
    # 更新字段
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(conflict, field, value)
    
    # 如果标记为已解决
    if update_data.is_resolved:
        conflict.resolved_by = current_user.id
        conflict.resolved_at = datetime.now()
        conflict.status = "RESOLVED"
    
    conflict.updated_at = datetime.now()
    db.commit()
    db.refresh(conflict)
    
    # 记录日志
    _log_action(
        db=db,
        conflict_id=conflict_id,
        action_type="RESOLVE" if update_data.is_resolved else "UPDATE",
        action_desc=f"更新冲突状态",
        operator_id=current_user.id,
        operator_name=current_user.real_name,
        result="SUCCESS",
    )
    
    return ResourceConflictDetectionInDB.model_validate(conflict)


@router.delete("/conflicts/{conflict_id}", summary="删除冲突记录")
def delete_conflict(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    conflict_id: int,
) -> Any:
    """删除指定的冲突记录（仅用于误检）"""
    conflict = db.query(ResourceConflictDetection).filter(ResourceConflictDetection.id == conflict_id).first()
    
    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conflict {conflict_id} not found",
        )
    
    db.delete(conflict)
    db.commit()
    
    return {"message": f"Conflict {conflict_id} deleted"}


# ============================================================================
# 2. AI调度方案推荐 API (5个端点)
# ============================================================================

@router.post("/suggestions/generate", response_model=AISchedulingSuggestionResponse, summary="AI生成调度方案")
def generate_scheduling_suggestions(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    request: AISchedulingSuggestionRequest,
) -> Any:
    """
    **AI生成多个调度方案**
    
    - 使用GLM-5分析冲突
    - 生成2-5个备选方案
    - 评估可行性、成本、风险
    - 自动推荐最优方案
    """
    start_time = time.time()
    
    service = ResourceSchedulingAIService(db)
    
    try:
        suggestions = service.generate_scheduling_suggestions(
            conflict_id=request.conflict_id,
            max_suggestions=request.max_suggestions,
            prefer_minimal_impact=request.prefer_minimal_impact,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI生成失败: {str(e)}",
        )
    
    # 找到推荐方案
    recommended_id = next((s.id for s in suggestions if s.is_recommended), None)
    
    # 统计Token消耗
    total_tokens = sum(s.ai_tokens_used or 0 for s in suggestions)
    
    # 记录日志
    _log_action(
        db=db,
        conflict_id=request.conflict_id,
        action_type="SUGGEST",
        action_desc=f"AI生成{len(suggestions)}个调度方案",
        operator_id=current_user.id,
        operator_name=current_user.real_name,
        result="SUCCESS",
        execution_time_ms=int((time.time() - start_time) * 1000),
        ai_tokens_used=total_tokens,
    )
    
    return AISchedulingSuggestionResponse(
        conflict_id=request.conflict_id,
        suggestions=[ResourceSchedulingSuggestionInDB.model_validate(s) for s in suggestions],
        recommended_suggestion_id=recommended_id,
        generation_time_ms=int((time.time() - start_time) * 1000),
        ai_tokens_used=total_tokens,
    )


@router.get("/suggestions", response_model=List[ResourceSchedulingSuggestionInDB], summary="查询调度方案列表")
def list_suggestions(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    conflict_id: Optional[int] = Query(None, description="冲突ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    solution_type: Optional[str] = Query(None, description="方案类型筛选"),
    is_recommended: Optional[bool] = Query(None, description="是否推荐"),
) -> Any:
    """查询调度方案列表"""
    query = db.query(ResourceSchedulingSuggestion)
    
    if conflict_id:
        query = query.filter(ResourceSchedulingSuggestion.conflict_id == conflict_id)
    if status:
        query = query.filter(ResourceSchedulingSuggestion.status == status)
    if solution_type:
        query = query.filter(ResourceSchedulingSuggestion.solution_type == solution_type)
    if is_recommended is not None:
        query = query.filter(ResourceSchedulingSuggestion.is_recommended == is_recommended)
    
    suggestions = query.order_by(ResourceSchedulingSuggestion.rank_order).offset(skip).limit(limit).all()
    
    return [ResourceSchedulingSuggestionInDB.model_validate(s) for s in suggestions]


@router.get("/suggestions/{suggestion_id}", response_model=ResourceSchedulingSuggestionInDB, summary="获取方案详情")
def get_suggestion(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    suggestion_id: int,
) -> Any:
    """获取指定方案的详细信息"""
    suggestion = db.query(ResourceSchedulingSuggestion).filter(
        ResourceSchedulingSuggestion.id == suggestion_id
    ).first()
    
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion {suggestion_id} not found",
        )
    
    return ResourceSchedulingSuggestionInDB.model_validate(suggestion)


@router.put("/suggestions/{suggestion_id}/review", response_model=ResourceSchedulingSuggestionInDB, summary="审核调度方案")
def review_suggestion(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    suggestion_id: int,
    action: str = Query(..., description="审核动作: ACCEPT/REJECT"),
    review_comment: Optional[str] = Query(None, description="审核意见"),
) -> Any:
    """
    **审核调度方案**
    
    - ACCEPT: 接受方案
    - REJECT: 拒绝方案
    """
    suggestion = db.query(ResourceSchedulingSuggestion).filter(
        ResourceSchedulingSuggestion.id == suggestion_id
    ).first()
    
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion {suggestion_id} not found",
        )
    
    if action == "ACCEPT":
        suggestion.status = "ACCEPTED"
    elif action == "REJECT":
        suggestion.status = "REJECTED"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Use ACCEPT or REJECT.",
        )
    
    suggestion.reviewed_by = current_user.id
    suggestion.reviewed_at = datetime.now()
    suggestion.review_comment = review_comment
    suggestion.updated_at = datetime.now()
    
    db.commit()
    db.refresh(suggestion)
    
    # 记录日志
    _log_action(
        db=db,
        suggestion_id=suggestion_id,
        action_type="REVIEW",
        action_desc=f"审核方案: {action}",
        operator_id=current_user.id,
        operator_name=current_user.real_name,
        result="SUCCESS",
    )
    
    return ResourceSchedulingSuggestionInDB.model_validate(suggestion)


@router.put("/suggestions/{suggestion_id}/implement", response_model=ResourceSchedulingSuggestionInDB, summary="执行调度方案")
def implement_suggestion(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    suggestion_id: int,
    implementation_result: str = Query(..., description="执行结果描述"),
) -> Any:
    """
    **执行调度方案**
    
    标记方案为已执行状态
    """
    suggestion = db.query(ResourceSchedulingSuggestion).filter(
        ResourceSchedulingSuggestion.id == suggestion_id
    ).first()
    
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion {suggestion_id} not found",
        )
    
    if suggestion.status != "ACCEPTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ACCEPTED suggestions can be implemented",
        )
    
    suggestion.status = "IMPLEMENTED"
    suggestion.implemented_by = current_user.id
    suggestion.implemented_at = datetime.now()
    suggestion.implementation_result = implementation_result
    suggestion.updated_at = datetime.now()
    
    db.commit()
    db.refresh(suggestion)
    
    # 同时解决关联的冲突
    conflict = db.query(ResourceConflictDetection).filter(
        ResourceConflictDetection.id == suggestion.conflict_id
    ).first()
    
    if conflict:
        conflict.is_resolved = True
        conflict.resolved_by = current_user.id
        conflict.resolved_at = datetime.now()
        conflict.resolution_method = f"AI方案{suggestion.solution_type}"
        conflict.status = "RESOLVED"
        db.commit()
    
    # 记录日志
    _log_action(
        db=db,
        suggestion_id=suggestion_id,
        conflict_id=suggestion.conflict_id,
        action_type="IMPLEMENT",
        action_desc="执行调度方案",
        operator_id=current_user.id,
        operator_name=current_user.real_name,
        result="SUCCESS",
    )
    
    return ResourceSchedulingSuggestionInDB.model_validate(suggestion)


# ============================================================================
# 3. 资源需求预测 API (3个端点)
# ============================================================================

@router.post("/forecast", response_model=ForecastResponse, summary="生成资源需求预测")
def generate_forecast(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    request: ForecastRequest,
) -> Any:
    """
    **生成资源需求预测**
    
    - 预测未来1-12个月资源需求
    - AI分析历史趋势
    - 识别技能缺口
    - 提供招聘/培训建议
    """
    start_time = time.time()
    
    service = ResourceSchedulingAIService(db)
    
    forecasts = service.forecast_resource_demand(
        forecast_period=request.forecast_period,
        resource_type=request.resource_type,
        skill_category=request.skill_category,
    )
    
    # 统计关键缺口
    critical_gaps = sum(1 for f in forecasts if f.gap_severity in ["SHORTAGE", "CRITICAL"])
    total_hiring = sum(f.demand_gap for f in forecasts if f.demand_gap and f.demand_gap > 0)
    
    return ForecastResponse(
        forecasts=[ResourceDemandForecastInDB.model_validate(f) for f in forecasts],
        critical_gaps=critical_gaps,
        total_hiring_needed=total_hiring or 0,
        total_training_needed=0,  # TODO: 实现培训需求统计
        generation_time_ms=int((time.time() - start_time) * 1000),
    )


@router.get("/forecast", response_model=List[ResourceDemandForecastInDB], summary="查询预测列表")
def list_forecasts(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    forecast_period: Optional[str] = Query(None, description="预测周期"),
    status: Optional[str] = Query(None, description="状态筛选"),
) -> Any:
    """查询资源需求预测列表"""
    query = db.query(ResourceDemandForecast)
    
    if forecast_period:
        query = query.filter(ResourceDemandForecast.forecast_period == forecast_period)
    if status:
        query = query.filter(ResourceDemandForecast.status == status)
    
    forecasts = query.order_by(desc(ResourceDemandForecast.created_at)).offset(skip).limit(limit).all()
    
    return [ResourceDemandForecastInDB.model_validate(f) for f in forecasts]


@router.get("/forecast/{forecast_id}", response_model=ResourceDemandForecastInDB, summary="获取预测详情")
def get_forecast(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    forecast_id: int,
) -> Any:
    """获取指定预测的详细信息"""
    forecast = db.query(ResourceDemandForecast).filter(ResourceDemandForecast.id == forecast_id).first()
    
    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forecast {forecast_id} not found",
        )
    
    return ResourceDemandForecastInDB.model_validate(forecast)


# ============================================================================
# 4. 资源利用率分析 API (3个端点)
# ============================================================================

@router.post("/utilization/analyze", response_model=UtilizationAnalysisResponse, summary="分析资源利用率")
def analyze_utilization(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    request: UtilizationAnalysisRequest,
) -> Any:
    """
    **分析资源利用率**
    
    - 统计实际工时和可用工时
    - 计算利用率、效率率
    - 识别闲置和超负荷资源
    - AI优化建议
    """
    start_time = time.time()
    
    service = ResourceSchedulingAIService(db)
    
    analyses = []
    
    # 如果指定resource_id，分析单个资源
    if request.resource_id:
        analysis = service.analyze_resource_utilization(
            resource_id=request.resource_id,
            start_date=request.start_date,
            end_date=request.end_date,
            analysis_period=request.analysis_period,
        )
        analyses.append(analysis)
    else:
        # 否则分析所有资源（限制数量）
        from app.models.user import User
        users = db.query(User).filter(User.is_active == True).limit(50).all()
        
        for user in users:
            try:
                analysis = service.analyze_resource_utilization(
                    resource_id=user.id,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    analysis_period=request.analysis_period,
                )
                analyses.append(analysis)
            except Exception:
                pass
    
    # 统计
    idle_count = sum(1 for a in analyses if a.is_idle_resource)
    overloaded_count = sum(1 for a in analyses if a.is_overloaded)
    
    # 计算平均利用率
    avg_utilization = sum(a.utilization_rate or 0 for a in analyses) / len(analyses) if analyses else 0
    
    return UtilizationAnalysisResponse(
        analyses=[ResourceUtilizationAnalysisInDB.model_validate(a) for a in analyses],
        idle_resources_count=idle_count,
        overloaded_resources_count=overloaded_count,
        avg_utilization=avg_utilization,
        optimization_opportunities=idle_count + overloaded_count,
        analysis_time_ms=int((time.time() - start_time) * 1000),
    )


@router.get("/utilization", response_model=List[ResourceUtilizationAnalysisInDB], summary="查询利用率分析列表")
def list_utilization_analyses(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    resource_id: Optional[int] = Query(None, description="资源ID筛选"),
    is_idle: Optional[bool] = Query(None, description="是否闲置"),
    is_overloaded: Optional[bool] = Query(None, description="是否超负荷"),
) -> Any:
    """查询资源利用率分析列表"""
    query = db.query(ResourceUtilizationAnalysis)
    
    if resource_id:
        query = query.filter(ResourceUtilizationAnalysis.resource_id == resource_id)
    if is_idle is not None:
        query = query.filter(ResourceUtilizationAnalysis.is_idle_resource == is_idle)
    if is_overloaded is not None:
        query = query.filter(ResourceUtilizationAnalysis.is_overloaded == is_overloaded)
    
    analyses = query.order_by(desc(ResourceUtilizationAnalysis.created_at)).offset(skip).limit(limit).all()
    
    return [ResourceUtilizationAnalysisInDB.model_validate(a) for a in analyses]


@router.get("/utilization/{analysis_id}", response_model=ResourceUtilizationAnalysisInDB, summary="获取利用率分析详情")
def get_utilization_analysis(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    analysis_id: int,
) -> Any:
    """获取指定利用率分析的详细信息"""
    analysis = db.query(ResourceUtilizationAnalysis).filter(
        ResourceUtilizationAnalysis.id == analysis_id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis {analysis_id} not found",
        )
    
    return ResourceUtilizationAnalysisInDB.model_validate(analysis)


# ============================================================================
# 5. 仪表板和统计 API (2个端点)
# ============================================================================

@router.get("/dashboard/summary", response_model=DashboardSummary, summary="资源调度仪表板摘要")
def get_dashboard_summary(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    **资源调度仪表板摘要**
    
    汇总所有关键指标
    """
    # 冲突统计
    total_conflicts = db.query(func.count(ResourceConflictDetection.id)).scalar() or 0
    critical_conflicts = db.query(func.count(ResourceConflictDetection.id)).filter(
        ResourceConflictDetection.severity == "CRITICAL"
    ).scalar() or 0
    unresolved_conflicts = db.query(func.count(ResourceConflictDetection.id)).filter(
        ResourceConflictDetection.is_resolved == False
    ).scalar() or 0
    
    # 方案统计
    total_suggestions = db.query(func.count(ResourceSchedulingSuggestion.id)).scalar() or 0
    pending_suggestions = db.query(func.count(ResourceSchedulingSuggestion.id)).filter(
        ResourceSchedulingSuggestion.status == "PENDING"
    ).scalar() or 0
    implemented_suggestions = db.query(func.count(ResourceSchedulingSuggestion.id)).filter(
        ResourceSchedulingSuggestion.status == "IMPLEMENTED"
    ).scalar() or 0
    
    # 利用率统计
    idle_resources = db.query(func.count(ResourceUtilizationAnalysis.id)).filter(
        ResourceUtilizationAnalysis.is_idle_resource == True
    ).scalar() or 0
    overloaded_resources = db.query(func.count(ResourceUtilizationAnalysis.id)).filter(
        ResourceUtilizationAnalysis.is_overloaded == True
    ).scalar() or 0
    
    # 平均利用率
    avg_util = db.query(func.avg(ResourceUtilizationAnalysis.utilization_rate)).scalar()
    avg_utilization = float(avg_util) if avg_util else 0.0
    
    # 预测统计
    forecasts_count = db.query(func.count(ResourceDemandForecast.id)).filter(
        ResourceDemandForecast.status == "ACTIVE"
    ).scalar() or 0
    
    critical_gaps = db.query(func.count(ResourceDemandForecast.id)).filter(
        ResourceDemandForecast.gap_severity.in_(["SHORTAGE", "CRITICAL"])
    ).scalar() or 0
    
    # 招聘需求
    hiring_query = db.query(func.sum(ResourceDemandForecast.demand_gap)).filter(
        ResourceDemandForecast.demand_gap > 0
    ).scalar()
    hiring_needed = int(hiring_query) if hiring_query else 0
    
    # 最近检测/分析时间
    last_conflict = db.query(ResourceConflictDetection).order_by(
        desc(ResourceConflictDetection.created_at)
    ).first()
    
    last_analysis = db.query(ResourceUtilizationAnalysis).order_by(
        desc(ResourceUtilizationAnalysis.created_at)
    ).first()
    
    return DashboardSummary(
        total_conflicts=total_conflicts,
        critical_conflicts=critical_conflicts,
        unresolved_conflicts=unresolved_conflicts,
        total_suggestions=total_suggestions,
        pending_suggestions=pending_suggestions,
        implemented_suggestions=implemented_suggestions,
        idle_resources=idle_resources,
        overloaded_resources=overloaded_resources,
        avg_utilization=avg_utilization,
        forecasts_count=forecasts_count,
        critical_gaps=critical_gaps,
        hiring_needed=hiring_needed,
        last_detection_time=last_conflict.created_at if last_conflict else None,
        last_analysis_time=last_analysis.created_at if last_analysis else None,
    )


@router.get("/logs", response_model=List[ResourceSchedulingLogInDB], summary="查询操作日志")
def list_logs(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action_type: Optional[str] = Query(None, description="操作类型筛选"),
    conflict_id: Optional[int] = Query(None, description="冲突ID筛选"),
) -> Any:
    """查询资源调度操作日志"""
    query = db.query(ResourceSchedulingLog)
    
    if action_type:
        query = query.filter(ResourceSchedulingLog.action_type == action_type)
    if conflict_id:
        query = query.filter(ResourceSchedulingLog.conflict_id == conflict_id)
    
    logs = query.order_by(desc(ResourceSchedulingLog.created_at)).offset(skip).limit(limit).all()
    
    return [ResourceSchedulingLogInDB.model_validate(log) for log in logs]


# ============================================================================
# 辅助函数
# ============================================================================

def _log_action(
    db: Session,
    action_type: str,
    action_desc: str,
    operator_id: int,
    operator_name: str,
    result: str = "SUCCESS",
    conflict_id: Optional[int] = None,
    suggestion_id: Optional[int] = None,
    execution_time_ms: Optional[int] = None,
    ai_tokens_used: Optional[int] = None,
    error_message: Optional[str] = None,
) -> None:
    """记录操作日志"""
    log = ResourceSchedulingLog(
        conflict_id=conflict_id,
        suggestion_id=suggestion_id,
        action_type=action_type,
        action_desc=action_desc,
        operator_id=operator_id,
        operator_name=operator_name,
        result=result,
        execution_time_ms=execution_time_ms,
        ai_tokens_used=ai_tokens_used,
        error_message=error_message,
    )
    db.add(log)
    db.commit()
