# -*- coding: utf-8 -*-
"""
资源浪费分析服务 - 核心类
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session


class ResourceWasteAnalysisCore:
    """资源浪费分析服务核心类"""

    # 默认工时成本（元/小时）
    DEFAULT_HOURLY_RATE = Decimal('300')

    # 角色工时成本
    ROLE_HOURLY_RATES = {
        'engineer': Decimal('300'),      # 工程师
        'senior_engineer': Decimal('400'),  # 高级工程师
        'presales': Decimal('350'),       # 售前
        'designer': Decimal('320'),       # 设计师
        'project_manager': Decimal('450'),  # 项目经理
    }

    def __init__(self, db: Session, hourly_rate: Optional[Decimal] = None):
        self.db = db
        self.hourly_rate = hourly_rate or self.DEFAULT_HOURLY_RATE
