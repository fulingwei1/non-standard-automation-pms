# -*- coding: utf-8 -*-
"""
阶段实例服务 - 核心类
"""

from sqlalchemy.orm import Session


class StageInstanceCore:
    """阶段实例服务核心类"""

    def __init__(self, db: Session):
        self.db = db
