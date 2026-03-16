# -*- coding: utf-8 -*-
"""
数据范围口径统一工具。

系统里同时存在：
- 旧角色 data_scope：ALL/DEPT/SUBORDINATE/PROJECT/OWN
- 新 ScopeType：ALL/BUSINESS_UNIT/DEPARTMENT/TEAM/PROJECT/OWN/CUSTOM

这里把旧过滤器统一到一套可比较的 canonical scope 上，避免不同模块各自解释。
"""

from __future__ import annotations

from typing import Iterable, Optional

from app.models.enums import DataScopeEnum

_SCOPE_ALIAS_MAP = {
    DataScopeEnum.ALL.value: DataScopeEnum.ALL.value,
    "BUSINESS_UNIT": DataScopeEnum.DEPT.value,
    "DEPARTMENT": DataScopeEnum.DEPT.value,
    DataScopeEnum.DEPT.value: DataScopeEnum.DEPT.value,
    "TEAM": DataScopeEnum.DEPT.value,
    DataScopeEnum.SUBORDINATE.value: DataScopeEnum.SUBORDINATE.value,
    DataScopeEnum.PROJECT.value: DataScopeEnum.PROJECT.value,
    DataScopeEnum.CUSTOMER.value: DataScopeEnum.CUSTOMER.value,
    DataScopeEnum.CUSTOM.value: DataScopeEnum.CUSTOM.value,
    DataScopeEnum.OWN.value: DataScopeEnum.OWN.value,
}

_SCOPE_PRIORITY = {
    DataScopeEnum.ALL.value: 60,
    DataScopeEnum.DEPT.value: 50,
    DataScopeEnum.SUBORDINATE.value: 40,
    DataScopeEnum.PROJECT.value: 30,
    DataScopeEnum.CUSTOMER.value: 20,
    DataScopeEnum.CUSTOM.value: 10,
    DataScopeEnum.OWN.value: 0,
}


def normalize_data_scope(scope: Optional[str]) -> str:
    """将任意历史/新口径的数据范围值归一化。"""
    if not scope:
        return DataScopeEnum.OWN.value

    normalized = _SCOPE_ALIAS_MAP.get(str(scope).upper())
    return normalized or str(scope).upper()


def pick_broadest_scope(scopes: Iterable[str]) -> str:
    """在一组数据范围中选出当前系统可识别的最宽范围。"""
    normalized_scopes = [normalize_data_scope(scope) for scope in scopes if scope]
    if not normalized_scopes:
        return DataScopeEnum.OWN.value

    return max(normalized_scopes, key=lambda scope: _SCOPE_PRIORITY.get(scope, -1))
