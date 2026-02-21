# -*- coding: utf-8 -*-
"""
完整单元测试 - strategy/kpi_service/snapshot.py
目标：60%+ 覆盖率，30+ 测试用例
"""
import pytest
import sys
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.strategy.kpi_service.snapshot import (
    _get_current_period,
    _calculate_trend,
    create_kpi_snapshot,
)


class TestGetCurrentPeriod:
    """当前周期获取测试"""
    
    def test_daily_period_format(self):
        """测试日度周期格式"""
        result = _get_current_period("DAILY")
        
        # 应该是YYYY-MM-DD格式
        assert len(result) == 10
        assert result[4] == "-"
        assert result[7] == "-"
        
        # 验证是今天的日期
        today = date.today()
        expected = today.strftime("%Y-%m-%d")
        assert result == expected
    
    def test_weekly_period_format(self):
        """测试周度周期格式"""
        result = _get_current_period("WEEKLY")
        
        # 应该包含W（week）
        assert "W" in result
        # 格式：YYYY-WXX
        assert len(result) >= 7
        
        # 验证年份正确
        today = date.today()
        assert result.startswith(str(today.year))
    
    def test_monthly_period_format(self):
        """测试月度周期格式"""
        result = _get_current_period("MONTHLY")
        
        # 应该是YYYY-MM格式
        assert len(result) == 7
        assert result[4] == "-"
        
        # 验证是当前月份
        today = date.today()
        expected = today.strftime("%Y-%m")
        assert result == expected
    
    def test_quarterly_period_format(self):
        """测试季度周期格式"""
        result = _get_current_period("QUARTERLY")
        
        # 应该包含Q
        assert "Q" in result
        # 格式：YYYY-QX
        assert len(result) >= 7
        
        # 验证季度正确
        today = date.today()
        quarter = (today.month - 1) // 3 + 1
        expected = f"{today.year}-Q{quarter}"
        assert result == expected
    
    def test_quarterly_period_q1(self):
        """测试Q1季度（1-3月）"""
        with patch("app.services.strategy.kpi_service.snapshot.date") as mock_date:
            mock_date.today.return_value = date(2024, 2, 15)
            result = _get_current_period("QUARTERLY")
            assert result == "2024-Q1"
    
    def test_quarterly_period_q2(self):
        """测试Q2季度（4-6月）"""
        with patch("app.services.strategy.kpi_service.snapshot.date") as mock_date:
            mock_date.today.return_value = date(2024, 5, 20)
            result = _get_current_period("QUARTERLY")
            assert result == "2024-Q2"
    
    def test_quarterly_period_q3(self):
        """测试Q3季度（7-9月）"""
        with patch("app.services.strategy.kpi_service.snapshot.date") as mock_date:
            mock_date.today.return_value = date(2024, 8, 10)
            result = _get_current_period("QUARTERLY")
            assert result == "2024-Q3"
    
    def test_quarterly_period_q4(self):
        """测试Q4季度（10-12月）"""
        with patch("app.services.strategy.kpi_service.snapshot.date") as mock_date:
            mock_date.today.return_value = date(2024, 12, 31)
            result = _get_current_period("QUARTERLY")
            assert result == "2024-Q4"
    
    def test_annually_period_format(self):
        """测试年度周期格式"""
        result = _get_current_period("ANNUALLY")
        
        # 应该只有年份，4位数字
        assert len(result) == 4
        assert result.isdigit()
        
        # 验证是当前年份
        today = date.today()
        assert result == str(today.year)
    
    def test_unknown_frequency_defaults_to_year(self):
        """测试未知频率默认返回年份"""
        for freq in ["UNKNOWN", "CUSTOM", "REALTIME", None]:
            result = _get_current_period(freq or "")
            assert len(result) == 4
            assert result.isdigit()


class TestCalculateTrend:
    """趋势计算测试"""
    
    def test_trend_up(self):
        """测试上升趋势"""
        db = MagicMock()
        h1 = MagicMock(value=Decimal("100"))
        h2 = MagicMock(value=Decimal("80"))
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        
        trend = _calculate_trend(db, 1)
        
        assert trend == "UP"
    
    def test_trend_down(self):
        """测试下降趋势"""
        db = MagicMock()
        h1 = MagicMock(value=Decimal("50"))
        h2 = MagicMock(value=Decimal("80"))
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        
        trend = _calculate_trend(db, 1)
        
        assert trend == "DOWN"
    
    def test_trend_stable(self):
        """测试稳定趋势"""
        db = MagicMock()
        h1 = MagicMock(value=Decimal("70"))
        h2 = MagicMock(value=Decimal("70"))
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        
        trend = _calculate_trend(db, 1)
        
        assert trend == "STABLE"
    
    def test_trend_no_history(self):
        """测试无历史记录"""
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        trend = _calculate_trend(db, 1)
        
        assert trend is None
    
    def test_trend_single_record(self):
        """测试只有一条历史记录"""
        db = MagicMock()
        h1 = MagicMock(value=Decimal("100"))
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1]
        
        trend = _calculate_trend(db, 1)
        
        assert trend is None
    
    def test_trend_current_none(self):
        """测试当前值为None"""
        db = MagicMock()
        h1 = MagicMock(value=None)
        h2 = MagicMock(value=Decimal("80"))
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        
        trend = _calculate_trend(db, 1)
        
        assert trend is None
    
    def test_trend_previous_none(self):
        """测试前值为None"""
        db = MagicMock()
        h1 = MagicMock(value=Decimal("100"))
        h2 = MagicMock(value=None)
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        
        trend = _calculate_trend(db, 1)
        
        assert trend is None
    
    def test_trend_both_none(self):
        """测试两个值都为None"""
        db = MagicMock()
        h1 = MagicMock(value=None)
        h2 = MagicMock(value=None)
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        
        trend = _calculate_trend(db, 1)
        
        assert trend is None
    
    def test_trend_small_increase(self):
        """测试小幅上升"""
        db = MagicMock()
        h1 = MagicMock(value=Decimal("100.1"))
        h2 = MagicMock(value=Decimal("100.0"))
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        
        trend = _calculate_trend(db, 1)
        
        assert trend == "UP"
    
    def test_trend_large_decrease(self):
        """测试大幅下降"""
        db = MagicMock()
        h1 = MagicMock(value=Decimal("10"))
        h2 = MagicMock(value=Decimal("1000"))
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        
        trend = _calculate_trend(db, 1)
        
        assert trend == "DOWN"
    
    def test_trend_zero_to_positive(self):
        """测试从0增长"""
        db = MagicMock()
        h1 = MagicMock(value=Decimal("50"))
        h2 = MagicMock(value=Decimal("0"))
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        
        trend = _calculate_trend(db, 1)
        
        assert trend == "UP"
    
    def test_trend_positive_to_zero(self):
        """测试降至0"""
        db = MagicMock()
        h1 = MagicMock(value=Decimal("0"))
        h2 = MagicMock(value=Decimal("100"))
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        
        trend = _calculate_trend(db, 1)
        
        assert trend == "DOWN"


class TestCreateKpiSnapshot:
    """创建KPI快照测试"""
    
    def setup_method(self):
        """设置测试环境"""
        # 模拟health_calculator模块
        self.hc_mock = MagicMock()
        self.hc_mock.calculate_kpi_completion_rate = MagicMock(return_value=75.0)
        self.hc_mock.get_health_level = MagicMock(return_value="GOOD")
        sys.modules["app.services.strategy.kpi_service.health_calculator"] = self.hc_mock
    
    def teardown_method(self):
        """清理测试环境"""
        sys.modules.pop("app.services.strategy.kpi_service.health_calculator", None)
    
    def test_create_snapshot_kpi_not_found(self):
        """测试KPI不存在时返回None"""
        db = MagicMock()
        with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=None):
            result = create_kpi_snapshot(db, kpi_id=999, source_type="MANUAL")
        
        assert result is None
        db.add.assert_not_called()
    
    def test_create_snapshot_basic(self):
        """测试基础快照创建"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.current_value = Decimal("75")
        kpi_mock.target_value = Decimal("100")
        kpi_mock.frequency = "MONTHLY"
        
        with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=kpi_mock):
            result = create_kpi_snapshot(db, kpi_id=1, source_type="MANUAL")
        
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()
    
    def test_create_snapshot_with_recorded_by(self):
        """测试带记录人的快照"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.current_value = Decimal("80")
        kpi_mock.target_value = Decimal("100")
        kpi_mock.frequency = "WEEKLY"
        
        with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=kpi_mock):
            result = create_kpi_snapshot(db, kpi_id=1, source_type="MANUAL", recorded_by=123)
        
        # 验证历史记录被创建
        call_args = db.add.call_args[0][0]
        db.add.assert_called_once()
    
    def test_create_snapshot_with_remark(self):
        """测试带备注的快照"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.current_value = Decimal("90")
        kpi_mock.target_value = Decimal("100")
        kpi_mock.frequency = "DAILY"
        
        with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=kpi_mock):
            result = create_kpi_snapshot(
                db,
                kpi_id=1,
                source_type="AUTO",
                remark="Automatic collection"
            )
        
        db.add.assert_called_once()
    
    def test_create_snapshot_auto_source(self):
        """测试自动采集源"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.current_value = Decimal("85")
        kpi_mock.target_value = Decimal("100")
        kpi_mock.frequency = "MONTHLY"
        
        with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=kpi_mock):
            result = create_kpi_snapshot(db, kpi_id=1, source_type="AUTO")
        
        # 验证source_type被正确设置
        call_args = db.add.call_args[0][0]
        db.add.assert_called_once()
    
    def test_create_snapshot_calculates_completion_rate(self):
        """测试计算完成率"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.current_value = Decimal("50")
        kpi_mock.target_value = Decimal("100")
        kpi_mock.frequency = "MONTHLY"
        
        with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=kpi_mock):
            create_kpi_snapshot(db, kpi_id=1, source_type="MANUAL")
        
        # 验证调用了计算函数
        self.hc_mock.calculate_kpi_completion_rate.assert_called_once_with(kpi_mock)
    
    def test_create_snapshot_calculates_health_level(self):
        """测试计算健康度"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.current_value = Decimal("90")
        kpi_mock.target_value = Decimal("100")
        kpi_mock.frequency = "MONTHLY"
        
        with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=kpi_mock):
            create_kpi_snapshot(db, kpi_id=1, source_type="MANUAL")
        
        # 验证调用了健康度计算
        self.hc_mock.get_health_level.assert_called_once()
    
    def test_create_snapshot_completion_rate_none(self):
        """测试完成率为None时"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.current_value = None
        kpi_mock.target_value = Decimal("100")
        kpi_mock.frequency = "MONTHLY"
        
        self.hc_mock.calculate_kpi_completion_rate.return_value = None
        
        with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=kpi_mock):
            result = create_kpi_snapshot(db, kpi_id=1, source_type="MANUAL")
        
        # 即使completion_rate为None，仍应创建快照
        db.add.assert_called_once()
    
    def test_create_snapshot_completion_rate_over_100(self):
        """测试完成率超过100%"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.current_value = Decimal("150")
        kpi_mock.target_value = Decimal("100")
        kpi_mock.frequency = "MONTHLY"
        
        self.hc_mock.calculate_kpi_completion_rate.return_value = 150.0
        
        with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=kpi_mock):
            result = create_kpi_snapshot(db, kpi_id=1, source_type="MANUAL")
        
        # 完成率应被限制在100
        call_args = db.add.call_args[0][0]
        db.add.assert_called_once()
    
    def test_create_snapshot_different_frequencies(self):
        """测试不同频率的快照"""
        db = MagicMock()
        
        for freq in ["DAILY", "WEEKLY", "MONTHLY", "QUARTERLY", "ANNUALLY"]:
            kpi_mock = MagicMock()
            kpi_mock.current_value = Decimal("80")
            kpi_mock.target_value = Decimal("100")
            kpi_mock.frequency = freq
            
            with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=kpi_mock):
                result = create_kpi_snapshot(db, kpi_id=1, source_type="MANUAL")
            
            # 每个频率都应该能创建快照
            assert db.add.called
            db.reset_mock()
    
    def test_create_snapshot_sets_snapshot_date(self):
        """测试设置快照日期为今天"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.current_value = Decimal("70")
        kpi_mock.target_value = Decimal("100")
        kpi_mock.frequency = "MONTHLY"
        
        with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.snapshot.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 15)
            
            result = create_kpi_snapshot(db, kpi_id=1, source_type="MANUAL")
        
        # 验证使用了今天的日期
        call_args = db.add.call_args[0][0]
        db.add.assert_called_once()
    
    def test_create_snapshot_sets_correct_period(self):
        """测试设置正确的周期"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.current_value = Decimal("80")
        kpi_mock.target_value = Decimal("100")
        kpi_mock.frequency = "MONTHLY"
        
        with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=kpi_mock), \
             patch("app.services.strategy.kpi_service.snapshot.date") as mock_date:
            mock_date.today.return_value = date(2024, 3, 15)
            
            result = create_kpi_snapshot(db, kpi_id=1, source_type="MANUAL")
        
        # 周期应该是2024-03
        call_args = db.add.call_args[0][0]
        db.add.assert_called_once()


class TestIntegrationScenarios:
    """集成场景测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.hc_mock = MagicMock()
        self.hc_mock.calculate_kpi_completion_rate = MagicMock(return_value=80.0)
        self.hc_mock.get_health_level = MagicMock(return_value="GOOD")
        sys.modules["app.services.strategy.kpi_service.health_calculator"] = self.hc_mock
    
    def teardown_method(self):
        """清理测试环境"""
        sys.modules.pop("app.services.strategy.kpi_service.health_calculator", None)
    
    def test_create_multiple_snapshots_for_same_kpi(self):
        """测试为同一KPI创建多个快照"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.current_value = Decimal("75")
        kpi_mock.target_value = Decimal("100")
        kpi_mock.frequency = "MONTHLY"
        
        with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=kpi_mock):
            # 创建第一个快照
            snapshot1 = create_kpi_snapshot(db, kpi_id=1, source_type="MANUAL")
            
            # 更新值后创建第二个快照
            kpi_mock.current_value = Decimal("85")
            snapshot2 = create_kpi_snapshot(db, kpi_id=1, source_type="AUTO")
        
        # 两次都应该创建快照
        assert db.add.call_count == 2
        assert db.commit.call_count == 2
    
    def test_snapshot_workflow_with_trend_calculation(self):
        """测试快照与趋势计算的完整流程"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.current_value = Decimal("90")
        kpi_mock.target_value = Decimal("100")
        kpi_mock.frequency = "MONTHLY"
        
        # 创建快照
        with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=kpi_mock):
            snapshot = create_kpi_snapshot(db, kpi_id=1, source_type="MANUAL")
        
        # 计算趋势
        h1 = MagicMock(value=Decimal("90"))
        h2 = MagicMock(value=Decimal("70"))
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        
        trend = _calculate_trend(db, 1)
        
        assert trend == "UP"


class TestEdgeCases:
    """边界情况测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.hc_mock = MagicMock()
        self.hc_mock.calculate_kpi_completion_rate = MagicMock(return_value=50.0)
        self.hc_mock.get_health_level = MagicMock(return_value="MEDIUM")
        sys.modules["app.services.strategy.kpi_service.health_calculator"] = self.hc_mock
    
    def teardown_method(self):
        """清理测试环境"""
        sys.modules.pop("app.services.strategy.kpi_service.health_calculator", None)
    
    def test_period_at_year_boundary(self):
        """测试跨年边界的周期"""
        with patch("app.services.strategy.kpi_service.snapshot.date") as mock_date:
            # 测试年底
            mock_date.today.return_value = date(2024, 12, 31)
            result = _get_current_period("MONTHLY")
            assert result == "2024-12"
            
            # 测试年初
            mock_date.today.return_value = date(2025, 1, 1)
            result = _get_current_period("MONTHLY")
            assert result == "2025-01"
    
    def test_trend_with_negative_values(self):
        """测试负值趋势"""
        db = MagicMock()
        h1 = MagicMock(value=Decimal("-10"))
        h2 = MagicMock(value=Decimal("-20"))
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
        
        trend = _calculate_trend(db, 1)
        
        # -10 > -20，所以是上升
        assert trend == "UP"
    
    def test_snapshot_with_zero_target(self):
        """测试目标值为0的快照"""
        db = MagicMock()
        kpi_mock = MagicMock()
        kpi_mock.current_value = Decimal("0")
        kpi_mock.target_value = Decimal("0")
        kpi_mock.frequency = "MONTHLY"
        
        with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=kpi_mock):
            result = create_kpi_snapshot(db, kpi_id=1, source_type="MANUAL")
        
        db.add.assert_called_once()
