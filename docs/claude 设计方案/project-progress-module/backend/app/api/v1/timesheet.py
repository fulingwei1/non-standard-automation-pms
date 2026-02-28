"""
工时管理API接口
"""
from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

router = APIRouter(prefix="/timesheets", tags=["工时管理"])

# ============== Pydantic模型 ==============

class TimesheetCreate(BaseModel):
    project_id: int
    task_id: int
    assign_id: Optional[int] = None
    work_date: date
    hours: float
    work_content: Optional[str] = None
    overtime_type: Optional[str] = None  # 正常/加班

class TimesheetUpdate(BaseModel):
    hours: Optional[float] = None
    work_content: Optional[str] = None
    overtime_type: Optional[str] = None

class TimesheetBatchCreate(BaseModel):
    entries: List[TimesheetCreate]

class TimesheetApprove(BaseModel):
    timesheet_ids: List[int]
    status: str  # 通过/驳回
    comment: Optional[str] = None

# ============== API接口 ==============

@router.get("")
async def get_timesheet_list(
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
):
    """
    获取工时列表
    
    筛选条件:
    - user_id: 用户ID
    - project_id: 项目ID
    - start_date/end_date: 日期范围
    - status: 状态（草稿/待审核/已通过/已驳回）
    """
    timesheets = [
        {"timesheet_id": 1, "project_code": "PRJ-001", "project_name": "某客户设备", "task_name": "方案设计", "work_date": "2025-01-02", "hours": 4, "work_content": "完成总体方案初稿", "status": "已通过", "overtime_type": "正常"},
        {"timesheet_id": 2, "project_code": "PRJ-001", "project_name": "某客户设备", "task_name": "结构设计", "work_date": "2025-01-02", "hours": 4, "work_content": "底座结构建模", "status": "已通过", "overtime_type": "正常"},
        {"timesheet_id": 3, "project_code": "PRJ-002", "project_name": "电池检测设备", "task_name": "电气设计", "work_date": "2025-01-03", "hours": 6, "work_content": "绘制电气原理图", "status": "待审核", "overtime_type": "正常"},
        {"timesheet_id": 4, "project_code": "PRJ-001", "project_name": "某客户设备", "task_name": "方案设计", "work_date": "2025-01-03", "hours": 2, "work_content": "方案评审修改", "status": "待审核", "overtime_type": "正常"}
    ]
    return {"code": 200, "message": "success", "data": {"total": len(timesheets), "list": timesheets}}

@router.post("")
async def create_timesheet(entry: TimesheetCreate):
    """创建单条工时记录"""
    return {"code": 200, "message": "工时填报成功", "data": {"timesheet_id": 1}}

@router.post("/batch")
async def create_timesheet_batch(batch: TimesheetBatchCreate):
    """批量创建工时记录"""
    return {"code": 200, "message": f"成功填报{len(batch.entries)}条工时", "data": {"count": len(batch.entries)}}

@router.put("/{timesheet_id}")
async def update_timesheet(timesheet_id: int, entry: TimesheetUpdate):
    """更新工时记录"""
    return {"code": 200, "message": "更新成功", "data": {"timesheet_id": timesheet_id}}

@router.delete("/{timesheet_id}")
async def delete_timesheet(timesheet_id: int):
    """删除工时记录（仅草稿状态可删除）"""
    return {"code": 200, "message": "删除成功"}

@router.post("/submit")
async def submit_timesheets(timesheet_ids: List[int]):
    """提交工时（草稿→待审核）"""
    return {"code": 200, "message": f"成功提交{len(timesheet_ids)}条工时", "data": {"count": len(timesheet_ids)}}

@router.post("/approve")
async def approve_timesheets(approval: TimesheetApprove):
    """审核工时（项目经理/部门经理）"""
    return {"code": 200, "message": f"审核完成，{len(approval.timesheet_ids)}条工时已{approval.status}"}

@router.get("/week")
async def get_week_timesheet(
    user_id: int,
    week_start: date
):
    """
    获取周工时表数据
    
    返回一周内按任务分组的工时数据，便于工时填报页面展示
    """
    week_data = {
        "user_id": user_id,
        "week_start": str(week_start),
        "week_end": "2025-01-05",
        "tasks": [
            {
                "assign_id": 1,
                "project_id": 1,
                "project_code": "PRJ-001",
                "task_id": 101,
                "task_name": "方案设计",
                "progress_rate": 80,
                "hours": {
                    "2024-12-30": 0, "2024-12-31": 0, "2025-01-01": 0,
                    "2025-01-02": 4, "2025-01-03": 6, "2025-01-04": 0, "2025-01-05": 0
                }
            },
            {
                "assign_id": 2,
                "project_id": 1,
                "project_code": "PRJ-001",
                "task_id": 102,
                "task_name": "结构设计",
                "progress_rate": 30,
                "hours": {
                    "2024-12-30": 0, "2024-12-31": 0, "2025-01-01": 0,
                    "2025-01-02": 4, "2025-01-03": 2, "2025-01-04": 0, "2025-01-05": 0
                }
            }
        ],
        "summary": {
            "total_hours": 16,
            "standard_hours": 40,
            "overtime_hours": 0,
            "daily_totals": {
                "2024-12-30": 0, "2024-12-31": 0, "2025-01-01": 0,
                "2025-01-02": 8, "2025-01-03": 8, "2025-01-04": 0, "2025-01-05": 0
            }
        }
    }
    return {"code": 200, "message": "success", "data": week_data}

@router.get("/month-summary")
async def get_month_summary(
    user_id: int,
    year: int,
    month: int
):
    """获取月度工时汇总"""
    summary = {
        "user_id": user_id,
        "year": year,
        "month": month,
        "total_hours": 168,
        "standard_hours": 176,
        "overtime_hours": 12,
        "project_breakdown": [
            {"project_code": "PRJ-001", "project_name": "某客户设备", "hours": 120, "percentage": 71.4},
            {"project_code": "PRJ-002", "project_name": "电池检测设备", "hours": 48, "percentage": 28.6}
        ],
        "daily_hours": [
            {"date": "2025-01-02", "hours": 8, "overtime": 0},
            {"date": "2025-01-03", "hours": 9, "overtime": 1},
            {"date": "2025-01-06", "hours": 8, "overtime": 0}
        ],
        "status_breakdown": {
            "已通过": 140,
            "待审核": 28,
            "已驳回": 0
        }
    }
    return {"code": 200, "message": "success", "data": summary}

@router.get("/pending-approval")
async def get_pending_approval(
    approver_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200)
):
    """获取待审核工时列表（审核人视角）"""
    pending = [
        {"timesheet_id": 3, "user_name": "张工", "project_code": "PRJ-001", "task_name": "方案设计", "work_date": "2025-01-03", "hours": 6, "work_content": "方案修改", "submit_time": "2025-01-03 18:00"},
        {"timesheet_id": 4, "user_name": "李工", "project_code": "PRJ-002", "task_name": "电气设计", "work_date": "2025-01-03", "hours": 8, "work_content": "原理图设计", "submit_time": "2025-01-03 17:30"}
    ]
    return {"code": 200, "message": "success", "data": {"total": len(pending), "list": pending}}

@router.get("/statistics")
async def get_timesheet_statistics(
    project_id: Optional[int] = None,
    dept_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """工时统计分析"""
    stats = {
        "total_hours": 2400,
        "user_count": 15,
        "avg_hours_per_user": 160,
        "overtime_hours": 180,
        "overtime_rate": 7.5,
        "by_project": [
            {"project_code": "PRJ-001", "hours": 800, "user_count": 8},
            {"project_code": "PRJ-002", "hours": 600, "user_count": 6},
            {"project_code": "PRJ-003", "hours": 1000, "user_count": 10}
        ],
        "by_department": [
            {"dept_name": "机械组", "hours": 1000, "user_count": 6},
            {"dept_name": "电气组", "hours": 800, "user_count": 5},
            {"dept_name": "测试组", "hours": 600, "user_count": 4}
        ],
        "trend": [
            {"week": "2025-W01", "hours": 560, "overtime": 40},
            {"week": "2025-W02", "hours": 600, "overtime": 60},
            {"week": "2025-W03", "hours": 620, "overtime": 40},
            {"week": "2025-W04", "hours": 620, "overtime": 40}
        ]
    }
    return {"code": 200, "message": "success", "data": stats}
