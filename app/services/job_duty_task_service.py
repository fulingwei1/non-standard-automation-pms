# -*- coding: utf-8 -*-
"""
岗位职责任务生成服务

提取岗位职责模板任务生成的业务逻辑
"""

import calendar
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.task_center import JobDutyTemplate, TaskUnified
from app.models.user import User


def should_generate_task(
    template: JobDutyTemplate,
    today: date
) -> Tuple[bool, date]:
    """
    判断是否需要生成任务

    Args:
        template: 岗位职责模板
        today: 当前日期

    Returns:
        (是否需要生成, 目标日期)
    """
    should_generate = False
    target_date = today

    if template.frequency == 'DAILY':
        # 每天生成
        should_generate = True
        target_date = today + timedelta(days=template.generate_before_days or 0)

    elif template.frequency == 'WEEKLY':
        # 每周生成（检查是否是目标星期几）
        if template.day_of_week:
            # 计算本周的目标日期
            days_until_target = (template.day_of_week - today.weekday() - 1) % 7
            if days_until_target == 0:  # 今天就是目标日期
                should_generate = True
                target_date = today + timedelta(days=template.generate_before_days or 0)
            elif 0 < days_until_target <= (template.generate_before_days or 3):
                # 在提前生成范围内
                should_generate = True
                target_date = today + timedelta(days=days_until_target)

    elif template.frequency == 'MONTHLY':
        # 每月生成（检查是否是目标日期）
        if template.day_of_month:
            # 计算本月的目标日期
            last_day = calendar.monthrange(today.year, today.month)[1]
            target_day = min(template.day_of_month, last_day)
            target_date_in_month = date(today.year, today.month, target_day)

            days_until_target = (target_date_in_month - today).days
            if days_until_target == 0:  # 今天就是目标日期
                should_generate = True
                target_date = today + timedelta(days=template.generate_before_days or 0)
            elif 0 < days_until_target <= (template.generate_before_days or 3):
                # 在提前生成范围内
                should_generate = True
                target_date = target_date_in_month

    elif template.frequency == 'YEARLY':
        # 每年生成（检查是否是目标月份和日期）
        if template.month_of_year and template.day_of_month:
            target_date_in_year = date(today.year, template.month_of_year,
                                      min(template.day_of_month,
                                          calendar.monthrange(today.year, template.month_of_year)[1]))
            days_until_target = (target_date_in_year - today).days
            if days_until_target == 0:  # 今天就是目标日期
                should_generate = True
                target_date = today + timedelta(days=template.generate_before_days or 0)
            elif 0 < days_until_target <= (template.generate_before_days or 3):
                # 在提前生成范围内
                should_generate = True
                target_date = target_date_in_year

    return should_generate, target_date


def find_template_users(
    db: Session,
    template: JobDutyTemplate
) -> List[User]:
    """
    查找模板对应的用户列表

    Args:
        db: 数据库会话
        template: 岗位职责模板

    Returns:
        用户列表
    """
    users = []

    # 如果User表有position_id字段
    if hasattr(User, 'position_id') and template.position_id:
        users = db.query(User).filter(
            User.position_id == template.position_id,
            User.is_active == True
        ).all()
    elif template.department_id:
        # 如果有部门ID，通过部门查找用户
        if hasattr(User, 'department_id'):
            users = db.query(User).filter(
                User.department_id == template.department_id,
                User.is_active == True
            ).all()

    return users


def create_task_from_template(
    db: Session,
    template: JobDutyTemplate,
    user: User,
    target_date: date,
    generate_task_code_func
) -> TaskUnified:
    """
    根据模板为用户创建任务

    Args:
        db: 数据库会话
        template: 岗位职责模板
        user: 用户
        target_date: 目标日期
        generate_task_code_func: 任务编号生成函数

    Returns:
        创建的任务对象
    """
    # 计算截止日期
    deadline = target_date + timedelta(days=template.deadline_offset_days or 0)

    # 生成任务编号
    task_code = generate_task_code_func(db)

    task = TaskUnified(
        task_code=task_code,
        title=f"{template.duty_name}",
        description=template.duty_description,
        task_type='JOB_DUTY',
        assignee_id=user.id,
        assignee_name=user.real_name or user.username,
        assigner_id=None,  # 系统自动生成
        assigner_name='系统',
        plan_start_date=target_date,
        plan_end_date=target_date,
        deadline=deadline,
        estimated_hours=template.estimated_hours,
        priority=template.default_priority or 'MEDIUM',
        is_urgent=False,
        tags=['岗位职责'],
        category='JOB_DUTY',
        reminder_enabled=True,
        reminder_before_hours=24,
        status='PENDING',
        source_type='JOB_DUTY_TEMPLATE',
        source_id=template.id,
        created_by=None  # 系统生成
    )

    return task


def check_task_exists(
    db: Session,
    template: JobDutyTemplate,
    target_date: date
) -> bool:
    """
    检查是否已经生成过该日期的任务

    Args:
        db: 数据库会话
        template: 岗位职责模板
        target_date: 目标日期

    Returns:
        是否存在
    """
    existing_task = db.query(TaskUnified).filter(
        TaskUnified.task_type == 'JOB_DUTY',
        TaskUnified.source_type == 'JOB_DUTY_TEMPLATE',
        TaskUnified.source_id == template.id,
        TaskUnified.plan_start_date == target_date
    ).first()

    return existing_task is not None
