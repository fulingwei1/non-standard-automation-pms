# -*- coding: utf-8 -*-
"""
员工任职资格管理端点
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.qualification import EmployeeQualification
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.qualification import (
    EmployeeQualificationCertifyRequest,
    EmployeeQualificationListResponse,
    EmployeeQualificationPromoteRequest,
    EmployeeQualificationResponse,
)
from app.services.qualification_service import QualificationService

router = APIRouter()


@router.post("/employees/{employee_id}/certify", response_model=ResponseModel[EmployeeQualificationResponse], status_code=status.HTTP_201_CREATED)
def certify_employee_qualification(
    *,
    db: Session = Depends(deps.get_db),
    employee_id: int,
    certify_in: EmployeeQualificationCertifyRequest,
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Any:
    """认证员工任职资格"""
    try:
        qualification = QualificationService.certify_employee(
            db=db,
            employee_id=employee_id,
            position_type=certify_in.position_type,
            level_id=certify_in.level_id,
            assessment_details=certify_in.assessment_details,
            certifier_id=current_user.id,
            certified_date=certify_in.certified_date,
            valid_until=certify_in.valid_until
        )
        return ResponseModel(code=200, message="认证成功", data=qualification)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/employees/{employee_id}", response_model=ResponseModel[EmployeeQualificationResponse], status_code=status.HTTP_200_OK)
def get_employee_qualification(
    *,
    db: Session = Depends(deps.get_db),
    employee_id: int,
    position_type: Optional[str] = Query(None, description="岗位类型"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取员工任职资格"""
    qualification = QualificationService.get_employee_qualification(
        db, employee_id, position_type
    )
    if not qualification:
        raise HTTPException(status_code=404, detail="员工任职资格不存在")

    return ResponseModel(code=200, message="获取成功", data=qualification)


@router.get("/employees", response_model=EmployeeQualificationListResponse, status_code=status.HTTP_200_OK)
def get_employee_qualifications(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    employee_id: Optional[int] = Query(None, description="员工ID"),
    position_type: Optional[str] = Query(None, description="岗位类型"),
    level_id: Optional[int] = Query(None, description="等级ID"),
    cert_status: Optional[str] = Query(None, alias="status", description="认证状态"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取员工任职资格列表"""
    query = db.query(EmployeeQualification)

    if employee_id:
        query = query.filter(EmployeeQualification.employee_id == employee_id)
    if position_type:
        query = query.filter(EmployeeQualification.position_type == position_type)
    if level_id:
        query = query.filter(EmployeeQualification.current_level_id == level_id)
    if cert_status:
        query = query.filter(EmployeeQualification.status == cert_status)

    total = query.count()
    qualifications = query.order_by(desc(EmployeeQualification.created_at)).offset(
        pagination.offset
    ).limit(pagination.limit).all()

    return EmployeeQualificationListResponse(
        items=qualifications,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.post("/employees/{employee_id}/promote", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def promote_employee_qualification(
    *,
    db: Session = Depends(deps.get_db),
    employee_id: int,
    promote_in: EmployeeQualificationPromoteRequest,
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Any:
    """员工晋升评估"""
    # 检查晋升资格
    eligibility = QualificationService.check_promotion_eligibility(
        db, employee_id, promote_in.target_level_id
    )

    if not eligibility.get('eligible'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=eligibility.get('reason', '不满足晋升条件')
        )

    # 获取当前任职资格
    qualification = QualificationService.get_employee_qualification(db, employee_id)

    # 创建评估记录
    assessment = QualificationService.assess_employee(
        db=db,
        employee_id=employee_id,
        assessment_type='PROMOTION',
        scores=promote_in.assessment_details,
        assessor_id=current_user.id,
        qualification_id=qualification.id if qualification else None,
        assessment_period=promote_in.assessment_period
    )

    # 如果评估通过，更新任职资格
    if assessment.result == 'PASS':
        QualificationService.certify_employee(
            db=db,
            employee_id=employee_id,
            position_type=qualification.position_type if qualification else 'ENGINEER',
            level_id=promote_in.target_level_id,
            assessment_details=promote_in.assessment_details,
            certifier_id=current_user.id
        )

    return ResponseModel(
        code=200,
        message="晋升评估完成",
        data={
            'assessment_id': assessment.id,
            'result': assessment.result,
            'total_score': float(assessment.total_score) if assessment.total_score else None,
            'promoted': assessment.result == 'PASS'
        }
    )
