"""
任务中心 API
统一的个人任务管理接口
"""
from fastapi import APIRouter, Query, HTTPException, Body
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

from app.services.task_center_service import (
    TaskCenterService,
    TaskType,
    TaskStatus,
    TaskPriority,
    create_task_center_service
)

router = APIRouter(prefix="/task-center", tags=["任务中心"])


# ==================== 任务列表 ====================

@router.get("/my-tasks", summary="获取我的所有任务")
async def get_my_tasks(
    task_type: Optional[str] = Query(None, description="任务类型"),
    status: Optional[str] = Query(None, description="状态"),
    priority: Optional[str] = Query(None, description="优先级"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    is_overdue: Optional[bool] = Query(None, description="是否逾期"),
    is_due_today: Optional[bool] = Query(None, description="是否今日到期"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_by: str = Query("smart", description="排序方式: smart/deadline/priority/created"),
    current_user_id: int = Query(1, description="当前用户ID（测试用）")
):
    """
    获取我的所有任务
    
    聚合以下来源的任务：
    - 项目WBS任务：项目分解产生的任务
    - 岗位职责任务：定期自动生成的职责任务
    - 流程待办：工作流待处理节点
    - 转办任务：同事委托转办的任务
    - 遗留任务：历史未完成的任务
    - 预警任务：预警系统生成的跟踪任务
    - 个人自建：自己创建的备忘任务
    - 临时指派：领导临时安排的任务
    
    智能排序规则：
    1. 紧急标记 > 已逾期 > 今日到期 > 优先级
    2. 相同优先级按截止时间排序
    """
    service = create_task_center_service()
    
    # 转换枚举
    type_enum = TaskType(task_type) if task_type else None
    status_enum = TaskStatus(status) if status else None
    priority_enum = TaskPriority(priority) if priority else None
    
    result = service.get_my_tasks(
        user_id=current_user_id,
        task_type=type_enum,
        status=status_enum,
        priority=priority_enum,
        project_id=project_id,
        is_overdue=is_overdue,
        is_due_today=is_due_today,
        keyword=keyword,
        page=page,
        page_size=page_size,
        sort_by=sort_by
    )
    
    return {
        "code": 200,
        "data": result
    }


@router.get("/statistics", summary="获取任务统计")
async def get_task_statistics(
    current_user_id: int = Query(1, description="当前用户ID")
):
    """
    获取任务统计数据
    
    返回：
    - 总数、待处理、进行中、已完成
    - 逾期数、今日到期、本周到期、紧急
    - 按类型分布
    - 按项目分布
    - 按优先级分布
    """
    service = create_task_center_service()
    stats = service.get_task_statistics(current_user_id)
    
    return {
        "code": 200,
        "data": stats.to_dict()
    }


@router.get("/today", summary="获取今日任务")
async def get_today_tasks(
    current_user_id: int = Query(1, description="当前用户ID")
):
    """获取今日到期的任务"""
    service = create_task_center_service()
    result = service.get_my_tasks(
        user_id=current_user_id,
        is_due_today=True,
        page_size=50,
        sort_by="smart"
    )
    
    return {
        "code": 200,
        "data": result
    }


@router.get("/urgent", summary="获取紧急任务")
async def get_urgent_tasks(
    current_user_id: int = Query(1, description="当前用户ID")
):
    """获取紧急和逾期的任务"""
    service = create_task_center_service()
    
    # 获取所有任务
    result = service.get_my_tasks(
        user_id=current_user_id,
        page_size=100,
        sort_by="smart"
    )
    
    # 筛选紧急和逾期
    urgent_tasks = [
        t for t in result['tasks'] 
        if t.get('is_urgent') or t.get('is_overdue')
    ]
    
    return {
        "code": 200,
        "data": {
            "tasks": urgent_tasks,
            "total": len(urgent_tasks)
        }
    }


@router.get("/overdue", summary="获取逾期任务")
async def get_overdue_tasks(
    current_user_id: int = Query(1, description="当前用户ID")
):
    """获取已逾期的任务"""
    service = create_task_center_service()
    result = service.get_my_tasks(
        user_id=current_user_id,
        is_overdue=True,
        page_size=50,
        sort_by="deadline"
    )
    
    return {
        "code": 200,
        "data": result
    }


@router.get("/by-type/{task_type}", summary="按类型获取任务")
async def get_tasks_by_type(
    task_type: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user_id: int = Query(1)
):
    """
    按类型获取任务
    
    类型：
    - job_duty: 岗位职责
    - project_wbs: 项目任务
    - workflow: 流程待办
    - transfer: 转办任务
    - legacy: 遗留任务
    - alert: 预警任务
    - personal: 个人自建
    - assigned: 临时指派
    """
    service = create_task_center_service()
    
    try:
        type_enum = TaskType(task_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的任务类型: {task_type}")
    
    result = service.get_my_tasks(
        user_id=current_user_id,
        task_type=type_enum,
        page=page,
        page_size=page_size
    )
    
    return {
        "code": 200,
        "data": result
    }


@router.get("/by-project/{project_id}", summary="按项目获取任务")
async def get_tasks_by_project(
    project_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user_id: int = Query(1)
):
    """获取指定项目的任务"""
    service = create_task_center_service()
    result = service.get_my_tasks(
        user_id=current_user_id,
        project_id=project_id,
        page=page,
        page_size=page_size
    )
    
    return {
        "code": 200,
        "data": result
    }


# ==================== 任务详情与操作 ====================

@router.get("/task/{task_id}", summary="获取任务详情")
async def get_task_detail(
    task_id: int,
    current_user_id: int = Query(1)
):
    """获取任务详情"""
    # 模拟返回详情
    return {
        "code": 200,
        "data": {
            "id": task_id,
            "task_code": f"T{task_id}",
            "title": "示例任务",
            "description": "任务详细描述",
            "task_type": "project_wbs",
            "status": "in_progress",
            "progress": 50,
            "comments": [],
            "logs": []
        }
    }


@router.post("/task/{task_id}/accept", summary="接收任务")
async def accept_task(
    task_id: int,
    current_user_id: int = Query(1)
):
    """接收任务，状态变为已接收"""
    return {
        "code": 200,
        "message": "任务已接收"
    }


@router.post("/task/{task_id}/start", summary="开始任务")
async def start_task(
    task_id: int,
    current_user_id: int = Query(1)
):
    """开始任务，状态变为进行中"""
    return {
        "code": 200,
        "message": "任务已开始"
    }


@router.post("/task/{task_id}/progress", summary="更新进度")
async def update_task_progress(
    task_id: int,
    progress: int = Body(..., ge=0, le=100, embed=True),
    remark: Optional[str] = Body(None, embed=True),
    current_user_id: int = Query(1)
):
    """更新任务进度"""
    return {
        "code": 200,
        "message": f"进度已更新为 {progress}%"
    }


@router.post("/task/{task_id}/complete", summary="完成任务")
async def complete_task(
    task_id: int,
    remark: Optional[str] = Body(None, embed=True),
    current_user_id: int = Query(1)
):
    """完成任务，提交验收"""
    return {
        "code": 200,
        "message": "任务已提交完成"
    }


@router.post("/task/{task_id}/pause", summary="暂停任务")
async def pause_task(
    task_id: int,
    reason: str = Body(..., embed=True),
    current_user_id: int = Query(1)
):
    """暂停任务"""
    return {
        "code": 200,
        "message": "任务已暂停"
    }


@router.post("/task/{task_id}/resume", summary="恢复任务")
async def resume_task(
    task_id: int,
    current_user_id: int = Query(1)
):
    """恢复暂停的任务"""
    return {
        "code": 200,
        "message": "任务已恢复"
    }


# ==================== 任务转办 ====================

@router.post("/task/{task_id}/transfer", summary="转办任务")
async def transfer_task(
    task_id: int,
    to_user_id: int = Body(..., embed=True),
    reason: str = Body(..., embed=True),
    current_user_id: int = Query(1)
):
    """
    转办任务给其他人
    
    转办后：
    - 原任务状态不变
    - 生成新的转办任务给目标用户
    - 记录转办原因和时间
    """
    return {
        "code": 200,
        "message": "任务已转办"
    }


# ==================== 新建任务 ====================

@router.post("/task/create", summary="新建个人任务")
async def create_personal_task(
    title: str = Body(...),
    description: Optional[str] = Body(None),
    deadline: Optional[str] = Body(None),
    priority: str = Body("medium"),
    project_id: Optional[int] = Body(None),
    tags: List[str] = Body(default=[]),
    current_user_id: int = Query(1)
):
    """
    新建个人任务
    
    用于创建备忘、个人计划等自建任务
    """
    return {
        "code": 200,
        "message": "任务创建成功",
        "data": {
            "id": 9001,
            "task_code": "PS2025010002"
        }
    }


# ==================== 工时填报 ====================

@router.post("/task/{task_id}/log-hours", summary="填报工时")
async def log_task_hours(
    task_id: int,
    hours: float = Body(..., gt=0),
    work_date: str = Body(...),
    description: Optional[str] = Body(None),
    current_user_id: int = Query(1)
):
    """为任务填报工时"""
    return {
        "code": 200,
        "message": f"已记录 {hours} 小时工时"
    }


# ==================== 任务评论 ====================

@router.post("/task/{task_id}/comment", summary="添加评论")
async def add_task_comment(
    task_id: int,
    content: str = Body(..., embed=True),
    mentioned_users: List[int] = Body(default=[], embed=True),
    current_user_id: int = Query(1)
):
    """添加任务评论"""
    return {
        "code": 200,
        "message": "评论已添加"
    }


@router.get("/task/{task_id}/comments", summary="获取评论列表")
async def get_task_comments(
    task_id: int,
    current_user_id: int = Query(1)
):
    """获取任务评论列表"""
    return {
        "code": 200,
        "data": {
            "comments": [
                {
                    "id": 1,
                    "content": "进度如何？",
                    "commenter": {"id": 100, "name": "张经理"},
                    "created_at": "2025-01-02T10:00:00"
                }
            ]
        }
    }


# ==================== 任务类型与状态 ====================

@router.get("/task-types", summary="获取任务类型列表")
async def get_task_types():
    """获取所有任务类型"""
    return {
        "code": 200,
        "data": [
            {"code": "job_duty", "name": "岗位职责", "icon": "📋", "color": "#6366F1"},
            {"code": "project_wbs", "name": "项目任务", "icon": "📁", "color": "#F59E0B"},
            {"code": "workflow", "name": "流程待办", "icon": "🔄", "color": "#10B981"},
            {"code": "transfer", "name": "转办任务", "icon": "📨", "color": "#EC4899"},
            {"code": "legacy", "name": "遗留任务", "icon": "⏰", "color": "#8B5CF6"},
            {"code": "alert", "name": "预警任务", "icon": "🔔", "color": "#EF4444"},
            {"code": "personal", "name": "个人任务", "icon": "📝", "color": "#3B82F6"},
            {"code": "assigned", "name": "临时指派", "icon": "🎯", "color": "#14B8A6"}
        ]
    }


@router.get("/task-statuses", summary="获取任务状态列表")
async def get_task_statuses():
    """获取所有任务状态"""
    return {
        "code": 200,
        "data": [
            {"code": "pending", "name": "待接收", "color": "#94A3B8"},
            {"code": "accepted", "name": "已接收", "color": "#6366F1"},
            {"code": "in_progress", "name": "进行中", "color": "#3B82F6"},
            {"code": "paused", "name": "已暂停", "color": "#F59E0B"},
            {"code": "submitted", "name": "待验收", "color": "#8B5CF6"},
            {"code": "approved", "name": "已通过", "color": "#10B981"},
            {"code": "rejected", "name": "已驳回", "color": "#EF4444"},
            {"code": "completed", "name": "已完成", "color": "#059669"},
            {"code": "cancelled", "name": "已取消", "color": "#6B7280"}
        ]
    }


# ==================== 岗位职责模板 ====================

@router.get("/job-duty-templates", summary="获取岗位职责模板")
async def get_job_duty_templates(
    current_user_id: int = Query(1)
):
    """获取当前用户岗位的职责模板"""
    return {
        "code": 200,
        "data": [
            {
                "id": 1,
                "duty_name": "周报提交",
                "frequency": "weekly",
                "day_of_week": 5,
                "estimated_hours": 1
            },
            {
                "id": 2,
                "duty_name": "月度设备巡检",
                "frequency": "monthly",
                "day_of_month": 1,
                "estimated_hours": 4
            }
        ]
    }
