# -*- coding: utf-8 -*-
"""
项目审批管理 API 模块统一导出

模块结构：
 ├── submit.py  # 提交审批（统一审批系统）
 ├── action.py  # 执行审批操作（旧系统）
 ├── cancel.py  # 撤销审批（旧系统）
 ├── status.py  # 获取审批状态（旧系统）
 ├── history.py # 获取审批历史（旧系统）
 └── utils.py   # 工具函数（旧系统）

迁移到统一审批系统的新文件：
 ├── submit_new.py  # 提交审批
 ├── action_new.py  # 执行审批操作（统一系统）
 ├── cancel_new.py  # 撤回审批（统一系统）
 ├── status_new.py  # 获取审批状态（统一系统）
 └── history_new.py # 获取审批历史（统一系统）
"""

from fastapi import APIRouter

# 临时导入新端点（待替换旧端点）
# from . import submit_new, action_new, cancel_new, status_new, history_new

# 暂时保留旧端点导入
# from . import submit, action, cancel, status, history, utils

# 创建主路由
router = APIRouter()

# 项目审批的实体类型常量
ENTITY_TYPE_PROJECT = "PROJECT"

# 注：下一步计划：
# 1. 测试新端点功能
# 2. 更新 __init__.py 使用新端点
# 3. 删除旧端点文件
# 4. 更新 projects 路由注册

__all__ = ["router", "ENTITY_TYPE_PROJECT"]
