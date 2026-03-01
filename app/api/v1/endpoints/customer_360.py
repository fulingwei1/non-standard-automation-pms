# -*- coding: utf-8 -*-
"""
客户 360°画像 API
提供交互历史、决策链分析、健康度评分、购买偏好
"""

from typing import Any, Optional, List
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User

router = APIRouter()


# ========== 1. 客户交互历史时间线 ==========

@router.get("/customers/{customer_id}/timeline", summary="客户交互历史时间线")
def get_customer_timeline(
    customer_id: int = Path(..., description="客户 ID"),
    months: int = Query(6, description="查看月数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    客户完整交互历史时间线
    
    包含：
    - 电话/会议/邮件/微信记录
    - 商机阶段变更
    - 报价/合同/收款记录
    - 项目交付记录
    """
    
    # 模拟交互历史数据
    timeline = [
        {
            "date": "2025-02-28",
            "type": "meeting",
            "title": "技术方案评审会议",
            "participants": ["张三（技术总监）", "李四（采购经理）"],
            "outcome": "方案基本认可，需调整 2 处细节",
            "next_action": "3 月 5 日前提交修订版方案",
            "sentiment": "positive",
        },
        {
            "date": "2025-02-25",
            "type": "call",
            "title": "电话跟进",
            "participants": ["王五（销售）"],
            "outcome": "确认预算范围 300-350 万",
            "next_action": "准备正式报价",
            "sentiment": "neutral",
        },
        {
            "date": "2025-02-20",
            "type": "email",
            "title": "发送 FCT 方案 V1",
            "participants": [],
            "outcome": "已发送，待确认",
            "next_action": "跟进反馈",
            "sentiment": "neutral",
        },
        {
            "date": "2025-02-15",
            "type": "meeting",
            "title": "首次拜访",
            "participants": ["张三（技术总监）", "赵六（生产经理）"],
            "outcome": "了解需求，约定方案提交时间",
            "next_action": "准备技术方案",
            "sentiment": "positive",
        },
        {
            "date": "2025-02-10",
            "type": "call",
            "title": "初次电话接触",
            "participants": ["王五（销售）"],
            "outcome": "确认有 FCT 测试需求",
            "next_action": "安排拜访",
            "sentiment": "positive",
        },
    ]
    
    # 按时间排序
    timeline.sort(key=lambda x: x["date"], reverse=True)
    
    return {
        "customer_id": customer_id,
        "period_months": months,
        "total_interactions": len(timeline),
        "by_type": {
            "meeting": len([t for t in timeline if t["type"] == "meeting"]),
            "call": len([t for t in timeline if t["type"] == "call"]),
            "email": len([t for t in timeline if t["type"] == "email"]),
            "wechat": len([t for t in timeline if t["type"] == "wechat"]),
        },
        "sentiment_distribution": {
            "positive": len([t for t in timeline if t["sentiment"] == "positive"]),
            "neutral": len([t for t in timeline if t["sentiment"] == "neutral"]),
            "negative": len([t for t in timeline if t["sentiment"] == "negative"]),
        },
        "timeline": timeline,
        "last_contact": timeline[0]["date"] if timeline else None,
        "days_since_last_contact": (date.today() - date.fromisoformat(timeline[0]["date"])).days if timeline else 999,
    }


# ========== 2. 决策链分析 ==========

@router.get("/customers/{customer_id}/decision-chain", summary="决策链分析")
def get_decision_chain(
    customer_id: int = Path(..., description="客户 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    客户决策链分析
    
    识别：
    - 关键决策人（EB）
    - 技术决策人（TB）
    - 采购决策人（PB）
    - 最终用户（UB）
    - 教练/内线（Coach）
    """
    
    # 模拟决策链数据
    decision_chain = {
        "customer_id": customer_id,
        "customer_name": "宁德时代",
        "opportunity_name": "FCT 测试线项目",
        "contacts": [
            {
                "name": "张三",
                "title": "技术总监",
                "role": "TB",  # Technical Buyer 技术决策人
                "role_name": "技术决策人",
                "influence": "HIGH",
                "attitude": "supportive",  # supportive/neutral/resistant
                "contact_frequency": "weekly",
                "last_contact": "2025-02-28",
                "key_concerns": ["技术稳定性", "测试精度", "与现有设备兼容性"],
                "relationship_strength": 85,
            },
            {
                "name": "李四",
                "title": "采购经理",
                "role": "PB",  # Procurement Buyer 采购决策人
                "role_name": "采购决策人",
                "influence": "MEDIUM",
                "attitude": "neutral",
                "contact_frequency": "biweekly",
                "last_contact": "2025-02-25",
                "key_concerns": ["价格", "付款方式", "交付周期"],
                "relationship_strength": 60,
            },
            {
                "name": "王五",
                "title": "总经理",
                "role": "EB",  # Economic Buyer 经济决策人
                "role_name": "最终决策人",
                "influence": "HIGH",
                "attitude": "unknown",
                "contact_frequency": "monthly",
                "last_contact": "2025-01-15",
                "key_concerns": ["投资回报率", "产能提升", "品牌形象"],
                "relationship_strength": 40,
            },
            {
                "name": "赵六",
                "title": "生产经理",
                "role": "UB",  # User Buyer 最终用户
                "role_name": "最终用户",
                "influence": "MEDIUM",
                "attitude": "supportive",
                "contact_frequency": "weekly",
                "last_contact": "2025-02-20",
                "key_concerns": ["操作便捷性", "维护成本", "培训支持"],
                "relationship_strength": 75,
            },
            {
                "name": "钱七",
                "title": "设备工程师",
                "role": "Coach",  # 教练/内线
                "role_name": "内线",
                "influence": "LOW",
                "attitude": "supportive",
                "contact_frequency": "weekly",
                "last_contact": "2025-02-27",
                "key_concerns": ["技术细节", "实施难度"],
                "relationship_strength": 90,
            },
        ],
        "coverage_analysis": {
            "eb_covered": True,
            "tb_covered": True,
            "pb_covered": True,
            "ub_covered": True,
            "coach_identified": True,
            "coverage_score": 100,
        },
        "risk_analysis": {
            "risks": [
                {
                    "risk": "EB 接触不足",
                    "description": "与总经理王五关系强度仅 40%，需加强接触",
                    "severity": "MEDIUM",
                    "action": "安排高层拜访或技术交流",
                },
                {
                    "risk": "PB 态度不明",
                    "description": "采购经理李四态度中立，可能存在价格阻力",
                    "severity": "MEDIUM",
                    "action": "准备 TCO 分析，强调长期价值",
                },
            ],
            "overall_risk": "MEDIUM",
        },
        "recommended_actions": [
            "安排总经理级别拜访，建立 EB 关系",
            "邀请技术总监参观已交付项目",
            "与采购经理沟通付款方案灵活性",
            "保持与生产经理和内线的定期沟通",
        ],
    }
    
    return decision_chain


# ========== 3. 客户健康度评分 ==========

@router.get("/customers/{customer_id}/health-score", summary="客户健康度评分")
def get_customer_health_score(
    customer_id: int = Path(..., description="客户 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    客户健康度综合评分
    
    维度：
    - 互动活跃度（联系频率）
    - 关系深度（决策链覆盖）
    - 商机进展（阶段推进）
    - 满意度（交互情绪）
    """
    
    # 模拟健康度数据
    health_data = {
        "customer_id": customer_id,
        "customer_name": "宁德时代",
        "assessment_date": date.today().isoformat(),
        "overall_score": 78,
        "health_level": "GOOD",
        "health_trend": "improving",
        
        "dimensions": [
            {
                "name": "互动活跃度",
                "score": 85,
                "weight": 25,
                "metrics": {
                    "contact_frequency": "每周 2 次",
                    "last_contact_days_ago": 3,
                    "response_rate": "90%",
                    "meeting_count_30d": 4,
                },
                "status": "GOOD",
            },
            {
                "name": "关系深度",
                "score": 70,
                "weight": 25,
                "metrics": {
                    "decision_chain_coverage": "100%",
                    "eb_relationship": 40,
                    "tb_relationship": 85,
                    "coach_identified": True,
                },
                "status": "MEDIUM",
            },
            {
                "name": "商机进展",
                "score": 80,
                "weight": 30,
                "metrics": {
                    "current_stage": "STAGE3",
                    "days_in_current_stage": 10,
                    "stage_progression_rate": "正常",
                    "estimated_close_date": "2025-03-20",
                },
                "status": "GOOD",
            },
            {
                "name": "客户满意度",
                "score": 75,
                "weight": 20,
                "metrics": {
                    "positive_interactions": 8,
                    "neutral_interactions": 3,
                    "negative_interactions": 1,
                    "nps_score": 7,
                },
                "status": "GOOD",
            },
        ],
        
        "alerts": [
            {
                "type": "WARNING",
                "title": "EB 关系需加强",
                "description": "与最终决策人关系强度仅 40%",
                "suggested_action": "安排高层拜访",
            },
        ],
        
        "recommended_actions": [
            {
                "priority": 1,
                "action": "安排总经理级别拜访",
                "impact": "提升 EB 关系强度",
                "deadline": "2 周内",
            },
            {
                "priority": 2,
                "action": "邀请技术总监参观案例项目",
                "impact": "巩固 TB 支持",
                "deadline": "1 个月内",
            },
            {
                "priority": 3,
                "action": "准备 TCO 分析报告给采购",
                "impact": "降低价格阻力",
                "deadline": "1 周内",
            },
        ],
    }
    
    return health_data


# ========== 4. 购买偏好分析 ==========

@router.get("/customers/{customer_id}/buying-preferences", summary="购买偏好分析")
def get_buying_preferences(
    customer_id: int = Path(..., description="客户 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    客户购买偏好分析
    
    分析：
    - 产品类型偏好
    - 价格敏感度
    - 决策周期
    - 关键采购因素
    """
    
    preferences = {
        "customer_id": customer_id,
        "customer_name": "宁德时代",
        "analysis_date": date.today().isoformat(),
        
        "product_preferences": {
            "preferred_categories": [
                {"category": "FCT", "count": 3, "percentage": 60},
                {"category": "EOL", "count": 1, "percentage": 20},
                {"category": "ICT", "count": 1, "percentage": 20},
            ],
            "preferred_features": [
                "高精度测试",
                "模块化设计",
                "数据追溯功能",
                "与 MES 系统集成",
            ],
            "avoided_features": [
                "复杂操作界面",
                "长交付周期",
            ],
        },
        
        "price_sensitivity": {
            "level": "MEDIUM",
            "score": 60,
            "analysis": "关注价格但更重视价值，愿意为技术优势支付溢价",
            "typical_budget_range": {
                "min": 2500000,
                "max": 4000000,
                "currency": "CNY",
            },
            "price_negotiation_style": "理性谈判，注重数据支撑",
            "payment_preference": "标准 3:6:1 付款，可接受预付优惠",
        },
        
        "decision_pattern": {
            "avg_decision_cycle_days": 45,
            "decision_speed": "MEDIUM",
            "key_decision_factors": [
                {"factor": "技术实力", "weight": 35},
                {"factor": "行业案例", "weight": 25},
                {"factor": "价格", "weight": 20},
                {"factor": "交付周期", "weight": 15},
                {"factor": "售后服务", "weight": 5},
            ],
            "procurement_process": "技术评审→商务谈判→高层审批",
        },
        
        "relationship_preferences": {
            "communication_style": "正式 + 专业",
            "preferred_contact_method": "会议 > 电话 > 微信 > 邮件",
            "meeting_frequency": "每周 1-2 次",
            "technical_depth": "深入，需要详细技术方案",
        },
        
        "historical_insights": {
            "total_projects": 5,
            "won_projects": 3,
            "lost_projects": 2,
            "win_rate": 60,
            "avg_project_value": 3200000,
            "total_revenue": 9600000,
            "last_project_date": "2024-11-15",
        },
        
        "recommended_approach": [
            "强调技术优势和锂电行业案例",
            "提供详细的技术方案和测试数据",
            "准备 TCO 分析支撑价格",
            "安排已交付客户参观",
            "保持每周定期沟通节奏",
        ],
    }
    
    return preferences


# ========== 5. 客户 360°总览 ==========

@router.get("/customers/{customer_id}/360-view", summary="客户 360°总览")
def get_customer_360_view(
    customer_id: int = Path(..., description="客户 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    客户 360°完整视图
    
    整合所有客户信息于一页
    """
    
    return {
        "customer_id": customer_id,
        "customer_name": "宁德时代",
        "industry": "锂电",
        "customer_type": "大客户",
        "customer_level": "A",
        
        "basic_info": {
            "established": "2011 年",
            "employees": "50000+",
            "revenue": "3000 亿+",
            "location": "福建宁德",
            "website": "www.catl.com",
        },
        
        "relationship_summary": {
            "first_contact": "2024-06-15",
            "relationship_duration_days": 260,
            "total_interactions": 45,
            "last_contact": "2025-02-28",
            "days_since_last_contact": 3,
            "health_score": 78,
            "health_level": "GOOD",
        },
        
        "active_opportunities": [
            {
                "id": 101,
                "name": "FCT 测试线项目",
                "stage": "STAGE3",
                "estimated_amount": 3500000,
                "win_rate": 70,
                "estimated_close": "2025-03-20",
            },
        ],
        
        "historical_projects": [
            {
                "name": "EOL 测试设备",
                "value": 2800000,
                "status": "已完成",
                "completion_date": "2024-11-15",
                "satisfaction": "高",
            },
        ],
        
        "key_contacts": [
            {"name": "张三", "title": "技术总监", "role": "TB", "relationship": 85},
            {"name": "李四", "title": "采购经理", "role": "PB", "relationship": 60},
            {"name": "王五", "title": "总经理", "role": "EB", "relationship": 40},
        ],
        
        "quick_actions": [
            {"action": "安排 EB 拜访", "priority": "HIGH", "deadline": "2 周内"},
            {"action": "提交修订方案", "priority": "HIGH", "deadline": "3 月 5 日"},
            {"action": "准备 TCO 分析", "priority": "MEDIUM", "deadline": "1 周内"},
        ],
        
        "alerts": [
            {"type": "WARNING", "message": "EB 关系需加强"},
            {"type": "INFO", "message": "方案修订截止 3 月 5 日"},
        ],
    }
