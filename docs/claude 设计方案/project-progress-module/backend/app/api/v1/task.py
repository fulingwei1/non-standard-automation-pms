"""
任务管理 API 接口
"""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import WbsTask, TaskDependency, Project
from app.services.progress_service import ProgressService
from app.services.cpm_service import CpmService

router = APIRouter()


# ============== Pydantic 模型 ==============

class TaskCreate(BaseModel):
    """创建任务请求"""
    project_id: int
    wbs_code: str
    task_name: str
    parent_id: Optional[int] = None
    level: int = 2
    phase: str
    task_type: str
    plan_start_date: date
    plan_end_date: date
    plan_duration: int = 1
    plan_manhours: float = 0
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    owner_dept_id: Optional[int] = None
    owner_dept_name: Optional[str] = None
    is_milestone: int = 0
    deliverable: Optional[str] = None
    priority: int = 3
    weight: float = 1.0


class TaskUpdate(BaseModel):
    """更新任务请求"""
    task_name: Optional[str] = None
    plan_start_date: Optional[date] = None
    plan_end_date: Optional[date] = None
    plan_duration: Optional[int] = None
    plan_manhours: Optional[float] = None
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    deliverable: Optional[str] = None
    weight: Optional[float] = None


class ProgressUpdate(BaseModel):
    """更新进度请求"""
    progress_rate: float = Field(..., ge=0, le=100)
    remark: Optional[str] = None


class BatchProgressUpdate(BaseModel):
    """批量更新进度请求"""
    updates: List[dict]  # [{"task_id": 1, "progress_rate": 50}, ...]


class TaskDateUpdate(BaseModel):
    """更新任务日期（甘特图拖拽）"""
    plan_start_date: date
    plan_end_date: date


class DependencyCreate(BaseModel):
    """创建依赖关系"""
    task_id: int  # 后置任务
    predecessor_id: int  # 前置任务
    depend_type: str = "FS"
    lag_days: int = 0


class TaskStatusUpdate(BaseModel):
    """更新任务状态"""
    status: str
    block_reason: Optional[str] = None
    block_type: Optional[str] = None


# ============== API 接口 ==============

@router.get("/{project_id}/wbs")
async def get_wbs_tree(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目WBS树结构
    """
    tasks = db.query(WbsTask).filter(
        WbsTask.project_id == project_id,
        WbsTask.is_deleted == 0
    ).order_by(WbsTask.level, WbsTask.sort_order).all()
    
    if not tasks:
        return {"code": 200, "data": {"tree": []}}
    
    # 构建树结构
    task_dict = {}
    for task in tasks:
        task_dict[task.task_id] = {
            "task_id": task.task_id,
            "wbs_code": task.wbs_code,
            "task_name": task.task_name,
            "level": task.level,
            "phase": task.phase,
            "plan_start_date": str(task.plan_start_date),
            "plan_end_date": str(task.plan_end_date),
            "plan_duration": task.plan_duration,
            "plan_manhours": float(task.plan_manhours or 0),
            "actual_manhours": float(task.actual_manhours or 0),
            "progress_rate": float(task.progress_rate or 0),
            "owner_id": task.owner_id,
            "owner_name": task.owner_name,
            "status": task.status,
            "is_critical": task.is_critical == 1,
            "is_milestone": task.is_milestone == 1,
            "float_days": task.float_days,
            "priority": task.priority,
            "children": []
        }
    
    # 构建父子关系
    tree = []
    for task in tasks:
        if task.parent_id and task.parent_id in task_dict:
            task_dict[task.parent_id]["children"].append(task_dict[task.task_id])
        elif not task.parent_id or task.parent_id not in task_dict:
            tree.append(task_dict[task.task_id])
    
    return {"code": 200, "data": {"tree": tree}}


@router.post("")
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user_id: int = 1,  # 实际从JWT获取
    current_user_name: str = "系统"
):
    """
    创建任务
    """
    # 验证项目存在
    project = db.query(Project).filter(
        Project.project_id == task_data.project_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 创建任务
    task = WbsTask(
        project_id=task_data.project_id,
        wbs_code=task_data.wbs_code,
        task_name=task_data.task_name,
        parent_id=task_data.parent_id,
        level=task_data.level,
        phase=task_data.phase,
        task_type=task_data.task_type,
        plan_start_date=task_data.plan_start_date,
        plan_end_date=task_data.plan_end_date,
        plan_duration=task_data.plan_duration,
        plan_manhours=task_data.plan_manhours,
        owner_id=task_data.owner_id,
        owner_name=task_data.owner_name,
        owner_dept_id=task_data.owner_dept_id,
        owner_dept_name=task_data.owner_dept_name,
        is_milestone=task_data.is_milestone,
        deliverable=task_data.deliverable,
        priority=task_data.priority,
        weight=task_data.weight,
        created_by=current_user_id
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return {
        "code": 200,
        "message": "创建成功",
        "data": {"task_id": task.task_id}
    }


@router.put("/{task_id}")
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)
):
    """
    更新任务
    """
    task = db.query(WbsTask).filter(
        WbsTask.task_id == task_id,
        WbsTask.is_deleted == 0
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 更新字段
    update_data = task_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(task, key, value)
    
    db.commit()
    
    return {"code": 200, "message": "更新成功"}


@router.put("/{task_id}/progress")
async def update_task_progress(
    task_id: int,
    progress_data: ProgressUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = 1,
    current_user_name: str = "系统"
):
    """
    更新任务进度
    """
    service = ProgressService(db)
    
    try:
        result = service.update_task_progress(
            task_id=task_id,
            new_progress=progress_data.progress_rate,
            operator_id=current_user_id,
            operator_name=current_user_name,
            remark=progress_data.remark
        )
        return {"code": 200, "message": "更新成功", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/batch-progress")
async def batch_update_progress(
    batch_data: BatchProgressUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = 1,
    current_user_name: str = "系统"
):
    """
    批量更新进度
    """
    service = ProgressService(db)
    results = service.batch_update_progress(
        updates=batch_data.updates,
        operator_id=current_user_id,
        operator_name=current_user_name
    )
    return {"code": 200, "data": results}


@router.put("/{task_id}/status")
async def update_task_status(
    task_id: int,
    status_data: TaskStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    更新任务状态
    """
    task = db.query(WbsTask).filter(
        WbsTask.task_id == task_id,
        WbsTask.is_deleted == 0
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    valid_statuses = ['未开始', '进行中', '已完成', '阻塞', '暂停', '取消']
    if status_data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"无效状态，有效值: {valid_statuses}")
    
    task.status = status_data.status
    if status_data.status == '阻塞':
        task.block_reason = status_data.block_reason
        task.block_type = status_data.block_type
    else:
        task.block_reason = None
        task.block_type = None
    
    # 如果设为已完成，更新进度为100%
    if status_data.status == '已完成':
        task.progress_rate = 100
        if not task.actual_end_date:
            task.actual_end_date = date.today()
    
    db.commit()
    
    return {"code": 200, "message": "状态更新成功"}


@router.put("/{task_id}/dates")
async def update_task_dates(
    task_id: int,
    date_data: TaskDateUpdate,
    db: Session = Depends(get_db)
):
    """
    更新任务日期（甘特图拖拽）
    """
    task = db.query(WbsTask).filter(
        WbsTask.task_id == task_id,
        WbsTask.is_deleted == 0
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 计算工期
    duration = (date_data.plan_end_date - date_data.plan_start_date).days + 1
    
    task.plan_start_date = date_data.plan_start_date
    task.plan_end_date = date_data.plan_end_date
    task.plan_duration = duration
    
    db.commit()
    
    return {"code": 200, "message": "日期更新成功"}


@router.get("/{project_id}/gantt")
async def get_gantt_data(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取甘特图数据
    """
    # 获取任务
    tasks = db.query(WbsTask).filter(
        WbsTask.project_id == project_id,
        WbsTask.is_deleted == 0
    ).order_by(WbsTask.level, WbsTask.sort_order).all()
    
    # 获取依赖关系
    dependencies = db.query(TaskDependency).filter(
        TaskDependency.project_id == project_id
    ).all()
    
    task_list = []
    for task in tasks:
        task_list.append({
            "id": task.task_id,
            "wbs_code": task.wbs_code,
            "label": task.task_name,
            "start": str(task.plan_start_date),
            "end": str(task.plan_end_date),
            "duration": task.plan_duration,
            "progress": float(task.progress_rate or 0),
            "type": "milestone" if task.is_milestone else "task",
            "style": {
                "base": {
                    "fill": "#FF0000" if task.is_critical else "#1890ff",
                    "stroke": "#FF0000" if task.is_critical else "#1890ff"
                }
            },
            "parent_id": task.parent_id,
            "level": task.level,
            "owner": task.owner_name,
            "status": task.status,
            "is_critical": task.is_critical == 1
        })
    
    dep_list = []
    for dep in dependencies:
        dep_list.append({
            "id": dep.depend_id,
            "from": dep.predecessor_id,
            "to": dep.task_id,
            "type": dep.depend_type,
            "lag": dep.lag_days
        })
    
    return {
        "code": 200,
        "data": {
            "tasks": task_list,
            "dependencies": dep_list
        }
    }


@router.post("/dependencies")
async def create_dependency(
    dep_data: DependencyCreate,
    db: Session = Depends(get_db)
):
    """
    创建任务依赖关系
    """
    # 获取任务所属项目
    task = db.query(WbsTask).filter(WbsTask.task_id == dep_data.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    predecessor = db.query(WbsTask).filter(WbsTask.task_id == dep_data.predecessor_id).first()
    if not predecessor:
        raise HTTPException(status_code=404, detail="前置任务不存在")
    
    if task.project_id != predecessor.project_id:
        raise HTTPException(status_code=400, detail="任务必须属于同一项目")
    
    # 检查环路
    cpm_service = CpmService(db)
    if cpm_service.check_dependency_cycle(
        task.project_id, 
        dep_data.task_id, 
        dep_data.predecessor_id
    ):
        raise HTTPException(status_code=400, detail="添加此依赖会产生循环依赖")
    
    # 检查是否已存在
    existing = db.query(TaskDependency).filter(
        TaskDependency.task_id == dep_data.task_id,
        TaskDependency.predecessor_id == dep_data.predecessor_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="依赖关系已存在")
    
    # 创建依赖
    dependency = TaskDependency(
        task_id=dep_data.task_id,
        predecessor_id=dep_data.predecessor_id,
        project_id=task.project_id,
        depend_type=dep_data.depend_type,
        lag_days=dep_data.lag_days
    )
    
    db.add(dependency)
    db.commit()
    db.refresh(dependency)
    
    return {
        "code": 200,
        "message": "依赖关系创建成功",
        "data": {"depend_id": dependency.depend_id}
    }


@router.delete("/dependencies/{depend_id}")
async def delete_dependency(
    depend_id: int,
    db: Session = Depends(get_db)
):
    """
    删除任务依赖关系
    """
    dependency = db.query(TaskDependency).filter(
        TaskDependency.depend_id == depend_id
    ).first()
    
    if not dependency:
        raise HTTPException(status_code=404, detail="依赖关系不存在")
    
    db.delete(dependency)
    db.commit()
    
    return {"code": 200, "message": "删除成功"}


@router.post("/{project_id}/calculate-cpm")
async def calculate_critical_path(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    计算关键路径
    """
    cpm_service = CpmService(db)
    
    try:
        result = cpm_service.calculate_critical_path(project_id)
        return {"code": 200, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my-tasks")
async def get_my_tasks(
    status: Optional[str] = None,
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user_id: int = 1
):
    """
    获取我的任务列表
    """
    from app.models.models import TaskAssignment
    
    query = db.query(TaskAssignment).filter(
        TaskAssignment.user_id == current_user_id
    )
    
    if status:
        query = query.filter(TaskAssignment.status == status)
    if project_id:
        query = query.filter(TaskAssignment.project_id == project_id)
    
    assignments = query.order_by(
        TaskAssignment.priority,
        TaskAssignment.plan_end_date
    ).all()
    
    result = []
    for assign in assignments:
        task = db.query(WbsTask).filter(WbsTask.task_id == assign.task_id).first()
        project = db.query(Project).filter(Project.project_id == assign.project_id).first()
        
        if task and project:
            result.append({
                "assign_id": assign.assign_id,
                "task_id": assign.task_id,
                "task_name": task.task_name,
                "project_id": assign.project_id,
                "project_name": project.project_name,
                "project_code": project.project_code,
                "plan_start_date": str(assign.plan_start_date),
                "plan_end_date": str(assign.plan_end_date),
                "plan_manhours": float(assign.plan_manhours or 0),
                "actual_manhours": float(assign.actual_manhours or 0),
                "progress_rate": float(assign.progress_rate or 0),
                "status": assign.status,
                "priority": assign.priority,
                "is_overdue": assign.plan_end_date < date.today() and assign.status != '已完成'
            })
    
    return {"code": 200, "data": {"list": result}}


@router.get("/my-tasks/today")
async def get_today_tasks(
    db: Session = Depends(get_db),
    current_user_id: int = 1
):
    """
    获取今日任务
    """
    from app.models.models import TaskAssignment
    
    today = date.today()
    
    assignments = db.query(TaskAssignment).filter(
        TaskAssignment.user_id == current_user_id,
        TaskAssignment.status.in_(['未开始', '进行中']),
        TaskAssignment.plan_start_date <= today,
        TaskAssignment.plan_end_date >= today
    ).order_by(TaskAssignment.priority).all()
    
    result = []
    for assign in assignments:
        task = db.query(WbsTask).filter(WbsTask.task_id == assign.task_id).first()
        project = db.query(Project).filter(Project.project_id == assign.project_id).first()
        
        if task and project:
            result.append({
                "assign_id": assign.assign_id,
                "task_id": assign.task_id,
                "task_name": task.task_name,
                "project_code": project.project_code,
                "plan_manhours": float(assign.plan_manhours or 0),
                "actual_manhours": float(assign.actual_manhours or 0),
                "progress_rate": float(assign.progress_rate or 0),
                "priority": assign.priority
            })
    
    return {"code": 200, "data": {"list": result, "count": len(result)}}
