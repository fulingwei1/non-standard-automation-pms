"""
售前AI系统集成 - API路由
Team 10: 售前AI系统集成与前端UI
"""
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks
from sqlalchemy.orm import Session
import logging

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.presale_ai import (
    AIUsageStatsResponse,
    AIFeedbackCreate,
    AIFeedbackResponse,
    AIConfigUpdate,
    AIConfigResponse,
    AIWorkflowLogResponse,
    AIAuditLogResponse,
    DashboardStatsResponse,
    WorkflowStartRequest,
    WorkflowStatusResponse,
    BatchProcessRequest,
    BatchProcessResponse,
    HealthCheckResponse,
    ExportReportRequest,
    ExportReportResponse
)
from app.services.presale_ai_integration import PresaleAIIntegrationService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ 仪表盘统计 ============

@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    days: int = Query(default=30, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取AI仪表盘统计数据
    
    - 总使用次数
    - 总成功次数
    - 成功率
    - 平均响应时间
    - Top AI功能
    - 使用趋势
    - 用户统计
    """
    service = PresaleAIIntegrationService(db)
    return service.get_dashboard_stats(days=days)


# ============ 使用统计 ============

@router.get("/usage-stats", response_model=List[AIUsageStatsResponse])
async def get_usage_stats(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    ai_functions: Optional[List[str]] = Query(None, description="AI功能列表"),
    user_ids: Optional[List[int]] = Query(None, description="用户ID列表"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取AI使用统计
    
    支持多维度查询：日期范围、AI功能、用户等
    """
    service = PresaleAIIntegrationService(db)
    stats = service.get_usage_stats(
        start_date=start_date,
        end_date=end_date,
        ai_functions=ai_functions,
        user_ids=user_ids
    )
    return stats


# ============ 反馈管理 ============

@router.post("/feedback", response_model=AIFeedbackResponse)
async def submit_feedback(
    feedback_data: AIFeedbackCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    提交AI反馈
    
    - 评分1-5星
    - 反馈文本
    - 关联售前工单
    """
    service = PresaleAIIntegrationService(db)
    
    # 创建反馈
    feedback = service.create_feedback(
        user_id=current_user.id,
        feedback_data=feedback_data
    )
    
    # 记录审计日志
    service.create_audit_log(
        user_id=current_user.id,
        action="submit_feedback",
        ai_function=feedback_data.ai_function,
        resource_type="feedback",
        resource_id=feedback.id,
        details={"rating": feedback_data.rating},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    return feedback


@router.get("/feedback/{function}", response_model=List[AIFeedbackResponse])
async def get_feedback_by_function(
    function: str,
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    max_rating: Optional[int] = Query(None, ge=1, le=5),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定AI功能的反馈
    
    支持评分过滤、日期范围等
    """
    service = PresaleAIIntegrationService(db)
    feedbacks = service.get_feedbacks(
        ai_function=function,
        min_rating=min_rating,
        max_rating=max_rating,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    return feedbacks


# ============ 工作流管理 ============

@router.post("/workflow/start", response_model=List[AIWorkflowLogResponse])
async def start_workflow(
    workflow_request: WorkflowStartRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    启动AI工作流
    
    自动创建：需求理解 → 方案生成 → 成本估算 → 赢率预测 → 报价生成
    """
    service = PresaleAIIntegrationService(db)
    
    try:
        logs = service.start_workflow(
            presale_ticket_id=workflow_request.presale_ticket_id,
            initial_data=workflow_request.initial_data,
            auto_run=workflow_request.auto_run
        )
        
        # 记录审计日志
        service.create_audit_log(
            user_id=current_user.id,
            action="start_workflow",
            resource_type="workflow",
            resource_id=workflow_request.presale_ticket_id,
            details={"auto_run": workflow_request.auto_run},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return logs
    except Exception as e:
        logger.error(f"Failed to start workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")


@router.get("/workflow/status/{ticket_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取工作流状态
    
    返回：
    - 当前步骤
    - 整体状态
    - 所有步骤详情
    - 进度百分比
    """
    service = PresaleAIIntegrationService(db)
    status = service.get_workflow_status(ticket_id)
    
    if not status:
        raise HTTPException(status_code=404, detail=f"Workflow not found for ticket {ticket_id}")
    
    return status


# ============ 批量处理 ============

@router.post("/batch-process", response_model=BatchProcessResponse)
async def batch_process(
    batch_request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量AI处理
    
    支持批量处理多个工单的指定AI功能
    """
    import uuid
    
    job_id = str(uuid.uuid4())
    
    # 记录审计日志
    service = PresaleAIIntegrationService(db)
    service.create_audit_log(
        user_id=current_user.id,
        action="batch_process",
        ai_function=batch_request.ai_function,
        details={
            "job_id": job_id,
            "ticket_count": len(batch_request.ticket_ids),
            "options": batch_request.options
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    # TODO: 实际的批量处理逻辑（异步处理）
    # background_tasks.add_task(process_batch, batch_request, job_id)
    
    return BatchProcessResponse(
        job_id=job_id,
        total_count=len(batch_request.ticket_ids),
        status="started",
        started_at=datetime.now()
    )


# ============ 健康检查 ============

@router.get("/health-check", response_model=HealthCheckResponse)
async def health_check(
    db: Session = Depends(get_db)
):
    """
    AI服务健康检查
    
    检查：
    - 数据库连接
    - AI功能配置
    - 最近活动情况
    """
    service = PresaleAIIntegrationService(db)
    return service.health_check()


# ============ 配置管理 ============

@router.post("/config/update", response_model=AIConfigResponse)
async def update_config(
    ai_function: str,
    config_data: AIConfigUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新AI配置
    
    可配置：
    - 是否启用
    - 模型名称
    - 温度参数
    - 最大tokens
    - 超时时间
    """
    service = PresaleAIIntegrationService(db)
    
    try:
        config = service.update_config(ai_function, config_data)
        
        # 记录审计日志
        service.create_audit_log(
            user_id=current_user.id,
            action="update_config",
            ai_function=ai_function,
            resource_type="config",
            resource_id=config.id,
            details=config_data.dict(exclude_unset=True),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return config
    except Exception as e:
        logger.error(f"Failed to update config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


@router.get("/config", response_model=List[AIConfigResponse])
async def get_all_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有AI配置
    """
    service = PresaleAIIntegrationService(db)
    return service.get_all_configs()


# ============ 审计日志 ============

@router.get("/audit-log", response_model=List[AIAuditLogResponse])
async def get_audit_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取操作审计日志
    
    记录所有AI相关操作
    """
    service = PresaleAIIntegrationService(db)
    return service.get_audit_logs(
        user_id=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )


# ============ 报告导出 ============

@router.post("/export-report", response_model=ExportReportResponse)
async def export_report(
    export_request: ExportReportRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出AI使用报告
    
    支持格式：
    - Excel
    - PDF
    - CSV
    """
    
    service = PresaleAIIntegrationService(db)
    
    # 记录审计日志
    service.create_audit_log(
        user_id=current_user.id,
        action="export_report",
        details={
            "start_date": export_request.start_date.isoformat(),
            "end_date": export_request.end_date.isoformat(),
            "format": export_request.format
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    # TODO: 实际的报告生成逻辑
    file_name = f"ai_report_{export_request.start_date}_{export_request.end_date}.{export_request.format}"
    
    return ExportReportResponse(
        file_url=f"/api/v1/presale/ai/downloads/{file_name}",
        file_name=file_name,
        file_size=0,  # 待实现
        generated_at=datetime.now()
    )
