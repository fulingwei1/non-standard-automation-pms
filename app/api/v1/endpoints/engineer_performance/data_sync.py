# -*- coding: utf-8 -*-
"""
绩效数据自动同步 API 端点
"""

from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.debug_issue_sync_service import DebugIssueSyncService
from app.services.design_review_sync_service import DesignReviewSyncService
from app.services.knowledge_auto_identification_service import (
    KnowledgeAutoIdentificationService,
)
from app.services.work_log_auto_generator import WorkLogAutoGenerator

router = APIRouter(prefix="/data-sync", tags=["绩效数据同步"])


class SyncRequest(BaseModel):
    """同步请求"""
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    auto_submit: bool = Field(False, description="是否自动提交工作日志")


@router.post("/work-log/generate", summary="生成工作日志")
async def generate_work_logs(
    request: SyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从工时记录自动生成工作日志"""
    generator = WorkLogAutoGenerator(db)

    if request.start_date and request.end_date:
        stats = generator.batch_generate_work_logs(
            start_date=request.start_date,
            end_date=request.end_date,
            auto_submit=request.auto_submit
        )
    else:
        # 默认生成昨日工作日志
        stats = generator.generate_yesterday_work_logs(
            auto_submit=request.auto_submit
        )

    return ResponseModel(
        code=200,
        message="工作日志生成完成",
        data=stats
    )


@router.post("/design-review/sync", summary="同步设计评审")
async def sync_design_reviews(
    request: SyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从技术评审系统同步设计评审记录"""
    sync_service = DesignReviewSyncService(db)

    stats = sync_service.sync_all_completed_reviews(
        start_date=request.start_date,
        end_date=request.end_date
    )

    return ResponseModel(
        code=200,
        message="设计评审同步完成",
        data=stats
    )


@router.post("/debug-issue/sync", summary="同步调试问题")
async def sync_debug_issues(
    request: SyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从问题管理系统同步调试问题记录"""
    sync_service = DebugIssueSyncService(db)

    stats = sync_service.sync_all_project_issues(
        start_date=request.start_date,
        end_date=request.end_date
    )

    return ResponseModel(
        code=200,
        message="调试问题同步完成",
        data=stats
    )


@router.post("/knowledge/identify", summary="识别知识贡献")
async def identify_knowledge(
    request: SyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从服务工单和知识库自动识别知识贡献"""
    identification_service = KnowledgeAutoIdentificationService(db)

    ticket_stats = identification_service.batch_identify_from_service_tickets(
        start_date=request.start_date,
        end_date=request.end_date
    )

    kb_stats = identification_service.batch_identify_from_knowledge_base(
        start_date=request.start_date,
        end_date=request.end_date
    )

    return ResponseModel(
        code=200,
        message="知识贡献识别完成",
        data={
            'ticket_stats': ticket_stats,
            'kb_stats': kb_stats
        }
    )


@router.post("/all", summary="同步所有绩效数据")
async def sync_all_performance_data(
    request: SyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """同步所有绩效数据（工作日志、设计评审、调试问题、知识贡献）"""
    results = {}

    # 1. 生成工作日志
    generator = WorkLogAutoGenerator(db)
    if request.start_date and request.end_date:
        work_log_stats = generator.batch_generate_work_logs(
            start_date=request.start_date,
            end_date=request.end_date,
            auto_submit=request.auto_submit
        )
    else:
        work_log_stats = generator.generate_yesterday_work_logs(
            auto_submit=request.auto_submit
        )
    results['work_log'] = work_log_stats

    # 2. 同步设计评审
    design_sync = DesignReviewSyncService(db)
    design_stats = design_sync.sync_all_completed_reviews(
        start_date=request.start_date,
        end_date=request.end_date
    )
    results['design_review'] = design_stats

    # 3. 同步调试问题
    debug_sync = DebugIssueSyncService(db)
    debug_stats = debug_sync.sync_all_project_issues(
        start_date=request.start_date,
        end_date=request.end_date
    )
    results['debug_issue'] = debug_stats

    # 4. 识别知识贡献
    knowledge_service = KnowledgeAutoIdentificationService(db)
    ticket_stats = knowledge_service.batch_identify_from_service_tickets(
        start_date=request.start_date,
        end_date=request.end_date
    )
    kb_stats = knowledge_service.batch_identify_from_knowledge_base(
        start_date=request.start_date,
        end_date=request.end_date
    )
    results['knowledge'] = {
        'ticket_stats': ticket_stats,
        'kb_stats': kb_stats
    }

    return ResponseModel(
        code=200,
        message="所有绩效数据同步完成",
        data=results
    )


@router.get("/status", summary="获取同步状态")
async def get_sync_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据同步状态（最近7天）"""
    end_date = date.today()
    start_date = end_date - timedelta(days=7)

    # 统计各数据源的同步情况
    status = {
        'work_log': {
            'description': '工作日志自动生成',
            'last_sync': None,  # 可以从日志或数据库获取
            'recent_count': 0
        },
        'design_review': {
            'description': '设计评审自动同步',
            'last_sync': None,
            'recent_count': 0
        },
        'debug_issue': {
            'description': '调试问题自动同步',
            'last_sync': None,
            'recent_count': 0
        },
        'knowledge': {
            'description': '知识贡献自动识别',
            'last_sync': None,
            'recent_count': 0
        }
    }

    # 这里可以添加实际的统计逻辑
    # 例如从数据库查询最近同步的记录数量

    return ResponseModel(
        code=200,
        message="获取同步状态成功",
        data=status
    )
