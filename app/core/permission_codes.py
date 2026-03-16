# -*- coding: utf-8 -*-
"""
权限编码统一工具。

当前系统历史上同时存在 ``*:read`` 和 ``*:view`` 两套查看权限编码。
这里统一将查看类权限收口为 ``*:read``，同时保留对旧 ``*:view`` 数据的兼容。
"""

from __future__ import annotations

from typing import Iterable, List, Set

READ_ACTION_ALIASES = {"read", "view"}


def canonicalize_permission_code(permission_code: str) -> str:
    """将权限编码归一化到统一口径。"""
    if not permission_code or ":" not in permission_code:
        return permission_code

    resource, action = permission_code.rsplit(":", 1)
    if action.lower() in READ_ACTION_ALIASES:
        return f"{resource}:read"
    return permission_code


def get_equivalent_permission_codes(permission_code: str) -> List[str]:
    """返回与指定权限编码等价的全部编码。"""
    if not permission_code or ":" not in permission_code:
        return [permission_code] if permission_code else []

    resource, action = permission_code.rsplit(":", 1)
    if action.lower() in READ_ACTION_ALIASES:
        return [f"{resource}:read", f"{resource}:view"]
    return [permission_code]


def canonicalize_permission_codes(permission_codes: Iterable[str]) -> Set[str]:
    """批量归一化权限编码，自动去重并忽略空值。"""
    return {
        canonicalize_permission_code(permission_code)
        for permission_code in permission_codes
        if permission_code
    }
