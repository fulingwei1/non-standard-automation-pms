# -*- coding: utf-8 -*-
"""
看板 - 自动生成
从 assembly_kit.py 拆分
"""

# -*- coding: utf-8 -*-
"""
齐套分析模块 API 端点

基于装配工艺路径的智能齐套分析系统
"""

import json
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.api import deps
from app.core import security
from app.models import (
    AssemblyStage, AssemblyTemplate, CategoryStageMapping,
    BomItemAssemblyAttrs, MaterialReadiness, ShortageDetail,
    ShortageAlertRule, SchedulingSuggestion,
    Project, Machine, BomHeader, BomItem, Material, MaterialCategory,
    User
)
from app.models.enums import (
    AssemblyStageEnum, ImportanceLevelEnum, ShortageAlertLevelEnum,
    SuggestionTypeEnum, SuggestionStatusEnum
)
from app.schemas.assembly_kit import (
    # Stage
    AssemblyStageCreate, AssemblyStageUpdate, AssemblyStageResponse,
    # Template
    AssemblyTemplateCreate, AssemblyTemplateUpdate, AssemblyTemplateResponse,
    # Category Mapping
    CategoryStageMappingCreate, CategoryStageMappingUpdate, CategoryStageMappingResponse,
    # BOM Assembly Attrs
    BomItemAssemblyAttrsCreate, BomItemAssemblyAttrsBatchCreate,
    BomItemAssemblyAttrsUpdate, BomItemAssemblyAttrsResponse,
    BomAssemblyAttrsAutoRequest, BomAssemblyAttrsTemplateRequest,
    # Readiness
    MaterialReadinessCreate, MaterialReadinessResponse, MaterialReadinessDetailResponse, StageKitRate,
    # Shortage
    ShortageDetailResponse, ShortageAlertItem, ShortageAlertListResponse,
    # Alert Rule
    ShortageAlertRuleCreate, ShortageAlertRuleUpdate, ShortageAlertRuleResponse,
    # Suggestion
    SchedulingSuggestionResponse, SchedulingSuggestionAccept, SchedulingSuggestionReject,
    # Dashboard
    AssemblyDashboardResponse, AssemblyDashboardStats, AssemblyDashboardStageStats
)
from app.schemas.common import ResponseModel, MessageResponse

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/assembly-kit/dashboard",
    tags=["dashboard"]
)

# 共 1 个路由

# ==================== 看板 ====================

def _calculate_dashboard_stats(recent_analyses):
    """计算看板基础统计"""
    total = len(recent_analyses)
    can_start = sum(1 for r in recent_analyses if r.can_start)
    not_ready = sum(1 for r in recent_analyses if r.blocking_kit_rate < 50)
    partial = total - can_start - not_ready
    avg_kit = sum(r.overall_kit_rate for r in recent_analyses) / total if total > 0 else Decimal(0)
    avg_blocking = sum(r.blocking_kit_rate for r in recent_analyses) / total if total > 0 else Decimal(0)
    return {
        'total': total, 'can_start': can_start, 'partial': partial,
        'not_ready': not_ready, 'avg_kit': avg_kit, 'avg_blocking': avg_blocking
    }


def _calculate_stage_stats(db, stages, recent_analyses, total_projects):
    """计算分阶段统计"""
    stage_stats = []
    for stage in stages:
        can_start, blocked, total_rate = 0, 0, Decimal(0)
        for r in recent_analyses:
            rate_info = (r.stage_kit_rates or {}).get(stage.stage_code, {})
            if rate_info.get("can_start", False):
                can_start += 1
            else:
                blocked += 1
            total_rate += Decimal(rate_info.get("kit_rate", 0))

        stage_stats.append(AssemblyDashboardStageStats(
            stage_code=stage.stage_code,
            stage_name=stage.stage_name,
            can_start_count=can_start,
            blocked_count=blocked,
            avg_kit_rate=round(total_rate / total_projects, 2) if total_projects > 0 else Decimal(0)
        ))
    return stage_stats


def _build_recent_analyses_list(db, recent_analyses, Project, BomHeader, Machine):
    """构建最近分析列表"""
    recent_list = []
    for r in recent_analyses[:10]:
        project = db.query(Project).filter(Project.id == r.project_id).first()
        bom = db.query(BomHeader).filter(BomHeader.id == r.bom_id).first()
        machine = db.query(Machine).filter(Machine.id == r.machine_id).first() if r.machine_id else None

        recent_list.append(MaterialReadinessResponse(
            id=r.id, readiness_no=r.readiness_no, project_id=r.project_id,
            machine_id=r.machine_id, bom_id=r.bom_id,
            check_date=r.planned_start_date or date.today(),
            overall_kit_rate=r.overall_kit_rate, blocking_kit_rate=r.blocking_kit_rate,
            can_start=r.can_start, first_blocked_stage=r.first_blocked_stage,
            estimated_ready_date=r.estimated_ready_date, stage_kit_rates=[],
            project_no=project.project_code if project else None,
            project_name=project.project_name if project else None,
            machine_no=machine.machine_code if machine else None,
            bom_no=bom.bom_no if bom else None,
            analysis_time=r.analysis_time, analyzed_by=r.analyzed_by, created_at=r.created_at
        ))
    return recent_list


@router.get("/dashboard", response_model=ResponseModel)
async def get_assembly_dashboard(
    db: Session = Depends(deps.get_db),
    project_ids: Optional[str] = Query(None, description="项目ID列表，逗号分隔")
):
    """获取装配齐套看板数据"""
    # 获取最近的齐套分析记录(每个项目取最新一条)
    subquery = db.query(
        MaterialReadiness.project_id,
        func.max(MaterialReadiness.id).label("max_id")
    ).group_by(MaterialReadiness.project_id).subquery()

    query = db.query(MaterialReadiness).join(
        subquery,
        and_(
            MaterialReadiness.project_id == subquery.c.project_id,
            MaterialReadiness.id == subquery.c.max_id
        )
    )

    if project_ids:
        ids = [int(x) for x in project_ids.split(",") if x.strip().isdigit()]
        if ids:
            query = query.filter(MaterialReadiness.project_id.in_(ids))

    recent_analyses = query.all()

    # 空数据返回
    if not recent_analyses:
        return ResponseModel(
            code=200, message="success",
            data=AssemblyDashboardResponse(
                stats=AssemblyDashboardStats(
                    total_projects=0, can_start_count=0, partial_ready_count=0,
                    not_ready_count=0, avg_kit_rate=Decimal(0), avg_blocking_rate=Decimal(0)
                ),
                stage_stats=[], alert_summary={"L1": 0, "L2": 0, "L3": 0, "L4": 0},
                recent_analyses=[], pending_suggestions=[]
            )
        )

    # 使用辅助函数计算统计数据
    stats = _calculate_dashboard_stats(recent_analyses)
    stages = db.query(AssemblyStage).filter(AssemblyStage.is_active == True).order_by(AssemblyStage.stage_order).all()
    stage_stats = _calculate_stage_stats(db, stages, recent_analyses, stats['total'])

    # 预警汇总
    alert_summary = {
        level: db.query(ShortageDetail).filter(
            ShortageDetail.alert_level == level, ShortageDetail.shortage_qty > 0
        ).count()
        for level in ["L1", "L2", "L3", "L4"]
    }

    # 构建响应数据
    recent_list = _build_recent_analyses_list(db, recent_analyses, Project, BomHeader, Machine)

    # 待处理建议
    pending_suggestions = db.query(SchedulingSuggestion).filter(
        SchedulingSuggestion.status == "pending"
    ).order_by(SchedulingSuggestion.priority_score.desc()).limit(5).all()

    suggestion_list = []
    for s in pending_suggestions:
        project = db.query(Project).filter(Project.id == s.project_id).first()
        machine = db.query(Machine).filter(Machine.id == s.machine_id).first() if s.machine_id else None

        data = SchedulingSuggestionResponse.model_validate(s)
        data.project_no = project.project_no if project else None
        data.project_name = project.name if project else None
        data.machine_no = machine.machine_no if machine else None
        suggestion_list.append(data)

    return ResponseModel(
        code=200,
        message="success",
        data=AssemblyDashboardResponse(
            stats=AssemblyDashboardStats(
                total_projects=stats['total'],
                can_start_count=stats['can_start'],
                partial_ready_count=stats['partial'],
                not_ready_count=stats['not_ready'],
                avg_kit_rate=round(stats['avg_kit'], 2),
                avg_blocking_rate=round(stats['avg_blocking'], 2)
            ),
            stage_stats=stage_stats,
            alert_summary=alert_summary,
            recent_analyses=recent_list,
            pending_suggestions=suggestion_list
        )
    )



