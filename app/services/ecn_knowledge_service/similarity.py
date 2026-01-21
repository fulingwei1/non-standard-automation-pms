# -*- coding: utf-8 -*-
"""
ECN知识库服务 - 相似度计算
"""
import re
from typing import Any, Dict, List

from app.models.ecn import Ecn, EcnAffectedMaterial


def find_similar_ecns(
    service: "EcnKnowledgeService",
    ecn_id: int,
    top_n: int = 5,
    min_similarity: float = 0.3
) -> List[Dict[str, Any]]:
    """
    查找相似的ECN

    Args:
        service: EcnKnowledgeService实例
        ecn_id: 当前ECN ID
        top_n: 返回数量
        min_similarity: 最小相似度阈值

    Returns:
        相似ECN列表
    """
    current_ecn = service.db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not current_ecn:
        raise ValueError(f"ECN {ecn_id} 不存在")

    # 获取所有已完成的ECN（排除当前ECN）
    completed_ecns = service.db.query(Ecn).filter(
        Ecn.id != ecn_id,
        Ecn.status.in_(['COMPLETED', 'CLOSED']),
        Ecn.solution.isnot(None),
        Ecn.solution != ''
    ).all()

    similar_ecns = []

    for ecn in completed_ecns:
        similarity_score = _calculate_similarity(service, current_ecn, ecn)

        if similarity_score >= min_similarity:
            similar_ecns.append({
                "ecn_id": ecn.id,
                "ecn_no": ecn.ecn_no,
                "ecn_title": ecn.ecn_title,
                "ecn_type": ecn.ecn_type,
                "similarity_score": similarity_score,
                "solution": ecn.solution,
                "root_cause_category": ecn.root_cause_category,
                "cost_impact": float(ecn.cost_impact or 0),
                "schedule_impact_days": ecn.schedule_impact_days or 0,
                "completed_at": ecn.execution_end.isoformat() if ecn.execution_end else None,
                "match_reasons": _get_match_reasons(current_ecn, ecn, similarity_score)
            })

    # 按相似度排序
    similar_ecns.sort(key=lambda x: x['similarity_score'], reverse=True)

    return similar_ecns[:top_n]


def _calculate_similarity(service: "EcnKnowledgeService", ecn1: Ecn, ecn2: Ecn) -> float:
    """计算两个ECN的相似度"""
    score = 0.0
    max_score = 0.0

    # 1. ECN类型匹配（权重：30%）
    max_score += 30
    if ecn1.ecn_type == ecn2.ecn_type:
        score += 30

    # 2. 根本原因分类匹配（权重：25%）
    max_score += 25
    if ecn1.root_cause_category and ecn2.root_cause_category:
        if ecn1.root_cause_category == ecn2.root_cause_category:
            score += 25

    # 3. 变更描述相似度（权重：20%）
    max_score += 20
    if ecn1.change_description and ecn2.change_description:
        text_similarity = _text_similarity(
            ecn1.change_description,
            ecn2.change_description
        )
        score += 20 * text_similarity

    # 4. 受影响物料相似度（权重：15%）
    max_score += 15
    material_similarity = _material_similarity(service, ecn1.id, ecn2.id)
    score += 15 * material_similarity

    # 5. 成本影响相似度（权重：10%）
    max_score += 10
    cost_similarity = _cost_similarity(
        float(ecn1.cost_impact or 0),
        float(ecn2.cost_impact or 0)
    )
    score += 10 * cost_similarity

    # 归一化到0-1
    return score / max_score if max_score > 0 else 0.0


def _text_similarity(text1: str, text2: str) -> float:
    """计算文本相似度（简单的关键词匹配）"""
    if not text1 or not text2:
        return 0.0

    # 提取关键词
    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))

    if not words1 or not words2:
        return 0.0

    # Jaccard相似度
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


def _material_similarity(service: "EcnKnowledgeService", ecn_id1: int, ecn_id2: int) -> float:
    """计算受影响物料的相似度"""
    mats1 = service.db.query(EcnAffectedMaterial).filter(
        EcnAffectedMaterial.ecn_id == ecn_id1
    ).all()

    mats2 = service.db.query(EcnAffectedMaterial).filter(
        EcnAffectedMaterial.ecn_id == ecn_id2
    ).all()

    if not mats1 or not mats2:
        return 0.0

    # 物料编码匹配
    codes1 = {mat.material_code for mat in mats1}
    codes2 = {mat.material_code for mat in mats2}

    intersection = len(codes1 & codes2)
    union = len(codes1 | codes2)

    return intersection / union if union > 0 else 0.0


def _cost_similarity(cost1: float, cost2: float) -> float:
    """计算成本相似度"""
    if cost1 == 0 and cost2 == 0:
        return 1.0

    if cost1 == 0 or cost2 == 0:
        return 0.0

    # 使用相对差异
    diff = abs(cost1 - cost2) / max(abs(cost1), abs(cost2))
    return 1.0 - min(diff, 1.0)


def _get_match_reasons(ecn1: Ecn, ecn2: Ecn, similarity: float) -> List[str]:
    """获取匹配原因"""
    reasons = []

    if ecn1.ecn_type == ecn2.ecn_type:
        reasons.append(f"相同ECN类型：{ecn1.ecn_type}")

    if ecn1.root_cause_category and ecn2.root_cause_category:
        if ecn1.root_cause_category == ecn2.root_cause_category:
            reasons.append(f"相同根本原因分类：{ecn1.root_cause_category}")

    if similarity > 0.7:
        reasons.append("高度相似")
    elif similarity > 0.5:
        reasons.append("中等相似")
    else:
        reasons.append("部分相似")

    return reasons
