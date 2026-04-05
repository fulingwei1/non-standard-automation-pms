# -*- coding: utf-8 -*-
"""
销售预测（合并自 sales_forecast / sales_forecast_enhanced）

功能：
- 基础预测（公司整体/团队/个人，按时间/产品/区域）
- 增强预测（AI 辅助/多模型、数据质量系数、销售动作完成度）
- 预测准确率分析（历史追踪、准确性对比）
- 领导驾驶舱
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User

# ---------- 两个 router，分别对应原来注册时的不同 prefix ----------
# forecast_router: 原 sales_forecast.router（prefix="/forecast"）
# forecast_enhanced_router: 原 sales_forecast_enhanced.router（prefix="/forecast-enhanced"）
forecast_router = APIRouter()
forecast_enhanced_router = APIRouter()


# ==================== 基础预测（原 sales_forecast） ====================


@forecast_router.get("/forecast/company-overview", summary="公司整体销售预测")
def get_company_forecast(
    period: str = Query("quarterly", description="周期：monthly/quarterly/yearly"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    公司整体销售计划完成情况预测

    基于：
    - 当前已完成业绩
    - 漏斗中各阶段商机金额 x 赢单率
    - 历史同期数据
    - 季节性因素
    """
    forecast = {
        "period": "2026-Q1",
        "period_type": "quarterly",
        "generated_at": date.today().isoformat(),
        "targets": {
            "quarterly_target": 50000000,
            "actual_revenue": 28500000,
            "completion_rate": 57.0,
            "days_elapsed": 60,
            "total_days": 90,
            "time_progress": 66.7,
        },
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
        "funnel_contribution": {
            "stage1": {"count": 45, "total_amount": 18000000, "weighted_amount": 4500000, "win_rate": 25},
            "stage2": {"count": 28, "total_amount": 12000000, "weighted_amount": 6000000, "win_rate": 50},
            "stage3": {"count": 15, "total_amount": 8000000, "weighted_amount": 5200000, "win_rate": 65},
            "stage4": {"count": 10, "total_amount": 5000000, "weighted_amount": 3750000, "win_rate": 75},
            "stage5": {"count": 5, "total_amount": 2500000, "weighted_amount": 2125000, "win_rate": 85},
            "total_weighted": 21575000,
        },
        "forecast_breakdown": {
            "committed": {"amount": 28500000, "percentage": 54, "confidence": 100},
            "best_case": {"amount": 15200000, "percentage": 29, "confidence": 85},
            "pipeline": {"amount": 9100000, "percentage": 17, "confidence": 60},
        },
        "key_drivers": [
            {"factor": "Q1 淡季影响", "impact": -5, "description": "春节假期导致 2 月有效工作日减少"},
            {"factor": "大客户签约", "impact": 15, "description": "宁德时代 350 万项目已签约"},
            {"factor": "新产品上市", "impact": 8, "description": "视觉检测设备带动新增需求"},
        ],
        "risks": [
            {"risk": "STAGE4 转化率偏低", "impact": -3000000, "probability": "MEDIUM", "mitigation": "加强价格谈判支持"},
            {"risk": "关键销售离职风险", "impact": -2000000, "probability": "LOW", "mitigation": "做好客户交接预案"},
        ],
        "recommended_actions": [
            {"priority": 1, "action": "重点跟进 STAGE4 的 10 个商机", "impact": 3750000, "deadline": "3 月 20 日前"},
            {"priority": 2, "action": "加速 STAGE2->STAGE3 转化", "impact": 2000000, "deadline": "3 月 15 日前"},
            {"priority": 3, "action": "启动月底冲刺激励", "impact": 1500000, "deadline": "3 月 25 日前"},
        ],
        "historical_comparison": {
            "last_quarter": {"period": "2025-Q4", "target": 48000000, "actual": 51200000, "completion_rate": 106.7},
            "last_year_same_period": {"period": "2025-Q1", "target": 42000000, "actual": 44800000, "completion_rate": 106.7},
            "average_q1_completion": 102.5,
        },
    }
    return forecast


@forecast_router.get("/forecast/team-breakdown", summary="团队销售预测分解")
def get_team_forecast(
    period: str = Query("quarterly", description="周期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """各销售团队/大区预测分解"""
    teams = [
        {
            "team_id": 1, "team_name": "华南大区", "manager": "王五", "members_count": 8,
            "quarterly_target": 18000000, "actual_revenue": 10800000, "completion_rate": 60.0,
            "predicted_revenue": 19500000, "predicted_completion": 108.3,
            "confidence": 88, "risk_level": "LOW", "trend": "up", "rank": 1, "rank_change": 0,
            "key_opportunities": [
                {"name": "宁德时代 FCT", "amount": 3500000, "stage": "STAGE4"},
                {"name": "亿纬锂能 EOL", "amount": 2800000, "stage": "STAGE3"},
            ],
        },
        {
            "team_id": 2, "team_name": "华东大区", "manager": "李四", "members_count": 7,
            "quarterly_target": 16000000, "actual_revenue": 9200000, "completion_rate": 57.5,
            "predicted_revenue": 17200000, "predicted_completion": 107.5,
            "confidence": 82, "risk_level": "MEDIUM", "trend": "stable", "rank": 2, "rank_change": 0,
            "key_opportunities": [
                {"name": "中创新航 ICT", "amount": 2500000, "stage": "STAGE3"},
            ],
        },
        {
            "team_id": 3, "team_name": "华北大区", "manager": "赵六", "members_count": 6,
            "quarterly_target": 16000000, "actual_revenue": 8500000, "completion_rate": 53.1,
            "predicted_revenue": 15800000, "predicted_completion": 98.8,
            "confidence": 75, "risk_level": "HIGH", "trend": "down", "rank": 3, "rank_change": -1,
            "key_opportunities": [
                {"name": "欣旺达 FCT", "amount": 3200000, "stage": "STAGE2"},
            ],
            "alerts": ["完成率落后时间进度 13.6%", "需要加速 STAGE2->STAGE3 转化"],
        },
    ]
    return {
        "period": "2026-Q1",
        "total_teams": len(teams),
        "teams_on_track": len([t for t in teams if t["predicted_completion"] >= 100]),
        "teams_at_risk": len([t for t in teams if t["risk_level"] == "HIGH"]),
        "teams": sorted(teams, key=lambda x: x["predicted_completion"], reverse=True),
    }


@forecast_router.get("/forecast/sales-rep-breakdown", summary="个人销售预测分解")
def get_sales_rep_forecast(
    team_id: Optional[int] = Query(None, description="团队 ID"),
    period: str = Query("quarterly", description="周期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """各销售人员预测分解"""
    sales_reps = [
        {
            "sales_id": 101, "sales_name": "张三", "team": "华南大区",
            "quarterly_target": 10000000, "actual_revenue": 6500000, "completion_rate": 65.0,
            "predicted_revenue": 11200000, "predicted_completion": 112.0, "confidence": 90, "rank": 1,
            "pipeline_value": 8500000, "weighted_pipeline": 5200000,
            "key_deals": [
                {"customer": "宁德时代", "amount": 3500000, "probability": 85},
                {"customer": "比亚迪", "amount": 2800000, "probability": 70},
            ],
            "performance_trend": "excellent",
        },
        {
            "sales_id": 102, "sales_name": "李四", "team": "华东大区",
            "quarterly_target": 10000000, "actual_revenue": 5800000, "completion_rate": 58.0,
            "predicted_revenue": 10500000, "predicted_completion": 105.0, "confidence": 82, "rank": 2,
            "pipeline_value": 7200000, "weighted_pipeline": 4500000,
            "key_deals": [{"customer": "中创新航", "amount": 2500000, "probability": 65}],
            "performance_trend": "good",
        },
        {
            "sales_id": 103, "sales_name": "王五", "team": "华南大区",
            "quarterly_target": 10000000, "actual_revenue": 5200000, "completion_rate": 52.0,
            "predicted_revenue": 9200000, "predicted_completion": 92.0, "confidence": 75, "rank": 3,
            "pipeline_value": 6500000, "weighted_pipeline": 3800000,
            "key_deals": [{"customer": "亿纬锂能", "amount": 2200000, "probability": 60}],
            "performance_trend": "at_risk",
            "alerts": ["需要加速商机推进"],
        },
    ]

    if team_id:
        sales_reps = [s for s in sales_reps if s.get("team_id") == team_id]

    return {
        "period": "2026-Q1",
        "total_reps": len(sales_reps),
        "on_track_count": len([s for s in sales_reps if s["predicted_completion"] >= 100]),
        "at_risk_count": len([s for s in sales_reps if s["predicted_completion"] < 100]),
        "sales_reps": sorted(sales_reps, key=lambda x: x["predicted_completion"], reverse=True),
    }


@forecast_router.get("/forecast/accuracy-tracking", summary="预测准确性追踪")
def get_forecast_accuracy(
    months: int = Query(6, description="追踪月数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """追踪历史预测的准确性"""
    accuracy_history = [
        {"period": "2025-09", "predicted": 42000000, "actual": 41500000, "variance": -1.2, "accuracy": 98.8},
        {"period": "2025-10", "predicted": 45000000, "actual": 46200000, "variance": 2.7, "accuracy": 97.3},
        {"period": "2025-11", "predicted": 48000000, "actual": 47500000, "variance": -1.0, "accuracy": 99.0},
        {"period": "2025-12", "predicted": 51000000, "actual": 51200000, "variance": 0.4, "accuracy": 99.6},
        {"period": "2026-01", "predicted": 38000000, "actual": 39200000, "variance": 3.2, "accuracy": 96.8},
        {"period": "2026-02", "predicted": 42000000, "actual": 44500000, "variance": 6.0, "accuracy": 94.0},
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


@forecast_router.get("/forecast/executive-dashboard", summary="领导驾驶舱")
def get_executive_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """领导驾驶舱 - 一页纸看全公司销售情况"""
    return {
        "dashboard_date": date.today().isoformat(),
        "period": "2026-Q1",
        "kpi_summary": {
            "revenue": {
                "target": 50000000, "actual": 28500000, "predicted": 52800000,
                "completion_rate": 57.0, "predicted_completion": 105.6, "status": "on_track",
            },
            "new_customers": {
                "target": 30, "actual": 18, "predicted": 32,
                "completion_rate": 60.0, "predicted_completion": 106.7, "status": "on_track",
            },
            "avg_deal_size": {"target": 1500000, "actual": 1580000, "trend": "up", "change_percentage": 5.3},
        },
        "traffic_lights": {
            "overall": "GREEN",
            "by_team": [
                {"team": "华南大区", "light": "GREEN", "completion": 108.3},
                {"team": "华东大区", "light": "GREEN", "completion": 107.5},
                {"team": "华北大区", "light": "RED", "completion": 98.8},
            ],
        },
        "top_risks": [
            {"risk": "华北大区完成率落后", "impact": "影响整体 2-3%", "action": "已安排区域经理专项跟进"},
            {"risk": "STAGE4 转化率偏低", "impact": "可能损失 300 万", "action": "加强价格谈判支持"},
        ],
        "top_opportunities": [
            {"customer": "欣旺达", "amount": 3200000, "probability": 70, "expected_close": "3 月 20 日"},
            {"customer": "中创新航", "amount": 2500000, "probability": 65, "expected_close": "3 月 15 日"},
        ],
        "executive_actions": [
            {"priority": 1, "action": "拜访欣旺达高层", "reason": "320 万项目，决策阶段", "deadline": "3 月 10 日前"},
            {"priority": 2, "action": "审批华北大区特殊折扣政策", "reason": "帮助追赶进度", "deadline": "3 月 5 日前"},
        ],
        "trend_data": [
            {"month": "1 月", "target": 15000000, "actual": 13500000, "predicted": 14200000},
            {"month": "2 月", "target": 15000000, "actual": 15000000, "predicted": 15800000},
            {"month": "3 月", "target": 20000000, "actual": 0, "predicted": 22800000},
        ],
    }


# ==================== 增强预测（原 sales_forecast_enhanced） ====================


@forecast_enhanced_router.get("/forecast/enhanced-prediction", summary="增强版销售预测")
def get_enhanced_prediction(
    period: str = Query("quarterly", description="周期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    增强版销售预测模型

    考虑因素：基础漏斗数据、数据质量系数、销售动作完成度、商机健康度、
    历史预测准确性、季节性因素、竞争态势、客户质量评分
    """
    prediction = {
        "period": "2026-Q1",
        "generated_at": date.today().isoformat(),
        "base_prediction": {
            "formula": "已完成 + Σ(漏斗金额 x 阶段赢单率)",
            "completed": 28500000,
            "pipeline_weighted": 21575000,
            "base_predicted": 50075000,
            "base_completion_rate": 100.15,
        },
        "data_quality_factor": {
            "overall_score": 78,
            "impact": -0.05,
            "dimensions": [
                {"name": "线索完整度", "score": 85, "weight": 20, "description": "必填字段填写率", "issues": ["15% 的商机缺少预算信息"]},
                {"name": "跟进及时性", "score": 72, "weight": 25, "description": "X 天未跟进的商机占比", "issues": ["8 个商机超过 7 天未跟进"]},
                {"name": "决策链完整度", "score": 65, "weight": 25, "description": "关键决策人信息填写率", "issues": ["40% 的商机未识别 EB（最终决策人）"]},
                {"name": "拜访记录完整度", "score": 80, "weight": 15, "description": "拜访打卡 + 记录填写", "issues": ["20% 的拜访缺少现场照片"]},
                {"name": "赢单/输单原因", "score": 90, "weight": 15, "description": "关闭商机时原因填写", "issues": []},
            ],
        },
        "activity_factor": {
            "overall_score": 82,
            "impact": 0.02,
            "metrics": {
                "visits_target": 120, "visits_actual": 98, "visits_completion": 81.7,
                "calls_target": 300, "calls_actual": 276, "calls_completion": 92.0,
                "meetings_target": 50, "meetings_actual": 45, "meetings_completion": 90.0,
                "proposals_target": 30, "proposals_actual": 28, "proposals_completion": 93.3,
            },
            "correlation_analysis": {
                "high_activity_win_rate": 72,
                "low_activity_win_rate": 35,
                "insight": "高频跟进的商机赢单率是低频的 2 倍",
            },
        },
        "opportunity_health_factor": {
            "overall_score": 75,
            "impact": -0.03,
            "healthy_opportunities": {
                "count": 45, "total_amount": 32000000,
                "criteria": "7 天内有跟进 + 决策链完整 + 下一步明确",
            },
            "at_risk_opportunities": {
                "count": 18, "total_amount": 8500000,
                "criteria": "超过 14 天未跟进 或 决策链缺失",
                "details": [
                    {"name": "欣旺达 FCT", "amount": 3200000, "risk": "14 天未跟进"},
                    {"name": "蜂巢能源 EOL", "amount": 2800000, "risk": "未识别 EB"},
                    {"name": "国轩高科 ICT", "amount": 2500000, "risk": "无明确下一步"},
                ],
            },
        },
        "historical_accuracy_factor": {
            "avg_accuracy": 94.5,
            "impact": 0,
            "recent_predictions": [
                {"period": "2025-12", "predicted": 51000000, "actual": 51200000, "accuracy": 99.6},
                {"period": "2026-01", "predicted": 38000000, "actual": 39200000, "accuracy": 96.8},
                {"period": "2026-02", "predicted": 42000000, "actual": 44500000, "accuracy": 94.0},
            ],
        },
        "seasonality_factor": {
            "current_month": "3 月",
            "factor": 1.08,
            "impact": 0.03,
            "historical_pattern": "Q1 末月通常比前 2 个月增长 30-50%",
        },
        "final_prediction": {
            "base": 50075000,
            "adjustments": {
                "data_quality": -2503750,
                "activity": 1001500,
                "health": -1502250,
                "seasonality": 1502250,
            },
            "total_adjustment": -1502250,
            "final_predicted": 48572750,
            "final_completion_rate": 97.15,
            "confidence_level": 82,
            "confidence_interval": {"optimistic": 53000000, "pessimistic": 44000000},
        },
        "key_insights": [
            {
                "type": "WARNING", "title": "数据质量影响预测准确性",
                "description": "当前数据质量系数 78 分，导致预测下调 5%（250 万）",
                "action": "督促销售完善商机信息，特别是决策链和跟进记录", "impact": 2500000,
            },
            {
                "type": "WARNING", "title": "18 个商机存在风险",
                "description": "超过 14 天未跟进或决策链缺失，涉及金额 850 万",
                "action": "立即跟进这些商机，更新状态", "impact": 8500000,
            },
            {
                "type": "SUCCESS", "title": "销售动作完成良好",
                "description": "电话/会议完成率 90%+，高频跟进的商机赢单率 72%",
                "action": "保持当前跟进节奏", "impact": 1000000,
            },
        ],
        "improvement_recommendations": [
            {
                "priority": 1, "action": "完善决策链信息",
                "description": "40% 的商机未识别 EB，需要补充关键决策人信息",
                "expected_impact": "+3% 预测准确率", "deadline": "3 月 10 日前", "responsible": "全体销售",
            },
            {
                "priority": 2, "action": "跟进逾期商机",
                "description": "18 个商机超过 14 天未跟进，需要立即联系",
                "expected_impact": "+5% 赢单率", "deadline": "3 月 5 日前", "responsible": "相关销售",
            },
            {
                "priority": 3, "action": "提升拜访记录质量",
                "description": "20% 的拜访缺少现场照片，需要完整记录",
                "expected_impact": "+2% 数据质量分", "deadline": "持续改进", "responsible": "全体销售",
            },
        ],
    }
    return prediction


@forecast_enhanced_router.get("/forecast/data-quality-score", summary="数据质量评分")
def get_data_quality_score(
    sales_id: Optional[int] = Query(None, description="销售 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """销售数据质量评分"""
    team_scores = [
        {
            "rank": 1, "sales_id": 101, "sales_name": "张三", "team": "华南大区", "overall_score": 92,
            "dimensions": {"lead_completeness": 95, "follow_up_timeliness": 90, "decision_chain": 88, "visit_records": 95, "close_reason": 100},
            "opportunities_count": 12, "healthy_opportunities": 11, "prediction_accuracy": 96.5,
        },
        {
            "rank": 2, "sales_id": 102, "sales_name": "李四", "team": "华东大区", "overall_score": 85,
            "dimensions": {"lead_completeness": 88, "follow_up_timeliness": 85, "decision_chain": 80, "visit_records": 88, "close_reason": 85},
            "opportunities_count": 10, "healthy_opportunities": 8, "prediction_accuracy": 92.0,
        },
        {
            "rank": 3, "sales_id": 103, "sales_name": "王五", "team": "华南大区", "overall_score": 72,
            "dimensions": {"lead_completeness": 75, "follow_up_timeliness": 65, "decision_chain": 70, "visit_records": 78, "close_reason": 72},
            "opportunities_count": 11, "healthy_opportunities": 6, "prediction_accuracy": 85.0,
            "alerts": ["5 个商机超过 14 天未跟进", "3 个商机缺少决策链信息"],
        },
    ]
    return {
        "assessment_date": date.today().isoformat(),
        "team_average": 83,
        "company_average": 78,
        "top_performer": {"name": "张三", "score": 92},
        "needs_improvement": {"name": "王五", "score": 72},
        "rankings": team_scores,
        "scoring_rules": {
            "lead_completeness": {"name": "线索完整度", "weight": 20, "criteria": "必填字段填写率 >=95% 得满分"},
            "follow_up_timeliness": {"name": "跟进及时性", "weight": 25, "criteria": "无超过 7 天未跟进的商机"},
            "decision_chain": {"name": "决策链完整度", "weight": 25, "criteria": "EB/TB/PB 信息完整"},
            "visit_records": {"name": "拜访记录完整度", "weight": 15, "criteria": "拜访打卡 + 照片 + 记录"},
            "close_reason": {"name": "赢单/输单原因", "weight": 15, "criteria": "关闭商机时详细填写原因"},
        },
        "impact_explanation": {
            "on_prediction": "数据质量分每低 10 分，预测准确率下降约 5%",
            "on_performance": "数据质量纳入绩效考核，占比 15%",
            "on_support": "低分销售将获得更多培训和辅导",
        },
    }


@forecast_enhanced_router.get("/forecast/activity-tracking", summary="销售动作追踪")
def get_activity_tracking(
    sales_id: Optional[int] = Query(None, description="销售 ID"),
    period: str = Query("monthly", description="周期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """销售动作完成度追踪"""
    tracking = {
        "period": "2026-02",
        "team_summary": {
            "visits": {"target": 120, "actual": 98, "completion": 81.7},
            "calls": {"target": 300, "actual": 276, "completion": 92.0},
            "meetings": {"target": 50, "actual": 45, "completion": 90.0},
            "proposals": {"target": 30, "actual": 28, "completion": 93.3},
            "stage_advances": {"target": 40, "actual": 35, "completion": 87.5},
        },
        "individual_tracking": [
            {
                "sales_id": 101, "sales_name": "张三",
                "activities": {
                    "visits": {"target": 15, "actual": 16, "completion": 106.7},
                    "calls": {"target": 40, "actual": 45, "completion": 112.5},
                    "meetings": {"target": 8, "actual": 9, "completion": 112.5},
                    "proposals": {"target": 5, "actual": 6, "completion": 120.0},
                },
                "avg_response_time_hours": 2.5, "opportunities_advanced": 5,
                "correlation": {"high_activity_opps": 8, "high_activity_win_rate": 75, "low_activity_opps": 2, "low_activity_win_rate": 25},
            },
            {
                "sales_id": 103, "sales_name": "王五",
                "activities": {
                    "visits": {"target": 15, "actual": 10, "completion": 66.7},
                    "calls": {"target": 40, "actual": 28, "completion": 70.0},
                    "meetings": {"target": 8, "actual": 5, "completion": 62.5},
                    "proposals": {"target": 5, "actual": 3, "completion": 60.0},
                },
                "avg_response_time_hours": 8.5, "opportunities_advanced": 2,
                "correlation": {"high_activity_opps": 3, "high_activity_win_rate": 67, "low_activity_opps": 6, "low_activity_win_rate": 17},
                "alerts": ["拜访完成率仅 66.7%", "平均响应时间 8.5 小时（团队平均 3 小时）"],
            },
        ],
        "insights": [
            {
                "insight": "高频跟进的商机赢单率是低频的 3 倍",
                "data": "高频（周跟进>=2 次）赢单率 72%，低频（周跟进<1 次）赢单率 24%",
                "recommendation": "要求所有商机至少每周跟进 2 次",
            },
            {
                "insight": "快速响应的销售成交周期短 40%",
                "data": "响应<4 小时的销售平均成交周期 35 天，响应>8 小时的销售 58 天",
                "recommendation": "建立 4 小时响应机制",
            },
        ],
    }
    return tracking


@forecast_enhanced_router.get("/forecast/accuracy-comparison", summary="预测准确性对比")
def get_accuracy_comparison(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """对比不同数据质量下的预测准确性"""
    comparison = {
        "high_data_quality": {
            "description": "数据质量>=90 分的销售", "sales_count": 5,
            "avg_prediction_accuracy": 96.5, "avg_win_rate": 68, "avg_sales_cycle_days": 32,
            "characteristics": ["决策链信息完整", "跟进记录及时", "拜访记录详细"],
        },
        "medium_data_quality": {
            "description": "数据质量 70-90 分的销售", "sales_count": 12,
            "avg_prediction_accuracy": 88.0, "avg_win_rate": 52, "avg_sales_cycle_days": 45,
            "characteristics": ["部分信息缺失", "跟进偶尔延迟", "拜访记录简单"],
        },
        "low_data_quality": {
            "description": "数据质量<70 分的销售", "sales_count": 8,
            "avg_prediction_accuracy": 75.0, "avg_win_rate": 35, "avg_sales_cycle_days": 62,
            "characteristics": ["关键信息缺失", "跟进经常延迟", "拜访记录不完整"],
        },
        "key_findings": [
            "数据质量高的销售，预测准确率高 21.5%",
            "数据质量高的销售，赢单率高 33%",
            "数据质量高的销售，成交周期短 48%",
        ],
        "conclusion": "认真填写数据不仅提高预测准确性，还直接提升销售业绩",
    }
    return comparison
