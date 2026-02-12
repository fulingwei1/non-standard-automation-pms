# -*- coding: utf-8 -*-
"""
ECN知识库服务 - 解决方案提取
"""
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List

from app.models.ecn import Ecn, EcnAffectedMaterial

if TYPE_CHECKING:
    from app.services.ecn_knowledge_service import EcnKnowledgeService


def extract_solution(
    service: "EcnKnowledgeService",
    ecn_id: int,
    auto_extract: bool = True
) -> Dict[str, Any]:
    """
    从ECN中提取解决方案

    Args:
        service: EcnKnowledgeService实例
        ecn_id: ECN ID
        auto_extract: 是否自动提取（否则手动填写）

    Returns:
        提取结果
    """
    ecn = service.db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise ValueError(f"ECN {ecn_id} 不存在")

    if auto_extract:
        # 自动提取解决方案
        solution = _auto_extract_solution(ecn)
    else:
        # 使用手动填写的解决方案
        solution = ecn.solution or ""

    # 提取关键词
    keywords = _extract_keywords(service, ecn)

    # 构建解决方案描述
    solution_description = _build_solution_description(ecn, solution)

    # 提取解决步骤
    solution_steps = _extract_solution_steps(service, ecn, solution)

    # 估算成本和天数
    estimated_cost = float(ecn.cost_impact or 0)
    estimated_days = ecn.schedule_impact_days or 0

    return {
        "ecn_id": ecn_id,
        "solution": solution_description,
        "solution_steps": solution_steps,
        "keywords": keywords,
        "estimated_cost": estimated_cost,
        "estimated_days": estimated_days,
        "ecn_type": ecn.ecn_type,
        "root_cause_category": ecn.root_cause_category,
        "extracted_at": datetime.now().isoformat()
    }


def _auto_extract_solution(ecn: Ecn) -> str:
    """自动提取解决方案"""
    # 从solution字段直接提取
    if ecn.solution:
        return ecn.solution

    # 从执行说明中提取
    if ecn.execution_note:
        return ecn.execution_note

    # 从变更描述中提取
    if ecn.change_description:
        # 尝试提取解决方案部分
        solution_keywords = ['解决方案', '解决方法', '处理方式', '解决', '处理']
        for keyword in solution_keywords:
            if keyword in ecn.change_description:
                # 提取包含关键词的段落
                parts = ecn.change_description.split(keyword)
                if len(parts) > 1:
                    return parts[1].strip()

    return ""


def _extract_keywords(service: "EcnKnowledgeService", ecn: Ecn) -> List[str]:
    """提取关键词"""
    keywords = []

    # 从ECN类型
    if ecn.ecn_type:
        keywords.append(ecn.ecn_type)

    # 从根本原因分类
    if ecn.root_cause_category:
        keywords.append(ecn.root_cause_category)

    # 从变更描述中提取关键词
    if ecn.change_description:
        # 简单的关键词提取（可以后续优化为NLP）
        text = ecn.change_description.lower()
        common_keywords = ['物料', '设计', '工艺', '测试', '质量', '成本', '交期']
        for kw in common_keywords:
            if kw in text:
                keywords.append(kw)

    # 从受影响物料中提取
    affected_materials = service.db.query(EcnAffectedMaterial).filter(
        EcnAffectedMaterial.ecn_id == ecn.id
    ).limit(5).all()

    for mat in affected_materials:
        if mat.material_name:
            # 提取物料名称中的关键词
            words = mat.material_name.split()
            keywords.extend(words[:2])  # 取前两个词

    # 去重并返回
    return list(set(keywords))[:10]


def _build_solution_description(ecn: Ecn, solution: str) -> str:
    """构建解决方案描述"""
    if solution:
        return solution

    # 如果没有解决方案，根据ECN信息构建
    description_parts = []

    if ecn.change_description:
        description_parts.append(f"变更内容：{ecn.change_description}")

    if ecn.root_cause_analysis:
        description_parts.append(f"根本原因：{ecn.root_cause_analysis}")

    if ecn.execution_note:
        description_parts.append(f"执行说明：{ecn.execution_note}")

    return "\n".join(description_parts) if description_parts else "暂无解决方案描述"


def _extract_solution_steps(service: "EcnKnowledgeService", ecn: Ecn, solution: str) -> List[str]:
    """提取解决步骤"""
    steps = []

    if solution:
        # 尝试从解决方案中提取步骤（按序号或换行）
        lines = solution.split('\n')
        for line in lines:
            line = line.strip()
            # 匹配序号格式：1. 2. 3. 或 一、 二、 三、
            if re.match(r'^[\d一二三四五六七八九十]+[\.、]', line):
                steps.append(line)
            elif line.startswith('-') or line.startswith('•'):
                steps.append(line)

    # 如果没有提取到步骤，从执行任务中提取
    if not steps:
        from app.models.ecn import EcnTask
        tasks = service.db.query(EcnTask).filter(
            EcnTask.ecn_id == ecn.id,
            EcnTask.status.in_(['COMPLETED', 'IN_PROGRESS'])
        ).order_by(EcnTask.planned_start).limit(10).all()

        for task in tasks:
            steps.append(f"{task.task_name}: {task.task_description or ''}")

    return steps[:10]  # 最多返回10个步骤
