# -*- coding: utf-8 -*-
"""Compatibility routes for project requirement extraction."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.project_requirements import EngineerRecommendation, ProjectRequirement
from app.models.user import User
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


def _loads_list(value: Any) -> list[Any]:
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return []
    return parsed if isinstance(parsed, list) else []


def _serialize_requirement(row: ProjectRequirement) -> dict[str, Any]:
    req_type = (row.requirement_type or "production").lower()
    return {
        "id": row.id,
        "requirement_id": row.id,
        "requirement_no": row.requirement_no,
        "requirement_type": req_type,
        "requirement_text": row.requirement_text,
        "production_complexity": row.production_complexity,
        "required_skills": _loads_list(row.required_skills),
        "estimated_hours": row.estimated_hours or 0,
        "required_certifications": _loads_list(row.required_certifications),
        "service_type": row.service_type,
        "service_location": row.service_location,
        "service_duration": row.service_duration,
        "required_experience_years": row.required_experience_years or 0,
        "customer_facing": bool(row.customer_facing),
        "language_requirements": _loads_list(row.language_requirements),
        "priority": row.priority or 50,
        "deadline": row.deadline.isoformat() if row.deadline else None,
        "status": row.status or "PENDING",
    }


def _serialize_recommendation(row: EngineerRecommendation) -> dict[str, Any]:
    return {
        "id": row.id,
        "recommendation_id": row.id,
        "requirement_id": row.requirement_id,
        "engineer_id": row.engineer_id,
        "engineer_name": (
            row.engineer_name
            or (row.engineer.display_name if row.engineer else None)
            or f"工程师#{row.engineer_id}"
        ),
        "overall_match_score": row.overall_match_score or 0,
        "skill_match_score": row.skill_match_score or 0,
        "capacity_match_score": row.capacity_match_score or 0,
        "availability_score": row.availability_score or 0,
        "location_match_score": row.location_match_score or 0,
        "matched_skills": _loads_list(row.matched_skills),
        "missing_skills": _loads_list(row.missing_skills),
        "advantages": _loads_list(row.advantages),
        "risks": _loads_list(row.risks),
        "recommendation_reason": row.recommendation_reason,
        "rank": row.rank or 999,
        "status": row.status or "PENDING",
    }


@router.get("/")
def read_root() -> dict[str, str]:
    return {"message": "requirement_extraction compatibility routes"}


@router.get("/projects/{project_id}/requirements")
def get_project_requirements(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> dict[str, Any]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    check_project_access_or_raise(db, current_user, project_id)

    grouped: dict[str, list[dict[str, Any]]] = {
        "production": [],
        "service": [],
        "design": [],
        "debug": [],
    }
    rows = (
        db.query(ProjectRequirement)
        .filter(ProjectRequirement.project_id == project_id)
        .order_by(ProjectRequirement.priority.desc(), ProjectRequirement.id)
        .all()
    )
    for row in rows:
        item = _serialize_requirement(row)
        grouped.setdefault(item["requirement_type"], []).append(item)

    return {
        "project_id": project_id,
        "project_name": project.project_name,
        "total_requirements": len(rows),
        "requirements": grouped,
    }


@router.post("/requirements/{requirement_id}/recommend")
def recommend_for_requirement(
    requirement_id: int,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> dict[str, Any]:
    requirement = db.query(ProjectRequirement).filter(ProjectRequirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="项目需求不存在")
    check_project_access_or_raise(db, current_user, requirement.project_id)

    rows = (
        db.query(EngineerRecommendation)
        .filter(EngineerRecommendation.requirement_id == requirement_id)
        .order_by(EngineerRecommendation.rank, EngineerRecommendation.id)
        .limit(limit)
        .all()
    )
    return {
        "requirement_id": requirement_id,
        "recommendations": [_serialize_recommendation(row) for row in rows],
    }


@router.post("/projects/{project_id}/auto-recommend")
def auto_recommend_for_project(
    project_id: int,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> dict[str, Any]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    check_project_access_or_raise(db, current_user, project_id)

    requirements = (
        db.query(ProjectRequirement)
        .filter(ProjectRequirement.project_id == project_id)
        .order_by(ProjectRequirement.priority.desc(), ProjectRequirement.id)
        .all()
    )
    grouped: dict[str, list[dict[str, Any]]] = {
        "production": [],
        "service": [],
        "design": [],
        "debug": [],
    }
    for requirement in requirements:
        req_type = (requirement.requirement_type or "production").lower()
        rows = (
            db.query(EngineerRecommendation)
            .filter(EngineerRecommendation.requirement_id == requirement.id)
            .order_by(EngineerRecommendation.rank, EngineerRecommendation.id)
            .limit(limit)
            .all()
        )
        grouped.setdefault(req_type, []).extend(_serialize_recommendation(row) for row in rows)

    return {
        "project_id": project_id,
        "recommendations": grouped,
    }


__all__ = ["router"]
