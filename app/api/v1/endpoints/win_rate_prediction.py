# -*- coding: utf-8 -*-
"""
赢单率综合预测模型
多因素评估：商务关系 + 技术方案 + 价格竞争力 + 其他因素
"""

from typing import Any, Optional, List, Dict
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User

router = APIRouter()


# ========== 1. 综合赢单率预测模型 ==========

@router.get("/win-rate/comprehensive-model", summary="综合赢单率预测模型")
def get_comprehensive_win_rate_model(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    综合赢单率预测模型
    
    4 大核心因素：
    1. 商务关系成熟度 (35%) - 决策链/互动/关系深度/支持度
    2. 技术方案匹配度 (30%) - 需求覆盖/技术优势/案例背书
    3. 价格竞争力 (25%) - 价格水平/性价比/付款方式
    4. 其他因素 (10%) - 品牌/交付能力/售后服务
    
    计算公式：
    综合赢单率 = 商务关系×35% + 技术方案×30% + 价格竞争力×25% + 其他×10%
    """
    
    model = {
        "model_name": "综合赢单率预测模型 v1.0",
        "version": "1.0",
        "created_date": date.today().isoformat(),
        
        "formula": {
            "description": "加权平均计算",
            "calculation": "商务关系×35% + 技术方案×30% + 价格竞争力×25% + 其他×10%",
            "weights": {
                "business_relationship": {"weight": 0.35, "description": "商务关系成熟度"},
                "technical_solution": {"weight": 0.30, "description": "技术方案匹配度"},
                "price_competitiveness": {"weight": 0.25, "description": "价格竞争力"},
                "other_factors": {"weight": 0.10, "description": "其他因素"},
            },
        },
        
        # ========== 因素 1: 商务关系成熟度 (35%) ==========
        "business_relationship": {
            "weight": 35,
            "max_score": 100,
            "dimensions": [
                {"name": "决策链覆盖", "weight": 20, "description": "EB/TB/PB/UB/Coach"},
                {"name": "互动频率", "weight": 15, "description": "联系密度"},
                {"name": "关系深度", "weight": 20, "description": "L1 陌生→L5 伙伴"},
                {"name": "信息获取", "weight": 15, "description": "预算/流程/竞品"},
                {"name": "支持度", "weight": 20, "description": "关键人态度"},
                {"name": "高层互动", "weight": 10, "description": "CEO/VP 级交流"},
            ],
            "scoring_example": {
                "customer": "宁德时代",
                "scores": {
                    "decision_chain": 80,
                    "interaction": 80,
                    "relationship_depth": 70,
                    "information": 87,
                    "support": 80,
                    "executive": 70,
                },
                "weighted_score": 78,
                "contribution_to_win_rate": 78 * 0.35,  # 27.3%
            },
        },
        
        # ========== 因素 2: 技术方案匹配度 (30%) ==========
        "technical_solution": {
            "weight": 30,
            "max_score": 100,
            "dimensions": [
                {
                    "name": "需求覆盖度",
                    "weight": 30,
                    "description": "技术规格书要求覆盖比例",
                    "scoring": {
                        "full_coverage": {"range": "≥95%", "score": 100},
                        "high_coverage": {"range": "85-94%", "score": 80},
                        "medium_coverage": {"range": "70-84%", "score": 60},
                        "low_coverage": {"range": "<70%", "score": 40},
                    },
                },
                {
                    "name": "技术优势",
                    "weight": 25,
                    "description": "相比竞品的技术亮点",
                    "scoring": {
                        "significant_advantage": {"description": "显著领先", "score": 100},
                        "moderate_advantage": {"description": "适度领先", "score": 75},
                        "parity": {"description": "与竞品相当", "score": 50},
                        "disadvantage": {"description": "落后竞品", "score": 25},
                    },
                },
                {
                    "name": "案例背书",
                    "weight": 20,
                    "description": "同行业标杆案例",
                    "scoring": {
                        "multiple_flagship": {"description": "多个标杆案例", "score": 100},
                        "one_flagship": {"description": "1 个标杆案例", "score": 75},
                        "similar_cases": {"description": "类似案例", "score": 50},
                        "no_cases": {"description": "无相关案例", "score": 25},
                    },
                },
                {
                    "name": "定制化能力",
                    "weight": 15,
                    "description": "满足特殊需求的能力",
                    "scoring": {
                        "full_custom": {"description": "完全定制", "score": 100},
                        "partial_custom": {"description": "部分定制", "score": 70},
                        "standard_only": {"description": "仅标准方案", "score": 40},
                    },
                },
                {
                    "name": "技术团队实力",
                    "weight": 10,
                    "description": "客户对技术团队的认可",
                    "scoring": {
                        "highly_recognized": {"description": "高度认可", "score": 100},
                        "recognized": {"description": "认可", "score": 75},
                        "neutral": {"description": "中立", "score": 50},
                        "concerns": {"description": "有顾虑", "score": 25},
                    },
                },
            ],
            "scoring_example": {
                "opportunity": "FCT 测试线项目",
                "scores": {
                    "requirement_coverage": 90,  # 覆盖 92%
                    "technical_advantage": 75,   # 适度领先
                    "case_references": 75,       # 1 个标杆案例
                    "customization": 70,         # 部分定制
                    "team_recognition": 80,      # 认可
                },
                "weighted_score": 81,
                "contribution_to_win_rate": 81 * 0.30,  # 24.3%
            },
        },
        
        # ========== 因素 3: 价格竞争力 (25%) ==========
        "price_competitiveness": {
            "weight": 25,
            "max_score": 100,
            "dimensions": [
                {
                    "name": "价格水平",
                    "weight": 40,
                    "description": "相比竞品的价格位置",
                    "scoring": {
                        "lowest": {"range": "最低", "score": 100},
                        "below_average": {"range": "低于平均 10-20%", "score": 75},
                        "average": {"range": "市场平均", "score": 50},
                        "above_average": {"range": "高于平均 10-20%", "score": 25},
                        "highest": {"range": "最高", "score": 0},
                    },
                },
                {
                    "name": "性价比",
                    "weight": 30,
                    "description": "性能/价格比",
                    "scoring": {
                        "excellent": {"description": "性价比极高", "score": 100},
                        "good": {"description": "性价比好", "score": 75},
                        "fair": {"description": "性价比一般", "score": 50},
                        "poor": {"description": "性价比差", "score": 25},
                    },
                },
                {
                    "name": "付款方式",
                    "weight": 20,
                    "description": "付款条件灵活性",
                    "scoring": {
                        "very_flexible": {"description": "非常灵活", "score": 100},
                        "flexible": {"description": "灵活", "score": 75},
                        "standard": {"description": "标准条款", "score": 50},
                        "rigid": {"description": "僵化", "score": 25},
                    },
                },
                {
                    "name": "总拥有成本 (TCO)",
                    "weight": 10,
                    "description": "全生命周期成本优势",
                    "scoring": {
                        "significant_advantage": {"description": "显著优势", "score": 100},
                        "moderate_advantage": {"description": "适度优势", "score": 75},
                        "parity": {"description": "相当", "score": 50},
                        "disadvantage": {"description": "劣势", "score": 25},
                    },
                },
            ],
            "scoring_example": {
                "opportunity": "FCT 测试线项目",
                "scores": {
                    "price_level": 50,      # 市场平均
                    "cost_performance": 75,  # 性价比好
                    "payment_terms": 75,     # 灵活
                    "tco": 75,               # 适度优势
                },
                "weighted_score": 66,
                "contribution_to_win_rate": 66 * 0.25,  # 16.5%
            },
        },
        
        # ========== 因素 4: 其他因素 (10%) ==========
        "other_factors": {
            "weight": 10,
            "max_score": 100,
            "dimensions": [
                {
                    "name": "品牌影响力",
                    "weight": 30,
                    "description": "品牌知名度和美誉度",
                },
                {
                    "name": "交付能力",
                    "weight": 30,
                    "description": "交期保证和产能",
                },
                {
                    "name": "售后服务",
                    "weight": 25,
                    "description": "售后响应和支持",
                },
                {
                    "name": "合作历史",
                    "weight": 15,
                    "description": "过往合作经验",
                },
            ],
            "scoring_example": {
                "opportunity": "FCT 测试线项目",
                "scores": {
                    "brand": 70,
                    "delivery": 80,
                    "after_sales": 75,
                    "history": 60,
                },
                "weighted_score": 72,
                "contribution_to_win_rate": 72 * 0.10,  # 7.2%
            },
        },
        
        # ========== 综合计算示例 ==========
        "comprehensive_example": {
            "opportunity": "宁德时代 FCT 测试线项目",
            "factors": {
                "business_relationship": {"score": 78, "weight": 0.35, "contribution": 27.3},
                "technical_solution": {"score": 81, "weight": 0.30, "contribution": 24.3},
                "price_competitiveness": {"score": 66, "weight": 0.25, "contribution": 16.5},
                "other_factors": {"score": 72, "weight": 0.10, "contribution": 7.2},
            },
            "total_win_rate": 75.3,
            "confidence_level": 85,
            "recommendation": "重点跟进，赢单率 75%，建议加强价格谈判",
        },
        
        # ========== 赢单率分级 ==========
        "win_rate_levels": {
            "very_high": {"range": "≥80%", "action": "锁定赢单，防止意外"},
            "high": {"range": "60-79%", "action": "重点跟进，巩固优势"},
            "medium": {"range": "40-59%", "action": "找出短板，针对性改进"},
            "low": {"range": "20-39%", "action": "评估投入产出比"},
            "very_low": {"range": "<20%", "action": "考虑放弃或战略投入"},
        },
    }
    
    return model


# ========== 2. 商机赢单率评估 ==========

@router.get("/win-rate/opportunity/{opportunity_id}/assess", summary="商机赢单率评估")
def assess_opportunity_win_rate(
    opportunity_id: int = Path(..., description="商机 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    评估特定商机的赢单率
    
    返回：
    - 4 大因素得分
    - 综合赢单率
    - 短板分析
    - 改进建议
    """
    
    assessment = {
        "opportunity_id": opportunity_id,
        "opportunity_name": "宁德时代 FCT 测试线项目",
        "customer_name": "宁德时代",
        "estimated_amount": 3500000,
        "expected_close_date": "2026-03-31",
        "assessment_date": date.today().isoformat(),
        
        # ========== 4 大因素详细评估 ==========
        "factors_assessment": {
            "business_relationship": {
                "name": "商务关系",
                "weight": 35,
                "score": 78,
                "level": "L4 战略级",
                "strengths": [
                    "与技术总监关系深厚（85 分）",
                    "有内部教练支持（90 分）",
                    "每周互动 2.8 次，频率良好",
                ],
                "weaknesses": [
                    "总经理（EB）态度中立，需争取",
                    "采购经理可能倾向竞品",
                ],
                "improvement_actions": [
                    "安排 CEO 互访，争取 EB 支持",
                    "准备 TCO 分析，说服采购",
                ],
            },
            "technical_solution": {
                "name": "技术方案",
                "weight": 30,
                "score": 81,
                "level": "优秀",
                "strengths": [
                    "需求覆盖度 92%，超出竞品",
                    "测试精度领先竞品 15%",
                    "有比亚迪标杆案例背书",
                ],
                "weaknesses": [
                    "交付周期比竞品长 2 周",
                ],
                "improvement_actions": [
                    "提供加急交付方案",
                    "强调精度优势带来的长期价值",
                ],
            },
            "price_competitiveness": {
                "name": "价格竞争力",
                "weight": 25,
                "score": 66,
                "level": "中等",
                "strengths": [
                    "性价比好（性能/价格比高）",
                    "付款方式灵活",
                    "TCO 有优势（能耗低 20%）",
                ],
                "weaknesses": [
                    "报价比竞品 A 高 8%",
                    "客户预算有限",
                ],
                "improvement_actions": [
                    "准备价格分解，强调价值",
                    "提供分期付款选项",
                    "计算 3 年 TCO 对比",
                ],
            },
            "other_factors": {
                "name": "其他因素",
                "weight": 10,
                "score": 72,
                "level": "良好",
                "strengths": [
                    "交付能力可靠（80 分）",
                    "售后服务响应快（75 分）",
                ],
                "weaknesses": [
                    "品牌知名度不如竞品 A",
                    "与该客户合作历史短",
                ],
                "improvement_actions": [
                    "提供标杆客户参观",
                    "强调服务响应速度",
                ],
            },
        },
        
        # ========== 综合计算 ==========
        "comprehensive_calculation": {
            "business_relationship": {"score": 78, "weight": 0.35, "contribution": 27.3},
            "technical_solution": {"score": 81, "weight": 0.30, "contribution": 24.3},
            "price_competitiveness": {"score": 66, "weight": 0.25, "contribution": 16.5},
            "other_factors": {"score": 72, "weight": 0.10, "contribution": 7.2},
            "total_win_rate": 75.3,
            "rounded_win_rate": 75,
        },
        
        # ========== 赢单率分级 ==========
        "win_rate_classification": {
            "level": "high",
            "range": "60-79%",
            "description": "重点跟进，巩固优势",
            "confidence": 85,
        },
        
        # ========== 雷达图数据 ==========
        "radar_data": [
            {"factor": "商务关系", "score": 78, "max": 100, "percentage": 78},
            {"factor": "技术方案", "score": 81, "max": 100, "percentage": 81},
            {"factor": "价格竞争力", "score": 66, "max": 100, "percentage": 66},
            {"factor": "其他因素", "score": 72, "max": 100, "percentage": 72},
        ],
        
        # ========== 短板分析 ==========
        "weakness_analysis": {
            "primary_weakness": {
                "factor": "价格竞争力",
                "score": 66,
                "gap_to_best": 15,  # 比技术方案低 15 分
                "impact": "影响赢单率约 3.75%（15×25%）",
                "root_causes": [
                    "报价比竞品 A 高 8%",
                    "客户预算紧张",
                ],
            },
            "secondary_weakness": {
                "factor": "其他因素",
                "score": 72,
                "gap_to_best": 9,
                "impact": "影响赢单率约 0.9%（9×10%）",
                "root_causes": [
                    "品牌知名度不如竞品",
                    "合作历史短",
                ],
            },
        },
        
        # ========== 改进建议（按优先级） ==========
        "improvement_recommendations": [
            {
                "priority": 1,
                "factor": "价格竞争力",
                "current_score": 66,
                "target_score": 75,
                "expected_win_rate_increase": 2.25,  # (75-66)×25%
                "actions": [
                    {
                        "action": "准备价值导向的价格分解",
                        "description": "将 350 万分解到 5 年使用周期，每天成本仅 1900 元",
                        "owner": "销售经理",
                        "deadline": "1 周内",
                    },
                    {
                        "action": "提供 TCO 对比分析",
                        "description": "强调能耗低 20%，3 年节省电费 42 万",
                        "owner": "技术支持",
                        "deadline": "1 周内",
                    },
                    {
                        "action": "提供分期付款方案",
                        "description": "30% 首付 +40% 发货 +30% 验收，减轻客户资金压力",
                        "owner": "商务",
                        "deadline": "3 天内",
                    },
                ],
            },
            {
                "priority": 2,
                "factor": "商务关系",
                "current_score": 78,
                "target_score": 85,
                "expected_win_rate_increase": 2.45,  # (85-78)×35%
                "actions": [
                    {
                        "action": "安排 CEO 互访",
                        "description": "我司 CEO 拜访客户总经理，争取 EB 支持",
                        "owner": "CEO/销售总监",
                        "deadline": "2 周内",
                    },
                    {
                        "action": "邀请参观比亚迪标杆项目",
                        "description": "增强客户信心，展示成功案例",
                        "owner": "销售经理",
                        "deadline": "2 周内",
                    },
                ],
            },
            {
                "priority": 3,
                "factor": "其他因素",
                "current_score": 72,
                "target_score": 78,
                "expected_win_rate_increase": 0.6,  # (78-72)×10%
                "actions": [
                    {
                        "action": "提供快速响应承诺",
                        "description": "2 小时响应，24 小时到场，弥补品牌劣势",
                        "owner": "售后总监",
                        "deadline": "1 周内",
                    },
                ],
            },
        ],
        
        # ========== 预计结果 ==========
        "projected_outcome": {
            "current_win_rate": 75,
            "if_all_improvements": 81,  # 75 + 2.25 + 2.45 + 0.6
            "potential_increase": 6,
            "estimated_revenue": 3500000,
            "expected_revenue": 3500000 * 0.75,  # 262.5 万
            "if_improved_revenue": 3500000 * 0.81,  # 283.5 万
            "revenue_upside": 210000,  # 21 万
        },
        
        # ========== 风险预警 ==========
        "risk_alerts": [
            {
                "type": "WARNING",
                "title": "价格劣势",
                "description": "报价比竞品 A 高 8%，客户预算紧张",
                "impact": "可能导致输单",
                "mitigation": "强调 TCO 优势，提供分期付款",
            },
            {
                "type": "WARNING",
                "title": "EB 态度未定",
                "description": "总经理尚未明确支持",
                "impact": "决策阶段可能生变",
                "mitigation": "安排高层拜访，争取支持",
            },
            {
                "type": "INFO",
                "title": "交付周期较长",
                "description": "比竞品长 2 周",
                "impact": "可能影响客户选择",
                "mitigation": "提供加急方案，强调质量优先",
            },
        ],
    }
    
    return assessment


# ========== 3. 多商机对比 ==========

@router.get("/win-rate/portfolio-comparison", summary="多商机赢单率对比")
def get_portfolio_win_rate_comparison(
    team_id: Optional[int] = Query(None, description="团队 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    对比多个商机的赢单率
    
    帮助领导了解整体 pipeline 健康度
    """
    
    comparison = {
        "assessment_date": date.today().isoformat(),
        "total_opportunities": 28,
        "total_pipeline_value": 125000000,
        "weighted_pipeline_value": 68500000,  # 金额×赢单率
        
        # 赢单率分布
        "win_rate_distribution": {
            "very_high_80plus": {"count": 3, "value": 12000000, "percentage": 10.7},
            "high_60_79": {"count": 8, "value": 35000000, "percentage": 28.6},
            "medium_40_59": {"count": 10, "value": 45000000, "percentage": 35.7},
            "low_20_39": {"count": 5, "value": 23000000, "percentage": 17.9},
            "very_low_below_20": {"count": 2, "value": 10000000, "percentage": 7.1},
        },
        
        # 重点商机列表
        "key_opportunities": [
            {
                "id": 1,
                "name": "宁德时代 FCT",
                "customer": "宁德时代",
                "amount": 3500000,
                "win_rate": 75,
                "expected_value": 2625000,
                "factors": {
                    "relationship": 78,
                    "technical": 81,
                    "price": 66,
                    "other": 72,
                },
                "primary_weakness": "价格",
                "close_date": "2026-03-31",
            },
            {
                "id": 2,
                "name": "比亚迪 EOL",
                "customer": "比亚迪",
                "amount": 4200000,
                "win_rate": 82,
                "expected_value": 3444000,
                "factors": {
                    "relationship": 85,
                    "technical": 88,
                    "price": 75,
                    "other": 78,
                },
                "primary_weakness": "无明显短板",
                "close_date": "2026-03-25",
            },
            {
                "id": 3,
                "name": "中创新航 ICT",
                "customer": "中创新航",
                "amount": 2800000,
                "win_rate": 58,
                "expected_value": 1624000,
                "factors": {
                    "relationship": 62,
                    "technical": 70,
                    "price": 55,
                    "other": 58,
                },
                "primary_weakness": "商务关系",
                "close_date": "2026-04-15",
            },
            {
                "id": 4,
                "name": "亿纬锂能 烧录",
                "customer": "亿纬锂能",
                "amount": 1800000,
                "win_rate": 68,
                "expected_value": 1224000,
                "factors": {
                    "relationship": 72,
                    "technical": 75,
                    "price": 60,
                    "other": 65,
                },
                "primary_weakness": "价格",
                "close_date": "2026-04-05",
            },
        ],
        
        # 需要关注的商机
        "needs_attention": [
            {
                "id": 10,
                "name": "欣旺达 FCT",
                "customer": "欣旺达",
                "amount": 3200000,
                "win_rate": 35,
                "issue": "高金额但赢单率低",
                "primary_weakness": "商务关系（L2 发展级）",
                "recommended_action": "增加拜访频率，识别关键决策人",
            },
            {
                "id": 11,
                "name": "蜂巢能源 EOL",
                "customer": "蜂巢能源",
                "amount": 2500000,
                "win_rate": 28,
                "issue": "技术方案不匹配",
                "primary_weakness": "技术方案（需求覆盖仅 65%）",
                "recommended_action": "重新评估需求，调整方案",
            },
        ],
        
        # 团队对比
        "team_comparison": [
            {
                "team": "华南大区",
                "opportunities": 12,
                "avg_win_rate": 68,
                "total_value": 52000000,
                "weighted_value": 35360000,
            },
            {
                "team": "华东大区",
                "opportunities": 10,
                "avg_win_rate": 62,
                "total_value": 48000000,
                "weighted_value": 29760000,
            },
            {
                "team": "华北大区",
                "opportunities": 6,
                "avg_win_rate": 55,
                "total_value": 25000000,
                "weighted_value": 13750000,
            },
        ],
        
        # 改进建议
        "strategic_recommendations": [
            {
                "priority": 1,
                "action": "提升中金额商机赢单率",
                "target": "10 个 40-59% 赢单率的商机",
                "potential_upside": "平均提升 10% → 增加 450 万预期收入",
                "focus_areas": ["价格谈判", "商务关系深化"],
            },
            {
                "priority": 2,
                "action": "巩固高金额高赢单率商机",
                "target": "3 个 80%+ 赢单率的商机",
                "potential_upside": "防止意外，锁定 1200 万",
                "focus_areas": ["高层关系维护", "合同细节确认"],
            },
            {
                "priority": 3,
                "action": "评估低赢单率大商机",
                "target": "2 个<20% 赢单率但金额大的商机",
                "potential_upside": "决定投入还是放弃",
                "focus_areas": ["投入产出比分析", "战略价值评估"],
            },
        ],
    }
    
    return comparison
