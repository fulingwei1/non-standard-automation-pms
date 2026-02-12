# -*- coding: utf-8 -*-
"""
gate_s8_s9 阶段门检查

包含gate_s8_s9相关的阶段门校验逻辑
"""

"""
项目模块 - 阶段门检查函数

包含所有阶段门校验逻辑（S1→S2 到 S8→S9）
"""

from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models.project import Machine, Project, ProjectPaymentPlan



def check_gate_s8_to_s9(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """
    G8: S8→S9 阶段门校验 - 终验收通过、回款达标
    """
    missing = []

    from app.models.acceptance import AcceptanceOrder
    final_orders = db.query(AcceptanceOrder).filter(
        AcceptanceOrder.project_id == project.id,
        AcceptanceOrder.acceptance_type == "FINAL",
        AcceptanceOrder.status == "COMPLETED",
        AcceptanceOrder.overall_result == "PASSED"
    ).all()

    if not final_orders:
        sat_orders = db.query(AcceptanceOrder).filter(
            AcceptanceOrder.project_id == project.id,
            AcceptanceOrder.acceptance_type == "SAT",
            AcceptanceOrder.status == "COMPLETED",
            AcceptanceOrder.overall_result == "PASSED"
        ).all()

        if not sat_orders:
            sat_failed = db.query(AcceptanceOrder).filter(
                AcceptanceOrder.project_id == project.id,
                AcceptanceOrder.acceptance_type == "SAT",
                AcceptanceOrder.status == "COMPLETED",
                AcceptanceOrder.overall_result == "FAILED"
            ).count()

            if sat_failed > 0:
                missing.append("SAT验收不通过（请完成整改后重新验收）")
            else:
                missing.append("终验收未完成（请完成SAT或终验收流程）")
        else:
            missing.append("终验收未完成（SAT已通过，请完成终验收）")

    # 检查回款达标
    payment_plans = db.query(ProjectPaymentPlan).filter(
        ProjectPaymentPlan.project_id == project.id
    ).all()

    if payment_plans:
        total_paid = sum(float(plan.actual_amount or 0) for plan in payment_plans if plan.status == "PAID")
        total_planned = sum(float(plan.planned_amount or 0) for plan in payment_plans)
        contract_amount = float(project.contract_amount or 0)

        base_amount = max(contract_amount, total_planned) if total_planned > 0 else contract_amount

        if base_amount > 0:
            payment_rate = (total_paid / base_amount) * 100
            if payment_rate < 80:
                missing.append(f"回款率 {payment_rate:.1f}%，需≥80%（已回款：{total_paid:.2f}，合同金额：{base_amount:.2f}）")
    else:
        if project.contract_amount and project.contract_amount > 0:
            missing.append("收款计划未设置（请设置收款计划）")

    # 检查设备交付状态
    if project.stage == "S8":
        machines = db.query(Machine).filter(Machine.project_id == project.id).all()
        if machines:
            for machine in machines:
                if machine.status not in ["DELIVERED", "COMPLETED"]:
                    missing.append(f"机台 {machine.machine_code} 未交付（当前状态：{machine.status}）")

    return (len(missing) == 0, missing)


