# -*- coding: utf-8 -*-
"""
工时记录服务
提供工时记录的基本CRUD操作
"""

from datetime import date
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.timesheet import Timesheet
from app.models.user import User
from app.schemas.timesheet import (
    TimesheetCreate,
    TimesheetUpdate,
    TimesheetResponse
)


class TimesheetRecordsService:
    """工时记录服务"""

    def __init__(self, db: Session):
        self.db = db

    def list_timesheets(
        self,
        current_user: User,
        offset: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None,
    ) -> tuple[List[Timesheet], int]:
        """
        获取工时记录列表（带分页和筛选）
        
        Args:
            current_user: 当前用户
            offset: 偏移量
            limit: 限制数量
            user_id: 用户ID筛选
            project_id: 项目ID筛选
            start_date: 开始日期筛选
            end_date: 结束日期筛选
            status: 状态筛选
            
        Returns:
            (工时记录列表, 总数)
        """
        # 构建查询
        query = self.db.query(Timesheet)
        
        # 权限控制：普通用户只能查看自己的工时
        if not current_user.is_admin():
            query = query.filter(Timesheet.user_id == current_user.id)
        
        # 应用筛选条件
        if user_id:
            query = query.filter(Timesheet.user_id == user_id)
        if project_id:
            query = query.filter(Timesheet.project_id == project_id)
        if start_date:
            query = query.filter(Timesheet.date >= start_date)
        if end_date:
            query = query.filter(Timesheet.date <= end_date)
        if status:
            query = query.filter(Timesheet.status == status)
        
        # 获取总数
        total = query.count()
        
        # 应用分页
        timesheets = query.offset(offset).limit(limit).all()
        
        return timesheets, total

    def create_timesheet(
        self, 
        timesheet_in: TimesheetCreate, 
        current_user: User
    ) -> TimesheetResponse:
        """
        创建工时记录
        
        Args:
            timesheet_in: 工时创建数据
            current_user: 当前用户
            
        Returns:
            创建的工时记录
        """
        # 检查权限：只能为自己创建工时
        if timesheet_in.user_id != current_user.id and not current_user.is_admin():
            raise ValueError("无权为其他用户创建工时记录")
        
        # 创建工时记录
        timesheet = Timesheet(
            user_id=timesheet_in.user_id,
            project_id=timesheet_in.project_id,
            date=timesheet_in.date,
            hours=timesheet_in.hours,
            description=timesheet_in.description,
            status="draft"  # 新创建的工时默认为草稿状态
        )
        
        self.db.add(timesheet)
        self.db.commit()
        self.db.refresh(timesheet)
        
        return TimesheetResponse.from_orm(timesheet)

    def batch_create_timesheets(
        self, 
        timesheets_data: List[TimesheetCreate], 
        current_user: User
    ) -> Dict[str, Any]:
        """
        批量创建工时记录
        
        Args:
            timesheets_data: 工时创建数据列表
            current_user: 当前用户
            
        Returns:
            包含成功和失败统计的结果
        """
        success_count = 0
        failed_count = 0
        errors = []
        
        for timesheet_data in timesheets_data:
            try:
                # 检查权限：只能为自己创建工时
                if timesheet_data.user_id != current_user.id and not current_user.is_admin():
                    raise ValueError("无权为其他用户创建工时记录")
                
                timesheet = Timesheet(
                    user_id=timesheet_data.user_id,
                    project_id=timesheet_data.project_id,
                    date=timesheet_data.date,
                    hours=timesheet_data.hours,
                    description=timesheet_data.description,
                    status="draft"
                )
                
                self.db.add(timesheet)
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(str(e))
        
        self.db.commit()
        
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors
        }

    def get_timesheet_detail(
        self, 
        timesheet_id: int, 
        current_user: User
    ) -> TimesheetResponse:
        """
        获取工时记录详情
        
        Args:
            timesheet_id: 工时记录ID
            current_user: 当前用户
            
        Returns:
            工时记录详情
        """
        timesheet = self.db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
        
        if not timesheet:
            raise ValueError("工时记录不存在")
        
        # 权限检查：只能查看自己的工时或管理员可以查看所有
        if timesheet.user_id != current_user.id and not current_user.is_admin():
            raise ValueError("无权查看此工时记录")
        
        return TimesheetResponse.from_orm(timesheet)

    def update_timesheet(
        self, 
        timesheet_id: int, 
        timesheet_in: TimesheetUpdate, 
        current_user: User
    ) -> TimesheetResponse:
        """
        更新工时记录
        
        Args:
            timesheet_id: 工时记录ID
            timesheet_in: 工时更新数据
            current_user: 当前用户
            
        Returns:
            更新后的工时记录
        """
        timesheet = self.db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
        
        if not timesheet:
            raise ValueError("工时记录不存在")
        
        # 权限检查：只能更新自己的工时或管理员可以更新所有
        if timesheet.user_id != current_user.id and not current_user.is_admin():
            raise ValueError("无权更新此工时记录")
        
        # 检查状态：已提交或已批准的工时不能直接编辑
        if timesheet.status in ["submitted", "approved"]:
            raise ValueError("已提交或已批准的工时记录不能直接编辑")
        
        # 更新字段
        update_data = timesheet_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(timesheet, field, value)
        
        self.db.commit()
        self.db.refresh(timesheet)
        
        return TimesheetResponse.from_orm(timesheet)

    def delete_timesheet(
        self, 
        timesheet_id: int, 
        current_user: User
    ):
        """
        删除工时记录
        
        Args:
            timesheet_id: 工时记录ID
            current_user: 当前用户
        """
        timesheet = self.db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
        
        if not timesheet:
            raise ValueError("工时记录不存在")
        
        # 权限检查：只能删除自己的工时或管理员可以删除所有
        if timesheet.user_id != current_user.id and not current_user.is_admin():
            raise ValueError("无权删除此工时记录")
        
        # 检查状态：已提交或已批准的工时不能删除
        if timesheet.status in ["submitted", "approved"]:
            raise ValueError("已提交或已批准的工时记录不能删除")
        
        self.db.delete(timesheet)
        self.db.commit()