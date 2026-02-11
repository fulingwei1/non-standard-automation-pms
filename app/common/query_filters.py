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


def _normalize_keywords(keyword: Optional[Union[str, Sequence[str]]]) -> List[str]:
    keywords: List[str] = []
    if keyword is None:
        return keywords
    if isinstance(keyword, str):
        if keyword.strip():
            keywords.append(keyword)
        return keywords
    if isinstance(keyword, (list, tuple, set)):
        for item in keyword:
            if item is None:
                continue
            item_str = str(item)
            if item_str.strip():
                keywords.append(item_str)
        return keywords
    item_str = str(keyword)
    if item_str.strip():
        keywords.append(item_str)
    return keywords


def build_keyword_conditions(
    model: Type[Any],
    keyword: Optional[Union[str, Sequence[str]]],
    field_names: Union[str, Sequence[str]],
    *,
    use_ilike: bool = True,
) -> List[Any]:
    """
    构建关键词模糊搜索条件（多字段 OR）。

    Returns:
        条件列表，调用方可自行组合 OR/AND。
    """
    keywords = _normalize_keywords(keyword)
    if not keywords:
        return []

    names: List[str] = [field_names] if isinstance(field_names, str) else list(field_names)
    conditions: List[Any] = []

    for kw in keywords:
        pattern = f"%{kw.strip()}%"
        for name in names:
            col = getattr(model, name, None)
            if col is not None:
                if use_ilike:
                    conditions.append(col.ilike(pattern))
                else:
                    conditions.append(col.like(pattern))

    return conditions


def build_like_conditions(
    model: Type[Any],
    pattern: Optional[Union[str, Sequence[str]]],
    field_names: Union[str, Sequence[str]],
    *,
    use_ilike: bool = True,
) -> List[Any]:
    """
    构建自定义 LIKE 模式条件（pattern 可包含通配符）。

    Returns:
        条件列表，调用方可自行组合 OR/AND。
    """
    patterns = _normalize_keywords(pattern)
    if not patterns:
        return []

    names: List[str] = [field_names] if isinstance(field_names, str) else list(field_names)
    conditions: List[Any] = []

    for pat in patterns:
        for name in names:
            col = getattr(model, name, None)
            if col is not None:
                if use_ilike:
                    conditions.append(col.ilike(pat))
                else:
                    conditions.append(col.like(pat))

    return conditions


def apply_keyword_filter(
    query: Query,
    model: Type[Any],
    keyword: Optional[Union[str, Sequence[str]]],
    field_names: Union[str, Sequence[str]],
    *,
    use_ilike: bool = True,
) -> Query:
    """
    在已有 Query 上应用关键词模糊搜索（多字段 OR）。

    Args:
        query: 已有查询（如 db.query(Model).filter(...)）。
        model: 模型类，用于取字段。
        keyword: 关键词或关键词列表；None 或空字符串时不加条件。
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
    conditions = build_keyword_conditions(
        model,
        keyword,
        field_names,
        use_ilike=use_ilike,
    )
    if not conditions:
        return query
    return query.filter(or_(*conditions))


def apply_like_filter(
    query: Query,
    model: Type[Any],
    pattern: Optional[Union[str, Sequence[str]]],
    field_names: Union[str, Sequence[str]],
    *,
    use_ilike: bool = True,
) -> Query:
    """
    在已有 Query 上应用自定义 LIKE 模式过滤（pattern 可包含通配符）。
    """
    conditions = build_like_conditions(
        model,
        pattern,
        field_names,
        use_ilike=use_ilike,
    )
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
