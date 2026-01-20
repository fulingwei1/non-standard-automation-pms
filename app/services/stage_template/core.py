# -*- coding: utf-8 -*-
"""
阶段模板服务 - 核心类
"""

from sqlalchemy.orm import Session


class StageTemplateCore:
    """阶段模板服务核心类"""

    def __init__(self, db: Session):
        self.db = db
