# -*- coding: utf-8 -*-
"""
销售预测仪表盘 API
为领导层提供公司整体销售计划完成情况的 AI 预测
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.services.sales.forecast_dashboard_service import SalesForecastDashboardService
from app.services.sales_forecast_service import SalesForecastService

router = APIRouter()


# ========== 1. 公司整体销售预测 ==========


@router.get("/forecast/company-overview", summary="公司整体销售预测")
def get_company_forecast(
    period: str = Query("quarterly", description="周期：monthly/quarterly/yearly"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    公司整体销售计划完成情况预测

    基于：
    - 当前已完成业绩
    - 漏斗中各阶段商机金额 × 赢单率
    - 历史同期数据
    - 季节性因素

    返回：
    - 预测完成率
    - 置信区间
    - 风险等级
    - 关键驱动因素
    """
    service = SalesForecastService(db)
    forecast = service.get_company_forecast(period=period)
    return forecast


# Legacy mock data endpoint for reference
@router.get("/forecast/company-overview-legacy", summary="公司整体销售预测 (旧版)")
def get_company_forecast_legacy(
    period: str = Query("quarterly", description="周期：monthly/quarterly/yearly"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    【旧版】模拟数据，仅供参考
    """
    forecast = {
        "period": "2026-Q1",
        "period_type": "quarterly",
        "generated_at": date.today().isoformat(),
        # 目标 vs 实际 vs 预测
        "targets": {
            "quarterly_target": 50000000,
            "actual_revenue": 28500000,
            "completion_rate": 57.0,
            "days_elapsed": 60,
            "total_days": 90,
            "time_progress": 66.7,
        },
        # AI 预测结果
        "prediction": {
            "predicted_revenue": 52800000,
            "predicted_completion_rate": 105.6,
            "confidence_level": 85,
            "confidence_interval": {
                "optimistic": 58000000,
                "pessimistic": 47500000,
            },
            "risk_level": "LOW",
            "trend": "positive",
        },
        # 预测依据 - 漏斗分析
        "funnel_contribution": {
            "stage1": {
                "count": 45,
                "total_amount": 18000000,
                "weighted_amount": 4500000,
                "win_rate": 25,
            },
            "stage2": {
                "count": 28,
                "total_amount": 12000000,
                "weighted_amount": 6000000,
                "win_rate": 50,
            },
            "stage3": {
                "count": 15,
                "total_amount": 8000000,
                "weighted_amount": 5200000,
                "win_rate": 65,
            },
            "stage4": {
                "count": 10,
                "total_amount": 5000000,
                "weighted_amount": 3750000,
                "win_rate": 75,
            },
            "stage5": {
                "count": 5,
                "total_amount": 2500000,
                "weighted_amount": 2125000,
                "win_rate": 85,
            },
            "total_weighted": 21575000,
        },
        # 预测分解
        "forecast_breakdown": {
            "committed": {  # 已签约
                "amount": 28500000,
                "percentage": 54,
                "confidence": 100,
            },
            "best_case": {  # 高概率商机
                "amount": 15200000,
                "percentage": 29,
                "confidence": 85,
            },
            "pipeline": {  # 漏斗中
                "amount": 9100000,
                "percentage": 17,
                "confidence": 60,
            },
        },
        # 关键驱动因素
        "key_drivers": [
            {
                "factor": "Q1 淡季影响",
                "impact": -5,
                "description": "春节假期导致 2 月有效工作日减少",
            },
            {
                "factor": "大客户签约",
                "impact": 15,
                "description": "宁德时代 350 万项目已签约",
            },
            {
                "factor": "新产品上市",
                "impact": 8,
                "description": "视觉检测设备带动新增需求",
            },
        ],
        # 风险预警
        "risks": [
            {
                "risk": "STAGE4 转化率偏低",
                "impact": -3000000,
                "probability": "MEDIUM",
                "mitigation": "加强价格谈判支持",
            },
            {
                "risk": "关键销售离职风险",
                "impact": -2000000,
                "probability": "LOW",
                "mitigation": "做好客户交接预案",
            },
        ],
        # 建议行动
        "recommended_actions": [
            {
                "priority": 1,
                "action": "重点跟进 STAGE4 的 10 个商机",
                "impact": 3750000,
                "deadline": "3 月 20 日前",
            },
            {
                "priority": 2,
                "action": "加速 STAGE2→STAGE3 转化",
                "impact": 2000000,
                "deadline": "3 月 15 日前",
            },
            {
                "priority": 3,
                "action": "启动月底冲刺激励",
                "impact": 1500000,
                "deadline": "3 月 25 日前",
            },
        ],
        # 历史对比
        "historical_comparison": {
            "last_quarter": {
                "period": "2025-Q4",
                "target": 48000000,
                "actual": 51200000,
                "completion_rate": 106.7,
            },
            "last_year_same_period": {
                "period": "2025-Q1",
                "target": 42000000,
                "actual": 44800000,
                "completion_rate": 106.7,
            },
            "average_q1_completion": 102.5,
        },
    }

    return forecast


# ========== 2. 销售团队预测 ==========


@router.get("/forecast/team-breakdown", summary="团队销售预测分解")
def get_team_forecast(
    period: str = Query("quarterly", description="周期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    各销售团队/大区预测分解

    显示：
    - 各团队完成率
    - 预测排名
    - 风险团队标识
    """

    return SalesForecastDashboardService(db).get_team_breakdown(period=period)


# ========== 3. 个人销售预测 ==========


@router.get("/forecast/sales-rep-breakdown", summary="个人销售预测分解")
def get_sales_rep_forecast(
    team_id: Optional[int] = Query(None, description="团队 ID"),
    period: str = Query("quarterly", description="周期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    各销售人员预测分解

    显示：
    - 个人完成率
    - 预测排名
    - 关键商机
    """

    return SalesForecastDashboardService(db).get_sales_rep_breakdown(
        team_id=team_id,
        period=period,
    )


# ========== 4. 预测准确性追踪 ==========


@router.get("/forecast/accuracy-tracking", summary="预测准确性追踪")
def get_forecast_accuracy(
    months: int = Query(6, description="追踪月数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    追踪历史预测的准确性

    用于：
    - 验证预测模型可靠性
    - 持续改进预测算法
    """

    return SalesForecastDashboardService(db).get_accuracy_tracking(months=months)


# ========== 5. 领导驾驶舱汇总 ==========


@router.get("/forecast/executive-dashboard", summary="领导驾驶舱")
def get_executive_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    领导驾驶舱 - 一页纸看全公司销售情况

    专为 CEO/销售副总设计
    """

    return SalesForecastDashboardService(db).get_executive_dashboard()
