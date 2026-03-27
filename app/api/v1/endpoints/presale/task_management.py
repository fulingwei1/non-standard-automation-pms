# -*- coding: utf-8 -*-
"""
售前任务管理增强 API
端点:
- POST /api/v1/presale/tasks/auto-assign — 工单自动分配
- GET  /api/v1/presale/tasks/workload   — 工作量视图
- POST /api/v1/presale/tasks/batch-update — 批量更新状态
- GET  /api/v1/presale/tasks/{id}/timeline — 任务进度时间轴
"""
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.presale import (
    PresaleSupportTicket,
    PresaleTicketProgress,
)
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/tasks", tags=["presale-task-management"])


# ==================== Schemas ====================


class AutoAssignRequest(BaseModel):
    """自动分配请求"""
    ticket_ids: List[int] = Field(..., description="待分配的工单 ID 列表")
    candidate_user_ids: Optional[List[int]] = Field(
        None, description="候选处理人 ID 列表（为空则自动选择所有售前人员）"
    )


class AutoAssignResult(BaseModel):
    """单条分配结果"""
    ticket_id: int
    ticket_no: str
    assigned_to_id: Optional[int] = None
    assigned_to_name: Optional[str] = None
    reason: str


class BatchUpdateRequest(BaseModel):
    """批量更新请求"""
    ticket_ids: List[int] = Field(..., description="工单 ID 列表")
    action: str = Field(
        ..., description="操作类型: complete / assign / cancel"
    )
    assignee_id: Optional[int] = Field(
        None, description="批量分配时的目标处理人 ID"
    )
    notes: Optional[str] = Field(None, description="操作备注")


# ==================== 1. 自动分配 ====================


@router.post("/auto-assign", response_model=ResponseModel)
def auto_assign_tickets(
    req: AutoAssignRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    工单自动分配

    算法：区域匹配 + 产品匹配 + 负载均衡
    1. 从候选人中筛选
    2. 计算每个候选人当前活跃工单数（负载）
    3. 对每张工单，优先匹配同部门/同区域候选人，再按负载最低分配
    """
    # 获取待分配工单
    tickets = (
        db.query(PresaleSupportTicket)
        .filter(PresaleSupportTicket.id.in_(req.ticket_ids))
        .all()
    )
    if not tickets:
        raise HTTPException(status_code=404, detail="未找到指定工单")

    # 获取候选人
    if req.candidate_user_ids:
        candidates = (
            db.query(User)
            .filter(User.id.in_(req.candidate_user_ids), User.is_active == True)
            .all()
        )
    else:
        candidates = db.query(User).filter(User.is_active == True).all()

    if not candidates:
        raise HTTPException(status_code=400, detail="无可用候选处理人")

    # 计算每个候选人的当前活跃工单数
    active_statuses = {"PENDING", "ACCEPTED", "PROCESSING", "REVIEW"}
    active_counts: Dict[int, int] = defaultdict(int)
    active_tickets = (
        db.query(
            PresaleSupportTicket.assignee_id,
            func.count(PresaleSupportTicket.id),
        )
        .filter(PresaleSupportTicket.status.in_(active_statuses))
        .group_by(PresaleSupportTicket.assignee_id)
        .all()
    )
    for uid, cnt in active_tickets:
        if uid:
            active_counts[uid] = cnt

    # 构建候选人查找表
    candidate_map = {u.id: u for u in candidates}

    results: List[Dict] = []
    now = datetime.now()

    for ticket in tickets:
        # 跳过已分配 / 已完成的工单
        if ticket.status not in ("PENDING",):
            results.append({
                "ticket_id": ticket.id,
                "ticket_no": ticket.ticket_no,
                "assigned_to_id": ticket.assignee_id,
                "assigned_to_name": ticket.assignee_name,
                "reason": f"工单状态为 {ticket.status}，跳过分配",
            })
            continue

        # 评分：负载越低分越高
        best_candidate = None
        best_score = -1

        for uid, user in candidate_map.items():
            score = 100 - active_counts.get(uid, 0) * 10

            # 部门匹配加分（模拟区域匹配）
            if ticket.applicant_dept and user.department and ticket.applicant_dept == user.department:
                score += 20

            # 同类工单经验加分（查历史完成工单）
            if score > best_score:
                best_score = score
                best_candidate = user

        if best_candidate:
            ticket.assignee_id = best_candidate.id
            ticket.assignee_name = best_candidate.real_name or best_candidate.username
            ticket.status = "ACCEPTED"
            ticket.accept_time = now
            active_counts[best_candidate.id] = active_counts.get(best_candidate.id, 0) + 1

            # 记录进度
            progress = PresaleTicketProgress(
                ticket_id=ticket.id,
                progress_type="ASSIGN",
                content=f"系统自动分配给 {ticket.assignee_name}（负载均衡）",
                operator_id=current_user.id,
                operator_name=current_user.real_name or current_user.username,
            )
            db.add(progress)

            results.append({
                "ticket_id": ticket.id,
                "ticket_no": ticket.ticket_no,
                "assigned_to_id": best_candidate.id,
                "assigned_to_name": ticket.assignee_name,
                "reason": f"自动分配（当前负载: {active_counts[best_candidate.id]} 单）",
            })
        else:
            results.append({
                "ticket_id": ticket.id,
                "ticket_no": ticket.ticket_no,
                "assigned_to_id": None,
                "assigned_to_name": None,
                "reason": "无合适候选人",
            })

    db.commit()

    assigned_count = sum(1 for r in results if r["assigned_to_id"] is not None and "自动分配" in r["reason"])
    return ResponseModel(
        code=200,
        message="success",
        data={
            "total": len(results),
            "assigned": assigned_count,
            "skipped": len(results) - assigned_count,
            "details": results,
        },
    )


# ==================== 2. 工作量视图 ====================


@router.get("/workload", response_model=ResponseModel)
def get_team_workload(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    团队工作量可视化

    实时查询每个售前人员的工单分布、工时、忙闲状态。
    """
    active_statuses = {"PENDING", "ACCEPTED", "PROCESSING", "REVIEW"}

    # 获取所有有工单记录的处理人
    assignee_ids = (
        db.query(PresaleSupportTicket.assignee_id)
        .filter(PresaleSupportTicket.assignee_id.isnot(None))
        .distinct()
        .all()
    )
    assignee_ids = [a[0] for a in assignee_ids]

    if not assignee_ids:
        return ResponseModel(code=200, message="success", data={"members": []})

    users = db.query(User).filter(User.id.in_(assignee_ids)).all()
    user_map = {u.id: u for u in users}

    # 获取所有相关工单
    all_tickets = (
        db.query(PresaleSupportTicket)
        .filter(PresaleSupportTicket.assignee_id.in_(assignee_ids))
        .all()
    )

    # 按处理人分组统计
    by_user: Dict[int, Dict] = defaultdict(lambda: {
        "pending": 0,
        "processing": 0,
        "completed": 0,
        "total_hours": 0.0,
        "overdue": 0,
        "tickets": [],
    })

    now = datetime.now()
    for t in all_tickets:
        uid = t.assignee_id
        if t.status == "PENDING":
            by_user[uid]["pending"] += 1
        elif t.status in ("ACCEPTED", "PROCESSING", "REVIEW"):
            by_user[uid]["processing"] += 1
        elif t.status in ("COMPLETED", "CLOSED"):
            by_user[uid]["completed"] += 1
        by_user[uid]["total_hours"] += float(t.actual_hours or 0)

        if t.status in active_statuses and t.deadline and t.deadline < now:
            by_user[uid]["overdue"] += 1

    members = []
    for uid, stats in by_user.items():
        user = user_map.get(uid)
        if not user:
            continue
        active_count = stats["pending"] + stats["processing"]
        # 忙闲判定：>=5 单为忙，>=3 单为适中，<3 单为闲
        if active_count >= 5:
            load_level = "busy"
        elif active_count >= 3:
            load_level = "moderate"
        else:
            load_level = "idle"

        members.append({
            "user_id": uid,
            "user_name": user.real_name or user.username,
            "department": user.department,
            "pending": stats["pending"],
            "processing": stats["processing"],
            "completed": stats["completed"],
            "overdue": stats["overdue"],
            "total_hours": round(stats["total_hours"], 2),
            "active_count": active_count,
            "load_level": load_level,
        })

    # 按活跃工单数降序
    members.sort(key=lambda x: -x["active_count"])

    # 汇总
    summary = {
        "total_members": len(members),
        "busy_count": sum(1 for m in members if m["load_level"] == "busy"),
        "moderate_count": sum(1 for m in members if m["load_level"] == "moderate"),
        "idle_count": sum(1 for m in members if m["load_level"] == "idle"),
    }

    return ResponseModel(
        code=200,
        message="success",
        data={"summary": summary, "members": members},
    )


# ==================== 3. 批量更新 ====================


@router.post("/batch-update", response_model=ResponseModel)
def batch_update_tickets(
    req: BatchUpdateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量更新工单状态

    支持操作：
    - complete: 批量完成
    - assign: 批量分配给指定人
    - cancel: 批量取消
    """
    allowed_actions = {"complete", "assign", "cancel"}
    if req.action not in allowed_actions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的操作: {req.action}，可选: {', '.join(allowed_actions)}",
        )

    tickets = (
        db.query(PresaleSupportTicket)
        .filter(PresaleSupportTicket.id.in_(req.ticket_ids))
        .all()
    )
    if not tickets:
        raise HTTPException(status_code=404, detail="未找到指定工单")

    now = datetime.now()
    operator_name = current_user.real_name or current_user.username
    success_ids = []
    failed = []

    # 如果是批量分配，先获取目标用户
    target_user = None
    if req.action == "assign":
        if not req.assignee_id:
            raise HTTPException(status_code=400, detail="批量分配需要指定 assignee_id")
        target_user = db.query(User).filter(User.id == req.assignee_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="目标处理人不存在")

    for ticket in tickets:
        try:
            if req.action == "complete":
                if ticket.status in ("COMPLETED", "CLOSED", "CANCELLED"):
                    failed.append({"ticket_id": ticket.id, "reason": f"状态为 {ticket.status}，无法完成"})
                    continue
                ticket.status = "COMPLETED"
                ticket.complete_time = now
                progress_type = "COMPLETE"
                content = f"批量操作：标记为已完成"

            elif req.action == "assign":
                ticket.assignee_id = target_user.id
                ticket.assignee_name = target_user.real_name or target_user.username
                if ticket.status == "PENDING":
                    ticket.status = "ACCEPTED"
                    ticket.accept_time = now
                progress_type = "ASSIGN"
                content = f"批量分配给 {ticket.assignee_name}"

            elif req.action == "cancel":
                if ticket.status in ("COMPLETED", "CLOSED", "CANCELLED"):
                    failed.append({"ticket_id": ticket.id, "reason": f"状态为 {ticket.status}，无法取消"})
                    continue
                ticket.status = "CANCELLED"
                progress_type = "CANCEL"
                content = f"批量取消"

            if req.notes:
                content += f"（备注: {req.notes}）"

            progress = PresaleTicketProgress(
                ticket_id=ticket.id,
                progress_type=progress_type,
                content=content,
                operator_id=current_user.id,
                operator_name=operator_name,
            )
            db.add(progress)
            success_ids.append(ticket.id)

        except Exception as e:
            failed.append({"ticket_id": ticket.id, "reason": str(e)})

    db.commit()

    return ResponseModel(
        code=200,
        message="success",
        data={
            "action": req.action,
            "total": len(tickets),
            "success": len(success_ids),
            "failed_count": len(failed),
            "success_ids": success_ids,
            "failed": failed,
        },
    )


# ==================== 4. 任务进度时间轴 ====================


@router.get("/{ticket_id}/timeline", response_model=ResponseModel)
def get_ticket_timeline(
    ticket_id: int = Path(..., description="工单ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    工单处理时间轴

    返回：
    - 工单处理时间轴（全部进度记录）
    - 各阶段耗时分析
    - 处理人变更历史
    - 关键节点记录
    """
    ticket = (
        db.query(PresaleSupportTicket)
        .filter(PresaleSupportTicket.id == ticket_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")

    # 获取全部进度记录
    progress_records = (
        db.query(PresaleTicketProgress)
        .filter(PresaleTicketProgress.ticket_id == ticket_id)
        .order_by(PresaleTicketProgress.created_at.asc())
        .all()
    )

    # ── 时间轴事件列表 ──
    timeline_events = []

    # 创建事件
    timeline_events.append({
        "event_type": "CREATE",
        "timestamp": ticket.apply_time.isoformat() if ticket.apply_time else ticket.created_at.isoformat(),
        "operator": ticket.applicant_name or f"user_{ticket.applicant_id}",
        "content": f"创建工单：{ticket.title}",
        "detail": {
            "ticket_type": ticket.ticket_type,
            "urgency": ticket.urgency,
            "customer_name": ticket.customer_name,
        },
    })

    # 接单事件
    if ticket.accept_time:
        timeline_events.append({
            "event_type": "ACCEPT",
            "timestamp": ticket.accept_time.isoformat(),
            "operator": ticket.assignee_name or f"user_{ticket.assignee_id}",
            "content": f"{ticket.assignee_name or '处理人'} 接单",
            "detail": None,
        })

    # 进度记录事件
    for p in progress_records:
        timeline_events.append({
            "event_type": p.progress_type,
            "timestamp": p.created_at.isoformat() if p.created_at else None,
            "operator": p.operator_name or f"user_{p.operator_id}",
            "content": p.content,
            "detail": {
                "progress_percent": p.progress_percent,
            } if p.progress_percent is not None else None,
        })

    # 完成事件
    if ticket.complete_time:
        timeline_events.append({
            "event_type": "COMPLETE",
            "timestamp": ticket.complete_time.isoformat(),
            "operator": ticket.assignee_name or "系统",
            "content": "工单完成",
            "detail": {
                "actual_hours": float(ticket.actual_hours) if ticket.actual_hours else None,
                "satisfaction_score": ticket.satisfaction_score,
            },
        })

    # 按时间排序
    timeline_events.sort(key=lambda x: x["timestamp"] or "")

    # ── 各阶段耗时分析 ──
    stage_duration = {}

    if ticket.apply_time and ticket.accept_time:
        wait_hours = (ticket.accept_time - ticket.apply_time).total_seconds() / 3600
        stage_duration["wait_for_accept"] = {
            "label": "等待接单",
            "hours": round(wait_hours, 2),
            "start": ticket.apply_time.isoformat(),
            "end": ticket.accept_time.isoformat(),
        }

    if ticket.accept_time and ticket.complete_time:
        process_hours = (ticket.complete_time - ticket.accept_time).total_seconds() / 3600
        stage_duration["processing"] = {
            "label": "处理中",
            "hours": round(process_hours, 2),
            "start": ticket.accept_time.isoformat(),
            "end": ticket.complete_time.isoformat(),
        }

    if ticket.apply_time:
        end_time = ticket.complete_time or datetime.now()
        total_hours = (end_time - ticket.apply_time).total_seconds() / 3600
        stage_duration["total"] = {
            "label": "总耗时",
            "hours": round(total_hours, 2),
            "start": ticket.apply_time.isoformat(),
            "end": end_time.isoformat(),
        }

    # ── 处理人变更历史 ──
    assignee_changes = []
    for p in progress_records:
        if p.progress_type == "ASSIGN":
            assignee_changes.append({
                "timestamp": p.created_at.isoformat() if p.created_at else None,
                "operator": p.operator_name,
                "content": p.content,
            })

    # ── 关键节点 ──
    key_milestones = []
    if ticket.apply_time:
        key_milestones.append({"event": "创建", "time": ticket.apply_time.isoformat()})
    if ticket.accept_time:
        key_milestones.append({"event": "接单", "time": ticket.accept_time.isoformat()})
    if ticket.complete_time:
        key_milestones.append({"event": "完成", "time": ticket.complete_time.isoformat()})
    if ticket.deadline:
        is_overdue = (
            ticket.status in ("PENDING", "ACCEPTED", "PROCESSING", "REVIEW")
            and ticket.deadline < datetime.now()
        )
        key_milestones.append({
            "event": "截止时间",
            "time": ticket.deadline.isoformat(),
            "is_overdue": is_overdue,
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "ticket": {
                "id": ticket.id,
                "ticket_no": ticket.ticket_no,
                "title": ticket.title,
                "status": ticket.status,
                "urgency": ticket.urgency,
                "assignee_name": ticket.assignee_name,
            },
            "timeline": timeline_events,
            "stage_duration": stage_duration,
            "assignee_changes": assignee_changes,
            "key_milestones": key_milestones,
        },
    )
