# -*- coding: utf-8 -*-
"""
同步统计服务基类 & 聚合协议

设计目标:
- 为现有的同步统计服务提供可选基类，减少重复的 count-by-field 模式
- 定义聚合服务协议，统一 timesheet/project_cost/performance 等聚合接口
- 不强制迁移，现有服务可按需逐步采用

与 app.common.statistics.base.BaseStatisticsService 的区别:
- 本基类使用同步 Session（项目中大部分服务是同步的）
- BaseStatisticsService 使用 AsyncSession，适合异步端点
"""

from abc import abstractmethod
from datetime import date
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    runtime_checkable,
)

from sqlalchemy import func
from sqlalchemy.orm import Session

T = TypeVar("T")


class SyncStatisticsService:
    """
    同步统计服务基类

    子类需要设置:
        model: SQLAlchemy 模型类
        default_status_field: 默认状态字段名 (默认 "status")
        default_exclude_statuses: 默认排除的状态列表 (默认 [])

    Example::

        class IssueStatistics(SyncStatisticsService):
            model = Issue
            default_exclude_statuses = ["DELETED"]

            def get_severity_distribution(self) -> Dict[str, int]:
                return self.count_by_field("severity")
    """

    model: ClassVar[Type[Any]]
    default_status_field: ClassVar[str] = "status"
    default_exclude_statuses: ClassVar[List[str]] = []

    def __init__(self, db: Session):
        self.db = db

    def _base_query(self):
        """返回基础查询（排除默认排除状态）"""
        q = self.db.query(self.model)
        if self.default_exclude_statuses:
            status_col = getattr(self.model, self.default_status_field)
            q = q.filter(status_col.notin_(self.default_exclude_statuses))
        return q

    def count_total(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """统计总数"""
        q = self._base_query()
        if filters:
            for field, value in filters.items():
                q = q.filter(getattr(self.model, field) == value)
        return q.count()

    def count_by_field(
        self,
        field: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, int]:
        """
        按指定字段分组计数

        Args:
            field: 模型字段名
            filters: 额外过滤条件 {field_name: value}

        Returns:
            {字段值: 数量}
        """
        col = getattr(self.model, field)
        q = self.db.query(col, func.count(self.model.id)).filter(
            col.isnot(None)
        )
        # 应用排除状态
        if self.default_exclude_statuses:
            status_col = getattr(self.model, self.default_status_field)
            q = q.filter(status_col.notin_(self.default_exclude_statuses))
        if filters:
            for f, v in filters.items():
                q = q.filter(getattr(self.model, f) == v)
        q = q.group_by(col)
        return {str(row[0]): row[1] for row in q.all()}

    def count_by_status(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, int]:
        """按状态字段分组计数"""
        return self.count_by_field(self.default_status_field, filters)


@runtime_checkable
class AggregationServiceProtocol(Protocol):
    """
    聚合服务协议

    定义聚合服务的通用接口，用于类型检查。
    现有的聚合服务（TimesheetAggregationService, ProjectCostAggregationService,
    PerformanceDataAggregator）可逐步实现此协议。

    这是一个 Protocol，不需要显式继承，只要实现了对应方法即可通过类型检查。
    """

    def aggregate(
        self,
        start_date: date,
        end_date: date,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        执行聚合计算

        Args:
            start_date: 聚合开始日期
            end_date: 聚合结束日期
            **kwargs: 额外过滤参数

        Returns:
            聚合结果字典
        """
        ...
