# -*- coding: utf-8 -*-
"""
发票自动服务 - 基础类
"""
from sqlalchemy.orm import Session


class InvoiceAutoService:
    """发票自动服务"""

    def __init__(self, db: Session):
        self.db = db
