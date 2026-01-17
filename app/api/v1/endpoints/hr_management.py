# -*- coding: utf-8 -*-
"""
人事管理API端点

已拆分为模块化结构，详见 hr_management/ 目录：
- transactions.py: 人事事务（入职/离职/转正/调岗/晋升/调薪）
- contracts.py: 合同管理
- reminders.py: 合同到期提醒
- dashboard.py: 人事仪表板统计
"""

from .hr_management import router

__all__ = ["router"]
