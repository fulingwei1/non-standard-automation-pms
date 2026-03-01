# -*- coding: utf-8 -*-
"""
销售预测增强版 API
考虑多维度因素，提高预测准确性，倒逼数据填写
"""

from typing import Any, Optional, List
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User

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
    
    prediction = {
        "period": "2026-Q1",
        "generated_at": date.today().isoformat(),
        
        # ========== 基础预测（仅漏斗） ==========
        "base_prediction": {
            "formula": "已完成 + Σ(漏斗金额 × 阶段赢单率)",
            "completed": 28500000,
            "pipeline_weighted": 21575000,
            "base_predicted": 50075000,
            "base_completion_rate": 100.15,
        },
        
        # ========== 数据质量系数 ==========
        "data_quality_factor": {
            "overall_score": 78,
            "impact": -0.05,  # 数据质量差，预测下调 5%
            
            "dimensions": [
                {
                    "name": "线索完整度",
                    "score": 85,
                    "weight": 20,
                    "description": "必填字段填写率",
                    "issues": ["15% 的商机缺少预算信息"],
                },
                {
                    "name": "跟进及时性",
                    "score": 72,
                    "weight": 25,
                    "description": "X 天未跟进的商机占比",
                    "issues": ["8 个商机超过 7 天未跟进"],
                },
                {
                    "name": "决策链完整度",
                    "score": 65,
                    "weight": 25,
                    "description": "关键决策人信息填写率",
                    "issues": ["40% 的商机未识别 EB（最终决策人）"],
                },
                {
                    "name": "拜访记录完整度",
                    "score": 80,
                    "weight": 15,
                    "description": "拜访打卡 + 记录填写",
                    "issues": ["20% 的拜访缺少现场照片"],
                },
                {
                    "name": "赢单/输单原因",
                    "score": 90,
                    "weight": 15,
                    "description": "关闭商机时原因填写",
                    "issues": [],
                },
            ],
        },
        
        # ========== 销售动作完成度 ==========
        "activity_factor": {
            "overall_score": 82,
            "impact": 0.02,  # 动作完成好，预测上调 2%
            
            "metrics": {
                "visits_target": 120,
                "visits_actual": 98,
                "visits_completion": 81.7,
                "calls_target": 300,
                "calls_actual": 276,
                "calls_completion": 92.0,
                "meetings_target": 50,
                "meetings_actual": 45,
                "meetings_completion": 90.0,
                "proposals_target": 30,
                "proposals_actual": 28,
                "proposals_completion": 93.3,
            },
            
            "correlation_analysis": {
                "high_activity_win_rate": 72,  # 高频跟进的商机赢单率
                "low_activity_win_rate": 35,   # 低频跟进的商机赢单率
                "insight": "高频跟进的商机赢单率是低频的 2 倍",
            },
        },
        
        # ========== 商机健康度 ==========
        "opportunity_health_factor": {
            "overall_score": 75,
            "impact": -0.03,  # 商机健康度一般，下调 3%
            
            "healthy_opportunities": {
                "count": 45,
                "total_amount": 32000000,
                "criteria": "7 天内有跟进 + 决策链完整 + 下一步明确",
            },
            "at_risk_opportunities": {
                "count": 18,
                "total_amount": 8500000,
                "criteria": "超过 14 天未跟进 或 决策链缺失",
                "details": [
                    {"name": "欣旺达 FCT", "amount": 3200000, "risk": "14 天未跟进"},
                    {"name": "蜂巢能源 EOL", "amount": 2800000, "risk": "未识别 EB"},
                    {"name": "国轩高科 ICT", "amount": 2500000, "risk": "无明确下一步"},
                ],
            },
        },
        
        # ========== 历史预测准确性 ==========
        "historical_accuracy_factor": {
            "avg_accuracy": 94.5,
            "impact": 0,  # 历史准确，不调整
            
            "recent_predictions": [
                {"period": "2025-12", "predicted": 51000000, "actual": 51200000, "accuracy": 99.6},
                {"period": "2026-01", "predicted": 38000000, "actual": 39200000, "accuracy": 96.8},
                {"period": "2026-02", "predicted": 42000000, "actual": 44500000, "accuracy": 94.0},
            ],
        },
        
        # ========== 季节性因素 ==========
        "seasonality_factor": {
            "current_month": "3 月",
            "factor": 1.08,  # Q1 末通常是签约高峰，上调 8%
            "impact": 0.03,
            "historical_pattern": "Q1 末月通常比前 2 个月增长 30-50%",
        },
        
        # ========== 最终预测 ==========
        "final_prediction": {
            "base": 50075000,
            "adjustments": {
                "data_quality": -2503750,  # -5%
                "activity": 1001500,       # +2%
                "health": -1502250,        # -3%
                "seasonality": 1502250,    # +3%
            },
            "total_adjustment": -1502250,
            "final_predicted": 48572750,
            "final_completion_rate": 97.15,
            "confidence_level": 82,
            "confidence_interval": {
                "optimistic": 53000000,   # 110%
                "pessimistic": 44000000,   # 88%
            },
        },
        
        # ========== 关键发现 ==========
        "key_insights": [
            {
                "type": "WARNING",
                "title": "数据质量影响预测准确性",
                "description": "当前数据质量系数 78 分，导致预测下调 5%（250 万）",
                "action": "督促销售完善商机信息，特别是决策链和跟进记录",
                "impact": 2500000,
            },
            {
                "type": "WARNING",
                "title": "18 个商机存在风险",
                "description": "超过 14 天未跟进或决策链缺失，涉及金额 850 万",
                "action": "立即跟进这些商机，更新状态",
                "impact": 8500000,
            },
            {
                "type": "SUCCESS",
                "title": "销售动作完成良好",
                "description": "电话/会议完成率 90%+，高频跟进的商机赢单率 72%",
                "action": "保持当前跟进节奏",
                "impact": 1000000,
            },
        ],
        
        # ========== 改进建议 ==========
        "improvement_recommendations": [
            {
                "priority": 1,
                "action": "完善决策链信息",
                "description": "40% 的商机未识别 EB，需要补充关键决策人信息",
                "expected_impact": "+3% 预测准确率",
                "deadline": "3 月 10 日前",
                "responsible": "全体销售",
            },
            {
                "priority": 2,
                "action": "跟进逾期商机",
                "description": "18 个商机超过 14 天未跟进，需要立即联系",
                "expected_impact": "+5% 赢单率",
                "deadline": "3 月 5 日前",
                "responsible": "相关销售",
            },
            {
                "priority": 3,
                "action": "提升拜访记录质量",
                "description": "20% 的拜访缺少现场照片，需要完整记录",
                "expected_impact": "+2% 数据质量分",
                "deadline": "持续改进",
                "responsible": "全体销售",
            },
        ],
    }
    
    return prediction


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
    
    # 团队数据质量排名
    team_scores = [
        {
            "rank": 1,
            "sales_id": 101,
            "sales_name": "张三",
            "team": "华南大区",
            "overall_score": 92,
            "dimensions": {
                "lead_completeness": 95,
                "follow_up_timeliness": 90,
                "decision_chain": 88,
                "visit_records": 95,
                "close_reason": 100,
            },
            "opportunities_count": 12,
            "healthy_opportunities": 11,
            "prediction_accuracy": 96.5,
        },
        {
            "rank": 2,
            "sales_id": 102,
            "sales_name": "李四",
            "team": "华东大区",
            "overall_score": 85,
            "dimensions": {
                "lead_completeness": 88,
                "follow_up_timeliness": 85,
                "decision_chain": 80,
                "visit_records": 88,
                "close_reason": 85,
            },
            "opportunities_count": 10,
            "healthy_opportunities": 8,
            "prediction_accuracy": 92.0,
        },
        {
            "rank": 3,
            "sales_id": 103,
            "sales_name": "王五",
            "team": "华南大区",
            "overall_score": 72,
            "dimensions": {
                "lead_completeness": 75,
                "follow_up_timeliness": 65,
                "decision_chain": 70,
                "visit_records": 78,
                "close_reason": 72,
            },
            "opportunities_count": 11,
            "healthy_opportunities": 6,
            "prediction_accuracy": 85.0,
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
            "lead_completeness": {
                "name": "线索完整度",
                "weight": 20,
                "criteria": "必填字段填写率 ≥95% 得满分",
            },
            "follow_up_timeliness": {
                "name": "跟进及时性",
                "weight": 25,
                "criteria": "无超过 7 天未跟进的商机",
            },
            "decision_chain": {
                "name": "决策链完整度",
                "weight": 25,
                "criteria": "EB/TB/PB 信息完整",
            },
            "visit_records": {
                "name": "拜访记录完整度",
                "weight": 15,
                "criteria": "拜访打卡 + 照片 + 记录",
            },
            "close_reason": {
                "name": "赢单/输单原因",
                "weight": 15,
                "criteria": "关闭商机时详细填写原因",
            },
        },
        
        "impact_explanation": {
            "on_prediction": "数据质量分每低 10 分，预测准确率下降约 5%",
            "on_performance": "数据质量纳入绩效考核，占比 15%",
            "on_support": "低分销售将获得更多培训和辅导",
        },
    }


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
                "sales_id": 101,
                "sales_name": "张三",
                "activities": {
                    "visits": {"target": 15, "actual": 16, "completion": 106.7},
                    "calls": {"target": 40, "actual": 45, "completion": 112.5},
                    "meetings": {"target": 8, "actual": 9, "completion": 112.5},
                    "proposals": {"target": 5, "actual": 6, "completion": 120.0},
                },
                "avg_response_time_hours": 2.5,
                "opportunities_advanced": 5,
                "correlation": {
                    "high_activity_opps": 8,
                    "high_activity_win_rate": 75,
                    "low_activity_opps": 2,
                    "low_activity_win_rate": 25,
                },
            },
            {
                "sales_id": 103,
                "sales_name": "王五",
                "activities": {
                    "visits": {"target": 15, "actual": 10, "completion": 66.7},
                    "calls": {"target": 40, "actual": 28, "completion": 70.0},
                    "meetings": {"target": 8, "actual": 5, "completion": 62.5},
                    "proposals": {"target": 5, "actual": 3, "completion": 60.0},
                },
                "avg_response_time_hours": 8.5,
                "opportunities_advanced": 2,
                "correlation": {
                    "high_activity_opps": 3,
                    "high_activity_win_rate": 67,
                    "low_activity_opps": 6,
                    "low_activity_win_rate": 17,
                },
                "alerts": ["拜访完成率仅 66.7%", "平均响应时间 8.5 小时（团队平均 3 小时）"],
            },
        ],
        
        "insights": [
            {
                "insight": "高频跟进的商机赢单率是低频的 3 倍",
                "data": "高频（周跟进≥2 次）赢单率 72%，低频（周跟进<1 次）赢单率 24%",
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
    
    comparison = {
        "high_data_quality": {
            "description": "数据质量≥90 分的销售",
            "sales_count": 5,
            "avg_prediction_accuracy": 96.5,
            "avg_win_rate": 68,
            "avg_sales_cycle_days": 32,
            "characteristics": [
                "决策链信息完整",
                "跟进记录及时",
                "拜访记录详细",
            ],
        },
        "medium_data_quality": {
            "description": "数据质量 70-90 分的销售",
            "sales_count": 12,
            "avg_prediction_accuracy": 88.0,
            "avg_win_rate": 52,
            "avg_sales_cycle_days": 45,
            "characteristics": [
                "部分信息缺失",
                "跟进偶尔延迟",
                "拜访记录简单",
            ],
        },
        "low_data_quality": {
            "description": "数据质量<70 分的销售",
            "sales_count": 8,
            "avg_prediction_accuracy": 75.0,
            "avg_win_rate": 35,
            "avg_sales_cycle_days": 62,
            "characteristics": [
                "关键信息缺失",
                "跟进经常延迟",
                "拜访记录不完整",
            ],
        },
        
        "key_findings": [
            "数据质量高的销售，预测准确率高 21.5%",
            "数据质量高的销售，赢单率高 33%",
            "数据质量高的销售，成交周期短 48%",
        ],
        
        "conclusion": "认真填写数据不仅提高预测准确性，还直接提升销售业绩",
    }
    
    return comparison
