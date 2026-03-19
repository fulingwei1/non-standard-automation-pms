# -*- coding: utf-8 -*-
"""
销售预测增强版 API
考虑多维度因素，提高预测准确性，倒逼数据填写。
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.services.sales.forecast_enhancement_service import SalesForecastEnhancementService

router = APIRouter()


# ========== 1. 增强版预测模型 ==========


@router.get("/forecast/enhanced-prediction", summary="增强版销售预测")
def get_enhanced_prediction(
    period: str = Query("quarterly", description="周期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    增强版销售预测模型

    考虑因素：
    1. 基础漏斗数据（金额 × 赢单率）
    2. 数据质量系数（填写完整度）
    3. 销售动作完成度（拜访/电话/会议）
    4. 商机健康度（跟进及时性、决策链覆盖）
    5. 历史预测准确性
    6. 季节性因素
    7. 竞争态势
    8. 客户质量评分

    返回：
    - 基础预测（仅漏斗）
    - 数据质量调整
    - 最终预测（调整后）
    - 各因素影响分析
    """

    return SalesForecastEnhancementService(db).get_enhanced_prediction(period=period)


# ========== 2. 数据质量评分 ==========


@router.get("/forecast/data-quality-score", summary="数据质量评分")
def get_data_quality_score(
    sales_id: Optional[int] = Query(None, description="销售 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售数据质量评分

    用于倒逼销售认真填写：
    - 评分公开排名
    - 影响预测准确性
    - 与绩效挂钩
    """

    return SalesForecastEnhancementService(db).get_data_quality_score(sales_id=sales_id)


# ========== 3. 销售动作追踪 ==========


@router.get("/forecast/activity-tracking", summary="销售动作追踪")
def get_activity_tracking(
    sales_id: Optional[int] = Query(None, description="销售 ID"),
    period: str = Query("monthly", description="周期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售动作完成度追踪

    追踪：
    - 拜访次数（打卡）
    - 电话/微信沟通
    - 会议/演示
    - 方案/报价提交
    - 商机阶段推进

    关联分析：
    - 动作频率 vs 赢单率
    - 响应速度 vs 转化率
    """

    return SalesForecastEnhancementService(db).get_activity_tracking(
        sales_id=sales_id,
        period=period,
    )


# ========== 4. 预测准确性对比 ==========


@router.get("/forecast/accuracy-comparison", summary="预测准确性对比")
def get_accuracy_comparison(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    对比不同数据质量下的预测准确性

    用于证明：认真填写数据 = 更准确的预测 = 更好的决策
    """

    return SalesForecastEnhancementService(db).get_accuracy_comparison()
