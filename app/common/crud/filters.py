# -*- coding: utf-8 -*-
"""
通用查询构建器
支持筛选、排序、分页、关键词搜索
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type, TypeVar
from sqlalchemy import Select, and_, or_, func, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud.types import SortOrder
from app.common.query_filters import build_keyword_conditions
ModelType = TypeVar("ModelType")


class QueryBuilder:
    """统一查询构建器"""
    
    @staticmethod
    def build_list_query(
        model: Type[ModelType],
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        keyword: Optional[str] = None,
        keyword_fields: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        order_direction: str | SortOrder = "asc"
    ) -> tuple[Select, Select]:
        """
        构建列表查询
        
        Args:
            model: SQLAlchemy模型类
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数
            filters: 筛选条件字典，支持多种格式：
                - 精确匹配: {"status": "ACTIVE"}
                - 列表匹配: {"status": ["ACTIVE", "PENDING"]}
                - 范围查询: {"price": {"min": 100, "max": 1000}}
                - 模糊匹配: {"name": {"like": "test"}}
                - 空值查询: {"deleted_at": None}
            keyword: 关键词搜索
            keyword_fields: 关键词搜索的字段列表
            order_by: 排序字段
            order_direction: 排序方向 (asc/desc)
        
        Returns:
            (查询对象, 计数查询对象)
        """
        from sqlalchemy import select
        
        # 基础查询
        query = select(model)
        count_query = select(func.count()).select_from(model)
        
        conditions = []
        
        # 应用筛选条件
        if filters:
            filter_conditions = QueryBuilder._build_filter_conditions(
                model, filters
            )
            if filter_conditions:
                conditions.extend(filter_conditions)
        
        # 应用关键词搜索
        if keyword and keyword_fields:
            keyword_conditions = QueryBuilder._build_keyword_conditions(
                model, keyword, keyword_fields
            )
            if keyword_conditions:
                conditions.append(or_(*keyword_conditions))
        
        # 应用所有条件
        if conditions:
            where_clause = and_(*conditions)
            query = query.where(where_clause)
            count_query = count_query.where(where_clause)
        
        # 应用排序
        direction = (
            order_direction.value
            if isinstance(order_direction, SortOrder)
            else str(order_direction or "asc").lower()
        )

        if order_by:
            order_field = getattr(model, order_by, None)
            if order_field:
                if direction == "desc":
                    query = query.order_by(desc(order_field))
                else:
                    query = query.order_by(asc(order_field))
        
        # 应用分页
        if skip > 0:
            query = query.offset(skip)
        if limit > 0:
            query = query.limit(limit)
        
        return query, count_query
    
    @staticmethod
    def _build_filter_conditions(
        model: Type[ModelType],
        filters: Dict[str, Any]
    ) -> List:
        """构建筛选条件"""
        conditions = []
        
        for field_name, value in filters.items():
            if value is None:
                continue
            
            # 获取模型字段
            field = getattr(model, field_name, None)
            if not field:
                continue
            
            # 处理不同类型的筛选
            if isinstance(value, list):
                # 列表匹配：{"status": ["ACTIVE", "PENDING"]}
                conditions.append(field.in_(value))
            
            elif isinstance(value, dict):
                # 字典格式的复杂查询
                if "min" in value or "max" in value:
                    # 范围查询：{"price": {"min": 100, "max": 1000}}
                    if "min" in value:
                        conditions.append(field >= value["min"])
                    if "max" in value:
                        conditions.append(field <= value["max"])
                
                elif "like" in value:
                    # 模糊匹配：{"name": {"like": "test"}}
                    like_conditions = build_keyword_conditions(
                        model,
                        value.get("like"),
                        field_name,
                    )
                    if like_conditions:
                        conditions.append(or_(*like_conditions))
                
                elif "in" in value:
                    # IN查询：{"id": {"in": [1, 2, 3]}}
                    conditions.append(field.in_(value["in"]))
                
                elif "not_in" in value:
                    # NOT IN查询
                    conditions.append(~field.in_(value["not_in"]))
                
                elif "is_null" in value:
                    # NULL查询：{"deleted_at": {"is_null": True}}
                    if value["is_null"]:
                        conditions.append(field.is_(None))
                    else:
                        conditions.append(field.isnot(None))
            
            else:
                # 精确匹配
                conditions.append(field == value)
        
        return conditions
    
    @staticmethod
    def _build_keyword_conditions(
        model: Type[ModelType],
        keyword: str,
        fields: List[str]
    ) -> List:
        """构建关键词搜索条件"""
        return build_keyword_conditions(model, keyword, fields)
    
    @staticmethod
    async def execute_list_query(
        query: Select,
        count_query: Select,
        db: AsyncSession
    ) -> tuple[List[ModelType], int]:
        """
        执行列表查询
        
        Returns:
            (结果列表, 总数)
        """
        # 执行计数查询
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 执行数据查询
        result = await db.execute(query)
        items = result.scalars().all()
        
        return list(items), total
