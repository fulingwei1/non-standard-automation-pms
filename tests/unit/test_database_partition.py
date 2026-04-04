# -*- coding: utf-8 -*-
"""
数据库分区配置测试
"""

import pytest
from datetime import date, datetime


class TestPartitionType:
    """测试分区类型枚举"""

    def test_partition_type_values(self):
        """测试枚举值"""
        from app.core.database.partition import PartitionType

        assert PartitionType.RANGE.value == "RANGE"
        assert PartitionType.LIST.value == "LIST"
        assert PartitionType.HASH.value == "HASH"

    def test_partition_type_from_string(self):
        """测试从字符串创建"""
        from app.core.database.partition import PartitionType

        assert PartitionType("RANGE") == PartitionType.RANGE
        assert PartitionType("LIST") == PartitionType.LIST


class TestPartitionInterval:
    """测试分区间隔枚举"""

    def test_partition_interval_values(self):
        """测试枚举值"""
        from app.core.database.partition import PartitionInterval

        assert PartitionInterval.MONTHLY.value == "monthly"
        assert PartitionInterval.QUARTERLY.value == "quarterly"
        assert PartitionInterval.YEARLY.value == "yearly"


class TestPartitionConfig:
    """测试分区配置数据类"""

    def test_partition_config_creation(self):
        """测试配置创建"""
        from app.core.database.partition import PartitionConfig, PartitionType

        config = PartitionConfig(
            table_name="test_table",
            partition_type=PartitionType.RANGE,
            partition_column="created_at",
        )
        assert config.table_name == "test_table"
        assert config.partition_type == PartitionType.RANGE
        assert config.partition_column == "created_at"
        assert config.retention_months == 36  # 默认值

    def test_partition_config_custom_values(self):
        """测试自定义配置"""
        from app.core.database.partition import (
            PartitionConfig,
            PartitionInterval,
            PartitionType,
        )

        config = PartitionConfig(
            table_name="contracts",
            partition_type=PartitionType.RANGE,
            partition_column="created_at",
            interval=PartitionInterval.MONTHLY,
            retention_months=60,
            enabled=True,
        )
        assert config.interval == PartitionInterval.MONTHLY
        assert config.retention_months == 60
        assert config.enabled is True


class TestSalesPartitionConfigs:
    """测试销售模块分区配置"""

    def test_sales_partition_configs_exist(self):
        """测试配置列表存在"""
        from app.core.database.partition import SALES_PARTITION_CONFIGS

        assert len(SALES_PARTITION_CONFIGS) > 0

    def test_contracts_partition_config(self):
        """测试合同表分区配置"""
        from app.core.database.partition import (
            PartitionInterval,
            PartitionType,
            SALES_PARTITION_CONFIGS,
        )

        contracts = next(
            (c for c in SALES_PARTITION_CONFIGS if c.table_name == "contracts"), None
        )
        assert contracts is not None
        assert contracts.partition_type == PartitionType.RANGE
        assert contracts.partition_column == "created_at"
        assert contracts.interval == PartitionInterval.MONTHLY
        assert contracts.retention_months == 60

    def test_opportunities_partition_config(self):
        """测试商机表分区配置"""
        from app.core.database.partition import (
            PartitionInterval,
            PartitionType,
            SALES_PARTITION_CONFIGS,
        )

        opportunities = next(
            (c for c in SALES_PARTITION_CONFIGS if c.table_name == "opportunities"),
            None,
        )
        assert opportunities is not None
        assert opportunities.partition_type == PartitionType.RANGE

    def test_partition_config_enabled(self):
        """测试默认启用"""
        from app.core.database.partition import SALES_PARTITION_CONFIGS

        for config in SALES_PARTITION_CONFIGS:
            assert config.enabled is True


class TestGetPartitionNameDateRange:
    """测试获取分区名称的日期范围计算"""

    def test_monthly_partition_range(self):
        """测试月度分区范围"""
        from app.core.database.partition import (
            PartitionConfig,
            PartitionInterval,
            PartitionType,
        )

        config = PartitionConfig(
            table_name="test_table",
            partition_type=PartitionType.RANGE,
            partition_column="created_at",
            interval=PartitionInterval.MONTHLY,
        )
        assert config.interval == PartitionInterval.MONTHLY

    def test_quarterly_partition_range(self):
        """测试季度分区范围"""
        from app.core.database.partition import (
            PartitionConfig,
            PartitionInterval,
            PartitionType,
        )

        config = PartitionConfig(
            table_name="test_table",
            partition_type=PartitionType.RANGE,
            partition_column="created_at",
            interval=PartitionInterval.QUARTERLY,
        )
        assert config.interval == PartitionInterval.QUARTERLY

    def test_yearly_partition_range(self):
        """测试年度分区范围"""
        from app.core.database.partition import (
            PartitionConfig,
            PartitionInterval,
            PartitionType,
        )

        config = PartitionConfig(
            table_name="test_table",
            partition_type=PartitionType.RANGE,
            partition_column="created_at",
            interval=PartitionInterval.YEARLY,
        )
        assert config.interval == PartitionInterval.YEARLY