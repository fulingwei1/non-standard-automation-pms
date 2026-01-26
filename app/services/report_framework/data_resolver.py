# -*- coding: utf-8 -*-
"""
数据源解析器

协调多个数据源，获取报告所需的所有数据
"""

from typing import Any, Dict, Type

from sqlalchemy.orm import Session

from app.services.report_framework.data_sources.base import DataSource, DataSourceError
from app.services.report_framework.data_sources.query import QueryDataSource
from app.services.report_framework.data_sources.service import ServiceDataSource
from app.services.report_framework.expressions import ExpressionParser
from app.services.report_framework.models import DataSourceConfig, DataSourceType


class DataResolver:
    """
    数据源解析器

    根据配置创建数据源实例并获取数据
    """

    # 数据源类型映射
    DATA_SOURCE_TYPES: Dict[DataSourceType, Type[DataSource]] = {
        DataSourceType.QUERY: QueryDataSource,
        DataSourceType.SERVICE: ServiceDataSource,
    }

    def __init__(self, db: Session):
        """
        初始化数据源解析器

        Args:
            db: 数据库会话
        """
        self.db = db
        self._expression_parser = ExpressionParser()

    def resolve_all(
        self,
        data_sources: Dict[str, DataSourceConfig],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        解析所有数据源

        Args:
            data_sources: 数据源配置字典
            params: 参数

        Returns:
            数据字典，键为数据源名称
        """
        context = {"params": params}

        for name, config in data_sources.items():
            try:
                # 处理配置中的表达式
                resolved_config = self._resolve_config_expressions(config, context)

                # 获取数据
                data = self.resolve_one(resolved_config, params)

                # 添加到上下文（供后续数据源使用）
                context[name] = data

            except DataSourceError as e:
                # 数据源错误，记录并继续
                context[name] = []
                print(f"Warning: Data source '{name}' failed: {e}")

        # 移除 params，只返回数据
        context.pop("params", None)
        return context

    def resolve_one(
        self,
        config: DataSourceConfig,
        params: Dict[str, Any],
    ) -> Any:
        """
        解析单个数据源

        Args:
            config: 数据源配置
            params: 参数

        Returns:
            数据源返回的数据

        Raises:
            DataSourceError: 数据源类型不支持或获取失败
        """
        # 获取数据源类型
        ds_type = config.type
        if isinstance(ds_type, str):
            ds_type = DataSourceType(ds_type)

        # 获取数据源类
        ds_class = self.DATA_SOURCE_TYPES.get(ds_type)
        if not ds_class:
            raise DataSourceError(f"Unsupported data source type: {ds_type}")

        # 创建数据源实例
        ds_instance = ds_class(self.db, config)

        # 合并配置参数和运行时参数
        merged_params = {**config.args, **params}

        # 获取数据
        return ds_instance.fetch(merged_params)

    def _resolve_config_expressions(
        self,
        config: DataSourceConfig,
        context: Dict[str, Any],
    ) -> DataSourceConfig:
        """
        解析配置中的表达式

        Args:
            config: 原始配置
            context: 当前上下文

        Returns:
            解析后的配置
        """
        # 复制配置
        config_dict = config.model_dump()

        # 解析 args 中的表达式
        if config_dict.get("args"):
            resolved_args = {}
            for key, value in config_dict["args"].items():
                if isinstance(value, str) and "{{" in value:
                    resolved_args[key] = self._expression_parser.evaluate(value, context)
                else:
                    resolved_args[key] = value
            config_dict["args"] = resolved_args

        return DataSourceConfig(**config_dict)

    def register_data_source(
        self,
        ds_type: DataSourceType,
        ds_class: Type[DataSource],
    ) -> None:
        """
        注册自定义数据源类型

        Args:
            ds_type: 数据源类型
            ds_class: 数据源类
        """
        self.DATA_SOURCE_TYPES[ds_type] = ds_class
