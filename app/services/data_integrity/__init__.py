# -*- coding: utf-8 -*-
"""
数据完整性保障服务统一导出

通过多重继承组合所有功能模块
"""

from sqlalchemy.orm import Session

from .auto_fix import AutoFixMixin
from .check import DataCheckMixin
from .core import DataIntegrityCore
from .export import ExportMixin
from .reminders import RemindersMixin
from .report import DataReportMixin


class DataIntegrityService(
    DataIntegrityCore,
    DataCheckMixin,
    DataReportMixin,
    RemindersMixin,
    AutoFixMixin,
    ExportMixin,
):
    """数据完整性保障服务（组合所有功能模块）"""

    def __init__(self, db: Session):
        DataIntegrityCore.__init__(self, db)


__all__ = ["DataIntegrityService"]
