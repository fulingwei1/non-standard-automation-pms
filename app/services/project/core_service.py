# -*- coding: utf-8 -*-
"""
项目核心聚合服务

提供项目基础查询与“我的项目/部门项目”分页能力，供 API 层和其他
聚合服务（执行、资源、财务、分析）复用。
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from app.common.pagination import get_pagination_params
from app.common.query_filters import apply_pagination
from app.models.organization import Department
from app.models.project import Project, ProjectMember
from app.models.task_center import TaskUnified
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.engineer import MyProjectListResponse, MyProjectResponse, TaskStatsResponse
from app.schemas.project import ProjectListResponse
from app.services.data_scope import DataScopeService


class ProjectCoreService:
    """集中处理项目列表、分页和个人视角查询的服务类。"""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------ #
    # 基础查询与分页
    # ------------------------------------------------------------------ #
    def _base_query(self) -> Query:
        return self.db.query(Project).filter(Project.is_active == True)  # noqa: E712

    def get_scoped_query(self, current_user: User) -> Query:
        """返回已应用数据权限过滤的项目查询。"""
        query = self._base_query()
        return DataScopeService.filter_projects_by_scope(self.db, query, current_user)

    @staticmethod
    def _paginate(query: Query, page: int, page_size: int) -> Tuple[int, int, Sequence[Project]]:
        pagination = get_pagination_params(page=page, page_size=page_size)
        total = query.count()
        query = apply_pagination(query, pagination.offset, pagination.limit)
        items = query.all()
        return total, pagination.pages_for_total(total), items

    # ------------------------------------------------------------------ #
    # 我的项目
    # ------------------------------------------------------------------ #
    def list_user_projects(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
    ) -> MyProjectListResponse:
        project_ids = self._collect_user_project_ids(current_user)
        if not project_ids:
            return MyProjectListResponse(items=[], total=0, page=page, page_size=page_size, pages=0)

        query = self.db.query(Project).filter(Project.id.in_(project_ids))
        query = query.order_by(Project.updated_at.desc().nullslast(), Project.id.desc())

        total, pages, projects = self._paginate(query, page, page_size)
        memberships = self._load_memberships(current_user.id, [p.id for p in projects])
        task_stats = self._build_task_stats(current_user.id, [p.id for p in projects])

        items: List[MyProjectResponse] = []
        for project in projects:
            member_info = memberships.get(project.id, {})
            roles = member_info.get("roles", [])
            allocations = member_info.get("allocations", [])

            if not roles and project.pm_id == current_user.id:
                roles = ["PM"]

            avg_allocation = (
                round(sum(allocations) / len(allocations), 2) if allocations else 100.0
            )
            stats = task_stats.get(project.id, TaskStatsResponse())

            items.append(
                MyProjectResponse(
                    project_id=project.id,
                    project_code=project.project_code,
                    project_name=project.project_name,
                    customer_name=self._get_customer_name(project),
                    stage=project.stage or "S1",
                    status=project.status or "ST01",
                    health=project.health or "H1",
                    progress_pct=float(project.progress_pct or 0),
                    my_roles=roles,
                    my_allocation_pct=int(avg_allocation),
                    task_stats=stats,
                    planned_start_date=project.planned_start_date,
                    planned_end_date=project.planned_end_date,
                    last_activity_at=project.updated_at,
                )
            )

        return MyProjectListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def _collect_user_project_ids(self, current_user: User) -> List[int]:
        member_ids = [
            project_id
            for (project_id,) in self.db.query(ProjectMember.project_id)
            .filter(
                ProjectMember.user_id == current_user.id,
                ProjectMember.is_active == True,  # noqa: E712
            )
            .all()
        ]
        owned_ids = [
            project_id
            for (project_id,) in self.db.query(Project.id)
            .filter(or_(Project.pm_id == current_user.id, Project.created_by == current_user.id))
            .all()
        ]
        return sorted({*member_ids, *owned_ids})

    def _load_memberships(self, user_id: int, project_ids: List[int]) -> Dict[int, Dict[str, List[float]]]:
        if not project_ids:
            return {}

        rows = (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.user_id == user_id,
                ProjectMember.project_id.in_(project_ids),
                ProjectMember.is_active == True,  # noqa: E712
            )
            .all()
        )

        mapping: Dict[int, Dict[str, List[float]]] = {}
        for member in rows:
            project_info = mapping.setdefault(member.project_id, {"roles": [], "allocations": []})
            if member.role_code:
                project_info["roles"].append(member.role_code)
            if member.allocation_pct is not None:
                project_info["allocations"].append(float(member.allocation_pct))
        return mapping

    def _build_task_stats(self, user_id: int, project_ids: List[int]) -> Dict[int, TaskStatsResponse]:
        if not project_ids:
            return {}

        tasks = (
            self.db.query(TaskUnified)
            .filter(
                TaskUnified.assignee_id == user_id,
                TaskUnified.project_id.in_(project_ids),
                TaskUnified.is_active == True,  # noqa: E712
            )
            .all()
        )

        stats_map: Dict[int, Dict[str, int]] = {}
        now = datetime.utcnow()
        for task in tasks:
            bucket = stats_map.setdefault(
                task.project_id,
                {
                    "total": 0,
                    "pending": 0,
                    "in_progress": 0,
                    "completed": 0,
                    "overdue": 0,
                    "delayed": 0,
                    "pending_approval": 0,
                },
            )
            bucket["total"] += 1
            status = (task.status or "").upper()
            if status in {"PENDING", "ACCEPTED"}:
                bucket["pending"] += 1
            elif status in {"IN_PROGRESS", "PAUSED"}:
                bucket["in_progress"] += 1
            elif status in {"COMPLETED", "APPROVED"}:
                bucket["completed"] += 1

            if (
                task.deadline
                and task.deadline < now
                and status not in {"COMPLETED", "CANCELLED", "APPROVED"}
            ):
                bucket["overdue"] += 1
            if getattr(task, "is_delayed", False):
                bucket["delayed"] += 1
            if getattr(task, "approval_status", None) == "PENDING_APPROVAL":
                bucket["pending_approval"] += 1

        return {
            project_id: TaskStatsResponse(
                total_tasks=data["total"],
                pending_tasks=data["pending"],
                in_progress_tasks=data["in_progress"],
                completed_tasks=data["completed"],
                overdue_tasks=data["overdue"],
                delayed_tasks=data["delayed"],
                pending_approval_tasks=data["pending_approval"],
            )
            for project_id, data in stats_map.items()
        }

    # ------------------------------------------------------------------ #
    # 部门项目
    # ------------------------------------------------------------------ #
    def list_department_projects(
        self,
        dept_id: int,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[ProjectListResponse]:
        query = self._base_query().filter(Project.dept_id == dept_id)
        query = DataScopeService.filter_projects_by_scope(self.db, query, current_user)
        query = query.order_by(Project.updated_at.desc().nullslast(), Project.id.desc())

        total, pages, projects = self._paginate(query, page, page_size)
        items = [self._to_project_list_response(p) for p in projects]

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    # ------------------------------------------------------------------ #
    # 工具方法
    # ------------------------------------------------------------------ #
    @staticmethod
    def _get_customer_name(project: Project) -> Optional[str]:
        if project.customer_name:
            return project.customer_name
        if getattr(project, "customer", None):
            return project.customer.customer_name
        return None

    @staticmethod
    def _to_project_list_response(project: Project) -> ProjectListResponse:
        customer_name = project.customer_name
        if not customer_name and getattr(project, "customer", None):
            customer_name = project.customer.customer_name

        pm_name = project.pm_name
        if not pm_name and getattr(project, "manager", None):
            pm_name = project.manager.real_name or project.manager.username

        return ProjectListResponse(
            id=project.id,
            project_code=project.project_code,
            project_name=project.project_name,
            customer_name=customer_name,
            stage=project.stage or "S1",
            health=project.health or "H1",
            progress_pct=project.progress_pct or 0,
            pm_name=pm_name,
            pm_id=project.pm_id,
            sales_id=getattr(project, "salesperson_id", None),
            te_id=getattr(project, "te_id", None),
        )

    def get_department(self, dept_id: int) -> Optional[Department]:
        """获取部门对象，供 API 层做 404 检查。"""
        return self.db.query(Department).filter(Department.id == dept_id).first()
