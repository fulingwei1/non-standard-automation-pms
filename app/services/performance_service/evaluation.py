# -*- coding: utf-8 -*-
"""
绩效管理服务 - 评价任务
"""
from typing import List

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.common.date_range import get_month_range_by_ym

from app.models.organization import Department, Employee
from app.models.performance import (
    EvaluationStatusEnum,
    EvaluatorTypeEnum,
    MonthlyWorkSummary,
    PerformanceEvaluationRecord,
)
from app.models.project import Project, ProjectMember
from app.models.user import User



def create_evaluation_tasks(
    db: Session,
    summary: MonthlyWorkSummary
) -> List[PerformanceEvaluationRecord]:
    """
    员工提交工作总结后，自动创建评价任务

    Args:
        db: 数据库会话
        summary: 工作总结对象

    Returns:
        创建的评价记录列表
    """
    created_records = []
    employee = db.query(User).get(summary.employee_id)

    if not employee:
        return created_records

    # 1. 创建部门经理评价任务
    if employee.employee_id:
        # 找到员工所属部门的经理
        emp_obj = db.query(Employee).get(employee.employee_id)
        if emp_obj and emp_obj.department:
            dept = db.query(Department).filter(
                Department.dept_name == emp_obj.department,
                Department.is_active
            ).first()

            if dept and dept.manager_id:
                # 找到经理的User对象
                manager_emp = db.query(Employee).get(dept.manager_id)
                if manager_emp:
                    manager_user = db.query(User).filter(
                        User.employee_id == manager_emp.id,
                        User.is_active
                    ).first()

                    if manager_user:
                        # 检查是否已存在评价记录
                        existing = db.query(PerformanceEvaluationRecord).filter(
                            PerformanceEvaluationRecord.summary_id == summary.id,
                            PerformanceEvaluationRecord.evaluator_id == manager_user.id,
                            PerformanceEvaluationRecord.evaluator_type == EvaluatorTypeEnum.DEPT_MANAGER
                        ).first()

                        if not existing:
                            dept_eval = PerformanceEvaluationRecord(
                                summary_id=summary.id,
                                evaluator_id=manager_user.id,
                                evaluator_type=EvaluatorTypeEnum.DEPT_MANAGER,
                                project_id=None,
                                project_weight=None,
                                score=0,  # 默认0，待评价
                                comment="",
                                status=EvaluationStatusEnum.PENDING
                            )
                            db.add(dept_eval)
                            created_records.append(dept_eval)

    # 2. 创建项目经理评价任务
    # 查找员工参与的所有活跃项目
    year, month = map(int, summary.period.split('-'))
    period_start, period_end = get_month_range_by_ym(year, month)

    project_members = db.query(ProjectMember).filter(
        ProjectMember.user_id == summary.employee_id,
        ProjectMember.is_active,
        or_(
            ProjectMember.start_date.is_(None),
            ProjectMember.start_date <= period_end
        ),
        or_(
            ProjectMember.end_date.is_(None),
            ProjectMember.end_date >= period_start
        )
    ).all()

    for member in project_members:
        project = db.query(Project).filter(
            Project.id == member.project_id,
            Project.is_active
        ).first()

        if project and project.pm_id:
            # 检查是否已存在评价记录
            existing = db.query(PerformanceEvaluationRecord).filter(
                PerformanceEvaluationRecord.summary_id == summary.id,
                PerformanceEvaluationRecord.evaluator_id == project.pm_id,
                PerformanceEvaluationRecord.evaluator_type == EvaluatorTypeEnum.PROJECT_MANAGER,
                PerformanceEvaluationRecord.project_id == project.id
            ).first()

            if not existing:
                # 计算项目权重（如果有多个项目，默认平均分配）
                project_weight = 100 // len(project_members) if len(project_members) > 0 else 100

                proj_eval = PerformanceEvaluationRecord(
                    summary_id=summary.id,
                    evaluator_id=project.pm_id,
                    evaluator_type=EvaluatorTypeEnum.PROJECT_MANAGER,
                    project_id=project.id,
                    project_weight=project_weight,
                    score=0,  # 默认0，待评价
                    comment="",
                    status=EvaluationStatusEnum.PENDING
                )
                db.add(proj_eval)
                created_records.append(proj_eval)

    # 提交到数据库
    if created_records:
        db.commit()
        for record in created_records:
            db.refresh(record)

    return created_records
