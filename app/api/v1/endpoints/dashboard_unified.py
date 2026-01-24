# -*- coding: utf-8 -*-
"""
统一工作台数据 API

当前返回空数据，供前端自行加载各组件的数据。
后续可根据角色聚合并返回各 widget 的预加载数据。
"""

from typing import Dict

from fastapi import APIRouter, Depends

from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/dashboard/unified/{role_code}", response_model=ResponseModel[Dict])
def get_unified_dashboard(
    role_code: str,
    current_user: User = Depends(security.get_current_active_user),
) -> ResponseModel[Dict]:
    # 目前不区分角色，返回空对象即可避免 404。
    # 前端各组件会自行调用各自的 API 获取数据。
    return ResponseModel(data={})
