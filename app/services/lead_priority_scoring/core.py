# -*- coding: utf-8 -*-
"""
销售线索优先级评分服务 - 核心类
"""

from sqlalchemy.orm import Session


class LeadPriorityScoringCore:
    """销售线索优先级评分服务核心类"""

    def __init__(self, db: Session):
        self.db = db
