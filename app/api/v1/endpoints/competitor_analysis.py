# -*- coding: utf-8 -*-
"""
竞争对手分析模块
分析对不同竞品的赢单率，指导竞争策略
"""

from typing import Any, Optional, List, Dict
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User

router = APIRouter()


# ========== 1. 竞争对手总览 ==========

@router.get("/competitor/overview", summary="竞争对手总览")
def get_competitor_overview(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    竞争对手整体分析
    
    返回：
    - 主要竞争对手列表
    - 对各竞品的赢单率
    - 竞争优势/劣势分析
    """
    
    overview = {
        "analysis_date": date.today().isoformat(),
        "total_opportunities_analyzed": 156,
        "time_range": "2024-01-01 ~ 2026-03-01",
        
        # 主要竞争对手
        "main_competitors": [
            {
                "id": 1,
                "name": "竞品 A（某知名自动化公司）",
                "short_name": "竞品 A",
                "headquarters": "德国",
                "strengths": ["品牌知名度高", "技术成熟", "全球服务网络"],
                "weaknesses": ["价格高", "交付周期长", "定制化能力弱"],
                "market_position": "高端市场领导者",
            },
            {
                "id": 2,
                "name": "竞品 B（某国内上市公司）",
                "short_name": "竞品 B",
                "headquarters": "上海",
                "strengths": ["价格适中", "响应速度快", "本地化好"],
                "weaknesses": ["技术积累浅", "案例较少"],
                "market_position": "中端市场主要竞争者",
            },
            {
                "id": 3,
                "name": "竞品 C（某新兴公司）",
                "short_name": "竞品 C",
                "headquarters": "深圳",
                "strengths": ["价格低", "灵活定制", "服务积极"],
                "weaknesses": ["品牌弱", "稳定性待验证"],
                "market_position": "低端市场挑战者",
            },
            {
                "id": 4,
                "name": "竞品 D（某台系厂商）",
                "short_name": "竞品 D",
                "headquarters": "台湾",
                "strengths": ["性价比高", "电子行业经验丰富"],
                "weaknesses": ["服务网络弱", "大项目经验少"],
                "market_position": "中端市场细分领域",
            },
        ],
        
        # 对各竞品的赢单率对比
        "win_rate_by_competitor": [
            {
                "competitor": "竞品 A",
                "total_opportunities": 45,
                "won": 32,
                "lost": 13,
                "win_rate": 71.1,
                "avg_amount": 3200000,
                "trend": "stable",
                "analysis": "与竞品 A 竞争时赢单率较高，主要优势在价格和服务响应",
            },
            {
                "competitor": "竞品 B",
                "total_opportunities": 52,
                "won": 28,
                "lost": 24,
                "win_rate": 53.8,
                "avg_amount": 2800000,
                "trend": "improving",
                "analysis": "与竞品 B 竞争激烈，双方在价格和技术上相当",
            },
            {
                "competitor": "竞品 C",
                "total_opportunities": 38,
                "won": 30,
                "lost": 8,
                "win_rate": 78.9,
                "avg_amount": 2500000,
                "trend": "stable",
                "analysis": "对竞品 C 赢单率高，主要优势在品牌和技术实力",
            },
            {
                "competitor": "竞品 D",
                "total_opportunities": 21,
                "won": 10,
                "lost": 11,
                "win_rate": 47.6,
                "avg_amount": 2600000,
                "trend": "declining",
                "analysis": "对竞品 D 赢单率较低，需加强性价比和电子行业案例",
            },
        ],
        
        # 赢单率排名
        "win_rate_ranking": {
            "highest": {
                "competitor": "竞品 C",
                "win_rate": 78.9,
                "reason": "品牌和技术实力明显领先",
            },
            "lowest": {
                "competitor": "竞品 D",
                "win_rate": 47.6,
                "reason": "性价比和电子行业案例不足",
            },
        },
        
        # 竞争优势分析
        "competitive_advantages": [
            {
                "advantage": "价格竞争力",
                "vs_competitor_A": "显著优势（低 15-20%）",
                "vs_competitor_B": "相当",
                "vs_competitor_C": "劣势（高 10-15%）",
                "vs_competitor_D": "相当",
                "importance": "高",
            },
            {
                "advantage": "技术实力",
                "vs_competitor_A": "相当",
                "vs_competitor_B": "适度领先",
                "vs_competitor_C": "显著领先",
                "vs_competitor_D": "适度领先",
                "importance": "高",
            },
            {
                "advantage": "交付周期",
                "vs_competitor_A": "显著优势（快 30%）",
                "vs_competitor_B": "适度优势",
                "vs_competitor_C": "相当",
                "vs_competitor_D": "相当",
                "importance": "中",
            },
            {
                "advantage": "售后服务",
                "vs_competitor_A": "显著优势（2 小时响应）",
                "vs_competitor_B": "适度优势",
                "vs_competitor_C": "相当",
                "vs_competitor_D": "劣势",
                "importance": "高",
            },
            {
                "advantage": "定制化能力",
                "vs_competitor_A": "显著优势",
                "vs_competitor_B": "适度优势",
                "vs_competitor_C": "相当",
                "vs_competitor_D": "劣势",
                "importance": "中",
            },
        ],
    }
    
    return overview


# ========== 2. 竞品对比详情 ==========

@router.get("/competitor/{competitor_id}/analysis", summary="竞品对比详情")
def get_competitor_detailed_analysis(
    competitor_id: int = Path(..., description="竞品 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    与特定竞品的详细对比分析
    
    返回：
    - 历史交锋记录
    - 赢单/输单原因分析
    - 价格对比
    - 竞争优势/劣势
    """
    
    # 示例：竞品 A 分析
    analysis = {
        "competitor": {
            "id": 1,
            "name": "竞品 A（某知名自动化公司）",
            "short_name": "竞品 A",
            "headquarters": "德国",
            "founded": 1985,
            "employees": 5000,
            "revenue": "5 亿欧元",
        },
        
        # 交锋统计
        "head_to_head_stats": {
            "total_opportunities": 45,
            "won": 32,
            "lost": 13,
            "win_rate": 71.1,
            "avg_won_amount": 3200000,
            "avg_lost_amount": 4500000,
            "time_range": "2024-01-01 ~ 2026-03-01",
        },
        
        # 按行业分析
        "by_industry": [
            {
                "industry": "动力电池",
                "opportunities": 25,
                "won": 20,
                "lost": 5,
                "win_rate": 80.0,
                "analysis": "在动力电池行业优势明显，案例丰富",
            },
            {
                "industry": "消费电子",
                "opportunities": 12,
                "won": 7,
                "lost": 5,
                "win_rate": 58.3,
                "analysis": "消费电子行业竞争激烈，需加强案例",
            },
            {
                "industry": "储能",
                "opportunities": 8,
                "won": 5,
                "lost": 3,
                "win_rate": 62.5,
                "analysis": "储能行业双方都在拓展，势均力敌",
            },
        ],
        
        # 按金额区间分析
        "by_amount_range": [
            {
                "range": "<200 万",
                "opportunities": 10,
                "won": 8,
                "lost": 2,
                "win_rate": 80.0,
                "analysis": "小金额项目价格优势明显",
            },
            {
                "range": "200-500 万",
                "opportunities": 25,
                "won": 18,
                "lost": 7,
                "win_rate": 72.0,
                "analysis": "中等金额项目竞争力强",
            },
            {
                "range": ">500 万",
                "opportunities": 10,
                "won": 6,
                "lost": 4,
                "win_rate": 60.0,
                "analysis": "大金额项目品牌劣势明显",
            },
        ],
        
        # 赢单原因分析
        "win_reasons": [
            {
                "reason": "价格优势",
                "count": 18,
                "percentage": 56.3,
                "description": "比竞品 A 低 15-20%",
            },
            {
                "reason": "交付周期短",
                "count": 15,
                "percentage": 46.9,
                "description": "比竞品 A 快 30%",
            },
            {
                "reason": "售后服务好",
                "count": 12,
                "percentage": 37.5,
                "description": "2 小时响应，24 小时到场",
            },
            {
                "reason": "定制化能力强",
                "count": 10,
                "percentage": 31.3,
                "description": "灵活满足特殊需求",
            },
            {
                "reason": "商务关系好",
                "count": 8,
                "percentage": 25.0,
                "description": "客户关系成熟度高",
            },
        ],
        
        # 输单原因分析
        "loss_reasons": [
            {
                "reason": "品牌知名度不足",
                "count": 8,
                "percentage": 61.5,
                "description": "客户偏好国际大牌",
            },
            {
                "reason": "大项目经验少",
                "count": 5,
                "percentage": 38.5,
                "description": "缺乏 500 万 + 项目案例",
            },
            {
                "reason": "价格仍偏高",
                "count": 3,
                "percentage": 23.1,
                "description": "相比竞品 C 价格高",
            },
            {
                "reason": "技术方案不匹配",
                "count": 2,
                "percentage": 15.4,
                "description": "特殊需求无法满足",
            },
        ],
        
        # 价格对比
        "price_comparison": {
            "our_avg_price": 3200000,
            "competitor_avg_price": 4200000,
            "price_difference": -23.8,
            "price_position": "低于竞品 A 23.8%",
            "by_product_type": [
                {
                    "type": "ICT",
                    "our_price": 2500000,
                    "competitor_price": 3200000,
                    "difference": -21.9,
                },
                {
                    "type": "FCT",
                    "our_price": 3500000,
                    "competitor_price": 4500000,
                    "difference": -22.2,
                },
                {
                    "type": "EOL",
                    "our_price": 4000000,
                    "competitor_price": 5000000,
                    "difference": -20.0,
                },
            ],
        },
        
        # 历史交锋记录
        "recent_opportunities": [
            {
                "id": 1,
                "customer": "宁德时代",
                "project": "FCT 测试线",
                "amount": 3500000,
                "result": "won",
                "close_date": "2026-02-15",
                "key_factor": "价格优势 + 交付周期",
            },
            {
                "id": 2,
                "customer": "比亚迪",
                "project": "EOL 测试设备",
                "amount": 4200000,
                "result": "won",
                "close_date": "2026-01-20",
                "key_factor": "技术方案 + 商务关系",
            },
            {
                "id": 3,
                "customer": "某头部客户",
                "project": "大型测试线",
                "amount": 8000000,
                "result": "lost",
                "close_date": "2025-12-10",
                "key_factor": "品牌知名度不足",
            },
        ],
        
        # 竞争策略建议
        "strategy_recommendations": [
            {
                "priority": 1,
                "strategy": "强化价格优势",
                "description": "保持比竞品 A 低 15-20% 的价格优势",
                "expected_impact": "赢单率提升 5%",
            },
            {
                "priority": 2,
                "strategy": "突出交付周期优势",
                "description": "强调比竞品 A 快 30% 的交付能力",
                "expected_impact": "赢单率提升 3%",
            },
            {
                "priority": 3,
                "strategy": "加强大项目案例建设",
                "description": "积累 500 万 + 项目案例，提升品牌",
                "expected_impact": "大项目赢单率提升 10%",
            },
        ],
    }
    
    return analysis


# ========== 3. 竞争策略建议 ==========

@router.get("/competitor/strategy-recommendations", summary="竞争策略建议")
def get_competitor_strategy_recommendations(
    industry: Optional[str] = Query(None, description="行业"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    基于竞争分析的策略建议
    
    返回：
    - 针对不同竞品的应对策略
    - 销售话术建议
    - 定价策略建议
    """
    
    recommendations = {
        "generated_date": date.today().isoformat(),
        
        # 针对不同竞品的策略
        "strategies_by_competitor": [
            {
                "competitor": "竞品 A（德国知名）",
                "our_win_rate": 71.1,
                "strategy": "价格 + 服务双优势",
                "tactics": [
                    "强调价格低 15-20%，TCO 优势明显",
                    "突出 2 小时响应 vs 竞品 A 的 48 小时",
                    "强调交付周期快 30%",
                    "提供标杆客户参观，弥补品牌劣势",
                ],
                "sales_talks": [
                    "我们价格比竞品 A 低 20%，性能相当，TCO 更低",
                    "我们 2 小时响应，竞品 A 需要 48 小时",
                    "我们交付周期 8 周，竞品 A 需要 12 周",
                ],
                "pricing_strategy": "保持 15-20% 价格优势",
            },
            {
                "competitor": "竞品 B（国内上市）",
                "our_win_rate": 53.8,
                "strategy": "技术 + 案例差异化",
                "tactics": [
                    "强调技术积累和专利优势",
                    "展示同行业标杆案例",
                    "突出定制化能力",
                    "强调售后服务网络",
                ],
                "sales_talks": [
                    "我们有 50+ 专利，技术领先竞品 B 一代",
                    "我们在宁德时代有成功案例，竞品 B 没有",
                    "我们可以完全定制，竞品 B 只能标准方案",
                ],
                "pricing_strategy": "与竞品 B 持平，强调价值",
            },
            {
                "competitor": "竞品 C（新兴公司）",
                "our_win_rate": 78.9,
                "strategy": "品牌 + 稳定性压制",
                "tactics": [
                    "强调品牌实力和稳定性",
                    "展示长期合作客户",
                    "突出售后保障",
                    "强调项目风险控制",
                ],
                "sales_talks": [
                    "我们成立 15 年，竞品 C 只有 3 年",
                    "我们有 100+ 长期客户，返修率<1%",
                    "我们提供 3 年质保，竞品 C 只有 1 年",
                ],
                "pricing_strategy": "溢价 10-15%，强调价值",
            },
            {
                "competitor": "竞品 D（台系厂商）",
                "our_win_rate": 47.6,
                "strategy": "加强性价比 + 电子行业案例",
                "tactics": [
                    "提升性价比，缩小价格差距",
                    "加强电子行业案例建设",
                    "强调本地化服务优势",
                    "突出大项目经验",
                ],
                "sales_talks": [
                    "我们价格与竞品 D 相当，但配置更高",
                    "我们有电子行业 20+ 案例",
                    "我们大陆服务团队 50 人，竞品 D 只有 10 人",
                ],
                "pricing_strategy": "与竞品 D 持平或略低 5%",
            },
        ],
        
        # 按行业策略
        "strategies_by_industry": [
            {
                "industry": "动力电池",
                "our_avg_win_rate": 72,
                "main_competitors": ["竞品 A", "竞品 B"],
                "strategy": "案例 + 技术领先",
                "key_messages": [
                    "宁德时代/比亚迪标杆案例",
                    "动力电池测试专利 30+",
                    "交付业绩 100+ 条测试线",
                ],
            },
            {
                "industry": "消费电子",
                "our_avg_win_rate": 58,
                "main_competitors": ["竞品 B", "竞品 D"],
                "strategy": "加强案例建设",
                "key_messages": [
                    "珠海冠宇等成功案例",
                    "消费电子行业经验 10 年+",
                    "快速响应，配合客户节奏",
                ],
            },
            {
                "industry": "储能",
                "our_avg_win_rate": 62,
                "main_competitors": ["竞品 A", "竞品 C"],
                "strategy": "技术 + 价格平衡",
                "key_messages": [
                    "储能测试解决方案专家",
                    "安全性验证充分",
                    "性价比高，TCO 优势",
                ],
            },
        ],
        
        # 定价策略建议
        "pricing_recommendations": {
            "vs_premium_competitor": {
                "competitor": "竞品 A",
                "recommended_discount": "15-20%",
                "rationale": "品牌劣势需要价格补偿",
            },
            "vs_same_level_competitor": {
                "competitor": "竞品 B",
                "recommended_discount": "0-5%",
                "rationale": "实力相当，价值导向",
            },
            "vs_budget_competitor": {
                "competitor": "竞品 C",
                "recommended_premium": "10-15%",
                "rationale": "品牌和技术领先，可溢价",
            },
        },
    }
    
    return recommendations
