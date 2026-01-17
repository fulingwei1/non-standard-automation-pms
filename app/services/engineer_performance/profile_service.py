# -*- coding: utf-8 -*-
"""
工程师档案管理服务
负责工程师档案的CRUD操作
"""

from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.engineer_performance import EngineerProfile
from app.models.organization import Employee
from app.models.user import User
from app.schemas.engineer_performance import (
    EngineerProfileCreate,
    EngineerProfileUpdate,
)


class ProfileService:
    """工程师档案管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_profile(self, user_id: int) -> Optional[EngineerProfile]:
        """获取工程师档案"""
        return self.db.query(EngineerProfile).filter(
            EngineerProfile.user_id == user_id
        ).first()

    def get_profile_by_id(self, profile_id: int) -> Optional[EngineerProfile]:
        """通过ID获取工程师档案"""
        return self.db.query(EngineerProfile).filter(
            EngineerProfile.id == profile_id
        ).first()

    def create_profile(self, data: EngineerProfileCreate) -> EngineerProfile:
        """创建工程师档案"""
        profile = EngineerProfile(
            user_id=data.user_id,
            job_type=data.job_type,
            job_level=data.job_level or 'junior',
            skills=data.skills,
            certifications=data.certifications,
            job_start_date=data.job_start_date,
            level_start_date=data.level_start_date
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def update_profile(
        self, user_id: int, data: EngineerProfileUpdate
    ) -> Optional[EngineerProfile]:
        """更新工程师档案"""
        profile = self.get_profile(user_id)
        if not profile:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)

        profile.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def list_profiles(
        self,
        job_type: Optional[str] = None,
        job_level: Optional[str] = None,
        department_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[EngineerProfile], int]:
        """获取工程师列表"""
        query = self.db.query(EngineerProfile).join(
            User, EngineerProfile.user_id == User.id
        )

        if job_type:
            query = query.filter(EngineerProfile.job_type == job_type)
        if job_level:
            query = query.filter(EngineerProfile.job_level == job_level)
        if department_id:
            query = query.filter(User.department_id == department_id)

        total = query.count()
        items = query.offset(offset).limit(limit).all()
        return items, total

    def get_profiles_by_job_type(self, job_type: str) -> List[EngineerProfile]:
        """按岗位类型获取工程师"""
        return self.db.query(EngineerProfile).filter(
            EngineerProfile.job_type == job_type
        ).all()

    def count_profiles_by_config(
        self, job_type: str, job_level: Optional[str] = None,
        department_id: Optional[int] = None
    ) -> int:
        """
        统计受配置影响的工程师人数

        Args:
            job_type: 岗位类型
            job_level: 职级（可选）
            department_id: 部门ID（如果指定则只统计该部门的工程师）
        """
        query = self.db.query(EngineerProfile).filter(
            EngineerProfile.job_type == job_type
        )
        if job_level:
            query = query.filter(EngineerProfile.job_level == job_level)

        if department_id:
            # 获取部门内的员工
            employees = self.db.query(Employee).filter(
                Employee.department_id == department_id,
                Employee.is_active == True
            ).all()

            employee_ids = [e.id for e in employees]
            user_ids = [
                u.id for u in self.db.query(User).filter(
                    User.employee_id.in_(employee_ids)
                ).all()
            ]

            query = query.filter(EngineerProfile.user_id.in_(user_ids))

        return query.count()
