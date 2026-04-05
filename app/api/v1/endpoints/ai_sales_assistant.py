# -*- coding: utf-8 -*-
"""
AI销售助手API
提供话术推荐、方案生成、竞品分析、谈判建议、流失预警
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.services.sales_ai_assistant_service import SalesAIAssistantService

router = APIRouter()


# ========== 1. AI话术推荐 ==========


@router.get("/customers/{customer_id}/recommend-scripts", summary="AI推荐销售话术")
def recommend_scripts(
    customer_id: int = Path(..., description="客户ID"),
    opportunity_id: Optional[int] = Query(None, description="商机ID"),
    scenario_type: Optional[str] = Query(None, description="场景类型"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """根据客户特征AI推荐销售话术"""
    service = SalesAIAssistantService(db)
    return service.recommend_scripts(customer_id, opportunity_id, scenario_type)


# ========== 2. AI方案生成 ==========


@router.post("/opportunities/{opportunity_id}/generate-proposal", summary="AI生成方案")
def generate_proposal(
    opportunity_id: int = Path(..., description="商机ID"),
    proposal_type: str = Query("technical", description="方案类型：technical/business"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """根据商机自动生成技术/商务方案"""
    service = SalesAIAssistantService(db)
    return service.generate_proposal(opportunity_id, proposal_type)


# ========== 3. 竞品分析 ==========


@router.get("/competitor-analysis", summary="竞品分析")
def analyze_competitor(
    competitor_name: str = Query(..., description="竞品公司名称"),
    product_category: Optional[str] = Query(None, description="产品类型"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """竞品分析"""
    service = SalesAIAssistantService(db)
    return service.analyze_competitor(competitor_name, product_category)


# ========== 4. 谈判建议 ==========


@router.get("/opportunities/{opportunity_id}/negotiation-advice", summary="谈判建议")
def get_negotiation_advice(
    opportunity_id: int = Path(..., description="商机ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """根据客户特征给出谈判建议"""
    service = SalesAIAssistantService(db)
    return service.get_negotiation_advice(opportunity_id)


# ========== 5. 流失风险预警 ==========


@router.get("/customers/{customer_id}/churn-risk", summary="流失风险预测")
def predict_churn_risk(
    customer_id: int = Path(..., description="客户ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """AI预测客户流失风险"""
    service = SalesAIAssistantService(db)
    return service.predict_churn_risk(customer_id)


@router.get("/churn-risk-list", summary="高风险客户列表")
def get_churn_risk_list(
    risk_level: Optional[str] = Query(None, description="风险等级：HIGH/MEDIUM/LOW"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取流失风险客户列表"""
    service = SalesAIAssistantService(db)
    return service.get_churn_risk_list(risk_level)
