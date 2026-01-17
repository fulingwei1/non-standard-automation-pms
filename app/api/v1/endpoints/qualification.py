# -*- coding: utf-8 -*-
"""
任职资格管理 API 端点
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.qualification import (
    EmployeeQualification,
    PositionCompetencyModel,
    QualificationAssessment,
    QualificationLevel,
)
from app.models.user import User
from app.schemas.common import PageParams, ResponseModel
from app.schemas.qualification import (
    EmployeeQualificationCertifyRequest,
    EmployeeQualificationCreate,
    EmployeeQualificationListResponse,
    EmployeeQualificationPromoteRequest,
    EmployeeQualificationQuery,
    EmployeeQualificationResponse,
    EmployeeQualificationUpdate,
    PositionCompetencyModelCreate,
    PositionCompetencyModelListResponse,
    PositionCompetencyModelQuery,
    PositionCompetencyModelResponse,
    PositionCompetencyModelUpdate,
    QualificationAssessmentCreate,
    QualificationAssessmentListResponse,
    QualificationAssessmentQuery,
    QualificationAssessmentResponse,
    QualificationAssessmentSubmitRequest,
    QualificationAssessmentUpdate,
    QualificationLevelCreate,
    QualificationLevelListResponse,
    QualificationLevelQuery,
    QualificationLevelResponse,
    QualificationLevelUpdate,
)
from app.services.qualification_service import QualificationService

router = APIRouter()


# ==================== 任职资格等级管理 ====================

@router.post("/levels", response_model=ResponseModel[QualificationLevelResponse], status_code=status.HTTP_201_CREATED)
def create_qualification_level(
    *,
    db: Session = Depends(deps.get_db),
    level_in: QualificationLevelCreate,
    current_user: User = Depends(security.require_hr_access),
) -> Any:
    """创建任职资格等级（仅人力资源经理可配置）"""
    # 检查等级编码是否已存在
    existing = db.query(QualificationLevel).filter(
        QualificationLevel.level_code == level_in.level_code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"等级编码 {level_in.level_code} 已存在"
        )

    level = QualificationLevel(**level_in.model_dump())
    db.add(level)
    db.commit()
    db.refresh(level)

    return ResponseModel(code=200, message="创建成功", data=level)


@router.get("/levels", response_model=QualificationLevelListResponse, status_code=status.HTTP_200_OK)
def get_qualification_levels(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role_type: Optional[str] = Query(None, description="角色类型"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取任职资格等级列表"""
    query = db.query(QualificationLevel)

    if role_type:
        query = query.filter(QualificationLevel.role_type == role_type)
    if is_active is not None:
        query = query.filter(QualificationLevel.is_active == is_active)

    total = query.count()
    levels = query.order_by(QualificationLevel.level_order).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return QualificationLevelListResponse(
        items=levels,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/levels/{level_id}", response_model=ResponseModel[QualificationLevelResponse], status_code=status.HTTP_200_OK)
def get_qualification_level(
    *,
    db: Session = Depends(deps.get_db),
    level_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取任职资格等级详情"""
    level = db.query(QualificationLevel).filter(QualificationLevel.id == level_id).first()
    if not level:
        raise HTTPException(status_code=404, detail="等级不存在")

    return ResponseModel(code=200, message="获取成功", data=level)


@router.put("/levels/{level_id}", response_model=ResponseModel[QualificationLevelResponse], status_code=status.HTTP_200_OK)
def update_qualification_level(
    *,
    db: Session = Depends(deps.get_db),
    level_id: int,
    level_in: QualificationLevelUpdate,
    current_user: User = Depends(security.require_hr_access),
) -> Any:
    """更新任职资格等级"""
    level = db.query(QualificationLevel).filter(QualificationLevel.id == level_id).first()
    if not level:
        raise HTTPException(status_code=404, detail="等级不存在")

    update_data = level_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(level, field, value)

    db.commit()
    db.refresh(level)

    return ResponseModel(code=200, message="更新成功", data=level)


@router.delete("/levels/{level_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_qualification_level(
    *,
    db: Session = Depends(deps.get_db),
    level_id: int,
    current_user: User = Depends(security.require_hr_access),
) -> Any:
    """删除任职资格等级"""
    level = db.query(QualificationLevel).filter(QualificationLevel.id == level_id).first()
    if not level:
        raise HTTPException(status_code=404, detail="等级不存在")

    # 检查是否有关联数据
    competency_count = db.query(PositionCompetencyModel).filter(
        PositionCompetencyModel.level_id == level_id
    ).count()
    qualification_count = db.query(EmployeeQualification).filter(
        EmployeeQualification.current_level_id == level_id
    ).count()

    if competency_count > 0 or qualification_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该等级下存在关联数据，无法删除"
        )

    db.delete(level)
    db.commit()

    return ResponseModel(code=200, message="删除成功", data=None)


# ==================== 岗位能力模型管理 ====================

@router.post("/models", response_model=ResponseModel[PositionCompetencyModelResponse], status_code=status.HTTP_201_CREATED)
def create_competency_model(
    *,
    db: Session = Depends(deps.get_db),
    model_in: PositionCompetencyModelCreate,
    current_user: User = Depends(security.require_hr_access),
) -> Any:
    """创建岗位能力模型"""
    # 检查等级是否存在
    level = db.query(QualificationLevel).filter(QualificationLevel.id == model_in.level_id).first()
    if not level:
        raise HTTPException(status_code=404, detail="等级不存在")

    model = PositionCompetencyModel(**model_in.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)

    return ResponseModel(code=200, message="创建成功", data=model)


@router.get("/models", response_model=PositionCompetencyModelListResponse, status_code=status.HTTP_200_OK)
def get_competency_models(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    position_type: Optional[str] = Query(None, description="岗位类型"),
    position_subtype: Optional[str] = Query(None, description="岗位子类型"),
    level_id: Optional[int] = Query(None, description="等级ID"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取岗位能力模型列表"""
    query = db.query(PositionCompetencyModel)

    if position_type:
        query = query.filter(PositionCompetencyModel.position_type == position_type)
    if position_subtype:
        query = query.filter(PositionCompetencyModel.position_subtype == position_subtype)
    if level_id:
        query = query.filter(PositionCompetencyModel.level_id == level_id)
    if is_active is not None:
        query = query.filter(PositionCompetencyModel.is_active == is_active)

    total = query.count()
    models = query.order_by(desc(PositionCompetencyModel.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return PositionCompetencyModelListResponse(
        items=models,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/models/{position_type}/{level_id}", response_model=ResponseModel[PositionCompetencyModelResponse], status_code=status.HTTP_200_OK)
def get_competency_model_by_position_level(
    *,
    db: Session = Depends(deps.get_db),
    position_type: str,
    level_id: int,
    position_subtype: Optional[str] = Query(None, description="岗位子类型"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取特定岗位等级的能力要求"""
    model = QualificationService.get_competency_model(
        db, position_type, level_id, position_subtype
    )
    if not model:
        raise HTTPException(status_code=404, detail="能力模型不存在")

    return ResponseModel(code=200, message="获取成功", data=model)


@router.put("/models/{model_id}", response_model=ResponseModel[PositionCompetencyModelResponse], status_code=status.HTTP_200_OK)
def update_competency_model(
    *,
    db: Session = Depends(deps.get_db),
    model_id: int,
    model_in: PositionCompetencyModelUpdate,
    current_user: User = Depends(security.require_hr_access),
) -> Any:
    """更新岗位能力模型"""
    model = db.query(PositionCompetencyModel).filter(PositionCompetencyModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="能力模型不存在")

    update_data = model_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)

    db.commit()
    db.refresh(model)

    return ResponseModel(code=200, message="更新成功", data=model)


# ==================== 员工任职资格管理 ====================

@router.post("/employees/{employee_id}/certify", response_model=ResponseModel[EmployeeQualificationResponse], status_code=status.HTTP_201_CREATED)
def certify_employee_qualification(
    *,
    db: Session = Depends(deps.get_db),
    employee_id: int,
    certify_in: EmployeeQualificationCertifyRequest,
    current_user: User = Depends(security.require_hr_access),
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
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    employee_id: Optional[int] = Query(None, description="员工ID"),
    position_type: Optional[str] = Query(None, description="岗位类型"),
    level_id: Optional[int] = Query(None, description="等级ID"),
    status: Optional[str] = Query(None, description="认证状态"),
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
    if status:
        query = query.filter(EmployeeQualification.status == status)

    total = query.count()
    qualifications = query.order_by(desc(EmployeeQualification.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return EmployeeQualificationListResponse(
        items=qualifications,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/employees/{employee_id}/promote", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def promote_employee_qualification(
    *,
    db: Session = Depends(deps.get_db),
    employee_id: int,
    promote_in: EmployeeQualificationPromoteRequest,
    current_user: User = Depends(security.require_hr_access),
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


# ==================== 任职资格评估 ====================

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






