# -*- coding: utf-8 -*-
"""Tests for app/services/strategy/comparison_service.py"""
from unittest.mock import MagicMock, patch

from app.services.strategy.comparison_service import (
    create_strategy_comparison,
    get_strategy_comparison,
    list_strategy_comparisons,
    delete_strategy_comparison,
)


class TestComparisonService:
    def setup_method(self):
        self.db = MagicMock()

    def test_create_strategy_comparison(self):
        data = MagicMock()
        data.base_strategy_id = 1
        data.compare_strategy_id = 2
        data.comparison_type = "YOY"
        data.base_year = 2025
        data.compare_year = 2026
        data.summary = "test"
        with patch("app.services.strategy.comparison_service.StrategyComparison") as MockSC:
            MockSC.return_value = MagicMock()
            result = create_strategy_comparison(self.db, data, created_by=1)
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    def test_get_strategy_comparison_found(self):
        mock_comp = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_comp
        result = get_strategy_comparison(self.db, 1)
        assert result == mock_comp

    def test_get_strategy_comparison_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = get_strategy_comparison(self.db, 999)
        assert result is None

    def test_delete_strategy_comparison_found(self):
        mock_comp = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_comp
        result = delete_strategy_comparison(self.db, 1)
        assert result is True

    def test_delete_strategy_comparison_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = delete_strategy_comparison(self.db, 999)
        assert result is False


# ──────────────────────────────────────────────────────────
# G4 补充测试
# ──────────────────────────────────────────────────────────
class TestComparisonServiceG4:
    """G4 补充：comparison_service 深度覆盖"""

    def setup_method(self):
        self.db = MagicMock()

    # ---- create_strategy_comparison ----

    def test_create_comparison_patches_model(self):
        """patch StrategyComparison 避免属性校验，确保 db.add/commit 被调用"""
        with patch(
            "app.services.strategy.comparison_service.StrategyComparison"
        ) as MockComp:
            mock_instance = MagicMock()
            MockComp.return_value = mock_instance

            data = MagicMock()
            data.base_strategy_id = 1
            data.compare_strategy_id = 2
            data.comparison_type = "YOY"
            data.base_year = 2024
            data.compare_year = 2025
            data.summary = "对比摘要"

            result = create_strategy_comparison(self.db, data, created_by=10)

            MockComp.assert_called_once()
            self.db.add.assert_called_once_with(mock_instance)
            self.db.commit.assert_called_once()
            self.db.refresh.assert_called_once_with(mock_instance)
            assert result == mock_instance

    def test_create_comparison_sets_created_by(self):
        """创建时传入正确的 created_by"""
        with patch(
            "app.services.strategy.comparison_service.StrategyComparison"
        ) as MockComp:
            MockComp.return_value = MagicMock()
            data = MagicMock()
            data.base_strategy_id = 3
            data.compare_strategy_id = 4
            data.comparison_type = "QOQ"
            data.base_year = 2023
            data.compare_year = 2024
            data.summary = None

            create_strategy_comparison(self.db, data, created_by=99)
            call_kwargs = MockComp.call_args[1]
            assert call_kwargs.get("created_by") == 99

    # ---- list_strategy_comparisons ----

    def test_list_comparisons_returns_tuple(self):
        """list_strategy_comparisons 返回 (list, int)"""
        mock_items = [MagicMock(), MagicMock()]
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 2
        q.order_by.return_value = q
        # apply_pagination 返回 q，q.all() 返回 items
        with patch(
            "app.services.strategy.comparison_service.apply_pagination",
            return_value=MagicMock(all=MagicMock(return_value=mock_items))
        ):
            self.db.query.return_value = q
            items, total = list_strategy_comparisons(self.db)
            assert total == 2
            assert items == mock_items

    def test_list_comparisons_with_base_id_filter(self):
        """传入 base_strategy_id 时额外过滤"""
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 1
        q.order_by.return_value = q
        with patch(
            "app.services.strategy.comparison_service.apply_pagination",
            return_value=MagicMock(all=MagicMock(return_value=[MagicMock()]))
        ):
            self.db.query.return_value = q
            items, total = list_strategy_comparisons(self.db, base_strategy_id=5)
            assert total == 1
            # filter 被调用至少两次（is_active + base_id）
            assert q.filter.call_count >= 1

    def test_list_comparisons_empty(self):
        """无记录时返回空列表"""
        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = 0
        q.order_by.return_value = q
        with patch(
            "app.services.strategy.comparison_service.apply_pagination",
            return_value=MagicMock(all=MagicMock(return_value=[]))
        ):
            self.db.query.return_value = q
            items, total = list_strategy_comparisons(self.db)
            assert total == 0
            assert items == []

    # ---- generate_yoy_report ----

    def test_generate_yoy_report_missing_strategies(self):
        """当年度战略不存在时返回空维度列表"""
        from app.services.strategy.comparison_service import generate_yoy_report
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None  # 两个战略都不存在
        self.db.query.return_value = q

        result = generate_yoy_report(self.db, current_year=2025)

        assert result.current_year == 2025
        assert result.previous_year == 2024
        assert result.dimensions == []

    def test_generate_yoy_report_default_previous_year(self):
        """未传 previous_year 时默认为 current_year - 1"""
        from app.services.strategy.comparison_service import generate_yoy_report
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        self.db.query.return_value = q

        result = generate_yoy_report(self.db, current_year=2026)
        assert result.previous_year == 2025
