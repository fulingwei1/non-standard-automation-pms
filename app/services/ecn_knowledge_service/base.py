# -*- coding: utf-8 -*-
"""
ECN知识库服务 - 基础类
"""
from sqlalchemy.orm import Session


class EcnKnowledgeService:
    """ECN知识库服务"""

    def __init__(self, db: Session):
        self.db = db
