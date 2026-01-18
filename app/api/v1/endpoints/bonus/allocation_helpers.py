# -*- coding: utf-8 -*-
"""
奖金分配明细表 - 辅助函数

包含编号生成等工具函数
"""

import uuid
from datetime import datetime


def generate_sheet_code() -> str:
    """生成分配明细表编号"""
    today = datetime.now().strftime('%y%m%d')
    return f"BAS-{today}-{uuid.uuid4().hex[:6].upper()}"
