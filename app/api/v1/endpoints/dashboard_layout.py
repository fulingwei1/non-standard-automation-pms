# -*- coding: utf-8 -*-
"""
用户仪表盘布局自定义 API

支持用户保存/加载自定义的仪表盘组件布局
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Dict, List, Optional

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.user_dashboard_layout import UserDashboardLayout
from app.schemas.common import ResponseModel

router = APIRouter()


class WidgetLayoutItem(BaseModel):
    """单个组件布局配置"""
    widget_id: str = Field(..., description="组件ID")
    visible: bool = Field(True, description="是否显示")
    order: int = Field(0, description="排序")
    size: Optional[str] = Field(None, description="尺寸覆盖: small/medium/large/full")
    props: Optional[Dict] = Field(None, description="自定义属性覆盖")


class DashboardLayoutRequest(BaseModel):
    """保存布局请求"""
    role_code: str = Field(..., description="角色编码")
    layout: str = Field("2-column", description="布局模式")
    widgets: List[WidgetLayoutItem] = Field(..., description="组件布局列表")


class DashboardLayoutResponse(BaseModel):
    """布局响应"""
    role_code: str
    layout: str = "2-column"
    widgets: List[WidgetLayoutItem] = []
    is_customized: bool = False


@router.get(
    "/dashboard/layout/{role_code}",
    response_model=ResponseModel[DashboardLayoutResponse],
)
def get_dashboard_layout(
    role_code: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> ResponseModel[DashboardLayoutResponse]:
    """
    获取用户的自定义仪表盘布局

    如果用户没有自定义布局，返回 is_customized=False 的默认空布局
    """
    record = (
        db.query(UserDashboardLayout)
        .filter(
            UserDashboardLayout.user_id == current_user.id,
            UserDashboardLayout.role_code == role_code,
            UserDashboardLayout.is_active == True,  # noqa: E712
        )
        .first()
    )

    if not record:
        return ResponseModel(
            data=DashboardLayoutResponse(
                role_code=role_code,
                is_customized=False,
            )
        )

    try:
        config = json.loads(record.layout_config)
    except (json.JSONDecodeError, TypeError):
        config = {"layout": "2-column", "widgets": []}

    widgets = [WidgetLayoutItem(**w) for w in config.get("widgets", [])]

    return ResponseModel(
        data=DashboardLayoutResponse(
            role_code=role_code,
            layout=config.get("layout", "2-column"),
            widgets=widgets,
            is_customized=True,
        )
    )


@router.put(
    "/dashboard/layout",
    response_model=ResponseModel[DashboardLayoutResponse],
)
def save_dashboard_layout(
    request: DashboardLayoutRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> ResponseModel[DashboardLayoutResponse]:
    """
    保存用户的自定义仪表盘布局

    如果已有记录则更新，否则创建新记录
    """
    config = {
        "layout": request.layout,
        "widgets": [w.model_dump() for w in request.widgets],
    }
    config_json = json.dumps(config, ensure_ascii=False)

    record = (
        db.query(UserDashboardLayout)
        .filter(
            UserDashboardLayout.user_id == current_user.id,
            UserDashboardLayout.role_code == request.role_code,
        )
        .first()
    )

    if record:
        record.layout_config = config_json
        record.is_active = True
    else:
        record = UserDashboardLayout(
            user_id=current_user.id,
            role_code=request.role_code,
            layout_config=config_json,
        )
        db.add(record)

    db.commit()
    db.refresh(record)

    return ResponseModel(
        data=DashboardLayoutResponse(
            role_code=request.role_code,
            layout=request.layout,
            widgets=request.widgets,
            is_customized=True,
        )
    )


@router.delete("/dashboard/layout/{role_code}", response_model=ResponseModel[dict])
def reset_dashboard_layout(
    role_code: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> ResponseModel[dict]:
    """
    重置用户的自定义布局（恢复默认）
    """
    record = (
        db.query(UserDashboardLayout)
        .filter(
            UserDashboardLayout.user_id == current_user.id,
            UserDashboardLayout.role_code == role_code,
        )
        .first()
    )

    if record:
        record.is_active = False
        db.commit()

    return ResponseModel(data={"role_code": role_code, "reset": True})
