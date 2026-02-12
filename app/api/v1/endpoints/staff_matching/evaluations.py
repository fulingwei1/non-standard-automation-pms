# -*- coding: utf-8 -*-
"""
员工标签评估 API端点
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.organization import Employee
from app.models.staff_matching import HrEmployeeTagEvaluation, HrTagDict
from app.models.user import User
from app.schemas import staff_matching as schemas
from app.services.staff_matching import StaffMatchingService
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination

router = APIRouter()


@router.get("/", response_model=List[schemas.EmployeeTagEvaluationResponse])
def list_evaluations(
    employee_id: Optional[int] = Query(None, description="员工ID"),
    tag_id: Optional[int] = Query(None, description="标签ID"),
    tag_type: Optional[str] = Query(None, description="标签类型"),
    is_valid: Optional[bool] = Query(True, description="是否有效"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取员工标签评估列表"""
    query = db.query(HrEmployeeTagEvaluation).join(HrTagDict)

    if employee_id:
        query = query.filter(HrEmployeeTagEvaluation.employee_id == employee_id)
    if tag_id:
        query = query.filter(HrEmployeeTagEvaluation.tag_id == tag_id)
    if tag_type:
        query = query.filter(HrTagDict.tag_type == tag_type)
    if is_valid is not None:
        query = query.filter(HrEmployeeTagEvaluation.is_valid == is_valid)

    evaluations = apply_pagination(query.order_by(HrEmployeeTagEvaluation.evaluate_date.desc()), pagination.offset, pagination.limit).all()

    # 附加关联信息
    result = []
    for eval in evaluations:
        eval_dict = {
            'id': eval.id,
            'employee_id': eval.employee_id,
            'tag_id': eval.tag_id,
            'score': eval.score,
            'evidence': eval.evidence,
            'evaluator_id': eval.evaluator_id,
            'evaluate_date': eval.evaluate_date,
            'is_valid': eval.is_valid,
            'created_at': eval.created_at,
            'tag_name': eval.tag.tag_name if eval.tag else None,
            'tag_type': eval.tag.tag_type if eval.tag else None,
            'evaluator_name': eval.evaluator.real_name if eval.evaluator else None
        }
        result.append(eval_dict)

    return result


@router.post("/", response_model=schemas.EmployeeTagEvaluationResponse, status_code=status.HTTP_201_CREATED)
def create_evaluation(
    eval_data: schemas.EmployeeTagEvaluationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:create"))
):
    """创建员工标签评估"""
    # 验证员工和标签存在
    employee = db.query(Employee).filter(Employee.id == eval_data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    tag = db.query(HrTagDict).filter(HrTagDict.id == eval_data.tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    evaluation = HrEmployeeTagEvaluation(
        **eval_data.model_dump(),
        evaluator_id=current_user.id
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    return {
        'id': evaluation.id,
        'employee_id': evaluation.employee_id,
        'tag_id': evaluation.tag_id,
        'score': evaluation.score,
        'evidence': evaluation.evidence,
        'evaluator_id': evaluation.evaluator_id,
        'evaluate_date': evaluation.evaluate_date,
        'is_valid': evaluation.is_valid,
        'created_at': evaluation.created_at,
        'tag_name': tag.tag_name,
        'tag_type': tag.tag_type,
        'evaluator_name': current_user.real_name
    }


@router.post("/batch", status_code=status.HTTP_201_CREATED)
def batch_create_evaluations(
    batch_data: schemas.EmployeeTagEvaluationBatch,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:create"))
):
    """批量创建员工标签评估"""
    # 验证员工存在
    employee = db.query(Employee).filter(Employee.id == batch_data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    created_count = 0
    for eval_item in batch_data.evaluations:
        tag_id = eval_item.get('tag_id')
        score = eval_item.get('score')
        evidence = eval_item.get('evidence', '')

        if not tag_id or not score:
            continue

        # 检查标签存在
        tag = db.query(HrTagDict).filter(HrTagDict.id == tag_id).first()
        if not tag:
            continue

        evaluation = HrEmployeeTagEvaluation(
            employee_id=batch_data.employee_id,
            tag_id=tag_id,
            score=score,
            evidence=evidence,
            evaluator_id=current_user.id,
            evaluate_date=batch_data.evaluate_date
        )
        db.add(evaluation)
        created_count += 1

    db.commit()

    # 更新员工档案
    StaffMatchingService.aggregate_employee_profile(db, batch_data.employee_id)

    return {"message": f"成功创建 {created_count} 条评估记录"}


@router.put("/{eval_id}", response_model=schemas.EmployeeTagEvaluationResponse)
def update_evaluation(
    eval_id: int,
    eval_data: schemas.EmployeeTagEvaluationUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:update"))
):
    """更新员工标签评估"""
    evaluation = db.query(HrEmployeeTagEvaluation).filter(HrEmployeeTagEvaluation.id == eval_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="评估记录不存在")

    for field, value in eval_data.model_dump(exclude_unset=True).items():
        setattr(evaluation, field, value)

    db.commit()
    db.refresh(evaluation)

    return {
        'id': evaluation.id,
        'employee_id': evaluation.employee_id,
        'tag_id': evaluation.tag_id,
        'score': evaluation.score,
        'evidence': evaluation.evidence,
        'evaluator_id': evaluation.evaluator_id,
        'evaluate_date': evaluation.evaluate_date,
        'is_valid': evaluation.is_valid,
        'created_at': evaluation.created_at,
        'tag_name': evaluation.tag.tag_name if evaluation.tag else None,
        'tag_type': evaluation.tag.tag_type if evaluation.tag else None,
        'evaluator_name': evaluation.evaluator.real_name if evaluation.evaluator else None
    }


@router.delete("/{eval_id}")
def delete_evaluation(
    eval_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """删除评估记录（软删除）"""
    evaluation = db.query(HrEmployeeTagEvaluation).filter(HrEmployeeTagEvaluation.id == eval_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="评估记录不存在")

    evaluation.is_valid = False
    db.commit()
    return {"message": "评估记录已删除"}
