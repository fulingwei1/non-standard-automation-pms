# -*- coding: utf-8 -*-
"""
工作日志服务层
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.work_log import WorkLog, WorkLogConfig, WorkLogMention, MentionTypeEnum
from app.models.project import Project, Machine, ProjectStatusLog
from app.models.user import User
from app.models.timesheet import Timesheet
from app.models.organization import Department
from app.schemas.work_log import WorkLogCreate, WorkLogUpdate, MentionOption, MentionOptionsResponse


class WorkLogService:
    """工作日志服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_work_log(
        self,
        user_id: int,
        work_log_in: WorkLogCreate
    ) -> WorkLog:
        """
        创建工作日志
        
        Args:
            user_id: 提交人ID
            work_log_in: 工作日志创建数据
            
        Returns:
            WorkLog: 创建的工作日志对象
        """
        # 验证内容长度
        if len(work_log_in.content) > 300:
            raise ValueError('工作内容不能超过300字')
        
        # 检查同一天是否已有记录（如果状态不是草稿，则不允许重复提交）
        existing = self.db.query(WorkLog).filter(
            WorkLog.user_id == user_id,
            WorkLog.work_date == work_log_in.work_date,
            WorkLog.status != 'DRAFT'
        ).first()
        
        if existing:
            raise ValueError(f'该日期已提交工作日志，请更新现有记录或选择其他日期')
        
        # 获取用户信息
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError('用户不存在')
        
        # 创建工作日志
        work_log = WorkLog(
            user_id=user_id,
            user_name=user.real_name or user.username,
            work_date=work_log_in.work_date,
            content=work_log_in.content,
            status=work_log_in.status or 'SUBMITTED'
        )
        
        self.db.add(work_log)
        self.db.flush()  # 获取work_log.id
        
        # 处理@提及
        self._create_mentions(work_log.id, work_log_in)
        
        # 自动关联到项目/设备进展
        self._link_to_progress(work_log, work_log_in, user_id)
        
        # 如果提供了工时信息，自动创建工时记录
        if work_log_in.work_hours is not None and work_log_in.work_hours > 0:
            timesheet = self._create_timesheet_from_worklog(work_log, work_log_in, user_id)
            work_log.timesheet_id = timesheet.id
        
        self.db.commit()
        self.db.refresh(work_log)
        
        return work_log
    
    def update_work_log(
        self,
        work_log_id: int,
        user_id: int,
        work_log_in: WorkLogUpdate
    ) -> WorkLog:
        """
        更新工作日志（仅限草稿状态）
        
        Args:
            work_log_id: 工作日志ID
            user_id: 操作人ID
            work_log_in: 工作日志更新数据
            
        Returns:
            WorkLog: 更新后的工作日志对象
        """
        work_log = self.db.query(WorkLog).filter(WorkLog.id == work_log_id).first()
        if not work_log:
            raise ValueError('工作日志不存在')
        
        # 验证权限：只能更新自己的日志
        if work_log.user_id != user_id:
            raise ValueError('只能更新自己的工作日志')
        
        # 只能更新草稿状态的日志
        if work_log.status != 'DRAFT':
            raise ValueError('只能更新草稿状态的工作日志')
        
        # 更新内容
        if work_log_in.content is not None:
            if len(work_log_in.content) > 300:
                raise ValueError('工作内容不能超过300字')
            work_log.content = work_log_in.content
        
        if work_log_in.status is not None:
            work_log.status = work_log_in.status
        
        # 更新@提及（如果提供了新的提及列表）
        if work_log_in.mentioned_projects is not None or \
           work_log_in.mentioned_machines is not None or \
           work_log_in.mentioned_users is not None:
            # 删除旧的提及
            self.db.query(WorkLogMention).filter(
                WorkLogMention.work_log_id == work_log_id
            ).delete()
            
            # 创建新的提及
            create_data = WorkLogCreate(
                work_date=work_log.work_date,
                content=work_log.content,
                mentioned_projects=work_log_in.mentioned_projects or [],
                mentioned_machines=work_log_in.mentioned_machines or [],
                mentioned_users=work_log_in.mentioned_users or [],
                status=work_log.status
            )
            self._create_mentions(work_log_id, create_data)
            
            # 重新关联到项目/设备进展（删除旧的，创建新的）
            # 注意：这里简化处理，实际可能需要更复杂的逻辑
            self._link_to_progress(work_log, create_data, user_id)
        
        # 更新工时记录（如果提供了工时信息）
        if work_log_in.work_hours is not None or \
           work_log_in.work_type is not None or \
           work_log_in.project_id is not None or \
           work_log_in.rd_project_id is not None:
            self._update_timesheet_from_worklog(work_log, work_log_in, user_id)
        
        self.db.commit()
        self.db.refresh(work_log)
        
        return work_log
    
    def _create_mentions(
        self,
        work_log_id: int,
        work_log_in: WorkLogCreate
    ):
        """创建@提及记录"""
        # 处理项目提及
        if work_log_in.mentioned_projects:
            for project_id in work_log_in.mentioned_projects:
                project = self.db.query(Project).filter(Project.id == project_id).first()
                if project:
                    mention = WorkLogMention(
                        work_log_id=work_log_id,
                        mention_type=MentionTypeEnum.PROJECT.value,
                        mention_id=project_id,
                        mention_name=project.project_name
                    )
                    self.db.add(mention)
        
        # 处理设备提及
        if work_log_in.mentioned_machines:
            for machine_id in work_log_in.mentioned_machines:
                machine = self.db.query(Machine).filter(Machine.id == machine_id).first()
                if machine:
                    mention = WorkLogMention(
                        work_log_id=work_log_id,
                        mention_type=MentionTypeEnum.MACHINE.value,
                        mention_id=machine_id,
                        mention_name=machine.machine_name
                    )
                    self.db.add(mention)
        
        # 处理人员提及
        if work_log_in.mentioned_users:
            for user_id in work_log_in.mentioned_users:
                user = self.db.query(User).filter(User.id == user_id).first()
                if user:
                    mention = WorkLogMention(
                        work_log_id=work_log_id,
                        mention_type=MentionTypeEnum.USER.value,
                        mention_id=user_id,
                        mention_name=user.real_name or user.username
                    )
                    self.db.add(mention)
    
    def _link_to_progress(
        self,
        work_log: WorkLog,
        work_log_in: WorkLogCreate,
        user_id: int
    ):
        """
        自动关联到项目/设备进展
        当@了项目或设备时，创建ProjectStatusLog记录
        """
        # 处理项目提及
        if work_log_in.mentioned_projects:
            for project_id in work_log_in.mentioned_projects:
                project = self.db.query(Project).filter(Project.id == project_id).first()
                if project:
                    status_log = ProjectStatusLog(
                        project_id=project_id,
                        machine_id=None,
                        change_type='WORK_LOG',
                        change_note=work_log_in.content,
                        changed_by=user_id,
                        changed_at=datetime.now()
                    )
                    self.db.add(status_log)
        
        # 处理设备提及
        if work_log_in.mentioned_machines:
            for machine_id in work_log_in.mentioned_machines:
                machine = self.db.query(Machine).filter(Machine.id == machine_id).first()
                if machine:
                    status_log = ProjectStatusLog(
                        project_id=machine.project_id,
                        machine_id=machine_id,
                        change_type='WORK_LOG',
                        change_note=work_log_in.content,
                        changed_by=user_id,
                        changed_at=datetime.now()
                    )
                    self.db.add(status_log)
    
    def _create_timesheet_from_worklog(
        self,
        work_log: WorkLog,
        work_log_in: WorkLogCreate,
        user_id: int
    ) -> Timesheet:
        """
        从工作日志创建工时记录
        
        Args:
            work_log: 工作日志对象
            work_log_in: 工作日志创建数据
            user_id: 用户ID
            
        Returns:
            Timesheet: 创建的工时记录
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError('用户不存在')
        
        # 获取部门信息
        department_id = None
        department_name = None
        if hasattr(user, 'department_id') and user.department_id:
            department = self.db.query(Department).filter(Department.id == user.department_id).first()
            if department:
                department_id = department.id
                department_name = department.name
        
        # 获取项目信息
        project_id = work_log_in.project_id
        project_code = None
        project_name = None
        if project_id:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if project:
                project_code = project.project_code
                project_name = project.project_name
        
        # 确定项目ID（优先使用project_id，如果没有则从mentioned_projects中取第一个）
        if not project_id and work_log_in.mentioned_projects:
            project_id = work_log_in.mentioned_projects[0]
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if project:
                project_code = project.project_code
                project_name = project.project_name
        
        # 创建工时记录
        timesheet = Timesheet(
            user_id=user_id,
            user_name=user.real_name or user.username,
            department_id=department_id,
            department_name=department_name,
            project_id=project_id,
            project_code=project_code,
            project_name=project_name,
            rd_project_id=work_log_in.rd_project_id,
            task_id=work_log_in.task_id,
            work_date=work_log_in.work_date,
            hours=work_log_in.work_hours,
            overtime_type=work_log_in.work_type or 'NORMAL',
            work_content=work_log_in.content,
            status='DRAFT',  # 初始状态为草稿，需要单独提交审批
            created_by=user_id
        )
        
        self.db.add(timesheet)
        self.db.flush()  # 获取timesheet.id
        
        return timesheet
    
    def _update_timesheet_from_worklog(
        self,
        work_log: WorkLog,
        work_log_in: WorkLogUpdate,
        user_id: int
    ):
        """
        从工作日志更新工时记录
        
        Args:
            work_log: 工作日志对象
            work_log_in: 工作日志更新数据
            user_id: 用户ID
        """
        # 如果已有工时记录，更新它
        if work_log.timesheet_id:
            timesheet = self.db.query(Timesheet).filter(Timesheet.id == work_log.timesheet_id).first()
            if timesheet:
                # 只能更新草稿状态的工时记录
                if timesheet.status == 'DRAFT':
                    if work_log_in.work_hours is not None:
                        timesheet.hours = work_log_in.work_hours
                    if work_log_in.work_type is not None:
                        timesheet.overtime_type = work_log_in.work_type
                    if work_log_in.project_id is not None:
                        timesheet.project_id = work_log_in.project_id
                        if work_log_in.project_id:
                            project = self.db.query(Project).filter(Project.id == work_log_in.project_id).first()
                            if project:
                                timesheet.project_code = project.project_code
                                timesheet.project_name = project.project_name
                    if work_log_in.rd_project_id is not None:
                        timesheet.rd_project_id = work_log_in.rd_project_id
                    if work_log_in.task_id is not None:
                        timesheet.task_id = work_log_in.task_id
                    if work_log_in.content is not None:
                        timesheet.work_content = work_log_in.content
        else:
            # 如果没有工时记录，但提供了工时信息，创建新的
            if work_log_in.work_hours is not None and work_log_in.work_hours > 0:
                create_data = WorkLogCreate(
                    work_date=work_log.work_date,
                    content=work_log_in.content or work_log.content,
                    mentioned_projects=[],
                    mentioned_machines=[],
                    mentioned_users=[],
                    status=work_log.status,
                    work_hours=work_log_in.work_hours,
                    work_type=work_log_in.work_type or 'NORMAL',
                    project_id=work_log_in.project_id,
                    rd_project_id=work_log_in.rd_project_id,
                    task_id=work_log_in.task_id
                )
                timesheet = self._create_timesheet_from_worklog(work_log, create_data, user_id)
                work_log.timesheet_id = timesheet.id
    
    def get_mention_options(
        self,
        user_id: int
    ) -> MentionOptionsResponse:
        """
        获取可@的选项列表
        
        Args:
            user_id: 当前用户ID
            
        Returns:
            MentionOptionsResponse: 提及选项响应
        """
        projects = []
        machines = []
        users = []
        
        # 获取用户有权限的项目列表（简化处理：获取所有项目，实际应该根据权限过滤）
        project_list = self.db.query(Project).filter(
            Project.is_active == True
        ).all()
        for project in project_list:
            projects.append(MentionOption(
                id=project.id,
                name=project.project_name,
                type='PROJECT'
            ))
        
        # 获取用户有权限的设备列表（简化处理：获取所有设备，实际应该根据权限过滤）
        machine_list = self.db.query(Machine).join(Project).filter(
            Project.is_active == True
        ).all()
        for machine in machine_list:
            machines.append(MentionOption(
                id=machine.id,
                name=machine.machine_name,
                type='MACHINE'
            ))
        
        # 获取用户列表（简化处理：获取所有活跃用户，实际应该根据权限范围过滤）
        user_list = self.db.query(User).filter(
            User.is_active == True
        ).all()
        for user in user_list:
            users.append(MentionOption(
                id=user.id,
                name=user.real_name or user.username,
                type='USER'
            ))
        
        return MentionOptionsResponse(
            projects=projects,
            machines=machines,
            users=users
        )
