# -*- coding: utf-8 -*-
"""
工作日志配置端点
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.work_log import WorkLogConfig
from app.schemas.common import ResponseModel
from app.schemas.work_log import (
    WorkLogConfigCreate,
    WorkLogConfigListResponse,
    WorkLogConfigResponse,
    WorkLogConfigUpdate,
)

router = APIRouter()


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
