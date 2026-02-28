# -*- coding: utf-8 -*-
"""
现场调试移动端视图 API

提供现场调试任务管理、签到、进度更新、问题报告等功能
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import sqlite3
import os

router = APIRouter()

# ==================== 数据库路径 ====================
DB_PATH = os.path.join(os.path.dirname(__file__), "../../../../data/app.db")


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_tables():
    """Lazy init 创建表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 现场调试任务表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS field_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_no TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            project_name TEXT NOT NULL,
            address TEXT NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'completed', 'cancelled')),
            assigned_to TEXT,
            scheduled_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            progress INTEGER DEFAULT 0,
            progress_note TEXT,
            completion_signature TEXT,
            completion_time TIMESTAMP
        )
    """)
    
    # 签到记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS field_checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            checkin_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES field_tasks(id)
        )
    """)
    
    # 问题记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS field_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            photo_url TEXT,
            severity TEXT DEFAULT 'medium' CHECK(severity IN ('low', 'medium', 'high', 'critical')),
            status TEXT DEFAULT 'open' CHECK(status IN ('open', 'in_progress', 'resolved', 'closed')),
            reported_by TEXT,
            reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            resolution_note TEXT,
            FOREIGN KEY (task_id) REFERENCES field_tasks(id)
        )
    """)
    
    conn.commit()
    conn.close()


# 初始化表（模块加载时）
init_tables()


# ==================== Pydantic Models ====================

class FieldTask(BaseModel):
    id: int
    task_no: str
    customer_name: str
    project_name: str
    address: str
    status: str
    assigned_to: Optional[str] = None
    scheduled_date: Optional[str] = None
    progress: int = 0
    progress_note: Optional[str] = None
    created_at: str
    updated_at: str


class FieldTaskDetail(FieldTask):
    completion_signature: Optional[str] = None
    completion_time: Optional[str] = None
    checkin_count: int = 0
    issue_count: int = 0


class CheckinRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    user_id: Optional[str] = None


class ProgressRequest(BaseModel):
    progress: int = Field(..., ge=0, le=100)
    note: Optional[str] = None


class IssueRequest(BaseModel):
    description: str
    photo_url: Optional[str] = None
    severity: str = "medium"
    reported_by: Optional[str] = None


class CompleteRequest(BaseModel):
    signature: str
    completion_note: Optional[str] = None


class DashboardStats(BaseModel):
    today_tasks: int
    in_progress: int
    completed: int
    issue_count: int


# ==================== API Endpoints ====================

@router.get("/field/tasks", response_model=List[FieldTask], tags=["field-commissioning"])
async def get_field_tasks(
    status: Optional[str] = Query(None, description="任务状态筛选"),
    assigned_to: Optional[str] = Query(None, description="负责人筛选")
):
    """获取当前用户的现场调试任务列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM field_tasks WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    if assigned_to:
        query += " AND assigned_to = ?"
        params.append(assigned_to)
    
    query += " ORDER BY scheduled_date DESC, created_at DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    tasks = []
    for row in rows:
        tasks.append(FieldTask(
            id=row["id"],
            task_no=row["task_no"],
            customer_name=row["customer_name"],
            project_name=row["project_name"],
            address=row["address"],
            status=row["status"],
            assigned_to=row["assigned_to"],
            scheduled_date=row["scheduled_date"],
            progress=row["progress"],
            progress_note=row["progress_note"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        ))
    
    return tasks


@router.get("/field/tasks/{task_id}", response_model=FieldTaskDetail, tags=["field-commissioning"])
async def get_field_task_detail(task_id: int):
    """获取任务详情"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取任务基本信息
    cursor.execute("SELECT * FROM field_tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 获取签到次数
    cursor.execute("SELECT COUNT(*) as count FROM field_checkins WHERE task_id = ?", (task_id,))
    checkin_count = cursor.fetchone()["count"]
    
    # 获取问题数量
    cursor.execute("SELECT COUNT(*) as count FROM field_issues WHERE task_id = ?", (task_id,))
    issue_count = cursor.fetchone()["count"]
    
    conn.close()
    
    return FieldTaskDetail(
        id=row["id"],
        task_no=row["task_no"],
        customer_name=row["customer_name"],
        project_name=row["project_name"],
        address=row["address"],
        status=row["status"],
        assigned_to=row["assigned_to"],
        scheduled_date=row["scheduled_date"],
        progress=row["progress"],
        progress_note=row["progress_note"],
        completion_signature=row["completion_signature"],
        completion_time=row["completion_time"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        checkin_count=checkin_count,
        issue_count=issue_count
    )


@router.post("/field/tasks/{task_id}/checkin", tags=["field-commissioning"])
async def checkin(task_id: int, request: CheckinRequest):
    """现场签到（记录 GPS 坐标、时间）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 验证任务存在
    cursor.execute("SELECT id, status FROM field_tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    
    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 记录签到
    user_id = request.user_id or "anonymous"
    cursor.execute("""
        INSERT INTO field_checkins (task_id, user_id, latitude, longitude)
        VALUES (?, ?, ?, ?)
    """, (task_id, user_id, request.latitude, request.longitude))
    
    # 如果任务是 pending 状态，自动转为 in_progress
    if task["status"] == "pending":
        cursor.execute("""
            UPDATE field_tasks 
            SET status = 'in_progress', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (task_id,))
    
    conn.commit()
    conn.close()
    
    return {"message": "签到成功", "checkin_time": datetime.now().isoformat()}


@router.post("/field/tasks/{task_id}/progress", tags=["field-commissioning"])
async def update_progress(task_id: int, request: ProgressRequest):
    """更新进度（百分比 + 备注）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 验证任务存在
    cursor.execute("SELECT id FROM field_tasks WHERE id = ?", (task_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 更新进度
    cursor.execute("""
        UPDATE field_tasks 
        SET progress = ?, progress_note = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (request.progress, request.note, task_id))
    
    conn.commit()
    conn.close()
    
    return {"message": "进度更新成功", "progress": request.progress}


@router.post("/field/tasks/{task_id}/issue", tags=["field-commissioning"])
async def report_issue(task_id: int, request: IssueRequest):
    """报告问题（描述、照片 URL、严重程度）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 验证任务存在
    cursor.execute("SELECT id FROM field_tasks WHERE id = ?", (task_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 创建问题记录
    reported_by = request.reported_by or "anonymous"
    cursor.execute("""
        INSERT INTO field_issues (task_id, description, photo_url, severity, reported_by)
        VALUES (?, ?, ?, ?, ?)
    """, (task_id, request.description, request.photo_url, request.severity, reported_by))
    
    issue_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"message": "问题报告成功", "issue_id": issue_id}


@router.post("/field/tasks/{task_id}/complete", tags=["field-commissioning"])
async def complete_task(task_id: int, request: CompleteRequest):
    """完成调试（签名确认）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 验证任务存在
    cursor.execute("SELECT id FROM field_tasks WHERE id = ?", (task_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 更新任务状态为 completed
    cursor.execute("""
        UPDATE field_tasks 
        SET status = 'completed', 
            progress = 100,
            completion_signature = ?,
            completion_time = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (request.signature, task_id))
    
    conn.commit()
    conn.close()
    
    return {"message": "任务完成确认成功", "completion_time": datetime.now().isoformat()}


@router.get("/field/dashboard", response_model=DashboardStats, tags=["field-commissioning"])
async def get_dashboard():
    """调试概览（今日任务数、进行中、已完成、问题数）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 今日任务数
    cursor.execute("""
        SELECT COUNT(*) as count FROM field_tasks 
        WHERE date(scheduled_date) = date(?)
    """, (today,))
    today_tasks = cursor.fetchone()["count"]
    
    # 进行中任务数
    cursor.execute("""
        SELECT COUNT(*) as count FROM field_tasks 
        WHERE status = 'in_progress'
    """)
    in_progress = cursor.fetchone()["count"]
    
    # 已完成任务数
    cursor.execute("""
        SELECT COUNT(*) as count FROM field_tasks 
        WHERE status = 'completed'
    """)
    completed = cursor.fetchone()["count"]
    
    # 未解决问题数
    cursor.execute("""
        SELECT COUNT(*) as count FROM field_issues 
        WHERE status IN ('open', 'in_progress')
    """)
    issue_count = cursor.fetchone()["count"]
    
    conn.close()
    
    return DashboardStats(
        today_tasks=today_tasks,
        in_progress=in_progress,
        completed=completed,
        issue_count=issue_count
    )
