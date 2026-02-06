# -*- coding: utf-8 -*-
"""
gate_common 阶段门检查

包含gate_common相关的阶段门校验逻辑
"""

"""
项目模块 - 阶段门检查函数

包含所有阶段门校验逻辑（S1→S2 到 S8→S9）
"""

from decimal import Decimal
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from app.models.project import Machine, Project, ProjectPaymentPlan
from .gate_s1_s2 import check_gate_s1_to_s2
from .gate_s2_s3 import check_gate_s2_to_s3
from .gate_s3_s4 import check_gate_s3_to_s4
from .gate_s4_s5 import check_gate_s4_to_s5
from .gate_s5_s6 import check_gate_s5_to_s6
from .gate_s6_s7 import check_gate_s6_to_s7
from .gate_s7_s8 import check_gate_s7_to_s8
from .gate_s8_s9 import check_gate_s8_to_s9


def check_gate(db: Session, project: Project, target_stage: str) -> Tuple[bool, List[str]]:
    """
    阶段门准入校验

    Args:
        db: 数据库会话
        project: 项目对象
        target_stage: 目标阶段（S1-S9）

    Returns:
        (is_pass, missing_items): 是否通过，缺失项列表
    """
    gates = {
        'S2': check_gate_s1_to_s2,
        'S3': check_gate_s2_to_s3,
        'S4': check_gate_s3_to_s4,
        'S5': check_gate_s4_to_s5,
        'S6': check_gate_s5_to_s6,
        'S7': check_gate_s6_to_s7,
        'S8': check_gate_s7_to_s8,
        'S9': check_gate_s8_to_s9,
    }

    if target_stage in gates:
        return gates[target_stage](db, project)
    return (True, [])


def check_gate_detailed(db: Session, project: Project, target_stage: str) -> Dict[str, Any]:
    """
    Issue 1.4: 阶段门校验结果详细反馈

    返回结构化的校验结果，包含每个条件的检查状态
    """
    from app.schemas.project import GateCheckCondition

    gate_info = {
        'S2': ('G1', '需求进入→需求澄清', 'S1', 'S2'),
        'S3': ('G2', '需求澄清→立项评审', 'S2', 'S3'),
        'S4': ('G3', '立项评审→方案设计', 'S3', 'S4'),
        'S5': ('G4', '方案设计→采购制造', 'S4', 'S5'),
        'S6': ('G5', '采购制造→装配联调', 'S5', 'S6'),
        'S7': ('G6', '装配联调→出厂验收', 'S6', 'S7'),
        'S8': ('G7', '出厂验收→现场交付', 'S7', 'S8'),
        'S9': ('G8', '现场交付→质保结项', 'S8', 'S9'),
    }

    if target_stage not in gate_info:
        return {
            "gate_code": "",
            "gate_name": "",
            "from_stage": project.stage,
            "to_stage": target_stage,
            "passed": True,
            "total_conditions": 0,
            "passed_conditions": 0,
            "failed_conditions": 0,
            "conditions": [],
            "missing_items": [],
            "suggestions": [],
            "progress_pct": 100.0
        }

    gate_code, gate_name, from_stage, to_stage = gate_info[target_stage]

    # 执行校验
    gate_passed, missing_items = check_gate(db, project, target_stage)

    # 构建条件详情
    conditions = []
    passed_count = 0
    failed_count = 0

    # 根据阶段门类型构建条件列表
    if target_stage == 'S2':
        conditions = [
            GateCheckCondition(
                condition_name="客户信息齐全",
                condition_desc="客户名称、联系人、联系电话",
                status="PASSED" if project.customer_id and project.customer_name and project.customer_contact and project.customer_phone else "FAILED",
                message="客户信息已完整" if project.customer_id and project.customer_name else "请填写客户信息",
                action_url=f"/projects/{project.id}/edit",
                action_text="去填写"
            ),
            GateCheckCondition(
                condition_name="需求采集表完整",
                condition_desc="项目基本信息、需求描述",
                status="PASSED" if project.requirements else "FAILED",
                message="需求采集表已填写" if project.requirements else "请填写需求采集表",
                action_url=f"/projects/{project.id}/edit",
                action_text="去填写"
            ),
        ]
    elif target_stage == 'S3':
        from app.models.project import ProjectDocument
        spec_docs_count = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project.id,
            ProjectDocument.doc_type.in_(["REQUIREMENT", "SPECIFICATION"]),
            ProjectDocument.status == "APPROVED"
        ).count()

        conditions = [
            GateCheckCondition(
                condition_name="需求规格书已确认",
                condition_desc="需求规格书文档已上传并确认",
                status="PASSED" if spec_docs_count > 0 else "FAILED",
                message=f"已确认 {spec_docs_count} 个规格书文档" if spec_docs_count > 0 else "请上传并确认需求规格书",
                action_url=f"/projects/{project.id}/documents",
                action_text="去上传"
            ),
            GateCheckCondition(
                condition_name="验收标准明确",
                condition_desc="验收标准文档或记录",
                status="PASSED" if project.requirements and ("验收标准" in project.requirements or "acceptance" in project.requirements.lower()) else "FAILED",
                message="验收标准已明确" if project.requirements and ("验收标准" in project.requirements or "acceptance" in project.requirements.lower()) else "请明确验收标准",
                action_url=f"/projects/{project.id}/edit",
                action_text="去填写"
            ),
            GateCheckCondition(
                condition_name="客户已签字确认",
                condition_desc="需求规格书客户签字确认",
                status="PASSED" if project.status != "ST05" else "FAILED",
                message="客户已确认" if project.status != "ST05" else "待客户签字确认",
                action_url=f"/projects/{project.id}",
                action_text="查看详情"
            ),
        ]

    # 统计通过和失败的条件数
    for condition in conditions:
        if condition.status == "PASSED":
            passed_count += 1
        elif condition.status == "FAILED":
            failed_count += 1

    total_conditions = len(conditions) if conditions else len(missing_items)
    if total_conditions == 0:
        progress_pct = 100.0
    else:
        progress_pct = (passed_count / total_conditions) * 100

    # 生成建议操作
    suggestions = []
    if not gate_passed:
        suggestions.append(f"请完成以上 {failed_count} 项条件后重新尝试推进阶段")
        if missing_items:
            suggestions.append(f"缺失项：{', '.join(missing_items[:3])}{'...' if len(missing_items) > 3 else ''}")

    return {
        "gate_code": gate_code,
        "gate_name": gate_name,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "passed": gate_passed,
        "total_conditions": total_conditions,
        "passed_conditions": passed_count,
        "failed_conditions": failed_count,
        "conditions": [c.model_dump() for c in conditions] if conditions else [],
        "missing_items": missing_items,
        "suggestions": suggestions,
        "progress_pct": round(progress_pct, 1)
    }
