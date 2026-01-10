# -*- coding: utf-8 -*-
"""
工作日志 API endpoints
"""

from typing import Any, List, Optional
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.work_log import WorkLog, WorkLogConfig, WorkLogMention
from app.schemas.work_log import (
    WorkLogCreate, WorkLogUpdate, WorkLogResponse, WorkLogListResponse,
    WorkLogConfigCreate, WorkLogConfigUpdate, WorkLogConfigResponse, WorkLogConfigListResponse,
    MentionOptionsResponse, MentionResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.services.work_log_service import WorkLogService
from app.services.work_log_ai_service import WorkLogAIService
from fastapi import Body
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 工作日志 ====================

@router.post("/work-logs", response_model=ResponseModel[WorkLogResponse], status_code=status.HTTP_201_CREATED)
def create_work_log(
    *,
    db: Session = Depends(deps.get_db),
    work_log_in: WorkLogCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建工作日志
    """
    try:
        service = WorkLogService(db)
        work_log = service.create_work_log(current_user.id, work_log_in)
        
        # 构建响应
        mentions = []
        for mention in work_log.mentions:
            mentions.append(MentionResponse(
                id=mention.id,
                mention_type=mention.mention_type,
                mention_id=mention.mention_id,
                mention_name=mention.mention_name
            ))
        
        response = WorkLogResponse(
            id=work_log.id,
            user_id=work_log.user_id,
            user_name=work_log.user_name,
            work_date=work_log.work_date,
            content=work_log.content,
            status=work_log.status,
            mentions=mentions,
            created_at=work_log.created_at,
            updated_at=work_log.updated_at
        )
        
        return ResponseModel(
            code=201,
            message="工作日志创建成功",
            data=response
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建工作日志失败: {str(e)}")


@router.get("/work-logs", response_model=ResponseModel[WorkLogListResponse])
def get_work_logs(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工作日志列表
    """
    query = db.query(WorkLog)
    
    # 权限控制：普通用户只能查看自己的工作日志，管理员可以查看所有
    if not current_user.is_superuser:
        query = query.filter(WorkLog.user_id == current_user.id)
    elif user_id:
        query = query.filter(WorkLog.user_id == user_id)
    
    # 日期范围筛选
    if start_date:
        query = query.filter(WorkLog.work_date >= start_date)
    if end_date:
        query = query.filter(WorkLog.work_date <= end_date)
    
    # 状态筛选
    if status:
        query = query.filter(WorkLog.status == status)
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    work_logs = query.order_by(desc(WorkLog.work_date), desc(WorkLog.created_at)).offset(offset).limit(page_size).all()
    
    # 构建响应
    items = []
    for work_log in work_logs:
        mentions = []
        for mention in work_log.mentions:
            mentions.append(MentionResponse(
                id=mention.id,
                mention_type=mention.mention_type,
                mention_id=mention.mention_id,
                mention_name=mention.mention_name
            ))
        
            items.append(WorkLogResponse(
                id=work_log.id,
                user_id=work_log.user_id,
                user_name=work_log.user_name,
                work_date=work_log.work_date,
                content=work_log.content,
                status=work_log.status,
                mentions=mentions,
                timesheet_id=work_log.timesheet_id,
                created_at=work_log.created_at,
                updated_at=work_log.updated_at
            ))
    
    return ResponseModel(
        code=200,
        message="success",
        data=WorkLogListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
    )


@router.get("/work-logs/{work_log_id}", response_model=ResponseModel[WorkLogResponse])
def get_work_log(
    *,
    db: Session = Depends(deps.get_db),
    work_log_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取单个工作日志详情
    """
    work_log = db.query(WorkLog).filter(WorkLog.id == work_log_id).first()
    if not work_log:
        raise HTTPException(status_code=404, detail="工作日志不存在")
    
    # 权限控制：只能查看自己的工作日志，除非是管理员
    if not current_user.is_superuser and work_log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此工作日志")
    
    mentions = []
    for mention in work_log.mentions:
        mentions.append(MentionResponse(
            id=mention.id,
            mention_type=mention.mention_type,
            mention_id=mention.mention_id,
            mention_name=mention.mention_name
        ))
    
    response = WorkLogResponse(
        id=work_log.id,
        user_id=work_log.user_id,
        user_name=work_log.user_name,
        work_date=work_log.work_date,
        content=work_log.content,
        status=work_log.status,
        mentions=mentions,
        created_at=work_log.created_at,
        updated_at=work_log.updated_at
    )
    
    return ResponseModel(
        code=200,
        message="success",
        data=response
    )


@router.put("/work-logs/{work_log_id}", response_model=ResponseModel[WorkLogResponse])
def update_work_log(
    *,
    db: Session = Depends(deps.get_db),
    work_log_id: int,
    work_log_in: WorkLogUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新工作日志（仅限草稿状态）
    """
    try:
        service = WorkLogService(db)
        work_log = service.update_work_log(work_log_id, current_user.id, work_log_in)
        
        # 重新加载提及
        db.refresh(work_log)
        
        mentions = []
        for mention in work_log.mentions:
            mentions.append(MentionResponse(
                id=mention.id,
                mention_type=mention.mention_type,
                mention_id=mention.mention_id,
                mention_name=mention.mention_name
            ))
        
        response = WorkLogResponse(
            id=work_log.id,
            user_id=work_log.user_id,
            user_name=work_log.user_name,
            work_date=work_log.work_date,
            content=work_log.content,
            status=work_log.status,
            mentions=mentions,
            created_at=work_log.created_at,
            updated_at=work_log.updated_at
        )
        
        return ResponseModel(
            code=200,
            message="工作日志更新成功",
            data=response
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新工作日志失败: {str(e)}")


@router.delete("/work-logs/{work_log_id}", response_model=ResponseModel)
def delete_work_log(
    *,
    db: Session = Depends(deps.get_db),
    work_log_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除工作日志（仅限草稿状态）
    """
    work_log = db.query(WorkLog).filter(WorkLog.id == work_log_id).first()
    if not work_log:
        raise HTTPException(status_code=404, detail="工作日志不存在")
    
    # 权限控制：只能删除自己的工作日志
    if work_log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己的工作日志")
    
    # 只能删除草稿状态的日志
    if work_log.status != 'DRAFT':
        raise HTTPException(status_code=400, detail="只能删除草稿状态的工作日志")
    
    db.delete(work_log)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="工作日志删除成功"
    )


# ==================== 工作日志配置 ====================

@router.get("/work-logs/config", response_model=ResponseModel[WorkLogConfigResponse])
def get_work_log_config(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取当前用户的工作日志配置
    """
    # 优先查找用户专属配置
    config = db.query(WorkLogConfig).filter(
        WorkLogConfig.user_id == current_user.id,
        WorkLogConfig.is_active == True
    ).first()
    
    # 如果没有用户专属配置，查找部门配置
    # 注意：User.department是字符串（部门名称），需要先通过部门名称查找部门ID
    if not config and current_user.department:
        from app.models.organization import Department
        dept = db.query(Department).filter(Department.dept_name == current_user.department).first()
        if dept:
            config = db.query(WorkLogConfig).filter(
                WorkLogConfig.department_id == dept.id,
                WorkLogConfig.is_active == True
            ).first()
    
    # 如果没有部门配置，查找全员配置
    if not config:
        config = db.query(WorkLogConfig).filter(
            WorkLogConfig.user_id == None,
            WorkLogConfig.department_id == None,
            WorkLogConfig.is_active == True
        ).first()
    
    if not config:
        # 返回默认配置
        response = WorkLogConfigResponse(
            id=0,
            user_id=None,
            department_id=None,
            is_required=True,
            is_active=True,
            remind_time="18:00",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    else:
        response = WorkLogConfigResponse(
            id=config.id,
            user_id=config.user_id,
            department_id=config.department_id,
            is_required=config.is_required,
            is_active=config.is_active,
            remind_time=config.remind_time,
            created_at=config.created_at,
            updated_at=config.updated_at
        )
    
    return ResponseModel(
        code=200,
        message="success",
        data=response
    )


@router.post("/work-logs/config", response_model=ResponseModel[WorkLogConfigResponse], status_code=status.HTTP_201_CREATED)
def create_work_log_config(
    *,
    db: Session = Depends(deps.get_db),
    config_in: WorkLogConfigCreate,
    current_user: User = Depends(security.require_permission("work_log:config:create")),
) -> Any:
    """
    创建工作日志配置（管理员）
    """
    config = WorkLogConfig(
        user_id=config_in.user_id,
        department_id=config_in.department_id,
        is_required=config_in.is_required,
        is_active=config_in.is_active,
        remind_time=config_in.remind_time
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    response = WorkLogConfigResponse(
        id=config.id,
        user_id=config.user_id,
        department_id=config.department_id,
        is_required=config.is_required,
        is_active=config.is_active,
        remind_time=config.remind_time,
        created_at=config.created_at,
        updated_at=config.updated_at
    )
    
    return ResponseModel(
        code=201,
        message="配置创建成功",
        data=response
    )


@router.put("/work-logs/config/{config_id}", response_model=ResponseModel[WorkLogConfigResponse])
def update_work_log_config(
    *,
    db: Session = Depends(deps.get_db),
    config_id: int,
    config_in: WorkLogConfigUpdate,
    current_user: User = Depends(security.require_permission("work_log:config:update")),
) -> Any:
    """
    更新工作日志配置（管理员）
    """
    config = db.query(WorkLogConfig).filter(WorkLogConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    if config_in.is_required is not None:
        config.is_required = config_in.is_required
    if config_in.is_active is not None:
        config.is_active = config_in.is_active
    if config_in.remind_time is not None:
        config.remind_time = config_in.remind_time
    
    db.commit()
    db.refresh(config)
    
    response = WorkLogConfigResponse(
        id=config.id,
        user_id=config.user_id,
        department_id=config.department_id,
        is_required=config.is_required,
        is_active=config.is_active,
        remind_time=config.remind_time,
        created_at=config.created_at,
        updated_at=config.updated_at
    )
    
    return ResponseModel(
        code=200,
        message="配置更新成功",
        data=response
    )


@router.get("/work-logs/config/list", response_model=ResponseModel[WorkLogConfigListResponse])
def list_work_log_configs(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("work_log:config:read")),
) -> Any:
    """
    获取工作日志配置列表（管理员）
    """
    configs = db.query(WorkLogConfig).order_by(WorkLogConfig.created_at.desc()).all()
    
    items = []
    for config in configs:
        items.append(WorkLogConfigResponse(
            id=config.id,
            user_id=config.user_id,
            department_id=config.department_id,
            is_required=config.is_required,
            is_active=config.is_active,
            remind_time=config.remind_time,
            created_at=config.created_at,
            updated_at=config.updated_at
        ))
    
    return ResponseModel(
        code=200,
        message="success",
        data=WorkLogConfigListResponse(items=items)
    )


# ==================== 提及选项 ====================

@router.get("/work-logs/mentions/options", response_model=ResponseModel[MentionOptionsResponse])
def get_mention_options(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取可@的项目/设备/人员列表（用于下拉选择）
    """
    service = WorkLogService(db)
    options = service.get_mention_options(current_user.id)
    
    return ResponseModel(
        code=200,
        message="success",
        data=options
    )


# ==================== AI智能分析 ====================

@router.post("/work-logs/ai-analyze", response_model=ResponseModel)
def analyze_work_log_with_ai(
    *,
    db: Session = Depends(deps.get_db),
    content: str = Body(..., description="工作日志内容"),
    work_date: date = Body(..., description="工作日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    AI分析工作日志内容，自动提取工作项、工时和项目关联
    
    返回分析结果，包括：
    - work_items: 工作项列表（每个包含工作内容、工时、项目ID等）
    - suggested_projects: 建议的项目列表
    - total_hours: 总工时
    - confidence: 置信度
    """
    try:
        service = WorkLogAIService(db)
        
        # 使用AI服务分析（同步调用）
        result = service.analyze_work_log(content, current_user.id, work_date)
        
        return ResponseModel(
            code=200,
            message="分析完成",
            data=result
        )
    except Exception as e:
        logger.error(f"AI分析失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分析工作日志失败: {str(e)}")


@router.get("/work-logs/suggested-projects", response_model=ResponseModel)
def get_suggested_projects(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取用户参与的项目列表（用于智能推荐）
    
    返回用户参与的项目，按历史填报频率排序
    """
    try:
        service = WorkLogAIService(db)
        projects = service.get_user_projects_for_suggestion(current_user.id)
        
        return ResponseModel(
            code=200,
            message="success",
            data={
                "projects": projects,
                "total": len(projects)
            }
        )
    except Exception as e:
        logger.error(f"获取建议项目失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取建议项目失败: {str(e)}")
