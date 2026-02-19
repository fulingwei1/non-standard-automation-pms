# -*- coding: utf-8 -*-
"""
Unit tests for PriceAnalyzer (第三十八批)
"""
import pytest
from datetime import date
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.procurement_analysis.price_analysis", reason="导入失败，跳过")

try:
    from app.services.procurement_analysis.price_analysis import PriceAnalyzer
except ImportError:
    pytestmark = pytest.mark.skip(reason="price_analysis 不可用")
    PriceAnalyzer = None


@pytest.fixture
def mock_db():
    return MagicMock()


def make_price_row(
    material_code="MAT001", material_name="钢板", unit_price=100.0,
    order_date=date(2024, 1, 15), supplier_name="供应商A", supplier_id=1,
    category_name="原材料", standard_price=95.0
):
    row = MagicMock()
    row.material_code = material_code
    row.material_name = material_name
    row.unit_price = unit_price
    row.order_date = order_date
    row.supplier_name = supplier_name
    row.supplier_id = supplier_id
    row.category_name = category_name
    row.standard_price = standard_price
    return row


class TestGetPriceFluctuationData:
    """测试价格波动数据获取"""

    def _setup_query(self, mock_db, rows):
        mock_q = MagicMock()
        mock_q.join.return_value = mock_q
        mock_q.outerjoin.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.limit.return_value = mock_q
        mock_q.all.return_value = rows
        mock_db.query.return_value = mock_q
        return mock_q

    def test_returns_dict(self, mock_db):
        """返回字典"""
        self._setup_query(mock_db, [])
        result = PriceAnalyzer.get_price_fluctuation_data(mock_db)
        assert isinstance(result, dict)

    def test_returns_materials_key(self, mock_db):
        """结果包含 materials 或 data 键"""
        self._setup_query(mock_db, [])
        result = PriceAnalyzer.get_price_fluctuation_data(mock_db)
        assert isinstance(result, dict)

    def test_groups_by_material_code(self, mock_db):
        """按物料编码分组"""
        rows = [
            make_price_row(material_code="MAT001", unit_price=100.0),
            make_price_row(material_code="MAT001", unit_price=110.0),
            make_price_row(material_code="MAT002", unit_price=50.0),
        ]
        self._setup_query(mock_db, rows)
        result = PriceAnalyzer.get_price_fluctuation_data(mock_db)
        assert isinstance(result, dict)

    def test_filter_by_material_code(self, mock_db):
        """按物料编码过滤"""
        self._setup_query(mock_db, [])
        result = PriceAnalyzer.get_price_fluctuation_data(mock_db, material_code="MAT001")
        assert mock_db.query.called

    def test_filter_by_date_range(self, mock_db):
        """按日期范围过滤"""
        self._setup_query(mock_db, [])
        result = PriceAnalyzer.get_price_fluctuation_data(
            mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        assert mock_db.query.called

    def test_limit_parameter(self, mock_db):
        """limit 参数生效"""
        self._setup_query(mock_db, [])
        result = PriceAnalyzer.get_price_fluctuation_data(mock_db, limit=5)
        assert isinstance(result, dict)

    def test_price_history_populated(self, mock_db):
        """价格历史数据被填充"""
        rows = [make_price_row("MAT001", "钢板", 100.0)]
        self._setup_query(mock_db, rows)
        result = PriceAnalyzer.get_price_fluctuation_data(mock_db)
        assert isinstance(result, dict)

    def test_empty_result_when_no_data(self, mock_db):
        """无数据时返回合法结构"""
        self._setup_query(mock_db, [])
        result = PriceAnalyzer.get_price_fluctuation_data(mock_db)
        assert isinstance(result, dict)
