# -*- coding: utf-8 -*-
"""
时薪配置管理 API
"""

from typing import Any, List, Optional
from decimal import Decimal
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User, Role
from app.models.organization import Department
from app.models.hourly_rate import HourlyRateConfig
from app.schemas.hourly_rate import (
    HourlyRateConfigCreate, HourlyRateConfigUpdate, HourlyRateConfigResponse
)
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[HourlyRateConfigResponse])
def list_hourly_rate_configs(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    config_type: Optional[str] = Query(None, description="配置类型筛选"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    role_id: Optional[int] = Query(None, description="角色ID筛选"),
    dept_id: Optional[int] = Query(None, description="部门ID筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.require_permission("hourly_rate:read")),
) -> Any:
    """
    获取时薪配置列表
    """
    query = db.query(HourlyRateConfig)
    
    if config_type:
        query = query.filter(HourlyRateConfig.config_type == config_type)
    if user_id:
        query = query.filter(HourlyRateConfig.user_id == user_id)
    if role_id:
        query = query.filter(HourlyRateConfig.role_id == role_id)
    if dept_id:
        query = query.filter(HourlyRateConfig.dept_id == dept_id)
    if is_active is not None:
        query = query.filter(HourlyRateConfig.is_active == is_active)
    
    total = query.count()
    offset = (page - 1) * page_size
    configs = query.order_by(desc(HourlyRateConfig.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for config in configs:
        config_dict = {
            **{c.name: getattr(config, c.name) for c in config.__table__.columns},
            "user_name": config.user.real_name if config.user else None,
            "role_name": config.role.role_name if config.role else None,
            "dept_name": config.dept.dept_name if config.dept else None,
        }
        items.append(HourlyRateConfigResponse(**config_dict))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/", response_model=HourlyRateConfigResponse, status_code=status.HTTP_201_CREATED)
def create_hourly_rate_config(
    *,
    db: Session = Depends(deps.get_db),
    config_in: HourlyRateConfigCreate,
    current_user: User = Depends(security.require_permission("hourly_rate:create")),
) -> Any:
    """
    创建时薪配置
    """
    # 验证配置类型和关联对象
    if config_in.config_type == "USER" and not config_in.user_id:
        raise HTTPException(status_code=400, detail="用户配置必须指定user_id")
    if config_in.config_type == "ROLE" and not config_in.role_id:
        raise HTTPException(status_code=400, detail="角色配置必须指定role_id")
    if config_in.config_type == "DEPT" and not config_in.dept_id:
        raise HTTPException(status_code=400, detail="部门配置必须指定dept_id")
    
    # 检查是否已存在相同配置
    existing = None
    if config_in.config_type == "USER" and config_in.user_id:
        existing = db.query(HourlyRateConfig).filter(
            HourlyRateConfig.config_type == "USER",
            HourlyRateConfig.user_id == config_in.user_id,
            HourlyRateConfig.is_active == True
        ).first()
    elif config_in.config_type == "ROLE" and config_in.role_id:
        existing = db.query(HourlyRateConfig).filter(
            HourlyRateConfig.config_type == "ROLE",
            HourlyRateConfig.role_id == config_in.role_id,
            HourlyRateConfig.is_active == True
        ).first()
    elif config_in.config_type == "DEPT" and config_in.dept_id:
        existing = db.query(HourlyRateConfig).filter(
            HourlyRateConfig.config_type == "DEPT",
            HourlyRateConfig.dept_id == config_in.dept_id,
            HourlyRateConfig.is_active == True
        ).first()
    elif config_in.config_type == "DEFAULT":
        existing = db.query(HourlyRateConfig).filter(
            HourlyRateConfig.config_type == "DEFAULT",
            HourlyRateConfig.is_active == True
        ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="该配置已存在，请先禁用或删除现有配置")
    
    config_data = config_in.model_dump()
    config_data['created_by'] = current_user.id
    
    config = HourlyRateConfig(**config_data)
    db.add(config)
    db.commit()
    db.refresh(config)
    
    config_dict = {
        **{c.name: getattr(config, c.name) for c in config.__table__.columns},
        "user_name": config.user.real_name if config.user else None,
        "role_name": config.role.role_name if config.role else None,
        "dept_name": config.dept.dept_name if config.dept else None,
    }
    
    return HourlyRateConfigResponse(**config_dict)


@router.get("/{config_id}", response_model=HourlyRateConfigResponse)
def get_hourly_rate_config(
    *,
    db: Session = Depends(deps.get_db),
    config_id: int,
    current_user: User = Depends(security.require_permission("hourly_rate:read")),
) -> Any:
    """
    获取时薪配置详情
    """
    config = db.query(HourlyRateConfig).filter(HourlyRateConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="时薪配置不存在")
    
    config_dict = {
        **{c.name: getattr(config, c.name) for c in config.__table__.columns},
        "user_name": config.user.real_name if config.user else None,
        "role_name": config.role.role_name if config.role else None,
        "dept_name": config.dept.dept_name if config.dept else None,
    }
    
    return HourlyRateConfigResponse(**config_dict)


@router.put("/{config_id}", response_model=HourlyRateConfigResponse)
def update_hourly_rate_config(
    *,
    db: Session = Depends(deps.get_db),
    config_id: int,
    config_in: HourlyRateConfigUpdate,
    current_user: User = Depends(security.require_permission("hourly_rate:update")),
) -> Any:
    """
    更新时薪配置
    """
    config = db.query(HourlyRateConfig).filter(HourlyRateConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="时薪配置不存在")
    
    update_data = config_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(config, field):
            setattr(config, field, value)
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    config_dict = {
        **{c.name: getattr(config, c.name) for c in config.__table__.columns},
        "user_name": config.user.real_name if config.user else None,
        "role_name": config.role.role_name if config.role else None,
        "dept_name": config.dept.dept_name if config.dept else None,
    }
    
    return HourlyRateConfigResponse(**config_dict)


@router.delete("/{config_id}", status_code=status.HTTP_200_OK)
def delete_hourly_rate_config(
    *,
    db: Session = Depends(deps.get_db),
    config_id: int,
    current_user: User = Depends(security.require_permission("hourly_rate:delete")),
) -> Any:
    """
    删除时薪配置
    """
    config = db.query(HourlyRateConfig).filter(HourlyRateConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="时薪配置不存在")
    
    db.delete(config)
    db.commit()
    
    return ResponseModel(code=200, message="时薪配置已删除")


@router.get("/users/{user_id}/hourly-rate", response_model=ResponseModel)
def get_user_hourly_rate(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    work_date: Optional[str] = Query(None, description="工作日期（YYYY-MM-DD格式），默认今天"),
    current_user: User = Depends(security.require_permission("hourly_rate:read")),
) -> Any:
    """
    获取用户时薪（按优先级：用户配置 > 角色配置 > 部门配置 > 默认配置）
    """
    from app.services.hourly_rate_service import HourlyRateService
    from datetime import datetime
    
    work_date_obj = None
    if work_date:
        try:
            work_date_obj = datetime.strptime(work_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，应为YYYY-MM-DD")

    hourly_rate = HourlyRateService.get_user_hourly_rate(db, user_id, work_date_obj)
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "user_id": user_id,
            "hourly_rate": float(hourly_rate),
            "work_date": work_date or str(date.today()),
            "source": "配置"
        }
    )


@router.post("/users/batch-hourly-rates", response_model=ResponseModel)
def get_users_hourly_rates(
    *,
    db: Session = Depends(deps.get_db),
    user_ids: List[int] = Query(..., description="用户ID列表"),
    work_date: Optional[str] = Query(None, description="工作日期（YYYY-MM-DD格式），默认今天"),
    current_user: User = Depends(security.require_permission("hourly_rate:read")),
) -> Any:
    """
    批量获取多个用户的时薪
    """
    from app.services.hourly_rate_service import HourlyRateService
    from datetime import datetime
    
    work_date_obj = None
    if work_date:
        try:
            work_date_obj = datetime.strptime(work_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，应为YYYY-MM-DD")

    hourly_rates = HourlyRateService.get_users_hourly_rates(db, user_ids, work_date_obj)
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "work_date": work_date or str(date.today()),
            "hourly_rates": {
                str(user_id): float(rate)
                for user_id, rate in hourly_rates.items()
            }
        }
    )


@router.get("/history", response_model=ResponseModel)
def get_hourly_rate_history(
    *,
    db: Session = Depends(deps.get_db),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    role_id: Optional[int] = Query(None, description="角色ID筛选"),
    dept_id: Optional[int] = Query(None, description="部门ID筛选"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD格式）"),
    current_user: User = Depends(security.require_permission("hourly_rate:read")),
) -> Any:
    """
    获取时薪配置历史记录
    """
    from app.services.hourly_rate_service import HourlyRateService
    from datetime import datetime
    
    start_date_obj = None
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="开始日期格式错误，应为YYYY-MM-DD")

    end_date_obj = None
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="结束日期格式错误，应为YYYY-MM-DD")
    
    history = HourlyRateService.get_hourly_rate_history(
        db, user_id, role_id, dept_id, start_date_obj, end_date_obj
    )
    
    # 转换日期为字符串
    for item in history:
        if item.get("effective_date"):
            item["effective_date"] = str(item["effective_date"])
        if item.get("expiry_date"):
            item["expiry_date"] = str(item["expiry_date"])
        if item.get("created_at"):
            item["created_at"] = item["created_at"].isoformat() if hasattr(item["created_at"], "isoformat") else str(item["created_at"])
        if item.get("updated_at"):
            item["updated_at"] = item["updated_at"].isoformat() if hasattr(item["updated_at"], "isoformat") else str(item["updated_at"])
        if item.get("hourly_rate"):
            item["hourly_rate"] = float(item["hourly_rate"])
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "history": history,
            "total": len(history)
        }
    )


