# -*- coding: utf-8 -*-
"""
gate_s7_s8 阶段门检查

包含gate_s7_s8相关的阶段门校验逻辑
"""

"""
项目模块 - 阶段门检查函数

包含所有阶段门校验逻辑（S1→S2 到 S8→S9）
"""

from decimal import Decimal
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from app.models.project import Machine, Project, ProjectPaymentPlan



def check_gate_s7_to_s8(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """
    G7: S7→S8 阶段门校验 - FAT验收通过
    """
    missing = []

    from app.models.acceptance import AcceptanceOrder
    fat_orders = db.query(AcceptanceOrder).filter(
        AcceptanceOrder.project_id == project.id,
        AcceptanceOrder.acceptance_type == "FAT",
        AcceptanceOrder.status == "COMPLETED",
        AcceptanceOrder.overall_result == "PASSED"
    ).all()

    if not fat_orders:
        fat_orders_failed = db.query(AcceptanceOrder).filter(
            AcceptanceOrder.project_id == project.id,
            AcceptanceOrder.acceptance_type == "FAT",
            AcceptanceOrder.status == "COMPLETED",
            AcceptanceOrder.overall_result == "FAILED"
        ).count()

        if fat_orders_failed > 0:
            missing.append("FAT验收不通过（请完成整改后重新验收）")
        else:
            missing.append("FAT验收未完成（请完成FAT验收流程）")
    else:
        from app.models.acceptance import AcceptanceReport
        fat_reports = db.query(AcceptanceReport).join(
            AcceptanceOrder, AcceptanceReport.order_id == AcceptanceOrder.id
        ).filter(
            AcceptanceOrder.project_id == project.id,
            AcceptanceOrder.acceptance_type == "FAT",
            AcceptanceOrder.status == "COMPLETED"
        ).count()

        if fat_reports == 0:
            missing.append("FAT报告未生成（请生成FAT验收报告）")

        from app.models.acceptance import AcceptanceIssue
        unresolved_issues = db.query(AcceptanceIssue).join(
            AcceptanceOrder, AcceptanceIssue.order_id == AcceptanceOrder.id
        ).filter(
            AcceptanceOrder.project_id == project.id,
            AcceptanceOrder.acceptance_type == "FAT",
            AcceptanceIssue.status.notin_(["RESOLVED", "CLOSED"])
        ).count()

        if unresolved_issues > 0:
            missing.append(f"存在 {unresolved_issues} 个未完成的FAT整改项（请完成所有整改项）")

    return (len(missing) == 0, missing)


