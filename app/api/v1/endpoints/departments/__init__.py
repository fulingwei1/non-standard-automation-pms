# -*- coding: utf-8 -*-
"""
部门维度 API 模块

提供部门管理者视角的数据访问：
- /departments/{dept_id}/workload - 部门工作量汇总
- /departments/{dept_id}/projects - 部门相关项目
- /departments/{dept_id}/timesheet - 部门工时统计
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/{dept_id}/workload")
async def get_department_workload(dept_id: int):
    """部门工作量汇总 - 待实现"""
    return {"message": "Coming soon", "dept_id": dept_id}


@router.get("/{dept_id}/projects")
async def get_department_projects(dept_id: int):
    """部门相关项目 - 待实现"""
    return {"message": "Coming soon", "dept_id": dept_id}
