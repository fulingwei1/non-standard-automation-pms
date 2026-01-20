# -*- coding: utf-8 -*-
"""
数据完整性保障服务 - 核心类
"""

import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DataIntegrityCore:
    """数据完整性保障服务核心类"""

    def __init__(self, db: Session):
        self.db = db
