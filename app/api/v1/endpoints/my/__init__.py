# -*- coding: utf-8 -*-
"""
个人维度 API 模块

提供当前用户视角的数据访问：
- /my/projects - 我参与的项目
- /my/timesheet - 我的工时记录
- /my/workload - 我的工作量
- /my/tasks - 我的任务
- /my/work-logs - 我的工作日志
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/projects")
async def get_my_projects():
    """我参与的项目列表 - 待实现"""
    return {"message": "Coming soon"}


@router.get("/workload")
async def get_my_workload():
    """我的工作量 - 待实现"""
    return {"message": "Coming soon"}
