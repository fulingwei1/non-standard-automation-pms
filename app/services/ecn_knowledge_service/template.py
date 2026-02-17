# -*- coding: utf-8 -*-
"""
ECN知识库服务 - 模板管理
"""
import math
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List

from app.models.ecn import Ecn, EcnSolutionTemplate

from .solution_extraction import _extract_keywords
from app.utils.db_helpers import save_obj

if TYPE_CHECKING:
    from app.services.ecn_knowledge_service import EcnKnowledgeService


def recommend_solutions(
    service: "EcnKnowledgeService",
    ecn_id: int,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    推荐解决方案模板

    Args:
        service: EcnKnowledgeService实例
        ecn_id: ECN ID
        top_n: 返回数量

    Returns:
        推荐方案列表
    """
    ecn = service.db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise ValueError(f"ECN {ecn_id} 不存在")

    # 获取所有活跃的解决方案模板
    templates = service.db.query(EcnSolutionTemplate).filter(
        EcnSolutionTemplate.is_active
    ).all()

    recommendations = []

    for template in templates:
        score = _calculate_template_score(service, ecn, template)

        if score > 0:
            recommendations.append({
                "template_id": template.id,
                "template_code": template.template_code,
                "template_name": template.template_name,
                "template_category": template.template_category,
                "solution_description": template.solution_description,
                "solution_steps": template.solution_steps or [],
                "score": score,
                "success_rate": float(template.success_rate or 0),
                "usage_count": template.usage_count or 0,
                "estimated_cost": float(template.estimated_cost or 0),
                "estimated_days": template.estimated_days or 0,
                "match_reasons": _get_template_match_reasons(ecn, template, score)
            })

    # 按评分排序
    recommendations.sort(key=lambda x: x['score'], reverse=True)

    return recommendations[:top_n]


def create_solution_template(
    service: "EcnKnowledgeService",
    ecn_id: int,
    template_data: Dict[str, Any],
    created_by: int
) -> EcnSolutionTemplate:
    """
    从ECN创建解决方案模板

    Args:
        service: EcnKnowledgeService实例
        ecn_id: ECN ID
        template_data: 模板数据
        created_by: 创建人ID

    Returns:
        创建的模板
    """
    ecn = service.db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise ValueError(f"ECN {ecn_id} 不存在")

    # 生成模板编码
    template_code = _generate_template_code(ecn)

    template = EcnSolutionTemplate(
        template_code=template_code,
        template_name=template_data.get('template_name', f"{ecn.ecn_title} - 解决方案模板"),
        template_category=template_data.get('template_category', ecn.ecn_type),
        ecn_type=ecn.ecn_type,
        root_cause_category=ecn.root_cause_category,
        keywords=template_data.get('keywords', _extract_keywords(service, ecn)),
        solution_description=template_data.get('solution_description', ecn.solution or ''),
        solution_steps=template_data.get('solution_steps', []),
        required_resources=template_data.get('required_resources', []),
        estimated_cost=template_data.get('estimated_cost', ecn.cost_impact),
        estimated_days=template_data.get('estimated_days', ecn.schedule_impact_days),
        source_ecn_id=ecn_id,
        created_from='MANUAL',
        is_active=True,
        created_by=created_by
    )

    save_obj(service.db, template)

    return template


def apply_solution_template(
    service: "EcnKnowledgeService",
    ecn_id: int,
    template_id: int
) -> Dict[str, Any]:
    """
    应用解决方案模板到ECN

    Args:
        service: EcnKnowledgeService实例
        ecn_id: ECN ID
        template_id: 模板ID

    Returns:
        应用结果
    """
    from datetime import datetime

    ecn = service.db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise ValueError(f"ECN {ecn_id} 不存在")

    template = service.db.query(EcnSolutionTemplate).filter(
        EcnSolutionTemplate.id == template_id
    ).first()

    if not template:
        raise ValueError(f"解决方案模板 {template_id} 不存在")

    # 应用解决方案
    ecn.solution = template.solution_description
    ecn.solution_template_id = template_id
    ecn.solution_source = 'KNOWLEDGE_BASE'

    # 更新模板使用次数
    template.usage_count = (template.usage_count or 0) + 1

    service.db.commit()

    return {
        "ecn_id": ecn_id,
        "template_id": template_id,
        "solution": template.solution_description,
        "solution_steps": template.solution_steps or [],
        "applied_at": datetime.now().isoformat()
    }


def _calculate_template_score(service: "EcnKnowledgeService", ecn: Ecn, template: EcnSolutionTemplate) -> float:
    """计算模板推荐评分"""
    score = 0.0

    # 1. ECN类型匹配（30分）
    if ecn.ecn_type == template.ecn_type:
        score += 30.0

    # 2. 根本原因分类匹配（25分）
    if ecn.root_cause_category and template.root_cause_category:
        if ecn.root_cause_category == template.root_cause_category:
            score += 25.0

    # 3. 关键词匹配（20分）
    if template.keywords:
        ecn_keywords = set(_extract_keywords(service, ecn))
        template_keywords = set(template.keywords)
        if ecn_keywords & template_keywords:
            match_ratio = len(ecn_keywords & template_keywords) / len(template_keywords)
            score += 20.0 * match_ratio

    # 4. 成功率（15分）
    success_rate = float(template.success_rate or 0)
    score += 15.0 * (success_rate / 100.0)

    # 5. 使用频率（10分）
    usage_count = template.usage_count or 0
    if usage_count > 0:
        usage_score = min(10.0, math.log10(usage_count + 1) * 3)
        score += usage_score

    return round(score, 2)


def _get_template_match_reasons(ecn: Ecn, template: EcnSolutionTemplate, score: float) -> List[str]:
    """获取模板匹配原因"""
    reasons = []

    if ecn.ecn_type == template.ecn_type:
        reasons.append(f"匹配ECN类型：{ecn.ecn_type}")

    if ecn.root_cause_category and template.root_cause_category:
        if ecn.root_cause_category == template.root_cause_category:
            reasons.append(f"匹配根本原因分类：{ecn.root_cause_category}")

    if template.success_rate and template.success_rate > 80:
        reasons.append(f"高成功率：{template.success_rate}%")

    if template.usage_count and template.usage_count > 5:
        reasons.append(f"常用方案：已使用{template.usage_count}次")

    return reasons


def _generate_template_code(ecn: Ecn) -> str:
    """生成模板编码"""
    timestamp = datetime.now().strftime('%Y%m%d')
    return f"ECN-SOL-{timestamp}-{ecn.id:04d}"
