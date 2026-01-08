# -*- coding: utf-8 -*-
"""
工程师进度管理 API 端点
包含：我的项目、任务管理、进度更新、完成证明、延期报告
"""

from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.task_center import TaskUnified, TaskApprovalWorkflow, TaskCompletionProof
from app.models.alert import ExceptionEvent
from app.schemas import engineer as schemas
from app.services.progress_aggregation_service import (
    aggregate_task_progress,
    create_progress_log
)

import os
import uuid

router = APIRouter()

# ==================== 我的项目列表 ====================

@router.get("/my-projects", response_model=schemas.MyProjectListResponse)
def get_my_projects(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
):
    """
    获取工程师参与的所有项目（含任务统计）
    """
    # 查询用户参与的项目
    project_members = db.query(ProjectMember).filter(
        and_(
            ProjectMember.user_id == current_user.id,
            ProjectMember.is_active == True
        )
    ).all()

    project_ids = [pm.project_id for pm in project_members]

    # 分页查询项目
    query = db.query(Project).filter(Project.id.in_(project_ids))
    total = query.count()

    projects = query.offset((page - 1) * page_size).limit(page_size).all()

    # 构建响应
    items = []
    for project in projects:
        # 获取我的角色
        my_roles = [pm.role_code for pm in project_members if pm.project_id == project.id]
        my_allocation = next((pm.allocation_pct for pm in project_members if pm.project_id == project.id), 100)

        # 统计我的任务
        my_tasks = db.query(TaskUnified).filter(
            and_(
                TaskUnified.project_id == project.id,
                TaskUnified.assignee_id == current_user.id
            )
        ).all()

        task_stats = schemas.TaskStatsResponse(
            total_tasks=len(my_tasks),
            pending_tasks=len([t for t in my_tasks if t.status == 'PENDING']),
            in_progress_tasks=len([t for t in my_tasks if t.status == 'IN_PROGRESS']),
            completed_tasks=len([t for t in my_tasks if t.status == 'COMPLETED']),
            overdue_tasks=len([t for t in my_tasks if t.deadline and t.deadline < datetime.now()
                              and t.status not in ['COMPLETED', 'CANCELLED']]),
            delayed_tasks=len([t for t in my_tasks if t.is_delayed]),
            pending_approval_tasks=len([t for t in my_tasks if t.approval_status == 'PENDING_APPROVAL'])
        )

        # 获取客户名称
        customer_name = project.customer.customer_name if project.customer else None

        items.append(schemas.MyProjectResponse(
            project_id=project.id,
            project_code=project.project_code,
            project_name=project.project_name,
            customer_name=customer_name,
            stage=project.stage,
            status=project.status,
            health=project.health,
            progress_pct=float(project.progress_pct) if project.progress_pct else 0.0,
            my_roles=my_roles,
            my_allocation_pct=my_allocation,
            task_stats=task_stats,
            planned_start_date=project.planned_start_date,
            planned_end_date=project.planned_end_date,
            last_activity_at=project.updated_at
        ))

    pages = (total + page_size - 1) // page_size

    return schemas.MyProjectListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


# ==================== 任务创建 ====================

@router.post("/tasks", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: schemas.TaskCreateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
):
    """
    创建任务（支持智能审批路由）
    - IMPORTANT 任务：需要PM审批
    - GENERAL 任务：直接创建
    """
    # 验证项目存在且用户是成员
    project = db.query(Project).filter(Project.id == task_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查用户是否是项目成员
    is_member = db.query(ProjectMember).filter(
        and_(
            ProjectMember.project_id == task_data.project_id,
            ProjectMember.user_id == current_user.id,
            ProjectMember.is_active == True
        )
    ).first()

    if not is_member:
        raise HTTPException(status_code=403, detail="您不是该项目的成员")

    # 验证IMPORTANT任务必须填写justification
    if task_data.task_importance == 'IMPORTANT' and not task_data.justification:
        raise HTTPException(status_code=400, detail="重要任务必须填写任务必要性说明")

    # 生成任务编号
    task_code = f"TASK-{datetime.now().strftime('%y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    # 确定初始状态
    if task_data.task_importance == 'IMPORTANT':
        initial_status = 'PENDING_APPROVAL'
        approval_required = True
        approval_status = 'PENDING_APPROVAL'
    else:
        initial_status = 'ACCEPTED'
        approval_required = False
        approval_status = None

    # 创建任务
    new_task = TaskUnified(
        task_code=task_code,
        title=task_data.title,
        description=task_data.description,
        task_type='PROJECT_WBS',
        source_type='MANUAL',

        project_id=task_data.project_id,
        project_code=project.project_code,
        project_name=project.project_name,
        wbs_code=task_data.wbs_code,

        assignee_id=current_user.id,
        assignee_name=current_user.real_name,
        assigner_id=current_user.id,
        assigner_name=current_user.real_name,

        plan_start_date=task_data.plan_start_date,
        plan_end_date=task_data.plan_end_date,
        deadline=task_data.deadline,

        estimated_hours=task_data.estimated_hours,
        actual_hours=0,

        status=initial_status,
        progress=0,
        priority=task_data.priority,

        approval_required=approval_required,
        approval_status=approval_status,
        task_importance=task_data.task_importance,

        tags=task_data.tags,
        category=task_data.category,

        created_by=current_user.id,
        updated_by=current_user.id
    )

    db.add(new_task)
    db.flush()

    # 如果是IMPORTANT任务，创建审批工作流
    if task_data.task_importance == 'IMPORTANT':
        approval_workflow = TaskApprovalWorkflow(
            task_id=new_task.id,
            submitted_by=current_user.id,
            submitted_at=datetime.now(),
            submit_note=task_data.justification,
            approver_id=project.pm_id,  # 项目经理
            approval_status='PENDING',
            task_details={
                'title': task_data.title,
                'description': task_data.description,
                'estimated_hours': float(task_data.estimated_hours) if task_data.estimated_hours else None
            }
        )
        db.add(approval_workflow)

        # TODO: 发送通知给PM

    db.commit()
    db.refresh(new_task)

    # 构建响应
    response = schemas.TaskResponse.model_validate(new_task)
    response.proof_count = 0  # 新任务没有证明

    return response


# ==================== 进度更新 ====================

@router.put("/tasks/{task_id}/progress", response_model=schemas.ProgressUpdateResponse)
def update_task_progress(
    task_id: int,
    progress_data: schemas.ProgressUpdateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
):
    """
    更新任务进度（自动触发项目/阶段进度聚合）
    """
    # 获取任务
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证权限
    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能更新自己的任务")

    # 更新进度
    old_progress = task.progress
    task.progress = progress_data.progress

    if progress_data.actual_hours is not None:
        task.actual_hours = progress_data.actual_hours

    # 状态自动转换
    if progress_data.progress > 0 and task.status == 'ACCEPTED':
        task.status = 'IN_PROGRESS'
        task.actual_start_date = date.today()

    if progress_data.progress == 100:
        task.status = 'COMPLETED'
        task.actual_end_date = date.today()

    task.updated_by = current_user.id
    task.updated_at = datetime.now()

    db.commit()

    # 创建进度日志
    if progress_data.progress_note:
        create_progress_log(
            db,
            task_id=task.id,
            progress=progress_data.progress,
            actual_hours=float(progress_data.actual_hours) if progress_data.actual_hours else None,
            note=progress_data.progress_note,
            updater_id=current_user.id
        )

    # 触发进度聚合
    aggregation_result = aggregate_task_progress(db, task.id)

    return schemas.ProgressUpdateResponse(
        task_id=task.id,
        progress=task.progress,
        actual_hours=task.actual_hours,
        status=task.status,
        project_progress_updated=aggregation_result['project_progress_updated'],
        stage_progress_updated=aggregation_result['stage_progress_updated']
    )


# ==================== 完成任务 ====================

@router.put("/tasks/{task_id}/complete", response_model=schemas.TaskCompleteResponse)
def complete_task(
    task_id: int,
    complete_data: schemas.TaskCompleteRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
):
    """
    完成任务（含证明材料验证）
    """
    # 获取任务
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证权限
    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能完成自己的任务")

    # 验证证明材料（重要任务必须有证明）
    if task.task_importance == 'IMPORTANT' and not complete_data.skip_proof_validation:
        proof_count = db.query(TaskCompletionProof).filter(
            TaskCompletionProof.task_id == task_id
        ).count()

        if proof_count == 0:
            raise HTTPException(
                status_code=400,
                detail="重要任务必须上传至少1个完成证明材料"
            )

    # 更新任务
    task.status = 'COMPLETED'
    task.progress = 100
    task.actual_end_date = date.today()
    task.completion_note = complete_data.completion_note
    task.updated_by = current_user.id
    task.updated_at = datetime.now()

    db.commit()

    # 触发进度聚合
    aggregate_task_progress(db, task.id)

    # TODO: 发送通知

    proof_count = db.query(TaskCompletionProof).filter(
        TaskCompletionProof.task_id == task_id
    ).count()

    return schemas.TaskCompleteResponse(
        task_id=task.id,
        status=task.status,
        progress=task.progress,
        actual_end_date=task.actual_end_date,
        completion_note=task.completion_note,
        proof_count=proof_count
    )


# ==================== 上传完成证明 ====================

@router.post("/tasks/{task_id}/completion-proofs/upload", response_model=schemas.ProofUploadResponse)
async def upload_completion_proof(
    task_id: int,
    file: UploadFile = File(...),
    proof_type: str = Form(...),
    file_category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
):
    """
    上传任务完成证明材料
    """
    # 验证任务
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能为自己的任务上传证明")

    # 验证proof_type
    valid_proof_types = ['DOCUMENT', 'PHOTO', 'VIDEO', 'TEST_REPORT', 'DATA']
    if proof_type not in valid_proof_types:
        raise HTTPException(status_code=400, detail=f"无效的证明类型，必须是: {', '.join(valid_proof_types)}")

    # 保存文件
    upload_dir = f"uploads/task_proofs/{task_id}"
    os.makedirs(upload_dir, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)

    # 写入文件
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    file_size = len(content)

    # 创建证明记录
    proof = TaskCompletionProof(
        task_id=task_id,
        proof_type=proof_type,
        file_category=file_category,
        file_path=file_path,
        file_name=file.filename,
        file_size=file_size,
        file_type=file_ext.lstrip('.'),
        description=description,
        uploaded_by=current_user.id,
        uploaded_at=datetime.now()
    )

    db.add(proof)
    db.commit()
    db.refresh(proof)

    return schemas.ProofUploadResponse.model_validate(proof)


# ==================== 报告延期 ====================

@router.post("/tasks/{task_id}/report-delay", response_model=schemas.DelayReportResponse)
def report_task_delay(
    task_id: int,
    delay_data: schemas.DelayReportRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
):
    """
    报告任务延期（创建异常事件，自动通知相关方）
    """
    # 获取任务
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证权限
    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能报告自己任务的延期")

    # 更新任务延期信息
    task.is_delayed = True
    task.delay_reason = delay_data.delay_reason
    task.delay_responsibility = delay_data.delay_responsibility
    task.delay_impact_scope = delay_data.delay_impact_scope
    task.new_completion_date = delay_data.new_completion_date
    task.delay_reported_at = datetime.now()
    task.delay_reported_by = current_user.id
    task.updated_at = datetime.now()

    db.commit()

    # 创建异常事件
    exception_event = ExceptionEvent(
        event_no=f"EXC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        event_type='SCHEDULE_DELAY',
        severity='MEDIUM' if delay_data.schedule_impact_days <= 5 else 'HIGH',
        source_type='TASK_DELAY',
        source_id=task_id,
        project_id=task.project_id,
        title=f"任务延期：{task.title}",
        description=delay_data.delay_reason,
        discovered_at=datetime.now(),
        discovered_by=current_user.id,
        impact_scope=delay_data.delay_impact_scope,
        impact_description=f"延期{delay_data.schedule_impact_days}天",
        schedule_impact=delay_data.schedule_impact_days,
        cost_impact=delay_data.cost_impact,
        root_cause=delay_data.root_cause_analysis,
        preventive_measures=delay_data.preventive_measures,
        status='OPEN'
    )

    db.add(exception_event)
    db.commit()
    db.refresh(exception_event)

    # 确定可见范围和通知对象
    visible_roles = []
    notifications_count = 0

    if delay_data.delay_impact_scope == 'LOCAL':
        visible_roles = ['PROJECT_TEAM']
        notifications_count = 1
    elif delay_data.delay_impact_scope == 'PROJECT':
        visible_roles = ['PROJECT_TEAM', 'DEPT_HEAD', 'PM']
        notifications_count = 3
    elif delay_data.delay_impact_scope == 'MULTI_PROJECT':
        visible_roles = ['PROJECT_TEAM', 'DEPT_HEAD', 'PM', 'PMO', 'MANAGEMENT']
        notifications_count = 5

    # TODO: 实际发送通知

    # 检查是否需要更新项目健康度
    aggregate_task_progress(db, task.id)

    return schemas.DelayReportResponse(
        task_id=task.id,
        exception_event_id=exception_event.id,
        delay_visible_to=visible_roles,
        notifications_sent_count=notifications_count,
        health_status_updated=True
    )


# ==================== PM审批端点 ====================

@router.get("/tasks/pending-approval", response_model=schemas.TaskListResponse)
def get_pending_approval_tasks(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
):
    """
    获取待我审批的任务列表（PM视图）
    """
    # 查询当前用户作为PM的项目
    pm_projects = db.query(Project).filter(Project.pm_id == current_user.id).all()
    project_ids = [p.id for p in pm_projects]

    # 查询待审批任务
    query = db.query(TaskUnified).filter(
        and_(
            TaskUnified.project_id.in_(project_ids),
            TaskUnified.approval_status == 'PENDING_APPROVAL',
            TaskUnified.approval_required == True
        )
    ).order_by(TaskUnified.created_at.desc())

    total = query.count()
    tasks = query.offset((page - 1) * page_size).limit(page_size).all()

    # 构建响应
    items = []
    for task in tasks:
        proof_count = db.query(TaskCompletionProof).filter(
            TaskCompletionProof.task_id == task.id
        ).count()

        task_response = schemas.TaskResponse.model_validate(task)
        task_response.proof_count = proof_count
        items.append(task_response)

    pages = (total + page_size - 1) // page_size

    return schemas.TaskListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.put("/tasks/{task_id}/approve", response_model=schemas.TaskApprovalResponse)
def approve_task(
    task_id: int,
    approval_data: schemas.TaskApprovalRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
):
    """
    批准任务（PM操作）
    """
    # 获取任务
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证审批权限
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project or project.pm_id != current_user.id:
        raise HTTPException(status_code=403, detail="您没有权限审批此任务")

    # 验证任务状态
    if task.approval_status != 'PENDING_APPROVAL':
        raise HTTPException(status_code=400, detail="任务不在待审批状态")

    # 更新任务状态
    task.approval_status = 'APPROVED'
    task.approved_by = current_user.id
    task.approved_at = datetime.now()
    task.approval_note = approval_data.approval_note
    task.status = 'ACCEPTED'  # 审批通过后，任务可以开始执行
    task.updated_at = datetime.now()

    # 更新审批工作流
    workflow = db.query(TaskApprovalWorkflow).filter(
        and_(
            TaskApprovalWorkflow.task_id == task_id,
            TaskApprovalWorkflow.approval_status == 'PENDING'
        )
    ).first()

    if workflow:
        workflow.approval_status = 'APPROVED'
        workflow.approver_id = current_user.id
        workflow.approved_at = datetime.now()
        workflow.approval_note = approval_data.approval_note

    db.commit()

    # TODO: 发送通知给任务执行人

    return schemas.TaskApprovalResponse(
        task_id=task.id,
        approval_status=task.approval_status,
        approved_by=current_user.id,
        approved_at=task.approved_at,
        approval_note=task.approval_note
    )


@router.put("/tasks/{task_id}/reject", response_model=schemas.TaskApprovalResponse)
def reject_task(
    task_id: int,
    rejection_data: schemas.TaskRejectionRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
):
    """
    拒绝任务（PM操作）
    """
    # 获取任务
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证审批权限
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project or project.pm_id != current_user.id:
        raise HTTPException(status_code=403, detail="您没有权限审批此任务")

    # 验证任务状态
    if task.approval_status != 'PENDING_APPROVAL':
        raise HTTPException(status_code=400, detail="任务不在待审批状态")

    # 更新任务状态
    task.approval_status = 'REJECTED'
    task.approved_by = current_user.id
    task.approved_at = datetime.now()
    task.approval_note = rejection_data.rejection_reason
    task.status = 'CANCELLED'  # 审批拒绝后，任务取消
    task.updated_at = datetime.now()

    # 更新审批工作流
    workflow = db.query(TaskApprovalWorkflow).filter(
        and_(
            TaskApprovalWorkflow.task_id == task_id,
            TaskApprovalWorkflow.approval_status == 'PENDING'
        )
    ).first()

    if workflow:
        workflow.approval_status = 'REJECTED'
        workflow.approver_id = current_user.id
        workflow.approved_at = datetime.now()
        workflow.rejection_reason = rejection_data.rejection_reason

    db.commit()

    # TODO: 发送通知给任务创建人

    return schemas.TaskApprovalResponse(
        task_id=task.id,
        approval_status=task.approval_status,
        approved_by=current_user.id,
        approved_at=task.approved_at,
        approval_note=task.approval_note
    )


@router.get("/tasks/{task_id}/approval-history", response_model=List[dict])
def get_task_approval_history(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
):
    """
    获取任务审批历史
    """
    # 验证任务存在
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证权限（任务相关人员可查看）
    if task.assignee_id != current_user.id and task.created_by != current_user.id:
        project = db.query(Project).filter(Project.id == task.project_id).first()
        if not project or project.pm_id != current_user.id:
            raise HTTPException(status_code=403, detail="没有权限查看审批历史")

    # 查询审批历史
    workflows = db.query(TaskApprovalWorkflow).filter(
        TaskApprovalWorkflow.task_id == task_id
    ).order_by(TaskApprovalWorkflow.submitted_at.desc()).all()

    # 构建响应
    history = []
    for wf in workflows:
        submitter = db.query(User).filter(User.id == wf.submitted_by).first()
        approver = db.query(User).filter(User.id == wf.approver_id).first() if wf.approver_id else None

        history.append({
            "id": wf.id,
            "submitted_by": submitter.real_name if submitter else None,
            "submitted_at": wf.submitted_at,
            "submit_note": wf.submit_note,
            "approver": approver.real_name if approver else None,
            "approval_status": wf.approval_status,
            "approved_at": wf.approved_at,
            "approval_note": wf.approval_note,
            "rejection_reason": wf.rejection_reason
        })

    return history


# ==================== 证明材料管理 ====================

@router.get("/tasks/{task_id}/completion-proofs", response_model=schemas.TaskProofListResponse)
def get_task_completion_proofs(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
):
    """
    获取任务的所有完成证明材料
    """
    # 验证任务存在
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证权限（任务相关人员可查看）
    if task.assignee_id != current_user.id and task.created_by != current_user.id:
        project = db.query(Project).filter(Project.id == task.project_id).first()
        if not project or project.pm_id != current_user.id:
            raise HTTPException(status_code=403, detail="没有权限查看证明材料")

    # 查询证明材料
    proofs = db.query(TaskCompletionProof).filter(
        TaskCompletionProof.task_id == task_id
    ).order_by(TaskCompletionProof.uploaded_at.desc()).all()

    # 构建响应
    proof_responses = [schemas.ProofUploadResponse.model_validate(p) for p in proofs]

    return schemas.TaskProofListResponse(
        task_id=task_id,
        proofs=proof_responses,
        total_count=len(proof_responses)
    )


@router.delete("/tasks/{task_id}/completion-proofs/{proof_id}")
def delete_completion_proof(
    task_id: int,
    proof_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
):
    """
    删除任务完成证明材料
    """
    # 获取证明材料
    proof = db.query(TaskCompletionProof).filter(
        and_(
            TaskCompletionProof.id == proof_id,
            TaskCompletionProof.task_id == task_id
        )
    ).first()

    if not proof:
        raise HTTPException(status_code=404, detail="证明材料不存在")

    # 验证任务
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证权限（只有上传者和任务执行人可以删除）
    if proof.uploaded_by != current_user.id and task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="没有权限删除此证明材料")

    # 删除文件
    if os.path.exists(proof.file_path):
        try:
            os.remove(proof.file_path)
        except Exception as e:
            print(f"Warning: Could not delete file {proof.file_path}: {e}")

    # 删除数据库记录
    db.delete(proof)
    db.commit()

    return {"message": "证明材料已删除", "proof_id": proof_id}


# ==================== 任务列表查询（工程师视图） ====================

@router.get("/tasks", response_model=schemas.TaskListResponse)
def get_my_tasks(
    page: int = 1,
    page_size: int = 20,
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    is_delayed: Optional[bool] = None,
    is_overdue: Optional[bool] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
):
    """
    获取我的任务列表（支持多种筛选条件）
    """
    # 构建查询
    query = db.query(TaskUnified).filter(
        TaskUnified.assignee_id == current_user.id
    )

    # 应用筛选条件
    if project_id:
        query = query.filter(TaskUnified.project_id == project_id)

    if status:
        query = query.filter(TaskUnified.status == status)

    if priority:
        query = query.filter(TaskUnified.priority == priority)

    if is_delayed is not None:
        query = query.filter(TaskUnified.is_delayed == is_delayed)

    if is_overdue is not None:
        # 逾期任务：截止时间<当前时间 且 状态不是已完成/已取消
        if is_overdue:
            query = query.filter(
                and_(
                    TaskUnified.deadline < datetime.now(),
                    TaskUnified.status.notin_(['COMPLETED', 'CANCELLED'])
                )
            )
        else:
            # 未逾期任务
            query = query.filter(
                or_(
                    TaskUnified.deadline >= datetime.now(),
                    TaskUnified.deadline.is_(None),
                    TaskUnified.status.in_(['COMPLETED', 'CANCELLED'])
                )
            )

    # 排序：优先级+截止时间
    query = query.order_by(
        TaskUnified.priority.desc(),
        TaskUnified.deadline.asc()
    )

    total = query.count()
    tasks = query.offset((page - 1) * page_size).limit(page_size).all()

    # 构建响应
    items = []
    for task in tasks:
        proof_count = db.query(TaskCompletionProof).filter(
            TaskCompletionProof.task_id == task.id
        ).count()

        task_response = schemas.TaskResponse.model_validate(task)
        task_response.proof_count = proof_count
        items.append(task_response)

    pages = (total + page_size - 1) // page_size

    return schemas.TaskListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
def get_task_detail(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
):
    """
    获取任务详情
    """
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证权限（任务相关人员可查看）
    if task.assignee_id != current_user.id and task.created_by != current_user.id:
        project = db.query(Project).filter(Project.id == task.project_id).first()
        if not project or project.pm_id != current_user.id:
            raise HTTPException(status_code=403, detail="没有权限查看此任务")

    # 获取证明数量
    proof_count = db.query(TaskCompletionProof).filter(
        TaskCompletionProof.task_id == task_id
    ).count()

    task_response = schemas.TaskResponse.model_validate(task)
    task_response.proof_count = proof_count

    return task_response


# ==================== 跨部门进度视图 ====================

@router.get("/projects/{project_id}/progress-visibility", response_model=schemas.ProjectProgressVisibilityResponse)
def get_project_progress_visibility(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
):
    """
    获取项目的跨部门进度视图
    解决痛点：各部门可以看到彼此的工作进度
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 验证权限（项目成员可查看）
    is_member = db.query(ProjectMember).filter(
        and_(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
            ProjectMember.is_active == True
        )
    ).first()

    if not is_member and project.pm_id != current_user.id:
        raise HTTPException(status_code=403, detail="没有权限查看此项目进度")

    # 获取项目所有任务
    all_tasks = db.query(TaskUnified).filter(
        TaskUnified.project_id == project_id
    ).all()

    # 按部门分组统计
    from collections import defaultdict
    dept_stats = defaultdict(lambda: {
        'department_id': 0,
        'department_name': '',
        'total_tasks': 0,
        'completed_tasks': 0,
        'in_progress_tasks': 0,
        'delayed_tasks': 0,
        'members': defaultdict(lambda: {'name': '', 'total_tasks': 0, 'completed': 0, 'in_progress': 0})
    })

    for task in all_tasks:
        if task.assignee_id:
            # 获取用户信息
            user = db.query(User).filter(User.id == task.assignee_id).first()
            if user and user.department:
                dept_name = user.department

                # 部门统计
                dept_stats[dept_name]['department_name'] = dept_name
                dept_stats[dept_name]['total_tasks'] += 1

                if task.status == 'COMPLETED':
                    dept_stats[dept_name]['completed_tasks'] += 1
                elif task.status == 'IN_PROGRESS':
                    dept_stats[dept_name]['in_progress_tasks'] += 1

                if task.is_delayed:
                    dept_stats[dept_name]['delayed_tasks'] += 1

                # 人员统计
                member_key = user.real_name or user.username
                dept_stats[dept_name]['members'][member_key]['name'] = member_key
                dept_stats[dept_name]['members'][member_key]['total_tasks'] += 1

                if task.status == 'COMPLETED':
                    dept_stats[dept_name]['members'][member_key]['completed'] += 1
                elif task.status == 'IN_PROGRESS':
                    dept_stats[dept_name]['members'][member_key]['in_progress'] += 1

    # 构建部门进度响应
    department_progress = []
    for idx, (dept_name, stats) in enumerate(dept_stats.items(), 1):
        # 计算部门进度
        total = stats['total_tasks']
        completed = stats['completed_tasks']
        progress_pct = (completed / total * 100) if total > 0 else 0

        # 构建成员列表
        members = [
            schemas.MemberProgressSummary(
                name=m['name'],
                total_tasks=m['total_tasks'],
                completed_tasks=m['completed'],
                in_progress_tasks=m['in_progress'],
                progress_pct=(m['completed'] / m['total_tasks'] * 100) if m['total_tasks'] > 0 else 0
            )
            for m in stats['members'].values()
        ]

        department_progress.append(schemas.DepartmentProgressSummary(
            department_id=idx,
            department_name=dept_name,
            total_tasks=stats['total_tasks'],
            completed_tasks=stats['completed_tasks'],
            in_progress_tasks=stats['in_progress_tasks'],
            delayed_tasks=stats['delayed_tasks'],
            progress_pct=round(progress_pct, 2),
            members=members
        ))

    # 阶段进度统计
    from app.models.project import ProjectStage
    stages = db.query(ProjectStage).filter(
        ProjectStage.project_id == project_id
    ).all()

    stage_progress = {}
    for stage in stages:
        stage_progress[stage.stage_code] = schemas.StageProgressSummary(
            progress=float(stage.progress_pct) if stage.progress_pct else 0.0,
            status=stage.status
        )

    # 活跃延期列表
    delayed_tasks = [t for t in all_tasks if t.is_delayed and t.status not in ['COMPLETED', 'CANCELLED']]

    active_delays = []
    for task in delayed_tasks:
        user = db.query(User).filter(User.id == task.assignee_id).first()

        # 计算延期天数
        delay_days = 0
        if task.deadline and task.new_completion_date:
            delay_days = (task.new_completion_date - task.deadline.date()).days

        active_delays.append(schemas.ActiveDelayInfo(
            task_id=task.id,
            task_title=task.title,
            assignee_name=user.real_name if user else "未知",
            department=user.department if user else "未知",
            delay_days=delay_days,
            impact_scope=task.delay_impact_scope or "LOCAL",
            new_completion_date=task.new_completion_date or date.today(),
            delay_reason=task.delay_reason or "",
            reported_at=task.delay_reported_at or datetime.now()
        ))

    # 整体进度
    overall_progress = float(project.progress_pct) if project.progress_pct else 0.0

    return schemas.ProjectProgressVisibilityResponse(
        project_id=project.id,
        project_name=project.project_name,
        overall_progress=overall_progress,
        department_progress=department_progress,
        stage_progress=stage_progress,
        active_delays=active_delays,
        last_updated_at=datetime.now()
    )
