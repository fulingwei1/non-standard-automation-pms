# -*- coding: utf-8 -*-
"""
项目CRUD服务层

负责处理项目的核心业务逻辑：
- 项目列表查询、筛选、排序
- 项目创建、更新、删除
- 冗余字段维护
- 缓存管理
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import desc, case
from sqlalchemy.orm import Session, joinedload, selectinload

from app.common.pagination import PaginationParams
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.models.project import Customer, Project, ProjectMember
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectMemberResponse,
    MachineResponse,
    MilestoneResponse,
)
from app.utils.db_helpers import save_obj

logger = logging.getLogger(__name__)


class ProjectCrudService:
    """项目CRUD业务逻辑服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_projects_query(
        self,
        keyword: Optional[str] = None,
        customer_id: Optional[int] = None,
        stage: Optional[str] = None,
        status: Optional[str] = None,
        health: Optional[str] = None,
        project_type: Optional[str] = None,
        pm_id: Optional[int] = None,
        min_progress: Optional[float] = None,
        max_progress: Optional[float] = None,
        is_active: Optional[bool] = None,
        overrun_only: bool = False,
        current_user: Optional[User] = None,
    ):
        """构建项目查询（应用所有筛选条件）"""
        query = self.db.query(Project)

        # 关键词搜索
        query = apply_keyword_filter(
            query, Project, keyword, ["project_name", "project_code", "contract_no"]
        )

        # 客户筛选
        if customer_id:
            query = query.filter(Project.customer_id == customer_id)

        # 阶段筛选
        if stage:
            query = query.filter(Project.stage == stage)

        # 状态筛选
        if status:
            query = query.filter(Project.status == status)

        # 健康度筛选
        if health:
            query = query.filter(Project.health == health)

        # 项目类型筛选
        if project_type:
            query = query.filter(Project.project_type == project_type)

        # 项目经理筛选
        if pm_id:
            query = query.filter(Project.pm_id == pm_id)

        # 进度筛选
        if min_progress is not None:
            query = query.filter(Project.progress_pct >= min_progress)
        if max_progress is not None:
            query = query.filter(Project.progress_pct <= max_progress)

        # 是否启用筛选
        if is_active is not None:
            query = query.filter(Project.is_active == is_active)

        # 超支项目筛选
        if overrun_only:
            query = query.filter(
                Project.actual_cost > Project.budget_amount,
                Project.budget_amount > 0
            )

        # 应用数据权限过滤
        if current_user:
            from app.services.data_scope import DataScopeService
            query = DataScopeService.filter_projects_by_scope(
                self.db, query, current_user
            )

        return query

    def apply_sorting(self, query, sort: Optional[str] = None):
        """应用排序逻辑"""
        if sort == "cost_desc":
            query = query.order_by(desc(Project.actual_cost))
        elif sort == "cost_asc":
            query = query.order_by(Project.actual_cost)
        elif sort == "budget_used_pct":
            # 按预算使用率排序（避免除以0）
            budget_used_expr = case(
                (Project.budget_amount > 0, Project.actual_cost / Project.budget_amount),
                else_=0
            )
            query = query.order_by(desc(budget_used_expr))
        else:
            # 默认按创建时间倒序
            query = query.order_by(desc(Project.created_at))

        return query

    def get_projects_with_pagination(
        self,
        pagination: PaginationParams,
        keyword: Optional[str] = None,
        customer_id: Optional[int] = None,
        stage: Optional[str] = None,
        status: Optional[str] = None,
        health: Optional[str] = None,
        project_type: Optional[str] = None,
        pm_id: Optional[int] = None,
        min_progress: Optional[float] = None,
        max_progress: Optional[float] = None,
        is_active: Optional[bool] = None,
        overrun_only: bool = False,
        sort: Optional[str] = None,
        current_user: Optional[User] = None,
    ) -> Tuple[List[Project], int]:
        """获取分页的项目列表"""
        query = self.get_projects_query(
            keyword=keyword,
            customer_id=customer_id,
            stage=stage,
            status=status,
            health=health,
            project_type=project_type,
            pm_id=pm_id,
            min_progress=min_progress,
            max_progress=max_progress,
            is_active=is_active,
            overrun_only=overrun_only,
            current_user=current_user,
        )

        # 使用selectinload优化关联查询
        query = query.options(
            selectinload(Project.customer),
            selectinload(Project.manager)
        )

        # 应用排序
        query = self.apply_sorting(query, sort)

        # 总数统计
        try:
            count_result = query.count()
            total = int(count_result) if count_result is not None else 0
        except Exception:
            logger.debug("项目列表统计总数失败，降级为 0", exc_info=True)
            total = 0

        # 分页
        projects = apply_pagination(query, pagination.offset, pagination.limit).all()

        return projects, total

    def populate_redundant_fields(self, projects: List[Project]) -> None:
        """补充项目的冗余字段"""
        for project in projects:
            if not project.customer_name and project.customer:
                project.customer_name = project.customer.customer_name
            if not project.pm_name and project.manager:
                project.pm_name = project.manager.real_name or project.manager.username

    def check_project_code_exists(self, project_code: str) -> bool:
        """检查项目编码是否已存在"""
        project = (
            self.db.query(Project)
            .filter(Project.project_code == project_code)
            .first()
        )
        return project is not None

    def create_project(self, project_in: ProjectCreate) -> Project:
        """创建新项目"""
        # 检查项目编码唯一性
        if self.check_project_code_exists(project_in.project_code):
            raise HTTPException(
                status_code=400,
                detail="The project with this project number already exists in the system.",
            )

        # 准备项目数据
        project_data = project_in.model_dump()
        project_data.pop("machine_count", None)

        project = Project(**project_data)

        # 填充冗余字段
        self._populate_project_redundant_fields(project)

        # 保存项目
        save_obj(self.db, project)

        # 初始化标准阶段
        from app.utils.project_utils import init_project_stages
        init_project_stages(self.db, project.id)

        return project

    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """根据ID获取项目（含关联数据）"""
        project = (
            self.db.query(Project)
            .options(
                joinedload(Project.customer),
                joinedload(Project.manager),
            )
            .filter(Project.id == project_id)
            .first()
        )

        if project:
            # 补充冗余字段
            if not project.customer_name and project.customer:
                project.customer_name = project.customer.customer_name
                project.customer_contact = project.customer.contact_person
                project.customer_phone = project.customer.contact_phone
            if not project.pm_name and project.manager:
                project.pm_name = project.manager.real_name or project.manager.username

        return project

    def get_project_members(self, project_id: int) -> List[ProjectMemberResponse]:
        """获取项目成员列表"""
        members_query = (
            self.db.query(ProjectMember)
            .options(joinedload(ProjectMember.user))
            .filter(ProjectMember.project_id == project_id)
            .all()
        )

        members = []
        for member in members_query:
            member_data = {
                "id": member.id,
                "project_id": member.project_id,
                "user_id": member.user_id,
                "username": member.user.username if member.user else f"user_{member.user_id}",
                "real_name": member.user.real_name if member.user and member.user.real_name else None,
                "role_code": member.role_code,
                "allocation_pct": member.allocation_pct,
                "start_date": member.start_date,
                "end_date": member.end_date,
                "is_active": member.is_active,
                "remark": member.remark,
            }
            members.append(ProjectMemberResponse(**member_data))

        return members

    def get_project_machines(self, project: Project) -> List[MachineResponse]:
        """获取项目设备列表"""
        machines_query = project.machines.all() if hasattr(project.machines, 'all') else []
        return [MachineResponse.model_validate(m) for m in machines_query]

    def get_project_milestones(self, project: Project) -> List[MilestoneResponse]:
        """获取项目里程碑列表"""
        milestones_query = project.milestones.all() if hasattr(project.milestones, 'all') else []
        return [MilestoneResponse.model_validate(m) for m in milestones_query]

    def update_project(self, project: Project, update_data: Dict[str, Any]) -> Project:
        """更新项目"""
        for field, value in update_data.items():
            if hasattr(project, field):
                setattr(project, field, value)

        # 更新冗余字段（如果ID改变）
        if "customer_id" in update_data:
            self._update_customer_redundant_fields(project)

        if "pm_id" in update_data:
            self._update_pm_redundant_fields(project)

        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        return project

    def soft_delete_project(self, project: Project) -> None:
        """软删除项目"""
        project.is_active = False
        self.db.add(project)
        self.db.commit()

    def invalidate_project_cache(self, project_id: Optional[int] = None) -> None:
        """使项目缓存失效"""
        try:
            from app.services.cache_service import CacheService
            cache_service = CacheService()
            if project_id:
                cache_service.invalidate_project_detail(project_id)
            cache_service.invalidate_project_list()
        except Exception:
            logger.debug("项目缓存失效失败，忽略", exc_info=True)

    # 私有方法

    def _populate_project_redundant_fields(self, project: Project) -> None:
        """填充新项目的冗余字段"""
        if project.customer_id:
            self._update_customer_redundant_fields(project)

        if project.pm_id:
            self._update_pm_redundant_fields(project)

    def _update_customer_redundant_fields(self, project: Project) -> None:
        """更新客户相关冗余字段"""
        customer = self.db.query(Customer).get(project.customer_id)
        if customer:
            project.customer_name = customer.customer_name
            project.customer_contact = customer.contact_person
            project.customer_phone = customer.contact_phone

    def _update_pm_redundant_fields(self, project: Project) -> None:
        """更新项目经理相关冗余字段"""
        pm = self.db.query(User).get(project.pm_id)
        if pm:
            project.pm_name = pm.real_name or pm.username
