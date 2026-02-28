# -*- coding: utf-8 -*-
"""
缺料预警 - 自动生成
从 assembly_kit.py 拆分
"""

# -*- coding: utf-8 -*-
"""
齐套分析模块 API 端点

基于装配工艺路径的智能齐套分析系统
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.models import (
    AssemblyStage,
    Machine,
    MaterialReadiness,
    Project,
    ShortageAlertRule,
    ShortageDetail,
)
from app.schemas.assembly_kit import (  # Stage; Template; Category Mapping; BOM Assembly Attrs; Readiness; Shortage; Alert Rule; Suggestion; Dashboard
    ShortageAlertItem,
    ShortageAlertListResponse,
)
from app.schemas.common import ResponseModel

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/assembly-kit/shortage-alerts",
    tags=["shortage_alerts"]
)

# 共 1 个路由

# ==================== 缺料预警 ====================

@router.get("/shortage-alerts", response_model=ResponseModel)
async def get_shortage_alerts(
    db: Session = Depends(deps.get_db),
    alert_level: Optional[str] = Query(None, description="预警级别(L1/L2/L3/L4)"),
    is_blocking: Optional[bool] = Query(None, description="是否阻塞性物料"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    pagination: PaginationParams = Depends(get_pagination_query)
):
    """获取缺料预警列表"""
    query = db.query(ShortageDetail).filter(ShortageDetail.shortage_qty > 0)

    if alert_level:
        query = query.filter(ShortageDetail.alert_level == alert_level)
    if is_blocking is not None:
        query = query.filter(ShortageDetail.is_blocking == is_blocking)
    if project_id:
        # 通过readiness关联项目
        readiness_ids = db.query(MaterialReadiness.id).filter(
            MaterialReadiness.project_id == project_id
        ).subquery()
        query = query.filter(ShortageDetail.readiness_id.in_(readiness_ids))

    total = query.count()

    # 统计各级别数量
    l1_count = query.filter(ShortageDetail.alert_level == "L1").count()
    l2_count = query.filter(ShortageDetail.alert_level == "L2").count()
    l3_count = query.filter(ShortageDetail.alert_level == "L3").count()
    l4_count = query.filter(ShortageDetail.alert_level == "L4").count()

    shortages = apply_pagination(query.order_by(
        ShortageDetail.alert_level,
        ShortageDetail.is_blocking.desc(),
        ShortageDetail.shortage_qty.desc()
    ), pagination.offset, pagination.limit).all()

    # 构建预警项
    alert_items = []
    stages = {s.stage_code: s for s in db.query(AssemblyStage).all()}

    for s in shortages:
        readiness = db.query(MaterialReadiness).filter(MaterialReadiness.id == s.readiness_id).first()
        if not readiness:
            continue

        project = db.query(Project).filter(Project.id == readiness.project_id).first()
        machine = db.query(Machine).filter(Machine.id == readiness.machine_id).first() if readiness.machine_id else None
        stage = stages.get(s.assembly_stage)

        # 获取响应时限
        rule = db.query(ShortageAlertRule).filter(ShortageAlertRule.alert_level == s.alert_level).first()
        response_hours = rule.response_deadline_hours if rule else 24

        alert_items.append(ShortageAlertItem(
            shortage_id=s.id,
            readiness_id=s.readiness_id,
            project_id=readiness.project_id,
            project_no=project.project_no if project else "",
            project_name=project.name if project else "",
            machine_id=readiness.machine_id,
            machine_no=machine.machine_no if machine else None,
            material_code=s.material_code,
            material_name=s.material_name,
            assembly_stage=s.assembly_stage,
            stage_name=stage.stage_name if stage else s.assembly_stage,
            is_blocking=s.is_blocking,
            required_qty=s.required_qty,
            shortage_qty=s.shortage_qty,
            alert_level=s.alert_level,
            expected_arrival_date=s.expected_arrival_date,
            days_to_required=7,  # 简化处理
            response_deadline=datetime.now() + timedelta(hours=response_hours)
        ))

    return ResponseModel(
        code=200,
        message="success",
        data=ShortageAlertListResponse(
            total=total,
            l1_count=l1_count,
            l2_count=l2_count,
            l3_count=l3_count,
            l4_count=l4_count,
            items=alert_items
        )
    )



