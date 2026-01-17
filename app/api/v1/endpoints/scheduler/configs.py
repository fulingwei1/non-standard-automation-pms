# -*- coding: utf-8 -*-
"""
定时任务配置管理端点
"""

import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_active_user, has_scheduler_admin_access
from app.models.scheduler_config import SchedulerTaskConfig
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.scheduler_config import (
    SchedulerTaskConfigSyncRequest,
    SchedulerTaskConfigUpdate,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/configs", response_model=ResponseModel)
def get_task_configs(
    category: Optional[str] = Query(None, description="按分类筛选"),
    enabled: Optional[bool] = Query(None, description="按启用状态筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    获取所有定时任务配置列表
    """
    try:
        # 确保数据库会话有效
        if not db:
            raise HTTPException(status_code=500, detail="数据库连接失败")

        query = db.query(SchedulerTaskConfig)

        if category:
            query = query.filter(SchedulerTaskConfig.category == category)
        if enabled is not None:
            query = query.filter(SchedulerTaskConfig.is_enabled == enabled)

        configs = query.order_by(SchedulerTaskConfig.category, SchedulerTaskConfig.task_name).all()

        # 安全地处理 JSON 字段
        items = []
        for config in configs:
            try:
                # 处理 cron_config（JSONType 应该已经处理，但为了安全起见再次检查）
                cron_config = config.cron_config
                if cron_config is None:
                    cron_config = {}
                elif isinstance(cron_config, str):
                    try:
                        cron_config = json.loads(cron_config)
                    except (json.JSONDecodeError, TypeError):
                        cron_config = {}

                # 处理 dependencies_tables
                dependencies_tables = config.dependencies_tables
                if dependencies_tables is None:
                    dependencies_tables = []
                elif isinstance(dependencies_tables, str):
                    try:
                        dependencies_tables = json.loads(dependencies_tables)
                    except (json.JSONDecodeError, TypeError):
                        dependencies_tables = []

                # 处理 sla_config
                sla_config = config.sla_config
                if sla_config is None:
                    sla_config = {}
                elif isinstance(sla_config, str):
                    try:
                        sla_config = json.loads(sla_config)
                    except (json.JSONDecodeError, TypeError):
                        sla_config = {}

                items.append({
                    "id": config.id,
                    "task_id": config.task_id,
                    "task_name": config.task_name,
                    "module": config.module,
                    "callable_name": config.callable_name,
                    "owner": config.owner,
                    "category": config.category,
                    "description": config.description,
                    "is_enabled": config.is_enabled,
                    "cron_config": cron_config,
                    "dependencies_tables": dependencies_tables,
                    "risk_level": config.risk_level,
                    "sla_config": sla_config,
                    "updated_by": config.updated_by,
                    "created_at": config.created_at.isoformat() if config.created_at else None,
                    "updated_at": config.updated_at.isoformat() if config.updated_at else None,
                })
            except Exception as config_error:
                # 如果某个配置项处理失败，记录错误但继续处理其他项
                logger.error(f"处理配置项 {config.task_id} 失败: {config_error}", exc_info=True)
                continue

        return ResponseModel(
            code=200,
            message="success",
            data={
                "total": len(items),
                "items": items
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务配置列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取任务配置列表失败: {str(e)}")


@router.get("/configs/{task_id}", response_model=ResponseModel)
def get_task_config(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    获取指定任务的配置
    """
    try:
        config = db.query(SchedulerTaskConfig).filter(
            SchedulerTaskConfig.task_id == task_id
        ).first()

        if not config:
            raise HTTPException(status_code=404, detail=f"任务配置 {task_id} 不存在")

        return ResponseModel(
            code=200,
            message="success",
            data={
                "id": config.id,
                "task_id": config.task_id,
                "task_name": config.task_name,
                "module": config.module,
                "callable_name": config.callable_name,
                "owner": config.owner,
                "category": config.category,
                "description": config.description,
                "is_enabled": config.is_enabled,
                "cron_config": config.cron_config if config.cron_config else {},
                "dependencies_tables": config.dependencies_tables if config.dependencies_tables else [],
                "risk_level": config.risk_level,
                "sla_config": config.sla_config if config.sla_config else {},
                "updated_by": config.updated_by,
                "created_at": config.created_at.isoformat() if config.created_at else None,
                "updated_at": config.updated_at.isoformat() if config.updated_at else None,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务配置失败: {str(e)}")


@router.put("/configs/{task_id}", response_model=ResponseModel)
def update_task_config(
    task_id: str,
    config_update: SchedulerTaskConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    更新定时任务配置（频率、启用状态等）
    注意：需要管理员权限
    """
    # 检查管理员权限
    if not has_scheduler_admin_access(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限才能更新任务配置")

    try:
        config = db.query(SchedulerTaskConfig).filter(
            SchedulerTaskConfig.task_id == task_id
        ).first()

        if not config:
            raise HTTPException(status_code=404, detail=f"任务配置 {task_id} 不存在")

        # 更新配置
        if config_update.is_enabled is not None:
            config.is_enabled = config_update.is_enabled
        if config_update.cron_config is not None:
            config.cron_config = config_update.cron_config
        config.updated_by = current_user.id

        db.commit()

        # 动态更新调度器中的任务
        try:
            from app.utils.scheduler import scheduler
            job = scheduler.get_job(task_id)
            if job:
                # 更新任务的Cron配置
                if config_update.cron_config:
                    scheduler.reschedule_job(
                        task_id,
                        trigger='cron',
                        **config_update.cron_config
                    )
                # 启用/禁用任务
                if config_update.is_enabled is not None:
                    if config_update.is_enabled:
                        scheduler.resume_job(task_id)
                    else:
                        scheduler.pause_job(task_id)
        except Exception as scheduler_err:
            # 调度器更新失败不影响数据库更新
            logger.warning(f"更新调度器任务失败: {str(scheduler_err)}")

        return ResponseModel(
            code=200,
            message="success",
            data={
                "task_id": task_id,
                "message": "配置已更新"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新任务配置失败: {str(e)}")


@router.post("/configs/sync", response_model=ResponseModel)
def sync_task_configs(
    sync_request: SchedulerTaskConfigSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    从 scheduler_config.py 同步任务配置到数据库
    用于初始化或更新配置
    """
    # 检查管理员权限
    if not has_scheduler_admin_access(current_user):
        raise HTTPException(status_code=403, detail="需要管理员权限才能同步任务配置")

    try:
        from app.utils.scheduler_config import SCHEDULER_TASKS

        synced_count = 0
        created_count = 0
        updated_count = 0

        for task in SCHEDULER_TASKS:
            config = db.query(SchedulerTaskConfig).filter(
                SchedulerTaskConfig.task_id == task["id"]
            ).first()

            # 准备配置数据
            cron_config = task.get("cron", {})
            dependencies_tables = task.get("dependencies_tables", [])
            sla_config = task.get("sla", {})

            config_data = {
                "task_id": task["id"],
                "task_name": task["name"],
                "module": task["module"],
                "callable_name": task["callable"],
                "owner": task.get("owner"),
                "category": task.get("category"),
                "description": task.get("description"),
                "is_enabled": task.get("enabled", True),
                "cron_config": cron_config,
                "dependencies_tables": dependencies_tables if dependencies_tables else None,
                "risk_level": task.get("risk_level"),
                "sla_config": sla_config if sla_config else None,
                "updated_by": current_user.id,
            }

            if config:
                # 更新现有配置
                if sync_request.force:
                    for key, value in config_data.items():
                        if key != "task_id":  # 不更新task_id
                            setattr(config, key, value)
                    updated_count += 1
            else:
                # 创建新配置
                config = SchedulerTaskConfig(**config_data)
                db.add(config)
                created_count += 1

            synced_count += 1

        db.commit()

        return ResponseModel(
            code=200,
            message="success",
            data={
                "synced_count": synced_count,
                "created_count": created_count,
                "updated_count": updated_count,
                "message": f"成功同步 {synced_count} 个任务配置（新建 {created_count} 个，更新 {updated_count} 个）"
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"同步任务配置失败: {str(e)}")
