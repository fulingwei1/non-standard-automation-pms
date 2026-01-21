# -*- coding: utf-8 -*-
"""
ECN BOM影响分析服务 - 基础类
"""
from sqlalchemy.orm import Session


class EcnBomAnalysisService:
    """ECN BOM影响分析服务"""

    def __init__(self, db: Session):
        self.db = db
