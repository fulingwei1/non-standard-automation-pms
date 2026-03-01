# -*- coding: utf-8 -*-
"""
AI销售助手API
提供话术推荐、方案生成、竞品分析、谈判建议、流失预警
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
from sqlalchemy.orm import Session
from datetime import date, timedelta

from app.api import deps
from app.core import security
from app.models.user import User

router = APIRouter()


# ========== 1. AI话术推荐 ==========

@router.get("/customers/{customer_id}/recommend-scripts", summary="AI推荐销售话术")
def recommend_scripts(
    customer_id: int = Path(..., description="客户ID"),
    opportunity_id: Optional[int] = Query(None, description="商机ID"),
    scenario_type: Optional[str] = Query(None, description="场景类型"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """根据客户特征AI推荐销售话术"""
    
    # 模拟话术推荐
    scenarios = {
        "初次接触": [
            {"id": 1, "title": "初次拜访开场白", "content": "您好，我是金凯博自动化的[姓名]，专注于锂电行业自动化测试设备...", "match_score": 95},
            {"id": 2, "title": "电话陌拜话术", "content": "您好，请问是[客户姓名]吗？我是金凯博自动化的小[姓]...", "match_score": 88},
        ],
        "需求挖掘": [
            {"id": 3, "title": "需求了解话术", "content": "贵司目前在[产品]测试方面主要有哪些痛点？...", "match_score": 92},
            {"id": 4, "title": "预算探询话术", "content": "这类项目的预算范围大概在什么区间？我可以为您推荐最合适的方案...", "match_score": 85},
        ],
        "方案介绍": [
            {"id": 5, "title": "FCT方案介绍", "content": "我们的FCT设备采用模块化设计，支持ICT+FCT一体化测试...", "match_score": 90},
        ],
        "价格谈判": [
            {"id": 6, "title": "价格异议处理", "content": "我理解您对价格的关注，让我从TCO（总拥有成本）角度分析一下...", "match_score": 93},
        ],
    }
    
    target_scenario = scenario_type or "初次接触"
    
    return {
        "customer_id": customer_id,
        "opportunity_id": opportunity_id,
        "scenario": target_scenario,
        "recommended_scripts": scenarios.get(target_scenario, []),
        "total_matched": len(scenarios.get(target_scenario, [])),
    }


# ========== 2. AI方案生成 ==========

@router.post("/opportunities/{opportunity_id}/generate-proposal", summary="AI生成方案")
def generate_proposal(
    opportunity_id: int = Path(..., description="商机ID"),
    proposal_type: str = Query("technical", description="方案类型：technical/business"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """根据商机自动生成技术/商务方案"""
    
    if proposal_type == "technical":
        return {
            "opportunity_id": opportunity_id,
            "proposal_type": "technical",
            "title": "锂电FCT测试设备技术方案",
            "generated_content": {
                "sections": [
                    {"title": "1. 项目概述", "content": "本项目为锂电FCT功能测试设备，采用模块化设计..."},
                    {"title": "2. 技术方案", "content": "设备配置：ICT测试模块、FCT测试模块、数据采集系统..."},
                    {"title": "3. 实施方案", "content": "交付周期：60天（标准模式）/ 45天（密集模式）..."},
                    {"title": "4. 验收标准", "content": "测试覆盖率≥99%，误测率≤0.1%..."},
                ],
            },
            "reference_projects": [
                {"name": "宁德时代FCT项目", "similarity": "90%"},
                {"name": "比亚迪EOL项目", "similarity": "75%"},
            ],
        }
    else:
        return {
            "opportunity_id": opportunity_id,
            "proposal_type": "business",
            "title": "商务合作方案",
            "generated_content": {
                "sections": [
                    {"title": "1. 合作概述", "content": "基于双方在锂电自动化领域的互补优势..."},
                    {"title": "2. 报价方案", "content": "设备总价：350万元（含税），包含：设备本体、安装调试、培训..."},
                    {"title": "3. 交付周期", "content": "标准交付：60天；加急交付：45天（+10%费用）"},
                    {"title": "4. 付款方式", "content": "3:6:1付款（合同签订30%，发货前60%，验收后10%）"},
                ],
            },
        }


# ========== 3. 竞品分析 ==========

@router.get("/competitor-analysis", summary="竞品分析")
def analyze_competitor(
    competitor_name: str = Query(..., description="竞品公司名称"),
    product_category: Optional[str] = Query(None, description="产品类型"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """竞品分析"""
    
    return {
        "competitor_name": competitor_name,
        "product_category": product_category,
        "competitor_info": {
            "encounter_count": 15,
            "our_wins": 9,
            "our_losses": 6,
            "win_rate": 60.0,
            "avg_price": 2800000,
            "price_range": "250万-320万",
            "common_tactics": ["低价策略", "快速交付", "品牌影响力"],
        },
        "our_advantages": [
            "技术实力强，定制化能力高",
            "锂电行业经验丰富",
            "售后服务响应快",
            "AI智能化程度高",
        ],
        "comparison": [
            {"dimension": "价格", "competitor": "较低", "us": "中等", "advantage": "competitor"},
            {"dimension": "技术", "competitor": "一般", "us": "强", "advantage": "us"},
            {"dimension": "交付", "competitor": "快", "us": "标准", "advantage": "competitor"},
            {"dimension": "服务", "competitor": "一般", "us": "优", "advantage": "us"},
        ],
        "recommended_strategy": [
            "强调技术优势和定制化能力，避免价格战",
            "突出锂电行业成功案例",
            "提供AI智能化差异化方案",
            "承诺快速响应的售后服务",
        ],
    }


# ========== 4. 谈判建议 ==========

@router.get("/opportunities/{opportunity_id}/negotiation-advice", summary="谈判建议")
def get_negotiation_advice(
    opportunity_id: int = Path(..., description="商机ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """根据客户特征给出谈判建议"""
    
    return {
        "opportunity_id": opportunity_id,
        "customer_traits": {
            "type": "大客户",
            "price_sensitivity": "中",
            "decision_style": "谨慎",
            "tech_awareness": "高",
        },
        "recommended_approach": "详细方案，数据支撑，建立信任",
        "price_strategy": "标准报价+服务增值包",
        "talking_points": [
            "锂电行业成功案例分享",
            "AI智能化技术优势",
            "快速交付能力",
            "完善的售后服务",
        ],
        "potential_objections": [
            "价格太高",
            "交付周期太长",
            "担心技术稳定性",
            "竞品价格更低",
        ],
        "counter_strategies": {
            "价格太高": "强调TCO（总拥有成本）优势，提供分期付款",
            "交付周期太长": "解释定制化需要，提供加急方案选项",
            "担心技术稳定性": "提供试用期，展示成功案例",
            "竞品价格更低": "强调技术差异和服务质量",
        },
    }


# ========== 5. 流失风险预警 ==========

@router.get("/customers/{customer_id}/churn-risk", summary="流失风险预测")
def predict_churn_risk(
    customer_id: int = Path(..., description="客户ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """AI预测客户流失风险"""
    
    # 模拟不同客户的风险
    risk_levels = ["LOW", "MEDIUM", "HIGH"]
    risk_level = risk_levels[customer_id % 3]
    
    if risk_level == "HIGH":
        risk_score = 75
        risk_factors = [
            {"factor": "长时间未联系", "detail": "已45天未联系", "severity": "HIGH"},
            {"factor": "多次负面反馈", "detail": "最近有3次负面交互", "severity": "HIGH"},
        ]
        actions = ["立即安排高层拜访", "提供特别优惠政策", "了解具体不满原因"]
    elif risk_level == "MEDIUM":
        risk_score = 45
        risk_factors = [
            {"factor": "商机推进停滞", "detail": "有1个商机超过30天未更新", "severity": "MEDIUM"},
        ]
        actions = ["增加联系频率", "分享行业最新动态", "邀请参加技术交流会"]
    else:
        risk_score = 15
        risk_factors = []
        actions = ["保持正常联系节奏", "定期发送产品更新"]
    
    return {
        "customer_id": customer_id,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_color": "red" if risk_level == "HIGH" else "orange" if risk_level == "MEDIUM" else "green",
        "risk_factors": risk_factors,
        "recommended_actions": actions,
    }


@router.get("/churn-risk-list", summary="高风险客户列表")
def get_churn_risk_list(
    risk_level: Optional[str] = Query(None, description="风险等级：HIGH/MEDIUM/LOW"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取流失风险客户列表"""
    
    # 模拟数据
    all_risks = [
        {"customer_id": 1, "customer_name": "宁德时代", "risk_score": 75, "risk_level": "HIGH", "risk_factors": [{"factor": "长时间未联系"}]},
        {"customer_id": 2, "customer_name": "比亚迪", "risk_score": 60, "risk_level": "HIGH", "risk_factors": [{"factor": "负面反馈"}]},
        {"customer_id": 3, "customer_name": "中创新航", "risk_score": 45, "risk_level": "MEDIUM", "risk_factors": [{"factor": "商机停滞"}]},
        {"customer_id": 4, "customer_name": "亿纬锂能", "risk_score": 20, "risk_level": "LOW", "risk_factors": []},
    ]
    
    if risk_level:
        filtered = [r for r in all_risks if r["risk_level"] == risk_level]
    else:
        filtered = all_risks
    
    return {
        "total_count": len(filtered),
        "high_risk_count": len([r for r in all_risks if r["risk_level"] == "HIGH"]),
        "medium_risk_count": len([r for r in all_risks if r["risk_level"] == "MEDIUM"]),
        "risk_list": filtered,
    }
