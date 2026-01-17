# -*- coding: utf-8 -*-
"""
时薪配置服务
负责从配置中获取用户时薪（按优先级：用户 > 角色 > 部门 > 默认）
"""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.hourly_rate import HourlyRateConfig
from app.models.organization import Department
from app.models.user import User, UserRole


class HourlyRateService:
    """时薪配置服务"""

    # 默认时薪（当没有配置时使用）
    DEFAULT_HOURLY_RATE = Decimal("100")  # 默认100元/小时

    @staticmethod
    def get_user_hourly_rate(db: Session, user_id: int, work_date: Optional[date] = None) -> Decimal:
        """
        获取用户时薪（按优先级：用户配置 > 角色配置 > 部门配置 > 默认配置）

        Args:
            db: 数据库会话
            user_id: 用户ID
            work_date: 工作日期（用于判断配置是否在有效期内，默认今天）

        Returns:
            时薪（元/小时）
        """
        if work_date is None:
            work_date = date.today()

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return HourlyRateService.DEFAULT_HOURLY_RATE

        # 1. 优先查找用户配置
        user_config = db.query(HourlyRateConfig).filter(
            HourlyRateConfig.config_type == "USER",
            HourlyRateConfig.user_id == user_id,
            HourlyRateConfig.is_active == True,
            (HourlyRateConfig.effective_date.is_(None) | (HourlyRateConfig.effective_date <= work_date)),
            (HourlyRateConfig.expiry_date.is_(None) | (HourlyRateConfig.expiry_date >= work_date))
        ).order_by(HourlyRateConfig.effective_date.desc().nullslast()).first()

        if user_config:
            return user_config.hourly_rate

        # 2. 查找角色配置（用户可能有多个角色，取第一个有效的）
        user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
        for user_role in user_roles:
            role_config = db.query(HourlyRateConfig).filter(
                HourlyRateConfig.config_type == "ROLE",
                HourlyRateConfig.role_id == user_role.role_id,
                HourlyRateConfig.is_active == True,
                (HourlyRateConfig.effective_date.is_(None) | (HourlyRateConfig.effective_date <= work_date)),
                (HourlyRateConfig.expiry_date.is_(None) | (HourlyRateConfig.expiry_date >= work_date))
            ).order_by(HourlyRateConfig.effective_date.desc().nullslast()).first()

            if role_config:
                return role_config.hourly_rate

        # 3. 查找部门配置（通过Employee表获取部门信息）
        # 注意：由于User和Employee的关系，以及部门信息可能存储在多个地方，
        # 这里简化处理：如果有部门配置需求，可以通过Timesheet记录中的department_id获取
        # 或者通过Employee的hr_profile获取部门信息
        # 暂时跳过部门配置查找，直接使用默认配置
        # TODO: 如果需要部门级别的时薪配置，需要建立User/Employee到Department的关联

        # 4. 查找默认配置
        default_config = db.query(HourlyRateConfig).filter(
            HourlyRateConfig.config_type == "DEFAULT",
            HourlyRateConfig.is_active == True,
            (HourlyRateConfig.effective_date.is_(None) | (HourlyRateConfig.effective_date <= work_date)),
            (HourlyRateConfig.expiry_date.is_(None) | (HourlyRateConfig.expiry_date >= work_date))
        ).order_by(HourlyRateConfig.effective_date.desc().nullslast()).first()

        if default_config:
            return default_config.hourly_rate

        # 5. 使用默认值
        return HourlyRateService.DEFAULT_HOURLY_RATE

    @staticmethod
    def get_users_hourly_rates(
        db: Session,
        user_ids: List[int],
        work_date: Optional[date] = None
    ) -> Dict[int, Decimal]:
        """
        批量获取多个用户的时薪

        Args:
            db: 数据库会话
            user_ids: 用户ID列表
            work_date: 工作日期（用于判断配置是否在有效期内，默认今天）

        Returns:
            用户ID到时薪的映射字典
        """
        result = {}
        for user_id in user_ids:
            result[user_id] = HourlyRateService.get_user_hourly_rate(
                db, user_id, work_date
            )
        return result

    @staticmethod
    def get_hourly_rate_history(
        db: Session,
        user_id: Optional[int] = None,
        role_id: Optional[int] = None,
        dept_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict]:
        """
        获取时薪配置历史记录

        Args:
            db: 数据库会话
            user_id: 用户ID（可选）
            role_id: 角色ID（可选）
            dept_id: 部门ID（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            时薪配置历史记录列表
        """
        query = db.query(HourlyRateConfig)

        if user_id:
            query = query.filter(HourlyRateConfig.user_id == user_id)
        if role_id:
            query = query.filter(HourlyRateConfig.role_id == role_id)
        if dept_id:
            query = query.filter(HourlyRateConfig.dept_id == dept_id)
        if start_date:
            query = query.filter(
                (HourlyRateConfig.effective_date.is_(None)) |
                (HourlyRateConfig.effective_date >= start_date)
            )
        if end_date:
            query = query.filter(
                (HourlyRateConfig.expiry_date.is_(None)) |
                (HourlyRateConfig.expiry_date <= end_date)
            )

        configs = query.order_by(
            HourlyRateConfig.effective_date.desc().nullslast(),
            HourlyRateConfig.created_at.desc()
        ).all()

        result = []
        for config in configs:
            result.append({
                "id": config.id,
                "config_type": config.config_type,
                "user_id": config.user_id,
                "role_id": config.role_id,
                "dept_id": config.dept_id,
                "hourly_rate": config.hourly_rate,
                "effective_date": config.effective_date,
                "expiry_date": config.expiry_date,
                "is_active": config.is_active,
                "remark": config.remark,
                "created_at": config.created_at,
                "updated_at": config.updated_at
            })

        return result

