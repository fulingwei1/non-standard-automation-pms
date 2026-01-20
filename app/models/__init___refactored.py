# -*- coding: utf-8 -*-
"""
数据模型包（重构版本）

原 __init__.py 文件 772 行已重构为模块化结构：
- exports/core.py - 核心基础模型（用户、权限、项目）
- exports/business.py - 业务模型（销售、售前、报价等）
- exports/workflow.py - 工作流模型（任务、通知、工时等）
- exports/production.py - 生产制造模型（生产、物料、短缺等）
- exports/analytics.py - 分析服务模型（绩效、报表、服务、SLA等）

使用方式：
  from app.models import User, Project  # 仍然支持直接导入（向后兼容）
  from app.models.exports.core import User, Project  # 也可以从分组导入（推荐）
"""

# 从分组模块导入所有模型（保持向后兼容）
from .exports.core import *
from .exports.business import *
from .exports.workflow import *
from .exports.production import *
from .exports.analytics import *

# 重新导出所有模型
from .exports.core import __all__ as core_all
from .exports.business import __all__ as business_all
from .exports.workflow import __all__ as workflow_all
from .exports.production import __all__ as production_all
from .exports.analytics import __all__ as analytics_all

__all__ = core_all + business_all + workflow_all + production_all + analytics_all
