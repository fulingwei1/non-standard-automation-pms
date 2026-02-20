# -*- coding: utf-8 -*-
"""
工时记录服务层
从 endpoints 中提取业务逻辑
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User
from app.schemas.timesheet import (
    TimesheetCreate,
    TimesheetResponse,
    TimesheetUpdate,
)
from app.utils.db_helpers import delete_obj, get_or_404, save_obj


class TimesheetRecordsService:
    """工时记录业务逻辑服务"""

    def __init__(self, db: Session):
        self.db = db

    def list_timesheets(
        self,
        current_user: User,
        offset: int,
        limit: int,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None,
    ) -> Tuple[List[TimesheetResponse], int]:
        """
        获取工时记录列表（分页+筛选）

        Returns:
            Tuple[List[TimesheetResponse], int]: (工时记录列表, 总数)
        """
        from app.core.permissions.timesheet import apply_timesheet_access_filter

        query = self.db.query(Timesheet)
        query = apply_timesheet_access_filter(query, self.db, current_user)

        # 应用筛选条件
        if user_id:
            query = query.filter(Timesheet.user_id == user_id)
        if project_id:
            query = query.filter(Timesheet.project_id == project_id)
        if start_date:
            query = query.filter(Timesheet.work_date >= start_date)
        if end_date:
            query = query.filter(Timesheet.work_date <= end_date)
        if status:
            query = query.filter(Timesheet.status == status)

        total = query.count()

        # 排序和分页
        query = query.order_by(desc(Timesheet.work_date), desc(Timesheet.created_at))
        timesheets = query.offset(offset).limit(limit).all()

        # 构建响应
        items = [self._build_timesheet_response(ts) for ts in timesheets]

        return items, total

    def create_timesheet(
        self, timesheet_in: TimesheetCreate, current_user: User
    ) -> TimesheetResponse:
        """
        创建单条工时记录

        Args:
            timesheet_in: 工时创建数据
            current_user: 当前用户

        Returns:
            TimesheetResponse: 创建的工时记录

        Raises:
            HTTPException: 验证失败时抛出
        """
        # 验证项目
        self._validate_projects(timesheet_in.project_id, timesheet_in.rd_project_id)

        # 检查重复记录
        self._check_duplicate_timesheet(
            current_user.id,
            timesheet_in.work_date,
            timesheet_in.project_id,
            timesheet_in.rd_project_id,
        )

        # 获取用户和部门信息
        user_info = self._get_user_info(current_user.id)

        # 获取项目信息
        project_info = self._get_project_info(timesheet_in.project_id)

        # 创建工时记录
        timesheet = Timesheet(
            user_id=current_user.id,
            user_name=user_info["user_name"],
            department_id=user_info["department_id"],
            department_name=user_info["department_name"],
            project_id=timesheet_in.project_id,
            project_code=project_info["project_code"],
            project_name=project_info["project_name"],
            rd_project_id=timesheet_in.rd_project_id,
            task_id=timesheet_in.task_id,
            work_date=timesheet_in.work_date,
            hours=timesheet_in.work_hours,
            overtime_type=timesheet_in.work_type,
            work_content=timesheet_in.description,
            status="DRAFT",
            created_by=current_user.id,
        )

        save_obj(self.db, timesheet)

        return self.get_timesheet_detail(timesheet.id, current_user)

    def batch_create_timesheets(
        self, timesheets_data: List[TimesheetCreate], current_user: User
    ) -> Dict[str, Any]:
        """
        批量创建工时记录

        Args:
            timesheets_data: 工时记录列表
            current_user: 当前用户

        Returns:
            Dict: 包含成功数、失败数和错误信息
        """
        success_count = 0
        failed_count = 0
        errors = []

        for ts_in in timesheets_data:
            try:
                # 验证项目
                if ts_in.project_id:
                    project = (
                        self.db.query(Project)
                        .filter(Project.id == ts_in.project_id)
                        .first()
                    )
                    if not project:
                        errors.append(
                            {"date": ts_in.work_date.isoformat(), "error": "项目不存在"}
                        )
                        failed_count += 1
                        continue

                # 检查重复
                existing = (
                    self.db.query(Timesheet)
                    .filter(
                        Timesheet.user_id == current_user.id,
                        Timesheet.work_date == ts_in.work_date,
                        Timesheet.project_id == ts_in.project_id,
                        Timesheet.status != "REJECTED",
                    )
                    .first()
                )

                if existing:
                    errors.append(
                        {"date": ts_in.work_date.isoformat(), "error": "该日期已有记录"}
                    )
                    failed_count += 1
                    continue

                # 获取用户和项目信息
                user_info = self._get_user_info(current_user.id)
                project_info = self._get_project_info(ts_in.project_id)

                timesheet = Timesheet(
                    user_id=current_user.id,
                    user_name=user_info["user_name"],
                    project_id=ts_in.project_id,
                    project_code=project_info["project_code"],
                    project_name=project_info["project_name"],
                    task_id=ts_in.task_id,
                    work_date=ts_in.work_date,
                    hours=ts_in.work_hours,
                    overtime_type=ts_in.work_type,
                    work_content=ts_in.description,
                    status="DRAFT",
                    created_by=current_user.id,
                )

                self.db.add(timesheet)
                success_count += 1
            except Exception as e:
                errors.append(
                    {
                        "date": (
                            ts_in.work_date.isoformat() if ts_in.work_date else None
                        ),
                        "error": str(e),
                    }
                )
                failed_count += 1

        self.db.commit()

        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors,
        }

    def get_timesheet_detail(
        self, timesheet_id: int, current_user: User
    ) -> TimesheetResponse:
        """
        获取工时记录详情

        Args:
            timesheet_id: 工时记录ID
            current_user: 当前用户

        Returns:
            TimesheetResponse: 工时记录详情

        Raises:
            HTTPException: 记录不存在或权限不足时抛出
        """
        timesheet = get_or_404(self.db, Timesheet, timesheet_id, "工时记录不存在")

        # 权限检查
        self._check_access_permission(timesheet, current_user)

        return self._build_timesheet_detail_response(timesheet)

    def update_timesheet(
        self, timesheet_id: int, timesheet_in: TimesheetUpdate, current_user: User
    ) -> TimesheetResponse:
        """
        更新工时记录

        Args:
            timesheet_id: 工时记录ID
            timesheet_in: 更新数据
            current_user: 当前用户

        Returns:
            TimesheetResponse: 更新后的工时记录

        Raises:
            HTTPException: 验证失败时抛出
        """
        timesheet = get_or_404(self.db, Timesheet, timesheet_id, "工时记录不存在")

        # 权限检查：只能修改自己的记录
        if timesheet.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权修改此记录")

        # 状态检查：只能修改草稿
        if timesheet.status != "DRAFT":
            raise HTTPException(status_code=400, detail="只能修改草稿状态的记录")

        # 更新字段
        if timesheet_in.work_date is not None:
            timesheet.work_date = timesheet_in.work_date
        if timesheet_in.work_hours is not None:
            timesheet.hours = timesheet_in.work_hours
        if timesheet_in.work_type is not None:
            timesheet.overtime_type = timesheet_in.work_type
        if timesheet_in.description is not None:
            timesheet.work_content = timesheet_in.description

        save_obj(self.db, timesheet)

        return self.get_timesheet_detail(timesheet_id, current_user)

    def delete_timesheet(self, timesheet_id: int, current_user: User) -> None:
        """
        删除工时记录（仅草稿）

        Args:
            timesheet_id: 工时记录ID
            current_user: 当前用户

        Raises:
            HTTPException: 验证失败时抛出
        """
        timesheet = get_or_404(self.db, Timesheet, timesheet_id, "工时记录不存在")

        # 权限检查
        if timesheet.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权删除此记录")

        # 状态检查
        if timesheet.status != "DRAFT":
            raise HTTPException(status_code=400, detail="只能删除草稿状态的记录")

        delete_obj(self.db, timesheet)

    # ==================== 私有辅助方法 ====================

    def _validate_projects(
        self, project_id: Optional[int], rd_project_id: Optional[int]
    ) -> None:
        """验证项目ID"""
        if not project_id and not rd_project_id:
            raise HTTPException(status_code=400, detail="必须指定项目ID或研发项目ID")

        if project_id:
            get_or_404(self.db, Project, project_id, "项目不存在")

        if rd_project_id:
            from app.models.rd_project import RdProject

            rd_project = (
                self.db.query(RdProject).filter(RdProject.id == rd_project_id).first()
            )
            if not rd_project:
                raise HTTPException(status_code=404, detail="研发项目不存在")

    def _check_duplicate_timesheet(
        self,
        user_id: int,
        work_date: date,
        project_id: Optional[int],
        rd_project_id: Optional[int],
    ) -> None:
        """检查是否存在重复工时记录"""
        query_filter = [
            Timesheet.user_id == user_id,
            Timesheet.work_date == work_date,
            Timesheet.status != "REJECTED",
        ]
        if project_id:
            query_filter.append(Timesheet.project_id == project_id)
        if rd_project_id:
            query_filter.append(Timesheet.rd_project_id == rd_project_id)

        existing = self.db.query(Timesheet).filter(*query_filter).first()

        if existing:
            raise HTTPException(
                status_code=400, detail="该日期已有工时记录，请更新或删除后重试"
            )

    def _get_user_info(self, user_id: int) -> Dict[str, Any]:
        """获取用户和部门信息"""
        user = self.db.query(User).filter(User.id == user_id).first()
        department_id = None
        department_name = None

        if user and hasattr(user, "department_id") and user.department_id:
            department = (
                self.db.query(Department)
                .filter(Department.id == user.department_id)
                .first()
            )
            if department:
                department_id = department.id
                department_name = department.name

        return {
            "user_name": user.real_name or user.username if user else None,
            "department_id": department_id,
            "department_name": department_name,
        }

    def _get_project_info(self, project_id: Optional[int]) -> Dict[str, Any]:
        """获取项目信息"""
        project_code = None
        project_name = None

        if project_id:
            project = (
                self.db.query(Project).filter(Project.id == project_id).first()
            )
            if project:
                project_code = project.project_code
                project_name = project.project_name

        return {"project_code": project_code, "project_name": project_name}

    def _check_access_permission(self, timesheet: Timesheet, current_user: User) -> None:
        """检查访问权限"""
        if timesheet.user_id != current_user.id:
            if not hasattr(current_user, "is_superuser") or not current_user.is_superuser:
                raise HTTPException(status_code=403, detail="无权访问此记录")

    def _build_timesheet_response(self, ts: Timesheet) -> TimesheetResponse:
        """构建工时记录响应对象（列表用）"""
        user = self.db.query(User).filter(User.id == ts.user_id).first()
        project = None
        if ts.project_id:
            project = self.db.query(Project).filter(Project.id == ts.project_id).first()

        task_name = None
        if ts.task_id:
            from app.models.progress import Task

            task = self.db.query(Task).filter(Task.id == ts.task_id).first()
            task_name = task.task_name if task else None

        return TimesheetResponse(
            id=ts.id,
            user_id=ts.user_id,
            user_name=user.real_name or user.username if user else None,
            project_id=ts.project_id,
            rd_project_id=ts.rd_project_id,
            project_name=project.project_name if project else None,
            task_id=ts.task_id,
            task_name=task_name,
            work_date=ts.work_date,
            work_hours=ts.hours or Decimal("0"),
            work_type=ts.overtime_type or "NORMAL",
            description=ts.work_content,
            status=ts.status or "DRAFT",
            approved_by=ts.approver_id,
            approved_at=ts.approve_time,
            created_at=ts.created_at,
            updated_at=ts.updated_at,
        )

    def _build_timesheet_detail_response(self, timesheet: Timesheet) -> TimesheetResponse:
        """构建工时记录详情响应对象"""
        user = self.db.query(User).filter(User.id == timesheet.user_id).first()
        project = None
        if timesheet.project_id:
            project = (
                self.db.query(Project).filter(Project.id == timesheet.project_id).first()
            )

        rd_project = None
        if timesheet.rd_project_id:
            from app.models.rd_project import RdProject

            rd_project = (
                self.db.query(RdProject)
                .filter(RdProject.id == timesheet.rd_project_id)
                .first()
            )

        return TimesheetResponse(
            id=timesheet.id,
            user_id=timesheet.user_id,
            user_name=user.real_name or user.username if user else None,
            project_id=timesheet.project_id,
            rd_project_id=timesheet.rd_project_id,
            project_name=(
                project.project_name
                if project
                else (rd_project.project_name if rd_project else None)
            ),
            task_id=timesheet.task_id,
            task_name=None,
            work_date=timesheet.work_date,
            work_hours=timesheet.hours or Decimal("0"),
            work_type=timesheet.overtime_type or "NORMAL",
            description=timesheet.work_content,
            is_billable=True,
            status=timesheet.status or "DRAFT",
            approved_by=timesheet.approver_id,
            approved_at=timesheet.approve_time,
            created_at=timesheet.created_at,
            updated_at=timesheet.updated_at,
        )
