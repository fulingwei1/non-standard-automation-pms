# -*- coding: utf-8 -*-
"""
销售绩效与激励 API
提供实时排行榜、提成计算、PK 对战
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User

router = APIRouter()


# ========== 1. 实时业绩排行榜 ==========


@router.get("/performance/leaderboard", summary="实时业绩排行榜")
def get_performance_leaderboard(
    period: str = Query("monthly", description="周期：daily/weekly/monthly/quarterly/yearly"),
    department: Optional[str] = Query(None, description="部门"),
    limit: int = Query(10, description="返回数量"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    实时业绩排行榜

    维度：
    - 个人排行榜
    - 团队排行榜
    - 新人排行榜（入职<1 年）
    """

    # 模拟排行榜数据
    leaderboard = {
        "period": period,
        "period_label": {
            "daily": "今日",
            "weekly": "本周",
            "monthly": "本月",
            "quarterly": "本季度",
            "yearly": "本年度",
        }.get(period, "本月"),
        "updated_at": date.today().isoformat(),
        "individual_ranking": [
            {
                "rank": 1,
                "sales_id": 101,
                "sales_name": "张三",
                "department": "华南大区",
                "revenue": 15800000,
                "target": 10000000,
                "completion_rate": 158.0,
                "deals_won": 12,
                "avg_deal_size": 1316667,
                "trend": "up",
                "rank_change": 0,
            },
            {
                "rank": 2,
                "sales_id": 102,
                "sales_name": "李四",
                "department": "华东大区",
                "revenue": 12500000,
                "target": 10000000,
                "completion_rate": 125.0,
                "deals_won": 9,
                "avg_deal_size": 1388889,
                "trend": "up",
                "rank_change": 1,
            },
            {
                "rank": 3,
                "sales_id": 103,
                "sales_name": "王五",
                "department": "华北大区",
                "revenue": 11200000,
                "target": 10000000,
                "completion_rate": 112.0,
                "deals_won": 8,
                "avg_deal_size": 1400000,
                "trend": "down",
                "rank_change": -1,
            },
            {
                "rank": 4,
                "sales_id": 104,
                "sales_name": "赵六",
                "department": "华南大区",
                "revenue": 9800000,
                "target": 10000000,
                "completion_rate": 98.0,
                "deals_won": 7,
                "avg_deal_size": 1400000,
                "trend": "stable",
                "rank_change": 0,
            },
            {
                "rank": 5,
                "sales_id": 105,
                "sales_name": "钱七",
                "department": "华东大区",
                "revenue": 8500000,
                "target": 10000000,
                "completion_rate": 85.0,
                "deals_won": 6,
                "avg_deal_size": 1416667,
                "trend": "up",
                "rank_change": 2,
            },
        ],
        "team_ranking": [
            {
                "rank": 1,
                "team_name": "华南大区",
                "revenue": 45800000,
                "target": 40000000,
                "completion_rate": 114.5,
                "members_count": 8,
                "avg_per_person": 5725000,
            },
            {
                "rank": 2,
                "team_name": "华东大区",
                "revenue": 42500000,
                "target": 40000000,
                "completion_rate": 106.2,
                "members_count": 7,
                "avg_per_person": 6071429,
            },
            {
                "rank": 3,
                "team_name": "华北大区",
                "revenue": 38200000,
                "target": 40000000,
                "completion_rate": 95.5,
                "members_count": 6,
                "avg_per_person": 6366667,
            },
        ],
        "newcomer_ranking": [
            {
                "rank": 1,
                "sales_id": 108,
                "sales_name": "小陈",
                "department": "华南大区",
                "join_date": "2025-06-01",
                "revenue": 5200000,
                "target": 5000000,
                "completion_rate": 104.0,
                "deals_won": 4,
            },
            {
                "rank": 2,
                "sales_id": 109,
                "sales_name": "小刘",
                "department": "华东大区",
                "join_date": "2025-07-15",
                "revenue": 4800000,
                "target": 5000000,
                "completion_rate": 96.0,
                "deals_won": 3,
            },
        ],
        "top_performers": {
            "highest_revenue": {"sales_name": "张三", "value": 15800000},
            "highest_completion": {"sales_name": "张三", "value": 158.0},
            "most_deals": {"sales_name": "张三", "value": 12},
            "largest_deal": {"sales_name": "李四", "value": 2800000},
        },
    }

    return leaderboard


# ========== 2. 提成自动计算 ==========


@router.get("/commission/calculate", summary="提成计算")
def calculate_commission(
    sales_id: Optional[int] = Query(None, description="销售 ID"),
    month: Optional[str] = Query(None, description="月份 YYYY-MM"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    自动计算销售提成

    规则：
    - 阶梯提成（完成率越高，提成比例越高）
    - 产品类型系数（高毛利产品系数高）
    - 回款系数（按实际回款计算）
    """

    # 模拟提成计算数据
    commission_data = {
        "sales_id": sales_id or 101,
        "sales_name": "张三",
        "month": month or "2025-02",
        "base_data": {
            "monthly_target": 10000000,
            "monthly_revenue": 15800000,
            "completion_rate": 158.0,
            "deals_won": 12,
        },
        "commission_rules": {
            "tiers": [
                {"min_rate": 0, "max_rate": 80, "commission_rate": 1.0, "label": "基础档"},
                {"min_rate": 80, "max_rate": 100, "commission_rate": 1.5, "label": "达标档"},
                {"min_rate": 100, "max_rate": 120, "commission_rate": 2.0, "label": "超额档"},
                {"min_rate": 120, "max_rate": 999, "commission_rate": 3.0, "label": "卓越档"},
            ],
            "product_coefficients": {
                "FCT": 1.2,
                "ICT": 1.0,
                "EOL": 1.1,
                "VISION": 1.3,
            },
            "collection_coefficient": 0.9,  # 回款系数
        },
        "deals": [
            {
                "deal_id": 1001,
                "customer_name": "宁德时代",
                "product_type": "FCT",
                "revenue": 3200000,
                "gross_margin": 35,
                "collection_status": "partial",  # full/partial/none
                "collection_rate": 0.9,
                "base_commission_rate": 3.0,  # 卓越档
                "product_coefficient": 1.2,
                "final_commission_rate": 3.24,
                "commission_amount": 103680,
            },
            {
                "deal_id": 1002,
                "customer_name": "比亚迪",
                "product_type": "EOL",
                "revenue": 2800000,
                "gross_margin": 32,
                "collection_status": "full",
                "collection_rate": 1.0,
                "base_commission_rate": 3.0,
                "product_coefficient": 1.1,
                "final_commission_rate": 3.3,
                "commission_amount": 92400,
            },
            {
                "deal_id": 1003,
                "customer_name": "中创新航",
                "product_type": "FCT",
                "revenue": 3500000,
                "gross_margin": 38,
                "collection_status": "partial",
                "collection_rate": 0.6,
                "base_commission_rate": 3.0,
                "product_coefficient": 1.2,
                "final_commission_rate": 2.16,
                "commission_amount": 75600,
            },
        ],
        "summary": {
            "total_revenue": 15800000,
            "total_base_commission": 476000,
            "product_bonus": 28560,
            "collection_adjustment": -47600,
            "final_commission": 456960,
            "tax_estimate": 68544,
            "net_commission": 388416,
        },
        "breakdown": {
            "by_tier": [
                {"tier": "卓越档", "revenue": 12000000, "commission": 360000},
                {"tier": "超额档", "revenue": 2000000, "commission": 40000},
                {"tier": "达标档", "revenue": 1800000, "commission": 27000},
            ],
            "by_product": [
                {"product": "FCT", "revenue": 9500000, "commission": 285000},
                {"product": "EOL", "revenue": 4200000, "commission": 126000},
                {"product": "ICT", "revenue": 2100000, "commission": 45960},
            ],
        },
    }

    return commission_data


@router.get("/commission/rules", summary="提成规则")
def get_commission_rules(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取提成计算规则"""

    return {
        "commission_tiers": [
            {
                "tier_name": "基础档",
                "completion_range": "0% - 80%",
                "commission_rate": 1.0,
                "description": "未完成目标，基础提成",
            },
            {
                "tier_name": "达标档",
                "completion_range": "80% - 100%",
                "commission_rate": 1.5,
                "description": "完成目标，1.5 倍提成",
            },
            {
                "tier_name": "超额档",
                "completion_range": "100% - 120%",
                "commission_rate": 2.0,
                "description": "超额完成，2 倍提成",
            },
            {
                "tier_name": "卓越档",
                "completion_range": "120% 以上",
                "commission_rate": 3.0,
                "description": "卓越表现，3 倍提成",
            },
        ],
        "product_coefficients": [
            {"product": "FCT", "coefficient": 1.2, "reason": "高毛利产品"},
            {"product": "ICT", "coefficient": 1.0, "reason": "标准产品"},
            {"product": "EOL", "coefficient": 1.1, "reason": "中等毛利"},
            {"product": "VISION", "coefficient": 1.3, "reason": "战略产品"},
        ],
        "collection_rules": [
            {"status": "全额回款", "coefficient": 1.0},
            {"status": "部分回款", "coefficient": "按回款比例"},
            {"status": "未回款", "coefficient": 0, "note": "回款后发放"},
        ],
        "bonus_items": [
            {"name": "新人首单奖", "amount": 5000, "condition": "入职 3 个月内首单"},
            {"name": "大单奖", "amount": 10000, "condition": "单笔合同≥500 万"},
            {"name": "季度冠军奖", "amount": 20000, "condition": "季度业绩第一"},
            {"name": "年度冠军奖", "amount": 100000, "condition": "年度业绩第一"},
        ],
    }


# ========== 3. PK 对战系统 ==========


@router.get("/pk/battles", summary="PK 对战列表")
def get_pk_battles(
    status: Optional[str] = Query(None, description="状态：active/completed"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售 PK 对战列表

    类型：
    - 自由 PK（销售之间自愿发起）
    - 官方 PK（公司组织的 PK 活动）
    """

    battles = {
        "active_battles": [
            {
                "battle_id": 1,
                "type": "official",
                "title": "Q1 业绩 PK 赛",
                "period": "2025-Q1",
                "start_date": "2025-01-01",
                "end_date": "2025-03-31",
                "participants": [
                    {
                        "sales_id": 101,
                        "sales_name": "张三",
                        "current_revenue": 15800000,
                        "target": 10000000,
                        "completion_rate": 158.0,
                        "rank": 1,
                    },
                    {
                        "sales_id": 102,
                        "sales_name": "李四",
                        "current_revenue": 12500000,
                        "target": 10000000,
                        "completion_rate": 125.0,
                        "rank": 2,
                    },
                ],
                "prize": {
                    "first": {"name": "冠军奖", "amount": 20000},
                    "second": {"name": "亚军奖", "amount": 10000},
                    "third": {"name": "季军奖", "amount": 5000},
                },
                "days_remaining": 28,
            },
            {
                "battle_id": 2,
                "type": "free",
                "title": "张三 vs 王五 单挑赛",
                "period": "2025-02",
                "start_date": "2025-02-01",
                "end_date": "2025-02-29",
                "participants": [
                    {
                        "sales_id": 101,
                        "sales_name": "张三",
                        "current_revenue": 15800000,
                        "rank": 1,
                    },
                    {
                        "sales_id": 103,
                        "sales_name": "王五",
                        "current_revenue": 11200000,
                        "rank": 2,
                    },
                ],
                "bet": {"amount": 2000, "description": "输家请客吃饭"},
                "days_remaining": 3,
            },
        ],
        "completed_battles": [
            {
                "battle_id": 3,
                "type": "official",
                "title": "12 月业绩 PK 赛",
                "period": "2024-12",
                "winner": {
                    "sales_id": 101,
                    "sales_name": "张三",
                    "final_revenue": 12800000,
                },
                "runner_up": {
                    "sales_id": 102,
                    "sales_name": "李四",
                    "final_revenue": 11500000,
                },
                "prize_awarded": 20000,
            },
        ],
        "my_battles": [
            {
                "battle_id": 1,
                "title": "Q1 业绩 PK 赛",
                "my_rank": 1,
                "status": "leading",
                "days_remaining": 28,
            },
            {
                "battle_id": 2,
                "title": "张三 vs 王五 单挑赛",
                "my_rank": 1,
                "status": "leading",
                "days_remaining": 3,
            },
        ],
    }

    return battles


@router.post("/pk/challenge", summary="发起 PK 挑战")
def create_pk_challenge(
    challenger_id: int,
    challenged_id: int,
    bet_amount: Optional[int] = None,
    period: str = "monthly",
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """发起 PK 挑战"""

    return {
        "message": "PK 挑战已发送",
        "challenge_id": 123,
        "challenger_id": challenger_id,
        "challenged_id": challenged_id,
        "status": "pending",
        "bet_amount": bet_amount,
        "period": period,
    }


# ========== 4. 成就系统 ==========


@router.get("/achievements", summary="成就系统")
def get_achievements(
    sales_id: Optional[int] = Query(None, description="销售 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售成就系统

    成就类型：
    - 业绩成就（签单王、破纪录等）
    - 进步成就（最快进步等）
    - 技能成就（产品专家等）
    """

    achievements = {
        "sales_id": sales_id or 101,
        "sales_name": "张三",
        "total_achievements": 15,
        "total_points": 2850,
        "level": 8,
        "level_name": "销售精英",
        "next_level_points": 3500,
        "badges": [
            {
                "badge_id": 1,
                "name": "签单王",
                "description": "单月签单 10 笔以上",
                "icon": "🏆",
                "earned_date": "2025-01-15",
                "rarity": "gold",
                "points": 500,
            },
            {
                "badge_id": 2,
                "name": "破纪录者",
                "description": "单笔合同金额破纪录",
                "icon": "💎",
                "earned_date": "2025-02-10",
                "rarity": "diamond",
                "points": 800,
            },
            {
                "badge_id": 3,
                "name": "锂电专家",
                "description": "锂电行业签单 5 笔",
                "icon": "⚡",
                "earned_date": "2025-01-20",
                "rarity": "silver",
                "points": 300,
            },
            {
                "badge_id": 4,
                "name": "新人王",
                "description": "入职首月完成目标",
                "icon": "🌟",
                "earned_date": "2024-06-30",
                "rarity": "gold",
                "points": 400,
            },
            {
                "badge_id": 5,
                "name": "常胜将军",
                "description": "连续 3 个月业绩第一",
                "icon": "👑",
                "earned_date": "2025-02-28",
                "rarity": "platinum",
                "points": 850,
            },
        ],
        "progress": [
            {
                "achievement_name": "百万俱乐部",
                "description": "累计业绩破 1 亿",
                "current": 85000000,
                "target": 100000000,
                "progress": 85.0,
            },
            {
                "achievement_name": "百单达人",
                "description": "累计签单 100 笔",
                "current": 78,
                "target": 100,
                "progress": 78.0,
            },
        ],
        "recent_achievements": [
            {"name": "常胜将军", "earned_date": "2025-02-28", "points": 850},
            {"name": "破纪录者", "earned_date": "2025-02-10", "points": 800},
        ],
    }

    return achievements


# ========== 5. 激励方案 ==========


@router.get("/incentive-plans", summary="激励方案")
def get_incentive_plans(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取当前激励方案"""

    return {
        "active_plans": [
            {
                "plan_id": 1,
                "plan_name": "2026 年 Q1 冲刺计划",
                "period": "2026-Q1",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "description": "Q1 业绩冲刺，超额部分额外奖励",
                "rules": [
                    "完成率≥100%，额外奖励 5000 元",
                    "完成率≥120%，额外奖励 15000 元",
                    "完成率≥150%，额外奖励 30000 元",
                    "团队第一，额外奖励 10000 元",
                ],
                "participants_count": 45,
                "total_prize_pool": 500000,
            },
            {
                "plan_id": 2,
                "plan_name": "新品推广激励",
                "period": "2026-02",
                "description": "视觉检测设备推广专项激励",
                "rules": [
                    "每签单 1 台 VISION 设备，奖励 3000 元",
                    "月度 VISION 销冠，额外奖励 10000 元",
                ],
                "participants_count": 30,
                "total_prize_pool": 100000,
            },
        ],
        "my_incentives": [
            {
                "plan_name": "2026 年 Q1 冲刺计划",
                "current_progress": 158.0,
                "estimated_bonus": 30000,
                "status": "on_track",
            },
            {
                "plan_name": "新品推广激励",
                "current_progress": 2,
                "estimated_bonus": 6000,
                "status": "on_track",
            },
        ],
        "historical_rewards": [
            {"month": "2025-01", "plan": "12 月业绩 PK 赛", "amount": 20000, "status": "paid"},
            {"month": "2025-01", "plan": "新人王成就", "amount": 5000, "status": "paid"},
            {"month": "2024-12", "plan": "季度冠军奖", "amount": 20000, "status": "paid"},
        ],
        "total_earnings_ytd": 125000,
    }
