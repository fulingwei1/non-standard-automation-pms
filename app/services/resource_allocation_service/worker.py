# -*- coding: utf-8 -*-
"""
资源分配服务 - 人员相关
"""
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import PmoResourceAllocation, Task, Worker, WorkOrder

from .utils import calculate_overlap_days, calculate_workdays


def check_worker_availability(
    db: Session,
    worker_id: int,
    start_date: date,
    end_date: date,
    required_hours: float = 8.0,
    exclude_allocation_id: Optional[int] = None
) -> Tuple[bool, Optional[str], float]:
    """
    检查人员可用性

    Args:
        db: 数据库会话
        worker_id: 工人ID
        start_date: 计划开始日期
        end_date: 计划结束日期
        required_hours: 所需工时（默认8小时/天）
        exclude_allocation_id: 排除的资源分配ID（用于更新时检查）

    Returns:
        (是否可用, 不可用原因, 可用工时)
    """
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        return (False, "工人不存在", 0.0)

    if not worker.is_active or worker.status != 'ACTIVE':
        return (False, "工人不在职或状态异常", 0.0)

    # 计算总可用工时
    workdays = calculate_workdays(start_date, end_date)
    total_available_hours = workdays * 8.0  # 每天8小时

    # 计算已分配工时
    assigned_hours = 0.0

    # 1. 检查工单分配
    work_orders = db.query(WorkOrder).filter(
        WorkOrder.assigned_to == worker_id,
        WorkOrder.status.in_(['PLANNED', 'IN_PROGRESS', 'PAUSED']),
        WorkOrder.plan_start_date <= end_date,
        WorkOrder.plan_end_date >= start_date
    ).all()

    for wo in work_orders:
        if wo.plan_start_date and wo.plan_end_date:
            overlap_days = calculate_overlap_days(
                start_date, end_date,
                wo.plan_start_date, wo.plan_end_date
            )
            assigned_hours += overlap_days * 8.0

    # 2. 检查资源分配（PMO模块）
    allocations = db.query(PmoResourceAllocation).filter(
        PmoResourceAllocation.resource_id == worker_id,
        PmoResourceAllocation.status != 'CANCELLED',
        PmoResourceAllocation.start_date <= end_date,
        PmoResourceAllocation.end_date >= start_date
    )

    if exclude_allocation_id:
        allocations = allocations.filter(PmoResourceAllocation.id != exclude_allocation_id)

    for alloc in allocations:
        if alloc.planned_hours:
            assigned_hours += float(alloc.planned_hours)
        else:
            # 如果没有planned_hours，按天数计算
            overlap_days = calculate_overlap_days(
                start_date, end_date,
                alloc.start_date, alloc.end_date
            )
            assigned_hours += overlap_days * 8.0

    # 3. 检查任务分配（进度模块）
    tasks = db.query(Task).filter(
        Task.owner_id == worker_id,
        Task.status != 'CANCELLED',
        Task.plan_start <= end_date,
        Task.plan_end >= start_date
    ).all()

    for task in tasks:
        if task.plan_start and task.plan_end:
            overlap_days = calculate_overlap_days(
                start_date, end_date,
                task.plan_start, task.plan_end
            )
            # 假设任务占用50%时间（可配置）
            assigned_hours += overlap_days * 4.0

    # 计算可用工时
    available_hours = total_available_hours - assigned_hours

    # 检查是否满足需求
    required_total_hours = workdays * required_hours
    if available_hours < required_total_hours:
        return (
            False,
            f"可用工时不足（需要 {required_total_hours:.1f} 小时，可用 {available_hours:.1f} 小时）",
            available_hours
        )

    return (True, None, available_hours)


def find_available_workers(
    db: Session,
    workshop_id: Optional[int] = None,
    skill_required: Optional[str] = None,
    start_date: date = None,
    end_date: date = None,
    min_available_hours: float = 8.0
) -> List[Dict]:
    """
    查找可用人员

    Args:
        db: 数据库会话
        workshop_id: 车间ID（可选）
        skill_required: 所需技能（可选）
        start_date: 计划开始日期
        end_date: 计划结束日期
        min_available_hours: 最小可用工时

    Returns:
        可用人员列表
    """
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date + timedelta(days=7)

    # 查询工人
    query = db.query(Worker).filter(
        Worker.is_active == True,
        Worker.status == 'ACTIVE'
    )

    if workshop_id:
        query = query.filter(Worker.workshop_id == workshop_id)

    workers = query.all()

    available_workers = []
    for worker in workers:
        # 检查技能匹配
        skill_match = True
        matched_skills = []
        if skill_required:
            skill_match, matched_skills = check_worker_skill(
                db, worker.id, skill_required
            )
            if not skill_match:
                continue  # 技能不匹配，跳过

        is_available, reason, available_hours = check_worker_availability(
            db, worker.id, start_date, end_date
        )

        if is_available and available_hours >= min_available_hours:
            available_workers.append({
                'worker_id': worker.id,
                'worker_no': worker.worker_no,
                'worker_name': worker.worker_name,
                'workshop_id': worker.workshop_id,
                'position': worker.position,
                'skill_level': worker.skill_level,
                'available_hours': round(available_hours, 2),
                'matched_skills': matched_skills,
                'available_from': start_date,
                'available_until': end_date
            })

    # 按可用工时降序排序
    available_workers.sort(key=lambda x: x['available_hours'], reverse=True)

    return available_workers


def check_worker_skill(
    db: Session,
    worker_id: int,
    skill_required: str
) -> Tuple[bool, List[str]]:
    """
    检查工人技能匹配

    Args:
        db: 数据库会话
        worker_id: 工人ID
        skill_required: 所需技能（可以是工序编码、工序名称或工序类型）

    Returns:
        (是否匹配, 匹配的技能列表)
    """
    from app.models import ProcessDict, WorkerSkill

    # 查询工人的技能
    worker_skills = db.query(WorkerSkill).join(
        ProcessDict, WorkerSkill.process_id == ProcessDict.id
    ).filter(
        WorkerSkill.worker_id == worker_id,
        ProcessDict.is_active == True
    ).all()

    if not worker_skills:
        return (False, [])

    matched_skills = []
    skill_required_lower = skill_required.lower()

    for ws in worker_skills:
        process = ws.process
        if not process:
            continue

        # 匹配工序编码、名称或类型
        if (skill_required_lower in process.process_code.lower() or
            skill_required_lower in process.process_name.lower() or
            skill_required_lower in (process.process_type or '').lower()):
            matched_skills.append({
                'process_code': process.process_code,
                'process_name': process.process_name,
                'skill_level': ws.skill_level
            })

    return (len(matched_skills) > 0, matched_skills)
