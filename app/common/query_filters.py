# -*- coding: utf-8 -*-
"""
通用查询过滤工具

对已有 SQLAlchemy Query 应用关键词模糊搜索和分页，替代各处手写
.like('%keyword%') 与 .offset()/.limit() 的重复代码。
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence, Type, TypeVar, Union

from sqlalchemy.orm import Query
from sqlalchemy import or_

ModelType = TypeVar("ModelType")


def apply_keyword_filter(
    query: Query,
    model: Type[Any],
    keyword: Optional[str],
    field_names: Union[str, Sequence[str]],
    *,
    use_ilike: bool = True,
) -> Query:
    """
    在已有 Query 上应用关键词模糊搜索（多字段 OR）。

    Args:
        query: 已有查询（如 db.query(Model).filter(...)）。
        model: 模型类，用于取字段。
        keyword: 关键词；None 或空字符串时不加条件。
        field_names: 参与搜索的字段名，单个字符串或字符串列表。
        use_ilike: 是否使用 ilike（不区分大小写），默认 True。

    Returns:
        应用条件后的 query（keyword 为空时原样返回）。

    使用示例:
        q = db.query(Project).filter(Project.is_active == True)
        q = apply_keyword_filter(q, Project, keyword, ["name", "code"])
        q = apply_pagination(q, offset, limit)
        items = q.all()
    """
    if not keyword or not keyword.strip():
        return query

    names: List[str] = [field_names] if isinstance(field_names, str) else list(field_names)
    conditions = []
    pattern = f"%{keyword.strip()}%"

    for name in names:
        col = getattr(model, name, None)
        if col is not None:
            if use_ilike:
                conditions.append(col.ilike(pattern))
            else:
                conditions.append(col.like(pattern))

    if not conditions:
        return query
    return query.filter(or_(*conditions))


def apply_pagination(
    query: Query,
    offset: int,
    limit: int,
) -> Query:
    """
    在已有 Query 上应用 offset 和 limit。

    Args:
        query: 已有查询。
        offset: 跳过条数。
        limit: 返回条数上限。

    Returns:
        应用分页后的 query。

    使用示例:
        q = db.query(Model).filter(...)
        q = apply_pagination(q, pagination.offset, pagination.limit)
        items = q.all()
    """
    if offset > 0:
        query = query.offset(offset)
    if limit > 0:
        query = query.limit(limit)
    return query
