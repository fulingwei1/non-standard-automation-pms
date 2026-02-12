# -*- coding: utf-8 -*-
"""
gate_s1_s2 阶段门检查

包含gate_s1_s2相关的阶段门校验逻辑
"""

"""
项目模块 - 阶段门检查函数

包含所有阶段门校验逻辑（S1→S2 到 S8→S9）
"""

from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models.project import Project



def check_gate_s1_to_s2(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """G1: S1→S2 阶段门校验 - 基本信息完整、客户信息齐全、项目评价已完成"""
    missing = []

    # 基本信息检查
    if not project.project_name:
        missing.append("项目名称不能为空")
    if not project.customer_id:
        missing.append("客户信息不能为空")

    # 客户联系信息检查
    if not project.customer_name:
        missing.append("客户名称不能为空")
    if not project.customer_contact:
        missing.append("客户联系人不能为空")
    if not project.customer_phone:
        missing.append("客户联系电话不能为空")

    # 需求信息检查
    if not project.requirements:
        missing.append("需求采集表未填写")

    # 项目评价强制要求（新增）
    from app.models.project_evaluation import ProjectEvaluation
    evaluation = db.query(ProjectEvaluation).filter(
        ProjectEvaluation.project_id == project.id,
        ProjectEvaluation.status == 'CONFIRMED'
    ).first()

    if not evaluation:
        missing.append("项目评价未完成（项目管理部经理必须填写项目难度和工作量评价，状态需为已确认）")
    else:
        # 检查必要字段是否已填写
        if evaluation.difficulty_score is None:
            missing.append("项目难度得分未填写")
        if evaluation.workload_score is None:
            missing.append("项目工作量得分未填写")

    return (len(missing) == 0, missing)

