# -*- coding: utf-8 -*-
"""
项目阶段推进服务
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.project import Machine, Project, ProjectStatusLog

logger = logging.getLogger(__name__)


def validate_target_stage(target_stage: str) -> None:
    """
    验证目标阶段编码

    Raises:
        HTTPException: 如果阶段编码无效
    """
    from fastapi import HTTPException

    valid_stages = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
    if target_stage not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail=f"无效的目标阶段。有效值：{', '.join(valid_stages)}"
        )


def validate_stage_advancement(
    current_stage: str,
    target_stage: str
) -> None:
    """
    检查阶段是否向前推进

    Raises:
        HTTPException: 如果目标阶段不向前推进
    """
    from fastapi import HTTPException

    current_stage_num = int(current_stage[1]) if len(current_stage) > 1 else 1
    target_stage_num = int(target_stage[1]) if len(target_stage) > 1 else 1

    if target_stage_num <= current_stage_num:
        raise HTTPException(
            status_code=400,
            detail=f"目标阶段 {target_stage} 不能早于或等于当前阶段 {current_stage}"
        )


def perform_gate_check(
    db: Session,
    project: Project,
    target_stage: str,
    skip_gate_check: bool,
    current_user_is_superuser: bool
) -> Tuple[bool, list, Optional[Dict[str, Any]]]:
    """
    执行阶段门校验

    Returns:
        Tuple[bool, list, Optional[Dict]]: (是否通过, 缺失项列表, 详细校验结果)
    """
    from fastapi import HTTPException

    if skip_gate_check:
        if not current_user_is_superuser:
            raise HTTPException(
                status_code=403,
                detail="只有管理员可以跳过阶段门校验"
            )
        return True, [], None

    if current_user_is_superuser:
        return True, [], None

    from app.api.v1.endpoints.projects import check_gate, check_gate_detailed

    gate_passed, missing_items = check_gate(db, project, target_stage)

    if not gate_passed:
        gate_check_result = check_gate_detailed(db, project, target_stage)
        return False, missing_items, gate_check_result

    return True, [], None


def get_stage_status_mapping() -> Dict[str, str]:
    """
    获取阶段到状态的映射

    Returns:
        Dict[str, str]: 阶段到状态的映射字典
    """
    return {
        'S1': 'ST01',
        'S2': 'ST03',
        'S3': 'ST05',
        'S4': 'ST07',
        'S5': 'ST10',
        'S6': 'ST15',
        'S7': 'ST20',
        'S8': 'ST25',
        'S9': 'ST30',
    }


def update_project_stage_and_status(
    db: Session,
    project: Project,
    target_stage: str,
    old_stage: str,
    old_status: str
) -> str:
    """
    更新项目阶段和状态

    Returns:
        str: 新状态
    """
    project.stage = target_stage

    # 仅在阶段实际变化时，通过映射更新状态
    if target_stage != old_stage:
        stage_status_map = get_stage_status_mapping()
        new_status = stage_status_map.get(target_stage, old_status)
        if new_status != old_status:
            project.status = new_status
    else:
        # 阶段未变化时，使用传入的 old_status 作为目标状态
        new_status = old_status
        if project.status != old_status:
            project.status = old_status

    db.add(project)
    db.flush()

    return new_status


def create_status_log(
    db: Session,
    project_id: int,
    old_stage: str,
    new_stage: str,
    old_status: str,
    new_status: str,
    old_health: str,
    new_health: Optional[str] = None,
    reason: Optional[str] = None,
    changed_by: int = 0
) -> None:
    """
    创建状态变更历史记录

    支持两种调用方式：
    - 10参数：(db, project_id, old_stage, new_stage, old_status, new_status, old_health, new_health, reason, changed_by)
    - 9参数（旧兼容）：(db, project_id, old_stage, new_stage, old_status, new_status, project_health, reason, changed_by)
    """
    # 兼容旧调用方式：如果 new_health 看起来不像健康度值，则为旧的9参数模式
    if new_health is not None and new_health not in ("H1", "H2", "H3", "H4"):
        # 旧模式：new_health 实际上是 reason，reason 实际上是 changed_by
        actual_old_health = old_health
        actual_new_health = old_health
        actual_reason = new_health
        try:
            actual_changed_by = int(reason) if reason is not None else 0
        except (ValueError, TypeError):
            actual_changed_by = 0
    else:
        actual_old_health = old_health
        actual_new_health = new_health if new_health is not None else old_health
        actual_reason = reason
        actual_changed_by = changed_by

    status_log = ProjectStatusLog(
        project_id=project_id,
        old_stage=old_stage,
        new_stage=new_stage,
        old_status=old_status,
        new_status=new_status,
        old_health=actual_old_health,
        new_health=actual_new_health,
        change_type="STAGE_ADVANCEMENT",
        change_reason=actual_reason,
        changed_by=actual_changed_by,
        changed_at=datetime.now()
    )
    db.add(status_log)
    db.flush()


def create_installation_dispatch_orders(
    db: Session,
    project: Project,
    target_stage: str,
    old_stage: str
) -> None:
    """
    如果项目进入S8阶段，自动创建安装调试派工单
    """
    if target_stage != "S8" or old_stage == "S8":
        return

    try:
        from app.api.v1.endpoints.installation_dispatch import generate_order_no
        from app.models.installation_dispatch import InstallationDispatchOrder

        # 获取项目的所有机台
        machines = db.query(Machine).filter(Machine.project_id == project.id).all()

        # 为每个机台创建安装调试派工单
        for machine in machines:
            # 检查是否已存在该机台的安装调试派工单
            existing_order = db.query(InstallationDispatchOrder).filter(
                InstallationDispatchOrder.project_id == project.id,
                InstallationDispatchOrder.machine_id == machine.id,
                InstallationDispatchOrder.status != "CANCELLED"
            ).first()

            if not existing_order:
                dispatch_order = InstallationDispatchOrder(
                    order_no=generate_order_no(db),
                    project_id=project.id,
                    machine_id=machine.id,
                    customer_id=project.customer_id,
                    task_type="INSTALLATION",
                    task_title=f"{machine.machine_no} 现场安装调试",
                    task_description=f"项目 {project.project_name} 的 {machine.machine_no} 设备现场安装调试",
                    location=getattr(project, 'customer_address', None),
                    scheduled_date=date.today() + timedelta(days=7),  # 默认7天后
                    estimated_hours=Decimal("8.0"),
                    priority="HIGH",
                    status="PENDING",
                    progress=0,
                )
                db.add(dispatch_order)
    except Exception as e:
        logger.error(f"自动创建安装调试派工单失败：{str(e)}", exc_info=True)


def generate_cost_review_report(
    db: Session,
    project_id: int,
    target_stage: str,
    new_status: str,
    current_user_id: int
) -> None:
    """
    如果项目进入S9阶段或状态变为ST30，自动生成成本复盘报告
    """
    if target_stage != "S9" and new_status != "ST30":
        return

    try:
        from app.models.project import ProjectReview
        from app.services.cost_review_service import CostReviewService

        # 自动生成成本复盘报告（如果不存在）
        existing_review = db.query(ProjectReview).filter(
            ProjectReview.project_id == project_id,
            ProjectReview.review_type == "POST_MORTEM"
        ).first()

        if not existing_review:
            CostReviewService.generate_cost_review_report(
                db, project_id, current_user_id
            )
    except Exception as e:
        logger.warning(f"自动生成成本复盘报告失败：{str(e)}")
