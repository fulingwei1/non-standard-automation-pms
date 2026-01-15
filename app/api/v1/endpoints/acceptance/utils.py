# -*- coding: utf-8 -*-
"""
验收管理工具函数

包含：验收约束规则验证、编号生成等
"""

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.project import Project, Machine
from app.models.acceptance import AcceptanceOrder, AcceptanceIssue


# ==================== 验收约束规则验证 ====================

def validate_acceptance_rules(
    db: Session,
    acceptance_type: str,
    project_id: int,
    machine_id: Optional[int] = None,
    order_id: Optional[int] = None
) -> None:
    """
    验证验收约束规则

    规则：
    - AR001: FAT验收必须在设备调试完成后
    - AR002: SAT验收必须在FAT通过后
    - AR003: 终验收必须在所有SAT通过后

    Args:
        db: 数据库会话
        acceptance_type: 验收类型（FAT/SAT/FINAL）
        project_id: 项目ID
        machine_id: 设备ID（FAT/SAT需要）
        order_id: 验收单ID（用于更新时检查）

    Raises:
        HTTPException: 如果违反约束规则
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if acceptance_type == "FAT":
        # AR001: FAT验收必须在设备调试完成后
        if not machine_id:
            raise HTTPException(status_code=400, detail="FAT验收必须指定设备")

        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            raise HTTPException(status_code=404, detail="设备不存在")

        # 检查设备是否在S5（装配调试）阶段之后
        # S5是装配调试，S6是出厂验收，所以设备应该在S5或S6阶段
        if machine.stage not in ["S5", "S6"]:
            raise HTTPException(
                status_code=400,
                detail=f"设备尚未完成调试，当前阶段：{machine.stage}。FAT验收需要在设备调试完成后（S5阶段）进行"
            )

        # 检查项目阶段是否在S6（出厂验收）阶段
        if project.stage not in ["S5", "S6"]:
            raise HTTPException(
                status_code=400,
                detail=f"项目尚未进入调试出厂阶段，当前阶段：{project.stage}。FAT验收需要在S5或S6阶段进行"
            )

    elif acceptance_type == "SAT":
        # AR002: SAT验收必须在FAT通过后
        if not machine_id:
            raise HTTPException(status_code=400, detail="SAT验收必须指定设备")

        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            raise HTTPException(status_code=404, detail="设备不存在")

        # 检查该设备是否有通过的FAT验收
        fat_orders = db.query(AcceptanceOrder).filter(
            AcceptanceOrder.project_id == project_id,
            AcceptanceOrder.machine_id == machine_id,
            AcceptanceOrder.acceptance_type == "FAT",
            AcceptanceOrder.status == "COMPLETED",
            AcceptanceOrder.overall_result == "PASSED"
        ).all()

        if not fat_orders:
            raise HTTPException(
                status_code=400,
                detail="SAT验收必须在FAT验收通过后进行。请先完成并通过该设备的FAT验收"
            )

        # 检查项目阶段是否在S7或S8阶段（现场安装）
        if project.stage not in ["S7", "S8"]:
            raise HTTPException(
                status_code=400,
                detail=f"项目尚未进入现场安装阶段，当前阶段：{project.stage}。SAT验收需要在S7或S8阶段进行"
            )

    elif acceptance_type == "FINAL":
        # AR003: 终验收必须在所有SAT通过后
        # 检查项目中所有设备是否都有通过的SAT验收
        machines = db.query(Machine).filter(Machine.project_id == project_id).all()

        if not machines:
            raise HTTPException(status_code=400, detail="项目中没有设备，无法进行终验收")

        for machine in machines:
            # 检查该设备是否有通过的SAT验收
            sat_orders = db.query(AcceptanceOrder).filter(
                AcceptanceOrder.project_id == project_id,
                AcceptanceOrder.machine_id == machine.id,
                AcceptanceOrder.acceptance_type == "SAT",
                AcceptanceOrder.status == "COMPLETED",
                AcceptanceOrder.overall_result == "PASSED"
            ).all()

            if not sat_orders:
                raise HTTPException(
                    status_code=400,
                    detail=f"设备 {machine.machine_name} (编码: {machine.machine_code}) 尚未通过SAT验收，无法进行终验收。请先完成所有设备的SAT验收"
                )

        # 检查项目阶段是否在S8或S9阶段（验收结项）
        if project.stage not in ["S8", "S9"]:
            raise HTTPException(
                status_code=400,
                detail=f"项目尚未进入验收结项阶段，当前阶段：{project.stage}。终验收需要在S8或S9阶段进行"
            )


def validate_completion_rules(
    db: Session,
    order_id: int
) -> None:
    """
    验证完成验收的约束规则

    规则：
    - AR004: 存在未闭环阻塞问题不能通过验收
    - AR005: 必检项全部填写才能完成验收（已在complete_acceptance中实现）

    Args:
        db: 数据库会话
        order_id: 验收单ID

    Raises:
        HTTPException: 如果违反约束规则
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    # AR004: 检查是否存在未闭环的阻塞问题
    blocking_issues = db.query(AcceptanceIssue).filter(
        AcceptanceIssue.order_id == order_id,
        AcceptanceIssue.is_blocking == True,
        AcceptanceIssue.status.in_(["OPEN", "PROCESSING", "RESOLVED", "DEFERRED"])
    ).all()

    # 如果问题状态是RESOLVED，需要检查是否已验证通过
    unresolved_blocking_issues = []
    for issue in blocking_issues:
        if issue.status == "RESOLVED":
            # 已解决的问题需要验证通过才能算闭环
            if issue.verified_result != "VERIFIED":
                unresolved_blocking_issues.append(issue)
        else:
            unresolved_blocking_issues.append(issue)

    if unresolved_blocking_issues:
        issue_nos = [issue.issue_no for issue in unresolved_blocking_issues]
        raise HTTPException(
            status_code=400,
            detail=f"存在 {len(unresolved_blocking_issues)} 个未闭环的阻塞问题，无法通过验收。问题编号：{', '.join(issue_nos)}"
        )


def validate_edit_rules(
    db: Session,
    order_id: int
) -> None:
    """
    验证编辑验收单的约束规则

    规则：
    - AR006: 客户签字后验收单不可修改

    Args:
        db: 数据库会话
        order_id: 验收单ID

    Raises:
        HTTPException: 如果违反约束规则
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    # AR006: 检查是否有客户签字
    if order.customer_signed_at or order.customer_signer:
        raise HTTPException(
            status_code=400,
            detail="客户已签字确认，验收单不可修改。如需修改，请联系管理员"
        )

    # 检查是否有客户签署文件上传
    if order.is_officially_completed:
        raise HTTPException(
            status_code=400,
            detail="验收单已正式完成（已上传客户签署文件），不可修改"
        )


def generate_order_no(
    db: Session,
    acceptance_type: str,
    project_code: str,
    machine_no: Optional[int] = None
) -> str:
    """
    生成验收单号

    规则：
    - FAT验收单：FAT-{项目编号}-{设备序号}-{序号}
      示例：FAT-P2025001-M01-001
    - SAT验收单：SAT-{项目编号}-{设备序号}-{序号}
      示例：SAT-P2025001-M01-001
    - 终验收单：FIN-{项目编号}-{序号}
      示例：FIN-P2025001-001
    """
    # 确定前缀
    if acceptance_type == "FAT":
        prefix = "FAT"
    elif acceptance_type == "SAT":
        prefix = "SAT"
    elif acceptance_type == "FINAL":
        prefix = "FIN"
    else:
        # 兼容旧代码，如果类型未知，使用AC前缀
        prefix = "AC"

    # 构建基础编号（不含序号）
    if acceptance_type == "FINAL":
        # 终验收没有设备序号
        base_no = f"{prefix}-{project_code}"
    else:
        # FAT和SAT需要设备序号
        if machine_no is None:
            raise ValueError(f"{acceptance_type}验收单必须提供设备序号")
        machine_seq = f"M{machine_no:02d}"  # M01, M02, ...
        base_no = f"{prefix}-{project_code}-{machine_seq}"

    # 查找同类型、同项目、同设备（如果是FAT/SAT）的最大序号
    query = db.query(AcceptanceOrder).filter(
        AcceptanceOrder.order_no.like(f"{base_no}-%")
    )

    max_order = query.order_by(desc(AcceptanceOrder.order_no)).first()

    if max_order:
        # 提取最后一部分序号
        try:
            seq = int(max_order.order_no.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1

    return f"{base_no}-{seq:03d}"


def generate_issue_no(db: Session, order_no: str) -> str:
    """
    生成问题编号

    规则：
    - 验收问题：AI-{验收单号后缀}-{序号}
    - 示例：AI-FAT001-001（如果验收单号是 FAT-P2025001-M01-001）

    验收单号后缀提取规则：
    - 提取验收单号的前缀（FAT/SAT/FIN）和最后序号部分（保留3位数字格式）
    - 例如：FAT-P2025001-M01-001 -> FAT001
    - 例如：SAT-P2025001-M01-002 -> SAT002
    - 例如：FIN-P2025001-001 -> FIN001
    """
    # 解析验收单号，提取前缀和最后序号
    parts = order_no.split("-")
    if len(parts) >= 2:
        # 提取前缀（FAT/SAT/FIN）
        prefix = parts[0]
        # 提取最后序号部分（保留原始格式，如001）
        last_part = parts[-1]
        try:
            # 尝试转换为整数再格式化，确保是3位数字
            seq_num = int(last_part)
            suffix = f"{prefix}{seq_num:03d}"  # FAT001, SAT002, FIN001
        except ValueError:
            # 如果最后部分不是数字，使用原始格式
            suffix = f"{prefix}{last_part}"
    else:
        # 如果格式不符合预期，使用简化规则
        # 提取前3个字符作为前缀，最后3个字符作为序号
        if len(order_no) >= 6:
            suffix = f"{order_no[:3]}{order_no[-3:]}"
        else:
            suffix = order_no.replace("-", "")[:8]  # 取前8位

    # 查找同验收单的最大问题序号
    pattern = f"AI-{suffix}-%"
    max_issue = (
        db.query(AcceptanceIssue)
        .filter(AcceptanceIssue.issue_no.like(pattern))
        .order_by(desc(AcceptanceIssue.issue_no))
        .first()
    )

    if max_issue:
        try:
            seq = int(max_issue.issue_no.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1

    return f"AI-{suffix}-{seq:03d}"
