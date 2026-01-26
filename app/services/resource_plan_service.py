# -*- coding: utf-8 -*-
"""
资源计划服务

提供资源计划的创建、查询、分配、冲突检测等功能
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project.resource_plan import ProjectStageResourcePlan
from app.models.user import User
from app.schemas.resource_plan import (
    ConflictProject,
    EmployeeBrief,
    ResourceConflict,
    ResourcePlanCreate,
)


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
        db.add(plan)
        db.commit()
        db.refresh(plan)
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
