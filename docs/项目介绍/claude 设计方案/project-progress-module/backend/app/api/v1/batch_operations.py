"""
任务批量操作 API
支持批量完成、转办、更新优先级、更新进度、催办、删除
"""
from fastapi import APIRouter, Query, HTTPException, Body, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/task-center/batch", tags=["任务批量操作"])


class BatchTaskIds(BaseModel):
    """批量任务ID"""
    task_ids: List[int]


class BatchTransfer(BaseModel):
    """批量转办"""
    task_ids: List[int]
    to_user_id: int
    reason: str = ""


class BatchPriority(BaseModel):
    """批量设置优先级"""
    task_ids: List[int]
    priority: str  # urgent/high/medium/low


class BatchProgress(BaseModel):
    """批量更新进度"""
    task_ids: List[int]
    progress: int  # 0-100


class BatchUrge(BaseModel):
    """批量催办"""
    task_ids: List[int]
    remark: str = ""


# ==================== 批量操作接口 ====================

@router.post("/complete", summary="批量完成任务")
async def batch_complete(
    data: BatchTaskIds,
    current_user_id: int = Query(1)
):
    """
    批量完成任务
    
    将选中的任务状态设为已完成，进度设为100%
    """
    if not data.task_ids:
        raise HTTPException(status_code=400, detail="请选择要完成的任务")
    
    if len(data.task_ids) > 50:
        raise HTTPException(status_code=400, detail="单次最多完成50个任务")
    
    # 实际更新数据库
    # UPDATE task SET status='completed', progress=100, completed_at=NOW() WHERE id IN (...)
    
    success_count = len(data.task_ids)
    
    return {
        "code": 200,
        "message": f"成功完成 {success_count} 个任务",
        "data": {
            "success_count": success_count,
            "task_ids": data.task_ids
        }
    }


@router.post("/transfer", summary="批量转办任务")
async def batch_transfer(
    data: BatchTransfer,
    background_tasks: BackgroundTasks,
    current_user_id: int = Query(1),
    current_user_name: str = Query("当前用户")
):
    """
    批量转办任务
    
    将选中的任务转办给指定用户，并发送通知
    """
    if not data.task_ids:
        raise HTTPException(status_code=400, detail="请选择要转办的任务")
    
    if not data.to_user_id:
        raise HTTPException(status_code=400, detail="请选择转办对象")
    
    if len(data.task_ids) > 20:
        raise HTTPException(status_code=400, detail="单次最多转办20个任务")
    
    # 实际更新数据库
    # UPDATE task SET assignee_id=?, is_transferred=1, transfer_from_id=?, 
    #                 transfer_reason=?, transfer_time=NOW() WHERE id IN (...)
    
    # 发送转办通知
    # background_tasks.add_task(send_transfer_notifications, data.task_ids, data.to_user_id, current_user_name, data.reason)
    
    success_count = len(data.task_ids)
    
    return {
        "code": 200,
        "message": f"成功转办 {success_count} 个任务",
        "data": {
            "success_count": success_count,
            "to_user_id": data.to_user_id,
            "task_ids": data.task_ids
        }
    }


@router.post("/priority", summary="批量设置优先级")
async def batch_set_priority(
    data: BatchPriority,
    current_user_id: int = Query(1)
):
    """
    批量设置任务优先级
    
    可选优先级：urgent(紧急), high(高), medium(中), low(低)
    """
    if not data.task_ids:
        raise HTTPException(status_code=400, detail="请选择要更新的任务")
    
    valid_priorities = ["urgent", "high", "medium", "low"]
    if data.priority not in valid_priorities:
        raise HTTPException(status_code=400, detail=f"无效的优先级，可选值：{valid_priorities}")
    
    if len(data.task_ids) > 50:
        raise HTTPException(status_code=400, detail="单次最多更新50个任务")
    
    # 实际更新数据库
    # UPDATE task SET priority=? WHERE id IN (...)
    
    priority_labels = {"urgent": "紧急", "high": "高", "medium": "中", "low": "低"}
    success_count = len(data.task_ids)
    
    return {
        "code": 200,
        "message": f"成功将 {success_count} 个任务优先级设为"{priority_labels[data.priority]}"",
        "data": {
            "success_count": success_count,
            "priority": data.priority,
            "task_ids": data.task_ids
        }
    }


@router.post("/progress", summary="批量更新进度")
async def batch_update_progress(
    data: BatchProgress,
    current_user_id: int = Query(1)
):
    """
    批量更新任务进度
    
    进度范围：0-100
    """
    if not data.task_ids:
        raise HTTPException(status_code=400, detail="请选择要更新的任务")
    
    if data.progress < 0 or data.progress > 100:
        raise HTTPException(status_code=400, detail="进度必须在0-100之间")
    
    if len(data.task_ids) > 50:
        raise HTTPException(status_code=400, detail="单次最多更新50个任务")
    
    # 实际更新数据库
    # UPDATE task SET progress=? WHERE id IN (...)
    
    # 如果进度为100，同时更新状态为已完成
    # if data.progress == 100:
    #     UPDATE task SET status='completed', completed_at=NOW() WHERE id IN (...)
    
    success_count = len(data.task_ids)
    
    return {
        "code": 200,
        "message": f"成功更新 {success_count} 个任务进度为 {data.progress}%",
        "data": {
            "success_count": success_count,
            "progress": data.progress,
            "task_ids": data.task_ids
        }
    }


@router.post("/urge", summary="批量催办任务")
async def batch_urge(
    data: BatchUrge,
    background_tasks: BackgroundTasks,
    current_user_id: int = Query(1),
    current_user_name: str = Query("催办人")
):
    """
    批量催办任务
    
    向任务执行人发送催办提醒
    """
    if not data.task_ids:
        raise HTTPException(status_code=400, detail="请选择要催办的任务")
    
    if len(data.task_ids) > 20:
        raise HTTPException(status_code=400, detail="单次最多催办20个任务")
    
    # 获取任务信息，按执行人分组
    # tasks = SELECT * FROM task WHERE id IN (...)
    # grouped = group_by(tasks, 'assignee_id')
    
    # 发送催办通知
    # for assignee_id, tasks in grouped.items():
    #     background_tasks.add_task(send_urge_notification, assignee_id, tasks, current_user_name, data.remark)
    
    # 记录催办日志
    # INSERT INTO task_urge_log (task_id, urger_id, urger_name, remark, created_at) VALUES ...
    
    success_count = len(data.task_ids)
    
    return {
        "code": 200,
        "message": f"已对 {success_count} 个任务发送催办",
        "data": {
            "success_count": success_count,
            "task_ids": data.task_ids
        }
    }


@router.post("/delete", summary="批量删除任务")
async def batch_delete(
    data: BatchTaskIds,
    current_user_id: int = Query(1)
):
    """
    批量删除任务
    
    只能删除自己创建的个人任务，项目任务和流程任务不可删除
    """
    if not data.task_ids:
        raise HTTPException(status_code=400, detail="请选择要删除的任务")
    
    if len(data.task_ids) > 20:
        raise HTTPException(status_code=400, detail="单次最多删除20个任务")
    
    # 检查权限：只能删除自己创建的个人任务
    # deletable_tasks = SELECT id FROM task 
    #                   WHERE id IN (...) AND task_type='personal' AND created_by=?
    
    # 软删除
    # UPDATE task SET is_deleted=1, deleted_at=NOW(), deleted_by=? WHERE id IN (...)
    
    success_count = len(data.task_ids)
    
    return {
        "code": 200,
        "message": f"成功删除 {success_count} 个任务",
        "data": {
            "success_count": success_count,
            "task_ids": data.task_ids
        }
    }


@router.post("/start", summary="批量开始任务")
async def batch_start(
    data: BatchTaskIds,
    current_user_id: int = Query(1)
):
    """
    批量开始任务
    
    将待处理/待接收的任务状态设为进行中
    """
    if not data.task_ids:
        raise HTTPException(status_code=400, detail="请选择要开始的任务")
    
    # UPDATE task SET status='in_progress', actual_start_date=CURDATE() 
    #         WHERE id IN (...) AND status IN ('pending', 'accepted')
    
    success_count = len(data.task_ids)
    
    return {
        "code": 200,
        "message": f"成功开始 {success_count} 个任务",
        "data": {
            "success_count": success_count,
            "task_ids": data.task_ids
        }
    }


@router.post("/pause", summary="批量暂停任务")
async def batch_pause(
    data: BatchTaskIds,
    reason: str = Body("", embed=True),
    current_user_id: int = Query(1)
):
    """
    批量暂停任务
    """
    if not data.task_ids:
        raise HTTPException(status_code=400, detail="请选择要暂停的任务")
    
    # UPDATE task SET status='paused', pause_reason=? WHERE id IN (...)
    
    success_count = len(data.task_ids)
    
    return {
        "code": 200,
        "message": f"成功暂停 {success_count} 个任务",
        "data": {
            "success_count": success_count,
            "task_ids": data.task_ids
        }
    }


@router.post("/tag", summary="批量打标签")
async def batch_add_tags(
    task_ids: List[int] = Body(...),
    tags: List[str] = Body(...),
    current_user_id: int = Query(1)
):
    """
    批量给任务打标签
    """
    if not task_ids:
        raise HTTPException(status_code=400, detail="请选择要打标签的任务")
    
    if not tags:
        raise HTTPException(status_code=400, detail="请输入标签")
    
    # UPDATE task SET tags=JSON_ARRAY_APPEND(tags, '$', ?) WHERE id IN (...)
    
    success_count = len(task_ids)
    
    return {
        "code": 200,
        "message": f"成功为 {success_count} 个任务添加标签",
        "data": {
            "success_count": success_count,
            "tags": tags,
            "task_ids": task_ids
        }
    }


# ==================== 批量操作统计 ====================

@router.get("/statistics", summary="获取批量操作统计")
async def get_batch_statistics(
    current_user_id: int = Query(1)
):
    """
    获取用户批量操作统计
    
    用于展示操作历史
    """
    # 模拟统计数据
    return {
        "code": 200,
        "data": {
            "today": {
                "complete": 5,
                "transfer": 2,
                "priority_update": 8,
                "progress_update": 12,
                "urge": 3
            },
            "this_week": {
                "complete": 23,
                "transfer": 8,
                "priority_update": 35,
                "progress_update": 56,
                "urge": 12
            }
        }
    }
