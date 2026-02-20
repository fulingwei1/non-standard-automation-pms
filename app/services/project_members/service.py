# -*- coding: utf-8 -*-
"""
项目成员服务层

提取项目成员管理的核心业务逻辑
"""

from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.organization import Department, Employee
from app.models.project import ProjectMember, Project
from app.models.user import User
from app.utils.db_helpers import delete_obj, get_or_404, save_obj
from app.common.query_filters import apply_keyword_filter, apply_pagination


class ProjectMembersService:
    """项目成员服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def enrich_member_response(self, member: ProjectMember) -> ProjectMember:
        """填充成员的username和real_name"""
        if member.user:
            member.username = member.user.username
            member.real_name = member.user.real_name
        else:
            member.username = "Unknown"
            member.real_name = "Unknown"
        return member
    
    def get_member_by_id(
        self, 
        project_id: int, 
        member_id: int,
        enrich: bool = True
    ) -> ProjectMember:
        """获取项目成员详情"""
        member = self.db.query(ProjectMember).filter(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id,
        ).first()
        
        if not member:
            raise HTTPException(status_code=404, detail="项目成员不存在")
        
        if enrich:
            return self.enrich_member_response(member)
        return member
    
    def list_members(
        self,
        project_id: int,
        offset: int = 0,
        limit: int = 20,
        keyword: Optional[str] = None,
        order_by: Optional[str] = None,
        order_direction: str = "desc",
        role: Optional[str] = None,
        enrich: bool = True
    ) -> Tuple[List[ProjectMember], int]:
        """获取项目成员列表（支持分页、搜索、排序、筛选）"""
        # 构建查询
        query = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        )
        
        # 角色筛选
        if role:
            query = query.filter(ProjectMember.role_code == role)
        
        # 关键词搜索
        query = apply_keyword_filter(query, ProjectMember, keyword, "remark")
        
        # 排序
        order_field = getattr(ProjectMember, order_by or "created_at", None)
        if order_field:
            if order_direction == "asc":
                query = query.order_by(order_field.asc())
            else:
                query = query.order_by(order_field.desc())
        
        # 获取总数
        total = query.count()
        
        # 分页
        members = apply_pagination(query, offset, limit).all()
        
        # 填充用户信息
        if enrich:
            for member in members:
                self.enrich_member_response(member)
        
        return members, total
    
    def check_member_exists(self, project_id: int, user_id: int) -> bool:
        """检查用户是否已是项目成员"""
        existing = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        ).first()
        return existing is not None
    
    def create_member(
        self,
        project_id: int,
        user_id: int,
        role_code: str,
        allocation_pct: float = 100,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        commitment_level: Optional[str] = None,
        reporting_to_pm: bool = True,
        remark: Optional[str] = None,
        created_by: Optional[int] = None,
        enrich: bool = True
    ) -> ProjectMember:
        """创建项目成员"""
        # 验证项目存在
        get_or_404(self.db, Project, project_id, detail="项目不存在")
        
        # 验证用户存在
        get_or_404(self.db, User, user_id, detail="用户不存在")
        
        # 检查是否已是项目成员
        if self.check_member_exists(project_id, user_id):
            raise HTTPException(status_code=400, detail="该用户已是项目成员")
        
        # 创建成员
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role_code=role_code,
            allocation_pct=allocation_pct,
            start_date=start_date,
            end_date=end_date,
            commitment_level=commitment_level,
            reporting_to_pm=reporting_to_pm,
            remark=remark,
            dept_manager_notified=False,
            created_by=created_by
        )
        
        save_obj(self.db, member)
        
        if enrich:
            return self.enrich_member_response(member)
        return member
    
    def update_member(
        self,
        project_id: int,
        member_id: int,
        update_data: Dict[str, Any],
        enrich: bool = True
    ) -> ProjectMember:
        """更新项目成员信息"""
        member = self.db.query(ProjectMember).filter(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id,
        ).first()
        
        if not member:
            raise HTTPException(status_code=404, detail="项目成员不存在")
        
        # 更新字段
        for field, value in update_data.items():
            if hasattr(member, field):
                setattr(member, field, value)
        
        save_obj(self.db, member)
        
        if enrich:
            return self.enrich_member_response(member)
        return member
    
    def delete_member(self, project_id: int, member_id: int) -> None:
        """删除项目成员"""
        member = self.db.query(ProjectMember).filter(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id,
        ).first()
        
        if not member:
            raise HTTPException(status_code=404, detail="项目成员不存在")
        
        delete_obj(self.db, member)
    
    def check_member_conflicts(
        self,
        user_id: int,
        start_date: Optional[date],
        end_date: Optional[date],
        exclude_project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """检查成员分配冲突"""
        if not start_date or not end_date:
            return {'has_conflict': False}
        
        query = self.db.query(ProjectMember).filter(
            ProjectMember.user_id == user_id,
            ProjectMember.is_active,
            or_(
                and_(
                    ProjectMember.start_date <= start_date,
                    ProjectMember.end_date >= start_date
                ),
                and_(
                    ProjectMember.start_date <= end_date,
                    ProjectMember.end_date >= end_date
                ),
                and_(
                    ProjectMember.start_date >= start_date,
                    ProjectMember.end_date <= end_date
                )
            )
        )
        
        if exclude_project_id:
            query = query.filter(ProjectMember.project_id != exclude_project_id)
        
        conflicting_members = query.all()
        
        if not conflicting_members:
            return {'has_conflict': False}
        
        conflicting_projects = []
        for member in conflicting_members:
            project = self.db.query(Project).filter(
                Project.id == member.project_id
            ).first()
            if project:
                conflicting_projects.append({
                    'project_id': project.id,
                    'project_code': project.project_code,
                    'project_name': project.project_name,
                    'allocation_pct': float(member.allocation_pct or 100),
                    'start_date': (
                        member.start_date.isoformat()
                        if member.start_date else None
                    ),
                    'end_date': (
                        member.end_date.isoformat()
                        if member.end_date else None
                    ),
                })
        
        user = self.db.query(User).filter(User.id == user_id).first()
        user_name = user.real_name or user.username if user else f'User {user_id}'
        
        return {
            'has_conflict': True,
            'user_id': user_id,
            'user_name': user_name,
            'conflicting_projects': conflicting_projects,
            'conflict_count': len(conflicting_projects)
        }
    
    def batch_add_members(
        self,
        project_id: int,
        user_ids: List[int],
        role_code: str,
        allocation_pct: float = 100,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        commitment_level: Optional[str] = None,
        reporting_to_pm: bool = True,
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """批量添加项目成员"""
        # 验证项目存在
        get_or_404(self.db, Project, project_id, detail="项目不存在")
        
        added_count = 0
        skipped_count = 0
        conflicts = []
        
        for user_id in user_ids:
            # 检查是否已是成员
            if self.check_member_exists(project_id, user_id):
                skipped_count += 1
                continue
            
            # 检查冲突
            conflict_info = self.check_member_conflicts(
                user_id, start_date, end_date, project_id
            )
            if conflict_info['has_conflict']:
                conflicts.append({
                    'user_id': user_id,
                    'user_name': conflict_info.get('user_name', f'User {user_id}'),
                    'conflicting_projects': conflict_info.get(
                        'conflicting_projects', []
                    )
                })
                continue
            
            # 创建成员
            member = ProjectMember(
                project_id=project_id,
                user_id=user_id,
                role_code=role_code,
                allocation_pct=allocation_pct,
                start_date=start_date,
                end_date=end_date,
                commitment_level=commitment_level,
                reporting_to_pm=reporting_to_pm,
                dept_manager_notified=False,
                created_by=created_by
            )
            
            self.db.add(member)
            added_count += 1
        
        self.db.commit()
        
        return {
            'added_count': added_count,
            'skipped_count': skipped_count,
            'conflicts': conflicts,
            'message': (
                f'成功添加 {added_count} 位成员，'
                f'跳过 {skipped_count} 位，'
                f'发现 {len(conflicts)} 个时间冲突'
            )
        }
    
    def notify_dept_manager(self, project_id: int, member_id: int) -> Dict[str, str]:
        """通知部门经理（成员加入项目）"""
        member = self.db.query(ProjectMember).filter(
            ProjectMember.id == member_id,
            ProjectMember.project_id == project_id
        ).first()
        
        if not member:
            raise HTTPException(status_code=404, detail="项目成员不存在")
        
        if member.dept_manager_notified:
            return {'message': "部门经理已通知"}
        
        member.dept_manager_notified = True
        self.db.commit()
        
        return {'message': "部门经理通知已发送"}
    
    def get_dept_users_for_project(
        self,
        project_id: int,
        dept_id: int
    ) -> Dict[str, Any]:
        """获取部门用户列表（用于批量添加成员）"""
        dept = get_or_404(self.db, Department, dept_id, detail="部门不存在")
        
        # 获取部门员工
        employees = self.db.query(Employee).filter(
            Employee.department == dept.dept_name,
            Employee.is_active
        ).all()
        
        employee_ids = [e.id for e in employees]
        
        # 获取关联的用户
        users = self.db.query(User).filter(
            User.employee_id.in_(employee_ids),
            User.is_active
        ).all()
        
        # 获取已存在的项目成员
        existing_member_ids = self.db.query(ProjectMember.user_id).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.is_active
        ).all()
        existing_user_ids = {m[0] for m in existing_member_ids}
        
        # 构建用户列表
        available_users = []
        for user in users:
            available_users.append({
                'user_id': user.id,
                'username': user.username,
                'real_name': user.real_name,
                'is_member': user.id in existing_user_ids
            })
        
        return {
            'dept_id': dept_id,
            'dept_name': dept.dept_name,
            'users': available_users
        }
