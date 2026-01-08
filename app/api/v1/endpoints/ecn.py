# -*- coding: utf-8 -*-
"""
设计变更管理(ECN) API endpoints
包含：ECN基础管理、评估、审批、执行、追溯
"""

from typing import Any, List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.project import Project, Machine
from app.models.ecn import (
    Ecn, EcnType, EcnEvaluation, EcnApproval, EcnTask,
    EcnAffectedMaterial, EcnAffectedOrder, EcnLog, EcnApprovalMatrix
)
from app.services.ecn_notification_service import (
    notify_ecn_submitted,
    notify_evaluation_assigned,
    notify_evaluation_completed,
    notify_approval_assigned,
    notify_approval_result,
    notify_task_assigned,
    notify_task_completed,
    notify_overdue_alert,
)
from app.services.ecn_auto_assign_service import (
    auto_assign_evaluation,
    auto_assign_approval,
    auto_assign_task,
    auto_assign_pending_evaluations,
    auto_assign_pending_approvals,
    auto_assign_pending_tasks,
)
from app.schemas.ecn import (
    EcnCreate, EcnUpdate, EcnSubmit, EcnResponse, EcnListResponse,
    EcnEvaluationCreate, EcnEvaluationResponse,
    EcnApprovalCreate, EcnApprovalResponse,
    EcnTaskCreate, EcnTaskResponse,
    EcnAffectedMaterialCreate, EcnAffectedMaterialUpdate, EcnAffectedMaterialResponse,
    EcnAffectedOrderCreate, EcnAffectedOrderUpdate, EcnAffectedOrderResponse,
    EcnTypeCreate, EcnTypeUpdate, EcnTypeResponse,
    EcnStartExecution, EcnVerify, EcnClose
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
            project_name=project_name,
            status=ecn.status,
            priority=ecn.priority,
            applicant_name=applicant_name,
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
        applicant_dept=current_user.department,
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
        log_type="STATUS_CHANGE",
        log_action="SUBMIT",
        old_status="DRAFT",
        new_status="SUBMITTED",
        log_content=submit_in.remark or "提交ECN申请",
        created_by=current_user.id
    )
    db.add(log)
    
    # 自动触发评估流程：根据ECN类型获取需要评估的部门
    ecn_type_config = db.query(EcnType).filter(EcnType.type_code == ecn.ecn_type).first()
    if ecn_type_config and ecn_type_config.required_depts:
        ecn.status = "EVALUATING"
        preferred_evaluators = submit_in.preferred_evaluators or {}
        
        for dept in ecn_type_config.required_depts:
            # 创建评估记录（待评估）
            evaluation = EcnEvaluation(
                ecn_id=ecn_id,
                eval_dept=dept,
                status="PENDING"
            )
            db.add(evaluation)
            
            # 分配评估任务：优先使用手动指定，否则自动分配
            try:
                evaluator_id = None
                
                # 1. 优先使用手动指定的评估人员
                if dept in preferred_evaluators:
                    evaluator_id = preferred_evaluators[dept]
                    # 验证用户是否存在且属于该部门
                    evaluator = db.query(User).filter(
                        User.id == evaluator_id,
                        User.department == dept,
                        User.is_active == True
                    ).first()
                    if not evaluator:
                        evaluator_id = None  # 如果用户不存在或不属于该部门，使用自动分配
                
                # 2. 如果没有手动指定或手动指定无效，则自动分配
                if not evaluator_id:
                    evaluator_id = auto_assign_evaluation(db, ecn, evaluation)
                
                # 3. 如果分配成功，设置评估人并发送通知
                if evaluator_id:
                    evaluation.evaluator_id = evaluator_id
                    # 发送通知
                    notify_evaluation_assigned(db, ecn, evaluation, evaluator_id)
            except Exception as e:
                print(f"Failed to assign evaluation: {e}")
    
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
        log_type="STATUS_CHANGE",
        log_action="CANCEL",
        old_status=ecn.status,
        new_status="CANCELLED",
        log_content=cancel_reason or "取消ECN",
        created_by=current_user.id
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
    
    # 发送通知（评估任务分配）
    try:
        ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if ecn:
            notify_evaluation_assigned(db, ecn, evaluation, current_user.id)
    except Exception as e:
        print(f"Failed to send evaluation assigned notification: {e}")
    
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
                        EcnApprovalMatrix.is_active == True
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
                                    
                                    # 分配审批任务：如果没有手动指定，则自动分配
                                    try:
                                        approver_id = None
                                        
                                        # 如果审批记录创建时提供了 approver_id，优先使用
                                        # 注意：这里是在评估完成时自动创建审批，所以暂时不支持手动指定
                                        # 手动指定需要在单独创建审批记录时提供
                                        
                                        # 自动分配
                                        if not approver_id:
                                            approver_id = auto_assign_approval(db, ecn, approval)
                                        
                                        # 如果分配成功，设置审批人并发送通知
                                        if approver_id:
                                            approval.approver_id = approver_id
                                            # 发送通知
                                            notify_approval_assigned(db, ecn, approval, approver_id)
                                    except Exception as e:
                                        print(f"Failed to assign approval: {e}")
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
                                            # 发送通知
                                            notify_approval_assigned(db, ecn, approval, approver_id)
                                    except Exception as e:
                                        print(f"Failed to auto assign approval: {e}")
                    
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
                                # 发送通知
                                notify_approval_assigned(db, ecn, approval, approver_id)
                        except Exception as e:
                            print(f"Failed to auto assign approval: {e}")
    
    db.add(eval)
    db.add(ecn)
    db.commit()
    db.refresh(eval)
    
    # 发送通知（评估完成）
    try:
        notify_evaluation_completed(db, ecn, eval)
    except Exception as e:
        print(f"Failed to send evaluation completed notification: {e}")
    
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
    
    # 发送通知（审批任务分配）
    try:
        ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if ecn and approval.approver_id:
            notify_approval_assigned(db, ecn, approval, approval.approver_id)
    except Exception as e:
        print(f"Failed to send approval assigned notification: {e}")
    
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
            
            # ECN联动：如果工期影响 > 阈值，自动调整相关任务计划
            try:
                from app.services.progress_integration_service import ProgressIntegrationService
                integration_service = ProgressIntegrationService(db)
                result = integration_service.handle_ecn_approved(ecn, threshold_days=3)
                if result['adjusted_tasks'] or result['created_tasks']:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"ECN审批通过，已调整 {len(result['adjusted_tasks'])} 个任务，创建 {len(result['created_tasks'])} 个任务")
            except Exception as e:
                # 联动失败不影响ECN审批，记录日志
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"ECN联动处理失败: {str(e)}", exc_info=True)
            
            # 记录日志
            log = EcnLog(
                ecn_id=ecn.id,
                log_type="APPROVAL",
                log_action="APPROVED",
                old_status="PENDING_APPROVAL",
                new_status="APPROVED",
                log_content="ECN审批通过",
                created_by=current_user.id
            )
            db.add(log)
            db.add(ecn)
            
            # ECN审批通过时自动归集变更成本
            if ecn.cost_impact and ecn.cost_impact > 0 and ecn.project_id:
                try:
                    from app.services.cost_collection_service import CostCollectionService
                    CostCollectionService.collect_from_ecn(
                        db, ecn.id, created_by=current_user.id
                    )
                except Exception as e:
                    # 成本归集失败不影响审批流程，只记录错误
                    print(f"Failed to collect cost from ECN {ecn.id}: {e}")
    
    db.add(approval)
    db.commit()
    db.refresh(approval)
    
    # 发送通知（审批结果）
    try:
        notify_approval_result(db, ecn, approval, "APPROVED")
    except Exception as e:
        print(f"Failed to send approval result notification: {e}")
    
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
            log_type="APPROVAL",
            log_action="REJECTED",
            old_status="PENDING_APPROVAL",
            new_status="REJECTED",
            log_content=f"ECN审批驳回: {rejection_reason}",
            created_by=current_user.id
        )
        db.add(log)
        db.add(ecn)
    
    db.add(approval)
    db.commit()
    db.refresh(approval)
    
    # 发送通知（审批结果）
    try:
        notify_approval_result(db, ecn, approval, "REJECTED")
    except Exception as e:
        print(f"Failed to send approval result notification: {e}")
    
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
    
    # 分配执行任务：优先使用手动指定，否则自动分配
    try:
        assignee_id = task_in.assignee_id
        
        # 如果手动指定了执行人员，验证用户
        if assignee_id:
            assignee = db.query(User).filter(
                User.id == assignee_id,
                User.department == task_in.task_dept,
                User.is_active == True
            ).first()
            
            if not assignee:
                assignee_id = None  # 用户不存在或不属于该部门，使用自动分配
        
        # 如果没有手动指定或手动指定无效，则自动分配
        if not assignee_id:
            assignee_id = auto_assign_task(db, ecn, task)
        
        # 设置执行人
        if assignee_id:
            task.assignee_id = assignee_id
    except Exception as e:
        print(f"Failed to assign task: {e}")
    
    # 如果ECN状态是已审批，自动更新为执行中
    if ecn.status == "APPROVED":
        ecn.status = "EXECUTING"
        ecn.execution_start = datetime.now()
        ecn.current_step = "EXECUTION"
        db.add(ecn)
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # 发送通知（任务分配）
    try:
        if task.assignee_id:
            notify_task_assigned(db, ecn, task, task.assignee_id)
    except Exception as e:
        print(f"Failed to send task assigned notification: {e}")
    
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
    
    # 发送通知（任务完成）
    try:
        ecn = db.query(Ecn).filter(Ecn.id == task.ecn_id).first()
        if ecn:
            notify_task_completed(db, ecn, task)
    except Exception as e:
        print(f"Failed to send task completed notification: {e}")
    
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
        created_by_name = None
        if log.created_by:
            user = db.query(User).filter(User.id == log.created_by).first()
            created_by_name = user.real_name or user.username if user else None
        
        items.append({
            "id": log.id,
            "ecn_id": log.ecn_id,
            "log_type": log.log_type,
            "log_action": log.log_action,
            "old_status": log.old_status,
            "new_status": log.new_status,
            "log_content": log.log_content,
            "created_by": log.created_by,
            "created_by_name": created_by_name,
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


# ==================== ECN 受影响物料 CRUD ====================

@router.post("/ecns/{ecn_id}/affected-materials", response_model=EcnAffectedMaterialResponse, status_code=status.HTTP_201_CREATED)
def create_ecn_affected_material(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    material_in: EcnAffectedMaterialCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加受影响物料
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    # 验证物料是否存在（如果提供了material_id）
    if material_in.material_id:
        from app.models.material import Material
        material = db.query(Material).filter(Material.id == material_in.material_id).first()
        if not material:
            raise HTTPException(status_code=404, detail="物料不存在")
    
    affected_material = EcnAffectedMaterial(
        ecn_id=ecn_id,
        material_id=material_in.material_id,
        bom_item_id=material_in.bom_item_id,
        material_code=material_in.material_code,
        material_name=material_in.material_name,
        specification=material_in.specification,
        change_type=material_in.change_type,
        old_quantity=material_in.old_quantity,
        old_specification=material_in.old_specification,
        old_supplier_id=material_in.old_supplier_id,
        new_quantity=material_in.new_quantity,
        new_specification=material_in.new_specification,
        new_supplier_id=material_in.new_supplier_id,
        cost_impact=material_in.cost_impact or Decimal("0"),
        status="PENDING",
        remark=material_in.remark
    )
    
    db.add(affected_material)
    
    # 更新ECN的成本影响
    total_cost_impact = db.query(func.sum(EcnAffectedMaterial.cost_impact)).filter(
        EcnAffectedMaterial.ecn_id == ecn_id
    ).scalar() or Decimal("0")
    ecn.cost_impact = total_cost_impact
    db.add(ecn)
    
    db.commit()
    db.refresh(affected_material)
    
    return EcnAffectedMaterialResponse(
        id=affected_material.id,
        ecn_id=affected_material.ecn_id,
        material_id=affected_material.material_id,
        bom_item_id=affected_material.bom_item_id,
        material_code=affected_material.material_code,
        material_name=affected_material.material_name,
        specification=affected_material.specification,
        change_type=affected_material.change_type,
        old_quantity=affected_material.old_quantity,
        old_specification=affected_material.old_specification,
        old_supplier_id=affected_material.old_supplier_id,
        new_quantity=affected_material.new_quantity,
        new_specification=affected_material.new_specification,
        new_supplier_id=affected_material.new_supplier_id,
        cost_impact=affected_material.cost_impact or Decimal("0"),
        status=affected_material.status,
        processed_at=affected_material.processed_at,
        remark=affected_material.remark,
        created_at=affected_material.created_at,
        updated_at=affected_material.updated_at
    )


@router.put("/ecns/{ecn_id}/affected-materials/{material_id}", response_model=EcnAffectedMaterialResponse, status_code=status.HTTP_200_OK)
def update_ecn_affected_material(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    material_id: int,
    material_in: EcnAffectedMaterialUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新受影响物料
    """
    affected_material = db.query(EcnAffectedMaterial).filter(
        EcnAffectedMaterial.id == material_id,
        EcnAffectedMaterial.ecn_id == ecn_id
    ).first()
    if not affected_material:
        raise HTTPException(status_code=404, detail="受影响物料记录不存在")
    
    update_data = material_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(affected_material, field, value)
    
    # 如果更新了成本影响，重新计算ECN的总成本影响
    if 'cost_impact' in update_data:
        total_cost_impact = db.query(func.sum(EcnAffectedMaterial.cost_impact)).filter(
            EcnAffectedMaterial.ecn_id == ecn_id
        ).scalar() or Decimal("0")
        ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if ecn:
            ecn.cost_impact = total_cost_impact
            db.add(ecn)
    
    db.add(affected_material)
    db.commit()
    db.refresh(affected_material)
    
    return EcnAffectedMaterialResponse(
        id=affected_material.id,
        ecn_id=affected_material.ecn_id,
        material_id=affected_material.material_id,
        bom_item_id=affected_material.bom_item_id,
        material_code=affected_material.material_code,
        material_name=affected_material.material_name,
        specification=affected_material.specification,
        change_type=affected_material.change_type,
        old_quantity=affected_material.old_quantity,
        old_specification=affected_material.old_specification,
        old_supplier_id=affected_material.old_supplier_id,
        new_quantity=affected_material.new_quantity,
        new_specification=affected_material.new_specification,
        new_supplier_id=affected_material.new_supplier_id,
        cost_impact=affected_material.cost_impact or Decimal("0"),
        status=affected_material.status,
        processed_at=affected_material.processed_at,
        remark=affected_material.remark,
        created_at=affected_material.created_at,
        updated_at=affected_material.updated_at
    )


@router.delete("/ecns/{ecn_id}/affected-materials/{material_id}", status_code=status.HTTP_200_OK)
def delete_ecn_affected_material(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    material_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除受影响物料
    """
    affected_material = db.query(EcnAffectedMaterial).filter(
        EcnAffectedMaterial.id == material_id,
        EcnAffectedMaterial.ecn_id == ecn_id
    ).first()
    if not affected_material:
        raise HTTPException(status_code=404, detail="受影响物料记录不存在")
    
    db.delete(affected_material)
    
    # 重新计算ECN的总成本影响
    total_cost_impact = db.query(func.sum(EcnAffectedMaterial.cost_impact)).filter(
        EcnAffectedMaterial.ecn_id == ecn_id
    ).scalar() or Decimal("0")
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if ecn:
        ecn.cost_impact = total_cost_impact
        db.add(ecn)
    
    db.commit()
    
    return ResponseModel(code=200, message="受影响物料已删除")


# ==================== ECN 受影响订单 CRUD ====================

@router.post("/ecns/{ecn_id}/affected-orders", response_model=EcnAffectedOrderResponse, status_code=status.HTTP_201_CREATED)
def create_ecn_affected_order(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    order_in: EcnAffectedOrderCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加受影响订单
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    # 验证订单是否存在
    if order_in.order_type == "PURCHASE":
        from app.models.purchase import PurchaseOrder
        order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_in.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="采购订单不存在")
    elif order_in.order_type == "OUTSOURCING":
        from app.models.outsourcing import OutsourcingOrder
        order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_in.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="外协订单不存在")
    
    affected_order = EcnAffectedOrder(
        ecn_id=ecn_id,
        order_type=order_in.order_type,
        order_id=order_in.order_id,
        order_no=order_in.order_no,
        impact_description=order_in.impact_description,
        action_type=order_in.action_type,
        action_description=order_in.action_description,
        status="PENDING"
    )
    
    db.add(affected_order)
    db.commit()
    db.refresh(affected_order)
    
    return EcnAffectedOrderResponse(
        id=affected_order.id,
        ecn_id=affected_order.ecn_id,
        order_type=affected_order.order_type,
        order_id=affected_order.order_id,
        order_no=affected_order.order_no,
        impact_description=affected_order.impact_description,
        action_type=affected_order.action_type,
        action_description=affected_order.action_description,
        status=affected_order.status,
        processed_by=affected_order.processed_by,
        processed_at=affected_order.processed_at,
        created_at=affected_order.created_at,
        updated_at=affected_order.updated_at
    )


@router.put("/ecns/{ecn_id}/affected-orders/{order_id}", response_model=EcnAffectedOrderResponse, status_code=status.HTTP_200_OK)
def update_ecn_affected_order(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    order_id: int,
    order_in: EcnAffectedOrderUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新受影响订单
    """
    affected_order = db.query(EcnAffectedOrder).filter(
        EcnAffectedOrder.id == order_id,
        EcnAffectedOrder.ecn_id == ecn_id
    ).first()
    if not affected_order:
        raise HTTPException(status_code=404, detail="受影响订单记录不存在")
    
    update_data = order_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(affected_order, field, value)
    
    db.add(affected_order)
    db.commit()
    db.refresh(affected_order)
    
    return EcnAffectedOrderResponse(
        id=affected_order.id,
        ecn_id=affected_order.ecn_id,
        order_type=affected_order.order_type,
        order_id=affected_order.order_id,
        order_no=affected_order.order_no,
        impact_description=affected_order.impact_description,
        action_type=affected_order.action_type,
        action_description=affected_order.action_description,
        status=affected_order.status,
        processed_by=affected_order.processed_by,
        processed_at=affected_order.processed_at,
        created_at=affected_order.created_at,
        updated_at=affected_order.updated_at
    )


@router.delete("/ecns/{ecn_id}/affected-orders/{order_id}", status_code=status.HTTP_200_OK)
def delete_ecn_affected_order(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除受影响订单
    """
    affected_order = db.query(EcnAffectedOrder).filter(
        EcnAffectedOrder.id == order_id,
        EcnAffectedOrder.ecn_id == ecn_id
    ).first()
    if not affected_order:
        raise HTTPException(status_code=404, detail="受影响订单记录不存在")
    
    db.delete(affected_order)
    db.commit()
    
    return ResponseModel(code=200, message="受影响订单已删除")


# ==================== ECN 执行流程 ====================

@router.put("/ecns/{ecn_id}/start-execution", response_model=EcnResponse, status_code=status.HTTP_200_OK)
def start_ecn_execution(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    execution_in: EcnStartExecution,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    开始执行ECN
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    if ecn.status != "APPROVED":
        raise HTTPException(status_code=400, detail="只能开始执行已审批的ECN")
    
    ecn.status = "EXECUTING"
    ecn.execution_start = datetime.now()
    ecn.current_step = "EXECUTION"
    
    # 记录日志
    log = EcnLog(
        ecn_id=ecn_id,
        log_type="STATUS_CHANGE",
        log_action="START_EXECUTION",
        old_status="APPROVED",
        new_status="EXECUTING",
        log_content=execution_in.remark or "开始执行ECN",
        created_by=current_user.id
    )
    db.add(log)
    db.add(ecn)
    db.commit()
    db.refresh(ecn)
    
    return read_ecn(ecn_id, db, current_user)


@router.put("/ecns/{ecn_id}/verify", response_model=EcnResponse, status_code=status.HTTP_200_OK)
def verify_ecn(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    verify_in: EcnVerify,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    验证ECN执行结果
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    if ecn.status != "EXECUTING":
        raise HTTPException(status_code=400, detail="只能验证执行中的ECN")
    
    # 检查是否所有任务都已完成
    pending_tasks = db.query(EcnTask).filter(
        EcnTask.ecn_id == ecn_id,
        EcnTask.status != "COMPLETED"
    ).count()
    
    if pending_tasks > 0:
        raise HTTPException(status_code=400, detail="还有未完成的任务，无法验证")
    
    if verify_in.verify_result == "PASS":
        ecn.status = "COMPLETED"
        ecn.current_step = "COMPLETED"
        ecn.execution_end = datetime.now()
    else:
        ecn.status = "PENDING_VERIFY"
        ecn.current_step = "VERIFICATION_FAILED"
    
    # 记录日志
    log = EcnLog(
        ecn_id=ecn_id,
        log_type="VERIFICATION",
        log_action="VERIFY",
        old_status="EXECUTING",
        new_status=ecn.status,
        log_content=verify_in.verify_note or f"验证结果: {verify_in.verify_result}",
        created_by=current_user.id
    )
    db.add(log)
    db.add(ecn)
    db.commit()
    db.refresh(ecn)
    
    return read_ecn(ecn_id, db, current_user)


@router.put("/ecns/{ecn_id}/close", response_model=EcnResponse, status_code=status.HTTP_200_OK)
def close_ecn(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    close_in: EcnClose,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    关闭ECN
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    if ecn.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="只能关闭已完成的ECN")
    
    ecn.status = "CLOSED"
    ecn.closed_at = datetime.now()
    ecn.closed_by = current_user.id
    ecn.current_step = "CLOSED"
    
    # 记录日志
    log = EcnLog(
        ecn_id=ecn_id,
        log_type="STATUS_CHANGE",
        log_action="CLOSE",
        old_status="COMPLETED",
        new_status="CLOSED",
        log_content=close_in.close_note or "ECN已关闭",
        created_by=current_user.id
    )
    db.add(log)
    db.add(ecn)
    db.commit()
    db.refresh(ecn)
    
    return read_ecn(ecn_id, db, current_user)


# ==================== ECN 类型配置管理 ====================

@router.get("/ecn-types", response_model=List[EcnTypeResponse], status_code=status.HTTP_200_OK)
def list_ecn_types(
    db: Session = Depends(deps.get_db),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取ECN类型配置列表
    """
    query = db.query(EcnType)
    if is_active is not None:
        query = query.filter(EcnType.is_active == is_active)
    
    ecn_types = query.order_by(EcnType.type_code).all()
    
    items = []
    for et in ecn_types:
        items.append(EcnTypeResponse(
            id=et.id,
            type_code=et.type_code,
            type_name=et.type_name,
            description=et.description,
            required_depts=et.required_depts,
            optional_depts=et.optional_depts,
            approval_matrix=et.approval_matrix,
            is_active=et.is_active,
            created_at=et.created_at,
            updated_at=et.updated_at
        ))
    
    return items


@router.get("/ecn-types/{type_id}", response_model=EcnTypeResponse, status_code=status.HTTP_200_OK)
def get_ecn_type(
    type_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取ECN类型配置详情
    """
    ecn_type = db.query(EcnType).filter(EcnType.id == type_id).first()
    if not ecn_type:
        raise HTTPException(status_code=404, detail="ECN类型配置不存在")
    
    return EcnTypeResponse(
        id=ecn_type.id,
        type_code=ecn_type.type_code,
        type_name=ecn_type.type_name,
        description=ecn_type.description,
        required_depts=ecn_type.required_depts,
        optional_depts=ecn_type.optional_depts,
        approval_matrix=ecn_type.approval_matrix,
        is_active=ecn_type.is_active,
        created_at=ecn_type.created_at,
        updated_at=ecn_type.updated_at
    )


@router.post("/ecn-types", response_model=EcnTypeResponse, status_code=status.HTTP_201_CREATED)
def create_ecn_type(
    *,
    db: Session = Depends(deps.get_db),
    type_in: EcnTypeCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建ECN类型配置
    """
    # 检查类型编码是否已存在
    existing = db.query(EcnType).filter(EcnType.type_code == type_in.type_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="类型编码已存在")
    
    ecn_type = EcnType(
        type_code=type_in.type_code,
        type_name=type_in.type_name,
        description=type_in.description,
        required_depts=type_in.required_depts,
        optional_depts=type_in.optional_depts,
        approval_matrix=type_in.approval_matrix,
        is_active=type_in.is_active
    )
    
    db.add(ecn_type)
    db.commit()
    db.refresh(ecn_type)
    
    return get_ecn_type(ecn_type.id, db, current_user)


@router.put("/ecn-types/{type_id}", response_model=EcnTypeResponse, status_code=status.HTTP_200_OK)
def update_ecn_type(
    *,
    db: Session = Depends(deps.get_db),
    type_id: int,
    type_in: EcnTypeUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新ECN类型配置
    """
    ecn_type = db.query(EcnType).filter(EcnType.id == type_id).first()
    if not ecn_type:
        raise HTTPException(status_code=404, detail="ECN类型配置不存在")
    
    update_data = type_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ecn_type, field, value)
    
    db.add(ecn_type)
    db.commit()
    db.refresh(ecn_type)
    
    return get_ecn_type(type_id, db, current_user)


@router.delete("/ecn-types/{type_id}", status_code=status.HTTP_200_OK)
def delete_ecn_type(
    *,
    db: Session = Depends(deps.get_db),
    type_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除ECN类型配置
    """
    ecn_type = db.query(EcnType).filter(EcnType.id == type_id).first()
    if not ecn_type:
        raise HTTPException(status_code=404, detail="ECN类型配置不存在")
    
    # 检查是否有ECN使用此类型
    ecn_count = db.query(Ecn).filter(Ecn.ecn_type == ecn_type.type_code).count()
    if ecn_count > 0:
        raise HTTPException(status_code=400, detail=f"有{ecn_count}个ECN使用此类型，无法删除")
    
    db.delete(ecn_type)
    db.commit()
    
    return ResponseModel(code=200, message="ECN类型配置已删除")


# ==================== ECN 超时提醒 ====================

@router.get("/ecns/overdue-alerts", response_model=List[dict], status_code=status.HTTP_200_OK)
def get_ecn_overdue_alerts(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取ECN超时提醒列表
    包括：评估超时、审批超时、执行任务超时
    """
    now = datetime.now()
    alerts = []
    
    # 1. 评估超时提醒
    # 查找提交超过3天但评估未完成的ECN
    eval_timeout = now - timedelta(days=3)
    pending_evals = db.query(EcnEvaluation).filter(
        EcnEvaluation.status == "PENDING",
        EcnEvaluation.created_at < eval_timeout
    ).all()
    
    for eval in pending_evals:
        ecn = db.query(Ecn).filter(Ecn.id == eval.ecn_id).first()
        if ecn:
            alerts.append({
                "type": "EVALUATION_OVERDUE",
                "ecn_id": ecn.id,
                "ecn_no": ecn.ecn_no,
                "ecn_title": ecn.ecn_title,
                "dept": eval.eval_dept,
                "overdue_days": (now - eval.created_at).days,
                "message": f"ECN {ecn.ecn_no} 的{eval.eval_dept}评估已超时{(now - eval.created_at).days}天"
            })
    
    # 2. 审批超时提醒
    overdue_approvals = db.query(EcnApproval).filter(
        EcnApproval.status == "PENDING",
        EcnApproval.due_date < now
    ).all()
    
    for approval in overdue_approvals:
        ecn = db.query(Ecn).filter(Ecn.id == approval.ecn_id).first()
        if ecn:
            overdue_days = (now - approval.due_date).days if approval.due_date else 0
            alerts.append({
                "type": "APPROVAL_OVERDUE",
                "ecn_id": ecn.id,
                "ecn_no": ecn.ecn_no,
                "ecn_title": ecn.ecn_title,
                "approval_level": approval.approval_level,
                "approval_role": approval.approval_role,
                "overdue_days": overdue_days,
                "message": f"ECN {ecn.ecn_no} 的第{approval.approval_level}级审批（{approval.approval_role}）已超时{overdue_days}天"
            })
            # 更新超时标识
            approval.is_overdue = True
            db.add(approval)
    
    # 3. 执行任务超时提醒
    overdue_tasks = db.query(EcnTask).filter(
        EcnTask.status.in_(["PENDING", "IN_PROGRESS"]),
        EcnTask.planned_end < now.date()
    ).all()
    
    for task in overdue_tasks:
        ecn = db.query(Ecn).filter(Ecn.id == task.ecn_id).first()
        if ecn:
            overdue_days = (now.date() - task.planned_end).days if task.planned_end else 0
            alerts.append({
                "type": "TASK_OVERDUE",
                "ecn_id": ecn.id,
                "ecn_no": ecn.ecn_no,
                "ecn_title": ecn.ecn_title,
                "task_id": task.id,
                "task_name": task.task_name,
                "overdue_days": overdue_days,
                "message": f"ECN {ecn.ecn_no} 的任务「{task.task_name}」已超时{overdue_days}天"
            })
    
    db.commit()
    
    return alerts


@router.post("/ecns/batch-process-overdue-alerts", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_process_overdue_alerts(
    *,
    db: Session = Depends(deps.get_db),
    alerts: List[dict] = Body(..., description="超时提醒列表"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量处理ECN超时提醒
    发送提醒通知给相关人员
    """
    from app.models.organization import Department
    
    results = []
    success_count = 0
    fail_count = 0
    
    for alert_data in alerts:
        try:
            alert_type = alert_data.get('type')
            ecn_id = alert_data.get('ecn_id')
            
            if not alert_type or not ecn_id:
                results.append({
                    "alert": alert_data,
                    "status": "failed",
                    "message": "缺少必要字段"
                })
                fail_count += 1
                continue
            
            # 查找ECN
            ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
            if not ecn:
                results.append({
                    "alert": alert_data,
                    "status": "failed",
                    "message": "ECN不存在"
                })
                fail_count += 1
                continue
            
            # 根据提醒类型找到相关人员
            user_ids = []
            
            if alert_type == "EVALUATION_OVERDUE":
                # 评估超时：找到评估人员
                eval_dept = alert_data.get('dept')
                if eval_dept:
                    # 查找该部门的评估记录
                    evaluation = db.query(EcnEvaluation).filter(
                        EcnEvaluation.ecn_id == ecn_id,
                        EcnEvaluation.eval_dept == eval_dept,
                        EcnEvaluation.status == "PENDING"
                    ).first()
                    
                    if evaluation and evaluation.evaluator_id:
                        user_ids.append(evaluation.evaluator_id)
                    else:
                        # 如果没有指定评估人，尝试根据部门查找部门负责人
                        dept = db.query(Department).filter(Department.dept_name == eval_dept).first()
                        if dept and dept.manager_id:
                            user_ids.append(dept.manager_id)
                        else:
                            # 如果找不到，通知ECN申请人
                            if ecn.applicant_id:
                                user_ids.append(ecn.applicant_id)
            
            elif alert_type == "APPROVAL_OVERDUE":
                # 审批超时：找到审批人员
                approval_level = alert_data.get('approval_level')
                if approval_level:
                    approval = db.query(EcnApproval).filter(
                        EcnApproval.ecn_id == ecn_id,
                        EcnApproval.approval_level == approval_level,
                        EcnApproval.status == "PENDING"
                    ).first()
                    
                    if approval and approval.approver_id:
                        user_ids.append(approval.approver_id)
                    else:
                        # 如果找不到审批人，通知ECN申请人
                        if ecn.applicant_id:
                            user_ids.append(ecn.applicant_id)
            
            elif alert_type == "TASK_OVERDUE":
                # 任务超时：找到执行人员
                task_id = alert_data.get('task_id')
                if task_id:
                    task = db.query(EcnTask).filter(
                        EcnTask.id == task_id,
                        EcnTask.ecn_id == ecn_id
                    ).first()
                    
                    if task and task.assignee_id:
                        user_ids.append(task.assignee_id)
                    else:
                        # 如果找不到执行人，通知ECN申请人
                        if ecn.applicant_id:
                            user_ids.append(ecn.applicant_id)
            
            # 如果没有找到相关人员，通知ECN申请人
            if not user_ids and ecn.applicant_id:
                user_ids.append(ecn.applicant_id)
            
            # 发送通知
            if user_ids:
                notify_overdue_alert(db, alert_data, user_ids)
                results.append({
                    "alert": alert_data,
                    "status": "success",
                    "message": f"已发送提醒通知给 {len(user_ids)} 位相关人员",
                    "notified_users": user_ids
                })
                success_count += 1
            else:
                results.append({
                    "alert": alert_data,
                    "status": "failed",
                    "message": "未找到相关人员"
                })
                fail_count += 1
                
        except Exception as e:
            results.append({
                "alert": alert_data,
                "status": "failed",
                "message": str(e)
            })
            fail_count += 1
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"批量处理完成：成功 {success_count} 个，失败 {fail_count} 个",
        data={
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
        }
    )


# ==================== ECN 模块集成 ====================

@router.post("/ecns/{ecn_id}/sync-to-bom", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_ecn_to_bom(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    将ECN变更同步到BOM
    根据受影响物料自动更新BOM
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    if ecn.status != "APPROVED" and ecn.status != "EXECUTING":
        raise HTTPException(status_code=400, detail="只能同步已审批或执行中的ECN")
    
    affected_materials = db.query(EcnAffectedMaterial).filter(
        EcnAffectedMaterial.ecn_id == ecn_id,
        EcnAffectedMaterial.status == "PENDING"
    ).all()
    
    updated_count = 0
    for am in affected_materials:
        if am.bom_item_id:
            from app.models.material import BomItem
            bom_item = db.query(BomItem).filter(BomItem.id == am.bom_item_id).first()
            if bom_item:
                # 根据变更类型更新BOM
                if am.change_type == "UPDATE":
                    if am.new_quantity:
                        bom_item.qty = float(am.new_quantity)
                    if am.new_specification:
                        bom_item.specification = am.new_specification
                elif am.change_type == "REPLACE" and am.material_id:
                    bom_item.material_id = am.material_id
                
                am.status = "PROCESSED"
                am.processed_at = datetime.now()
                db.add(bom_item)
                db.add(am)
                updated_count += 1
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"已同步{updated_count}个物料变更到BOM",
        data={"updated_count": updated_count}
    )


@router.post("/ecns/{ecn_id}/sync-to-project", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_ecn_to_project(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    将ECN变更同步到项目
    更新项目成本和工期
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    if not ecn.project_id:
        raise HTTPException(status_code=400, detail="ECN未关联项目")
    
    project = db.query(Project).filter(Project.id == ecn.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 更新项目成本（累加ECN的成本影响）
    if ecn.cost_impact:
        project.total_cost = (project.total_cost or Decimal("0")) + ecn.cost_impact
    
    # 更新项目工期（累加ECN的工期影响）
    if ecn.schedule_impact_days:
        # 这里需要根据项目的实际工期计算逻辑来更新
        # 示例：更新项目结束日期
        if project.planned_end_date:
            from datetime import timedelta
            project.planned_end_date = project.planned_end_date + timedelta(days=ecn.schedule_impact_days)
    
    db.add(project)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="ECN变更已同步到项目",
        data={
            "cost_impact": float(ecn.cost_impact or 0),
            "schedule_impact_days": ecn.schedule_impact_days or 0
        }
    )


@router.post("/ecns/{ecn_id}/sync-to-purchase", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_ecn_to_purchase(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    将ECN变更同步到采购订单
    根据受影响订单自动更新采购订单状态
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    affected_orders = db.query(EcnAffectedOrder).filter(
        EcnAffectedOrder.ecn_id == ecn_id,
        EcnAffectedOrder.order_type == "PURCHASE",
        EcnAffectedOrder.status == "PENDING"
    ).all()
    
    updated_count = 0
    for ao in affected_orders:
        from app.models.purchase import PurchaseOrder
        order = db.query(PurchaseOrder).filter(PurchaseOrder.id == ao.order_id).first()
        if order:
            # 根据处理方式更新订单
            if ao.action_type == "CANCEL":
                order.status = "CANCELLED"
            elif ao.action_type == "MODIFY":
                # 这里可以添加更详细的订单修改逻辑
                pass
            
            ao.status = "PROCESSED"
            ao.processed_by = current_user.id
            ao.processed_at = datetime.now()
            db.add(order)
            db.add(ao)
            updated_count += 1
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"已同步{updated_count}个采购订单变更",
        data={"updated_count": updated_count}
    )


# ==================== ECN 批量操作 ====================

@router.post("/ecns/batch-sync-to-bom", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_sync_ecns_to_bom(
    *,
    db: Session = Depends(deps.get_db),
    ecn_ids: List[int] = Body(..., description="ECN ID列表"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量同步ECN变更到BOM
    """
    results = []
    success_count = 0
    fail_count = 0
    
    for ecn_id in ecn_ids:
        try:
            ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
            if not ecn:
                results.append({"ecn_id": ecn_id, "status": "failed", "message": "ECN不存在"})
                fail_count += 1
                continue
            
            if ecn.status != "APPROVED" and ecn.status != "EXECUTING":
                results.append({"ecn_id": ecn_id, "status": "failed", "message": "只能同步已审批或执行中的ECN"})
                fail_count += 1
                continue
            
            # 调用单个同步逻辑
            affected_materials = db.query(EcnAffectedMaterial).filter(
                EcnAffectedMaterial.ecn_id == ecn_id,
                EcnAffectedMaterial.status == "PENDING"
            ).all()
            
            updated_count = 0
            for am in affected_materials:
                if am.bom_item_id:
                    from app.models.material import BomItem
                    bom_item = db.query(BomItem).filter(BomItem.id == am.bom_item_id).first()
                    if bom_item:
                        if am.change_type == "UPDATE":
                            if am.new_quantity:
                                bom_item.qty = float(am.new_quantity)
                            if am.new_specification:
                                bom_item.specification = am.new_specification
                        elif am.change_type == "REPLACE" and am.material_id:
                            bom_item.material_id = am.material_id
                        
                        am.status = "PROCESSED"
                        am.processed_at = datetime.now()
                        db.add(bom_item)
                        db.add(am)
                        updated_count += 1
            
            db.commit()
            results.append({
                "ecn_id": ecn_id,
                "ecn_no": ecn.ecn_no,
                "status": "success",
                "updated_count": updated_count
            })
            success_count += 1
        except Exception as e:
            db.rollback()
            results.append({"ecn_id": ecn_id, "status": "failed", "message": str(e)})
            fail_count += 1
    
    return ResponseModel(
        code=200,
        message=f"批量同步完成：成功{success_count}个，失败{fail_count}个",
        data={
            "total": len(ecn_ids),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
        }
    )


@router.post("/ecns/batch-sync-to-project", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_sync_ecns_to_project(
    *,
    db: Session = Depends(deps.get_db),
    ecn_ids: List[int] = Body(..., description="ECN ID列表"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量同步ECN变更到项目
    """
    results = []
    success_count = 0
    fail_count = 0
    
    for ecn_id in ecn_ids:
        try:
            ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
            if not ecn:
                results.append({"ecn_id": ecn_id, "status": "failed", "message": "ECN不存在"})
                fail_count += 1
                continue
            
            if not ecn.project_id:
                results.append({"ecn_id": ecn_id, "status": "failed", "message": "ECN未关联项目"})
                fail_count += 1
                continue
            
            project = db.query(Project).filter(Project.id == ecn.project_id).first()
            if not project:
                results.append({"ecn_id": ecn_id, "status": "failed", "message": "项目不存在"})
                fail_count += 1
                continue
            
            # 更新项目成本
            if ecn.cost_impact:
                project.total_cost = (project.total_cost or Decimal("0")) + ecn.cost_impact
            
            # 更新项目工期
            if ecn.schedule_impact_days and project.planned_end_date:
                from datetime import timedelta
                project.planned_end_date = project.planned_end_date + timedelta(days=ecn.schedule_impact_days)
            
            db.add(project)
            db.commit()
            
            results.append({
                "ecn_id": ecn_id,
                "ecn_no": ecn.ecn_no,
                "project_id": ecn.project_id,
                "status": "success",
                "cost_impact": float(ecn.cost_impact or 0),
                "schedule_impact_days": ecn.schedule_impact_days or 0
            })
            success_count += 1
        except Exception as e:
            db.rollback()
            results.append({"ecn_id": ecn_id, "status": "failed", "message": str(e)})
            fail_count += 1
    
    return ResponseModel(
        code=200,
        message=f"批量同步完成：成功{success_count}个，失败{fail_count}个",
        data={
            "total": len(ecn_ids),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
        }
    )


@router.post("/ecns/batch-sync-to-purchase", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_sync_ecns_to_purchase(
    *,
    db: Session = Depends(deps.get_db),
    ecn_ids: List[int] = Body(..., description="ECN ID列表"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量同步ECN变更到采购
    """
    results = []
    success_count = 0
    fail_count = 0
    
    for ecn_id in ecn_ids:
        try:
            ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
            if not ecn:
                results.append({"ecn_id": ecn_id, "status": "failed", "message": "ECN不存在"})
                fail_count += 1
                continue
            
            affected_orders = db.query(EcnAffectedOrder).filter(
                EcnAffectedOrder.ecn_id == ecn_id,
                EcnAffectedOrder.order_type == "PURCHASE",
                EcnAffectedOrder.status == "PENDING"
            ).all()
            
            updated_count = 0
            for ao in affected_orders:
                from app.models.purchase import PurchaseOrder
                order = db.query(PurchaseOrder).filter(PurchaseOrder.id == ao.order_id).first()
                if order:
                    if ao.action_type == "CANCEL":
                        order.status = "CANCELLED"
                    elif ao.action_type == "MODIFY":
                        pass  # 可以添加更详细的订单修改逻辑
                    
                    ao.status = "PROCESSED"
                    ao.processed_by = current_user.id
                    ao.processed_at = datetime.now()
                    db.add(order)
                    db.add(ao)
                    updated_count += 1
            
            db.commit()
            
            results.append({
                "ecn_id": ecn_id,
                "ecn_no": ecn.ecn_no,
                "status": "success",
                "updated_count": updated_count
            })
            success_count += 1
        except Exception as e:
            db.rollback()
            results.append({"ecn_id": ecn_id, "status": "failed", "message": str(e)})
            fail_count += 1
    
    return ResponseModel(
        code=200,
        message=f"批量同步完成：成功{success_count}个，失败{fail_count}个",
        data={
            "total": len(ecn_ids),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
        }
    )


@router.post("/ecns/{ecn_id}/batch-create-tasks", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_create_ecn_tasks(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    tasks: List[EcnTaskCreate] = Body(..., description="任务列表"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量创建ECN执行任务
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")
    
    if ecn.status not in ["APPROVED", "EXECUTING"]:
        raise HTTPException(status_code=400, detail="ECN当前不在执行阶段")
    
    # 获取最大任务序号
    max_order = db.query(EcnTask).filter(EcnTask.ecn_id == ecn_id).order_by(desc(EcnTask.task_no)).first()
    start_no = (max_order.task_no + 1) if max_order else 1
    
    created_tasks = []
    for idx, task_in in enumerate(tasks):
        task = EcnTask(
            ecn_id=ecn_id,
            task_no=start_no + idx,
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
        
        # 如果没有指定负责人，自动分配
        if not task.assignee_id:
            try:
                assignee_id = auto_assign_task(db, ecn, task)
                if assignee_id:
                    task.assignee_id = assignee_id
            except Exception as e:
                print(f"Failed to auto assign task: {e}")
        
        db.add(task)
        created_tasks.append(task)
        
        # 发送通知
        if task.assignee_id:
            try:
                notify_task_assigned(db, ecn, task, task.assignee_id)
            except Exception as e:
                print(f"Failed to send task assigned notification: {e}")
    
    # 如果ECN状态是已审批，自动更新为执行中
    if ecn.status == "APPROVED":
        ecn.status = "EXECUTING"
        ecn.execution_start = datetime.now()
        ecn.current_step = "EXECUTION"
        db.add(ecn)
    
    db.commit()
    
    # 刷新任务以获取ID
    for task in created_tasks:
        db.refresh(task)
    
    return ResponseModel(
        code=200,
        message=f"批量创建任务成功：共{len(created_tasks)}个",
        data={
            "ecn_id": ecn_id,
            "created_count": len(created_tasks),
            "task_ids": [task.id for task in created_tasks]
        }
    )

