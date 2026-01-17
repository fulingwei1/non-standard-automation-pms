# -*- coding: utf-8 -*-
"""
任职资格评估端点
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.qualification import QualificationAssessment
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.qualification import (
    QualificationAssessmentCreate,
    QualificationAssessmentListResponse,
    QualificationAssessmentResponse,
    QualificationAssessmentSubmitRequest,
)
from app.services.qualification_service import QualificationService

router = APIRouter()


@router.post("/assessments", response_model=ResponseModel[QualificationAssessmentResponse], status_code=status.HTTP_201_CREATED)
def create_assessment(
    *,
    db: Session = Depends(deps.get_db),
    assessment_in: QualificationAssessmentCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建任职资格评估记录"""
    assessment = QualificationService.assess_employee(
        db=db,
        employee_id=assessment_in.employee_id,
        assessment_type=assessment_in.assessment_type,
        scores=assessment_in.scores,
        assessor_id=assessment_in.assessor_id or current_user.id,
        qualification_id=assessment_in.qualification_id,
        assessment_period=assessment_in.assessment_period,
        comments=assessment_in.comments
    )

    return ResponseModel(code=200, message="创建成功", data=assessment)


@router.get("/assessments/{employee_id}", response_model=QualificationAssessmentListResponse, status_code=status.HTTP_200_OK)
def get_employee_assessments(
    *,
    db: Session = Depends(deps.get_db),
    employee_id: int,
    qualification_id: Optional[int] = Query(None, description="任职资格ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取员工评估历史"""
    assessments = QualificationService.get_assessment_history(
        db, employee_id, qualification_id
    )

    return QualificationAssessmentListResponse(
        items=assessments,
        total=len(assessments),
        page=1,
        page_size=len(assessments),
        pages=1
    )


@router.post("/assessments/{assessment_id}/submit", response_model=ResponseModel[QualificationAssessmentResponse], status_code=status.HTTP_200_OK)
def submit_assessment(
    *,
    db: Session = Depends(deps.get_db),
    assessment_id: int,
    submit_in: QualificationAssessmentSubmitRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """提交评估结果"""
    assessment = db.query(QualificationAssessment).filter(
        QualificationAssessment.id == assessment_id
    ).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="评估记录不存在")

    assessment.total_score = submit_in.total_score
    assessment.result = submit_in.result
    assessment.comments = submit_in.comments
    assessment.assessed_at = datetime.now()

    db.commit()
    db.refresh(assessment)

    return ResponseModel(code=200, message="提交成功", data=assessment)
