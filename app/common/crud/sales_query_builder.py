# -*- coding: utf-8 -*-
"""
销售模块链式查询构建器

消除销售端点中分页、筛选、排序、权限过滤的重复代码。
复用现有工具：filter_sales_data_by_scope、apply_keyword_filter、apply_pagination。

使用示例:
    result = (
        SalesQueryBuilder(db, Lead, LEAD_CONFIG)
        .with_scope_filter(current_user)
        .with_keyword(keyword)
        .with_status(status)
        .with_owner(owner_id)
        .with_sort(nulls_last=True)
        .with_pagination(pagination)
        .execute_with_transform(transform_lead)
    )
    return result.to_paginated_response()
"""

from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from sqlalchemy import asc, desc
from sqlalchemy.orm import Query, Session

from app.common.pagination import PaginationParams
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core.sales_permissions import filter_sales_data_by_scope
from app.models.user import User

ModelType = TypeVar("ModelType")
TransformType = TypeVar("TransformType")


@dataclass(frozen=True)
class SalesQueryConfig:
    """
    销售查询配置（不可变）

    定义模型的搜索字段、默认排序等配置，在模块级别定义一次即可复用。

    Attributes:
        keyword_fields: 关键词搜索的字段列表
        default_sort_field: 默认排序字段
        default_sort_desc: 默认是否降序
        owner_field: 负责人字段名（用于权限过滤）
    """

    keyword_fields: Sequence[str] = field(default_factory=list)
    default_sort_field: str = "created_at"
    default_sort_desc: bool = True
    owner_field: str = "owner_id"


@dataclass
class SalesQueryResult(Generic[ModelType]):
    """
    查询结果容器

    包含查询结果列表和分页信息，提供便捷的响应构造方法。

    Attributes:
        items: 查询结果列表
        total: 总记录数
        pagination: 分页参数（可选）
    """

    items: List[ModelType]
    total: int
    pagination: Optional[PaginationParams] = None

    def to_paginated_response(self) -> dict:
        """
        构造分页响应字典

        Returns:
            包含 items, total, page, page_size, pages 的字典
        """
        if self.pagination:
            return self.pagination.to_response(self.items, self.total)
        return {
            "items": self.items,
            "total": self.total,
            "page": 1,
            "page_size": len(self.items),
            "pages": 1 if self.items else 0,
        }


class SalesQueryBuilder(Generic[ModelType]):
    """
    链式销售查询构建器

    通过链式调用构建复杂查询，自动处理权限过滤、关键词搜索、
    状态筛选、排序和分页，减少端点代码中的重复逻辑。

    所有 with_* 方法返回 self，支持链式调用。
    调用 execute() 或 execute_with_transform() 执行查询。
    """

    def __init__(
        self,
        db: Session,
        model: Type[ModelType],
        config: Optional[SalesQueryConfig] = None,
    ) -> None:
        """
        初始化查询构建器

        Args:
            db: 数据库会话
            model: SQLAlchemy 模型类
            config: 查询配置（可选，使用默认配置）
        """
        self._db = db
        self._model = model
        self._config = config or SalesQueryConfig()
        self._query: Query = db.query(model)
        self._pagination: Optional[PaginationParams] = None

        # 排序参数（延迟应用）
        self._sort_field: Optional[str] = None
        self._sort_desc: Optional[bool] = None
        self._nulls_last: bool = False
        self._skip_default_sort: bool = False

        # joinedload 选项（延迟应用）
        self._join_options: List[Any] = []

    def with_options(self, *options: Any) -> "SalesQueryBuilder[ModelType]":
        """
        添加 SQLAlchemy 查询选项（如 joinedload）

        Args:
            *options: 查询选项列表

        Returns:
            self，支持链式调用
        """
        self._join_options.extend(options)
        return self

    def with_scope_filter(
        self,
        user: User,
        owner_field: Optional[str] = None,
    ) -> "SalesQueryBuilder[ModelType]":
        """
        应用数据权限过滤

        根据用户角色和数据权限范围过滤查询结果。

        Args:
            user: 当前用户
            owner_field: 负责人字段名（覆盖配置）

        Returns:
            self，支持链式调用
        """
        field_name = owner_field or self._config.owner_field
        self._query = filter_sales_data_by_scope(
            self._query,
            user,
            self._db,
            self._model,
            field_name,
        )
        return self

    def with_keyword(
        self,
        keyword: Optional[str],
        fields: Optional[Sequence[str]] = None,
    ) -> "SalesQueryBuilder[ModelType]":
        """
        应用关键词搜索

        在指定字段中模糊匹配关键词。

        Args:
            keyword: 搜索关键词（为空时跳过）
            fields: 搜索字段列表（覆盖配置）

        Returns:
            self，支持链式调用
        """
        if not keyword:
            return self
        search_fields = fields or self._config.keyword_fields
        if search_fields:
            self._query = apply_keyword_filter(
                self._query,
                self._model,
                keyword,
                list(search_fields),
            )
        return self

    def with_filter(
        self,
        field_name: str,
        value: Any,
    ) -> "SalesQueryBuilder[ModelType]":
        """
        添加单字段精确过滤

        Args:
            field_name: 字段名
            value: 过滤值（为 None 时跳过）

        Returns:
            self，支持链式调用
        """
        if value is None:
            return self
        column = getattr(self._model, field_name, None)
        if column is not None:
            self._query = self._query.filter(column == value)
        return self

    def with_filter_in(
        self,
        field_name: str,
        values: Optional[Sequence[Any]],
    ) -> "SalesQueryBuilder[ModelType]":
        """
        添加 IN 过滤（多值匹配）

        Args:
            field_name: 字段名
            values: 值列表（为空时跳过）

        Returns:
            self，支持链式调用
        """
        if not values:
            return self
        column = getattr(self._model, field_name, None)
        if column is not None:
            self._query = self._query.filter(column.in_(values))
        return self

    def with_status(
        self,
        status: Optional[Union[str, Sequence[str]]],
        field_name: str = "status",
    ) -> "SalesQueryBuilder[ModelType]":
        """
        添加状态过滤

        支持单个状态或逗号分隔的多个状态。

        Args:
            status: 状态值或逗号分隔的状态列表（为空时跳过）
            field_name: 状态字段名（默认 "status"）

        Returns:
            self，支持链式调用
        """
        if not status:
            return self

        column = getattr(self._model, field_name, None)
        if column is None:
            return self

        # 处理逗号分隔的多个状态
        if isinstance(status, str):
            status_values = [s.strip() for s in status.split(",") if s.strip()]
        else:
            status_values = list(status)

        if len(status_values) == 1:
            self._query = self._query.filter(column == status_values[0])
        elif status_values:
            self._query = self._query.filter(column.in_(status_values))

        return self

    def with_owner(
        self,
        owner_id: Optional[int],
        field_name: Optional[str] = None,
    ) -> "SalesQueryBuilder[ModelType]":
        """
        添加负责人过滤

        Args:
            owner_id: 负责人 ID（为空时跳过）
            field_name: 负责人字段名（覆盖配置）

        Returns:
            self，支持链式调用
        """
        if owner_id is None:
            return self
        field = field_name or self._config.owner_field
        return self.with_filter(field, owner_id)

    def with_customer(
        self,
        customer_id: Optional[int],
        field_name: str = "customer_id",
    ) -> "SalesQueryBuilder[ModelType]":
        """
        添加客户过滤

        Args:
            customer_id: 客户 ID（为空时跳过）
            field_name: 客户字段名（默认 "customer_id"）

        Returns:
            self，支持链式调用
        """
        return self.with_filter(field_name, customer_id)

    def with_date_range(
        self,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None,
        field_name: str = "created_at",
    ) -> "SalesQueryBuilder[ModelType]":
        """
        添加日期范围过滤

        Args:
            start_date: 开始日期（为空时跳过）
            end_date: 结束日期（为空时跳过）
            field_name: 日期字段名（默认 "created_at"）

        Returns:
            self，支持链式调用
        """
        column = getattr(self._model, field_name, None)
        if column is None:
            return self

        if start_date is not None:
            self._query = self._query.filter(column >= start_date)
        if end_date is not None:
            self._query = self._query.filter(column <= end_date)

        return self

    def with_sort(
        self,
        field: Optional[str] = None,
        is_desc: Optional[bool] = None,
        nulls_last: bool = False,
    ) -> "SalesQueryBuilder[ModelType]":
        """
        设置排序

        排序在 execute() 时应用，支持 nulls_last 处理空值排序。

        Args:
            field: 排序字段（覆盖配置）
            is_desc: 是否降序（覆盖配置）
            nulls_last: 空值排在最后

        Returns:
            self，支持链式调用
        """
        self._sort_field = field or self._config.default_sort_field
        self._sort_desc = is_desc if is_desc is not None else self._config.default_sort_desc
        self._nulls_last = nulls_last
        return self

    def with_secondary_sort(
        self,
        field: str = "created_at",
        is_desc: bool = True,
    ) -> "SalesQueryBuilder[ModelType]":
        """
        添加二级排序（在主排序之后）

        注意：此方法需要在 with_sort 之后调用。

        Args:
            field: 排序字段
            is_desc: 是否降序

        Returns:
            self，支持链式调用
        """
        # 二级排序存储在额外属性中，在 _apply_sort 时处理
        if not hasattr(self, "_secondary_sorts"):
            self._secondary_sorts: List[Tuple[str, bool]] = []
        self._secondary_sorts.append((field, is_desc))
        return self

    def with_pagination(
        self,
        pagination: Optional[PaginationParams],
    ) -> "SalesQueryBuilder[ModelType]":
        """
        设置分页参数

        分页在 execute() 时应用。

        Args:
            pagination: 分页参数对象

        Returns:
            self，支持链式调用
        """
        self._pagination = pagination
        return self

    def with_raw_query_modifier(
        self,
        modifier: Callable[["Query"], "Query"],
    ) -> "SalesQueryBuilder[ModelType]":
        """
        应用自定义查询修改器

        用于处理非标准的过滤逻辑（如 join 权限过滤）。

        Args:
            modifier: 接收 Query 并返回修改后 Query 的函数

        Returns:
            self，支持链式调用

        示例:
            def apply_join_permission(query):
                if not is_admin(user):
                    return query.join(Customer).filter(Customer.owner_id == user.id)
                return query

            builder.with_raw_query_modifier(apply_join_permission)
        """
        self._query = modifier(self._query)
        return self

    def without_default_sort(self) -> "SalesQueryBuilder[ModelType]":
        """
        跳过默认排序

        当使用 with_raw_query_modifier 自定义排序时调用此方法，
        避免 execute() 重复应用默认排序。

        Returns:
            self，支持链式调用
        """
        self._skip_default_sort = True
        return self

    def _apply_options(self) -> None:
        """应用 joinedload 等查询选项"""
        if self._join_options:
            self._query = self._query.options(*self._join_options)

    def _apply_sort(self) -> None:
        """应用排序（如果未被跳过）"""
        if self._skip_default_sort:
            return

        sort_field = self._sort_field or self._config.default_sort_field
        is_desc = (
            self._sort_desc if self._sort_desc is not None else self._config.default_sort_desc
        )

        column = getattr(self._model, sort_field, None)
        if column is not None:
            if is_desc:
                order_clause = desc(column)
            else:
                order_clause = asc(column)

            if self._nulls_last:
                order_clause = order_clause.nullslast()

            self._query = self._query.order_by(order_clause)

        # 应用二级排序
        if hasattr(self, "_secondary_sorts"):
            for sec_field, sec_desc in self._secondary_sorts:
                sec_column = getattr(self._model, sec_field, None)
                if sec_column is not None:
                    if sec_desc:
                        self._query = self._query.order_by(desc(sec_column))
                    else:
                        self._query = self._query.order_by(asc(sec_column))

    def _apply_pagination(self) -> None:
        """应用分页"""
        if self._pagination:
            self._query = apply_pagination(
                self._query,
                self._pagination.offset,
                self._pagination.limit,
            )

    def count(self) -> int:
        """
        获取查询总数（不含分页）

        Returns:
            符合条件的记录总数
        """
        return self._query.count()

    def execute(self) -> SalesQueryResult[ModelType]:
        """
        执行查询并返回原始模型对象

        Returns:
            SalesQueryResult 包含模型对象列表和分页信息
        """
        # 先计数（分页之前）
        total = self._query.count()

        # 应用选项、排序、分页
        self._apply_options()
        self._apply_sort()
        self._apply_pagination()

        # 执行查询
        items = self._query.all()

        return SalesQueryResult(
            items=items,
            total=total,
            pagination=self._pagination,
        )

    def execute_with_transform(
        self,
        transform_fn: Callable[[ModelType], TransformType],
    ) -> SalesQueryResult[TransformType]:
        """
        执行查询并对每个结果应用转换函数

        Args:
            transform_fn: 转换函数，将模型对象转换为响应对象

        Returns:
            SalesQueryResult 包含转换后的对象列表和分页信息
        """
        result = self.execute()
        transformed_items = [transform_fn(item) for item in result.items]

        return SalesQueryResult(
            items=transformed_items,
            total=result.total,
            pagination=result.pagination,
        )

    def get_query(self) -> Query:
        """
        获取构建的查询对象（用于自定义处理）

        注意：调用此方法后不应再使用 execute() 方法。

        Returns:
            SQLAlchemy Query 对象
        """
        self._apply_options()
        self._apply_sort()
        self._apply_pagination()
        return self._query
