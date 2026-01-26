# -*- coding: utf-8 -*-
"""
SQL 查询数据源

执行参数化 SQL 查询
"""

import re
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.report_framework.data_sources.base import DataSource, DataSourceError
from app.services.report_framework.models import DataSourceConfig


class QueryDataSource(DataSource):
    """
    SQL 查询数据源

    执行配置中定义的 SQL 查询并返回结果
    """

    def __init__(self, db: Session, config: DataSourceConfig):
        """
        初始化查询数据源

        Args:
            db: 数据库会话
            config: 数据源配置
        """
        super().__init__(db, config)
        self.validate_config()

    def validate_config(self) -> None:
        """
        验证配置

        Raises:
            DataSourceError: SQL 未配置
        """
        if not self.config.sql:
            raise DataSourceError("SQL query is required for query data source")

        # 基本 SQL 安全检查（禁止危险操作）
        sql_upper = self.config.sql.upper()
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
        for keyword in dangerous_keywords:
            # 检查是否是独立的关键词（不是列名的一部分）
            if re.search(rf"\b{keyword}\b", sql_upper):
                raise DataSourceError(f"Dangerous SQL keyword detected: {keyword}")

    def fetch(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        执行 SQL 查询

        Args:
            params: 查询参数

        Returns:
            查询结果列表，每行为字典

        Raises:
            DataSourceError: 查询执行失败
        """
        try:
            # 执行参数化查询
            result = self.db.execute(text(self.config.sql), params)

            # 转换为字典列表
            rows = []
            columns = result.keys()
            for row in result.fetchall():
                row_dict = dict(zip(columns, row))
                rows.append(row_dict)

            return rows

        except Exception as e:
            raise DataSourceError(f"SQL query execution failed: {e}")

    def get_required_params(self) -> List[str]:
        """
        从 SQL 中提取需要的参数名

        Returns:
            参数名列表
        """
        # 匹配 :param_name 格式的参数
        pattern = r":(\w+)"
        matches = re.findall(pattern, self.config.sql)
        return list(set(matches))
