# -*- coding: utf-8 -*-
"""
工程师绩效评价模块 - 枚举值常量

包含各种枚举值常量定义
"""

"""
工程师绩效评价模块 Pydantic Schemas
包含：请求/响应模型、数据验证
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ==================== 枚举值常量 ====================

JOB_TYPES = ['mechanical', 'test', 'electrical']
JOB_LEVELS = ['junior', 'intermediate', 'senior', 'expert']
CONTRIBUTION_TYPES = ['document', 'template', 'module', 'training', 'patent', 'standard']
CONTRIBUTION_STATUSES = ['draft', 'pending', 'approved', 'rejected']
REVIEW_RESULTS = ['passed', 'rejected', 'conditional']
ISSUE_SEVERITIES = ['critical', 'major', 'normal', 'minor']
ISSUE_STATUSES = ['open', 'in_progress', 'resolved', 'closed']
BUG_FOUND_STAGES = ['internal_debug', 'site_debug', 'acceptance', 'production']
PLC_BRANDS = ['siemens', 'mitsubishi', 'omron', 'beckhoff', 'inovance', 'delta']


