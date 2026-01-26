# -*- coding: utf-8 -*-
"""
审批通知服务 - 基础类

提供审批通知服务的基础类定义
"""

import logging
from datetime import datetime, timedelta
from typing import Dict

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# 简单的内存缓存用于通知去重（生产环境建议用 Redis）
_notification_dedup_cache: Dict[str, datetime] = {}
_DEDUP_WINDOW_MINUTES = 30  # 去重窗口：30分钟内相同通知不重复发送


class ApprovalNotifyServiceBase:
    """审批通知服务基础类"""

    def __init__(self, db: Session):
        self.db = db
