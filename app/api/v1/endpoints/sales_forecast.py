# -*- coding: utf-8 -*-
"""
销售预测仪表盘 API
为领导层提供公司整体销售计划完成情况的 AI 预测
"""

from typing import Any, Optional, List, Dict
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User

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
    
    # 模拟预测数据
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
            "stage1": {"count": 45, "total_amount": 18000000, "weighted_amount": 4500000, "win_rate": 25},
            "stage2": {"count": 28, "total_amount": 12000000, "weighted_amount": 6000000, "win_rate": 50},
            "stage3": {"count": 15, "total_amount": 8000000, "weighted_amount": 5200000, "win_rate": 65},
            "stage4": {"count": 10, "total_amount": 5000000, "weighted_amount": 3750000, "win_rate": 75},
            "stage5": {"count": 5, "total_amount": 2500000, "weighted_amount": 2125000, "win_rate": 85},
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
    
    teams = [
        {
            "team_id": 1,
            "team_name": "华南大区",
            "manager": "王五",
            "members_count": 8,
            "quarterly_target": 18000000,
            "actual_revenue": 10800000,
            "completion_rate": 60.0,
            "predicted_revenue": 19500000,
            "predicted_completion": 108.3,
            "confidence": 88,
            "risk_level": "LOW",
            "trend": "up",
            "rank": 1,
            "rank_change": 0,
            "key_opportunities": [
                {"name": "宁德时代 FCT", "amount": 3500000, "stage": "STAGE4"},
                {"name": "亿纬锂能 EOL", "amount": 2800000, "stage": "STAGE3"},
            ],
        },
        {
            "team_id": 2,
            "team_name": "华东大区",
            "manager": "李四",
            "members_count": 7,
            "quarterly_target": 16000000,
            "actual_revenue": 9200000,
            "completion_rate": 57.5,
            "predicted_revenue": 17200000,
            "predicted_completion": 107.5,
            "confidence": 82,
            "risk_level": "MEDIUM",
            "trend": "stable",
            "rank": 2,
            "rank_change": 0,
            "key_opportunities": [
                {"name": "中创新航 ICT", "amount": 2500000, "stage": "STAGE3"},
            ],
        },
        {
            "team_id": 3,
            "team_name": "华北大区",
            "manager": "赵六",
            "members_count": 6,
            "quarterly_target": 16000000,
            "actual_revenue": 8500000,
            "completion_rate": 53.1,
            "predicted_revenue": 15800000,
            "predicted_completion": 98.8,
            "confidence": 75,
            "risk_level": "HIGH",
            "trend": "down",
            "rank": 3,
            "rank_change": -1,
            "key_opportunities": [
                {"name": "欣旺达 FCT", "amount": 3200000, "stage": "STAGE2"},
            ],
            "alerts": [
                "完成率落后时间进度 13.6%",
                "需要加速 STAGE2→STAGE3 转化",
            ],
        },
    ]
    
    return {
        "period": "2026-Q1",
        "total_teams": len(teams),
        "teams_on_track": len([t for t in teams if t["predicted_completion"] >= 100]),
        "teams_at_risk": len([t for t in teams if t["risk_level"] == "HIGH"]),
        "teams": sorted(teams, key=lambda x: x["predicted_completion"], reverse=True),
    }


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
    
    sales_reps = [
        {
            "sales_id": 101,
            "sales_name": "张三",
            "team": "华南大区",
            "quarterly_target": 10000000,
            "actual_revenue": 6500000,
            "completion_rate": 65.0,
            "predicted_revenue": 11200000,
            "predicted_completion": 112.0,
            "confidence": 90,
            "rank": 1,
            "pipeline_value": 8500000,
            "weighted_pipeline": 5200000,
            "key_deals": [
                {"customer": "宁德时代", "amount": 3500000, "probability": 85},
                {"customer": "比亚迪", "amount": 2800000, "probability": 70},
            ],
            "performance_trend": "excellent",
        },
        {
            "sales_id": 102,
            "sales_name": "李四",
            "team": "华东大区",
            "quarterly_target": 10000000,
            "actual_revenue": 5800000,
            "completion_rate": 58.0,
            "predicted_revenue": 10500000,
            "predicted_completion": 105.0,
            "confidence": 82,
            "rank": 2,
            "pipeline_value": 7200000,
            "weighted_pipeline": 4500000,
            "key_deals": [
                {"customer": "中创新航", "amount": 2500000, "probability": 65},
            ],
            "performance_trend": "good",
        },
        {
            "sales_id": 103,
            "sales_name": "王五",
            "team": "华南大区",
            "quarterly_target": 10000000,
            "actual_revenue": 5200000,
            "completion_rate": 52.0,
            "predicted_revenue": 9200000,
            "predicted_completion": 92.0,
            "confidence": 75,
            "rank": 3,
            "pipeline_value": 6500000,
            "weighted_pipeline": 3800000,
            "key_deals": [
                {"customer": "亿纬锂能", "amount": 2200000, "probability": 60},
            ],
            "performance_trend": "at_risk",
            "alerts": ["需要加速商机推进"],
        },
    ]
    
    if team_id:
        sales_reps = [s for s in sales_reps if s["team_id"] == team_id]
    
    return {
        "period": "2026-Q1",
        "total_reps": len(sales_reps),
        "on_track_count": len([s for s in sales_reps if s["predicted_completion"] >= 100]),
        "at_risk_count": len([s for s in sales_reps if s["predicted_completion"] < 100]),
        "sales_reps": sorted(sales_reps, key=lambda x: x["predicted_completion"], reverse=True),
    }


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
    
    accuracy_history = [
        {
            "period": "2025-09",
            "predicted": 42000000,
            "actual": 41500000,
            "variance": -1.2,
            "accuracy": 98.8,
        },
        {
            "period": "2025-10",
            "predicted": 45000000,
            "actual": 46200000,
            "variance": 2.7,
            "accuracy": 97.3,
        },
        {
            "period": "2025-11",
            "predicted": 48000000,
            "actual": 47500000,
            "variance": -1.0,
            "accuracy": 99.0,
        },
        {
            "period": "2025-12",
            "predicted": 51000000,
            "actual": 51200000,
            "variance": 0.4,
            "accuracy": 99.6,
        },
        {
            "period": "2026-01",
            "predicted": 38000000,
            "actual": 39200000,
            "variance": 3.2,
            "accuracy": 96.8,
        },
        {
            "period": "2026-02",
            "predicted": 42000000,
            "actual": 44500000,
            "variance": 6.0,
            "accuracy": 94.0,
        },
    ]
    
    avg_accuracy = sum(h["accuracy"] for h in accuracy_history) / len(accuracy_history)
    
    return {
        "tracking_period": f"最近{months}个月",
        "average_accuracy": round(avg_accuracy, 1),
        "trend": "stable",
        "confidence_assessment": "高" if avg_accuracy > 95 else "中" if avg_accuracy > 90 else "低",
        "history": accuracy_history,
        "model_insights": [
            "预测模型平均准确率 97.6%",
            "最大偏差 6.0%（2026-02，春节因素影响）",
            "建议：季节性因素权重可调整",
        ],
    }


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
    
    return {
        "dashboard_date": date.today().isoformat(),
        "period": "2026-Q1",
        
        # 核心指标
        "kpi_summary": {
            "revenue": {
                "target": 50000000,
                "actual": 28500000,
                "predicted": 52800000,
                "completion_rate": 57.0,
                "predicted_completion": 105.6,
                "status": "on_track",
            },
            "new_customers": {
                "target": 30,
                "actual": 18,
                "predicted": 32,
                "completion_rate": 60.0,
                "predicted_completion": 106.7,
                "status": "on_track",
            },
            "avg_deal_size": {
                "target": 1500000,
                "actual": 1580000,
                "trend": "up",
                "change_percentage": 5.3,
            },
        },
        
        # 红绿灯预警
        "traffic_lights": {
            "overall": "GREEN",
            "by_team": [
                {"team": "华南大区", "light": "GREEN", "completion": 108.3},
                {"team": "华东大区", "light": "GREEN", "completion": 107.5},
                {"team": "华北大区", "light": "RED", "completion": 98.8},
            ],
        },
        
        # 关键风险
        "top_risks": [
            {
                "risk": "华北大区完成率落后",
                "impact": "影响整体 2-3%",
                "action": "已安排区域经理专项跟进",
            },
            {
                "risk": "STAGE4 转化率偏低",
                "impact": "可能损失 300 万",
                "action": "加强价格谈判支持",
            },
        ],
        
        # 关键机会
        "top_opportunities": [
            {"customer": "欣旺达", "amount": 3200000, "probability": 70, "expected_close": "3 月 20 日"},
            {"customer": "中创新航", "amount": 2500000, "probability": 65, "expected_close": "3 月 15 日"},
        ],
        
        # 需要领导关注的事项
        "executive_actions": [
            {
                "priority": 1,
                "action": "拜访欣旺达高层",
                "reason": "320 万项目，决策阶段",
                "deadline": "3 月 10 日前",
            },
            {
                "priority": 2,
                "action": "审批华北大区特殊折扣政策",
                "reason": "帮助追赶进度",
                "deadline": "3 月 5 日前",
            },
        ],
        
        # 预测趋势图数据
        "trend_data": [
            {"month": "1 月", "target": 15000000, "actual": 13500000, "predicted": 14200000},
            {"month": "2 月", "target": 15000000, "actual": 15000000, "predicted": 15800000},
            {"month": "3 月", "target": 20000000, "actual": 0, "predicted": 22800000},
        ],
    }
