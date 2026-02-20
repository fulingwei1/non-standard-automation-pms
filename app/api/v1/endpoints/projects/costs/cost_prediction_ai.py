# -*- coding: utf-8 -*-
"""
成本预测与优化AI端点
提供AI驱动的成本预测、超支预警和优化建议功能
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models import (
    CostOptimizationSuggestion,
    CostPrediction,
    User,
)
from app.services.project_cost_prediction import ProjectCostPredictionService

router = APIRouter()


# ==================== Pydantic Schemas ====================

class PredictionResultSchema(BaseModel):
    """预测结果响应"""
    id: int
    project_id: int
    project_code: str
    prediction_date: date
    prediction_version: str
    
    # 当前状态
    current_bac: Decimal
    current_ac: Decimal
    current_ev: Decimal
    current_cpi: Optional[Decimal]
    current_percent_complete: Optional[Decimal]
    
    # 预测结果
    predicted_eac: Decimal
    predicted_eac_confidence: Optional[Decimal]
    eac_lower_bound: Optional[Decimal]
    eac_upper_bound: Optional[Decimal]
    eac_most_likely: Optional[Decimal]
    
    # 超支风险
    overrun_probability: Optional[Decimal]
    expected_overrun_amount: Optional[Decimal]
    overrun_percentage: Optional[Decimal]
    risk_level: Optional[str]
    risk_score: Optional[Decimal]
    
    # 趋势
    cost_trend: Optional[str]
    
    # 方法
    prediction_method: Optional[str]
    model_version: Optional[str]
    data_quality_score: Optional[Decimal]
    
    class Config:
        from_attributes = True


class PredictionDetailSchema(PredictionResultSchema):
    """预测详情（包含完整分析）"""
    
    # 完整分析数据
    risk_factors: Optional[dict]
    trend_analysis: Optional[str]
    cpi_trend_data: Optional[dict]
    ai_analysis_summary: Optional[str]
    ai_insights: Optional[dict]
    sensitivity_analysis: Optional[dict]
    
    # 元数据
    is_approved: bool
    approved_by: Optional[int]
    approved_at: Optional[date]
    created_by: Optional[int]
    created_at: Optional[date]
    notes: Optional[str]


class CreatePredictionRequest(BaseModel):
    """创建预测请求"""
    project_id: int = Field(..., description="项目ID")
    prediction_version: str = Field(default="V1.0", description="预测版本号")
    use_ai: bool = Field(default=True, description="是否使用AI预测")
    notes: Optional[str] = Field(None, description="备注")


class OptimizationSuggestionSchema(BaseModel):
    """优化建议响应"""
    id: int
    suggestion_code: str
    suggestion_title: str
    suggestion_type: Optional[str]
    priority: Optional[str]
    
    description: str
    proposed_action: Optional[str]
    
    # 财务影响
    estimated_cost_saving: Optional[Decimal]
    implementation_cost: Optional[Decimal]
    net_benefit: Optional[Decimal]
    roi_percentage: Optional[Decimal]
    
    # 影响评估
    impact_on_schedule: Optional[str]
    impact_on_quality: Optional[str]
    implementation_risk: Optional[str]
    
    # AI信息
    ai_confidence_score: Optional[Decimal]
    
    # 状态
    status: Optional[str]
    
    class Config:
        from_attributes = True


class OptimizationSuggestionDetailSchema(OptimizationSuggestionSchema):
    """优化建议详情"""
    
    current_situation: Optional[str]
    implementation_steps: Optional[dict]
    ai_reasoning: Optional[str]
    similar_cases: Optional[dict]
    
    # 实施跟踪
    assigned_to: Optional[int]
    start_date: Optional[date]
    target_completion_date: Optional[date]
    actual_completion_date: Optional[date]
    
    # 实施结果
    actual_cost_saving: Optional[Decimal]
    actual_implementation_cost: Optional[Decimal]
    effectiveness_rating: Optional[int]
    lessons_learned: Optional[str]
    
    # 审核
    reviewed_by: Optional[int]
    reviewed_at: Optional[date]
    review_decision: Optional[str]
    review_comments: Optional[str]
    
    created_by: Optional[int]
    created_at: Optional[date]


class ApprovalRequest(BaseModel):
    """审批请求"""
    decision: str = Field(..., description="审批决定：APPROVED/REJECTED/NEED_MORE_INFO")
    comments: Optional[str] = Field(None, description="审批意见")


class AssignmentRequest(BaseModel):
    """分配请求"""
    assigned_to: int = Field(..., description="责任人ID")
    target_completion_date: Optional[date] = Field(None, description="目标完成日期")


class ImplementationResultRequest(BaseModel):
    """实施结果记录"""
    actual_cost_saving: Decimal = Field(..., description="实际成本节约")
    actual_implementation_cost: Decimal = Field(..., description="实际实施成本")
    effectiveness_rating: int = Field(..., ge=1, le=5, description="有效性评分（1-5星）")
    lessons_learned: Optional[str] = Field(None, description="经验教训")


# ==================== API Endpoints ====================

@router.post("/predictions", response_model=PredictionDetailSchema, status_code=status.HTTP_201_CREATED)
def create_cost_prediction(
    request: CreatePredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建成本预测
    
    使用AI（GLM-5）或传统方法预测项目最终成本，并进行超支风险评估。
    
    - **project_id**: 项目ID
    - **prediction_version**: 预测版本号（如：V1.0, V2.0）
    - **use_ai**: 是否使用AI预测（默认：true）
    - **notes**: 备注说明
    
    返回完整的预测结果，包括：
    - 预测的EAC（完工估算）
    - 超支风险评估
    - 成本趋势分析
    - AI洞察（如启用AI）
    """
    service = ProjectCostPredictionService(db)
    
    try:
        prediction = service.create_prediction(
            project_id=request.project_id,
            prediction_version=request.prediction_version,
            use_ai=request.use_ai,
            created_by=current_user.id,
            notes=request.notes
        )
        
        return prediction
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预测创建失败: {str(e)}"
        )


@router.get("/predictions/{prediction_id}", response_model=PredictionDetailSchema)
def get_prediction_detail(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取预测详情
    
    返回指定预测的完整详情，包括AI分析结果和风险因素。
    """
    prediction = db.query(CostPrediction).filter(
        CostPrediction.id == prediction_id
    ).first()
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"预测不存在: id={prediction_id}"
        )
    
    return prediction


@router.get("/predictions/latest", response_model=PredictionDetailSchema)
def get_latest_prediction(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目最新预测
    
    返回指定项目的最新成本预测结果。
    """
    service = ProjectCostPredictionService(db)
    prediction = service.get_latest_prediction(project_id)
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目暂无预测数据: project_id={project_id}"
        )
    
    return prediction


@router.get("/predictions/history", response_model=List[PredictionResultSchema])
def get_prediction_history(
    project_id: int,
    limit: int = Query(default=10, ge=1, le=50, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取预测历史
    
    返回项目的历史预测记录，用于趋势分析。
    """
    service = ProjectCostPredictionService(db)
    predictions = service.get_prediction_history(project_id, limit=limit)
    
    return predictions


@router.post("/predictions/{prediction_id}/approve", response_model=PredictionDetailSchema)
def approve_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    审批预测
    
    审批通过后，预测结果可用于正式决策。
    """
    prediction = db.query(CostPrediction).filter(
        CostPrediction.id == prediction_id
    ).first()
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"预测不存在: id={prediction_id}"
        )
    
    prediction.is_approved = True
    prediction.approved_by = current_user.id
    prediction.approved_at = date.today()
    
    db.commit()
    db.refresh(prediction)
    
    return prediction


# ==================== 优化建议端点 ====================

@router.get("/predictions/{prediction_id}/suggestions", response_model=List[OptimizationSuggestionSchema])
def get_optimization_suggestions(
    prediction_id: int,
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    priority_filter: Optional[str] = Query(None, description="优先级筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取优化建议列表
    
    返回指定预测的所有优化建议。
    
    - **status_filter**: 按状态筛选（PENDING/APPROVED/REJECTED/IN_PROGRESS/COMPLETED）
    - **priority_filter**: 按优先级筛选（CRITICAL/HIGH/MEDIUM/LOW）
    """
    query = db.query(CostOptimizationSuggestion).filter(
        CostOptimizationSuggestion.prediction_id == prediction_id
    )
    
    if status_filter:
        query = query.filter(CostOptimizationSuggestion.status == status_filter)
    
    if priority_filter:
        query = query.filter(CostOptimizationSuggestion.priority == priority_filter)
    
    suggestions = query.all()
    
    return suggestions


@router.get("/suggestions/{suggestion_id}", response_model=OptimizationSuggestionDetailSchema)
def get_suggestion_detail(
    suggestion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取优化建议详情
    
    返回指定建议的完整信息，包括AI推理、实施步骤等。
    """
    suggestion = db.query(CostOptimizationSuggestion).filter(
        CostOptimizationSuggestion.id == suggestion_id
    ).first()
    
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"优化建议不存在: id={suggestion_id}"
        )
    
    return suggestion


@router.post("/suggestions/{suggestion_id}/review", response_model=OptimizationSuggestionDetailSchema)
def review_suggestion(
    suggestion_id: int,
    request: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    审核优化建议
    
    - **decision**: APPROVED（批准）/ REJECTED（拒绝）/ NEED_MORE_INFO（需要更多信息）
    - **comments**: 审核意见
    """
    suggestion = db.query(CostOptimizationSuggestion).filter(
        CostOptimizationSuggestion.id == suggestion_id
    ).first()
    
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"优化建议不存在: id={suggestion_id}"
        )
    
    suggestion.reviewed_by = current_user.id
    suggestion.reviewed_at = date.today()
    suggestion.review_decision = request.decision
    suggestion.review_comments = request.comments
    
    if request.decision == "APPROVED":
        suggestion.status = "APPROVED"
    elif request.decision == "REJECTED":
        suggestion.status = "REJECTED"
    
    db.commit()
    db.refresh(suggestion)
    
    return suggestion


@router.post("/suggestions/{suggestion_id}/assign", response_model=OptimizationSuggestionDetailSchema)
def assign_suggestion(
    suggestion_id: int,
    request: AssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    分配优化建议
    
    将建议分配给责任人执行。
    """
    from app.models import User as UserModel
    
    suggestion = db.query(CostOptimizationSuggestion).filter(
        CostOptimizationSuggestion.id == suggestion_id
    ).first()
    
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"优化建议不存在: id={suggestion_id}"
        )
    
    # 验证责任人存在
    assignee = db.query(UserModel).filter(UserModel.id == request.assigned_to).first()
    if not assignee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户不存在: id={request.assigned_to}"
        )
    
    suggestion.assigned_to = request.assigned_to
    suggestion.target_completion_date = request.target_completion_date
    suggestion.status = "IN_PROGRESS"
    suggestion.start_date = date.today()
    
    db.commit()
    db.refresh(suggestion)
    
    return suggestion


@router.post("/suggestions/{suggestion_id}/complete", response_model=OptimizationSuggestionDetailSchema)
def complete_suggestion(
    suggestion_id: int,
    request: ImplementationResultRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    完成优化建议
    
    记录实施结果和实际效果。
    """
    suggestion = db.query(CostOptimizationSuggestion).filter(
        CostOptimizationSuggestion.id == suggestion_id
    ).first()
    
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"优化建议不存在: id={suggestion_id}"
        )
    
    suggestion.actual_cost_saving = request.actual_cost_saving
    suggestion.actual_implementation_cost = request.actual_implementation_cost
    suggestion.effectiveness_rating = request.effectiveness_rating
    suggestion.lessons_learned = request.lessons_learned
    suggestion.actual_completion_date = date.today()
    suggestion.status = "COMPLETED"
    
    db.commit()
    db.refresh(suggestion)
    
    return suggestion


@router.get("/cost-health", response_model=dict)
def get_project_cost_health(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目成本健康度
    
    综合评估项目的成本状态，包括：
    - 最新预测结果
    - 超支风险等级
    - 待处理的优化建议
    - 成本趋势
    """
    service = ProjectCostPredictionService(db)
    
    try:
        health_analysis = service.get_cost_health_analysis(project_id)
        return health_analysis
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
