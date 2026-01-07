# -*- coding: utf-8 -*-
"""
设计变更管理(ECN) API endpoints
包含：ECN基础管理、评估、审批、执行、追溯
"""

from typing import Any, List, Optional
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.project import Project, Machine
from app.models.ecn import (
    Ecn, EcnType, EcnEvaluation, EcnApproval, EcnTask,
    EcnAffectedMaterial, EcnAffectedOrder, EcnLog, EcnApprovalMatrix
)
from app.schemas.ecn import (
    EcnCreate, EcnUpdate, EcnSubmit, EcnResponse, EcnListResponse,
    EcnEvaluationCreate, EcnEvaluationResponse,
    EcnApprovalCreate, EcnApprovalResponse,
    EcnTaskCreate, EcnTaskResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


def generate_ecn_no(db: Session) -> str:
    """生成ECN编号：ECN-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_ecn = (
        db.query(Ecn)
        .filter(Ecn.ecn_no.like(f"ECN-{today}-%"))
        .order_by(desc(Ecn.ecn_no))
        .first()
    )
    if max_ecn:
        seq = int(max_ecn.ecn_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"ECN-{today}-{seq:03d}"


# ==================== ECN 基础管理 ====================

@router.get("/ecns", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_ecns(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（ECN编号/标题）"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    ecn_type: Optional[str] = Query(None, description="变更类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取ECN列表
    """
    query = db.query(Ecn)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                Ecn.ecn_no.like(f"%{keyword}%"),
                Ecn.ecn_title.like(f"%{keyword}%"),
            )
        )
    
    # 项目筛选
    if project_id:
        query = query.filter(Ecn.project_id == project_id)
    
    # 机台筛选
    if machine_id:
        query = query.filter(Ecn.machine_id == machine_id)
    
    # 变更类型筛选
    if ecn_type:
        query = query.filter(Ecn.ecn_type == ecn_type)
    
    # 状态筛选
    if status:
        query = query.filter(Ecn.status == status)
    
    # 优先级筛选
    if priority:
        query = query.filter(Ecn.priority == priority)
    
    total = query.count()
    offset = (page - 1) * page_size
    ecns = query.order_by(desc(Ecn.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for ecn in ecns:
        project_name = None
        if ecn.project_id:
            project = db.query(Project).filter(Project.id == ecn.project_id).first()
            project_name = project.project_name if project else None
        
        items.append(EcnListResponse(
            id=ecn.id,
            ecn_no=ecn.ecn_no,
            ecn_title=ecn.ecn_title,
            ecn_type=ecn.ecn_type,
            project_id=ecn.project_id,
            project_name=project_name,
            status=ecn.status,
            priority=ecn.priority,
            applicant_name=None,  # TODO: 从User获取
            applied_at=ecn.applied_at,
            created_at=ecn.created_at
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/ecns/{ecn_id}", response_model=EcnResponse, status_code=status.HTTP_200_OK)
def read_ecn(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取ECN详情
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    project_name = None
    if ecn.project_id:
        project = db.query(Project).filter(Project.id == ecn.project_id).first()
        project_name = project.project_name if project else None
    
    machine_name = None
    if ecn.machine_id:
        machine = db.query(Machine).filter(Machine.id == ecn.machine_id).first()
        machine_name = machine.machine_name if machine else None
    
    applicant_name = None
    if ecn.applicant_id:
        applicant = db.query(User).filter(User.id == ecn.applicant_id).first()
        applicant_name = applicant.real_name or applicant.username if applicant else None
    
    return EcnResponse(
        id=ecn.id,
        ecn_no=ecn.ecn_no,
        ecn_title=ecn.ecn_title,
        ecn_type=ecn.ecn_type,
        source_type=ecn.source_type,
        source_no=ecn.source_no,
        project_id=ecn.project_id,
        project_name=project_name,
        machine_id=ecn.machine_id,
        machine_name=machine_name,
        change_reason=ecn.change_reason,
        change_description=ecn.change_description,
        change_scope=ecn.change_scope,
        priority=ecn.priority,
        urgency=ecn.urgency,
        cost_impact=ecn.cost_impact or Decimal("0"),
        schedule_impact_days=ecn.schedule_impact_days or 0,
        status=ecn.status,
        current_step=ecn.current_step,
        applicant_id=ecn.applicant_id,
        applicant_name=applicant_name,
        applied_at=ecn.applied_at,
        approval_result=ecn.approval_result,
        created_at=ecn.created_at,
        updated_at=ecn.updated_at
    )


@router.post("/ecns", response_model=EcnResponse, status_code=status.HTTP_201_CREATED)
def create_ecn(
    *,
    db: Session = Depends(deps.get_db),
    ecn_in: EcnCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建ECN申请
    """
    # 验证项目是否存在
    project = db.query(Project).filter(Project.id == ecn_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 验证机台（如果提供）
    if ecn_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == ecn_in.machine_id).first()
        if not machine or machine.project_id != ecn_in.project_id:
            raise HTTPException(status_code=400, detail="机台不存在或不属于该项目")
    
    ecn_no = generate_ecn_no(db)
    
    ecn = Ecn(
        ecn_no=ecn_no,
        ecn_title=ecn_in.ecn_title,
        ecn_type=ecn_in.ecn_type,
        source_type=ecn_in.source_type,
        source_no=ecn_in.source_no,
        source_id=ecn_in.source_id,
        project_id=ecn_in.project_id,
        machine_id=ecn_in.machine_id,
        change_reason=ecn_in.change_reason,
        change_description=ecn_in.change_description,
        change_scope=ecn_in.change_scope,
        priority=ecn_in.priority,
        urgency=ecn_in.urgency,
        cost_impact=ecn_in.cost_impact or Decimal("0"),
        schedule_impact_days=ecn_in.schedule_impact_days or 0,
        status="DRAFT",
        applicant_id=current_user.id,
        applicant_dept=None,  # TODO: 从用户信息获取部门
    )
    
    db.add(ecn)
    db.commit()
    db.refresh(ecn)
    
    return read_ecn(ecn.id, db, current_user)


@router.put("/ecns/{ecn_id}", response_model=EcnResponse, status_code=status.HTTP_200_OK)
def update_ecn(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    ecn_in: EcnUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新ECN
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    if ecn.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能修改草稿状态的ECN")
    
    update_data = ecn_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ecn, field, value)
    
    db.add(ecn)
    db.commit()
    db.refresh(ecn)
    
    return read_ecn(ecn_id, db, current_user)


@router.put("/ecns/{ecn_id}/submit", response_model=EcnResponse, status_code=status.HTTP_200_OK)
def submit_ecn(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    submit_in: EcnSubmit,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交ECN
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    if ecn.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能提交草稿状态的ECN")
    
    ecn.status = "SUBMITTED"
    ecn.applied_at = datetime.now()
    ecn.current_step = "EVALUATION"
    
    # 记录日志
    log = EcnLog(
        ecn_id=ecn_id,
        action="SUBMIT",
        action_by=current_user.id,
        action_note=submit_in.remark or "提交ECN申请"
    )
    db.add(log)
    
    db.add(ecn)
    db.commit()
    db.refresh(ecn)
    
    return read_ecn(ecn_id, db, current_user)


@router.put("/ecns/{ecn_id}/cancel", response_model=EcnResponse, status_code=status.HTTP_200_OK)
def cancel_ecn(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    cancel_reason: Optional[str] = Query(None, description="取消原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    取消ECN
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    if ecn.status in ["APPROVED", "EXECUTING", "COMPLETED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="该状态的ECN不能取消")
    
    ecn.status = "CANCELLED"
    
    # 记录日志
    log = EcnLog(
        ecn_id=ecn_id,
        action="CANCEL",
        action_by=current_user.id,
        action_note=cancel_reason or "取消ECN"
    )
    db.add(log)
    
    db.add(ecn)
    db.commit()
    db.refresh(ecn)
    
    return read_ecn(ecn_id, db, current_user)


# ==================== ECN 评估 ====================

@router.get("/ecns/{ecn_id}/evaluations", response_model=List[EcnEvaluationResponse], status_code=status.HTTP_200_OK)
def read_ecn_evaluations(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取评估列表
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    evaluations = db.query(EcnEvaluation).filter(EcnEvaluation.ecn_id == ecn_id).order_by(EcnEvaluation.created_at).all()
    
    items = []
    for eval in evaluations:
        evaluator_name = None
        if eval.evaluator_id:
            evaluator = db.query(User).filter(User.id == eval.evaluator_id).first()
            evaluator_name = evaluator.real_name or evaluator.username if evaluator else None
        
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
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
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
    
    return read_ecn_evaluation(evaluation.id, db, current_user)


@router.get("/ecn-evaluations/{eval_id}", response_model=EcnEvaluationResponse, status_code=status.HTTP_200_OK)
def read_ecn_evaluation(
    eval_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取评估详情
    """
    eval = db.query(EcnEvaluation).filter(EcnEvaluation.id == eval_id).first()
    if not eval:
        raise HTTPException(status_code=404, detail="评估记录不存在")
    
    evaluator_name = None
    if eval.evaluator_id:
        evaluator = db.query(User).filter(User.id == eval.evaluator_id).first()
        evaluator_name = evaluator.real_name or evaluator.username if evaluator else None
    
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
    eval = db.query(EcnEvaluation).filter(EcnEvaluation.id == eval_id).first()
    if not eval:
        raise HTTPException(status_code=404, detail="评估记录不存在")
    
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
    
    db.add(eval)
    db.add(ecn)
    db.commit()
    db.refresh(eval)
    
    return read_ecn_evaluation(eval_id, db, current_user)


@router.get("/ecns/{ecn_id}/evaluation-summary", response_model=dict, status_code=status.HTTP_200_OK)
def get_ecn_evaluation_summary(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取评估汇总
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
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


# ==================== ECN 审批 ====================

@router.get("/ecns/{ecn_id}/approvals", response_model=List[EcnApprovalResponse], status_code=status.HTTP_200_OK)
def read_ecn_approvals(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取审批记录列表
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    approvals = db.query(EcnApproval).filter(EcnApproval.ecn_id == ecn_id).order_by(EcnApproval.approval_level, EcnApproval.created_at).all()
    
    items = []
    for approval in approvals:
        approver_name = None
        if approval.approver_id:
            approver = db.query(User).filter(User.id == approval.approver_id).first()
            approver_name = approver.real_name or approver.username if approver else None
        
        items.append(EcnApprovalResponse(
            id=approval.id,
            ecn_id=approval.ecn_id,
            approval_level=approval.approval_level,
            approval_role=approval.approval_role,
            approver_id=approval.approver_id,
            approver_name=approver_name,
            approval_result=approval.approval_result,
            approval_opinion=approval.approval_opinion,
            approved_at=approval.approved_at,
            due_date=approval.due_date,
            is_overdue=approval.is_overdue or False,
            status=approval.status,
            created_at=approval.created_at,
            updated_at=approval.updated_at
        ))
    
    return items


@router.post("/ecns/{ecn_id}/approvals", response_model=EcnApprovalResponse, status_code=status.HTTP_201_CREATED)
def create_ecn_approval(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    approval_in: EcnApprovalCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建审批记录（系统自动创建或手动创建）
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    if ecn.status not in ["SUBMITTED", "IN_APPROVAL"]:
        raise HTTPException(status_code=400, detail="ECN当前不在审批阶段")
    
    approval = EcnApproval(
        ecn_id=ecn_id,
        approval_level=approval_in.approval_level,
        approval_role=approval_in.approval_role,
        approver_id=approval_in.approver_id,
        status="PENDING"
    )
    
    db.add(approval)
    db.commit()
    db.refresh(approval)
    
    return read_ecn_approval(approval.id, db, current_user)


@router.get("/ecn-approvals/{approval_id}", response_model=EcnApprovalResponse, status_code=status.HTTP_200_OK)
def read_ecn_approval(
    approval_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取审批记录详情
    """
    approval = db.query(EcnApproval).filter(EcnApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")
    
    approver_name = None
    if approval.approver_id:
        approver = db.query(User).filter(User.id == approval.approver_id).first()
        approver_name = approver.real_name or approver.username if approver else None
    
    return EcnApprovalResponse(
        id=approval.id,
        ecn_id=approval.ecn_id,
        approval_level=approval.approval_level,
        approval_role=approval.approval_role,
        approver_id=approval.approver_id,
        approver_name=approver_name,
        approval_result=approval.approval_result,
        approval_opinion=approval.approval_opinion,
        approved_at=approval.approved_at,
        due_date=approval.due_date,
        is_overdue=approval.is_overdue or False,
        status=approval.status,
        created_at=approval.created_at,
        updated_at=approval.updated_at
    )


@router.put("/ecn-approvals/{approval_id}/approve", response_model=EcnApprovalResponse, status_code=status.HTTP_200_OK)
def approve_ecn(
    *,
    db: Session = Depends(deps.get_db),
    approval_id: int,
    approval_comment: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批通过
    """
    approval = db.query(EcnApproval).filter(EcnApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")
    
    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审批状态的记录")
    
    if approval.approver_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能审批分配给自己的审批")
    
    approval.approval_result = "APPROVED"
    approval.approval_opinion = approval_comment
    approval.approved_at = datetime.now()
    approval.status = "COMPLETED"
    
    # 检查是否所有审批都已完成
    ecn = db.query(Ecn).filter(Ecn.id == approval.ecn_id).first()
    if ecn:
        pending_approvals = db.query(EcnApproval).filter(
            EcnApproval.ecn_id == ecn.id,
            EcnApproval.status == "PENDING"
        ).count()
        
        if pending_approvals == 0:
            # 所有审批都已完成，更新ECN状态
            ecn.status = "APPROVED"
            ecn.approval_result = "APPROVED"
            ecn.approved_at = datetime.now()
            ecn.current_step = "EXECUTION"
            
            # 记录日志
            log = EcnLog(
                ecn_id=ecn.id,
                action="APPROVED",
                action_by=current_user.id,
                action_note="ECN审批通过"
            )
            db.add(log)
            db.add(ecn)
    
    db.add(approval)
    db.commit()
    db.refresh(approval)
    
    return read_ecn_approval(approval_id, db, current_user)


@router.put("/ecn-approvals/{approval_id}/reject", response_model=EcnApprovalResponse, status_code=status.HTTP_200_OK)
def reject_ecn(
    *,
    db: Session = Depends(deps.get_db),
    approval_id: int,
    rejection_reason: str = Query(..., description="驳回原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批驳回
    """
    approval = db.query(EcnApproval).filter(EcnApproval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批记录不存在")
    
    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审批状态的记录")
    
    if approval.approver_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能审批分配给自己的审批")
    
    approval.approval_result = "REJECTED"
    approval.approval_opinion = rejection_reason
    approval.approved_at = datetime.now()
    approval.status = "COMPLETED"
    
    # 更新ECN状态为驳回
    ecn = db.query(Ecn).filter(Ecn.id == approval.ecn_id).first()
    if ecn:
        ecn.status = "REJECTED"
        ecn.approval_result = "REJECTED"
        ecn.approval_note = rejection_reason
        
        # 记录日志
        log = EcnLog(
            ecn_id=ecn.id,
            action="REJECTED",
            action_by=current_user.id,
            action_note=f"ECN审批驳回: {rejection_reason}"
        )
        db.add(log)
        db.add(ecn)
    
    db.add(approval)
    db.commit()
    db.refresh(approval)
    
    return read_ecn_approval(approval_id, db, current_user)


@router.get("/ecn-approval-matrix", response_model=List[dict], status_code=status.HTTP_200_OK)
def read_ecn_approval_matrix(
    ecn_type: Optional[str] = Query(None, description="ECN类型筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取审批规则配置
    """
    query = db.query(EcnApprovalMatrix).filter(EcnApprovalMatrix.is_active == True)
    
    if ecn_type:
        query = query.filter(EcnApprovalMatrix.ecn_type == ecn_type)
    
    matrices = query.order_by(EcnApprovalMatrix.approval_level).all()
    
    return [
        {
            "id": m.id,
            "ecn_type": m.ecn_type,
            "condition_type": m.condition_type,
            "condition_min": float(m.condition_min) if m.condition_min else None,
            "condition_max": float(m.condition_max) if m.condition_max else None,
            "approval_level": m.approval_level,
            "approval_role": m.approval_role
        }
        for m in matrices
    ]


# ==================== ECN 执行 ====================

@router.get("/ecns/{ecn_id}/tasks", response_model=List[EcnTaskResponse], status_code=status.HTTP_200_OK)
def read_ecn_tasks(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取ECN任务列表
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    tasks = db.query(EcnTask).filter(EcnTask.ecn_id == ecn_id).order_by(EcnTask.task_no, EcnTask.created_at).all()
    
    items = []
    for task in tasks:
        assignee_name = None
        if task.assignee_id:
            assignee = db.query(User).filter(User.id == task.assignee_id).first()
            assignee_name = assignee.real_name or assignee.username if assignee else None
        
        items.append(EcnTaskResponse(
            id=task.id,
            ecn_id=task.ecn_id,
            task_no=task.task_no,
            task_name=task.task_name,
            task_type=task.task_type,
            task_dept=task.task_dept,
            assignee_id=task.assignee_id,
            assignee_name=assignee_name,
            planned_start=task.planned_start,
            planned_end=task.planned_end,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            progress_pct=task.progress_pct or 0,
            status=task.status,
            created_at=task.created_at,
            updated_at=task.updated_at
        ))
    
    return items


@router.post("/ecns/{ecn_id}/tasks", response_model=EcnTaskResponse, status_code=status.HTTP_201_CREATED)
def create_ecn_task(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    task_in: EcnTaskCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    分派ECN任务
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    if ecn.status not in ["APPROVED", "EXECUTING"]:
        raise HTTPException(status_code=400, detail="ECN当前不在执行阶段")
    
    # 验证负责人
    if task_in.assignee_id:
        assignee = db.query(User).filter(User.id == task_in.assignee_id).first()
        if not assignee:
            raise HTTPException(status_code=404, detail="负责人不存在")
    
    # 获取最大任务序号
    max_order = db.query(EcnTask).filter(EcnTask.ecn_id == ecn_id).order_by(desc(EcnTask.task_no)).first()
    task_no = (max_order.task_no + 1) if max_order else 1
    
    task = EcnTask(
        ecn_id=ecn_id,
        task_no=task_no,
        task_name=task_in.task_name,
        task_type=task_in.task_type,
        task_dept=task_in.task_dept,
        task_description=task_in.task_description,
        assignee_id=task_in.assignee_id,
        planned_start=task_in.planned_start,
        planned_end=task_in.planned_end,
        status="PENDING",
        progress_pct=0
    )
    
    # 如果ECN状态是已审批，自动更新为执行中
    if ecn.status == "APPROVED":
        ecn.status = "EXECUTING"
        ecn.execution_start = datetime.now()
        ecn.current_step = "EXECUTION"
        db.add(ecn)
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return read_ecn_task(task.id, db, current_user)


@router.get("/ecn-tasks/{task_id}", response_model=EcnTaskResponse, status_code=status.HTTP_200_OK)
def read_ecn_task(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取ECN任务详情
    """
    task = db.query(EcnTask).filter(EcnTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="ECN任务不存在")
    
    assignee_name = None
    if task.assignee_id:
        assignee = db.query(User).filter(User.id == task.assignee_id).first()
        assignee_name = assignee.real_name or assignee.username if assignee else None
    
    return EcnTaskResponse(
        id=task.id,
        ecn_id=task.ecn_id,
        task_no=task.task_no,
        task_name=task.task_name,
        task_type=task.task_type,
        task_dept=task.task_dept,
        assignee_id=task.assignee_id,
        assignee_name=assignee_name,
        planned_start=task.planned_start,
        planned_end=task.planned_end,
        actual_start=task.actual_start,
        actual_end=task.actual_end,
        progress_pct=task.progress_pct or 0,
        status=task.status,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.put("/ecn-tasks/{task_id}/progress", response_model=EcnTaskResponse, status_code=status.HTTP_200_OK)
def update_ecn_task_progress(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    progress: int = Query(..., ge=0, le=100, description="进度百分比"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新任务进度
    """
    task = db.query(EcnTask).filter(EcnTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="ECN任务不存在")
    
    task.progress_pct = progress
    
    # 如果进度大于0且状态为待处理，自动设置为进行中
    if progress > 0 and task.status == "PENDING":
        task.status = "IN_PROGRESS"
        if not task.actual_start:
            task.actual_start = datetime.now().date()
    
    # 如果进度达到100%，自动设置为完成
    if progress >= 100:
        task.status = "COMPLETED"
        task.progress_pct = 100
        if not task.actual_end:
            task.actual_end = datetime.now().date()
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return read_ecn_task(task_id, db, current_user)


@router.put("/ecn-tasks/{task_id}/complete", response_model=EcnTaskResponse, status_code=status.HTTP_200_OK)
def complete_ecn_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    完成ECN任务
    """
    task = db.query(EcnTask).filter(EcnTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="ECN任务不存在")
    
    task.status = "COMPLETED"
    task.progress_pct = 100
    if not task.actual_end:
        task.actual_end = datetime.now().date()
    if not task.actual_start:
        task.actual_start = task.planned_start or datetime.now().date()
    
    # 检查是否所有任务都已完成
    ecn = db.query(Ecn).filter(Ecn.id == task.ecn_id).first()
    if ecn:
        pending_tasks = db.query(EcnTask).filter(
            EcnTask.ecn_id == ecn.id,
            EcnTask.status != "COMPLETED"
        ).count()
        
        if pending_tasks == 0:
            # 所有任务都已完成，更新ECN状态
            ecn.status = "COMPLETED"
            ecn.execution_end = datetime.now()
            ecn.current_step = "COMPLETED"
            db.add(ecn)
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return read_ecn_task(task_id, db, current_user)


@router.get("/ecns/{ecn_id}/affected-materials", response_model=List[dict], status_code=status.HTTP_200_OK)
def read_ecn_affected_materials(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取受影响物料列表
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    affected_materials = db.query(EcnAffectedMaterial).filter(EcnAffectedMaterial.ecn_id == ecn_id).all()
    
    items = []
    for am in affected_materials:
        from app.models.material import Material
        material = db.query(Material).filter(Material.id == am.material_id).first()
        
        items.append({
            "id": am.id,
            "material_id": am.material_id,
            "material_code": material.material_code if material else None,
            "material_name": material.material_name if material else None,
            "change_type": am.change_type,
            "change_description": am.change_description,
            "impact_analysis": am.impact_analysis
        })
    
    return items


@router.get("/ecns/{ecn_id}/affected-orders", response_model=List[dict], status_code=status.HTTP_200_OK)
def read_ecn_affected_orders(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取受影响订单列表
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    affected_orders = db.query(EcnAffectedOrder).filter(EcnAffectedOrder.ecn_id == ecn_id).all()
    
    items = []
    for ao in affected_orders:
        items.append({
            "id": ao.id,
            "order_type": ao.order_type,
            "order_id": ao.order_id,
            "order_no": ao.order_no,
            "impact_type": ao.impact_type,
            "impact_description": ao.impact_description,
            "action_required": ao.action_required
        })
    
    return items


# ==================== ECN 追溯 ====================

@router.get("/ecns/{ecn_id}/logs", response_model=List[dict], status_code=status.HTTP_200_OK)
def read_ecn_logs(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取ECN日志列表
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    logs = db.query(EcnLog).filter(EcnLog.ecn_id == ecn_id).order_by(desc(EcnLog.created_at)).all()
    
    items = []
    for log in logs:
        action_by_name = None
        if log.action_by:
            user = db.query(User).filter(User.id == log.action_by).first()
            action_by_name = user.real_name or user.username if user else None
        
        items.append({
            "id": log.id,
            "ecn_id": log.ecn_id,
            "action": log.action,
            "action_by": log.action_by,
            "action_by_name": action_by_name,
            "action_note": log.action_note,
            "created_at": log.created_at
        })
    
    return items


@router.get("/projects/{project_id}/ecns", response_model=List[EcnListResponse], status_code=status.HTTP_200_OK)
def read_project_ecns(
    project_id: int,
    db: Session = Depends(deps.get_db),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目ECN列表
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    query = db.query(Ecn).filter(Ecn.project_id == project_id)
    
    if status:
        query = query.filter(Ecn.status == status)
    
    ecns = query.order_by(desc(Ecn.created_at)).all()
    
    items = []
    for ecn in ecns:
        applicant_name = None
        if ecn.applicant_id:
            applicant = db.query(User).filter(User.id == ecn.applicant_id).first()
            applicant_name = applicant.real_name or applicant.username if applicant else None
        
        items.append(EcnListResponse(
            id=ecn.id,
            ecn_no=ecn.ecn_no,
            ecn_title=ecn.ecn_title,
            ecn_type=ecn.ecn_type,
            project_id=ecn.project_id,
            project_name=project.project_name,
            status=ecn.status,
            priority=ecn.priority,
            applicant_name=applicant_name,
            applied_at=ecn.applied_at,
            created_at=ecn.created_at
        ))
    
    return items


@router.get("/ecns/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_ecn_statistics(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    ECN统计分析
    统计ECN的数量、状态分布、类型分布、成本影响等
    """
    query = db.query(Ecn)
    
    if project_id:
        query = query.filter(Ecn.project_id == project_id)
    if start_date:
        query = query.filter(Ecn.applied_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Ecn.applied_at <= datetime.combine(end_date, datetime.max.time()))
    
    ecns = query.all()
    
    # 总数统计
    total_count = len(ecns)
    
    # 按状态统计
    by_status = {}
    for ecn in ecns:
        status_key = ecn.status or "UNKNOWN"
        if status_key not in by_status:
            by_status[status_key] = {"status": status_key, "count": 0, "total_cost_impact": 0.0}
        by_status[status_key]["count"] += 1
        if ecn.cost_impact:
            by_status[status_key]["total_cost_impact"] += float(ecn.cost_impact)
    
    # 按类型统计
    by_type = {}
    for ecn in ecns:
        type_key = ecn.ecn_type or "UNKNOWN"
        if type_key not in by_type:
            by_type[type_key] = {"type": type_key, "count": 0, "total_cost_impact": 0.0}
        by_type[type_key]["count"] += 1
        if ecn.cost_impact:
            by_type[type_key]["total_cost_impact"] += float(ecn.cost_impact)
    
    # 按优先级统计
    by_priority = {}
    for ecn in ecns:
        priority_key = ecn.priority or "UNKNOWN"
        if priority_key not in by_priority:
            by_priority[priority_key] = {"priority": priority_key, "count": 0}
        by_priority[priority_key]["count"] += 1
    
    # 成本影响统计
    total_cost_impact = sum(float(ecn.cost_impact or 0) for ecn in ecns)
    avg_cost_impact = total_cost_impact / total_count if total_count > 0 else 0.0
    
    # 进度影响统计
    total_schedule_impact = sum(ecn.schedule_impact_days or 0 for ecn in ecns)
    avg_schedule_impact = total_schedule_impact / total_count if total_count > 0 else 0.0
    
    # 按项目统计（如果未指定项目）
    by_project = {}
    if not project_id:
        for ecn in ecns:
            if ecn.project_id:
                project = db.query(Project).filter(Project.id == ecn.project_id).first()
                project_name = project.project_name if project else f"项目{ecn.project_id}"
                if ecn.project_id not in by_project:
                    by_project[ecn.project_id] = {
                        "project_id": ecn.project_id,
                        "project_name": project_name,
                        "count": 0,
                        "total_cost_impact": 0.0
                    }
                by_project[ecn.project_id]["count"] += 1
                if ecn.cost_impact:
                    by_project[ecn.project_id]["total_cost_impact"] += float(ecn.cost_impact)
    
    return {
        "total_count": total_count,
        "total_cost_impact": round(total_cost_impact, 2),
        "avg_cost_impact": round(avg_cost_impact, 2),
        "total_schedule_impact": total_schedule_impact,
        "avg_schedule_impact": round(avg_schedule_impact, 2),
        "by_status": list(by_status.values()),
        "by_type": list(by_type.values()),
        "by_priority": list(by_priority.values()),
        "by_project": list(by_project.values()) if by_project else None,
    }

