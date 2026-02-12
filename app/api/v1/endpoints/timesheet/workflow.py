# -*- coding: utf-8 -*-
"""
工时审批工作流 API endpoints (统一审批引擎版)

提供工时审批的完整工作流功能：
- 提交审批
- 审批操作（通过/驳回）
- 撤回审批
- 查询审批状态
- 查询审批历史
"""

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.timesheet import Timesheet
from app.models.user import User
from app.models.approval import ApprovalInstance, ApprovalTask
from app.schemas.common import ResponseModel
from app.services.approval_engine import ApprovalEngineService

router = APIRouter(prefix="/timesheet/workflow", tags=["timesheet-workflow"])


# ==================== Request/Response Models ====================


class TimesheetSubmitRequest(BaseModel):
    """工时提交审批请求"""
    timesheet_ids: List[int] = Field(..., description="要提交的工时记录ID列表")
    comment: Optional[str] = Field(None, description="提交说明")


class TimesheetApprovalActionRequest(BaseModel):
    """工时审批操作请求"""
    action: str = Field(..., description="操作类型: APPROVE/REJECT")
    comment: Optional[str] = Field(None, description="审批意见")


class TimesheetBatchApprovalRequest(BaseModel):
    """批量审批请求"""
    task_ids: List[int] = Field(..., description="要审批的任务ID列表")
    action: str = Field(..., description="操作类型: APPROVE/REJECT")
    comment: Optional[str] = Field(None, description="审批意见")


class ApprovalTaskResponse(BaseModel):
    """审批任务响应"""
    id: int
    instance_id: int
    instance_no: Optional[str] = None
    title: Optional[str] = None
    entity_type: str
    entity_id: int
    status: str
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApprovalStatusResponse(BaseModel):
    """审批状态响应"""
    instance_id: Optional[int] = None
    instance_no: Optional[str] = None
    status: Optional[str] = None
    current_node_name: Optional[str] = None
    initiator_name: Optional[str] = None
    submitted_at: Optional[datetime] = None
    can_withdraw: bool = False


# ==================== API Endpoints ====================


@router.post("/submit", response_model=ResponseModel)
def submit_timesheets_for_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: TimesheetSubmitRequest,
    current_user: User = Depends(security.require_permission("timesheet:create")),
) -> Any:
    """
    提交工时审批

    将一条或多条工时记录提交给审批流程。
    只有草稿(DRAFT)或被驳回(REJECTED)状态的工时可以提交。
    """
    if not request.timesheet_ids:
        raise HTTPException(status_code=400, detail="请选择要提交的工时记录")

    engine = ApprovalEngineService(db)
    success_count = 0
    failed_items = []

    for timesheet_id in request.timesheet_ids:
        # 获取工时记录
        timesheet = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()

        if not timesheet:
            failed_items.append({"id": timesheet_id, "error": "工时记录不存在"})
            continue

        # 验证权限：只能提交自己的工时
        if timesheet.user_id != current_user.id:
            failed_items.append({"id": timesheet_id, "error": "无权提交此工时记录"})
            continue

        # 验证状态
        if timesheet.status not in ("DRAFT", "REJECTED"):
            failed_items.append({
                "id": timesheet_id,
                "error": f"当前状态({timesheet.status})不允许提交审批"
            })
            continue

        try:
            # 使用统一审批引擎提交
            engine.submit(
                template_code="TIMESHEET_APPROVAL",
                entity_type="TIMESHEET",
                entity_id=timesheet_id,
                form_data={
                    "hours": float(timesheet.hours) if timesheet.hours else 0,
                    "overtime_type": timesheet.overtime_type,
                    "project_id": timesheet.project_id,
                },
                initiator_id=current_user.id,
            )
            success_count += 1
        except ValueError as e:
            failed_items.append({"id": timesheet_id, "error": str(e)})
        except Exception as e:
            failed_items.append({"id": timesheet_id, "error": f"提交失败: {str(e)}"})

    if success_count == 0 and failed_items:
        raise HTTPException(
            status_code=400,
            detail=f"提交失败: {failed_items[0]['error']}"
        )

    return ResponseModel(
        code=200,
        message=f"提交完成：成功 {success_count} 条" + (
            f"，失败 {len(failed_items)} 条" if failed_items else ""
        ),
        data={
            "success_count": success_count,
            "failed_count": len(failed_items),
            "failed_items": failed_items,
        }
    )


@router.get("/pending-tasks", response_model=ResponseModel)
def get_pending_approval_tasks(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.require_permission("timesheet:approve")),
) -> Any:
    """
    获取待审批的工时任务

    返回当前用户需要审批的工时记录列表。
    """
    engine = ApprovalEngineService(db)
    result = engine.get_pending_tasks(
        user_id=current_user.id,
        page=pagination.page,
        page_size=pagination.page_size,
    )

    # 过滤出工时类型的任务
    timesheet_tasks = []
    for task in result["items"]:
        instance = task.instance
        if instance and instance.entity_type == "TIMESHEET":
            # 获取工时详情
            timesheet = db.query(Timesheet).filter(
                Timesheet.id == instance.entity_id
            ).first()

            timesheet_tasks.append({
                "task_id": task.id,
                "instance_id": instance.id,
                "instance_no": instance.instance_no,
                "title": instance.title,
                "entity_id": instance.entity_id,
                "initiator_name": instance.initiator_name,
                "submitted_at": instance.submitted_at,
                "timesheet": {
                    "id": timesheet.id,
                    "user_name": timesheet.user_name,
                    "project_name": timesheet.project_name,
                    "work_date": timesheet.work_date.isoformat() if timesheet.work_date else None,
                    "hours": float(timesheet.hours) if timesheet.hours else 0,
                    "overtime_type": timesheet.overtime_type,
                    "work_content": timesheet.work_content,
                } if timesheet else None,
            })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total": len(timesheet_tasks),
            "page": page,
            "page_size": page_size,
            "items": timesheet_tasks,
        }
    )


@router.post("/tasks/{task_id}/action", response_model=ResponseModel)
def process_approval_action(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    request: TimesheetApprovalActionRequest,
    current_user: User = Depends(security.require_permission("timesheet:approve")),
) -> Any:
    """
    处理工时审批操作

    支持的操作：
    - APPROVE: 审批通过
    - REJECT: 审批驳回（需要填写意见）
    """
    # 验证任务存在
    task = db.query(ApprovalTask).filter(ApprovalTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="审批任务不存在")

    # 验证任务状态
    if task.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"任务状态({task.status})不允许操作")

    # 验证是否为工时审批
    instance = task.instance
    if not instance or instance.entity_type != "TIMESHEET":
        raise HTTPException(status_code=400, detail="此任务不是工时审批")

    # 验证审批权限
    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="您不是此任务的审批人")

    engine = ApprovalEngineService(db)

    try:
        if request.action == "APPROVE":
            engine.approve(
                task_id=task_id,
                approver_id=current_user.id,
                comment=request.comment,
            )
            message = "审批通过"

        elif request.action == "REJECT":
            if not request.comment:
                raise HTTPException(status_code=400, detail="驳回时必须填写意见")

            engine.reject(
                task_id=task_id,
                approver_id=current_user.id,
                comment=request.comment,
            )
            message = "审批已驳回"

        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的操作类型: {request.action}"
            )

        return ResponseModel(
            code=200,
            message=message,
            data={"task_id": task_id}
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch-action", response_model=ResponseModel)
def batch_process_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: TimesheetBatchApprovalRequest,
    current_user: User = Depends(security.require_permission("timesheet:approve")),
) -> Any:
    """
    批量审批工时

    支持一次性通过或驳回多条工时记录。
    """
    if not request.task_ids:
        raise HTTPException(status_code=400, detail="请选择要审批的任务")

    if request.action not in ("APPROVE", "REJECT"):
        raise HTTPException(status_code=400, detail="操作类型必须是 APPROVE 或 REJECT")

    if request.action == "REJECT" and not request.comment:
        raise HTTPException(status_code=400, detail="驳回时必须填写意见")

    engine = ApprovalEngineService(db)
    success_count = 0
    failed_items = []

    for task_id in request.task_ids:
        task = db.query(ApprovalTask).filter(ApprovalTask.id == task_id).first()

        if not task:
            failed_items.append({"task_id": task_id, "error": "任务不存在"})
            continue

        if task.status != "PENDING":
            failed_items.append({
                "task_id": task_id,
                "error": f"任务状态({task.status})不允许操作"
            })
            continue

        if task.assignee_id != current_user.id:
            failed_items.append({"task_id": task_id, "error": "您不是此任务的审批人"})
            continue

        instance = task.instance
        if not instance or instance.entity_type != "TIMESHEET":
            failed_items.append({"task_id": task_id, "error": "不是工时审批任务"})
            continue

        try:
            if request.action == "APPROVE":
                engine.approve(
                    task_id=task_id,
                    approver_id=current_user.id,
                    comment=request.comment,
                )
            else:
                engine.reject(
                    task_id=task_id,
                    approver_id=current_user.id,
                    comment=request.comment,
                )
            success_count += 1
        except Exception as e:
            failed_items.append({"task_id": task_id, "error": str(e)})

    action_name = "通过" if request.action == "APPROVE" else "驳回"
    return ResponseModel(
        code=200,
        message=f"批量{action_name}完成：成功 {success_count} 条" + (
            f"，失败 {len(failed_items)} 条" if failed_items else ""
        ),
        data={
            "success_count": success_count,
            "failed_count": len(failed_items),
            "failed_items": failed_items,
        }
    )


@router.get("/{timesheet_id}/status", response_model=ResponseModel)
def get_timesheet_approval_status(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_id: int,
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取工时审批状态

    查询指定工时记录的审批进度。
    """
    # 验证工时存在
    timesheet = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
    if not timesheet:
        raise HTTPException(status_code=404, detail="工时记录不存在")

    # 查找审批实例
    instance = (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == "TIMESHEET",
            ApprovalInstance.entity_id == timesheet_id,
        )
        .order_by(ApprovalInstance.created_at.desc())
        .first()
    )

    if not instance:
        return ResponseModel(
            code=200,
            message="success",
            data={
                "timesheet_id": timesheet_id,
                "timesheet_status": timesheet.status,
                "approval": None,
            }
        )

    # 判断是否可以撤回
    can_withdraw = (
        instance.status == "PENDING" and
        instance.initiator_id == current_user.id
    )

    # 获取当前节点名称
    current_node_name = None
    if instance.current_node_id:
        from app.models.approval import ApprovalNodeDefinition
        node = db.query(ApprovalNodeDefinition).filter(
            ApprovalNodeDefinition.id == instance.current_node_id
        ).first()
        if node:
            current_node_name = node.node_name

    return ResponseModel(
        code=200,
        message="success",
        data={
            "timesheet_id": timesheet_id,
            "timesheet_status": timesheet.status,
            "approval": {
                "instance_id": instance.id,
                "instance_no": instance.instance_no,
                "status": instance.status,
                "current_node_name": current_node_name,
                "initiator_name": instance.initiator_name,
                "submitted_at": instance.submitted_at.isoformat() if instance.submitted_at else None,
                "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
                "can_withdraw": can_withdraw,
            }
        }
    )


@router.post("/{timesheet_id}/withdraw", response_model=ResponseModel)
def withdraw_timesheet_approval(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_id: int,
    comment: Optional[str] = None,
    current_user: User = Depends(security.require_permission("timesheet:create")),
) -> Any:
    """
    撤回工时审批

    发起人可以在审批未完成前撤回审批申请。
    """
    # 验证工时存在
    timesheet = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
    if not timesheet:
        raise HTTPException(status_code=404, detail="工时记录不存在")

    # 验证权限：只能撤回自己的工时
    if timesheet.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权撤回此工时审批")

    # 查找审批实例
    instance = (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == "TIMESHEET",
            ApprovalInstance.entity_id == timesheet_id,
            ApprovalInstance.status == "PENDING",
        )
        .first()
    )

    if not instance:
        raise HTTPException(status_code=400, detail="没有进行中的审批可以撤回")

    engine = ApprovalEngineService(db)

    try:
        engine.withdraw(
            instance_id=instance.id,
            initiator_id=current_user.id,
            comment=comment,
        )

        return ResponseModel(
            code=200,
            message="审批已撤回",
            data={"timesheet_id": timesheet_id}
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{timesheet_id}/history", response_model=ResponseModel)
def get_timesheet_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_id: int,
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取工时审批历史

    返回指定工时记录的完整审批历史记录。
    """
    # 验证工时存在
    timesheet = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
    if not timesheet:
        raise HTTPException(status_code=404, detail="工时记录不存在")

    # 查找审批实例
    instance = (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == "TIMESHEET",
            ApprovalInstance.entity_id == timesheet_id,
        )
        .order_by(ApprovalInstance.created_at.desc())
        .first()
    )

    if not instance:
        return ResponseModel(
            code=200,
            message="success",
            data={"history": []}
        )

    # 获取审批日志
    from app.models.approval import ApprovalActionLog
    logs = (
        db.query(ApprovalActionLog)
        .filter(ApprovalActionLog.instance_id == instance.id)
        .order_by(ApprovalActionLog.created_at.asc())
        .all()
    )

    history = []
    for log in logs:
        history.append({
            "id": log.id,
            "action": log.action,
            "operator_name": log.operator_name,
            "comment": log.comment,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    return ResponseModel(
        code=200,
        message="success",
        data={"history": history}
    )
