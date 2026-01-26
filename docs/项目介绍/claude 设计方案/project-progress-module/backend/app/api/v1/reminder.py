"""
任务提醒 API
提醒设置、消息通知、站内消息管理
"""
from fastapi import APIRouter, Query, HTTPException, Body, BackgroundTasks
from typing import Optional, List, Dict
from datetime import datetime

from app.services.reminder_service import (
    get_reminder_service,
    ReminderType,
    NotifyChannel,
    ReminderScheduler
)

router = APIRouter(prefix="/reminders", tags=["任务提醒"])


# ==================== 提醒设置 ====================

@router.get("/settings", summary="获取提醒设置")
async def get_reminder_settings(
    current_user_id: int = Query(1, description="当前用户ID")
):
    """
    获取用户的提醒设置
    
    包括：
    - 渠道开关（企业微信、邮件、APP推送等）
    - 类型开关（任务分配、截止提醒、逾期提醒等）
    - 免打扰设置
    - 提前提醒时间设置
    """
    service = get_reminder_service()
    settings = service.get_user_settings(current_user_id)
    
    return {
        "code": 200,
        "data": settings.to_dict()
    }


@router.put("/settings", summary="更新提醒设置")
async def update_reminder_settings(
    settings: Dict = Body(...),
    current_user_id: int = Query(1, description="当前用户ID")
):
    """
    更新用户的提醒设置
    
    请求体示例：
    ```json
    {
        "channels": {
            "wechat": true,
            "email": true,
            "sms": false,
            "in_app": true,
            "app_push": true
        },
        "types": {
            "task_assigned": true,
            "deadline_reminder": true,
            "overdue_reminder": true,
            "progress_urge": true,
            "transfer_notify": true,
            "daily_summary": true
        },
        "dnd": {
            "enabled": true,
            "start": "22:00",
            "end": "08:00"
        },
        "deadline_remind_hours": [24, 4, 1]
    }
    ```
    """
    service = get_reminder_service()
    updated = service.update_user_settings(current_user_id, settings)
    
    return {
        "code": 200,
        "message": "设置已更新",
        "data": updated.to_dict()
    }


@router.post("/settings/reset", summary="重置提醒设置")
async def reset_reminder_settings(
    current_user_id: int = Query(1, description="当前用户ID")
):
    """重置为默认设置"""
    service = get_reminder_service()
    # 删除现有设置，下次获取会创建默认设置
    if current_user_id in service.user_settings:
        del service.user_settings[current_user_id]
    
    settings = service.get_user_settings(current_user_id)
    
    return {
        "code": 200,
        "message": "已重置为默认设置",
        "data": settings.to_dict()
    }


# ==================== 站内消息 ====================

@router.get("/notifications", summary="获取站内消息")
async def get_notifications(
    status: str = Query("unread", description="状态: all/unread/read"),
    type: Optional[str] = Query(None, description="消息类型"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user_id: int = Query(1, description="当前用户ID")
):
    """
    获取站内消息列表
    
    支持按状态、类型筛选
    """
    service = get_reminder_service()
    
    if status == "unread":
        messages = service.get_unread_notifications(current_user_id, limit=page_size)
    else:
        # 获取全部消息（实际需要从数据库查询）
        messages = service.get_unread_notifications(current_user_id, limit=100)
    
    # 类型筛选
    if type:
        messages = [m for m in messages if m.get('type') == type]
    
    # 统计未读数
    unread_count = len([m for m in messages if not m.get('is_read')])
    
    # 分页
    start = (page - 1) * page_size
    end = start + page_size
    paged = messages[start:end]
    
    return {
        "code": 200,
        "data": {
            "notifications": paged,
            "total": len(messages),
            "unread_count": unread_count,
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/notifications/unread-count", summary="获取未读消息数")
async def get_unread_count(
    current_user_id: int = Query(1, description="当前用户ID")
):
    """获取未读消息数量（用于消息角标）"""
    service = get_reminder_service()
    messages = service.get_unread_notifications(current_user_id, limit=100)
    
    return {
        "code": 200,
        "data": {
            "unread_count": len(messages)
        }
    }


@router.post("/notifications/{notification_id}/read", summary="标记消息已读")
async def mark_notification_read(
    notification_id: str,
    current_user_id: int = Query(1, description="当前用户ID")
):
    """标记单条消息为已读"""
    service = get_reminder_service()
    service.mark_notification_read(current_user_id, notification_id)
    
    return {
        "code": 200,
        "message": "已标记为已读"
    }


@router.post("/notifications/read-all", summary="全部标记已读")
async def mark_all_read(
    current_user_id: int = Query(1, description="当前用户ID")
):
    """将所有消息标记为已读"""
    service = get_reminder_service()
    messages = service.get_unread_notifications(current_user_id, limit=1000)
    
    for msg in messages:
        service.mark_notification_read(current_user_id, msg['id'])
    
    return {
        "code": 200,
        "message": f"已将 {len(messages)} 条消息标记为已读"
    }


@router.delete("/notifications/{notification_id}", summary="删除消息")
async def delete_notification(
    notification_id: str,
    current_user_id: int = Query(1, description="当前用户ID")
):
    """删除单条消息"""
    # 实际从数据库删除
    return {
        "code": 200,
        "message": "消息已删除"
    }


# ==================== 手动发送提醒 ====================

@router.post("/send/task-assigned", summary="发送任务分配提醒")
async def send_task_assigned_reminder(
    background_tasks: BackgroundTasks,
    user_id: int = Body(...),
    user_name: str = Body(...),
    task_id: int = Body(...),
    task_title: str = Body(...),
    assigner: str = Body(...),
    deadline: str = Body(...),
    priority: str = Body(...)
):
    """
    发送任务分配提醒
    
    通常由任务分配时自动调用
    """
    service = get_reminder_service()
    
    # 异步发送
    background_tasks.add_task(
        service.send_task_assigned,
        user_id, user_name, task_id, task_title, assigner, deadline, priority
    )
    
    return {
        "code": 200,
        "message": "提醒已发送"
    }


@router.post("/send/transfer", summary="发送转办通知")
async def send_transfer_reminder(
    background_tasks: BackgroundTasks,
    user_id: int = Body(...),
    user_name: str = Body(...),
    task_id: int = Body(...),
    task_title: str = Body(...),
    from_user: str = Body(...),
    reason: str = Body(...),
    deadline: str = Body(...)
):
    """发送任务转办通知"""
    service = get_reminder_service()
    
    background_tasks.add_task(
        service.send_transfer_notify,
        user_id, user_name, task_id, task_title, from_user, reason, deadline
    )
    
    return {
        "code": 200,
        "message": "转办通知已发送"
    }


@router.post("/send/urge", summary="发送催办提醒")
async def send_urge_reminder(
    background_tasks: BackgroundTasks,
    user_id: int = Body(..., description="被催办人ID"),
    task_id: int = Body(...),
    task_title: str = Body(...),
    remark: str = Body("", description="催办备注"),
    current_user_id: int = Query(1),
    current_user_name: str = Query("催办人")
):
    """
    发送催办提醒
    
    用于领导催促任务进度
    """
    service = get_reminder_service()
    
    message = service.create_reminder(
        type=ReminderType.PROGRESS_URGE,
        user_id=user_id,
        user_name="被催办人",
        data={
            "task_id": task_id,
            "task_title": task_title,
            "urger": current_user_name,
            "progress": 50,  # 实际应查询
            "expected_progress": 80,
            "remark": remark or "请尽快推进任务"
        }
    )
    
    if message:
        background_tasks.add_task(service.send_reminder, message)
    
    return {
        "code": 200,
        "message": "催办提醒已发送"
    }


# ==================== 提醒类型与渠道 ====================

@router.get("/types", summary="获取提醒类型列表")
async def get_reminder_types():
    """获取所有提醒类型"""
    return {
        "code": 200,
        "data": [
            {"code": "task_assigned", "name": "任务分配", "description": "新任务分配给您时通知", "can_disable": True},
            {"code": "deadline_24h", "name": "24小时提醒", "description": "任务截止前24小时提醒", "can_disable": True},
            {"code": "deadline_4h", "name": "4小时提醒", "description": "任务截止前4小时提醒", "can_disable": True},
            {"code": "deadline_1h", "name": "1小时提醒", "description": "任务截止前1小时提醒", "can_disable": True},
            {"code": "task_overdue", "name": "逾期提醒", "description": "任务逾期时通知", "can_disable": True},
            {"code": "progress_urge", "name": "催办提醒", "description": "收到催办时通知", "can_disable": False},
            {"code": "task_transferred", "name": "转办通知", "description": "收到转办任务时通知", "can_disable": True},
            {"code": "workflow_pending", "name": "流程待办", "description": "有流程待您处理时通知", "can_disable": True},
            {"code": "task_approved", "name": "验收通过", "description": "任务通过验收时通知", "can_disable": True},
            {"code": "task_rejected", "name": "任务驳回", "description": "任务被驳回时通知", "can_disable": False},
            {"code": "daily_summary", "name": "每日汇总", "description": "每日任务汇总（早上8点）", "can_disable": True},
            {"code": "weekly_summary", "name": "每周汇总", "description": "每周工作汇总（周一早上）", "can_disable": True}
        ]
    }


@router.get("/channels", summary="获取通知渠道列表")
async def get_notify_channels():
    """获取所有通知渠道"""
    return {
        "code": 200,
        "data": [
            {"code": "wechat_work", "name": "企业微信", "icon": "💬", "description": "通过企业微信应用推送"},
            {"code": "email", "name": "邮件", "icon": "📧", "description": "发送到您的工作邮箱"},
            {"code": "sms", "name": "短信", "icon": "📱", "description": "发送短信到您的手机（紧急事项）"},
            {"code": "in_app", "name": "站内消息", "icon": "🔔", "description": "系统内消息中心"},
            {"code": "app_push", "name": "APP推送", "icon": "📲", "description": "推送到移动APP"}
        ]
    }


# ==================== 定时任务管理（管理员） ====================

@router.post("/scheduler/scan", summary="手动触发扫描")
async def trigger_scan(
    background_tasks: BackgroundTasks,
    admin_key: str = Query(..., description="管理员密钥")
):
    """
    手动触发提醒扫描
    
    管理员功能，用于测试或紧急情况
    """
    if admin_key != "admin_secret_key":
        raise HTTPException(status_code=403, detail="无权限")
    
    service = get_reminder_service()
    scheduler = ReminderScheduler(service)
    
    background_tasks.add_task(scheduler.run_once)
    
    return {
        "code": 200,
        "message": "扫描任务已触发"
    }


@router.post("/scheduler/send-daily-summary", summary="发送每日汇总")
async def trigger_daily_summary(
    background_tasks: BackgroundTasks,
    admin_key: str = Query(..., description="管理员密钥")
):
    """
    手动触发发送每日汇总
    
    管理员功能
    """
    if admin_key != "admin_secret_key":
        raise HTTPException(status_code=403, detail="无权限")
    
    service = get_reminder_service()
    scheduler = ReminderScheduler(service)
    
    background_tasks.add_task(scheduler.send_daily_summaries)
    
    return {
        "code": 200,
        "message": "每日汇总已触发"
    }


# ==================== 测试接口 ====================

@router.post("/test/send", summary="测试发送提醒")
async def test_send_reminder(
    type: str = Body("task_assigned", description="提醒类型"),
    current_user_id: int = Query(1)
):
    """
    测试发送提醒（仅发送给自己）
    
    用于测试各渠道是否正常
    """
    service = get_reminder_service()
    
    if type == "task_assigned":
        await service.send_task_assigned(
            user_id=current_user_id,
            user_name="测试用户",
            task_id=9999,
            task_title="测试任务",
            assigner="系统测试",
            deadline="2025-01-05 18:00",
            priority="中"
        )
    elif type == "deadline":
        await service.send_deadline_reminder(
            user_id=current_user_id,
            user_name="测试用户",
            task_id=9999,
            task_title="测试任务",
            deadline="2025-01-04 18:00",
            progress=50,
            hours_left=4
        )
    elif type == "overdue":
        await service.send_overdue_reminder(
            user_id=current_user_id,
            user_name="测试用户",
            task_id=9999,
            task_title="测试任务",
            deadline="2025-01-02 18:00",
            overdue_hours=24
        )
    
    return {
        "code": 200,
        "message": "测试提醒已发送，请检查各渠道"
    }
