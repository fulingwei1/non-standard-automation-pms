# -*- coding: utf-8 -*-
"""
数据源基类

定义数据源的抽象接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.services.report_framework.models import DataSourceConfig


class DataSourceError(Exception):
    """数据源错误"""
    pass


class DataSource(ABC):
    """
    数据源抽象基类

    所有数据源类型必须实现此接口
    """

    def __init__(self, db: Session, config: DataSourceConfig):
        """
        初始化数据源

        Args:
            db: 数据库会话
            config: 数据源配置
        """
        self.db = db
        self.config = config

    @abstractmethod
    def fetch(self, params: Dict[str, Any]) -> Any:
        """
        获取数据

        Args:
            params: 参数字典

        Returns:
            数据结果（列表或字典）

        Raises:
            DataSourceError: 数据获取失败
        """
        pass

    def validate_config(self) -> None:
        """
        验证配置有效性

        Raises:
            DataSourceError: 配置无效
        """
        pass
