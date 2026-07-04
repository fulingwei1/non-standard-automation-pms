# -*- coding: utf-8 -*-
"""
销售与客户商务关系成熟度模型
评估关系深度，预测赢单概率
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import Customer, CustomerRelationshipScore, Opportunity
from app.models.user import User
from app.services.relationship_scoring_service import (
    MATURITY_LEVELS,
    RelationshipScoringService,
)

router = APIRouter()


def _get_customer(db: Session, customer_id: int) -> Optional[Customer]:
    return db.query(Customer).filter(Customer.id == customer_id).first()


def _get_opportunity(db: Session, opportunity_id: Optional[int]) -> Optional[Opportunity]:
    if not opportunity_id:
        return None
    return db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()


def _customer_name(customer: Any) -> str:
    return (
        getattr(customer, "customer_name", None)
        or getattr(customer, "name", None)
        or getattr(customer, "short_name", None)
        or f"客户#{getattr(customer, 'id', '未知')}"
    )


def _score_level_key(level: str) -> str:
    suffix = {
        "L1": "initial",
        "L2": "developing",
        "L3": "mature",
        "L4": "strategic",
        "L5": "partnership",
    }.get(level, "unknown")
    return f"{level}_{suffix}"


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


# ========== 1. 关系成熟度评估模型 ==========


@router.get("/relationship/maturity-model", summary="关系成熟度评估模型")
def get_relationship_maturity_model(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    商务关系成熟度评估模型

    6 大维度，100 分制：
    1. 决策链覆盖度 (20 分) - EB/TB/PB/UB/Coach
    2. 互动频率 (15 分) - 联系密度
    3. 关系深度 (20 分) - 陌生→接触→认可→信任→伙伴
    4. 信息获取度 (15 分) - 预算/决策流程/竞品
    5. 支持度 (20 分) - 支持/中立/反对
    6. 高层互动 (10 分) - 对等接待

    成熟度等级：
    - L1 初始级 (0-30 分)：刚接触，信息有限
    - L2 发展级 (31-50 分)：建立联系，初步认可
    - L3 成熟级 (51-70 分)：深度信任，信息透明
    - L4 战略级 (71-85 分)：战略合作，高度支持
    - L5 伙伴级 (86-100 分)：长期伙伴，排他支持
    """

    model = {
        "model_name": "商务关系成熟度评估模型 v1.0",
        "version": "1.0",
        "created_date": date.today().isoformat(),
        "dimensions": [
            {
                "id": 1,
                "name": "决策链覆盖度",
                "weight": 20,
                "description": "关键决策人覆盖情况",
                "scoring": {
                    "EB_covered": {
                        "name": "最终决策人",
                        "score": 5,
                        "criteria": "已建立联系并深入沟通",
                    },
                    "TB_covered": {
                        "name": "技术决策人",
                        "score": 5,
                        "criteria": "技术认可，支持方案",
                    },
                    "PB_covered": {"name": "采购决策人", "score": 4, "criteria": "商务条件已沟通"},
                    "UB_covered": {"name": "最终用户", "score": 3, "criteria": "用户使用意愿强"},
                    "Coach_identified": {
                        "name": "内线/教练",
                        "score": 3,
                        "criteria": "有内部支持者",
                    },
                },
            },
            {
                "id": 2,
                "name": "互动频率",
                "weight": 15,
                "description": "联系密度和持续性",
                "scoring": {
                    "daily_contact": {"range": "每天联系", "score": 15},
                    "weekly_2plus": {"range": "每周 2 次以上", "score": 12},
                    "weekly_1": {"range": "每周 1 次", "score": 8},
                    "biweekly": {"range": "每 2 周 1 次", "score": 5},
                    "monthly": {"range": "每月 1 次", "score": 2},
                    "irregular": {"range": "不规律", "score": 0},
                },
            },
            {
                "id": 3,
                "name": "关系深度",
                "weight": 20,
                "description": "从陌生到伙伴的演进",
                "levels": {
                    "L1_stranger": {
                        "name": "陌生",
                        "score": 4,
                        "description": "刚接触，相互了解有限",
                    },
                    "L2_contact": {"name": "接触", "score": 8, "description": "建立联系，保持沟通"},
                    "L3_recognition": {
                        "name": "认可",
                        "score": 12,
                        "description": "认可专业能力，愿意交流",
                    },
                    "L4_trust": {
                        "name": "信任",
                        "score": 16,
                        "description": "深度信任，分享内部信息",
                    },
                    "L5_partnership": {
                        "name": "伙伴",
                        "score": 20,
                        "description": "战略合作伙伴，排他支持",
                    },
                },
            },
            {
                "id": 4,
                "name": "信息获取度",
                "weight": 15,
                "description": "客户内部信息掌握程度",
                "scoring": {
                    "budget_clear": {
                        "name": "预算明确",
                        "score": 4,
                        "criteria": "知道具体预算范围",
                    },
                    "decision_process": {
                        "name": "决策流程",
                        "score": 4,
                        "criteria": "清楚决策流程和关键节点",
                    },
                    "timeline": {"name": "时间表", "score": 3, "criteria": "了解项目时间计划"},
                    "competitor_info": {
                        "name": "竞品信息",
                        "score": 2,
                        "criteria": "知道参与竞品情况",
                    },
                    "pain_points": {"name": "痛点需求", "score": 2, "criteria": "深入理解客户痛点"},
                },
            },
            {
                "id": 5,
                "name": "支持度",
                "weight": 20,
                "description": "关键人对我们的支持程度",
                "scoring": {
                    "EB_support": {"name": "EB 支持", "level": "supportive", "score": 8},
                    "TB_support": {"name": "TB 支持", "level": "supportive", "score": 6},
                    "PB_support": {"name": "PB 支持", "level": "supportive", "score": 4},
                    "UB_support": {"name": "UB 支持", "level": "supportive", "score": 2},
                    "neutral_impact": {
                        "name": "中立影响",
                        "penalty": -5,
                        "description": "关键人持中立态度",
                    },
                    "opponent_impact": {
                        "name": "反对影响",
                        "penalty": -10,
                        "description": "有关键人反对我们",
                    },
                },
            },
            {
                "id": 6,
                "name": "高层互动",
                "weight": 10,
                "description": "双方高层互动情况",
                "scoring": {
                    "ceo_meeting": {
                        "name": "CEO 互访",
                        "score": 10,
                        "criteria": "双方 CEO/总经理会面",
                    },
                    "vp_meeting": {
                        "name": "VP 级交流",
                        "score": 7,
                        "criteria": "副总裁/总监级交流",
                    },
                    "director_meeting": {
                        "name": "总监级交流",
                        "score": 4,
                        "criteria": "部门总监级交流",
                    },
                    "working_level": {
                        "name": "工作层交流",
                        "score": 2,
                        "criteria": "仅工作层面对接",
                    },
                },
            },
        ],
        "maturity_levels": {
            "L1": {
                "name": "初始级",
                "score_range": "0-30",
                "win_rate_estimate": "10-25%",
                "characteristics": [
                    "刚接触客户，了解有限",
                    "决策链信息不完整",
                    "互动频率低",
                    "未建立信任关系",
                ],
                "recommended_actions": [
                    "增加拜访频率，建立联系",
                    "识别关键决策人",
                    "了解客户基本需求",
                ],
            },
            "L2": {
                "name": "发展级",
                "score_range": "31-50",
                "win_rate_estimate": "25-45%",
                "characteristics": [
                    "建立初步联系",
                    "识别部分决策人",
                    "客户认可专业能力",
                    "获取部分内部信息",
                ],
                "recommended_actions": [
                    "深化与技术决策人关系",
                    "争取试用/POC 机会",
                    "了解预算和决策流程",
                ],
            },
            "L3": {
                "name": "成熟级",
                "score_range": "51-70",
                "win_rate_estimate": "45-65%",
                "characteristics": [
                    "深度信任关系",
                    "决策链覆盖完整",
                    "信息透明共享",
                    "客户主动配合",
                ],
                "recommended_actions": [
                    "推动高层互访",
                    "制定差异化方案",
                    "锁定关键决策人支持",
                ],
            },
            "L4": {
                "name": "战略级",
                "score_range": "71-85",
                "win_rate_estimate": "65-85%",
                "characteristics": [
                    "战略合作伙伴关系",
                    "高层深度互动",
                    "客户内部强力支持",
                    "竞品难以切入",
                ],
                "recommended_actions": [
                    "巩固高层关系",
                    "扩展合作范围",
                    "预防竞品挖角",
                ],
            },
            "L5": {
                "name": "伙伴级",
                "score_range": "86-100",
                "win_rate_estimate": "85-95%",
                "characteristics": [
                    "长期战略合作",
                    "排他性支持",
                    "共同发展规划",
                    "几乎锁定赢单",
                ],
                "recommended_actions": [
                    "维护长期关系",
                    "挖掘新合作机会",
                    "转介绍新客户",
                ],
            },
        },
    }

    return model


# ========== 2. 客户关评估 ==========


@router.get("/relationship/customer/{customer_id}/assessment", summary="客户关系评估")
def get_customer_relationship_assessment(
    customer_id: int = Path(..., description="客户 ID"),
    opportunity_id: Optional[int] = Query(None, description="商机 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    评估与特定客户的关系成熟度

    返回：
    - 各维度得分
    - 总体成熟度
    - 赢单率预估
    - 改进建议
    """

    customer = _get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    opportunity = _get_opportunity(db, opportunity_id)
    service = RelationshipScoringService(db)
    assessment = service.calculate_customer_score(
        customer_id=customer_id,
        opportunity_id=opportunity_id,
        save_to_db=False,
    )
    assessment["customer_name"] = _customer_name(customer)
    assessment["opportunity_name"] = getattr(opportunity, "opp_name", None)
    get_history = getattr(service, "get_customer_score_history", None)
    assessment["historical_trend"] = get_history(customer_id) if get_history else []
    assessment["data_source"] = "relationship_scoring_service"
    return assessment


# ========== 3. 关系提升建议 ==========


@router.post("/relationship/improvement-plan", summary="关系提升计划")
def create_relationship_improvement_plan(
    customer_id: int = Body(..., description="客户 ID"),
    current_score: int = Body(..., description="当前得分"),
    target_score: int = Body(..., description="目标得分"),
    timeline_days: int = Body(30, description="时间线（天）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    生成客户关系提升计划

    根据当前得分和目标得分，生成具体行动计划
    """

    gap = target_score - current_score
    first_target = current_score + gap * 0.3

    plan = {
        "customer_id": customer_id,
        "current_score": current_score,
        "target_score": target_score,
        "gap": target_score - current_score,
        "timeline_days": timeline_days,
        "action_plan": [
            {
                "week": 1,
                "focus": "决策链补全",
                "actions": [
                    {
                        "action": "补齐未覆盖的采购、技术、使用和经济决策角色",
                        "owner": "销售经理",
                        "expected_outcome": "形成客户决策链清单和下一步跟进计划",
                    },
                    {
                        "action": "整理客户预算、时间表、验收标准和竞品信息",
                        "owner": "销售经理",
                        "expected_outcome": "补齐关系评分所需关键信息",
                    },
                ],
            },
            {
                "week": 2,
                "focus": "高层互动",
                "actions": [
                    {
                        "action": "安排双方管理层沟通",
                        "owner": "销售负责人",
                        "expected_outcome": "明确高层关注点和合作价值",
                    },
                    {
                        "action": "准备客户专属合作方案",
                        "owner": "销售总监",
                        "expected_outcome": "明确合作价值",
                    },
                ],
            },
            {
                "week": 3,
                "focus": "深化信任",
                "actions": [
                    {
                        "action": "提供行业洞察报告",
                        "owner": "市场部",
                        "expected_outcome": "展示专业能力",
                    },
                    {
                        "action": "邀请参观标杆项目",
                        "owner": "销售经理",
                        "expected_outcome": "增强信心",
                    },
                ],
            },
            {
                "week": 4,
                "focus": "锁定支持",
                "actions": [
                    {
                        "action": "获取书面支持意向",
                        "owner": "销售经理",
                        "expected_outcome": "锁定支持",
                    },
                    {"action": "敲定合作细节", "owner": "商务", "expected_outcome": "推进签约"},
                ],
            },
        ],
        "milestones": [
            {"week": 2, "target_score": first_target, "description": "完成关键角色补齐和高层沟通"},
            {"week": 4, "target_score": target_score, "description": "达成战略合作"},
        ],
        "success_metrics": [
            "关键决策角色覆盖率提升",
            "客户预算/决策流程/时间表信息完整",
            "至少一个关键角色明确支持",
        ],
    }

    return plan


# ========== 4. 客户组合分析 ==========


@router.get("/relationship/portfolio-analysis", summary="客户组合分析")
def get_relationship_portfolio_analysis(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    分析所有客户的关系成熟度分布

    帮助领导了解整体客户关系健康度
    """

    score_records = (
        db.query(CustomerRelationshipScore)
        .order_by(CustomerRelationshipScore.score_date.desc(), CustomerRelationshipScore.id.desc())
        .all()
    )
    latest_by_customer: dict[int, CustomerRelationshipScore] = {}
    for record in score_records:
        customer_id = getattr(record, "customer_id", None)
        if customer_id and customer_id not in latest_by_customer:
            latest_by_customer[customer_id] = record

    latest_records = list(latest_by_customer.values())
    total_customers = len(latest_records)

    distribution: dict[str, dict[str, Any]] = {}
    for level, config in MATURITY_LEVELS.items():
        key = _score_level_key(level)
        distribution[key] = {
            "level": level,
            "name": config["name"],
            "count": 0,
            "percentage": 0,
            "avg_win_rate": 0,
        }

    key_accounts = []
    for record in latest_records:
        level = getattr(record, "maturity_level", None) or "L1"
        if level not in MATURITY_LEVELS:
            level = "L1"
        dist = distribution[_score_level_key(level)]
        dist["count"] += 1
        dist["avg_win_rate"] += getattr(record, "estimated_win_rate", None) or 0

        customer = _get_customer(db, record.customer_id)
        customer_name = _customer_name(customer) if customer else f"客户#{record.customer_id}"
        revenue_potential = _safe_float(getattr(customer, "annual_revenue", 0))
        key_accounts.append(
            {
                "customer_id": record.customer_id,
                "customer_name": customer_name,
                "maturity_level": level,
                "score": getattr(record, "total_score", 0) or 0,
                "estimated_win_rate": getattr(record, "estimated_win_rate", 0) or 0,
                "revenue_potential": revenue_potential,
                "score_date": str(getattr(record, "score_date", "")),
            }
        )

    for item in distribution.values():
        if total_customers:
            item["percentage"] = round(item["count"] / total_customers * 100, 1)
        if item["count"]:
            item["avg_win_rate"] = round(item["avg_win_rate"] / item["count"], 1)

    healthy_count = sum(
        1 for record in latest_records if (getattr(record, "maturity_level", "") or "") in {"L3", "L4", "L5"}
    )
    at_risk_count = total_customers - healthy_count
    average_score = (
        round(sum((getattr(r, "total_score", 0) or 0) for r in latest_records) / total_customers, 1)
        if total_customers
        else 0
    )
    key_accounts.sort(key=lambda item: item["score"], reverse=True)

    needs_attention = [
        {
            **item,
            "issue": "关系成熟度低",
            "recommended_action": "补齐决策链并提升关键角色互动频率",
        }
        for item in key_accounts
        if item["maturity_level"] in {"L1", "L2"}
    ][:5]

    return {
        "total_customers": total_customers,
        "assessment_date": date.today().isoformat(),
        "data_source": "customer_relationship_scores",
        "maturity_distribution": distribution,
        "health_assessment": {
            "healthy_count": healthy_count,
            "healthy_percentage": round(healthy_count / total_customers * 100, 1) if total_customers else 0,
            "at_risk_count": at_risk_count,
            "at_risk_percentage": round(at_risk_count / total_customers * 100, 1) if total_customers else 0,
            "overall_health_score": average_score,
        },
        "key_accounts": key_accounts[:10],
        "needs_attention": needs_attention,
        "strategic_recommendations": [
            {
                "priority": 1,
                "action": "优先提升 L1/L2 客户关系成熟度",
                "target_customers": at_risk_count,
                "expected_impact": "提高低成熟度客户推进质量",
                "resources_needed": "销售拜访、技术支持、决策链补齐",
            },
            {
                "priority": 2,
                "action": "维护 L4/L5 高成熟度客户",
                "target_customers": sum(
                    1 for record in latest_records if (getattr(record, "maturity_level", "") or "") in {"L4", "L5"}
                ),
                "expected_impact": "降低关键客户流失和竞品切入风险",
                "resources_needed": "高层沟通、持续复盘、专属服务",
            },
        ],
    }
