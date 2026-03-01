# -*- coding: utf-8 -*-
"""
销售与客户商务关系成熟度模型
评估关系深度，预测赢单概率
"""

from typing import Any, Optional, List, Dict
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User

router = APIRouter()


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
                    "EB_covered": {"name": "最终决策人", "score": 5, "criteria": "已建立联系并深入沟通"},
                    "TB_covered": {"name": "技术决策人", "score": 5, "criteria": "技术认可，支持方案"},
                    "PB_covered": {"name": "采购决策人", "score": 4, "criteria": "商务条件已沟通"},
                    "UB_covered": {"name": "最终用户", "score": 3, "criteria": "用户使用意愿强"},
                    "Coach_identified": {"name": "内线/教练", "score": 3, "criteria": "有内部支持者"},
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
                    "L1_stranger": {"name": "陌生", "score": 4, "description": "刚接触，相互了解有限"},
                    "L2_contact": {"name": "接触", "score": 8, "description": "建立联系，保持沟通"},
                    "L3_recognition": {"name": "认可", "score": 12, "description": "认可专业能力，愿意交流"},
                    "L4_trust": {"name": "信任", "score": 16, "description": "深度信任，分享内部信息"},
                    "L5_partnership": {"name": "伙伴", "score": 20, "description": "战略合作伙伴，排他支持"},
                },
            },
            {
                "id": 4,
                "name": "信息获取度",
                "weight": 15,
                "description": "客户内部信息掌握程度",
                "scoring": {
                    "budget_clear": {"name": "预算明确", "score": 4, "criteria": "知道具体预算范围"},
                    "decision_process": {"name": "决策流程", "score": 4, "criteria": "清楚决策流程和关键节点"},
                    "timeline": {"name": "时间表", "score": 3, "criteria": "了解项目时间计划"},
                    "competitor_info": {"name": "竞品信息", "score": 2, "criteria": "知道参与竞品情况"},
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
                    "neutral_impact": {"name": "中立影响", "penalty": -5, "description": "关键人持中立态度"},
                    "opponent_impact": {"name": "反对影响", "penalty": -10, "description": "有关键人反对我们"},
                },
            },
            {
                "id": 6,
                "name": "高层互动",
                "weight": 10,
                "description": "双方高层互动情况",
                "scoring": {
                    "ceo_meeting": {"name": "CEO 互访", "score": 10, "criteria": "双方 CEO/总经理会面"},
                    "vp_meeting": {"name": "VP 级交流", "score": 7, "criteria": "副总裁/总监级交流"},
                    "director_meeting": {"name": "总监级交流", "score": 4, "criteria": "部门总监级交流"},
                    "working_level": {"name": "工作层交流", "score": 2, "criteria": "仅工作层面对接"},
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
    
    assessment = {
        "customer_id": customer_id,
        "customer_name": "宁德时代",
        "opportunity_id": opportunity_id,
        "opportunity_name": "FCT 测试线项目",
        "assessment_date": date.today().isoformat(),
        
        # 各维度得分
        "dimension_scores": {
            "decision_chain": {
                "name": "决策链覆盖度",
                "weight": 20,
                "score": 16,
                "max_score": 20,
                "details": {
                    "EB": {"covered": True, "name": "王五 - 总经理", "relationship": 70, "score": 4},
                    "TB": {"covered": True, "name": "张三 - 技术总监", "relationship": 85, "score": 5},
                    "PB": {"covered": True, "name": "李四 - 采购经理", "relationship": 60, "score": 3},
                    "UB": {"covered": True, "name": "赵六 - 生产经理", "relationship": 75, "score": 3},
                    "Coach": {"covered": True, "name": "钱七 - 设备工程师", "relationship": 90, "score": 3},
                },
                "gap_analysis": "PB 关系需加强（当前 60 分，目标 80 分）",
            },
            "interaction_frequency": {
                "name": "互动频率",
                "weight": 15,
                "score": 12,
                "max_score": 15,
                "details": {
                    "last_7_days": 3,
                    "last_30_days": 12,
                    "avg_per_week": 2.8,
                    "contact_methods": {
                        "visit": 5,
                        "call": 8,
                        "wechat": 15,
                        "email": 3,
                        "meeting": 4,
                    },
                },
                "level": "每周 2 次以上",
            },
            "relationship_depth": {
                "name": "关系深度",
                "weight": 20,
                "score": 14,
                "max_score": 20,
                "level": "L4 - 信任",
                "evidence": [
                    "客户主动分享内部信息",
                    "技术总监支持我们的方案",
                    "邀请参与前期规划",
                ],
                "next_level_requirement": "需要达成战略合作，获得排他支持",
            },
            "information_access": {
                "name": "信息获取度",
                "weight": 15,
                "score": 13,
                "max_score": 15,
                "details": {
                    "budget": {"known": True, "value": "300-350 万", "score": 4},
                    "decision_process": {"known": True, "process": "技术评审→商务谈判→高层审批", "score": 4},
                    "timeline": {"known": True, "deadline": "2025-03-31", "score": 3},
                    "competitors": {"known": True, "list": ["竞品 A", "竞品 B"], "score": 2},
                    "pain_points": {"known": True, "points": ["测试精度", "交付周期"], "score": 2},
                },
            },
            "support_level": {
                "name": "支持度",
                "weight": 20,
                "score": 16,
                "max_score": 20,
                "details": {
                    "EB": {"attitude": "neutral", "score": 4},
                    "TB": {"attitude": "supportive", "score": 6},
                    "PB": {"attitude": "neutral", "score": 2},
                    "UB": {"attitude": "supportive", "score": 2},
                    "internal_champion": True,
                },
                "risks": ["EB 态度中立，需争取支持", "PB 可能倾向竞品"],
            },
            "executive_engagement": {
                "name": "高层互动",
                "weight": 10,
                "score": 7,
                "max_score": 10,
                "level": "VP 级交流",
                "history": [
                    {"date": "2025-01-15", "event": "我司副总拜访客户技术副总"},
                    {"date": "2024-11-20", "event": "邀请客户总监参观公司"},
                ],
                "next_step": "安排 CEO 互访，提升至 CEO 级别",
            },
        },
        
        # 总体评估
        "overall_assessment": {
            "total_score": 78,
            "max_score": 100,
            "maturity_level": "L4",
            "maturity_level_name": "战略级",
            "estimated_win_rate": 72,
            "confidence": 85,
            "trend": "improving",
            "score_change_30d": 5,
        },
        
        # 雷达图数据
        "radar_data": [
            {"dimension": "决策链", "score": 16, "max": 20, "percentage": 80},
            {"dimension": "互动频率", "score": 12, "max": 15, "percentage": 80},
            {"dimension": "关系深度", "score": 14, "max": 20, "percentage": 70},
            {"dimension": "信息获取", "score": 13, "max": 15, "percentage": 87},
            {"dimension": "支持度", "score": 16, "max": 20, "percentage": 80},
            {"dimension": "高层互动", "score": 7, "max": 10, "percentage": 70},
        ],
        
        # 改进建议
        "improvement_recommendations": [
            {
                "priority": 1,
                "dimension": "支持度",
                "current_score": 16,
                "target_score": 20,
                "action": "争取 EB（总经理）明确支持",
                "specific_actions": [
                    "安排我司 CEO 拜访客户总经理",
                    "准备高层交流会议题",
                    "强调战略合作价值",
                ],
                "expected_impact": "+4 分，赢单率提升 5%",
                "deadline": "2 周内",
            },
            {
                "priority": 2,
                "dimension": "关系深度",
                "current_score": 14,
                "target_score": 18,
                "action": "从信任级提升至伙伴级",
                "specific_actions": [
                    "签署战略合作协议",
                    "邀请参与产品联合开发",
                    "提供 VIP 服务支持",
                ],
                "expected_impact": "+4 分，赢单率提升 3%",
                "deadline": "1 个月内",
            },
            {
                "priority": 3,
                "dimension": "高层互动",
                "current_score": 7,
                "target_score": 10,
                "action": "提升至 CEO 级别互动",
                "specific_actions": [
                    "安排双方 CEO 会面",
                    "签署合作备忘录",
                ],
                "expected_impact": "+3 分，赢单率提升 2%",
                "deadline": "1 个月内",
            },
        ],
        
        # 风险预警
        "risk_alerts": [
            {
                "type": "WARNING",
                "title": "PB 态度中立",
                "description": "采购经理李四态度中立，可能倾向竞品",
                "impact": "可能影响价格谈判",
                "mitigation": "准备 TCO 分析，强调长期价值",
            },
            {
                "type": "INFO",
                "title": "EB 未明确支持",
                "description": "总经理王五尚未明确表态支持",
                "impact": "决策阶段可能存在变数",
                "mitigation": "安排高层拜访，争取支持",
            },
        ],
        
        # 历史趋势
        "historical_trend": [
            {"date": "2024-12-01", "score": 65, "level": "L3"},
            {"date": "2025-01-01", "score": 70, "level": "L3"},
            {"date": "2025-02-01", "score": 73, "level": "L4"},
            {"date": "2025-03-01", "score": 78, "level": "L4"},
        ],
    }
    
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
                    {"action": "拜访采购经理李四", "owner": "销售经理", "expected_outcome": "了解采购关注点"},
                    {"action": "与技术总监深度交流", "owner": "技术总监", "expected_outcome": "获得技术认可"},
                ],
            },
            {
                "week": 2,
                "focus": "高层互动",
                "actions": [
                    {"action": "安排 CEO 互访", "owner": "CEO", "expected_outcome": "建立高层关系"},
                    {"action": "准备战略合作方案", "owner": "销售总监", "expected_outcome": "明确合作价值"},
                ],
            },
            {
                "week": 3,
                "focus": "深化信任",
                "actions": [
                    {"action": "提供行业洞察报告", "owner": "市场部", "expected_outcome": "展示专业能力"},
                    {"action": "邀请参观标杆项目", "owner": "销售经理", "expected_outcome": "增强信心"},
                ],
            },
            {
                "week": 4,
                "focus": "锁定支持",
                "actions": [
                    {"action": "获取书面支持意向", "owner": "销售经理", "expected_outcome": "锁定支持"},
                    {"action": "敲定合作细节", "owner": "商务", "expected_outcome": "推进签约"},
                ],
            },
        ],
        
        "milestones": [
            {"week": 2, "target_score": current_score + gap * 0.3, "description": "完成高层互访"},
            {"week": 4, "target_score": target_score, "description": "达成战略合作"},
        ],
        
        "success_metrics": [
            "EB 明确表态支持",
            "签署战略合作协议",
            "获得排他性承诺",
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
    
    portfolio = {
        "total_customers": 45,
        "assessment_date": date.today().isoformat(),
        
        # 成熟度分布
        "maturity_distribution": {
            "L1_initial": {"count": 8, "percentage": 17.8, "avg_win_rate": 15},
            "L2_developing": {"count": 15, "percentage": 33.3, "avg_win_rate": 35},
            "L3_mature": {"count": 12, "percentage": 26.7, "avg_win_rate": 55},
            "L4_strategic": {"count": 7, "percentage": 15.6, "avg_win_rate": 75},
            "L5_partnership": {"count": 3, "percentage": 6.7, "avg_win_rate": 90},
        },
        
        # 健康度评估
        "health_assessment": {
            "healthy_count": 22,  # L3+
            "healthy_percentage": 48.9,
            "at_risk_count": 23,  # L1/L2
            "at_risk_percentage": 51.1,
            "overall_health_score": 62,
        },
        
        # 重点客户列表
        "key_accounts": [
            {
                "customer_id": 1,
                "customer_name": "宁德时代",
                "maturity_level": "L4",
                "score": 78,
                "revenue_potential": 50000000,
                "trend": "improving",
                "strategic_value": "HIGH",
            },
            {
                "customer_id": 2,
                "customer_name": "比亚迪",
                "maturity_level": "L4",
                "score": 82,
                "revenue_potential": 40000000,
                "trend": "stable",
                "strategic_value": "HIGH",
            },
            {
                "customer_id": 3,
                "customer_name": "中创新航",
                "maturity_level": "L3",
                "score": 65,
                "revenue_potential": 30000000,
                "trend": "improving",
                "strategic_value": "MEDIUM",
            },
        ],
        
        # 需要关注的客户
        "needs_attention": [
            {
                "customer_id": 10,
                "customer_name": "欣旺达",
                "maturity_level": "L2",
                "score": 42,
                "revenue_potential": 25000000,
                "issue": "高潜力但关系成熟度低",
                "recommended_action": "增加拜访频率，识别关键人",
            },
            {
                "customer_id": 11,
                "customer_name": "蜂巢能源",
                "maturity_level": "L2",
                "score": 38,
                "revenue_potential": 20000000,
                "issue": "决策链不完整",
                "recommended_action": "识别 EB/TB，建立联系",
            },
        ],
        
        # 改进建议
        "strategic_recommendations": [
            {
                "priority": 1,
                "action": "提升 L2 客户至 L3",
                "target_customers": 15,
                "expected_impact": "整体赢单率提升 15%",
                "resources_needed": "增加销售拜访，技术支持",
            },
            {
                "priority": 2,
                "action": "巩固 L4 客户关系",
                "target_customers": 7,
                "expected_impact": "防止竞品挖角，锁定 75% 赢单率",
                "resources_needed": "高层互访，战略合作",
            },
            {
                "priority": 3,
                "action": "培育 L1 客户成长",
                "target_customers": 8,
                "expected_impact": "建立 pipeline，长期价值",
                "resources_needed": "基础拜访，需求调研",
            },
        ],
    }
    
    return portfolio
