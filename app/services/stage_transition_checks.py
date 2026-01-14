# -*- coding: utf-8 -*-
"""
阶段流转检查服务
"""

from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.sales import Contract
from app.models.material import BomHeader
from app.models.acceptance import AcceptanceOrder
from app.models.project import ProjectPaymentPlan


def check_s3_to_s4_transition(
    db: Session,
    project: Project
) -> Tuple[bool, Optional[str], List[str]]:
    """
    检查 S3→S4 流转条件（合同签订后自动推进）
    
    Returns:
        Tuple[bool, Optional[str], List[str]]: (是否可推进, 目标阶段, 缺失项列表)
    """
    if not (project.contract_no and project.contract_date and project.contract_amount):
        return False, None, ["合同信息不完整（请填写合同编号、签订日期和金额）"]
    
    # 检查合同状态
    contract = db.query(Contract).filter(
        Contract.contract_code == project.contract_no
    ).first()
    
    if contract and contract.status == "SIGNED":
        return True, "S4", []
    else:
        return False, None, ["合同未签订（请完成合同签订流程）"]


def check_s4_to_s5_transition(
    db: Session,
    project_id: int
) -> Tuple[bool, Optional[str], List[str]]:
    """
    检查 S4→S5 流转条件（BOM发布后自动推进）
    
    Returns:
        Tuple[bool, Optional[str], List[str]]: (是否可推进, 目标阶段, 缺失项列表)
    """
    released_boms = db.query(BomHeader).filter(
        BomHeader.project_id == project_id,
        BomHeader.status == "RELEASED"
    ).count()
    
    if released_boms > 0:
        return True, "S5", []
    else:
        return False, None, ["BOM未发布（请发布至少一个BOM）"]


def check_s5_to_s6_transition(
    db: Session,
    project: Project
) -> Tuple[bool, Optional[str], List[str]]:
    """
    检查 S5→S6 流转条件（物料齐套率≥80%时提示可推进）
    
    Returns:
        Tuple[bool, Optional[str], List[str]]: (是否可推进, 目标阶段, 缺失项列表)
    """
    from app.api.v1.endpoints.projects import check_gate_s5_to_s6
    
    gate_passed, gate_missing = check_gate_s5_to_s6(db, project)
    
    if gate_passed:
        return True, "S6", []
    else:
        return False, None, gate_missing


def check_s7_to_s8_transition(
    db: Session,
    project_id: int
) -> Tuple[bool, Optional[str], List[str]]:
    """
    检查 S7→S8 流转条件（FAT验收通过后自动推进）
    
    Returns:
        Tuple[bool, Optional[str], List[str]]: (是否可推进, 目标阶段, 缺失项列表)
    """
    fat_orders = db.query(AcceptanceOrder).filter(
        AcceptanceOrder.project_id == project_id,
        AcceptanceOrder.acceptance_type == "FAT",
        AcceptanceOrder.status == "COMPLETED",
        AcceptanceOrder.overall_result == "PASSED"
    ).count()
    
    if fat_orders > 0:
        return True, "S8", []
    else:
        return False, None, ["FAT验收未通过（请完成FAT验收流程）"]


def check_s8_to_s9_transition(
    db: Session,
    project: Project
) -> Tuple[bool, Optional[str], List[str]]:
    """
    检查 S8→S9 流转条件（终验收通过且回款达标后提示可推进）
    
    Returns:
        Tuple[bool, Optional[str], List[str]]: (是否可推进, 目标阶段, 缺失项列表)
    """
    project_id = project.id
    
    # 检查终验收
    final_orders = db.query(AcceptanceOrder).filter(
        AcceptanceOrder.project_id == project_id,
        AcceptanceOrder.acceptance_type.in_(["FINAL", "SAT"]),
        AcceptanceOrder.status == "COMPLETED",
        AcceptanceOrder.overall_result == "PASSED"
    ).count()
    
    if final_orders == 0:
        return False, None, ["终验收未通过（请完成终验收流程）"]
    
    # 检查回款达标
    payment_plans = db.query(ProjectPaymentPlan).filter(
        ProjectPaymentPlan.project_id == project_id
    ).all()
    
    if not payment_plans:
        return False, None, ["收款计划未设置"]
    
    total_paid = sum(float(plan.actual_amount or 0) for plan in payment_plans if plan.status == "PAID")
    total_planned = sum(float(plan.planned_amount or 0) for plan in payment_plans)
    contract_amount = float(project.contract_amount or 0)
    base_amount = max(contract_amount, total_planned) if total_planned > 0 else contract_amount
    
    if base_amount == 0:
        return False, None, ["合同金额未设置"]
    
    payment_rate = (total_paid / base_amount) * 100
    if payment_rate >= 80:
        return True, "S9", []
    else:
        return False, None, [f"回款率 {payment_rate:.1f}%，需≥80%"]


def get_stage_status_mapping() -> Dict[str, str]:
    """
    获取阶段到状态的映射
    
    Returns:
        Dict[str, str]: 阶段到状态的映射字典
    """
    return {
        'S4': 'ST09',
        'S5': 'ST12',
        'S6': 'ST16',
        'S8': 'ST23',
        'S9': 'ST30',
    }


def execute_stage_transition(
    db: Session,
    project: Project,
    target_stage: str,
    transition_reason: str
) -> Tuple[bool, Dict[str, Any]]:
    """
    执行阶段流转

    Returns:
        Tuple[bool, Dict[str, Any]]: (是否成功, 结果字典)
    """
    from app.api.v1.endpoints.projects.utils import check_gate

    try:
        gate_passed, gate_missing = check_gate(db, project, target_stage)
        
        if not gate_passed:
            return False, {
                "can_advance": False,
                "auto_advanced": False,
                "message": "阶段门校验未通过",
                "current_stage": project.stage,
                "target_stage": target_stage,
                "missing_items": gate_missing,
                "transition_reason": transition_reason
            }
        
        old_stage = project.stage
        project.stage = target_stage
        
        # 更新状态
        stage_status_map = get_stage_status_mapping()
        if target_stage in stage_status_map:
            project.status = stage_status_map[target_stage]
        
        return True, {
            "can_advance": True,
            "auto_advanced": True,
            "message": f"已自动推进至 {target_stage} 阶段",
            "current_stage": old_stage,
            "target_stage": target_stage,
            "missing_items": [],
            "transition_reason": transition_reason
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"自动推进阶段失败：{str(e)}", exc_info=True)
        return False, {
            "can_advance": False,
            "auto_advanced": False,
            "message": f"自动推进失败：{str(e)}",
            "current_stage": project.stage,
            "target_stage": target_stage,
            "missing_items": []
        }
