# -*- coding: utf-8 -*-
"""
测试 kpi_collector/calculation - KPI数据采集计算

覆盖率目标: 60%+
测试用例数: 30+
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.services.strategy.kpi_collector.calculation import (
    calculate_formula,
    collect_kpi_value,
    auto_collect_kpi,
    batch_collect_kpis
)
from app.models.strategy import KPI, KPIDataSource


class TestCalculateFormula:
    """测试公式计算"""

    def test_simple_addition(self):
        """测试简单加法"""
        result = calculate_formula("a + b", {"a": 10, "b": 20})
        assert result == Decimal('30')

    def test_simple_subtraction(self):
        """测试简单减法"""
        result = calculate_formula("a - b", {"a": 100, "b": 30})
        assert result == Decimal('70')

    def test_multiplication(self):
        """测试乘法"""
        result = calculate_formula("a * b", {"a": 5, "b": 6})
        assert result == Decimal('30')

    def test_division(self):
        """测试除法"""
        result = calculate_formula("a / b", {"a": 100, "b": 4})
        assert result == Decimal('25')

    def test_percentage_calculation(self):
        """测试百分比计算"""
        result = calculate_formula("a / b * 100", {"a": 25, "b": 50})
        assert result == Decimal('50')

    def test_complex_formula(self):
        """测试复杂公式"""
        result = calculate_formula("(a + b) * c / d", {"a": 10, "b": 5, "c": 4, "d": 2})
        assert result == Decimal('30')

    def test_decimal_parameters(self):
        """测试Decimal参数"""
        result = calculate_formula(
            "a + b",
            {"a": Decimal('10.5'), "b": Decimal('20.3')}
        )
        assert float(result) == pytest.approx(30.8, rel=1e-5)

    def test_none_parameter(self):
        """测试None参数"""
        result = calculate_formula("a + b", {"a": 10, "b": None})
        # None参数会被过滤掉，导致计算失败
        assert result is None

    def test_empty_formula(self):
        """测试空公式"""
        result = calculate_formula("", {"a": 10})
        assert result is None

    def test_none_formula(self):
        """测试None公式"""
        result = calculate_formula(None, {"a": 10})
        assert result is None

    @patch('app.services.strategy.kpi_collector.calculation.HAS_SIMPLEEVAL', False)
    def test_without_simpleeval(self):
        """测试没有simpleeval库"""
        with pytest.raises(RuntimeError, match="simpleeval"):
            calculate_formula("a + b", {"a": 10, "b": 20})

    def test_invalid_formula(self):
        """测试无效公式"""
        result = calculate_formula("invalid syntax", {"a": 10})
        assert result is None

    def test_division_by_zero(self):
        """测试除零错误"""
        result = calculate_formula("a / b", {"a": 10, "b": 0})
        assert result is None


class TestCollectKPIValue:
    """测试采集KPI值"""

    def test_collect_auto_source(self):
        """测试自动采集"""
        db = Mock(spec=Session)
        
        kpi = KPI(id=1, is_active=True)
        data_source = KPIDataSource(
            id=1,
            kpi_id=1,
            source_type="AUTO",
            source_module="project",
            metric="count",
            is_primary=True,
            is_active=True
        )
        
        # Mock查询
        mock_kpi_query = MagicMock()
        mock_kpi_query.filter.return_value.first.return_value = kpi
        
        mock_ds_query = MagicMock()
        mock_ds_query.filter.return_value.first.return_value = data_source
        
        def query_side_effect(model):
            if model == KPI:
                return mock_kpi_query
            elif model == KPIDataSource:
                return mock_ds_query
        
        db.query.side_effect = query_side_effect
        db.commit = MagicMock()
        
        # Mock采集器
        with patch('app.services.strategy.kpi_collector.calculation.get_collector') as mock_get_collector:
            mock_collector = MagicMock(return_value=Decimal('100'))
            mock_get_collector.return_value = mock_collector
            
            result = collect_kpi_value(db, 1)
        
        assert result == Decimal('100')
        db.commit.assert_called()

    def test_collect_with_formula(self):
        """测试带公式采集"""
        db = Mock(spec=Session)
        
        kpi = KPI(id=1, is_active=True)
        data_source = KPIDataSource(
            id=1,
            kpi_id=1,
            source_type="AUTO",
            source_module="project",
            metric="count",
            formula="value * 2",
            formula_params='{"multiplier": 2}',
            is_primary=True,
            is_active=True
        )
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.filter.return_value.first.return_value = kpi
        
        mock_ds_query = MagicMock()
        mock_ds_query.filter.return_value.first.return_value = data_source
        
        def query_side_effect(model):
            if model == KPI:
                return mock_kpi_query
            elif model == KPIDataSource:
                return mock_ds_query
        
        db.query.side_effect = query_side_effect
        db.commit = MagicMock()
        
        with patch('app.services.strategy.kpi_collector.calculation.get_collector') as mock_get_collector:
            mock_collector = MagicMock(return_value=Decimal('50'))
            mock_get_collector.return_value = mock_collector
            
            result = collect_kpi_value(db, 1)
        
        assert result == Decimal('100')

    def test_collect_formula_type(self):
        """测试纯公式类型"""
        db = Mock(spec=Session)
        
        kpi = KPI(id=1, is_active=True)
        data_source = KPIDataSource(
            id=1,
            kpi_id=1,
            source_type="FORMULA",
            formula="a + b",
            formula_params='{"a": 10, "b": 20}',
            is_primary=True,
            is_active=True
        )
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.filter.return_value.first.return_value = kpi
        
        mock_ds_query = MagicMock()
        mock_ds_query.filter.return_value.first.return_value = data_source
        
        def query_side_effect(model):
            if model == KPI:
                return mock_kpi_query
            elif model == KPIDataSource:
                return mock_ds_query
        
        db.query.side_effect = query_side_effect
        db.commit = MagicMock()
        
        result = collect_kpi_value(db, 1)
        
        assert result == Decimal('30')

    def test_collect_manual_type(self):
        """测试手动类型"""
        db = Mock(spec=Session)
        
        kpi = KPI(id=1, current_value=Decimal('75'), is_active=True)
        data_source = KPIDataSource(
            id=1,
            kpi_id=1,
            source_type="MANUAL",
            is_primary=True,
            is_active=True
        )
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.filter.return_value.first.return_value = kpi
        
        mock_ds_query = MagicMock()
        mock_ds_query.filter.return_value.first.return_value = data_source
        
        def query_side_effect(model):
            if model == KPI:
                return mock_kpi_query
            elif model == KPIDataSource:
                return mock_ds_query
        
        db.query.side_effect = query_side_effect
        db.commit = MagicMock()
        
        result = collect_kpi_value(db, 1)
        
        assert result == Decimal('75')

    def test_collect_kpi_not_found(self):
        """测试KPI不存在"""
        db = Mock(spec=Session)
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.filter.return_value.first.return_value = None
        db.query.return_value = mock_kpi_query
        
        result = collect_kpi_value(db, 999)
        
        assert result is None

    def test_collect_no_data_source(self):
        """测试无数据源"""
        db = Mock(spec=Session)
        
        kpi = KPI(id=1, is_active=True)
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.filter.return_value.first.return_value = kpi
        
        mock_ds_query = MagicMock()
        mock_ds_query.filter.return_value.first.return_value = None
        
        def query_side_effect(model):
            if model == KPI:
                return mock_kpi_query
            elif model == KPIDataSource:
                return mock_ds_query
        
        db.query.side_effect = query_side_effect
        
        result = collect_kpi_value(db, 1)
        
        assert result is None

    def test_collect_collector_not_found(self):
        """测试采集器不存在"""
        db = Mock(spec=Session)
        
        kpi = KPI(id=1, is_active=True)
        data_source = KPIDataSource(
            id=1,
            kpi_id=1,
            source_type="AUTO",
            source_module="unknown_module",
            is_primary=True,
            is_active=True
        )
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.filter.return_value.first.return_value = kpi
        
        mock_ds_query = MagicMock()
        mock_ds_query.filter.return_value.first.return_value = data_source
        
        def query_side_effect(model):
            if model == KPI:
                return mock_kpi_query
            elif model == KPIDataSource:
                return mock_ds_query
        
        db.query.side_effect = query_side_effect
        db.commit = MagicMock()
        
        with patch('app.services.strategy.kpi_collector.calculation.get_collector', return_value=None):
            result = collect_kpi_value(db, 1)
        
        assert result is None


class TestAutoCollectKPI:
    """测试自动采集KPI"""

    def test_auto_collect_success(self):
        """测试成功自动采集"""
        db = Mock(spec=Session)
        
        kpi = KPI(id=1, is_active=True)
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = kpi
        db.query.return_value = mock_query
        db.commit = MagicMock()
        db.refresh = MagicMock()
        
        with patch('app.services.strategy.kpi_collector.calculation.collect_kpi_value', return_value=Decimal('85')):
            with patch('app.services.strategy.kpi_collector.calculation.create_kpi_snapshot') as mock_snapshot:
                result = auto_collect_kpi(db, 1)
        
        assert result.current_value == Decimal('85')
        assert result.last_collected_at is not None
        mock_snapshot.assert_called_once()

    def test_auto_collect_with_recorded_by(self):
        """测试带记录人的自动采集"""
        db = Mock(spec=Session)
        
        kpi = KPI(id=1, is_active=True)
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = kpi
        db.query.return_value = mock_query
        db.commit = MagicMock()
        db.refresh = MagicMock()
        
        with patch('app.services.strategy.kpi_collector.calculation.collect_kpi_value', return_value=Decimal('90')):
            with patch('app.services.strategy.kpi_collector.calculation.create_kpi_snapshot') as mock_snapshot:
                result = auto_collect_kpi(db, 1, recorded_by=100)
        
        # 验证快照创建时传递了recorded_by
        mock_snapshot.assert_called_once_with(db, 1, "AUTO", 100)

    def test_auto_collect_no_value(self):
        """测试采集不到值"""
        db = Mock(spec=Session)
        
        with patch('app.services.strategy.kpi_collector.calculation.collect_kpi_value', return_value=None):
            result = auto_collect_kpi(db, 1)
        
        assert result is None

    def test_auto_collect_kpi_not_found(self):
        """测试KPI不存在"""
        db = Mock(spec=Session)
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        db.query.return_value = mock_query
        
        with patch('app.services.strategy.kpi_collector.calculation.collect_kpi_value', return_value=Decimal('80')):
            result = auto_collect_kpi(db, 999)
        
        assert result is None


class TestBatchCollectKPIs:
    """测试批量采集KPIs"""

    def test_batch_collect_all(self):
        """测试批量采集所有"""
        db = Mock(spec=Session)
        
        kpis = [
            KPI(id=1, code="KPI001", name="KPI1", data_source_type="AUTO", is_active=True),
            KPI(id=2, code="KPI002", name="KPI2", data_source_type="AUTO", is_active=True)
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = kpis
        db.query.return_value = mock_query
        
        with patch('app.services.strategy.kpi_collector.calculation.auto_collect_kpi') as mock_collect:
            mock_collect.side_effect = [kpis[0], kpis[1]]
            
            result = batch_collect_kpis(db)
        
        assert result['total'] == 2
        assert result['success'] == 2
        assert result['failed'] == 0

    def test_batch_collect_with_strategy_filter(self):
        """测试按战略过滤"""
        db = Mock(spec=Session)
        
        kpis = [
            KPI(id=1, code="KPI001", data_source_type="AUTO", is_active=True)
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.all.return_value = kpis
        db.query.return_value = mock_query
        
        with patch('app.services.strategy.kpi_collector.calculation.auto_collect_kpi') as mock_collect:
            mock_collect.return_value = kpis[0]
            
            result = batch_collect_kpis(db, strategy_id=1)
        
        assert result['total'] == 1

    def test_batch_collect_with_frequency_filter(self):
        """测试按频率过滤"""
        db = Mock(spec=Session)
        
        kpis = [
            KPI(id=1, code="KPI001", data_source_type="AUTO", frequency="DAILY", is_active=True)
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = kpis
        db.query.return_value = mock_query
        
        with patch('app.services.strategy.kpi_collector.calculation.auto_collect_kpi') as mock_collect:
            mock_collect.return_value = kpis[0]
            
            result = batch_collect_kpis(db, frequency="DAILY")
        
        assert result['total'] == 1

    def test_batch_collect_partial_failure(self):
        """测试部分失败"""
        db = Mock(spec=Session)
        
        kpis = [
            KPI(id=1, code="KPI001", name="KPI1", data_source_type="AUTO", is_active=True),
            KPI(id=2, code="KPI002", name="KPI2", data_source_type="AUTO", is_active=True),
            KPI(id=3, code="KPI003", name="KPI3", data_source_type="AUTO", is_active=True)
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = kpis
        db.query.return_value = mock_query
        
        with patch('app.services.strategy.kpi_collector.calculation.auto_collect_kpi') as mock_collect:
            # 第2个失败
            mock_collect.side_effect = [kpis[0], None, kpis[2]]
            
            result = batch_collect_kpis(db)
        
        assert result['total'] == 3
        assert result['success'] == 2
        assert result['failed'] == 1
        assert len(result['failed_kpis']) == 1
        assert result['failed_kpis'][0]['id'] == 2

    def test_batch_collect_empty(self):
        """测试无KPI"""
        db = Mock(spec=Session)
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        db.query.return_value = mock_query
        
        result = batch_collect_kpis(db)
        
        assert result['total'] == 0
        assert result['success'] == 0
        assert result['failed'] == 0


class TestEdgeCases:
    """测试边界情况"""

    def test_formula_with_zero(self):
        """测试公式中的零值"""
        result = calculate_formula("a * 0", {"a": 100})
        assert result == Decimal('0')

    def test_formula_with_negative(self):
        """测试公式中的负数"""
        result = calculate_formula("a - b", {"a": 10, "b": 20})
        assert result == Decimal('-10')

    def test_collect_specific_data_source(self):
        """测试指定数据源"""
        db = Mock(spec=Session)
        
        kpi = KPI(id=1, is_active=True)
        data_source = KPIDataSource(
            id=2,
            kpi_id=1,
            source_type="AUTO",
            source_module="project",
            is_active=True
        )
        
        mock_kpi_query = MagicMock()
        mock_kpi_query.filter.return_value.first.return_value = kpi
        
        mock_ds_query = MagicMock()
        mock_ds_query.filter.return_value.first.return_value = data_source
        
        def query_side_effect(model):
            if model == KPI:
                return mock_kpi_query
            elif model == KPIDataSource:
                return mock_ds_query
        
        db.query.side_effect = query_side_effect
        db.commit = MagicMock()
        
        with patch('app.services.strategy.kpi_collector.calculation.get_collector') as mock_get_collector:
            mock_collector = MagicMock(return_value=Decimal('60'))
            mock_get_collector.return_value = mock_collector
            
            result = collect_kpi_value(db, 1, data_source_id=2)
        
        assert result == Decimal('60')

    def test_batch_collect_result_timestamp(self):
        """测试批量采集结果时间戳"""
        db = Mock(spec=Session)
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        db.query.return_value = mock_query
        
        result = batch_collect_kpis(db)
        
        assert 'collected_at' in result
        assert isinstance(result['collected_at'], datetime)
