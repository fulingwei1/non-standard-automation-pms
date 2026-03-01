"""
项目管理API接口
"""
from fastapi import APIRouter, Query
from typing import Optional
from datetime import date
from pydantic import BaseModel

router = APIRouter(prefix="/projects", tags=["项目管理"])

# ============== Pydantic模型 ==============

class ProjectCreate(BaseModel):
    project_code: str
    project_name: str
    customer_id: Optional[int] = None
    project_level: str = 'C'
    pm_id: Optional[int] = None
    te_id: Optional[int] = None
    plan_start_date: Optional[date] = None
    plan_end_date: Optional[date] = None
    plan_manhours: Optional[float] = None

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    project_level: Optional[str] = None
    pm_id: Optional[int] = None
    te_id: Optional[int] = None
    plan_start_date: Optional[date] = None
    plan_end_date: Optional[date] = None
    status: Optional[str] = None

# ============== API接口 ==============

@router.get("")
async def get_project_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    level: Optional[str] = None,
    pm_id: Optional[int] = None,
    keyword: Optional[str] = None
):
    """获取项目列表"""
    projects = [
        {"project_id": 1, "project_code": "PRJ-2025-001", "project_name": "某客户自动化测试设备", "customer_name": "深圳XX科技", "project_level": "A", "pm_name": "张经理", "plan_end_date": "2025-03-31", "plan_manhours": 800, "actual_manhours": 320, "status": "进行中", "progress_rate": 45, "health_status": "黄", "current_phase": "结构设计"},
        {"project_id": 2, "project_code": "PRJ-2025-002", "project_name": "电池包检测设备", "customer_name": "东莞YY电池", "project_level": "B", "pm_name": "王经理", "plan_end_date": "2025-02-28", "plan_manhours": 600, "actual_manhours": 480, "status": "进行中", "progress_rate": 80, "health_status": "绿", "current_phase": "装配调试"},
        {"project_id": 3, "project_code": "PRJ-2025-003", "project_name": "芯片测试平台", "customer_name": "广州ZZ半导体", "project_level": "A", "pm_name": "李经理", "plan_end_date": "2025-04-30", "plan_manhours": 1200, "actual_manhours": 240, "status": "进行中", "progress_rate": 20, "health_status": "红", "current_phase": "方案设计"}
    ]
    return {"code": 200, "message": "success", "data": {"total": len(projects), "list": projects}}

@router.post("")
async def create_project(project: ProjectCreate):
    """创建项目"""
    return {"code": 200, "message": "项目创建成功", "data": {"project_id": 1, "project_code": project.project_code}}

@router.get("/{project_id}")
async def get_project_detail(project_id: int):
    """获取项目详情"""
    project = {"project_id": project_id, "project_code": "PRJ-2025-001", "project_name": "某客户自动化测试设备", "customer_name": "深圳XX科技", "project_level": "A", "pm_name": "张经理", "te_name": "李工", "plan_start_date": "2025-01-01", "plan_end_date": "2025-03-31", "plan_manhours": 800, "actual_manhours": 320, "status": "进行中", "progress_rate": 45, "health_status": "黄", "current_phase": "结构设计"}
    return {"code": 200, "message": "success", "data": project}

@router.put("/{project_id}")
async def update_project(project_id: int, project: ProjectUpdate):
    """更新项目信息"""
    return {"code": 200, "message": "更新成功", "data": {"project_id": project_id}}

@router.get("/{project_id}/progress")
async def get_project_progress(project_id: int):
    """获取项目进度汇总"""
    progress = {
        "progress_rate": 45, "plan_progress_rate": 50, "spi": 0.9, "health_status": "黄", "current_phase": "结构设计",
        "phase_progress": [
            {"phase": "立项启动", "progress": 100, "status": "已完成", "weight": 5},
            {"phase": "方案设计", "progress": 100, "status": "已完成", "weight": 15},
            {"phase": "结构设计", "progress": 60, "status": "进行中", "weight": 20},
            {"phase": "电气设计", "progress": 40, "status": "进行中", "weight": 15},
            {"phase": "采购制造", "progress": 0, "status": "未开始", "weight": 20},
            {"phase": "装配调试", "progress": 0, "status": "未开始", "weight": 20},
            {"phase": "验收交付", "progress": 0, "status": "未开始", "weight": 5}
        ],
        "task_status_count": {"未开始": 15, "进行中": 8, "已完成": 12, "阻塞": 2}
    }
    return {"code": 200, "message": "success", "data": progress}

@router.get("/{project_id}/team")
async def get_project_team(project_id: int):
    """获取项目团队成员"""
    team = [
        {"user_id": 1, "user_name": "张经理", "role": "PM", "allocation_rate": 100},
        {"user_id": 2, "user_name": "李工", "role": "TE", "allocation_rate": 100},
        {"user_id": 3, "user_name": "王工", "role": "ME", "allocation_rate": 80},
        {"user_id": 4, "user_name": "赵工", "role": "EE", "allocation_rate": 60}
    ]
    return {"code": 200, "message": "success", "data": team}

@router.get("/{project_id}/timeline")
async def get_project_timeline(project_id: int):
    """获取项目时间线（进度日志）"""
    timeline = [
        {"log_id": 1, "event_type": "进度更新", "content": "方案设计阶段完成", "operator": "张经理", "created_time": "2025-01-10 16:00"},
        {"log_id": 2, "event_type": "里程碑", "content": "完成方案评审", "operator": "系统", "created_time": "2025-01-10 14:30"},
        {"log_id": 3, "event_type": "任务完成", "content": "总体方案设计完成", "operator": "李工", "created_time": "2025-01-08 17:00"},
        {"log_id": 4, "event_type": "项目启动", "content": "项目正式启动", "operator": "张经理", "created_time": "2025-01-02 09:00"}
    ]
    return {"code": 200, "message": "success", "data": timeline}

@router.get("/{project_id}/statistics")
async def get_project_statistics(project_id: int):
    """获取项目统计数据"""
    stats = {
        "task_count": {"total": 37, "completed": 12, "in_progress": 8, "not_started": 15, "blocked": 2},
        "manhours": {"plan": 800, "actual": 320, "remaining": 480, "overtime": 24},
        "milestone_count": {"total": 8, "completed": 2, "upcoming": 1, "overdue": 0},
        "alert_count": {"total": 5, "critical": 1, "warning": 2, "info": 2},
        "progress_history": [
            {"date": "2025-01-01", "plan": 0, "actual": 0},
            {"date": "2025-01-08", "plan": 10, "actual": 8},
            {"date": "2025-01-15", "plan": 20, "actual": 18},
            {"date": "2025-01-22", "plan": 30, "actual": 25},
            {"date": "2025-01-29", "plan": 40, "actual": 35},
            {"date": "2025-02-05", "plan": 50, "actual": 45}
        ]
    }
    return {"code": 200, "message": "success", "data": stats}
