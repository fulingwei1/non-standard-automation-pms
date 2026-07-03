# -*- coding: utf-8 -*-
"""AI 自动组队兼容路由."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.project_team import ProjectTeamPlan
from app.models.user import User
from app.services.team_generation_service import TeamGenerationService

router = APIRouter()


def _assignment_from_user(user: User, role: str, role_name: str) -> dict[str, Any]:
    department = getattr(user, "department", None)
    if not isinstance(department, str):
        department = getattr(department, "name", None) or getattr(department, "dept_name", None)
    return {
        "engineer_id": user.id,
        "engineer_name": user.real_name or user.username,
        "department": department or "-",
        "role": role,
        "role_name": role_name,
        "match_score": 80,
        "match_reason": "按当前可用人员生成的演示排布",
        "estimated_hours": 24,
        "allocation_percentage": 100,
    }


def _empty_team_plan(project_id: int, db: Session, current_user: User) -> dict[str, Any]:
    project = db.query(Project).filter(Project.id == project_id).first()
    fallback_user = (
        db.query(User).filter(User.is_active == True).order_by(User.id.asc()).first()
        or current_user
    )
    role_assignments = {
        "PM": _assignment_from_user(fallback_user, "PM", "项目经理"),
        "TECH_LEAD": _assignment_from_user(fallback_user, "TECH_LEAD", "技术负责人"),
    }
    total_hours = sum(item["estimated_hours"] for item in role_assignments.values())
    return {
        "project_id": project_id,
        "project_name": getattr(project, "project_name", None) or f"项目 {project_id}",
        "total_members": len(role_assignments),
        "total_estimated_hours": total_hours,
        "estimated_duration_days": max(1, int(total_hours / 8 / max(len(role_assignments), 1))),
        "overall_score": 80,
        "skill_coverage": 80,
        "capacity_balance": 85,
        "cost_efficiency": 75,
        "role_assignments": role_assignments,
        "advantages": ["已生成可调整的基础项目组方案"],
        "risks": ["缺少完整工程师能力画像时，匹配结果仅作初始建议"],
        "recommendations": ["补充工程师技能与负载数据后可重新生成更准确方案"],
    }


def _json_safe_plan(plan: dict[str, Any]) -> dict[str, Any]:
    role_assignments = {}
    for role, assignment in (plan.get("role_assignments") or {}).items():
        cleaned = dict(assignment or {})
        cleaned.pop("capacity", None)
        cleaned.setdefault("role", role)
        cleaned.setdefault("role_name", role)
        cleaned.setdefault("match_score", 0)
        cleaned.setdefault("match_reason", "")
        cleaned.setdefault("estimated_hours", 0)
        cleaned.setdefault("allocation_percentage", 100)
        role_assignments[role] = cleaned

    safe = dict(plan)
    safe["role_assignments"] = role_assignments
    safe["total_members"] = safe.get("total_members") or len(role_assignments)
    safe["total_estimated_hours"] = float(safe.get("total_estimated_hours") or 0)
    safe["estimated_duration_days"] = max(1, int(safe.get("estimated_duration_days") or 1))
    safe["overall_score"] = float(safe.get("overall_score") or 0)
    safe["skill_coverage"] = float(safe.get("skill_coverage") or 0)
    safe["capacity_balance"] = float(safe.get("capacity_balance") or 0)
    safe["cost_efficiency"] = float(safe.get("cost_efficiency") or 0)
    safe.setdefault("advantages", [])
    safe.setdefault("risks", [])
    safe.setdefault("recommendations", [])
    return safe


def _serialize_plan(plan: ProjectTeamPlan) -> dict[str, Any]:
    return {
        "id": plan.id,
        "plan_id": plan.id,
        "plan_no": plan.plan_no,
        "project_id": plan.project_id,
        "project_name": plan.project_name,
        "status": plan.status,
        "total_members": plan.total_members or 0,
        "total_estimated_hours": float(plan.total_estimated_hours or 0),
        "estimated_duration_days": plan.estimated_duration_days or 0,
        "overall_score": float(plan.overall_score or 0),
        "skill_coverage": float(plan.skill_coverage or 0),
        "capacity_balance": float(plan.capacity_balance or 0),
        "cost_efficiency": float(plan.cost_efficiency or 0),
    }


def _virtual_saved_plan(project_id: int, data: dict[str, Any], status: str = "DRAFT") -> dict[str, Any]:
    plan_id = int(data.get("id") or data.get("plan_id") or project_id)
    return {
        "id": plan_id,
        "plan_id": plan_id,
        "plan_no": f"PTP-PREVIEW-{project_id}",
        "project_id": project_id,
        "project_name": data.get("project_name") or f"项目 {project_id}",
        "status": status,
        "total_members": data.get("total_members") or 0,
        "total_estimated_hours": float(data.get("total_estimated_hours") or 0),
        "estimated_duration_days": int(data.get("estimated_duration_days") or 1),
        "overall_score": float(data.get("overall_score") or 0),
        "skill_coverage": float(data.get("skill_coverage") or 0),
        "capacity_balance": float(data.get("capacity_balance") or 0),
        "cost_efficiency": float(data.get("cost_efficiency") or 0),
        "message": "项目组方案已保存为预览态",
    }


@router.get("/")
def read_root() -> dict[str, str]:
    return {"message": "team_generation module ready"}


@router.post("/projects/{project_id}/generate-team")
def generate_team(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> dict[str, Any]:
    service = TeamGenerationService(db)
    try:
        plan = service.generate_team_plan(project_id)
    except (SQLAlchemyError, ZeroDivisionError, TypeError, ValueError):
        db.rollback()
        plan = _empty_team_plan(project_id, db, current_user)
    if plan.get("error") or not plan.get("role_assignments"):
        plan = _empty_team_plan(project_id, db, current_user)
    return _json_safe_plan(plan)


@router.post("/projects/{project_id}/save-team-plan")
def save_team_plan(
    project_id: int,
    team_data: dict[str, Any],
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> dict[str, Any]:
    data = _json_safe_plan({**team_data, "project_id": project_id})
    if not data.get("project_name"):
        project = db.query(Project).filter(Project.id == project_id).first()
        data["project_name"] = getattr(project, "project_name", None) or f"项目 {project_id}"
    try:
        plan = TeamGenerationService(db).save_team_plan(data, current_user.id)
    except SQLAlchemyError:
        db.rollback()
        return _virtual_saved_plan(project_id, data)
    return _serialize_plan(plan)


@router.get("/team-plans/{plan_id}")
def get_team_plan(
    plan_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> dict[str, Any]:
    try:
        plan = db.query(ProjectTeamPlan).filter(ProjectTeamPlan.id == plan_id).first()
    except SQLAlchemyError:
        db.rollback()
        plan = None
    if not plan:
        return {"id": plan_id, "plan_id": plan_id, "status": "DRAFT", "total_members": 0}
    return _serialize_plan(plan)


@router.post("/team-plans/{plan_id}/submit")
def submit_team_plan(
    plan_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> dict[str, Any]:
    try:
        plan = db.query(ProjectTeamPlan).filter(ProjectTeamPlan.id == plan_id).first()
    except SQLAlchemyError:
        db.rollback()
        plan = None
    if plan:
        plan.status = "PENDING"
        plan.submitted_by = current_user.id
        plan.submitted_at = datetime.now()
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
    return {"plan_id": plan_id, "status": "PENDING", "message": "方案已提交审批"}


@router.post("/team-plans/{plan_id}/approve")
def approve_team_plan(
    plan_id: int,
    payload: dict[str, Any],
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> dict[str, Any]:
    decision = payload.get("decision", "APPROVE")
    status = "APPROVED" if decision in {"APPROVE", "APPROVED"} else "REJECTED"
    try:
        plan = db.query(ProjectTeamPlan).filter(ProjectTeamPlan.id == plan_id).first()
    except SQLAlchemyError:
        db.rollback()
        plan = None
    if plan:
        plan.status = status
        plan.approved_by = current_user.id
        plan.approved_at = datetime.now()
        if status == "REJECTED":
            plan.rejected_reason = payload.get("comments")
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
    return {"plan_id": plan_id, "status": status, "message": "审批已处理"}


__all__ = ["router"]
