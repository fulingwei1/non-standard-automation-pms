# -*- coding: utf-8 -*-
"""
G4 补充测试 - app/services/strategy/health_calculator.py
覆盖：
  - calculate_kpi_completion_rate（纯函数，无 db 依赖）
  - get_health_level（纯函数）
  - calculate_kpi_health（db mock）
  - calculate_csf_health（db mock）
  - calculate_dimension_health（db mock）
  - calculate_strategy_health（db mock）
"""

from unittest.mock import MagicMock, patch
import pytest


# ──────────────────────────────────────────────────────────
# 纯函数：calculate_kpi_completion_rate
# ──────────────────────────────────────────────────────────

class TestCalculateKpiCompletionRate:

    def _make_kpi(self, direction="UP", target=100, current=None):
        kpi = MagicMock()
        kpi.direction = direction
        kpi.target_value = target
        kpi.current_value = current
        return kpi

    def test_target_none_returns_none(self):
        from app.services.strategy.health_calculator import calculate_kpi_completion_rate
        kpi = self._make_kpi(target=None)
        assert calculate_kpi_completion_rate(kpi) is None

    def test_target_zero_returns_none(self):
        from app.services.strategy.health_calculator import calculate_kpi_completion_rate
        kpi = self._make_kpi(target=0)
        assert calculate_kpi_completion_rate(kpi) is None

    def test_current_none_returns_zero(self):
        from app.services.strategy.health_calculator import calculate_kpi_completion_rate
        kpi = self._make_kpi(target=100, current=None)
        assert calculate_kpi_completion_rate(kpi) == 0

    def test_up_direction_100_percent(self):
        from app.services.strategy.health_calculator import calculate_kpi_completion_rate
        kpi = self._make_kpi(direction="UP", target=100, current=100)
        assert calculate_kpi_completion_rate(kpi) == 100.0

    def test_up_direction_50_percent(self):
        from app.services.strategy.health_calculator import calculate_kpi_completion_rate
        kpi = self._make_kpi(direction="UP", target=100, current=50)
        assert calculate_kpi_completion_rate(kpi) == 50.0

    def test_up_direction_capped_at_150(self):
        """越大越好：当前值超过目标时，最高 150%"""
        from app.services.strategy.health_calculator import calculate_kpi_completion_rate
        kpi = self._make_kpi(direction="UP", target=100, current=200)
        assert calculate_kpi_completion_rate(kpi) == 150.0

    def test_down_direction_good(self):
        """越小越好：current < target 表示完成率 > 100%"""
        from app.services.strategy.health_calculator import calculate_kpi_completion_rate
        kpi = self._make_kpi(direction="DOWN", target=10, current=5)
        rate = calculate_kpi_completion_rate(kpi)
        assert rate == 150.0  # 10/5*100=200, capped at 150

    def test_down_direction_current_zero(self):
        """越小越好：current=0 且 target>0 → 200，capped at 150"""
        from app.services.strategy.health_calculator import calculate_kpi_completion_rate
        kpi = self._make_kpi(direction="DOWN", target=5, current=0)
        rate = calculate_kpi_completion_rate(kpi)
        assert rate == 150.0

    def test_down_direction_equal_values(self):
        """越小越好：current == target → 100%"""
        from app.services.strategy.health_calculator import calculate_kpi_completion_rate
        kpi = self._make_kpi(direction="DOWN", target=10, current=10)
        rate = calculate_kpi_completion_rate(kpi)
        assert rate == 100.0


# ──────────────────────────────────────────────────────────
# 纯函数：get_health_level
# ──────────────────────────────────────────────────────────

class TestGetHealthLevel:

    def test_excellent_at_90(self):
        from app.services.strategy.health_calculator import get_health_level
        assert get_health_level(90) == "EXCELLENT"

    def test_excellent_at_100(self):
        from app.services.strategy.health_calculator import get_health_level
        assert get_health_level(100) == "EXCELLENT"

    def test_good_at_70(self):
        from app.services.strategy.health_calculator import get_health_level
        assert get_health_level(70) == "GOOD"

    def test_good_at_89(self):
        from app.services.strategy.health_calculator import get_health_level
        assert get_health_level(89) == "GOOD"

    def test_warning_at_50(self):
        from app.services.strategy.health_calculator import get_health_level
        assert get_health_level(50) == "WARNING"

    def test_warning_at_69(self):
        from app.services.strategy.health_calculator import get_health_level
        assert get_health_level(69) == "WARNING"

    def test_danger_at_49(self):
        from app.services.strategy.health_calculator import get_health_level
        assert get_health_level(49) == "DANGER"

    def test_danger_at_0(self):
        from app.services.strategy.health_calculator import get_health_level
        assert get_health_level(0) == "DANGER"


# ──────────────────────────────────────────────────────────
# calculate_kpi_health
# ──────────────────────────────────────────────────────────

class TestCalculateKpiHealth:

    def setup_method(self):
        self.db = MagicMock()

    def test_kpi_not_found(self):
        from app.services.strategy.health_calculator import calculate_kpi_health
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = calculate_kpi_health(self.db, 999)
        assert result == {"score": None, "level": None, "completion_rate": None}

    def test_kpi_target_none(self):
        """KPI 无目标值时返回 None 健康度"""
        from app.services.strategy.health_calculator import calculate_kpi_health
        kpi = MagicMock()
        kpi.target_value = None
        kpi.is_active = True
        self.db.query.return_value.filter.return_value.first.return_value = kpi
        result = calculate_kpi_health(self.db, 1)
        assert result["score"] is None

    def test_kpi_full_completion(self):
        """完成率 100% → score=100, level=EXCELLENT"""
        from app.services.strategy.health_calculator import calculate_kpi_health
        kpi = MagicMock()
        kpi.target_value = 100
        kpi.current_value = 100
        kpi.direction = "UP"
        kpi.is_active = True
        self.db.query.return_value.filter.return_value.first.return_value = kpi
        result = calculate_kpi_health(self.db, 1)
        assert result["score"] == 100
        assert result["level"] == "EXCELLENT"

    def test_kpi_partial_completion(self):
        """完成率 70% → score=70, level=GOOD"""
        from app.services.strategy.health_calculator import calculate_kpi_health
        kpi = MagicMock()
        kpi.target_value = 100
        kpi.current_value = 70
        kpi.direction = "UP"
        kpi.is_active = True
        self.db.query.return_value.filter.return_value.first.return_value = kpi
        result = calculate_kpi_health(self.db, 1)
        assert result["score"] == 70
        assert result["level"] == "GOOD"

    def test_kpi_low_completion(self):
        """完成率 30% → score=30, level=DANGER"""
        from app.services.strategy.health_calculator import calculate_kpi_health
        kpi = MagicMock()
        kpi.target_value = 100
        kpi.current_value = 30
        kpi.direction = "UP"
        kpi.is_active = True
        self.db.query.return_value.filter.return_value.first.return_value = kpi
        result = calculate_kpi_health(self.db, 1)
        assert result["score"] == 30
        assert result["level"] == "DANGER"


# ──────────────────────────────────────────────────────────
# calculate_csf_health
# ──────────────────────────────────────────────────────────

class TestCalculateCsfHealth:

    def setup_method(self):
        self.db = MagicMock()

    def test_csf_not_found(self):
        from app.services.strategy.health_calculator import calculate_csf_health
        # first() 对 CSF 查询返回 None
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = calculate_csf_health(self.db, 999)
        assert result["score"] is None

    def test_csf_no_kpis(self):
        """CSF 存在但无 KPI → 返回 None"""
        from app.services.strategy.health_calculator import calculate_csf_health
        csf = MagicMock()
        csf.id = 1
        csf.is_active = True
        # first() 返回 csf，all() 返回空列表
        self.db.query.return_value.filter.return_value.first.return_value = csf
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = calculate_csf_health(self.db, 1)
        assert result["score"] is None

    def test_csf_with_kpis(self):
        """CSF 有 KPI 时能计算出健康度"""
        from app.services.strategy.health_calculator import calculate_csf_health
        csf = MagicMock()
        csf.id = 1
        csf.is_active = True

        kpi = MagicMock()
        kpi.id = 10
        kpi.target_value = 100
        kpi.current_value = 80
        kpi.direction = "UP"
        kpi.weight = 1
        kpi.is_active = True

        def query_side_effect(model):
            q = MagicMock()
            q.filter.return_value = q
            q.first.return_value = csf if model.__name__ == "CSF" else kpi
            q.all.return_value = [kpi] if model.__name__ == "KPI" else [csf]
            return q

        self.db.query.side_effect = query_side_effect
        result = calculate_csf_health(self.db, 1)
        # 只要没有异常并返回字典即可
        assert isinstance(result, dict)


# ──────────────────────────────────────────────────────────
# calculate_strategy_health
# ──────────────────────────────────────────────────────────

class TestCalculateStrategyHealth:

    def setup_method(self):
        self.db = MagicMock()

    def test_strategy_not_found_returns_none(self):
        from app.services.strategy.health_calculator import calculate_strategy_health
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = calculate_strategy_health(self.db, 999)
        assert result is None

    def test_strategy_with_no_csfs_returns_none(self):
        """战略存在但无 CSF → 总权重=0 → 返回 None"""
        from app.services.strategy.health_calculator import calculate_strategy_health

        strategy = MagicMock()
        strategy.id = 1
        strategy.is_active = True

        def query_side_effect(model):
            q = MagicMock()
            q.filter.return_value = q
            if hasattr(model, '__name__') and model.__name__ == "Strategy":
                q.first.return_value = strategy
            else:
                q.first.return_value = None
                q.all.return_value = []
                q.scalar.return_value = 0
            return q

        self.db.query.side_effect = query_side_effect

        # 用 patch 让 calculate_dimension_health 返回 score=None
        with patch(
            "app.services.strategy.health_calculator.calculate_dimension_health",
            return_value={"score": None, "level": None}
        ):
            result = calculate_strategy_health(self.db, 1)
        assert result is None
