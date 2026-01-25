# -*- coding: utf-8 -*-
"""
项目健康度端点

包含健康度计算、详情查询、批量计算等
"""

from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project, ProjectStatusLog
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.post("/{project_id}/health/calculate", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def calculate_project_health(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    auto_update: bool = Query(False, description="是否自动更新项目健康度"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    计算项目健康度
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    from app.services.health_calculator import HealthCalculator
    calculator = HealthCalculator(db)
    result = calculator.calculate_project_health(project_id)

    if auto_update and result.get("calculated_health"):
        new_health = result["calculated_health"]
        old_health = project.health or 'H1'

        if old_health != new_health:
            project.health = new_health
            db.add(project)

            status_log = ProjectStatusLog(
                project_id=project_id,
                old_stage=project.stage,
                new_stage=project.stage,
                old_status=project.status,
                new_status=project.status,
                old_health=old_health,
                new_health=new_health,
                change_type="HEALTH_CALCULATE",
                change_reason="系统自动计算健康度",
                changed_by=current_user.id,
                changed_at=datetime.now()
            )
            db.add(status_log)
            db.commit()

            result["updated"] = True
            result["old_health"] = old_health

    return ResponseModel(
        code=200,
        message="健康度计算完成",
        data=result
    )


@router.get("/{project_id}/health/details", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_health_details(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目健康度详情
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    from app.services.health_calculator import HealthCalculator
    calculator = HealthCalculator(db)
    details = calculator.get_health_details(project)

    return ResponseModel(
        code=200,
        message="success",
        data=details
    )


@router.post("/health/batch-calculate", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_calculate_project_health(
    *,
    db: Session = Depends(deps.get_db),
    project_ids: List[int] = Body(..., description="项目ID列表"),
    auto_update: bool = Body(False, description="是否自动更新项目健康度"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量计算项目健康度
    """
    from app.services.data_scope import DataScopeService
    from app.services.health_calculator import HealthCalculator

    query = db.query(Project).filter(Project.id.in_(project_ids))
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)
    accessible_project_ids = {p.id for p in query.all()}

    calculator = HealthCalculator(db)
    results = []

    for project_id in project_ids:
        if project_id not in accessible_project_ids:
            results.append({
                "project_id": project_id,
                "success": False,
                "error": "无访问权限"
            })
            continue

        try:
            result = calculator.calculate_project_health(project_id)

            if auto_update and result.get("calculated_health"):
                project = db.query(Project).filter(Project.id == project_id).first()
                if project:
                    new_health = result["calculated_health"]
                    old_health = project.health or 'H1'

                    if old_health != new_health:
                        project.health = new_health
                        db.add(project)

                        status_log = ProjectStatusLog(
                            project_id=project_id,
                            old_stage=project.stage,
                            new_stage=project.stage,
                            old_status=project.status,
                            new_status=project.status,
                            old_health=old_health,
                            new_health=new_health,
                            change_type="HEALTH_CALCULATE",
                            change_reason="批量自动计算健康度",
                            changed_by=current_user.id,
                            changed_at=datetime.now()
                        )
                        db.add(status_log)

                        result["updated"] = True
                        result["old_health"] = old_health

            results.append({
                "project_id": project_id,
                "success": True,
                **result
            })
        except Exception as e:
            results.append({
                "project_id": project_id,
                "success": False,
                "error": str(e)
            })

    db.commit()

    success_count = len([r for r in results if r.get("success")])
    return ResponseModel(
        code=200,
        message=f"批量计算完成：成功 {success_count} 个，失败 {len(results) - success_count} 个",
        data={
            "results": results,
            "success_count": success_count,
            "failed_count": len(results) - success_count
        }
    )
