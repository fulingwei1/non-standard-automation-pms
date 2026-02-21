# -*- coding: utf-8 -*-
"""
完整单元测试 - strategy/kpi_collector/status.py
目标：60%+ 覆盖率，30+ 测试用例
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, Mock

from app.services.strategy.kpi_collector.status import get_collection_status


def make_kpi(
    data_source_type="AUTO",
    frequency="MONTHLY",
    current_value=None,
    last_collected_at=None
):
    """创建模拟KPI对象"""
    kpi = MagicMock()
    kpi.data_source_type = data_source_type
    kpi.frequency = frequency
    kpi.current_value = current_value
    kpi.last_collected_at = last_collected_at
    return kpi


class TestGetCollectionStatus:
    """KPI采集状态查询完整测试套件"""
    
    # ========== 基础功能测试 ==========
    
    def test_returns_all_required_keys(self):
        """测试返回所有必需的键"""
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        
        result = get_collection_status(db, strategy_id=1)
        
        required_keys = [
            "total_kpis",
            "auto_kpis",
            "manual_kpis",
            "collected_kpis",
            "pending_kpis",
            "frequency_stats",
            "last_collected_at"
        ]
        for key in required_keys:
            assert key in result
    
    def test_empty_kpis_returns_zeros(self):
        """测试无KPI时返回零值"""
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        
        result = get_collection_status(db, strategy_id=1)
        
        assert result["total_kpis"] == 0
        assert result["auto_kpis"] == 0
        assert result["manual_kpis"] == 0
        assert result["collected_kpis"] == 0
        assert result["pending_kpis"] == 0
        assert result["frequency_stats"] == {}
        assert result["last_collected_at"] is None
    
    def test_single_kpi_counts_correctly(self):
        """测试单个KPI统计正确"""
        db = MagicMock()
        kpis = [make_kpi("AUTO", "MONTHLY", 100.0)]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        
        assert result["total_kpis"] == 1
        assert result["auto_kpis"] == 1
        assert result["manual_kpis"] == 0
        assert result["collected_kpis"] == 1
        assert result["pending_kpis"] == 0
    
    # ========== 数据源类型统计测试 ==========
    
    def test_counts_auto_kpis(self):
        """测试自动采集KPI统计"""
        db = MagicMock()
        kpis = [
            make_kpi("AUTO", "MONTHLY"),
            make_kpi("AUTO", "WEEKLY"),
            make_kpi("AUTO", "DAILY"),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        assert result["auto_kpis"] == 3
        assert result["manual_kpis"] == 0
    
    def test_counts_manual_kpis(self):
        """测试手动采集KPI统计"""
        db = MagicMock()
        kpis = [
            make_kpi("MANUAL", "MONTHLY"),
            make_kpi("MANUAL", "QUARTERLY"),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        assert result["auto_kpis"] == 0
        assert result["manual_kpis"] == 2
    
    def test_mixed_data_source_types(self):
        """测试混合数据源类型"""
        db = MagicMock()
        kpis = [
            make_kpi("AUTO", "MONTHLY"),
            make_kpi("MANUAL", "WEEKLY"),
            make_kpi("AUTO", "DAILY"),
            make_kpi("MANUAL", "QUARTERLY"),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        assert result["total_kpis"] == 4
        assert result["auto_kpis"] == 2
        assert result["manual_kpis"] == 2
    
    def test_unknown_data_source_type(self):
        """测试未知数据源类型（边界情况）"""
        db = MagicMock()
        kpis = [
            make_kpi("UNKNOWN_TYPE", "MONTHLY"),
            make_kpi("AUTO", "WEEKLY"),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        # UNKNOWN_TYPE不计入auto或manual
        assert result["auto_kpis"] == 1
        assert result["manual_kpis"] == 0
        assert result["total_kpis"] == 2
    
    # ========== 采集状态统计测试 ==========
    
    def test_all_kpis_collected(self):
        """测试所有KPI都已采集"""
        db = MagicMock()
        kpis = [
            make_kpi(current_value=Decimal("100")),
            make_kpi(current_value=Decimal("50")),
            make_kpi(current_value=Decimal("0")),  # 0也算已采集
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        assert result["collected_kpis"] == 3
        assert result["pending_kpis"] == 0
    
    def test_all_kpis_pending(self):
        """测试所有KPI都待采集"""
        db = MagicMock()
        kpis = [
            make_kpi(current_value=None),
            make_kpi(current_value=None),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        assert result["collected_kpis"] == 0
        assert result["pending_kpis"] == 2
    
    def test_mixed_collection_status(self):
        """测试混合采集状态"""
        db = MagicMock()
        kpis = [
            make_kpi(current_value=100),
            make_kpi(current_value=None),
            make_kpi(current_value=50),
            make_kpi(current_value=None),
            make_kpi(current_value=None),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        assert result["collected_kpis"] == 2
        assert result["pending_kpis"] == 3
    
    def test_zero_value_counts_as_collected(self):
        """测试值为0也算已采集"""
        db = MagicMock()
        kpis = [make_kpi(current_value=0)]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        assert result["collected_kpis"] == 1
        assert result["pending_kpis"] == 0
    
    # ========== 频率统计测试 ==========
    
    def test_frequency_stats_single_frequency(self):
        """测试单一频率统计"""
        db = MagicMock()
        kpis = [
            make_kpi(frequency="MONTHLY", current_value=100),
            make_kpi(frequency="MONTHLY", current_value=None),
            make_kpi(frequency="MONTHLY", current_value=50),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        stats = result["frequency_stats"]
        
        assert "MONTHLY" in stats
        assert stats["MONTHLY"]["total"] == 3
        assert stats["MONTHLY"]["collected"] == 2
    
    def test_frequency_stats_multiple_frequencies(self):
        """测试多种频率统计"""
        db = MagicMock()
        kpis = [
            make_kpi(frequency="DAILY", current_value=100),
            make_kpi(frequency="DAILY", current_value=None),
            make_kpi(frequency="WEEKLY", current_value=50),
            make_kpi(frequency="MONTHLY", current_value=None),
            make_kpi(frequency="MONTHLY", current_value=80),
            make_kpi(frequency="QUARTERLY", current_value=90),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        stats = result["frequency_stats"]
        
        assert stats["DAILY"]["total"] == 2
        assert stats["DAILY"]["collected"] == 1
        assert stats["WEEKLY"]["total"] == 1
        assert stats["WEEKLY"]["collected"] == 1
        assert stats["MONTHLY"]["total"] == 2
        assert stats["MONTHLY"]["collected"] == 1
        assert stats["QUARTERLY"]["total"] == 1
        assert stats["QUARTERLY"]["collected"] == 1
    
    def test_frequency_stats_unknown_frequency(self):
        """测试未知频率（None）"""
        db = MagicMock()
        kpis = [
            make_kpi(frequency=None, current_value=100),
            make_kpi(frequency=None, current_value=None),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        stats = result["frequency_stats"]
        
        assert "UNKNOWN" in stats
        assert stats["UNKNOWN"]["total"] == 2
        assert stats["UNKNOWN"]["collected"] == 1
    
    def test_frequency_stats_all_pending(self):
        """测试某频率下全部待采集"""
        db = MagicMock()
        kpis = [
            make_kpi(frequency="WEEKLY", current_value=None),
            make_kpi(frequency="WEEKLY", current_value=None),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        stats = result["frequency_stats"]
        
        assert stats["WEEKLY"]["total"] == 2
        assert stats["WEEKLY"]["collected"] == 0
    
    # ========== 最后采集时间测试 ==========
    
    def test_last_collected_at_single_kpi(self):
        """测试单个KPI的最后采集时间"""
        db = MagicMock()
        t1 = datetime(2024, 3, 15, 10, 30)
        kpis = [make_kpi(last_collected_at=t1)]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        assert result["last_collected_at"] == t1
    
    def test_last_collected_at_multiple_kpis(self):
        """测试多个KPI取最晚时间"""
        db = MagicMock()
        t1 = datetime(2024, 1, 10, 8, 0)
        t2 = datetime(2024, 3, 15, 14, 30)
        t3 = datetime(2024, 2, 20, 12, 0)
        
        kpis = [
            make_kpi(last_collected_at=t1),
            make_kpi(last_collected_at=t2),  # 最晚
            make_kpi(last_collected_at=t3),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        assert result["last_collected_at"] == t2
    
    def test_last_collected_at_some_none(self):
        """测试部分KPI无采集时间"""
        db = MagicMock()
        t1 = datetime(2024, 2, 10)
        t2 = datetime(2024, 3, 5)
        
        kpis = [
            make_kpi(last_collected_at=None),
            make_kpi(last_collected_at=t1),
            make_kpi(last_collected_at=None),
            make_kpi(last_collected_at=t2),  # 最晚
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        assert result["last_collected_at"] == t2
    
    def test_last_collected_at_all_none(self):
        """测试所有KPI都无采集时间"""
        db = MagicMock()
        kpis = [
            make_kpi(last_collected_at=None),
            make_kpi(last_collected_at=None),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        assert result["last_collected_at"] is None
    
    def test_last_collected_at_same_time(self):
        """测试多个KPI同一时间采集"""
        db = MagicMock()
        t = datetime(2024, 3, 15, 10, 0)
        
        kpis = [
            make_kpi(last_collected_at=t),
            make_kpi(last_collected_at=t),
            make_kpi(last_collected_at=t),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        assert result["last_collected_at"] == t
    
    # ========== 数据库查询测试 ==========
    
    def test_database_query_called_correctly(self):
        """测试数据库查询调用正确"""
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        
        get_collection_status(db, strategy_id=123)
        
        # 验证query被调用
        db.query.assert_called_once()
        # 验证join被调用
        db.query.return_value.join.assert_called_once()
        # 验证filter被调用
        db.query.return_value.join.return_value.filter.assert_called_once()
    
    def test_different_strategy_ids(self):
        """测试不同战略ID"""
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        
        # 测试不同的strategy_id都能正常工作
        for strategy_id in [1, 100, 999]:
            result = get_collection_status(db, strategy_id)
            assert isinstance(result, dict)
    
    # ========== 综合场景测试 ==========
    
    def test_realistic_scenario_mixed_data(self):
        """测试真实场景：混合数据"""
        db = MagicMock()
        now = datetime.now()
        
        kpis = [
            # 自动采集，已采集
            make_kpi("AUTO", "DAILY", Decimal("95"), now - timedelta(hours=1)),
            make_kpi("AUTO", "WEEKLY", Decimal("88"), now - timedelta(days=2)),
            make_kpi("AUTO", "MONTHLY", None, None),  # 待采集
            
            # 手动采集
            make_kpi("MANUAL", "MONTHLY", Decimal("100"), now - timedelta(days=5)),
            make_kpi("MANUAL", "QUARTERLY", None, None),  # 待采集
            make_kpi("MANUAL", "WEEKLY", Decimal("75"), now - timedelta(days=1)),
        ]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        
        assert result["total_kpis"] == 6
        assert result["auto_kpis"] == 3
        assert result["manual_kpis"] == 3
        assert result["collected_kpis"] == 4
        assert result["pending_kpis"] == 2
        assert result["last_collected_at"] == now - timedelta(hours=1)
        
        # 验证频率统计
        assert result["frequency_stats"]["DAILY"]["total"] == 1
        assert result["frequency_stats"]["WEEKLY"]["total"] == 2
        assert result["frequency_stats"]["MONTHLY"]["total"] == 2
        assert result["frequency_stats"]["QUARTERLY"]["total"] == 1
    
    def test_large_dataset(self):
        """测试大数据集"""
        db = MagicMock()
        
        # 生成100个KPI
        kpis = []
        for i in range(100):
            freq = ["DAILY", "WEEKLY", "MONTHLY", "QUARTERLY"][i % 4]
            source = "AUTO" if i % 2 == 0 else "MANUAL"
            value = Decimal(str(i)) if i % 3 != 0 else None
            kpis.append(make_kpi(source, freq, value))
        
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        
        assert result["total_kpis"] == 100
        assert result["auto_kpis"] == 50
        assert result["manual_kpis"] == 50
        # 67个已采集 (100 - 33个None)
        assert result["collected_kpis"] == 67
        assert result["pending_kpis"] == 33
    
    def test_edge_case_single_auto_pending(self):
        """测试边界：单个自动待采集KPI"""
        db = MagicMock()
        kpis = [make_kpi("AUTO", "MONTHLY", None, None)]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
        
        result = get_collection_status(db, strategy_id=1)
        
        assert result["total_kpis"] == 1
        assert result["auto_kpis"] == 1
        assert result["manual_kpis"] == 0
        assert result["collected_kpis"] == 0
        assert result["pending_kpis"] == 1
        assert result["frequency_stats"]["MONTHLY"]["total"] == 1
        assert result["frequency_stats"]["MONTHLY"]["collected"] == 0
        assert result["last_collected_at"] is None
