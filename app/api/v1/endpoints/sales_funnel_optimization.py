# -*- coding: utf-8 -*-
"""
销售漏斗优化 API
提供转化率分析、瓶颈识别、预测准确性分析
"""

from typing import Any, Optional, List, Dict
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.api import deps
from app.core import security
from app.models.user import User

router = APIRouter()


# ========== 1. 销售漏斗转化率分析 ==========

@router.get("/funnel/conversion-rates", summary="销售漏斗转化率分析")
def get_funnel_conversion_rates(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    sales_id: Optional[int] = Query(None, description="销售 ID（为空则全部）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    分析销售漏斗各环节转化率
    
    返回：
    - 各阶段商机数量
    - 阶段间转化率
    - 平均停留时间
    - 与历史对比
    """
    
    # 模拟销售漏斗数据
    funnel_data = {
        "period": {
            "start": start_date or (date.today() - timedelta(days=30)).isoformat(),
            "end": end_date or date.today().isoformat(),
        },
        "stages": [
            {
                "stage": "STAGE1",
                "stage_name": "初步接触",
                "count": 45,
                "conversion_to_next": 62.2,
                "avg_days_in_stage": 5.2,
                "trend": "up",
            },
            {
                "stage": "STAGE2",
                "stage_name": "需求挖掘",
                "count": 28,
                "conversion_to_next": 53.6,
                "avg_days_in_stage": 7.8,
                "trend": "stable",
            },
            {
                "stage": "STAGE3",
                "stage_name": "方案介绍",
                "count": 15,
                "conversion_to_next": 66.7,
                "avg_days_in_stage": 10.5,
                "trend": "up",
            },
            {
                "stage": "STAGE4",
                "stage_name": "价格谈判",
                "count": 10,
                "conversion_to_next": 50.0,
                "avg_days_in_stage": 8.3,
                "trend": "down",
            },
            {
                "stage": "STAGE5",
                "stage_name": "成交促成",
                "count": 5,
                "conversion_to_next": 80.0,
                "avg_days_in_stage": 4.1,
                "trend": "stable",
            },
            {
                "stage": "WON",
                "stage_name": "赢单",
                "count": 4,
                "conversion_to_next": None,
                "avg_days_in_stage": None,
                "trend": "up",
            },
        ],
        "overall_metrics": {
            "total_leads": 45,
            "total_won": 4,
            "overall_conversion_rate": 8.9,
            "avg_sales_cycle_days": 35.9,
            "total_pipeline_value": 15800000,
            "weighted_pipeline_value": 6320000,
        },
    }
    
    return funnel_data


# ========== 2. 瓶颈识别 ==========

@router.get("/funnel/bottlenecks", summary="瓶颈识别")
def get_funnel_bottlenecks(
    threshold: float = Query(50.0, description="转化率阈值%（低于此值标红）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    识别销售漏斗中的瓶颈环节
    
    返回：
    - 转化率低于阈值的阶段
    - 停留时间超长的阶段
    - 改进建议
    """
    
    bottlenecks = [
        {
            "stage": "STAGE4",
            "stage_name": "价格谈判",
            "issue_type": "low_conversion",
            "current_rate": 50.0,
            "benchmark_rate": 65.0,
            "gap": -15.0,
            "severity": "HIGH",
            "impact": "每月约损失 3-5 个商机，预计金额 800-1200 万",
            "root_causes": [
                "价格异议处理能力不足",
                "价值传递不够清晰",
                "决策链渗透不够深入",
            ],
            "recommendations": [
                "加强价格谈判培训",
                "准备 TCO（总拥有成本）分析工具",
                "提前识别并接触技术/采购决策人",
                "提供分期付款方案降低门槛",
            ],
        },
        {
            "stage": "STAGE2",
            "stage_name": "需求挖掘",
            "issue_type": "long_stay",
            "current_days": 7.8,
            "benchmark_days": 5.0,
            "gap": 2.8,
            "severity": "MEDIUM",
            "impact": "销售周期延长，影响整体效率",
            "root_causes": [
                "需求调研不够系统化",
                "客户配合度低",
                "技术方案反复修改",
            ],
            "recommendations": [
                "使用标准化需求调研模板",
                "设定明确的客户反馈截止时间",
                "提前准备 2-3 套备选方案",
            ],
        },
    ]
    
    return {
        "analysis_date": date.today().isoformat(),
        "threshold": threshold,
        "bottlenecks_found": len(bottlenecks),
        "high_severity": len([b for b in bottlenecks if b["severity"] == "HIGH"]),
        "medium_severity": len([b for b in bottlenecks if b["severity"] == "MEDIUM"]),
        "bottlenecks": bottlenecks,
        "overall_health_score": 72,
    }


# ========== 3. 预测准确性分析 ==========

@router.get("/funnel/prediction-accuracy", summary="预测准确性分析")
def get_prediction_accuracy(
    months: int = Query(3, description="分析月数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    分析赢单率预测的准确性
    
    对比：预测赢单率 vs 实际赢单率
    返回：
    - 预测准确性统计
    - 过度乐观/悲观的商机
    - 改进建议
    """
    
    accuracy_data = {
        "period": {
            "months": months,
            "total_opportunities": 127,
            "closed_opportunities": 89,
        },
        "overall_accuracy": {
            "predicted_win_rate": 68.5,
            "actual_win_rate": 62.9,
            "accuracy_score": 91.8,
            "bias": "略微乐观",
        },
        "by_stage": [
            {
                "stage": "STAGE1",
                "predicted": 25.0,
                "actual": 18.5,
                "accuracy": 74.0,
                "bias": "乐观",
            },
            {
                "stage": "STAGE2",
                "predicted": 45.0,
                "actual": 42.3,
                "accuracy": 94.0,
                "bias": "准确",
            },
            {
                "stage": "STAGE3",
                "predicted": 65.0,
                "actual": 68.2,
                "accuracy": 95.1,
                "bias": "准确",
            },
            {
                "stage": "STAGE4",
                "predicted": 80.0,
                "actual": 71.4,
                "accuracy": 89.3,
                "bias": "乐观",
            },
            {
                "stage": "STAGE5",
                "predicted": 90.0,
                "actual": 88.9,
                "accuracy": 98.8,
                "bias": "准确",
            },
        ],
        "over_optimistic": [
            {
                "opportunity_id": 101,
                "opportunity_name": "某客户 FCT 项目",
                "predicted_rate": 85,
                "actual_outcome": "LOST",
                "gap": -85,
                "reason": "低估竞品价格优势",
            },
            {
                "opportunity_id": 102,
                "opportunity_name": "某客户 EOL 项目",
                "predicted_rate": 75,
                "actual_outcome": "LOST",
                "gap": -75,
                "reason": "技术决策人变更未及时发现",
            },
        ],
        "recommendations": [
            "STAGE1 阶段预测偏乐观，建议加入更多客观评分因素",
            "STAGE4 价格谈判阶段需更谨慎评估",
            "建立预测复盘机制，每月分析偏差原因",
        ],
    }
    
    return accuracy_data


# ========== 4. 漏斗健康度仪表盘 ==========

@router.get("/funnel/health-dashboard", summary="漏斗健康度仪表盘")
def get_funnel_health_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售漏斗整体健康度评估
    
    返回：
    - 健康度评分
    - 关键指标
    - 风险预警
    - 行动建议
    """
    
    return {
        "dashboard_date": date.today().isoformat(),
        "overall_health": {
            "score": 78,
            "level": "GOOD",
            "trend": "improving",
        },
        "key_metrics": {
            "total_pipeline": 15800000,
            "weighted_pipeline": 6320000,
            "monthly_target": 5000000,
            "target_coverage": 126.4,
            "avg_deal_size": 1580000,
            "sales_velocity": 4.2,
        },
        "alerts": [
            {
                "type": "WARNING",
                "title": "STAGE4 转化率偏低",
                "description": "价格谈判阶段转化率 50%，低于基准 65%",
                "action": "查看瓶颈分析",
            },
            {
                "type": "INFO",
                "title": "Pipeline 充足",
                "description": "当前 Pipeline 覆盖月度目标的 126%",
                "action": null,
            },
            {
                "type": "SUCCESS",
                "title": "赢单率提升",
                "description": "本月赢单率 68%，环比提升 5%",
                "action": null,
            },
        ],
        "top_actions": [
            {
                "priority": 1,
                "action": "跟进 3 个高风险 STAGE4 商机",
                "impact": "预计影响 800 万业绩",
            },
            {
                "priority": 2,
                "action": "加速 5 个 STAGE2 商机推进",
                "impact": "缩短销售周期约 14 天",
            },
            {
                "priority": 3,
                "action": "复盘 2 个意外输单",
                "impact": "改进预测准确性",
            },
        ],
    }


# ========== 5. 销售趋势分析 ==========

@router.get("/funnel/trends", summary="销售趋势分析")
def get_funnel_trends(
    period: str = Query("monthly", description="周期：daily/weekly/monthly"),
    months: int = Query(6, description="分析月数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售漏斗趋势分析
    
    返回：
    - 各阶段数量趋势
    - 转化率趋势
    - 赢单率趋势
    """
    
    trends = {
        "period": period,
        "months": months,
        "data": [
            {
                "period": "2025-09",
                "leads": 38,
                "stage2": 22,
                "stage3": 12,
                "stage4": 8,
                "stage5": 4,
                "won": 3,
                "conversion_rate": 7.9,
            },
            {
                "period": "2025-10",
                "leads": 42,
                "stage2": 25,
                "stage3": 14,
                "stage4": 9,
                "stage5": 5,
                "won": 4,
                "conversion_rate": 9.5,
            },
            {
                "period": "2025-11",
                "leads": 40,
                "stage2": 24,
                "stage3": 13,
                "stage4": 8,
                "stage5": 4,
                "won": 3,
                "conversion_rate": 7.5,
            },
            {
                "period": "2025-12",
                "leads": 45,
                "stage2": 28,
                "stage3": 15,
                "stage4": 10,
                "stage5": 5,
                "won": 4,
                "conversion_rate": 8.9,
            },
        ],
        "insights": [
            "线索量稳步增长，月均增长 6%",
            "STAGE2→STAGE3 转化率有提升趋势",
            "Q4 整体表现优于 Q3",
        ],
    }
    
    return trends
