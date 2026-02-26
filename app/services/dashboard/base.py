# -*- coding: utf-8 -*-
"""
Dashboard 服务基类 (#26)

提取各 dashboard 服务的通用模式：
- 时间范围过滤
- 缓存集成（通过 DashboardCacheService）
- 数据聚合辅助方法
- 统一的 Dict 返回格式

子类只需实现具体的数据查询逻辑。
"""

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Callable, Dict, List, Optional, TypeVar

from sqlalchemy import func
from sqlalchemy.orm import Session

def _get_cache_service_class():
    from app.services.dashboard_cache_service import DashboardCacheService
    return DashboardCacheService

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class DateRange:
    """时间范围"""
    start: date
    end: date

    @classmethod
    def this_month(cls, today: Optional[date] = None) -> "DateRange":
        today = today or date.today()
        start = date(today.year, today.month, 1)
        return cls(start=start, end=today)

    @classmethod
    def last_n_months(cls, n: int, today: Optional[date] = None) -> "DateRange":
        today = today or date.today()
        # Go back n months
        month = today.month - n
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        start = date(year, month, 1)
        return cls(start=start, end=today)

    @classmethod
    def this_quarter(cls, today: Optional[date] = None) -> "DateRange":
        today = today or date.today()
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        start = date(today.year, quarter_start_month, 1)
        return cls(start=start, end=today)

    @classmethod
    def this_year(cls, today: Optional[date] = None) -> "DateRange":
        today = today or date.today()
        return cls(start=date(today.year, 1, 1), end=today)


class BaseDashboardService:
    """
    Dashboard 服务基类

    提供通用的缓存、时间范围和聚合能力。
    子类应设置 `cache_prefix` 并实现具体的数据获取方法。

    Usage::

        class MyDashboardService(BaseDashboardService):
            cache_prefix = "my_module"

            def get_overview(self) -> Dict[str, Any]:
                return self.cached("overview", self._build_overview)

            def _build_overview(self) -> Dict[str, Any]:
                ...
    """

    cache_prefix: str = "dashboard"
    default_cache_ttl: int = 300  # seconds

    def __init__(self, db: Session, cache_service=None):
        self.db = db
        if cache_service is None:
            DashboardCacheService = _get_cache_service_class()
            cache_service = DashboardCacheService()
        self._cache = cache_service

    # ── 缓存辅助 ──────────────────────────────────────────

    def cached(
        self,
        key_suffix: str,
        builder: Callable[[], T],
        ttl: Optional[int] = None,
        **key_parts,
    ) -> T:
        """
        带缓存的数据获取。

        Args:
            key_suffix: 缓存键后缀（如 "overview"）
            builder: 无缓存时的数据构建函数
            ttl: 自定义 TTL（秒），默认使用 default_cache_ttl
            **key_parts: 额外的缓存键部分（如 project_id=123）
        """
        cache_key = self._cache._get_cache_key(
            f"{self.cache_prefix}:{key_suffix}", **key_parts
        )
        result = self._cache.get(cache_key)
        if result is not None:
            return result

        result = builder()

        # 临时设置 TTL 如果自定义
        original_ttl = self._cache.ttl
        if ttl is not None:
            self._cache.ttl = ttl
        self._cache.set(cache_key, result)
        if ttl is not None:
            self._cache.ttl = original_ttl

        return result

    def invalidate(self, key_suffix: str, **key_parts) -> None:
        """删除指定缓存"""
        cache_key = self._cache._get_cache_key(
            f"{self.cache_prefix}:{key_suffix}", **key_parts
        )
        self._cache.delete(cache_key)

    # ── 时间范围 ──────────────────────────────────────────

    @staticmethod
    def date_range(period: str = "month", today: Optional[date] = None) -> DateRange:
        """
        快捷获取时间范围。

        Args:
            period: "month", "quarter", "year", "last_3m", "last_6m"
            today: 基准日期
        """
        factories = {
            "month": DateRange.this_month,
            "quarter": DateRange.this_quarter,
            "year": DateRange.this_year,
            "last_3m": lambda t: DateRange.last_n_months(3, t),
            "last_6m": lambda t: DateRange.last_n_months(6, t),
        }
        factory = factories.get(period)
        if factory is None:
            raise ValueError(f"Unknown period: {period}. Use: {list(factories.keys())}")
        return factory(today)

    # ── 聚合辅助 ──────────────────────────────────────────

    def aggregate_sum(self, model, column, filters=None) -> float:
        """
        对指定列求和。

        Args:
            model: SQLAlchemy 模型
            column: 模型字段
            filters: 可选的过滤条件列表
        """
        q = self.db.query(func.coalesce(func.sum(column), 0))
        if filters:
            q = q.filter(*filters)
        result = q.scalar()
        return float(result or 0)

    def aggregate_count(self, model, filters=None) -> int:
        """对指定模型计数。"""
        q = self.db.query(func.count(model.id))
        if filters:
            q = q.filter(*filters)
        return q.scalar() or 0

    def aggregate_avg(self, model, column, filters=None) -> float:
        """对指定列求平均。"""
        q = self.db.query(func.coalesce(func.avg(column), 0))
        if filters:
            q = q.filter(*filters)
        return float(q.scalar() or 0)

    # ── 格式化辅助 ──────────────────────────────────────────

    @staticmethod
    def pct(numerator: float, denominator: float, decimals: int = 1) -> float:
        """安全计算百分比"""
        if denominator == 0:
            return 0.0
        return round(numerator / denominator * 100, decimals)

    @staticmethod
    def safe_float(value, default: float = 0.0) -> float:
        """安全转换为 float"""
        try:
            return float(value) if value is not None else default
        except (TypeError, ValueError):
            return default
