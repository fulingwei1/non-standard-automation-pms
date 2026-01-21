# -*- coding: utf-8 -*-
"""
数据源模块

支持的数据源类型：
- QueryDataSource: SQL 查询
- ServiceDataSource: 服务方法调用
- AggregateDataSource: 聚合函数
"""

from app.services.report_framework.data_sources.base import DataSource, DataSourceError
from app.services.report_framework.data_sources.query import QueryDataSource
from app.services.report_framework.data_sources.service import ServiceDataSource

__all__ = [
    "DataSource",
    "DataSourceError",
    "QueryDataSource",
    "ServiceDataSource",
]
