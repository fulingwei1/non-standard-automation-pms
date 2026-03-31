# -*- coding: utf-8 -*-
"""
项目-变更单联动集成 API

端点：
  POST   /project-change-impacts/assess          — ECN 审批时：影响评估
  POST   /project-change-impacts/execute-linkage  — ECN 执行后：联动更新
  GET    /project-change-impacts/{impact_id}       — 查看单条记录
  GET    /project-change-impacts/by-ecn/{ecn_id}   — 查看 ECN 的所有影响
  GET    /project-change-impacts/by-project/{project_id}/summary  — 项目变更汇总
  GET    /project-change-impacts/by-project/{project_id}/delays   — 项目延期历史
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.project_change_impact import (
    AssessImpactRequest,
    ExecuteLinkageRequest,
    ImpactAssessmentReport,
    ProjectChangeImpactListResponse,
    ProjectChangeImpactResponse,
    ProjectChangeSummary,
)
from app.services import project_change_impact_service as service

router = APIRouter()


# ─────────────────────────────────────────────────
#  1. 影响评估（ECN 审批阶段）
# ─────────────────────────────────────────────────


@router.post(
    "/project-change-impacts/assess",
    response_model=ImpactAssessmentReport,
    status_code=status.HTTP_201_CREATED,
    summary="ECN影响评估",
    description="ECN审批时调用，评估变更对关联项目的进度/成本/风险影响",
)
def assess_change_impact(
    *,
    db: Session = Depends(deps.get_db),
    req: AssessImpactRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    try:
        record = service.assess_impact(
            db,
            ecn_id=req.ecn_id,
            project_id=req.project_id,
            current_user_id=current_user.id,
            machine_id=req.machine_id,
            schedule_impact_days=req.schedule_impact_days,
            affected_milestones=[m.model_dump() for m in req.affected_milestones] if req.affected_milestones else None,
            rework_cost=req.rework_cost,
            scrap_cost=req.scrap_cost,
            additional_cost=req.additional_cost,
            cost_breakdown=req.cost_breakdown.model_dump() if req.cost_breakdown else None,
            risk_level=req.risk_level,
            risk_description=req.risk_description,
            impact_summary=req.impact_summary,
            remark=req.remark,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 构建评估报告响应
    project = record.project
    return ImpactAssessmentReport(
        ecn_id=record.ecn_id,
        ecn_no=record.ecn_no,
        project_id=record.project_id,
        project_name=project.project_name if project else None,
        project_stage=record.project_stage_snapshot,
        project_progress=float(record.project_progress_snapshot) if record.project_progress_snapshot else None,
        schedule_impact_days=record.schedule_impact_days or 0,
        affected_milestone_count=len(record.affected_milestones) if record.affected_milestones else 0,
        affected_milestones=record.affected_milestones,
        rework_cost=record.rework_cost or 0,
        scrap_cost=record.scrap_cost or 0,
        additional_cost=record.additional_cost or 0,
        total_cost_impact=record.total_cost_impact or 0,
        risk_level=record.risk_level or "LOW",
        risk_description=record.risk_description,
        impact_summary=record.impact_summary or "",
        recommendation=record.impact_report.get("recommendation") if record.impact_report else None,
        impact_record_id=record.id,
    )


# ─────────────────────────────────────────────────
#  2. 执行联动（ECN 执行后）
# ─────────────────────────────────────────────────


@router.post(
    "/project-change-impacts/execute-linkage",
    response_model=ProjectChangeImpactResponse,
    summary="ECN执行联动",
    description="ECN执行后调用，自动更新项目里程碑/成本/风险",
)
def execute_change_linkage(
    *,
    db: Session = Depends(deps.get_db),
    req: ExecuteLinkageRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    try:
        record = service.execute_linkage(
            db,
            impact_id=req.impact_id,
            current_user_id=current_user.id,
            update_milestones=req.update_milestones,
            record_costs=req.record_costs,
            create_risk=req.create_risk,
            actual_delay_days=req.actual_delay_days,
            actual_cost_impact=req.actual_cost_impact,
            remark=req.remark,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _build_impact_response(record)


# ─────────────────────────────────────────────────
#  3. 查询接口
# ─────────────────────────────────────────────────


@router.get(
    "/project-change-impacts/{impact_id}",
    response_model=ProjectChangeImpactResponse,
    summary="影响记录详情",
)
def get_impact_detail(
    impact_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    record = service.get_impact_detail(db, impact_id)
    if not record:
        raise HTTPException(status_code=404, detail="影响记录不存在")
    return _build_impact_response(record)


@router.get(
    "/project-change-impacts/by-ecn/{ecn_id}",
    response_model=List[ProjectChangeImpactListResponse],
    summary="ECN的项目影响列表",
    description="查看某个ECN影响的所有项目记录",
)
def get_ecn_impacts(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    records = service.get_ecn_project_impacts(db, ecn_id)
    return [_build_list_response(r) for r in records]


@router.get(
    "/project-change-impacts/by-project/{project_id}/summary",
    response_model=ProjectChangeSummary,
    summary="项目变更影响汇总",
    description="项目详情页 — 查看关联变更单、影响汇总",
)
def get_project_change_summary(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    try:
        summary = service.get_project_change_summary(db, project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return ProjectChangeSummary(
        project_id=summary["project_id"],
        project_name=summary["project_name"],
        total_ecn_count=summary["total_ecn_count"],
        assessed_count=summary["assessed_count"],
        executing_count=summary["executing_count"],
        completed_count=summary["completed_count"],
        total_delay_days=summary["total_delay_days"],
        total_cost_impact=summary["total_cost_impact"],
        high_risk_count=summary["high_risk_count"],
        impacts=[_build_list_response(r) for r in summary["impacts"]],
    )


@router.get(
    "/project-change-impacts/by-project/{project_id}/delays",
    summary="项目延期历史",
    description="查看项目因变更导致的历史延期记录",
)
def get_project_delay_history(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    try:
        return service.get_project_delay_history(db, project_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ─────────────────────────────────────────────────
#  辅助函数
# ─────────────────────────────────────────────────


def _build_impact_response(record) -> ProjectChangeImpactResponse:
    project = record.project
    machine = record.machine
    return ProjectChangeImpactResponse(
        id=record.id,
        ecn_id=record.ecn_id,
        ecn_no=record.ecn_no,
        project_id=record.project_id,
        project_name=project.project_name if project else None,
        machine_id=record.machine_id,
        machine_name=machine.machine_name if machine else None,
        project_stage_snapshot=record.project_stage_snapshot,
        project_progress_snapshot=float(record.project_progress_snapshot) if record.project_progress_snapshot else None,
        schedule_impact_days=record.schedule_impact_days or 0,
        affected_milestones=record.affected_milestones,
        rework_cost=record.rework_cost or 0,
        scrap_cost=record.scrap_cost or 0,
        additional_cost=record.additional_cost or 0,
        total_cost_impact=record.total_cost_impact or 0,
        cost_breakdown=record.cost_breakdown,
        risk_level=record.risk_level or "LOW",
        risk_description=record.risk_description,
        impact_summary=record.impact_summary,
        assessed_by=record.assessed_by,
        assessed_at=record.assessed_at,
        milestones_updated=record.milestones_updated or False,
        costs_recorded=record.costs_recorded or False,
        risk_created=record.risk_created or False,
        actual_delay_days=record.actual_delay_days,
        actual_cost_impact=record.actual_cost_impact,
        status=record.status or "ASSESSED",
        executed_by=record.executed_by,
        executed_at=record.executed_at,
        remark=record.remark,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _build_list_response(record) -> ProjectChangeImpactListResponse:
    ecn = record.ecn
    project = record.project
    return ProjectChangeImpactListResponse(
        id=record.id,
        ecn_id=record.ecn_id,
        ecn_no=record.ecn_no,
        ecn_title=ecn.ecn_title if ecn else None,
        project_id=record.project_id,
        project_name=project.project_name if project else None,
        schedule_impact_days=record.schedule_impact_days or 0,
        total_cost_impact=record.total_cost_impact or 0,
        risk_level=record.risk_level or "LOW",
        status=record.status or "ASSESSED",
        assessed_at=record.assessed_at,
        created_at=record.created_at,
    )
