# -*- coding: utf-8 -*-
"""
ECN评估管理 API endpoints

包含：评估列表、创建评估、提交评估、评估汇总
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.ecn import Ecn, EcnApproval, EcnApprovalMatrix, EcnEvaluation, EcnType
from app.models.user import User
from app.schemas.ecn import EcnEvaluationCreate, EcnEvaluationResponse
from app.services.ecn_auto_assign_service import auto_assign_approval
from app.services.ecn_notification import (
    notify_approval_assigned,
    notify_evaluation_assigned,
    notify_evaluation_completed,
)

from .utils import get_user_display_name
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/ecns/{ecn_id}/evaluations", response_model=List[EcnEvaluationResponse], status_code=status.HTTP_200_OK)
def read_ecn_evaluations(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取评估列表
    """
    ecn = get_or_404(db, Ecn, ecn_id, "ECN不存在")

    evaluations = db.query(EcnEvaluation).filter(EcnEvaluation.ecn_id == ecn_id).order_by(EcnEvaluation.created_at).all()

    items = []
    for eval in evaluations:
        evaluator_name = get_user_display_name(db, eval.evaluator_id)

        items.append(EcnEvaluationResponse(
            id=eval.id,
            ecn_id=eval.ecn_id,
            eval_dept=eval.eval_dept,
            evaluator_id=eval.evaluator_id,
            evaluator_name=evaluator_name,
            impact_analysis=eval.impact_analysis,
            cost_estimate=eval.cost_estimate or Decimal("0"),
            schedule_estimate=eval.schedule_estimate or 0,
            resource_requirement=eval.resource_requirement,
            risk_assessment=eval.risk_assessment,
            eval_result=eval.eval_result,
            eval_opinion=eval.eval_opinion,
            conditions=eval.conditions,
            evaluated_at=eval.evaluated_at,
            status=eval.status,
            created_at=eval.created_at,
            updated_at=eval.updated_at
        ))

    return items


@router.post("/ecns/{ecn_id}/evaluations", response_model=EcnEvaluationResponse, status_code=status.HTTP_201_CREATED)
def create_ecn_evaluation(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    eval_in: EcnEvaluationCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建评估
    """
    ecn = get_or_404(db, Ecn, ecn_id, "ECN不存在")

    if ecn.status != "SUBMITTED" and ecn.current_step != "EVALUATION":
        raise HTTPException(status_code=400, detail="ECN当前不在评估阶段")

    # 检查是否已有该部门的评估
    existing = db.query(EcnEvaluation).filter(
        EcnEvaluation.ecn_id == ecn_id,
        EcnEvaluation.eval_dept == eval_in.eval_dept
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该部门已存在评估记录")

    evaluation = EcnEvaluation(
        ecn_id=ecn_id,
        eval_dept=eval_in.eval_dept,
        evaluator_id=current_user.id,
        impact_analysis=eval_in.impact_analysis,
        cost_estimate=eval_in.cost_estimate or Decimal("0"),
        schedule_estimate=eval_in.schedule_estimate or 0,
        resource_requirement=eval_in.resource_requirement,
        risk_assessment=eval_in.risk_assessment,
        eval_result=eval_in.eval_result,
        eval_opinion=eval_in.eval_opinion,
        conditions=eval_in.conditions,
        status="DRAFT"
    )

    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    # 发送通知（评估任务分配）
    try:
        ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if ecn:
            notify_evaluation_assigned(db, ecn, evaluation, current_user.id)
    except Exception as e:
        logger.error(f"Failed to send evaluation assigned notification: {e}")

    return _build_evaluation_response(db, evaluation)


@router.get("/ecn-evaluations/{eval_id}", response_model=EcnEvaluationResponse, status_code=status.HTTP_200_OK)
def read_ecn_evaluation(
    eval_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取评估详情
    """
    eval = get_or_404(db, EcnEvaluation, eval_id, "评估记录不存在")

    return _build_evaluation_response(db, eval)


@router.put("/ecn-evaluations/{eval_id}/submit", response_model=EcnEvaluationResponse, status_code=status.HTTP_200_OK)
def submit_ecn_evaluation(
    *,
    db: Session = Depends(deps.get_db),
    eval_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交评估结果
    """
    eval = get_or_404(db, EcnEvaluation, eval_id, "评估记录不存在")

    if eval.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能提交草稿状态的评估")

    if eval.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能提交自己的评估")

    eval.status = "SUBMITTED"
    eval.submitted_at = datetime.now()

    # 更新ECN的影响评估（汇总所有评估）
    ecn = db.query(Ecn).filter(Ecn.id == eval.ecn_id).first()
    if ecn:
        # 计算所有已提交评估的成本和工期影响
        submitted_evals = db.query(EcnEvaluation).filter(
            EcnEvaluation.ecn_id == ecn.id,
            EcnEvaluation.status == "SUBMITTED"
        ).all()

        total_cost = sum(float(e.cost_estimate or 0) for e in submitted_evals)
        max_schedule = max((e.schedule_estimate or 0) for e in submitted_evals) if submitted_evals else 0

        ecn.cost_impact = Decimal(str(total_cost))
        ecn.schedule_impact_days = max_schedule

        # 检查是否所有必需的评估都已完成
        ecn_type_config = db.query(EcnType).filter(EcnType.type_code == ecn.ecn_type).first()
        if ecn_type_config and ecn_type_config.required_depts:
            required_depts = ecn_type_config.required_depts
            submitted_depts = [e.eval_dept for e in submitted_evals]

            # 如果所有必需部门的评估都已完成，自动触发审批流程
            if all(dept in submitted_depts for dept in required_depts):
                ecn.status = "EVALUATED"
                ecn.current_step = "APPROVAL"

                # 根据审批矩阵自动创建审批记录
                approval_matrix = ecn_type_config.approval_matrix or {}
                if approval_matrix:
                    # 根据成本影响和工期影响确定审批层级
                    cost_impact = float(ecn.cost_impact or 0)
                    schedule_impact = ecn.schedule_impact_days or 0

                    # 查找匹配的审批规则
                    approval_rules = db.query(EcnApprovalMatrix).filter(
                        EcnApprovalMatrix.ecn_type == ecn.ecn_type,
                        EcnApprovalMatrix.is_active
                    ).all()

                    for rule in approval_rules:
                        if rule.condition_type == "COST":
                            if rule.condition_min and rule.condition_max:
                                if rule.condition_min <= cost_impact <= rule.condition_max:
                                    # 创建审批记录
                                    approval = EcnApproval(
                                        ecn_id=ecn.id,
                                        approval_level=rule.approval_level,
                                        approval_role=rule.approval_role,
                                        status="PENDING",
                                        due_date=datetime.now() + timedelta(days=3)  # 默认3天期限
                                    )
                                    db.add(approval)

                                    # 自动分配审批任务
                                    try:
                                        approver_id = auto_assign_approval(db, ecn, approval)
                                        if approver_id:
                                            approval.approver_id = approver_id
                                            notify_approval_assigned(db, ecn, approval, approver_id)
                                    except Exception as e:
                                        logger.error(f"Failed to assign approval: {e}")
                        elif rule.condition_type == "SCHEDULE":
                            if rule.condition_min and rule.condition_max:
                                if rule.condition_min <= schedule_impact <= rule.condition_max:
                                    approval = EcnApproval(
                                        ecn_id=ecn.id,
                                        approval_level=rule.approval_level,
                                        approval_role=rule.approval_role,
                                        status="PENDING",
                                        due_date=datetime.now() + timedelta(days=3)
                                    )
                                    db.add(approval)

                                    # 自动分配审批任务
                                    try:
                                        approver_id = auto_assign_approval(db, ecn, approval)
                                        if approver_id:
                                            approval.approver_id = approver_id
                                            notify_approval_assigned(db, ecn, approval, approver_id)
                                    except Exception as e:
                                        logger.error(f"Failed to auto assign approval: {e}")

                    # 如果没有匹配的规则，使用默认审批流程
                    if not approval_rules:
                        # 默认一级审批
                        approval = EcnApproval(
                            ecn_id=ecn.id,
                            approval_level=1,
                            approval_role="项目经理",
                            status="PENDING",
                            due_date=datetime.now() + timedelta(days=3)
                        )
                        db.add(approval)

                        # 自动分配审批任务
                        try:
                            approver_id = auto_assign_approval(db, ecn, approval)
                            if approver_id:
                                approval.approver_id = approver_id
                                notify_approval_assigned(db, ecn, approval, approver_id)
                        except Exception as e:
                            logger.error(f"Failed to auto assign approval: {e}")

    db.add(eval)
    db.add(ecn)
    db.commit()
    db.refresh(eval)

    # 发送通知（评估完成）
    try:
        notify_evaluation_completed(db, ecn, eval)
    except Exception as e:
        logger.error(f"Failed to send evaluation completed notification: {e}")

    return _build_evaluation_response(db, eval)


@router.get("/ecns/{ecn_id}/evaluation-summary", response_model=dict, status_code=status.HTTP_200_OK)
def get_ecn_evaluation_summary(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取评估汇总
    """
    ecn = get_or_404(db, Ecn, ecn_id, "ECN不存在")

    evaluations = db.query(EcnEvaluation).filter(EcnEvaluation.ecn_id == ecn_id).all()

    total_evaluations = len(evaluations)
    submitted_count = len([e for e in evaluations if e.status == "SUBMITTED"])
    approved_count = len([e for e in evaluations if e.eval_result == "APPROVE"])
    rejected_count = len([e for e in evaluations if e.eval_result == "REJECT"])

    total_cost_impact = sum(float(e.cost_estimate or 0) for e in evaluations)
    max_schedule_impact = max((e.schedule_estimate or 0) for e in evaluations) if evaluations else 0

    return {
        "ecn_id": ecn_id,
        "ecn_no": ecn.ecn_no,
        "total_evaluations": total_evaluations,
        "submitted_count": submitted_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "total_cost_impact": total_cost_impact,
        "max_schedule_impact": max_schedule_impact,
        "evaluations": [
            {
                "id": e.id,
                "eval_dept": e.eval_dept,
                "eval_result": e.eval_result,
                "cost_estimate": float(e.cost_estimate or 0),
                "schedule_estimate": e.schedule_estimate or 0,
                "status": e.status
            }
            for e in evaluations
        ]
    }


def _build_evaluation_response(db: Session, eval: EcnEvaluation) -> EcnEvaluationResponse:
    """构建评估响应"""
    evaluator_name = get_user_display_name(db, eval.evaluator_id)

    return EcnEvaluationResponse(
        id=eval.id,
        ecn_id=eval.ecn_id,
        eval_dept=eval.eval_dept,
        evaluator_id=eval.evaluator_id,
        evaluator_name=evaluator_name,
        impact_analysis=eval.impact_analysis,
        cost_estimate=eval.cost_estimate or Decimal("0"),
        schedule_estimate=eval.schedule_estimate or 0,
        resource_requirement=eval.resource_requirement,
        risk_assessment=eval.risk_assessment,
        eval_result=eval.eval_result,
        eval_opinion=eval.eval_opinion,
        conditions=eval.conditions,
        submitted_at=eval.submitted_at,
        created_at=eval.created_at,
        updated_at=eval.updated_at
    )
