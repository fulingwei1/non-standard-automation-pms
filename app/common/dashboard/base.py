# -*- coding: utf-8 -*-
"""
统一Dashboard服务基类
提供所有Dashboard服务的通用功能和标准接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type, TypeVar
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

ModelType = TypeVar("ModelType")


class BaseDashboardService(ABC):
    """
    统一Dashboard服务基类
    
    所有Dashboard服务都应继承此类，实现统一的接口和通用功能。
    支持同步数据库会话（Session）。
    
    使用示例:
    ```python
    class ProjectDashboardService(BaseDashboardService):
        def __init__(self, db: Session):
            super().__init__(db)
            # 初始化特定模型或服务
        
        def get_overview(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            # 实现特定的概览逻辑
            return {
                "total": 100,
                "active": 50,
                ...
            }
        
        def get_dashboard_data(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            # 可以重写以自定义Dashboard结构
            return {
                "overview": self.get_overview(filters),
                "stats": self.get_stats(filters),
                ...
            }
    ```
    """
    
    def __init__(self, db: Session):
        """
        初始化Dashboard服务
        
        Args:
            db: 数据库会话（同步Session）
        """
        self.db = db
    
    # ========== 抽象方法（子类必须实现） ==========
    
    @abstractmethod
    def get_overview(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        获取概览数据
        
        子类必须实现此方法，返回Dashboard的核心统计指标。
        
        Args:
            filters: 筛选条件字典
        
        Returns:
            概览数据字典，通常包含：
            - total: 总数
            - active: 活跃数
            - pending: 待处理数
            - completed: 完成数
            - 其他业务特定指标
        """
        pass
    
    # ========== 可选重写方法（子类可以重写以自定义行为） ==========
    
    def get_stats(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        获取统计数据
        
        子类可以重写此方法以实现特定的统计逻辑。
        默认返回空字典。
        
        Args:
            filters: 筛选条件
        
        Returns:
            统计数据字典
        """
        return {}
    
    def get_trends(
        self,
        date_field: str = "created_at",
        days: int = 30,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取趋势数据
        
        子类可以重写此方法以实现特定的趋势计算逻辑。
        
        Args:
            date_field: 日期字段名
            days: 统计天数
            filters: 筛选条件
        
        Returns:
            趋势数据列表，格式: [{"date": "2026-01-01", "value": 10}, ...]
        """
        return []
    
    def get_distribution(
        self,
        field: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        获取分布数据
        
        子类可以重写此方法以实现特定的分布计算逻辑。
        
        Args:
            field: 字段名
            filters: 筛选条件
        
        Returns:
            分布数据字典，格式:
            {
                "distribution": {值: 数量},
                "total": 总数,
                "percentages": {值: 百分比}
            }
        """
        return {
            "distribution": {},
            "total": 0,
            "percentages": {}
        }
    
    def get_recent_items(
        self,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取最近项目/记录列表
        
        子类可以重写此方法以实现特定的最近记录逻辑。
        
        Args:
            limit: 返回数量限制
            filters: 筛选条件
        
        Returns:
            最近记录列表
        """
        return []
    
    def get_alerts(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取预警/提醒列表
        
        子类可以重写此方法以实现特定的预警逻辑。
        
        Args:
            filters: 筛选条件
        
        Returns:
            预警列表
        """
        return []
    
    def get_dashboard_data(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        获取完整的Dashboard数据
        
        子类可以重写此方法以自定义Dashboard结构。
        默认实现组合了所有标准方法的结果。
        
        Args:
            filters: 筛选条件
        
        Returns:
            完整的Dashboard数据字典
        """
        return {
            "overview": self.get_overview(filters),
            "stats": self.get_stats(filters),
            "trends": self.get_trends(filters=filters),
            "distribution": self.get_distribution("status", filters) if filters else {},
            "recent_items": self.get_recent_items(filters=filters),
            "alerts": self.get_alerts(filters),
            "timestamp": datetime.now().isoformat()
        }
    
    # ========== 通用工具方法（子类可以直接使用） ==========
    
    def count_by_status(
        self,
        model: Type[ModelType],
        status_field: str = "status",
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """
        按状态统计
        
        Args:
            model: SQLAlchemy模型类
            status_field: 状态字段名
            filters: 额外的筛选条件
        
        Returns:
            {状态值: 数量}
        """
        query = self.db.query(
            getattr(model, status_field),
            func.count(model.id)
        )
        
        # 应用额外筛选
        if filters:
            query = self._apply_filters(query, model, filters)
        
        query = query.group_by(getattr(model, status_field))
        results = query.all()
        
        return {status: count for status, count in results if status is not None}
    
    def count_by_field(
        self,
        model: Type[ModelType],
        field: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """
        按字段统计
        
        Args:
            model: SQLAlchemy模型类
            field: 字段名
            filters: 额外的筛选条件
        
        Returns:
            {字段值: 数量}
        """
        model_field = getattr(model, field, None)
        if not model_field:
            raise ValueError(f"字段 {field} 不存在于模型 {model.__name__}")
        
        query = self.db.query(
            model_field,
            func.count(model.id)
        )
        
        # 应用额外筛选
        if filters:
            query = self._apply_filters(query, model, filters)
        
        query = query.group_by(model_field)
        results = query.all()
        
        return {value: count for value, count in results if value is not None}
    
    def count_total(
        self,
        model: Type[ModelType],
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        统计总数
        
        Args:
            model: SQLAlchemy模型类
            filters: 筛选条件
        
        Returns:
            总数
        """
        query = self.db.query(model)
        
        if filters:
            query = self._apply_filters(query, model, filters)
        
        return query.count()
    
    def calculate_sum(
        self,
        model: Type[ModelType],
        field: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        计算字段总和
        
        Args:
            model: SQLAlchemy模型类
            field: 数值字段名
            filters: 筛选条件
        
        Returns:
            总和
        """
        model_field = getattr(model, field, None)
        if not model_field:
            raise ValueError(f"字段 {field} 不存在于模型 {model.__name__}")
        
        query = self.db.query(func.sum(model_field))
        
        if filters:
            query = self._apply_filters(query, model, filters)
        
        result = query.scalar()
        return float(result or 0)
    
    def calculate_avg(
        self,
        model: Type[ModelType],
        field: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        计算字段平均值
        
        Args:
            model: SQLAlchemy模型类
            field: 数值字段名
            filters: 筛选条件
        
        Returns:
            平均值
        """
        model_field = getattr(model, field, None)
        if not model_field:
            raise ValueError(f"字段 {field} 不存在于模型 {model.__name__}")
        
        query = self.db.query(func.avg(model_field))
        
        if filters:
            query = self._apply_filters(query, model, filters)
        
        result = query.scalar()
        return float(result or 0)
    
    def get_trend_by_date(
        self,
        model: Type[ModelType],
        date_field: str,
        value_field: Optional[str] = None,
        days: int = 30,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取按日期的趋势数据
        
        Args:
            model: SQLAlchemy模型类
            date_field: 日期字段名
            value_field: 值字段名（如果为None，则统计数量）
            days: 统计天数
            filters: 筛选条件
        
        Returns:
            趋势数据列表，格式: [{"date": "2026-01-01", "value": 10}, ...]
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        model_date_field = getattr(model, date_field, None)
        if not model_date_field:
            raise ValueError(f"字段 {date_field} 不存在于模型 {model.__name__}")
        
        if value_field:
            # 按值字段聚合
            model_value_field = getattr(model, value_field, None)
            if not model_value_field:
                raise ValueError(f"字段 {value_field} 不存在于模型 {model.__name__}")
            
            query = self.db.query(
                func.date(model_date_field).label("date"),
                func.sum(model_value_field).label("value")
            ).filter(
                and_(
                    model_date_field >= start_date,
                    model_date_field <= end_date
                )
            )
        else:
            # 统计数量
            query = self.db.query(
                func.date(model_date_field).label("date"),
                func.count(model.id).label("value")
            ).filter(
                and_(
                    model_date_field >= start_date,
                    model_date_field <= end_date
                )
            )
        
        # 应用额外筛选
        if filters:
            query = self._apply_filters(query, model, filters)
        
        query = query.group_by(func.date(model_date_field)).order_by(func.date(model_date_field))
        results = query.all()
        
        return [
            {"date": str(row.date), "value": float(row.value or 0)}
            for row in results
        ]
    
    # ========== 私有辅助方法 ==========
    
    def _apply_filters(
        self,
        query,
        model: Type[ModelType],
        filters: Dict[str, Any]
    ):
        """
        应用筛选条件到查询
        
        Args:
            query: SQLAlchemy查询对象
            model: SQLAlchemy模型类
            filters: 筛选条件字典
        
        Returns:
            应用筛选后的查询对象
        """
        # 简单的筛选实现
        # 可以根据需要扩展更复杂的筛选逻辑
        for key, value in filters.items():
            if hasattr(model, key):
                model_field = getattr(model, key)
                if isinstance(value, list):
                    query = query.filter(model_field.in_(value))
                elif isinstance(value, dict):
                    # 支持范围查询等复杂条件
                    if "gte" in value:
                        query = query.filter(model_field >= value["gte"])
                    if "lte" in value:
                        query = query.filter(model_field <= value["lte"])
                    if "gt" in value:
                        query = query.filter(model_field > value["gt"])
                    if "lt" in value:
                        query = query.filter(model_field < value["lt"])
                else:
                    query = query.filter(model_field == value)
        
        return query
