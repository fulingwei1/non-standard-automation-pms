# -*- coding: utf-8 -*-
"""
资源计划服务

提供资源计划的创建、查询、分配、冲突检测等功能，
以及人员负载分析、项目资源需求预测、部门工作量统计。

NOTE: ResourcePlanningService 原位于 resource_planning_service.py，
已合并到此文件中。旧模块（兼容层）已删除。
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.progress import Task
from app.models.project import Project
from app.models.project.resource_plan import ProjectStageResourcePlan
from app.models.timesheet import Timesheet
from app.models.user import User
from app.schemas.resource_plan import (
    ConflictProject,
    EmployeeBrief,
    ResourceConflict,
    ResourcePlanCreate,
)
from app.utils.db_helpers import save_obj


class ResourcePlanService:
    """资源计划服务"""

    # ==================== 工具方法 ====================

    @staticmethod
    def calculate_fill_rate(requirements: List[ProjectStageResourcePlan]) -> float:
        """
        计算填充率

        Args:
            requirements: 资源需求列表

        Returns:
            填充率百分比 (0-100)
        """
        if not requirements:
            return 100.0

        total_headcount = sum(r.headcount for r in requirements)
        if total_headcount == 0:
            return 100.0

        filled_count = sum(
            r.headcount for r in requirements if r.assignment_status == "ASSIGNED"
        )

        return round(filled_count / total_headcount * 100, 2)

    @staticmethod
    def calculate_date_overlap(
        start1: date, end1: date, start2: date, end2: date
    ) -> Optional[Tuple[date, date]]:
        """
        计算两个日期范围的重叠部分

        Returns:
            重叠的 (开始日期, 结束日期)，无重叠返回 None
        """
        if not all([start1, end1, start2, end2]):
            return None

        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)

        if overlap_start <= overlap_end:
            return (overlap_start, overlap_end)
        return None

    @staticmethod
    def calculate_conflict_severity(total_allocation: Decimal) -> str:
        """
        计算冲突严重度

        Args:
            total_allocation: 总分配比例

        Returns:
            严重度: HIGH (>=150%), MEDIUM (>=120%), LOW (>100%)
        """
        if total_allocation >= 150:
            return "HIGH"
        elif total_allocation >= 120:
            return "MEDIUM"
        else:
            return "LOW"

    # ==================== CRUD 操作 ====================

    @staticmethod
    def get_project_resource_plans(
        db: Session, project_id: int, stage_code: Optional[str] = None
    ) -> List[ProjectStageResourcePlan]:
        """获取项目资源计划"""
        query = db.query(ProjectStageResourcePlan).filter(
            ProjectStageResourcePlan.project_id == project_id
        )
        if stage_code:
            query = query.filter(ProjectStageResourcePlan.stage_code == stage_code)
        return query.order_by(
            ProjectStageResourcePlan.stage_code, ProjectStageResourcePlan.role_code
        ).all()

    @staticmethod
    def create_resource_plan(
        db: Session, project_id: int, plan_in: ResourcePlanCreate
    ) -> ProjectStageResourcePlan:
        """创建资源计划"""
        plan = ProjectStageResourcePlan(project_id=project_id, **plan_in.model_dump())
        save_obj(db, plan)
        return plan

    @staticmethod
    def assign_employee(
        db: Session, plan_id: int, employee_id: int, force: bool = False
    ) -> Tuple[ProjectStageResourcePlan, Optional[ResourceConflict]]:
        """
        分配员工到资源计划

        Args:
            db: 数据库会话
            plan_id: 资源计划ID
            employee_id: 员工ID
            force: 是否强制分配（忽略冲突）

        Returns:
            (更新后的计划, 冲突信息或None)
        """
        plan = (
            db.query(ProjectStageResourcePlan)
            .filter(ProjectStageResourcePlan.id == plan_id)
            .first()
        )

        if not plan:
            raise ValueError("资源计划不存在")

        # 检查冲突
        conflict = ResourcePlanService.check_assignment_conflict(
            db,
            employee_id,
            plan.project_id,
            plan.planned_start,
            plan.planned_end,
            plan.allocation_pct,
        )

        if conflict and not force:
            plan.assignment_status = "CONFLICT"
            db.commit()
            return plan, conflict

        # 执行分配
        plan.assigned_employee_id = employee_id
        plan.assignment_status = "ASSIGNED"
        db.commit()
        db.refresh(plan)

        return plan, None

    @staticmethod
    def release_employee(db: Session, plan_id: int) -> ProjectStageResourcePlan:
        """释放员工分配"""
        plan = (
            db.query(ProjectStageResourcePlan)
            .filter(ProjectStageResourcePlan.id == plan_id)
            .first()
        )

        if not plan:
            raise ValueError("资源计划不存在")

        plan.assigned_employee_id = None
        plan.assignment_status = "RELEASED"
        db.commit()
        db.refresh(plan)

        return plan

    # ==================== 冲突检测 ====================

    @staticmethod
    def check_assignment_conflict(
        db: Session,
        employee_id: int,
        project_id: int,
        start_date: Optional[date],
        end_date: Optional[date],
        allocation_pct: Decimal,
    ) -> Optional[ResourceConflict]:
        """
        检查分配是否会产生冲突

        Returns:
            冲突信息，无冲突返回 None
        """
        if not start_date or not end_date:
            return None

        # 获取员工在时间范围内的其他分配
        existing = (
            db.query(ProjectStageResourcePlan)
            .filter(
                ProjectStageResourcePlan.assigned_employee_id == employee_id,
                ProjectStageResourcePlan.assignment_status == "ASSIGNED",
                ProjectStageResourcePlan.project_id != project_id,
                ProjectStageResourcePlan.planned_end >= start_date,
                ProjectStageResourcePlan.planned_start <= end_date,
            )
            .all()
        )

        for assignment in existing:
            overlap = ResourcePlanService.calculate_date_overlap(
                start_date, end_date, assignment.planned_start, assignment.planned_end
            )
            if overlap:
                total = allocation_pct + assignment.allocation_pct
                if total > 100:
                    # 获取相关信息
                    employee = db.query(User).filter(User.id == employee_id).first()
                    project = (
                        db.query(Project)
                        .filter(Project.id == assignment.project_id)
                        .first()
                    )

                    return ResourceConflict(
                        employee=EmployeeBrief(
                            id=employee.id if employee else employee_id,
                            name=employee.username if employee else "Unknown",
                            department=getattr(employee, "department", None),
                        ),
                        this_project=ConflictProject(
                            project_id=project_id,
                            project_name="当前项目",
                            stage_code="",
                            allocation_pct=allocation_pct,
                            period=f"{start_date} ~ {end_date}",
                        ),
                        conflict_with=ConflictProject(
                            project_id=project.id if project else assignment.project_id,
                            project_name=(
                                project.project_name if project else "Unknown Project"
                            ),
                            stage_code=assignment.stage_code,
                            allocation_pct=assignment.allocation_pct,
                            period=f"{assignment.planned_start} ~ {assignment.planned_end}",
                        ),
                        overlap_period=f"{overlap[0]} ~ {overlap[1]}",
                        total_allocation=total,
                        over_allocation=total - 100,
                        severity=ResourcePlanService.calculate_conflict_severity(total),
                    )

        return None

    @staticmethod
    def detect_employee_conflicts(
        db: Session, employee_id: int
    ) -> List[ResourceConflict]:
        """检测员工的所有资源冲突"""
        assignments = (
            db.query(ProjectStageResourcePlan)
            .filter(
                ProjectStageResourcePlan.assigned_employee_id == employee_id,
                ProjectStageResourcePlan.assignment_status == "ASSIGNED",
            )
            .all()
        )

        conflicts = []

        for i, a1 in enumerate(assignments):
            for a2 in assignments[i + 1 :]:
                overlap = ResourcePlanService.calculate_date_overlap(
                    a1.planned_start, a1.planned_end, a2.planned_start, a2.planned_end
                )
                if overlap:
                    total = a1.allocation_pct + a2.allocation_pct
                    if total > 100:
                        # 获取相关信息
                        employee = (
                            db.query(User).filter(User.id == employee_id).first()
                        )
                        project1 = (
                            db.query(Project)
                            .filter(Project.id == a1.project_id)
                            .first()
                        )
                        project2 = (
                            db.query(Project)
                            .filter(Project.id == a2.project_id)
                            .first()
                        )

                        conflicts.append(
                            ResourceConflict(
                                employee=EmployeeBrief(
                                    id=employee.id if employee else employee_id,
                                    name=employee.username if employee else "Unknown",
                                    department=getattr(employee, "department", None),
                                ),
                                this_project=ConflictProject(
                                    project_id=a1.project_id,
                                    project_name=(
                                        project1.project_name
                                        if project1
                                        else "Unknown"
                                    ),
                                    stage_code=a1.stage_code,
                                    allocation_pct=a1.allocation_pct,
                                    period=f"{a1.planned_start} ~ {a1.planned_end}",
                                ),
                                conflict_with=ConflictProject(
                                    project_id=a2.project_id,
                                    project_name=(
                                        project2.project_name
                                        if project2
                                        else "Unknown"
                                    ),
                                    stage_code=a2.stage_code,
                                    allocation_pct=a2.allocation_pct,
                                    period=f"{a2.planned_start} ~ {a2.planned_end}",
                                ),
                                overlap_period=f"{overlap[0]} ~ {overlap[1]}",
                                total_allocation=total,
                                over_allocation=total - 100,
                                severity=ResourcePlanService.calculate_conflict_severity(
                                    total
                                ),
                            )
                        )

        return conflicts

    @staticmethod
    def detect_project_conflicts(
        db: Session, project_id: int
    ) -> List[ResourceConflict]:
        """检测项目的所有资源冲突"""
        # 获取项目的所有已分配资源计划
        plans = (
            db.query(ProjectStageResourcePlan)
            .filter(
                ProjectStageResourcePlan.project_id == project_id,
                ProjectStageResourcePlan.assignment_status == "ASSIGNED",
                ProjectStageResourcePlan.assigned_employee_id.isnot(None),
            )
            .all()
        )

        conflicts = []
        checked_employees = set()

        for plan in plans:
            if plan.assigned_employee_id in checked_employees:
                continue

            employee_conflicts = ResourcePlanService.detect_employee_conflicts(
                db, plan.assigned_employee_id
            )

            # 只保留与当前项目相关的冲突
            for conflict in employee_conflicts:
                if (
                    conflict.this_project.project_id == project_id
                    or conflict.conflict_with.project_id == project_id
                ):
                    conflicts.append(conflict)

            checked_employees.add(plan.assigned_employee_id)

        return conflicts


class ResourcePlanningService:
    """资源规划服务

  负责人员负载分析、项目资源需求预测、部门工作量统计。

 NOTE: 此类原位于 resource_planning_service.py，已合并至此。旧模块已删除。
 """

    # 标准工时配置
    STANDARD_MONTHLY_HOURS = 176  # 标准月工时（22天 × 8小时）
    STANDARD_DAILY_HOURS = 8  # 标准日工时
    MAX_LOAD_RATE = 110  # 最大负载率（%）

    def __init__(self, db: Session):
        self.db = db

    def analyze_user_workload(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        分析用户工作负载

        Args:
            user_id: 用户ID
            start_date: 开始日期（可选，默认未来30天）
            end_date: 结束日期（可选，默认未来30天）

        Returns:
            工作负载分析结果
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {'error': '用户不存在'}

        # 默认分析未来30天
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=30)

        # 查询已分配的任务（预估工时）
        tasks = self.db.query(Task).filter(
            Task.assignee_id == user_id,
            Task.status.in_(['PENDING', 'IN_PROGRESS']),
            Task.plan_start_date <= end_date,
            Task.plan_end_date >= start_date
        ).all()

        # 计算已分配工时
        assigned_hours = sum(float(task.estimated_hours or 0) for task in tasks)

        # 查询已记录的工时
        recorded_timesheets = self.db.query(Timesheet).filter(
            Timesheet.user_id == user_id,
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date,
            Timesheet.status == 'APPROVED'
        ).all()

        recorded_hours = sum(float(ts.hours or 0) for ts in recorded_timesheets)

        # 计算标准工时
        work_days = self._calculate_work_days(start_date, end_date)
        standard_hours = work_days * self.STANDARD_DAILY_HOURS

        # 计算负载率
        total_hours = assigned_hours + recorded_hours
        load_rate = (total_hours / standard_hours * 100) if standard_hours > 0 else 0

        # 按项目统计
        project_loads = {}
        for task in tasks:
            if task.project_id:
                project_key = task.project_id
                if project_key not in project_loads:
                    project = self.db.query(Project).filter(Project.id == project_key).first()
                    project_loads[project_key] = {
                        'project_id': project_key,
                        'project_code': project.project_code if project else None,
                        'project_name': project.project_name if project else None,
                        'assigned_hours': 0,
                        'task_count': 0
                    }
                project_loads[project_key]['assigned_hours'] += float(task.estimated_hours or 0)
                project_loads[project_key]['task_count'] += 1

        return {
            'user_id': user_id,
            'user_name': user.real_name or user.username,
            'start_date': str(start_date),
            'end_date': str(end_date),
            'work_days': work_days,
            'standard_hours': standard_hours,
            'assigned_hours': assigned_hours,
            'recorded_hours': recorded_hours,
            'total_hours': total_hours,
            'load_rate': load_rate,
            'is_overloaded': load_rate > self.MAX_LOAD_RATE,
            'project_loads': list(project_loads.values())
        }

    def predict_project_resource_needs(
        self,
        project_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        预测项目资源需求

        Args:
            project_id: 项目ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            资源需求预测
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {'error': '项目不存在'}

        # 查询项目任务
        query = self.db.query(Task).filter(Task.project_id == project_id)

        if start_date:
            query = query.filter(Task.plan_start_date >= start_date)
        if end_date:
            query = query.filter(Task.plan_end_date <= end_date)

        tasks = query.all()

        # 按人员统计需求
        resource_needs = {}
        for task in tasks:
            if task.assignee_id:
                user_key = task.assignee_id
                if user_key not in resource_needs:
                    user = self.db.query(User).filter(User.id == user_key).first()
                    resource_needs[user_key] = {
                        'user_id': user_key,
                        'user_name': user.real_name or user.username if user else None,
                        'total_hours': 0,
                        'task_count': 0,
                        'tasks': []
                    }
                resource_needs[user_key]['total_hours'] += float(task.estimated_hours or 0)
                resource_needs[user_key]['task_count'] += 1
                resource_needs[user_key]['tasks'].append({
                    'task_id': task.id,
                    'task_name': task.task_name,
                    'estimated_hours': float(task.estimated_hours or 0),
                    'plan_start_date': str(task.plan_start_date) if task.plan_start_date else None,
                    'plan_end_date': str(task.plan_end_date) if task.plan_end_date else None
                })

        # 计算总需求
        total_hours = sum(r['total_hours'] for r in resource_needs.values())
        total_personnel = len(resource_needs)

        return {
            'project_id': project_id,
            'project_code': project.project_code,
            'project_name': project.project_name,
            'total_hours': total_hours,
            'total_personnel': total_personnel,
            'resource_needs': list(resource_needs.values()),
            'start_date': str(start_date) if start_date else None,
            'end_date': str(end_date) if end_date else None
        }

    def get_department_workload_stats(
        self,
        department_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取部门工作量统计

        Args:
            department_id: 部门ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            部门工作量统计
        """
        department = self.db.query(Department).filter(Department.id == department_id).first()
        if not department:
            return {'error': '部门不存在'}

        # 获取部门成员
        users = self.db.query(User).filter(User.department_id == department_id).all()
        user_ids = [u.id for u in users]

        if not user_ids:
            return {
                'department_id': department_id,
                'department_name': department.name,
                'total_users': 0,
                'total_hours': 0,
                'user_workloads': []
            }

        # 默认统计未来30天
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=30)

        # 计算每个用户的工作负载
        user_workloads = []
        for user_id in user_ids:
            workload = self.analyze_user_workload(user_id, start_date, end_date)
            if 'error' not in workload:
                user_workloads.append(workload)

        # 汇总统计
        total_hours = sum(w.get('total_hours', 0) for w in user_workloads)
        overloaded_users = [w for w in user_workloads if w.get('is_overloaded', False)]

        return {
            'department_id': department_id,
            'department_name': department.name,
            'total_users': len(user_workloads),
            'total_hours': total_hours,
            'overloaded_count': len(overloaded_users),
            'user_workloads': user_workloads,
            'start_date': str(start_date),
            'end_date': str(end_date)
        }

    def _calculate_work_days(self, start_date: date, end_date: date) -> int:
        """
        计算工作日数（简化处理，排除周末）

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            工作日数
        """
        work_days = 0
        current_date = start_date
        while current_date <= end_date:
            # 0=Monday, 6=Sunday
            if current_date.weekday() < 5:  # 周一到周五
                work_days += 1
            current_date += timedelta(days=1)
        return work_days
