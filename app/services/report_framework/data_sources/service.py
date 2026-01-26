# -*- coding: utf-8 -*-
"""
服务方法调用数据源

调用现有服务方法获取数据
"""

import importlib
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.services.report_framework.data_sources.base import DataSource, DataSourceError
from app.services.report_framework.models import DataSourceConfig


class ServiceDataSource(DataSource):
    """
    服务方法调用数据源

    支持调用现有服务类的方法获取数据
    配置格式: "ServiceClass.method_name"
    """

    def __init__(self, db: Session, config: DataSourceConfig):
        """
        初始化服务数据源

        Args:
            db: 数据库会话
            config: 数据源配置
        """
        super().__init__(db, config)
        self.validate_config()
        self._service_class = None
        self._method_name = None
        self._parse_method()

    def validate_config(self) -> None:
        """
        验证配置

        Raises:
            DataSourceError: method 未配置或格式错误
        """
        if not self.config.method:
            raise DataSourceError("Method is required for service data source")

        if "." not in self.config.method:
            raise DataSourceError(
                f"Invalid method format: {self.config.method}. "
                "Expected 'ServiceClass.method_name'"
            )

    def _parse_method(self) -> None:
        """解析方法配置"""
        parts = self.config.method.rsplit(".", 1)
        self._service_class = parts[0]
        self._method_name = parts[1]

    def fetch(self, params: Dict[str, Any]) -> Any:
        """
        调用服务方法获取数据

        Args:
            params: 方法参数

        Returns:
            服务方法返回的数据

        Raises:
            DataSourceError: 服务调用失败
        """
        try:
            # 获取服务实例
            service_instance = self._get_service_instance()

            # 获取方法
            method = getattr(service_instance, self._method_name, None)
            if not method:
                raise DataSourceError(
                    f"Method '{self._method_name}' not found in service"
                )

            # 合并配置参数和运行时参数
            call_args = {**self.config.args, **params}

            # 调用方法
            result = method(**call_args)

            return result

        except DataSourceError:
            raise
        except Exception as e:
            raise DataSourceError(f"Service method call failed: {e}")

    def _get_service_instance(self) -> Any:
        """
        获取服务实例

        Returns:
            服务实例

        Raises:
            DataSourceError: 服务类未找到
        """
        # 尝试多个可能的模块路径
        possible_paths = [
            f"app.services.{self._to_snake_case(self._service_class)}",
            f"app.services.{self._service_class.lower()}",
            f"app.services.{self._service_class}",
        ]

        for module_path in possible_paths:
            try:
                module = importlib.import_module(module_path)
                service_class = getattr(module, self._service_class, None)
                if service_class:
                    # 尝试实例化服务
                    return self._instantiate_service(service_class)
            except (ImportError, ModuleNotFoundError):
                continue

        raise DataSourceError(f"Service class '{self._service_class}' not found")

    def _instantiate_service(self, service_class: type) -> Any:
        """
        实例化服务类

        Args:
            service_class: 服务类

        Returns:
            服务实例
        """
        try:
            # 尝试用 db 参数初始化
            return service_class(self.db)
        except TypeError:
            try:
                # 尝试无参数初始化
                return service_class()
            except TypeError:
                # 尝试用 db=db 关键字参数
                return service_class(db=self.db)

    @staticmethod
    def _to_snake_case(name: str) -> str:
        """
        驼峰转下划线

        Args:
            name: 驼峰命名

        Returns:
            下划线命名
        """
        import re
        # 处理连续大写字母
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
