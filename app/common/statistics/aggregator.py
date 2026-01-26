# -*- coding: utf-8 -*-
"""
统计聚合器
用于组合多个统计服务的结果
"""

from typing import Dict, List, Any, Optional
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.statistics.base import BaseStatisticsService


class StatisticsAggregator:
    """统计聚合器"""
    
    def __init__(self, db: AsyncSession):
        """
        Args:
            db: 数据库会话
        """
        self.db = db
        self._services: Dict[str, BaseStatisticsService] = {}
    
    def register_service(
        self,
        name: str,
        service: BaseStatisticsService
    ):
        """注册统计服务"""
        self._services[name] = service
    
    async def get_overview_stats(
        self,
        services: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        获取概览统计
        
        Args:
            services: 要统计的服务列表（如果为None，则统计所有）
        
        Returns:
            {
                "service_name": {
                    "total": 总数,
                    "by_status": {状态: 数量},
                    ...
                }
            }
        """
        services_to_query = services or list(self._services.keys())
        result = {}
        
        for service_name in services_to_query:
            if service_name not in self._services:
                continue
            
            service = self._services[service_name]
            
            # 获取总数
            total = await service.count_total()
            
            # 尝试获取状态分布（如果模型有status字段）
            by_status = {}
            try:
                by_status = await service.count_by_status()
            except (ValueError, AttributeError):
                pass
            
            result[service_name] = {
                "total": total,
                "by_status": by_status
            }
        
        return result
    
    async def get_trends(
        self,
        service_name: str,
        date_field: str,
        days: int = 30,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取趋势数据
        
        Args:
            service_name: 服务名称
            date_field: 日期字段
            days: 统计天数
            filters: 筛选条件
        
        Returns:
            趋势数据列表
        """
        if service_name not in self._services:
            raise ValueError(f"服务 {service_name} 未注册")
        
        service = self._services[service_name]
        return await service.get_trend(date_field, days=days, filters=filters)
    
    async def get_comparison(
        self,
        service_name: str,
        field: str,
        current_period_filters: Optional[Dict[str, Any]] = None,
        previous_period_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        获取同比/环比数据
        
        Args:
            service_name: 服务名称
            field: 统计字段
            current_period_filters: 当前周期筛选
            previous_period_filters: 上一周期筛选
        
        Returns:
            {
                "current": 当前值,
                "previous": 上一值,
                "change": 变化量,
                "change_percent": 变化百分比
            }
        """
        if service_name not in self._services:
            raise ValueError(f"服务 {service_name} 未注册")
        
        service = self._services[service_name]
        
        current = await service.count_total(filters=current_period_filters)
        previous = await service.count_total(filters=previous_period_filters)
        
        change = current - previous
        change_percent = (change / previous * 100) if previous > 0 else 0
        
        return {
            "current": current,
            "previous": previous,
            "change": change,
            "change_percent": round(change_percent, 2)
        }
