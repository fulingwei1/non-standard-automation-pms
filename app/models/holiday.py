# -*- coding: utf-8 -*-
"""
节假日配置模型
用于存储法定节假日、调休日等，支持工时类型判断
"""

from sqlalchemy import Column, Integer, String, Date, Boolean, Text, Index
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Holiday(Base, TimestampMixin):
    """
    节假日配置表

    用于配置：
    - 法定节假日（如春节、国庆等）
    - 调休工作日（原本是周末但需要上班的日子）
    - 公司特殊假期（如年会等）
    """
    __tablename__ = 'holidays'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 日期信息
    holiday_date = Column(Date, nullable=False, unique=True, comment='日期')
    year = Column(Integer, nullable=False, comment='年份')

    # 类型
    holiday_type = Column(String(20), nullable=False, comment='类型')
    # HOLIDAY: 法定节假日（放假）
    # WORKDAY: 调休工作日（周末上班）
    # COMPANY: 公司假期

    # 名称和说明
    name = Column(String(100), nullable=False, comment='节假日名称')
    description = Column(Text, comment='说明')

    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')

    __table_args__ = (
        Index('idx_holiday_date', 'holiday_date'),
        Index('idx_holiday_year', 'year'),
        Index('idx_holiday_type', 'holiday_type'),
        {'comment': '节假日配置表'}
    )

    def __repr__(self):
        return f'<Holiday {self.holiday_date} {self.name}>'


class HolidayService:
    """节假日服务 - 提供节假日判断功能"""

    @staticmethod
    def is_holiday(db, check_date) -> bool:
        """
        检查指定日期是否为节假日

        Args:
            db: 数据库会话
            check_date: 要检查的日期

        Returns:
            bool: 是否为节假日
        """
        holiday = db.query(Holiday).filter(
            Holiday.holiday_date == check_date,
            Holiday.holiday_type == 'HOLIDAY',
            Holiday.is_active == True
        ).first()
        return holiday is not None

    @staticmethod
    def is_workday(db, check_date) -> bool:
        """
        检查指定日期是否为调休工作日（周末但需要上班）

        Args:
            db: 数据库会话
            check_date: 要检查的日期

        Returns:
            bool: 是否为调休工作日
        """
        workday = db.query(Holiday).filter(
            Holiday.holiday_date == check_date,
            Holiday.holiday_type == 'WORKDAY',
            Holiday.is_active == True
        ).first()
        return workday is not None

    @staticmethod
    def get_work_type(db, check_date) -> str:
        """
        获取指定日期的工作类型

        Args:
            db: 数据库会话
            check_date: 要检查的日期

        Returns:
            str: 工作类型 - NORMAL/WEEKEND/HOLIDAY
        """
        # 先检查是否是法定节假日
        if HolidayService.is_holiday(db, check_date):
            return "HOLIDAY"

        # 检查是否是调休工作日（周末变工作日）
        if HolidayService.is_workday(db, check_date):
            return "NORMAL"

        # 检查是否是周末
        if check_date.weekday() >= 5:
            return "WEEKEND"

        return "NORMAL"

    @staticmethod
    def get_holiday_name(db, check_date) -> str:
        """
        获取节假日名称

        Args:
            db: 数据库会话
            check_date: 要检查的日期

        Returns:
            str: 节假日名称，如果不是节假日返回None
        """
        holiday = db.query(Holiday).filter(
            Holiday.holiday_date == check_date,
            Holiday.is_active == True
        ).first()
        return holiday.name if holiday else None
