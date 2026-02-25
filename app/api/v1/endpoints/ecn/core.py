# -*- coding: utf-8 -*-
"""
ECN基础管理 API endpoints

包含：ECN列表、详情、创建、更新、提交、取消
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.ecn import Ecn, EcnEvaluation, EcnLog, EcnType
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.ecn import (
    EcnCreate,
    EcnResponse,
    EcnSubmit,
    EcnUpdate,
)
from app.services.ecn_auto_assign_service import auto_assign_evaluation
from app.services.ecn_notification import (
    notify_evaluation_assigned,
)

from .utils import build_ecn_list_response, build_ecn_response, generate_ecn_no
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/ecns", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_ecns(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（ECN编号/标题）"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    ecn_type: Optional[str] = Query(None, description="变更类型筛选"),
    ecn_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    current_user: User = Depends(security.require_permission("ecn:read")),
) -> Any:
    """
    获取ECN列表
    """
    query = db.query(Ecn)

    # 关键词搜索
    query = apply_keyword_filter(query, Ecn, keyword, ["ecn_no", "ecn_title"])

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
    if ecn_status:
        query = query.filter(Ecn.status == ecn_status)

    # 优先级筛选
    if priority:
        query = query.filter(Ecn.priority == priority)

    total = query.count()
    ecns = apply_pagination(query.order_by(desc(Ecn.created_at)), pagination.offset, pagination.limit).all()

    items = [build_ecn_list_response(db, ecn) for ecn in ecns]

    return pagination.to_response(items, total)


@router.get(
    "/ecns/{ecn_id}", response_model=EcnResponse, status_code=status.HTTP_200_OK
)
def read_ecn(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("ecn:read")),
) -> Any:
    """
    获取ECN详情
    """
    ecn = get_or_404(db, Ecn, ecn_id, "ECN不存在")

    return build_ecn_response(db, ecn)


@router.post("/ecns", response_model=EcnResponse, status_code=status.HTTP_201_CREATED)
def create_ecn(
    *,
    db: Session = Depends(deps.get_db),
    ecn_in: EcnCreate,
    current_user: User = Depends(security.require_permission("ecn:create")),
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

    return build_ecn_response(db, ecn)


@router.put(
    "/ecns/{ecn_id}", response_model=EcnResponse, status_code=status.HTTP_200_OK
)
def update_ecn(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    ecn_in: EcnUpdate,
    current_user: User = Depends(security.require_permission("ecn:update")),
) -> Any:
    """
    更新ECN
    """
    ecn = get_or_404(db, Ecn, ecn_id, "ECN不存在")

    if ecn.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能修改草稿状态的ECN")

    update_data = ecn_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ecn, field, value)

    db.add(ecn)
    db.commit()
    db.refresh(ecn)

    return build_ecn_response(db, ecn)


@router.put(
    "/ecns/{ecn_id}/submit", response_model=EcnResponse, status_code=status.HTTP_200_OK
)
def submit_ecn(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    submit_in: EcnSubmit,
    current_user: User = Depends(security.require_permission("ecn:submit")),
) -> Any:
    """
    提交ECN
    """
    ecn = get_or_404(db, Ecn, ecn_id, "ECN不存在")

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
        created_by=current_user.id,
    )
    db.add(log)

    # 自动触发评估流程：根据ECN类型获取需要评估的部门
    ecn_type_config = (
        db.query(EcnType).filter(EcnType.type_code == ecn.ecn_type).first()
    )
    if ecn_type_config and ecn_type_config.required_depts:
        ecn.status = "EVALUATING"
        preferred_evaluators = submit_in.preferred_evaluators or {}

        for dept in ecn_type_config.required_depts:
            # 创建评估记录（待评估）
            evaluation = EcnEvaluation(ecn_id=ecn_id, eval_dept=dept, status="PENDING")
            db.add(evaluation)

            # 分配评估任务：优先使用手动指定，否则自动分配
            try:
                evaluator_id = None

                # 1. 优先使用手动指定的评估人员
                if dept in preferred_evaluators:
                    evaluator_id = preferred_evaluators[dept]
                    # 验证用户是否存在且属于该部门
                    evaluator = (
                        db.query(User)
                        .filter(
                            User.id == evaluator_id,
                            User.department == dept,
                            User.is_active,
                        )
                        .first()
                    )
                    if not evaluator:
                        evaluator_id = (
                            None  # 如果用户不存在或不属于该部门，使用自动分配
                        )

                # 2. 如果没有手动指定或手动指定无效，则自动分配
                if not evaluator_id:
                    evaluator_id = auto_assign_evaluation(db, ecn, evaluation)

                # 3. 如果分配成功，设置评估人并发送通知
                if evaluator_id:
                    evaluation.evaluator_id = evaluator_id
                    # 发送通知
                    notify_evaluation_assigned(db, ecn, evaluation, evaluator_id)
            except Exception as e:
                logger.error(f"Failed to assign evaluation: {e}")

    db.add(ecn)
    db.commit()
    db.refresh(ecn)

    return build_ecn_response(db, ecn)


@router.put(
    "/ecns/{ecn_id}/cancel", response_model=EcnResponse, status_code=status.HTTP_200_OK
)
def cancel_ecn(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    cancel_reason: Optional[str] = Query(None, description="取消原因"),
    current_user: User = Depends(security.require_permission("ecn:cancel")),
) -> Any:
    """
    取消ECN
    """
    ecn = get_or_404(db, Ecn, ecn_id, "ECN不存在")

    if ecn.status in ["APPROVED", "EXECUTING", "COMPLETED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="该状态的ECN不能取消")

    old_status = ecn.status
    ecn.status = "CANCELLED"

    # 记录日志
    log = EcnLog(
        ecn_id=ecn_id,
        log_type="STATUS_CHANGE",
        log_action="CANCEL",
        old_status=old_status,
        new_status="CANCELLED",
        log_content=cancel_reason or "取消ECN",
        created_by=current_user.id,
    )
    db.add(log)

    db.add(ecn)
    db.commit()
    db.refresh(ecn)

    return build_ecn_response(db, ecn)
