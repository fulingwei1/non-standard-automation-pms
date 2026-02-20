# -*- coding: utf-8 -*-
"""
资源冲突智能调度系统 - API端点
重构后的薄控制器，业务逻辑已迁移到服务层
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.resource_scheduling import (
    AISchedulingSuggestionRequest,
    AISchedulingSuggestionResponse,
    ConflictDetectionRequest,
    ConflictDetectionResponse,
    DashboardSummary,
    ForecastRequest,
    ForecastResponse,
    ResourceConflictDetectionInDB,
    ResourceConflictDetectionUpdate,
    ResourceDemandForecastInDB,
    ResourceSchedulingLogInDB,
    ResourceSchedulingSuggestionInDB,
    ResourceUtilizationAnalysisInDB,
    UtilizationAnalysisRequest,
    UtilizationAnalysisResponse,
)
from app.services.resource_scheduling import ResourceSchedulingService


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
    service = ResourceSchedulingService(db)
    
    result = service.detect_conflicts(
        resource_id=request.resource_id,
        resource_type=request.resource_type or "PERSON",
        project_id=request.project_id,
        start_date=request.start_date,
        end_date=request.end_date,
        auto_generate_suggestions=request.auto_generate_suggestions,
        operator_id=current_user.id,
        operator_name=current_user.real_name,
    )
    
    return ConflictDetectionResponse(
        total_conflicts=result["total_conflicts"],
        new_conflicts=result["total_conflicts"],
        critical_conflicts=result["critical_conflicts"],
        conflicts=[ResourceConflictDetectionInDB.model_validate(c) for c in result["conflicts"]],
        suggestions_generated=result["suggestions_generated"],
        detection_time_ms=result["detection_time_ms"],
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
    service = ResourceSchedulingService(db)
    
    conflicts = service.list_conflicts(
        skip=skip,
        limit=limit,
        status=status,
        severity=severity,
        resource_id=resource_id,
        is_resolved=is_resolved,
    )
    
    return [ResourceConflictDetectionInDB.model_validate(c) for c in conflicts]


@router.get("/conflicts/{conflict_id}", response_model=ResourceConflictDetectionInDB, summary="获取冲突详情")
def get_conflict(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    conflict_id: int,
) -> Any:
    """获取指定冲突的详细信息"""
    service = ResourceSchedulingService(db)
    
    conflict = service.get_conflict(conflict_id)
    
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
    service = ResourceSchedulingService(db)
    
    conflict = service.update_conflict(
        conflict_id=conflict_id,
        update_data=update_data.model_dump(exclude_unset=True),
        operator_id=current_user.id,
        operator_name=current_user.real_name,
    )
    
    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conflict {conflict_id} not found",
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
    service = ResourceSchedulingService(db)
    
    success = service.delete_conflict(conflict_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conflict {conflict_id} not found",
        )
    
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
    service = ResourceSchedulingService(db)
    
    try:
        result = service.generate_suggestions(
            conflict_id=request.conflict_id,
            max_suggestions=request.max_suggestions,
            prefer_minimal_impact=request.prefer_minimal_impact,
            operator_id=current_user.id,
            operator_name=current_user.real_name,
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
    
    return AISchedulingSuggestionResponse(
        conflict_id=request.conflict_id,
        suggestions=[ResourceSchedulingSuggestionInDB.model_validate(s) for s in result["suggestions"]],
        recommended_suggestion_id=result["recommended_id"],
        generation_time_ms=result["generation_time_ms"],
        ai_tokens_used=result["total_tokens"],
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
    service = ResourceSchedulingService(db)
    
    suggestions = service.list_suggestions(
        skip=skip,
        limit=limit,
        conflict_id=conflict_id,
        status=status,
        solution_type=solution_type,
        is_recommended=is_recommended,
    )
    
    return [ResourceSchedulingSuggestionInDB.model_validate(s) for s in suggestions]


@router.get("/suggestions/{suggestion_id}", response_model=ResourceSchedulingSuggestionInDB, summary="获取方案详情")
def get_suggestion(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    suggestion_id: int,
) -> Any:
    """获取指定方案的详细信息"""
    service = ResourceSchedulingService(db)
    
    suggestion = service.get_suggestion(suggestion_id)
    
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
    service = ResourceSchedulingService(db)
    
    success, suggestion, error_msg = service.review_suggestion(
        suggestion_id=suggestion_id,
        action=action,
        review_comment=review_comment,
        operator_id=current_user.id,
        operator_name=current_user.real_name,
    )
    
    if not success:
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
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
    service = ResourceSchedulingService(db)
    
    success, suggestion, error_msg = service.implement_suggestion(
        suggestion_id=suggestion_id,
        implementation_result=implementation_result,
        operator_id=current_user.id,
        operator_name=current_user.real_name,
    )
    
    if not success:
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
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
    service = ResourceSchedulingService(db)
    
    result = service.generate_forecast(
        forecast_period=request.forecast_period,
        resource_type=request.resource_type,
        skill_category=request.skill_category,
    )
    
    return ForecastResponse(
        forecasts=[ResourceDemandForecastInDB.model_validate(f) for f in result["forecasts"]],
        critical_gaps=result["critical_gaps"],
        total_hiring_needed=result["total_hiring"],
        total_training_needed=0,  # TODO: 实现培训需求统计
        generation_time_ms=result["generation_time_ms"],
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
    service = ResourceSchedulingService(db)
    
    forecasts = service.list_forecasts(
        skip=skip,
        limit=limit,
        forecast_period=forecast_period,
        status=status,
    )
    
    return [ResourceDemandForecastInDB.model_validate(f) for f in forecasts]


@router.get("/forecast/{forecast_id}", response_model=ResourceDemandForecastInDB, summary="获取预测详情")
def get_forecast(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    forecast_id: int,
) -> Any:
    """获取指定预测的详细信息"""
    service = ResourceSchedulingService(db)
    
    forecast = service.get_forecast(forecast_id)
    
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
    service = ResourceSchedulingService(db)
    
    result = service.analyze_utilization(
        resource_id=request.resource_id,
        start_date=request.start_date,
        end_date=request.end_date,
        analysis_period=request.analysis_period,
    )
    
    return UtilizationAnalysisResponse(
        analyses=[ResourceUtilizationAnalysisInDB.model_validate(a) for a in result["analyses"]],
        idle_resources_count=result["idle_count"],
        overloaded_resources_count=result["overloaded_count"],
        avg_utilization=result["avg_utilization"],
        optimization_opportunities=result["optimization_opportunities"],
        analysis_time_ms=result["analysis_time_ms"],
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
    service = ResourceSchedulingService(db)
    
    analyses = service.list_utilization_analyses(
        skip=skip,
        limit=limit,
        resource_id=resource_id,
        is_idle=is_idle,
        is_overloaded=is_overloaded,
    )
    
    return [ResourceUtilizationAnalysisInDB.model_validate(a) for a in analyses]


@router.get("/utilization/{analysis_id}", response_model=ResourceUtilizationAnalysisInDB, summary="获取利用率分析详情")
def get_utilization_analysis(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    analysis_id: int,
) -> Any:
    """获取指定利用率分析的详细信息"""
    service = ResourceSchedulingService(db)
    
    analysis = service.get_utilization_analysis(analysis_id)
    
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
    service = ResourceSchedulingService(db)
    
    summary = service.get_dashboard_summary()
    
    return DashboardSummary(**summary)


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
    service = ResourceSchedulingService(db)
    
    logs = service.list_logs(
        skip=skip,
        limit=limit,
        action_type=action_type,
        conflict_id=conflict_id,
    )
    
    return [ResourceSchedulingLogInDB.model_validate(log) for log in logs]
