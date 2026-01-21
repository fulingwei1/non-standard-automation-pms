# -*- coding: utf-8 -*-
"""
非标自动化测试设备项目全流程模板（22阶段）

TPL_FULL_LIFECYCLE - 完整生命周期模板
从市场开拓到质保服务的全流程管理

来源: 非标自动化测试设备项目全流程阶段节点.xlsx

注意：此文件已拆分为多个模块文件以提高可维护性：
- sales_stages.py: 销售阶段 (S01-S03)
- presales_stages.py: 售前阶段 (S04-S08)
- execution_stages.py: 项目执行阶段 (S09-S20)
- closure_stages.py: 项目收尾阶段 (S21-S22)
"""

from typing import Any, Dict

from .closure_stages import CLOSURE_STAGES
from .execution_stages import EXECUTION_STAGES
from .presales_stages import PRESALES_STAGES
from .sales_stages import SALES_STAGES

# 完整生命周期模板（22大阶段）
# 组装所有阶段：销售 -> 售前 -> 执行 -> 收尾
FULL_LIFECYCLE_TEMPLATE: Dict[str, Any] = {
    "template_code": "TPL_FULL_LIFECYCLE",
    "template_name": "完整生命周期模板",
    "description": "非标自动化测试设备项目全流程，从市场开拓、销售、售前、项目执行到售后服务的完整22阶段管理",
    "project_type": "NEW",
    "stages": (
        SALES_STAGES
        + PRESALES_STAGES
        + EXECUTION_STAGES
        + CLOSURE_STAGES
    ),
}
