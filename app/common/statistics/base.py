# -*- coding: utf-8 -*-
"""
统一统计服务基类
所有统计功能都基于此基类实现
"""

from typing import Dict, List, Any, Optional, Type, TypeVar
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_, or_
from sqlalchemy.orm import Query

from app.common.crud.filters import QueryBuilder

ModelType = TypeVar("ModelType")


class BaseStatisticsService:
    """统一统计服务基类"""
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        Args:
            model: SQLAlchemy模型类
            db: 数据库会话
        """
        self.model = model
        self.db = db
    
    async def count_by_status(
        self,
        status_field: str = "status",
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """
        按状态统计
        
        Args:
            status_field: 状态字段名
            filters: 额外的筛选条件
        
        Returns:
            {状态值: 数量}
        """
        query = select(
            getattr(self.model, status_field),
            func.count(self.model.id)
        )
        
        # 应用额外筛选
        if filters:
            conditions = QueryBuilder._build_filter_conditions(self.model, filters)
            if conditions:
                query = query.where(and_(*conditions))
        
        query = query.group_by(getattr(self.model, status_field))
        result = await self.db.execute(query)
        
        return {row[0]: row[1] for row in result.all() if row[0] is not None}
    
    async def count_by_field(
        self,
        field: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """
        按字段统计
        
        Args:
            field: 字段名
            filters: 额外的筛选条件
        
        Returns:
            {字段值: 数量}
        """
        model_field = getattr(self.model, field, None)
        if not model_field:
            raise ValueError(f"字段 {field} 不存在")
        
        query = select(
            model_field,
            func.count(self.model.id)
        )
        
        # 应用额外筛选
        if filters:
            conditions = QueryBuilder._build_filter_conditions(self.model, filters)
            if conditions:
                query = query.where(and_(*conditions))
        
        query = query.group_by(model_field)
        result = await self.db.execute(query)
        
        return {row[0]: row[1] for row in result.all() if row[0] is not None}
    
    async def count_total(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """统计总数"""
        return await QueryBuilder.execute_list_query(
            *QueryBuilder.build_list_query(
                model=self.model,
                db=self.db,
                filters=filters
            ),
            self.db
        )[1]
    
    async def count_by_date_range(
        self,
        date_field: str,
        start_date: date,
        end_date: date,
        period: str = "day",  # day, week, month
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        按日期范围统计
        
        Args:
            date_field: 日期字段名
            start_date: 开始日期
            end_date: 结束日期
            period: 统计周期（day/week/month）
            filters: 额外的筛选条件
        
        Returns:
            [{"date": "2026-01-01", "count": 10}, ...]
        """
        model_field = getattr(self.model, date_field, None)
        if not model_field:
            raise ValueError(f"字段 {date_field} 不存在")
        
        # 根据周期选择日期格式化函数
        if period == "day":
            date_format = func.date(model_field)
        elif period == "week":
            date_format = func.date_trunc('week', model_field)
        elif period == "month":
            date_format = func.date_trunc('month', model_field)
        else:
            raise ValueError(f"不支持的周期: {period}")
        
        query = select(
            date_format.label("date"),
            func.count(self.model.id).label("count")
        ).where(
            and_(
                model_field >= start_date,
                model_field <= end_date
            )
        )
        
        # 应用额外筛选
        if filters:
            conditions = QueryBuilder._build_filter_conditions(self.model, filters)
            if conditions:
                query = query.where(and_(*conditions))
        
        query = query.group_by(date_format).order_by(date_format)
        result = await self.db.execute(query)
        
        return [
            {"date": str(row[0]), "count": row[1]}
            for row in result.all()
        ]
    
    async def get_trend(
        self,
        date_field: str,
        value_field: Optional[str] = None,
        period: str = "day",
        days: int = 30,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取趋势数据
        
        Args:
            date_field: 日期字段名
            value_field: 值字段名（如果为None，则统计数量）
            period: 统计周期
            days: 统计天数
            filters: 额外的筛选条件
        
        Returns:
            [{"date": "2026-01-01", "value": 10}, ...]
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        if value_field:
            # 按值字段聚合
            model_value_field = getattr(self.model, value_field, None)
            if not model_value_field:
                raise ValueError(f"字段 {value_field} 不存在")
            
            # 根据周期选择日期格式化函数
            if period == "day":
                date_format = func.date(getattr(self.model, date_field))
            elif period == "week":
                date_format = func.date_trunc('week', getattr(self.model, date_field))
            elif period == "month":
                date_format = func.date_trunc('month', getattr(self.model, date_field))
            else:
                raise ValueError(f"不支持的周期: {period}")
            
            query = select(
                date_format.label("date"),
                func.sum(model_value_field).label("value")
            ).where(
                and_(
                    getattr(self.model, date_field) >= start_date,
                    getattr(self.model, date_field) <= end_date
                )
            )
            
            # 应用额外筛选
            if filters:
                conditions = QueryBuilder._build_filter_conditions(self.model, filters)
                if conditions:
                    query = query.where(and_(*conditions))
            
            query = query.group_by(date_format).order_by(date_format)
            result = await self.db.execute(query)
            
            return [
                {"date": str(row[0]), "value": float(row[1] or 0)}
                for row in result.all()
            ]
        else:
            # 统计数量
            return await self.count_by_date_range(
                date_field, start_date, end_date, period, filters
            )
    
    async def get_distribution(
        self,
        field: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        获取分布数据
        
        Args:
            field: 字段名
            filters: 额外的筛选条件
        
        Returns:
            {
                "distribution": {字段值: 数量},
                "total": 总数,
                "percentages": {字段值: 百分比}
            }
        """
        counts = await self.count_by_field(field, filters)
        total = sum(counts.values())
        
        return {
            "distribution": counts,
            "total": total,
            "percentages": {
                k: round(v / total * 100, 2) if total > 0 else 0
                for k, v in counts.items()
            }
        }
    
    async def get_summary_stats(
        self,
        numeric_fields: Optional[List[str]] = None,
        date_field: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        获取汇总统计
        
        Args:
            numeric_fields: 需要统计的数值字段列表
            date_field: 日期字段（用于统计最近/最早）
            filters: 额外的筛选条件
        
        Returns:
            {
                "total": 总数,
                "sums": {字段: 总和},
                "averages": {字段: 平均值},
                "latest_date": 最新日期,
                "earliest_date": 最早日期
            }
        """
        query = select(self.model)
        
        # 应用筛选
        if filters:
            conditions = QueryBuilder._build_filter_conditions(self.model, filters)
            if conditions:
                query = query.where(and_(*conditions))
        
        # 统计总数
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        
        result = {
            "total": total
        }
        
        # 统计数值字段
        if numeric_fields:
            sums = {}
            averages = {}
            
            for field in numeric_fields:
                model_field = getattr(self.model, field, None)
                if model_field:
                    sum_query = select(func.sum(model_field))
                    avg_query = select(func.avg(model_field))
                    
                    if filters:
                        conditions = QueryBuilder._build_filter_conditions(self.model, filters)
                        if conditions:
                            sum_query = sum_query.where(and_(*conditions))
                            avg_query = avg_query.where(and_(*conditions))
                    
                    sum_result = await self.db.execute(sum_query)
                    avg_result = await self.db.execute(avg_query)
                    
                    sums[field] = float(sum_result.scalar() or 0)
                    averages[field] = float(avg_result.scalar() or 0)
            
            result["sums"] = sums
            result["averages"] = averages
        
        # 统计日期字段
        if date_field:
            model_date_field = getattr(self.model, date_field, None)
            if model_date_field:
                latest_query = select(func.max(model_date_field))
                earliest_query = select(func.min(model_date_field))
                
                if filters:
                    conditions = QueryBuilder._build_filter_conditions(self.model, filters)
                    if conditions:
                        latest_query = latest_query.where(and_(*conditions))
                        earliest_query = earliest_query.where(and_(*conditions))
                
                latest_result = await self.db.execute(latest_query)
                earliest_result = await self.db.execute(earliest_query)
                
                result["latest_date"] = latest_result.scalar()
                result["earliest_date"] = earliest_result.scalar()
        
        return result
