"""
负荷管理API接口
"""
from fastapi import APIRouter, Query
from typing import Optional
from datetime import date
from pydantic import BaseModel

router = APIRouter(prefix="/workload", tags=["负荷管理"])

@router.get("/user/{user_id}")
async def get_user_workload(
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """获取用户负荷详情"""
    workload = {
        "user_id": user_id,
        "user_name": "张工",
        "dept_name": "机械组",
        "period": {"start": str(start_date or "2025-01-01"), "end": str(end_date or "2025-01-31")},
        "summary": {
            "total_assigned_hours": 180,
            "standard_hours": 176,
            "allocation_rate": 102.3,
            "actual_hours": 168,
            "efficiency": 93.3
        },
        "by_project": [
            {"project_id": 1, "project_code": "PRJ-001", "project_name": "某客户设备", "assigned_hours": 120, "actual_hours": 110, "task_count": 5},
            {"project_id": 2, "project_code": "PRJ-002", "project_name": "电池检测设备", "assigned_hours": 60, "actual_hours": 58, "task_count": 3}
        ],
        "daily_load": [
            {"date": "2025-01-02", "assigned": 8, "actual": 8},
            {"date": "2025-01-03", "assigned": 10, "actual": 9},
            {"date": "2025-01-06", "assigned": 8, "actual": 8}
        ],
        "tasks": [
            {"task_id": 101, "task_name": "方案设计", "project_code": "PRJ-001", "plan_hours": 40, "actual_hours": 38, "progress": 80, "deadline": "2025-01-10"},
            {"task_id": 102, "task_name": "结构设计", "project_code": "PRJ-001", "plan_hours": 80, "actual_hours": 30, "progress": 30, "deadline": "2025-01-25"}
        ]
    }
    return {"code": 200, "message": "success", "data": workload}

@router.get("/team")
async def get_team_workload(
    dept_id: Optional[int] = None,
    project_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """获取团队负荷概览"""
    team_workload = [
        {"user_id": 1, "user_name": "张工", "dept_name": "机械组", "role": "ME", "assigned_hours": 180, "standard_hours": 176, "allocation_rate": 102.3, "task_count": 8, "overdue_count": 0},
        {"user_id": 2, "user_name": "李工", "dept_name": "机械组", "role": "ME", "assigned_hours": 160, "standard_hours": 176, "allocation_rate": 90.9, "task_count": 6, "overdue_count": 1},
        {"user_id": 3, "user_name": "王工", "dept_name": "电气组", "role": "EE", "assigned_hours": 200, "standard_hours": 176, "allocation_rate": 113.6, "task_count": 10, "overdue_count": 2},
        {"user_id": 4, "user_name": "赵工", "dept_name": "电气组", "role": "EE", "assigned_hours": 140, "standard_hours": 176, "allocation_rate": 79.5, "task_count": 5, "overdue_count": 0},
        {"user_id": 5, "user_name": "钱工", "dept_name": "测试组", "role": "TE", "assigned_hours": 120, "standard_hours": 176, "allocation_rate": 68.2, "task_count": 4, "overdue_count": 0}
    ]
    return {"code": 200, "message": "success", "data": team_workload}

@router.get("/heatmap")
async def get_workload_heatmap(
    dept_id: Optional[int] = None,
    start_date: date = None,
    weeks: int = Query(4, ge=1, le=12)
):
    """获取负荷热力图数据"""
    heatmap = {
        "users": ["张工", "李工", "王工", "赵工", "钱工"],
        "weeks": ["W01", "W02", "W03", "W04"],
        "data": [
            [100, 95, 110, 105],
            [90, 85, 95, 90],
            [120, 115, 130, 125],
            [80, 75, 85, 80],
            [70, 65, 75, 70]
        ]
    }
    return {"code": 200, "message": "success", "data": heatmap}

@router.get("/available")
async def get_available_resources(
    dept_id: Optional[int] = None,
    skill: Optional[str] = None,
    start_date: date = None,
    end_date: date = None,
    min_hours: float = Query(8, ge=0)
):
    """查询可用资源（负荷低于阈值的人员）"""
    available = [
        {"user_id": 4, "user_name": "赵工", "dept_name": "电气组", "role": "EE", "available_hours": 36, "skills": ["电气设计", "PLC编程"]},
        {"user_id": 5, "user_name": "钱工", "dept_name": "测试组", "role": "TE", "available_hours": 56, "skills": ["测试", "调试"]}
    ]
    return {"code": 200, "message": "success", "data": available}


"""
预警管理API接口
"""
alert_router = APIRouter(prefix="/alerts", tags=["预警管理"])

@alert_router.get("")
async def get_alert_list(
    project_id: Optional[int] = None,
    alert_type: Optional[str] = None,
    alert_level: Optional[str] = None,
    status: Optional[str] = Query("待处理"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
):
    """获取预警列表"""
    alerts = [
        {"alert_id": 1, "alert_type": "任务逾期", "alert_level": "红", "alert_title": "任务\"电气设计\"已逾期3天", "project_code": "PRJ-001", "task_name": "电气设计", "owner_name": "王工", "status": "待处理", "created_time": "2025-01-02 10:00"},
        {"alert_id": 2, "alert_type": "进度滞后", "alert_level": "橙", "alert_title": "项目PRJ-003进度滞后10%", "project_code": "PRJ-003", "task_name": None, "owner_name": "李经理", "status": "待处理", "created_time": "2025-01-02 09:00"},
        {"alert_id": 3, "alert_type": "任务即将到期", "alert_level": "黄", "alert_title": "任务\"BOM清单\"将于3天后到期", "project_code": "PRJ-001", "task_name": "BOM清单", "owner_name": "张工", "status": "待处理", "created_time": "2025-01-02 08:00"},
        {"alert_id": 4, "alert_type": "负荷过高", "alert_level": "黄", "alert_title": "王工本周负荷达到130%", "project_code": None, "task_name": None, "owner_name": "王工", "status": "已处理", "created_time": "2025-01-01 09:00"}
    ]
    return {"code": 200, "message": "success", "data": {"total": len(alerts), "list": alerts}}

@alert_router.get("/{alert_id}")
async def get_alert_detail(alert_id: int):
    """获取预警详情"""
    alert = {
        "alert_id": alert_id,
        "alert_type": "任务逾期",
        "alert_level": "红",
        "alert_title": "任务\"电气设计\"已逾期3天",
        "alert_content": "任务计划结束日期为2024-12-30，当前进度60%，已逾期3天",
        "project_id": 1,
        "project_code": "PRJ-001",
        "project_name": "某客户自动化测试设备",
        "task_id": 103,
        "task_name": "电气设计",
        "owner_id": 3,
        "owner_name": "王工",
        "status": "待处理",
        "created_time": "2025-01-02 10:00",
        "notified_users": ["王工", "张经理", "李工"],
        "handle_history": []
    }
    return {"code": 200, "message": "success", "data": alert}

class AlertHandle(BaseModel):
    action: str  # 忽略/处理中/已解决
    comment: Optional[str] = None

@alert_router.put("/{alert_id}/handle")
async def handle_alert(alert_id: int, handle: AlertHandle):
    """处理预警"""
    return {"code": 200, "message": "预警已处理", "data": {"alert_id": alert_id, "status": handle.action}}

@alert_router.get("/statistics")
async def get_alert_statistics(
    project_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """预警统计分析"""
    stats = {
        "summary": {"total": 45, "pending": 8, "processing": 5, "resolved": 32},
        "by_level": {"红": 5, "橙": 12, "黄": 28},
        "by_type": {"任务逾期": 15, "进度滞后": 10, "任务即将到期": 12, "负荷过高": 5, "里程碑风险": 3},
        "trend": [
            {"date": "2025-01-01", "new": 5, "resolved": 3},
            {"date": "2025-01-02", "new": 8, "resolved": 6},
            {"date": "2025-01-03", "new": 3, "resolved": 5}
        ],
        "top_projects": [
            {"project_code": "PRJ-003", "alert_count": 12},
            {"project_code": "PRJ-001", "alert_count": 8},
            {"project_code": "PRJ-002", "alert_count": 5}
        ]
    }
    return {"code": 200, "message": "success", "data": stats}

@alert_router.post("/check")
async def trigger_alert_check(project_id: Optional[int] = None):
    """手动触发预警检查"""
    return {"code": 200, "message": "预警检查完成", "data": {"new_alerts": 3, "updated_alerts": 2}}
