"""
售前AI成本估算 API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.auth import get_current_user, get_db
from app.models.user import User
from app.models.sales.presale_ai_cost import (
    PresaleAICostEstimation,
    PresaleCostHistory
)
from app.schemas.sales.presale_ai_cost import (
    CostEstimationInput,
    CostEstimationResponse,
    CostOptimizationInput,
    CostOptimizationResponse,
    PricingInput,
    PricingResponse,
    CostComparisonInput,
    CostComparisonResponse,
    CostComparisonItem,
    HistoricalAccuracyResponse,
    UpdateActualCostInput,
    UpdateActualCostResponse,
    CostBreakdown
)
from app.services.sales.ai_cost_estimation_service import AICostEstimationService

router = APIRouter(prefix="/presale/ai", tags=["售前AI成本估算"])


@router.post("/estimate-cost", response_model=CostEstimationResponse, summary="智能成本估算")
async def estimate_cost(
    input_data: CostEstimationInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    智能成本估算
    
    **功能**:
    - 多维度成本预测(硬件/软件/安装/服务/风险)
    - 基于历史数据的AI分析
    - 自动生成优化建议
    - 智能定价推荐
    
    **输入参数**:
    - presale_ticket_id: 售前工单ID
    - project_type: 项目类型
    - hardware_items: 硬件清单
    - software_requirements: 软件需求
    - complexity_level: 复杂度(low/medium/high)
    
    **返回**:
    - 详细成本分解
    - 优化建议列表
    - 定价推荐(低中高三档)
    - 置信度评分
    """
    try:
        service = AICostEstimationService(db, current_user.id)
        result = await service.estimate_cost(input_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"估算失败: {str(e)}")


@router.get("/cost-estimation/{estimation_id}", response_model=CostEstimationResponse, summary="获取估算结果")
async def get_cost_estimation(
    estimation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取成本估算结果详情
    """
    estimation = db.query(PresaleAICostEstimation).filter(
        PresaleAICostEstimation.id == estimation_id
    ).first()
    
    if not estimation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="估算记录不存在")
    
    # 构建响应
    from app.schemas.sales.presale_ai_cost import OptimizationSuggestion, PricingRecommendation
    
    return CostEstimationResponse(
        id=estimation.id,
        presale_ticket_id=estimation.presale_ticket_id,
        solution_id=estimation.solution_id,
        cost_breakdown=CostBreakdown(
            hardware_cost=estimation.hardware_cost,
            software_cost=estimation.software_cost,
            installation_cost=estimation.installation_cost,
            service_cost=estimation.service_cost,
            risk_reserve=estimation.risk_reserve,
            total_cost=estimation.total_cost
        ),
        optimization_suggestions=[
            OptimizationSuggestion(**s) for s in (estimation.optimization_suggestions or [])
        ],
        pricing_recommendations=PricingRecommendation(**estimation.pricing_recommendations) if estimation.pricing_recommendations else None,
        confidence_score=estimation.confidence_score,
        model_version=estimation.model_version,
        created_at=estimation.created_at
    )


@router.post("/optimize-cost", response_model=CostOptimizationResponse, summary="成本优化建议")
async def optimize_cost(
    input_data: CostOptimizationInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    成本优化分析
    
    **功能**:
    - 识别成本过高项
    - 推荐替代方案
    - 供应商比价建议
    - 风险可控的优化方案
    
    **输入参数**:
    - estimation_id: 估算记录ID
    - focus_areas: 重点优化领域(可选)
    - max_risk_level: 最大风险接受度
    
    **返回**:
    - 原始成本 vs 优化后成本
    - 详细优化建议
    - 可行性评估
    """
    try:
        service = AICostEstimationService(db, current_user.id)
        result = await service.optimize_cost(input_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"优化失败: {str(e)}")


@router.post("/pricing-recommendation", response_model=PricingResponse, summary="定价推荐")
async def pricing_recommendation(
    input_data: PricingInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    智能定价推荐
    
    **功能**:
    - 基于成本+目标毛利率
    - 市场竞争分析
    - 高中低三档报价
    - 价格敏感度分析
    
    **输入参数**:
    - estimation_id: 估算记录ID
    - target_margin_rate: 目标毛利率(默认30%)
    - market_competition_level: 市场竞争程度
    - customer_budget: 客户预算(可选)
    
    **返回**:
    - 低中高三档报价
    - 敏感度分析
    - 定价策略建议
    """
    try:
        service = AICostEstimationService(db, current_user.id)
        result = await service.recommend_pricing(input_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"定价推荐失败: {str(e)}")


@router.get("/cost-breakdown/{ticket_id}", response_model=CostBreakdown, summary="成本分解")
async def get_cost_breakdown(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取售前工单的最新成本分解
    """
    estimation = db.query(PresaleAICostEstimation).filter(
        PresaleAICostEstimation.presale_ticket_id == ticket_id
    ).order_by(PresaleAICostEstimation.created_at.desc()).first()
    
    if not estimation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该工单的成本估算记录")
    
    return CostBreakdown(
        hardware_cost=estimation.hardware_cost,
        software_cost=estimation.software_cost,
        installation_cost=estimation.installation_cost,
        service_cost=estimation.service_cost,
        risk_reserve=estimation.risk_reserve,
        total_cost=estimation.total_cost
    )


@router.post("/cost-comparison", response_model=CostComparisonResponse, summary="成本对比分析")
async def cost_comparison(
    input_data: CostComparisonInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    成本对比分析(对比多个估算方案)
    
    **功能**:
    - 并排对比多个方案
    - 差异分析
    - 推荐最优方案
    
    **输入参数**:
    - estimation_ids: 估算记录ID列表(2-5个)
    
    **返回**:
    - 各方案详细对比
    - 差异分析摘要
    - 推荐意见
    """
    if len(input_data.estimation_ids) < 2 or len(input_data.estimation_ids) > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="对比方案数量应在2-5个之间")
    
    estimations = db.query(PresaleAICostEstimation).filter(
        PresaleAICostEstimation.id.in_(input_data.estimation_ids)
    ).all()
    
    if len(estimations) != len(input_data.estimation_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部分估算记录不存在")
    
    # 构建对比项
    items = [
        CostComparisonItem(
            estimation_id=est.id,
            presale_ticket_id=est.presale_ticket_id,
            total_cost=est.total_cost,
            cost_breakdown=CostBreakdown(
                hardware_cost=est.hardware_cost,
                software_cost=est.software_cost,
                installation_cost=est.installation_cost,
                service_cost=est.service_cost,
                risk_reserve=est.risk_reserve,
                total_cost=est.total_cost
            ),
            confidence_score=est.confidence_score
        )
        for est in estimations
    ]
    
    # 对比分析
    total_costs = [float(item.total_cost) for item in items]
    min_cost = min(total_costs)
    max_cost = max(total_costs)
    avg_cost = sum(total_costs) / len(total_costs)
    
    comparison_summary = {
        "min_cost": min_cost,
        "max_cost": max_cost,
        "avg_cost": avg_cost,
        "cost_range": max_cost - min_cost,
        "variance_rate": ((max_cost - min_cost) / avg_cost * 100) if avg_cost > 0 else 0
    }
    
    # 推荐最优方案
    best_item = min(items, key=lambda x: float(x.total_cost))
    recommendations = f"推荐方案ID {best_item.estimation_id}: 成本最低({best_item.total_cost}元), 置信度: {best_item.confidence_score or 'N/A'}"
    
    return CostComparisonResponse(
        items=items,
        comparison_summary=comparison_summary,
        recommendations=recommendations
    )


@router.get("/historical-accuracy", response_model=HistoricalAccuracyResponse, summary="历史准确度")
async def get_historical_accuracy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取AI模型的历史预测准确度
    
    **功能**:
    - 统计总预测次数
    - 平均偏差率
    - 准确率(偏差<15%的比例)
    - 趋势分析
    
    **返回**:
    - 总体准确度指标
    - 最佳/最差表现类别
    - 近期趋势
    """
    try:
        service = AICostEstimationService(db, current_user.id)
        result = await service.get_historical_accuracy()
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"查询失败: {str(e)}")


@router.post("/update-actual-cost", response_model=UpdateActualCostResponse, summary="更新实际成本")
async def update_actual_cost(
    input_data: UpdateActualCostInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新实际成本(用于模型学习)
    
    **功能**:
    - 记录实际发生成本
    - 计算预测偏差
    - 反馈给AI模型学习
    - 提升未来预测准确度
    
    **输入参数**:
    - estimation_id: 估算记录ID
    - actual_cost: 实际总成本
    - actual_breakdown: 实际成本分解(可选)
    
    **返回**:
    - 偏差分析
    - 学习反馈状态
    """
    try:
        service = AICostEstimationService(db, current_user.id)
        result = await service.update_actual_cost(input_data)
        
        return UpdateActualCostResponse(
            history_id=result["history_id"],
            variance_rate=result["variance_rate"],
            variance_analysis=result["variance_analysis"],
            learning_applied=result["learning_applied"],
            message=result["message"]
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新失败: {str(e)}")
