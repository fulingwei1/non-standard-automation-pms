# -*- coding: utf-8 -*-
"""
时薪配置服务
负责从配置中获取用户时薪

优先级说明：
1. 用户个人配置 - 最高优先级，每个人可以有不同的时薪
2. 角色配置 - 按角色统一配置（如高级工程师、初级工程师等）
3. 部门配置 - 按部门统一配置
4. 默认配置 - 系统默认时薪
"""

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.hourly_rate import HourlyRateConfig
from app.models.organization import Department
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HourlyRateResolution:
    """Resolved hourly-rate value plus trace metadata."""

    hourly_rate: Decimal
    source: str
    config_id: Optional[int] = None
    is_fallback: bool = False
    fallback_reason: Optional[str] = None


class HourlyRateService:
    """时薪配置服务"""

    # 默认时薪（当没有配置时使用）
    DEFAULT_HOURLY_RATE = Decimal("100")  # 默认100元/小时

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    @staticmethod
    def _valid_rate_window_filter(work_date: date):
        """配置在指定日期可用于计算；历史已停用版本仍可回看。"""
        return and_(
            (
                HourlyRateConfig.effective_date.is_(None)
                | (HourlyRateConfig.effective_date <= work_date)
            ),
            (
                HourlyRateConfig.expiry_date.is_(None)
                | (HourlyRateConfig.expiry_date >= work_date)
            ),
            or_(
                HourlyRateConfig.is_active.is_(True),
                and_(
                    HourlyRateConfig.is_active.is_(False),
                    HourlyRateConfig.expiry_date.isnot(None),
                    HourlyRateConfig.expiry_date >= work_date,
                ),
            ),
        )

    @staticmethod
    def _pick_latest_config(query):
        return (
            query.order_by(
                HourlyRateConfig.effective_date.desc().nullslast(),
                HourlyRateConfig.updated_at.desc().nullslast(),
                HourlyRateConfig.id.desc(),
            )
            .first()
        )

    @staticmethod
    def get_user_hourly_rate_detail(
        db: Session, user_id: int, work_date: Optional[date] = None
    ) -> HourlyRateResolution:
        """
        获取用户时薪与来源（按优先级：用户配置 > 角色配置 > 部门配置 > 默认配置）

        Args:
            db: 数据库会话
            user_id: 用户ID
            work_date: 工作日期（用于判断配置是否在有效期内，默认今天）

        Returns:
            时薪解析结果
        """
        if work_date is None:
            work_date = date.today()

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(
                "时薪配置用户未找到，使用系统兜底: user_id=%s work_date=%s rate=%s",
                user_id,
                work_date,
                HourlyRateService.DEFAULT_HOURLY_RATE,
            )
            return HourlyRateResolution(
                hourly_rate=HourlyRateService.DEFAULT_HOURLY_RATE,
                source="系统兜底",
                is_fallback=True,
                fallback_reason="USER_NOT_FOUND",
            )

        # 1. 优先查找用户配置
        user_config = HourlyRateService._pick_latest_config(
            db.query(HourlyRateConfig)
            .filter(
                HourlyRateConfig.config_type == "USER",
                HourlyRateConfig.user_id == user_id,
                HourlyRateService._valid_rate_window_filter(work_date),
            )
        )

        if user_config:
            return HourlyRateResolution(
                hourly_rate=user_config.hourly_rate,
                source="用户配置",
                config_id=user_config.id,
            )

        # 2. 查找角色配置（用户可能有多个角色，取第一个有效的）
        user_roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
        for user_role in user_roles:
            role_config = HourlyRateService._pick_latest_config(
                db.query(HourlyRateConfig)
                .filter(
                    HourlyRateConfig.config_type == "ROLE",
                    HourlyRateConfig.role_id == user_role.role_id,
                    HourlyRateService._valid_rate_window_filter(work_date),
                )
            )

            if role_config:
                return HourlyRateResolution(
                    hourly_rate=role_config.hourly_rate,
                    source="角色配置",
                    config_id=role_config.id,
                )

        # 3. 查找部门配置
        # 通过User.department字符串字段或Employee的部门信息查找对应的Department
        dept_config = None

        # 3.1 尝试通过User.department字段匹配
        if user.department:
            dept = (
                db.query(Department)
                .filter(Department.dept_name == user.department, Department.is_active)
                .first()
            )
            if dept:
                dept_config = HourlyRateService._pick_latest_config(
                    db.query(HourlyRateConfig)
                    .filter(
                        HourlyRateConfig.config_type == "DEPT",
                        HourlyRateConfig.dept_id == dept.id,
                        HourlyRateService._valid_rate_window_filter(work_date),
                    )
                )

        if dept_config:
            return HourlyRateResolution(
                hourly_rate=dept_config.hourly_rate,
                source="部门配置",
                config_id=dept_config.id,
            )

        # 4. 查找默认配置
        default_config = HourlyRateService._pick_latest_config(
            db.query(HourlyRateConfig)
            .filter(
                HourlyRateConfig.config_type == "DEFAULT",
                HourlyRateService._valid_rate_window_filter(work_date),
            )
        )

        if default_config:
            return HourlyRateResolution(
                hourly_rate=default_config.hourly_rate,
                source="默认配置",
                config_id=default_config.id,
            )

        # 5. 使用默认值
        logger.warning(
            "时薪配置全级未命中，使用系统兜底: user_id=%s work_date=%s rate=%s",
            user_id,
            work_date,
            HourlyRateService.DEFAULT_HOURLY_RATE,
        )
        return HourlyRateResolution(
            hourly_rate=HourlyRateService.DEFAULT_HOURLY_RATE,
            source="系统兜底",
            is_fallback=True,
            fallback_reason="NO_ACTIVE_CONFIG",
        )

    @staticmethod
    def get_user_hourly_rate(
        db: Session, user_id: int, work_date: Optional[date] = None
    ) -> Decimal:
        """
        获取用户时薪（按优先级：用户配置 > 角色配置 > 部门配置 > 默认配置）

        Args:
            db: 数据库会话
            user_id: 用户ID
            work_date: 工作日期（用于判断配置是否在有效期内，默认今天）

        Returns:
            时薪（元/小时）
        """
        return HourlyRateService.get_user_hourly_rate_detail(
            db, user_id, work_date
        ).hourly_rate

    @staticmethod
    def get_users_hourly_rates(
        db: Session, user_ids: List[int], work_date: Optional[date] = None
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
            result[user_id] = HourlyRateService.get_user_hourly_rate(db, user_id, work_date)
        return result

    @staticmethod
    def get_hourly_rate_history(
        db: Session,
        user_id: Optional[int] = None,
        role_id: Optional[int] = None,
        dept_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
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
                (HourlyRateConfig.effective_date.is_(None))
                | (HourlyRateConfig.effective_date >= start_date)
            )
        if end_date:
            query = query.filter(
                (HourlyRateConfig.expiry_date.is_(None))
                | (HourlyRateConfig.expiry_date <= end_date)
            )

        configs = query.order_by(
            HourlyRateConfig.effective_date.desc().nullslast(), HourlyRateConfig.created_at.desc()
        ).all()

        result = []
        for config in configs:
            result.append(
                {
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
                    "updated_at": config.updated_at,
                }
            )

        return result
