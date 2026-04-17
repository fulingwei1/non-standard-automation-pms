# -*- coding: utf-8 -*-
"""
工程师智能排产与风险预警 API
"""

from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.engineer_capacity import EngineerTaskAssignment
from app.models.project import Project
from app.models.user import User
from app.services.engineer_scheduling_service import EngineerSchedulingService

router = APIRouter()


@router.post("/assignments", summary="创建工程师任务分配")
def create_assignment(
    payload: dict = Body(..., description="分配信息"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """为项目创建一条最小可用的工程师分配记录。"""
    project_id = payload.get("project_id")
    engineer_id = payload.get("engineer_id")
    allocation_pct = payload.get("allocation_pct", 100)

    if not project_id or not engineer_id:
        raise HTTPException(status_code=400, detail="project_id 和 engineer_id 为必填")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    engineer = db.query(User).filter(User.id == engineer_id, User.is_active == True).first()
    if not engineer:
        raise HTTPException(status_code=404, detail="工程师不存在")

    EngineerTaskAssignment.__table__.create(bind=db.get_bind(), checkfirst=True)

    existing = (
        db.query(EngineerTaskAssignment)
        .filter(
            EngineerTaskAssignment.project_id == project_id,
            EngineerTaskAssignment.engineer_id == engineer_id,
            EngineerTaskAssignment.status.in_(["PENDING", "IN_PROGRESS"]),
        )
        .first()
    )
    if existing:
        return {
            "id": existing.id,
            "assignment_no": existing.assignment_no,
            "project_id": existing.project_id,
            "engineer_id": existing.engineer_id,
            "engineer_name": engineer.real_name or engineer.username,
            "status": existing.status,
            "allocation_pct": allocation_pct,
            "message": "已存在有效分配",
        }

    assignment = EngineerTaskAssignment(
        assignment_no=f"ETA-{project_id}-{engineer_id}-{date.today().strftime('%Y%m%d')}",
        engineer_id=engineer_id,
        project_id=project_id,
        task_type=str(payload.get("task_type") or "AI推荐分配"),
        task_description=str(payload.get("task_description") or f"{project.project_name} 工程师推荐分配"),
        estimated_hours=float(payload.get("estimated_hours") or 8),
        planned_start_date=project.planned_start_date or date.today(),
        planned_end_date=project.planned_end_date or (date.today() + timedelta(days=7)),
        status="PENDING",
        priority=int(payload.get("priority") or 50),
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return {
        "id": assignment.id,
        "assignment_no": assignment.assignment_no,
        "project_id": assignment.project_id,
        "engineer_id": assignment.engineer_id,
        "engineer_name": engineer.real_name or engineer.username,
        "status": assignment.status,
        "allocation_pct": allocation_pct,
        "message": "分配成功",
    }


@router.get("/engineers/{engineer_id}/capacity", summary="获取工程师能力模型")
def get_engineer_capacity(
    engineer_id: int = Path(..., description="工程师 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取工程师能力模型（从历史数据提取）"""
    service = EngineerSchedulingService(db)
    capacity_data = service.extract_engineer_capacity(engineer_id)
    return capacity_data


@router.post("/engineers/{engineer_id}/capacity/update", summary="更新工程师能力模型")
def update_engineer_capacity(
    engineer_id: int = Path(..., description="工程师 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """重新计算并更新工程师能力模型"""
    service = EngineerSchedulingService(db)
    capacity = service.save_or_update_capacity(engineer_id)
    return {
        "engineer_id": capacity.engineer_id,
        "engineer_name": capacity.engineer_name,
        "avg_concurrent_projects": capacity.avg_concurrent_projects,
        "max_concurrent_projects": capacity.max_concurrent_projects,
        "avg_quality_score": capacity.avg_quality_score,
        "on_time_delivery_rate": capacity.on_time_delivery_rate,
    }


@router.get("/engineers/{engineer_id}/workload", summary="分析工程师任务量")
def analyze_workload(
    engineer_id: int = Path(..., description="工程师 ID"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    分析工程师任务量

    返回：
    - 当前任务数
    - 总工时
    - 负载状态（过载/正常/空闲）
    - 预警级别
    """

    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None

    service = EngineerSchedulingService(db)
    workload = service.analyze_engineer_workload(engineer_id, start, end)
    return workload


@router.post("/engineers/{engineer_id}/conflict-detect", summary="检测任务冲突")
def detect_conflicts(
    engineer_id: int = Path(..., description="工程师 ID"),
    task_data: dict = Body(..., description="任务信息"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    检测新任务与现有任务的冲突

    task_data:
    - project_id: 项目 ID
    - task_type: 任务类型
    - planned_start_date: 计划开始日期
    - planned_end_date: 计划结束日期
    """
    service = EngineerSchedulingService(db)
    conflicts = service.detect_task_conflicts(engineer_id, task_data)
    return {
        "engineer_id": engineer_id,
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
    }


@router.post("/warnings/generate", summary="生成工作量预警")
def generate_warnings(
    engineer_id: Optional[int] = Query(None, description="工程师 ID"),
    project_id: Optional[int] = Query(None, description="项目 ID"),
    department_id: Optional[int] = Query(None, description="部门 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """生成工作量预警"""
    service = EngineerSchedulingService(db)
    warnings = service.generate_workload_warnings(engineer_id, project_id, department_id)
    return {
        "warning_count": len(warnings),
        "warnings": [
            {
                "warning_no": w.warning_no,
                "warning_type": w.warning_type,
                "warning_level": w.warning_level,
                "title": w.title,
                "description": w.description,
                "suggestion": w.suggestion,
            }
            for w in warnings
        ],
    }


@router.get("/projects/{project_id}/scheduling-report", summary="项目排产决策报告")
def get_scheduling_report(
    project_id: int = Path(..., description="项目 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    生成项目排产决策支持报告

    包含：
    - 项目任务总览
    - 工程师负载分析
    - 冲突风险提示
    - 排产建议
    """
    service = EngineerSchedulingService(db)
    report = service.generate_scheduling_report(project_id)

    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])

    return report


@router.get("/engineers/{engineer_id}/ai-capability", summary="评估工程师 AI 能力")
def evaluate_ai_capability(
    engineer_id: int = Path(..., description="工程师 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    评估工程师的 AI 使用能力

    返回：
    - AI 技能等级（NONE/BASIC/INTERMEDIATE/ADVANCED/EXPERT）
    - 常用 AI 工具
    - 使用频率
    - 效率提升系数
    - AI 代码采纳率
    - 每周节省工时
    - AI 学习能力评分
    """
    service = EngineerSchedulingService(db)
    ai_capability = service.evaluate_ai_capability(engineer_id)
    return ai_capability


@router.post("/engineers/{engineer_id}/ai-capability/update", summary="更新 AI 能力评估")
def update_ai_capability(
    engineer_id: int = Path(..., description="工程师 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """重新评估并更新工程师 AI 能力"""
    service = EngineerSchedulingService(db)
    capacity = service.save_ai_capability(engineer_id)
    return {
        "engineer_id": capacity.engineer_id,
        "ai_skill_level": capacity.ai_skill_level,
        "ai_tools": capacity.ai_tools,
        "ai_usage_frequency": capacity.ai_usage_frequency,
        "ai_efficiency_boost": capacity.ai_efficiency_boost,
        "ai_saved_hours": capacity.ai_saved_hours,
    }


@router.get("/engineers/{engineer_id}/core-capabilities", summary="评估工程师核心能力")
def evaluate_core_capabilities(
    engineer_id: int = Path(..., description="工程师 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    评估工程师的核心能力

    返回：
    - 多项目并行能力（同时负责项目数/效率/切换成本）
    - 标准化/模块化能力（复用率/模块数量/文档质量）
    """
    service = EngineerSchedulingService(db)
    capabilities = service.evaluate_core_capabilities(engineer_id)
    return capabilities


@router.post("/engineers/{engineer_id}/core-capabilities/update", summary="更新核心能力评估")
def update_core_capabilities(
    engineer_id: int = Path(..., description="工程师 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """重新评估并更新工程师核心能力"""
    service = EngineerSchedulingService(db)
    capacity = service.save_core_capabilities(engineer_id)
    return {
        "engineer_id": capacity.engineer_id,
        "multi_project_capacity": capacity.multi_project_capacity,
        "multi_project_efficiency": capacity.multi_project_efficiency,
        "standardization_score": capacity.standardization_score,
        "modularity_score": capacity.modularity_score,
        "reuse_rate": capacity.reuse_rate,
    }
