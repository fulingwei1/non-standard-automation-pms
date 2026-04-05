# -*- coding: utf-8 -*-
"""
数据库分区配置测试
"""
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch
from app.core.database.partition import (
    PartitionType,
    PartitionInterval,
    PartitionConfig,
    PartitionManager,
    SALES_PARTITION_CONFIGS,
)


class TestPartitionType:
    """测试 PartitionType 枚举"""

    def test_partition_types(self):
        """测试分区类型值"""
        assert PartitionType.RANGE.value == "RANGE"
        assert PartitionType.LIST.value == "LIST"
        assert PartitionType.HASH.value == "HASH"


class TestPartitionInterval:
    """测试 PartitionInterval 枚举"""

    def test_interval_values(self):
        """测试间隔值"""
        assert PartitionInterval.MONTHLY.value == "monthly"
        assert PartitionInterval.QUARTERLY.value == "quarterly"
        assert PartitionInterval.YEARLY.value == "yearly"


class TestPartitionConfig:
    """测试 PartitionConfig 数据类"""

    def test_basic_config(self):
        """测试基本配置"""
        config = PartitionConfig(
            table_name="test_table",
            partition_type=PartitionType.RANGE,
            partition_column="created_at",
        )
        assert config.table_name == "test_table"
        assert config.partition_type == PartitionType.RANGE
        assert config.partition_column == "created_at"

    def test_config_with_interval(self):
        """测试带间隔的配置"""
        config = PartitionConfig(
            table_name="test_table",
            partition_type=PartitionType.RANGE,
            partition_column="created_at",
            interval=PartitionInterval.MONTHLY,
        )
        assert config.interval == PartitionInterval.MONTHLY

    def test_config_with_retention(self):
        """测试带保留期的配置"""
        config = PartitionConfig(
            table_name="test_table",
            partition_type=PartitionType.RANGE,
            partition_column="created_at",
            retention_months=12,
        )
        assert config.retention_months == 12

    def test_config_defaults(self):
        """测试默认值"""
        config = PartitionConfig(
            table_name="test_table",
            partition_type=PartitionType.LIST,
            partition_column="status",
        )
        assert config.enabled is True
        assert config.retention_months == 36
        assert config.list_values is None


class TestSalesPartitionConfigs:
    """测试销售模块分区配置"""

    def test_contracts_config(self):
        """测试合同表配置"""
        config = next((c for c in SALES_PARTITION_CONFIGS if c.table_name == "contracts"), None)
        assert config is not None
        assert config.partition_type == PartitionType.RANGE
        assert config.partition_column == "created_at"
        assert config.interval == PartitionInterval.MONTHLY
        assert config.retention_months == 60

    def test_opportunities_config(self):
        """测试商机表配置"""
        config = next((c for c in SALES_PARTITION_CONFIGS if c.table_name == "opportunities"), None)
        assert config is not None
        assert config.retention_months == 36

    def test_leads_config(self):
        """测试线索表配置"""
        config = next((c for c in SALES_PARTITION_CONFIGS if c.table_name == "leads"), None)
        assert config is not None
        assert config.retention_months == 24

    def test_invoices_config(self):
        """测试发票表配置"""
        config = next((c for c in SALES_PARTITION_CONFIGS if c.table_name == "invoices"), None)
        assert config is not None
        assert config.retention_months == 84


class TestPartitionManager:
    """测试 PartitionManager 类"""

    def test_manager_initialization(self):
        """测试管理器初始化"""
        db = MagicMock()
        manager = PartitionManager(db)
        assert manager.db is db

    def test_get_partition_name_range(self):
        """测试范围分区名称生成"""
        db = MagicMock()
        manager = PartitionManager(db)
        
        partition_name = manager.get_partition_name(
            "contracts",
            2026,
            month=1
        )
        assert "contracts" in partition_name
        assert "2026" in partition_name
        assert "01" in partition_name

    def test_get_partition_name_quarter(self):
        """测试季度分区名称生成"""
        db = MagicMock()
        manager = PartitionManager(db)
        
        partition_name = manager.get_partition_name(
            "contracts",
            2026,
            quarter=1
        )
        assert "contracts" in partition_name
        assert "2026" in partition_name
        assert "q1" in partition_name

    def test_get_partition_name_yearly(self):
        """测试年度分区名称生成"""
        db = MagicMock()
        manager = PartitionManager(db)
        
        partition_name = manager.get_partition_name(
            "contracts",
            2026
        )
        assert "contracts" in partition_name
        assert "2026" in partition_name

    def test_get_date_range_monthly(self):
        """测试月度分区日期范围"""
        db = MagicMock()
        manager = PartitionManager(db)
        
        start, end = manager.get_date_range_for_partition(
            2026,
            month=3,
            interval=PartitionInterval.MONTHLY
        )
        assert start == date(2026, 3, 1)
        assert end == date(2026, 4, 1)

    def test_get_date_range_quarterly(self):
        """测试季度分区日期范围"""
        db = MagicMock()
        manager = PartitionManager(db)
        
        start, end = manager.get_date_range_for_partition(
            2026,
            quarter=2,
            interval=PartitionInterval.QUARTERLY
        )
        assert start == date(2026, 4, 1)
        assert end == date(2026, 7, 1)

    def test_get_date_range_yearly(self):
        """测试年度分区日期范围"""
        db = MagicMock()
        manager = PartitionManager(db)
        
        start, end = manager.get_date_range_for_partition(
            2026,
            interval=PartitionInterval.YEARLY
        )
        assert start == date(2026, 1, 1)
        assert end == date(2027, 1, 1)