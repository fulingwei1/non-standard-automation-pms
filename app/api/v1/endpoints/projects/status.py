# -*- coding: utf-8 -*-
"""
项目状态管理端点

包含阶段管理、状态更新、健康度计算、状态历史等端点
"""

from typing import Any, List, Optional, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import (
    Project, Machine, ProjectStatusLog, ProjectPaymentPlan,
    ProjectStage, ProjectMember
)
from app.schemas.project import (
    ProjectStatusResponse,
    ProjectHealthDetailsResponse,
    StageAdvanceRequest,
    BatchUpdateStatusRequest,
    BatchUpdateStageRequest,
    BatchAssignPMRequest,
    BatchArchiveRequest,
)
from app.schemas.common import PaginatedResponse, ResponseModel

from .utils import (
    _serialize_project_status_log,
    check_gate,
    check_gate_detailed,
)

router = APIRouter()


@router.put("/{project_id}/stage", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_stage(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    new_stage: str = Body(..., description="新阶段（S1-S9）"),
    reason: Optional[str] = Body(None, description="变更原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目阶段
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    # 验证阶段编码
    valid_stages = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
    if new_stage not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail=f"无效的阶段编码。有效值：{', '.join(valid_stages)}"
        )

    old_stage = project.stage or 'S1'

    if old_stage == new_stage:
        return ResponseModel(
            code=200,
            message="阶段未变化",
            data={"project_id": project_id, "stage": new_stage}
        )

    # 更新阶段
    project.stage = new_stage
    db.add(project)

    # 记录状态变更历史
    status_log = ProjectStatusLog(
        project_id=project_id,
        old_stage=old_stage,
        new_stage=new_stage,
        old_status=project.status,
        new_status=project.status,
        old_health=project.health,
        new_health=project.health,
        change_type="STAGE_CHANGE",
        change_reason=reason or f"阶段变更：{old_stage} → {new_stage}",
        changed_by=current_user.id,
        changed_at=datetime.now()
    )
    db.add(status_log)
    db.commit()

    return ResponseModel(
        code=200,
        message="阶段更新成功",
        data={
            "project_id": project_id,
            "old_stage": old_stage,
            "new_stage": new_stage,
        }
    )


@router.get("/{project_id}/status", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目状态信息
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "stage": project.stage,
            "status": project.status,
            "health": project.health,
            "progress_pct": project.progress_pct,
        }
    )


@router.put("/{project_id}/status", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    new_status: str = Body(..., description="新状态（ST01-ST30）"),
    reason: Optional[str] = Body(None, description="变更原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目状态
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    # 验证状态编码
    valid_statuses = [f"ST{i:02d}" for i in range(1, 31)]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail="无效的状态编码。有效值：ST01-ST30"
        )

    old_status = project.status

    if old_status == new_status:
        return ResponseModel(
            code=200,
            message="状态未变化",
            data={"project_id": project_id, "status": new_status}
        )

    project.status = new_status
    db.add(project)

    # 记录状态变更历史
    status_log = ProjectStatusLog(
        project_id=project_id,
        old_stage=project.stage,
        new_stage=project.stage,
        old_status=old_status,
        new_status=new_status,
        old_health=project.health,
        new_health=project.health,
        change_type="STATUS_CHANGE",
        change_reason=reason or f"状态变更：{old_status} → {new_status}",
        changed_by=current_user.id,
        changed_at=datetime.now()
    )
    db.add(status_log)
    db.commit()

    return ResponseModel(
        code=200,
        message="状态更新成功",
        data={
            "project_id": project_id,
            "old_status": old_status,
            "new_status": new_status,
        }
    )


@router.put("/{project_id}/health", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_health(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    new_health: str = Body(..., description="新健康度（H1-H4）"),
    reason: Optional[str] = Body(None, description="变更原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目健康度
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    valid_healths = ['H1', 'H2', 'H3', 'H4']
    if new_health not in valid_healths:
        raise HTTPException(
            status_code=400,
            detail=f"无效的健康度编码。有效值：{', '.join(valid_healths)}"
        )

    old_health = project.health or 'H1'

    if old_health == new_health:
        return ResponseModel(
            code=200,
            message="健康度未变化",
            data={"project_id": project_id, "health": new_health}
        )

    project.health = new_health
    db.add(project)

    # 记录状态变更历史
    status_log = ProjectStatusLog(
        project_id=project_id,
        old_stage=project.stage,
        new_stage=project.stage,
        old_status=project.status,
        new_status=project.status,
        old_health=old_health,
        new_health=new_health,
        change_type="HEALTH_CHANGE",
        change_reason=reason or f"健康度变更：{old_health} → {new_health}",
        changed_by=current_user.id,
        changed_at=datetime.now()
    )
    db.add(status_log)
    db.commit()

    return ResponseModel(
        code=200,
        message="健康度更新成功",
        data={
            "project_id": project_id,
            "old_health": old_health,
            "new_health": new_health,
        }
    )


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
    details = calculator.get_health_details(project_id)

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
    from app.services.health_calculator import HealthCalculator
    from app.services.data_scope_service import DataScopeService

    # 应用数据权限过滤
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


@router.post("/{project_id}/stages/init", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def init_project_stages(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    初始化项目阶段
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    # 检查是否已有阶段
    existing_stages = db.query(ProjectStage).filter(
        ProjectStage.project_id == project_id
    ).count()

    if existing_stages > 0:
        return ResponseModel(
            code=200,
            message="项目阶段已存在，无需重复初始化",
            data={"project_id": project_id, "stage_count": existing_stages}
        )

    from app.utils.project_utils import init_project_stages as do_init_stages
    do_init_stages(db, project_id)

    stage_count = db.query(ProjectStage).filter(
        ProjectStage.project_id == project_id
    ).count()

    return ResponseModel(
        code=200,
        message="项目阶段初始化成功",
        data={"project_id": project_id, "stage_count": stage_count}
    )


@router.get("/{project_id}/status-history", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_status_history(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    change_type: Optional[str] = Query(None, description="变更类型筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目状态变更历史
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)

    query = db.query(ProjectStatusLog).filter(
        ProjectStatusLog.project_id == project_id
    )

    if change_type:
        query = query.filter(ProjectStatusLog.change_type == change_type)

    total = query.count()
    offset = (page - 1) * page_size
    logs = query.order_by(desc(ProjectStatusLog.changed_at)).offset(offset).limit(page_size).all()

    items = [_serialize_project_status_log(log) for log in logs]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/{project_id}/stage-advance", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def advance_project_stage(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    advance_request: StageAdvanceRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目阶段推进（含阶段门校验）
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    from app.services.stage_advance_service import (
        validate_target_stage,
        validate_stage_advancement,
        perform_gate_check,
        update_project_stage_and_status,
        create_status_log,
        create_installation_dispatch_orders,
        generate_cost_review_report
    )

    project = check_project_access_or_raise(db, current_user, project_id)

    validate_target_stage(advance_request.target_stage)

    current_stage = project.stage or "S1"
    validate_stage_advancement(current_stage, advance_request.target_stage)

    gate_passed, missing_items, gate_check_result = perform_gate_check(
        db, project, advance_request.target_stage,
        advance_request.skip_gate_check, current_user.is_superuser
    )

    if not gate_passed:
        return ResponseModel(
            code=400,
            message="阶段门校验未通过",
            data={
                "project_id": project_id,
                "target_stage": advance_request.target_stage,
                "gate_passed": False,
                "missing_items": missing_items,
                "gate_check_result": gate_check_result,
            }
        )

    old_stage = current_stage
    old_status = project.status

    new_status = update_project_stage_and_status(
        db, project, advance_request.target_stage, old_stage, old_status
    )

    create_status_log(
        db, project_id, old_stage, advance_request.target_stage,
        old_status, new_status, project.health,
        advance_request.reason, current_user.id
    )

    create_installation_dispatch_orders(
        db, project, advance_request.target_stage, old_stage
    )

    generate_cost_review_report(
        db, project_id, advance_request.target_stage, new_status, current_user.id
    )

    db.commit()
    db.refresh(project)

    return ResponseModel(
        code=200,
        message="阶段推进成功",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "old_stage": old_stage,
            "new_stage": advance_request.target_stage,
            "new_status": new_status,
            "gate_passed": gate_passed,
            "gate_check_result": check_gate_detailed(db, project, advance_request.target_stage) if not advance_request.skip_gate_check else None,
        }
    )


@router.post("/{project_id}/check-auto-transition", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def check_auto_stage_transition(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    auto_advance: bool = Query(False, description="是否自动推进"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    检查阶段自动流转条件
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    from app.services.status_transition_service import StatusTransitionService

    check_project_access_or_raise(db, current_user, project_id)

    transition_service = StatusTransitionService(db)
    result = transition_service.check_auto_stage_transition(project_id, auto_advance=auto_advance)

    return ResponseModel(
        code=200,
        message=result.get("message", "检查完成"),
        data=result
    )


@router.get("/{project_id}/gate-check/{target_stage}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_gate_check_result(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    target_stage: str = Path(..., description="目标阶段（S2-S9）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取阶段门校验详细结果
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    valid_stages = ['S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
    if target_stage not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail=f"无效的目标阶段。有效值：{', '.join(valid_stages)}"
        )

    gate_check_result = check_gate_detailed(db, project, target_stage)

    return ResponseModel(
        code=200,
        message="获取阶段门校验结果成功",
        data=gate_check_result
    )


# ==================== 批量操作端点 ====================

@router.post("/batch/update-status", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_update_project_status(
    *,
    db: Session = Depends(deps.get_db),
    batch_request: BatchUpdateStatusRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量更新项目状态
    """
    valid_statuses = [f"ST{i:02d}" for i in range(1, 31)]
    if batch_request.new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail="无效的状态编码。有效值：ST01-ST30"
        )

    success_count = 0
    failed_projects = []

    from app.services.data_scope_service import DataScopeService
    query = db.query(Project).filter(Project.id.in_(batch_request.project_ids))
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)
    accessible_project_ids = {p.id for p in query.all()}

    for project_id in batch_request.project_ids:
        try:
            if project_id not in accessible_project_ids:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "无访问权限"
                })
                continue

            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "项目不存在"
                })
                continue

            old_status = project.status
            if old_status == batch_request.new_status:
                continue

            project.status = batch_request.new_status
            db.add(project)

            status_log = ProjectStatusLog(
                project_id=project_id,
                old_stage=project.stage,
                new_stage=project.stage,
                old_status=old_status,
                new_status=batch_request.new_status,
                old_health=project.health,
                new_health=project.health,
                change_type="STATUS_CHANGE",
                change_reason=batch_request.reason or f"批量状态变更：{old_status} → {batch_request.new_status}",
                changed_by=current_user.id,
                changed_at=datetime.now()
            )
            db.add(status_log)
            success_count += 1

        except Exception as e:
            failed_projects.append({
                "project_id": project_id,
                "reason": str(e)
            })

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量状态更新完成：成功 {success_count} 个，失败 {len(failed_projects)} 个",
        data={
            "success_count": success_count,
            "failed_count": len(failed_projects),
            "failed_projects": failed_projects
        }
    )


@router.post("/batch/update-stage", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_update_project_stage(
    *,
    db: Session = Depends(deps.get_db),
    batch_request: BatchUpdateStageRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量更新项目阶段
    """
    valid_stages = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
    if batch_request.new_stage not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail=f"无效的阶段编码。有效值：{', '.join(valid_stages)}"
        )

    success_count = 0
    failed_projects = []

    from app.services.data_scope_service import DataScopeService
    query = db.query(Project).filter(Project.id.in_(batch_request.project_ids))
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)
    accessible_project_ids = {p.id for p in query.all()}

    for project_id in batch_request.project_ids:
        try:
            if project_id not in accessible_project_ids:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "无访问权限"
                })
                continue

            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "项目不存在"
                })
                continue

            old_stage = project.stage or "S1"
            if old_stage == batch_request.new_stage:
                continue

            project.stage = batch_request.new_stage
            db.add(project)

            status_log = ProjectStatusLog(
                project_id=project_id,
                old_stage=old_stage,
                new_stage=batch_request.new_stage,
                old_status=project.status,
                new_status=project.status,
                old_health=project.health,
                new_health=project.health,
                change_type="STAGE_CHANGE",
                change_reason=batch_request.reason or f"批量阶段变更：{old_stage} → {batch_request.new_stage}",
                changed_by=current_user.id,
                changed_at=datetime.now()
            )
            db.add(status_log)
            success_count += 1

        except Exception as e:
            failed_projects.append({
                "project_id": project_id,
                "reason": str(e)
            })

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量阶段更新完成：成功 {success_count} 个，失败 {len(failed_projects)} 个",
        data={
            "success_count": success_count,
            "failed_count": len(failed_projects),
            "failed_projects": failed_projects
        }
    )


@router.post("/batch/assign-pm", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_assign_project_manager(
    *,
    db: Session = Depends(deps.get_db),
    batch_request: BatchAssignPMRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量分配项目经理
    """
    pm = db.query(User).filter(User.id == batch_request.pm_id).first()
    if not pm:
        raise HTTPException(status_code=404, detail="项目经理不存在")

    pm_name = pm.real_name or pm.username

    success_count = 0
    failed_projects = []

    from app.services.data_scope_service import DataScopeService
    query = db.query(Project).filter(Project.id.in_(batch_request.project_ids))
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)
    accessible_project_ids = {p.id for p in query.all()}

    for project_id in batch_request.project_ids:
        try:
            if project_id not in accessible_project_ids:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "无访问权限"
                })
                continue

            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "项目不存在"
                })
                continue

            old_pm_id = project.pm_id
            old_pm_name = project.pm_name

            project.pm_id = batch_request.pm_id
            project.pm_name = pm_name
            db.add(project)

            if old_pm_id != batch_request.pm_id:
                status_log = ProjectStatusLog(
                    project_id=project_id,
                    old_stage=project.stage,
                    new_stage=project.stage,
                    old_status=project.status,
                    new_status=project.status,
                    old_health=project.health,
                    new_health=project.health,
                    change_type="PM_CHANGE",
                    change_reason=f"批量分配项目经理：{old_pm_name or '未分配'} → {pm_name}",
                    changed_by=current_user.id,
                    changed_at=datetime.now()
                )
                db.add(status_log)

            success_count += 1

        except Exception as e:
            failed_projects.append({
                "project_id": project_id,
                "reason": str(e)
            })

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量分配项目经理完成：成功 {success_count} 个，失败 {len(failed_projects)} 个",
        data={
            "success_count": success_count,
            "failed_count": len(failed_projects),
            "failed_projects": failed_projects,
            "pm_id": batch_request.pm_id,
            "pm_name": pm_name
        }
    )
