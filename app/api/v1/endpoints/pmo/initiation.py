# -*- coding: utf-8 -*-
"""
立项管理 - 自动生成
从 pmo.py 拆分
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.pmo import (
    InitiationApproveRequest,
    InitiationCreate,
    InitiationRejectRequest,
    InitiationResponse,
    InitiationUpdate,
)
from app.services.pmo_initiation import PmoInitiationService

router = APIRouter(tags=["pmo-initiation"])


def _to_response(
    initiation,
    presale_handover_context: Optional[dict[str, Any]] = None,
) -> InitiationResponse:
    """将 ORM 对象转换为响应模型"""
    return InitiationResponse(
        id=initiation.id,
        application_no=initiation.application_no,
        project_id=initiation.project_id,
        project_name=initiation.project_name,
        project_type=initiation.project_type,
        project_level=initiation.project_level,
        customer_name=initiation.customer_name,
        contract_no=initiation.contract_no,
        contract_amount=float(initiation.contract_amount) if initiation.contract_amount else None,
        required_start_date=initiation.required_start_date,
        required_end_date=initiation.required_end_date,
        technical_solution_id=initiation.technical_solution_id,
        requirement_summary=initiation.requirement_summary,
        technical_difficulty=initiation.technical_difficulty,
        estimated_hours=initiation.estimated_hours,
        resource_requirements=initiation.resource_requirements,
        risk_assessment=initiation.risk_assessment,
        applicant_id=initiation.applicant_id,
        applicant_name=initiation.applicant_name,
        apply_time=initiation.apply_time,
        status=initiation.status,
        review_result=initiation.review_result,
        approved_pm_id=initiation.approved_pm_id,
        approved_level=initiation.approved_level,
        approved_at=initiation.approved_at,
        approved_by=initiation.approved_by,
        created_at=initiation.created_at,
        updated_at=initiation.updated_at,
        presale_handover_context=presale_handover_context,
    )


def _to_project_manager_option(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "real_name": user.real_name,
        "department": user.department,
        "position": user.position,
    }


@router.get("/pmo/initiations", response_model=PaginatedResponse[InitiationResponse])
def read_initiations(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（申请编号/项目名称/合同编号）"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    applicant_id: Optional[int] = Query(None, description="申请人ID筛选"),
    contract_no: Optional[str] = Query(None, description="合同编号筛选"),
    current_user: User = Depends(security.require_permission("project:initiation:read")),
) -> Any:
    """立项申请列表"""
    try:
        service = PmoInitiationService(db)
        initiations, total = service.get_initiations(
            offset=pagination.offset,
            limit=pagination.limit,
            keyword=keyword,
            status=status_filter,
            applicant_id=applicant_id,
            contract_no=contract_no,
        )

        items = [
            _to_response(
                init,
                presale_handover_context=service.build_presale_handover_context(init),
            )
            for init in initiations
        ]
        return pagination.to_response(items, total)
    except Exception as e:
        import traceback

        error_detail = f"查询立项申请列表失败: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_detail)


@router.get("/pmo/initiations/project-managers", response_model=List[dict[str, Any]])
def read_project_manager_candidates(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project:initiation:approve")),
) -> Any:
    """立项审批可选项目经理列表。"""
    service = PmoInitiationService(db)
    return [
        _to_project_manager_option(user)
        for user in service.get_project_manager_candidates()
    ]


@router.post(
    "/pmo/initiations",
    response_model=InitiationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_initiation(
    *,
    db: Session = Depends(deps.get_db),
    initiation_in: InitiationCreate,
    current_user: User = Depends(security.require_permission("project:initiation:create")),
) -> Any:
    """创建立项申请"""
    try:
        service = PmoInitiationService(db)
        initiation = service.create_initiation(initiation_in, current_user)
        return _to_response(
            initiation,
            presale_handover_context=service.build_presale_handover_context(initiation),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/pmo/initiations/{initiation_id}", response_model=InitiationResponse)
def read_initiation(
    *,
    db: Session = Depends(deps.get_db),
    initiation_id: int,
    current_user: User = Depends(security.require_permission("project:initiation:read")),
) -> Any:
    """立项申请详情"""
    service = PmoInitiationService(db)
    initiation = service.get_initiation(initiation_id)
    if not initiation:
        raise HTTPException(status_code=404, detail="立项申请不存在")

    return _to_response(
        initiation,
        presale_handover_context=service.build_presale_handover_context(initiation),
    )


@router.put("/pmo/initiations/{initiation_id}", response_model=InitiationResponse)
def update_initiation(
    *,
    db: Session = Depends(deps.get_db),
    initiation_id: int,
    initiation_in: InitiationUpdate,
    current_user: User = Depends(security.require_permission("project:initiation:update")),
) -> Any:
    """更新立项申请"""
    try:
        service = PmoInitiationService(db)
        initiation = service.update_initiation(initiation_id, initiation_in)
        return _to_response(
            initiation,
            presale_handover_context=service.build_presale_handover_context(initiation),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/pmo/initiations/{initiation_id}/submit", response_model=ResponseModel)
def submit_initiation(
    *,
    db: Session = Depends(deps.get_db),
    initiation_id: int,
    current_user: User = Depends(security.require_permission("project:initiation:update")),
) -> Any:
    """提交立项评审"""
    try:
        service = PmoInitiationService(db)
        service.submit_initiation(initiation_id)
        return ResponseModel(code=200, message="提交成功")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/pmo/initiations/{initiation_id}/approve", response_model=ResponseModel)
def approve_initiation(
    *,
    db: Session = Depends(deps.get_db),
    initiation_id: int,
    approve_request: InitiationApproveRequest,
    current_user: User = Depends(security.require_permission("project:initiation:approve")),
) -> Any:
    """立项评审通过"""
    try:
        service = PmoInitiationService(db)
        initiation = service.approve_initiation(initiation_id, approve_request, current_user)
        return ResponseModel(
            code=200,
            message="审批通过",
            data={"project_id": initiation.project_id} if initiation.project_id else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/pmo/initiations/{initiation_id}/reject", response_model=ResponseModel)
def reject_initiation(
    *,
    db: Session = Depends(deps.get_db),
    initiation_id: int,
    reject_request: InitiationRejectRequest,
    current_user: User = Depends(security.require_permission("project:initiation:approve")),
) -> Any:
    """立项评审驳回"""
    try:
        service = PmoInitiationService(db)
        service.reject_initiation(initiation_id, reject_request, current_user)
        return ResponseModel(code=200, message="已驳回")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
