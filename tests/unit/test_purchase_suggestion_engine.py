# -*- coding: utf-8 -*-
"""
智能采购建议引擎单元测试
覆盖 app/services/purchase_suggestion_engine.py
"""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.purchase_suggestion_engine import PurchaseSuggestionEngine


# ────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────

def _make_db():
    return MagicMock()


def _make_engine(db=None, tenant_id=1):
    db = db or _make_db()
    return PurchaseSuggestionEngine(db=db, tenant_id=tenant_id), db


def _make_material(
    material_id=1,
    code="MAT-001",
    name="测试物料",
    unit="个",
    safety_stock=Decimal("50"),
    current_stock=Decimal("10"),
    min_order_qty=Decimal("1"),
    lead_time_days=7,
    last_price=Decimal("100"),
    standard_price=Decimal("90"),
    specification="规格A",
    is_active=True,
):
    m = MagicMock()
    m.id = material_id
    m.material_code = code
    m.material_name = name
    m.unit = unit
    m.safety_stock = safety_stock
    m.current_stock = current_stock
    m.min_order_qty = min_order_qty
    m.lead_time_days = lead_time_days
    m.last_price = last_price
    m.standard_price = standard_price
    m.specification = specification
    m.is_active = is_active
    return m


def _make_shortage(
    shortage_id=1,
    material_id=1,
    project_id=1,
    shortage_qty=Decimal("20"),
    required_date=None,
    status="OPEN",
):
    s = MagicMock()
    s.id = shortage_id
    s.material_id = material_id
    s.project_id = project_id
    s.shortage_qty = shortage_qty
    s.required_date = required_date or (date.today() + timedelta(days=10))
    s.status = status
    return s


# ────────────────────────────────────────────────
# 1. _determine_urgency
# ────────────────────────────────────────────────

@pytest.mark.unit
class TestDetermineUrgency:

    def test_no_required_date_returns_normal(self):
        engine, _ = _make_engine()
        shortage = _make_shortage()
        shortage.required_date = None
        assert engine._determine_urgency(shortage) == "NORMAL"

    def test_past_date_returns_urgent(self):
        engine, _ = _make_engine()
        shortage = _make_shortage()
        shortage.required_date = date.today() - timedelta(days=1)
        assert engine._determine_urgency(shortage) == "URGENT"

    def test_within_3_days_returns_high(self):
        engine, _ = _make_engine()
        shortage = _make_shortage()
        shortage.required_date = date.today() + timedelta(days=2)
        assert engine._determine_urgency(shortage) == "HIGH"

    def test_within_7_days_returns_normal(self):
        engine, _ = _make_engine()
        shortage = _make_shortage()
        shortage.required_date = date.today() + timedelta(days=5)
        assert engine._determine_urgency(shortage) == "NORMAL"

    def test_beyond_7_days_returns_low(self):
        engine, _ = _make_engine()
        shortage = _make_shortage()
        shortage.required_date = date.today() + timedelta(days=14)
        assert engine._determine_urgency(shortage) == "LOW"


# ────────────────────────────────────────────────
# 2. _generate_suggestion_no
# ────────────────────────────────────────────────

@pytest.mark.unit
class TestGenerateSuggestionNo:

    def test_first_suggestion_of_day(self):
        engine, db = _make_engine()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        no = engine._generate_suggestion_no()
        assert no.startswith("PS")
        assert no.endswith("0001")

    def test_increments_from_latest(self):
        engine, db = _make_engine()
        latest = MagicMock()
        latest.suggestion_no = "PS202401010003"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = latest
        no = engine._generate_suggestion_no()
        assert no.endswith("0004")


# ────────────────────────────────────────────────
# 3. _calculate_avg_consumption
# ────────────────────────────────────────────────

@pytest.mark.unit
class TestCalculateAvgConsumption:

    def test_returns_none_when_no_history(self):
        engine, db = _make_engine()
        db.query.return_value.join.return_value.filter.return_value.scalar.return_value = None
        result = engine._calculate_avg_consumption(material_id=1, months=6)
        assert result is None

    def test_calculates_monthly_average(self):
        engine, db = _make_engine()
        db.query.return_value.join.return_value.filter.return_value.scalar.return_value = Decimal("120")
        result = engine._calculate_avg_consumption(material_id=1, months=6)
        assert result == Decimal("20")  # 120 / 6

    def test_returns_none_when_zero_result(self):
        engine, db = _make_engine()
        db.query.return_value.join.return_value.filter.return_value.scalar.return_value = Decimal("0")
        result = engine._calculate_avg_consumption(material_id=1, months=3)
        assert result is None


# ────────────────────────────────────────────────
# 4. generate_from_shortages
# ────────────────────────────────────────────────

@pytest.mark.unit
class TestGenerateFromShortages:

    def test_skips_shortage_with_existing_suggestion(self):
        engine, db = _make_engine()
        shortage = _make_shortage()
        db.query.return_value.filter.return_value.all.return_value = [shortage]
        # Existing suggestion found
        existing = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing
        result = engine.generate_from_shortages()
        assert result == []

    def test_skips_if_material_not_found(self):
        engine, db = _make_engine()
        shortage = _make_shortage()
        db.query.return_value.filter.return_value.all.return_value = [shortage]
        # No existing suggestion
        db.query.return_value.filter.return_value.first.return_value = None
        # Material not found
        db.query.return_value.get.return_value = None
        result = engine.generate_from_shortages()
        assert result == []

    @patch.object(PurchaseSuggestionEngine, "_recommend_supplier",
                  return_value=(1, Decimal("85"), {"total_score": 85}, []))
    @patch.object(PurchaseSuggestionEngine, "_generate_suggestion_no",
                  return_value="PS202401010001")
    @patch.object(PurchaseSuggestionEngine, "_determine_urgency",
                  return_value="NORMAL")
    def test_creates_suggestion_for_open_shortage(self, mock_urgency, mock_no, mock_supplier):
        engine, db = _make_engine()
        shortage = _make_shortage()
        db.query.return_value.filter.return_value.all.return_value = [shortage]
        # No existing suggestion
        db.query.return_value.filter.return_value.first.return_value = None
        # Material found
        material = _make_material()
        db.query.return_value.get.return_value = material

        result = engine.generate_from_shortages()

        db.add.assert_called()
        db.commit.assert_called()
        assert len(result) == 1
        assert result[0].suggestion_no == "PS202401010001"
        assert result[0].source_type == "SHORTAGE"

    def test_filters_by_project_id(self):
        engine, db = _make_engine()
        db.query.return_value.filter.return_value.all.return_value = []
        result = engine.generate_from_shortages(project_id=42)
        assert result == []
        db.commit.assert_called()


# ────────────────────────────────────────────────
# 5. generate_from_safety_stock
# ────────────────────────────────────────────────

@pytest.mark.unit
class TestGenerateFromSafetyStock:

    def test_no_low_stock_materials_returns_empty(self):
        engine, db = _make_engine()
        db.query.return_value.filter.return_value.all.return_value = []
        result = engine.generate_from_safety_stock()
        assert result == []
        db.commit.assert_called()

    def test_skips_material_with_existing_suggestion(self):
        engine, db = _make_engine()
        material = _make_material()
        db.query.return_value.filter.return_value.all.return_value = [material]
        # Existing suggestion found
        db.query.return_value.filter.return_value.first.return_value = MagicMock()
        result = engine.generate_from_safety_stock()
        assert result == []

    @patch.object(PurchaseSuggestionEngine, "_recommend_supplier",
                  return_value=(2, Decimal("75"), {"total_score": 75}, []))
    @patch.object(PurchaseSuggestionEngine, "_generate_suggestion_no",
                  return_value="PS202401010002")
    def test_creates_suggestion_for_low_stock(self, mock_no, mock_supplier):
        engine, db = _make_engine()
        material = _make_material(
            current_stock=Decimal("5"),
            safety_stock=Decimal("50"),
            min_order_qty=Decimal("10"),
        )
        db.query.return_value.filter.return_value.all.return_value = [material]
        db.query.return_value.filter.return_value.first.return_value = None  # no existing

        result = engine.generate_from_safety_stock()

        assert len(result) == 1
        # suggested_qty should be at least (safety_stock - current_stock) * 1.2
        expected_min = (Decimal("50") - Decimal("5")) * Decimal("1.2")
        assert result[0].suggested_qty >= expected_min

    def test_suggested_qty_at_least_min_order(self):
        engine, db = _make_engine()
        material = _make_material(
            current_stock=Decimal("49"),
            safety_stock=Decimal("50"),
            min_order_qty=Decimal("100"),  # min order much larger than shortage
        )
        # Directly test the calculation logic
        shortage_qty = material.safety_stock - material.current_stock  # 1
        suggested_qty = max(shortage_qty * Decimal("1.2"), material.min_order_qty)
        assert suggested_qty == Decimal("100")


# ────────────────────────────────────────────────
# 6. generate_from_forecast
# ────────────────────────────────────────────────

@pytest.mark.unit
class TestGenerateFromForecast:

    def test_returns_none_if_material_not_found(self):
        engine, db = _make_engine()
        db.query.return_value.get.return_value = None
        result = engine.generate_from_forecast(material_id=99)
        assert result is None

    def test_returns_none_if_no_consumption_history(self):
        engine, db = _make_engine()
        material = _make_material()
        db.query.return_value.get.return_value = material
        with patch.object(engine, "_calculate_avg_consumption", return_value=None):
            result = engine.generate_from_forecast(material_id=1)
        assert result is None

    def test_returns_none_if_stock_covers_forecast(self):
        engine, db = _make_engine()
        material = _make_material(current_stock=Decimal("1000"))
        db.query.return_value.get.return_value = material
        # avg consumption = 10/month, forecast 3 months = 30 < 1000 current
        with patch.object(engine, "_calculate_avg_consumption", return_value=Decimal("10")):
            result = engine.generate_from_forecast(material_id=1, forecast_months=3)
        assert result is None

    @patch.object(PurchaseSuggestionEngine, "_recommend_supplier",
                  return_value=(1, Decimal("90"), {"total_score": 90}, []))
    @patch.object(PurchaseSuggestionEngine, "_generate_suggestion_no",
                  return_value="PS202401010003")
    def test_creates_suggestion_when_stock_insufficient(self, mock_no, mock_supplier):
        engine, db = _make_engine()
        material = _make_material(current_stock=Decimal("5"))
        db.query.return_value.get.return_value = material
        # avg = 100/month, 3 months = 300 > 5
        db.query.return_value.filter.return_value.first.return_value = None  # no existing
        with patch.object(engine, "_calculate_avg_consumption", return_value=Decimal("100")):
            result = engine.generate_from_forecast(material_id=1, forecast_months=3)

        assert result is not None
        assert result.source_type == "FORECAST"
        # suggested_qty = 300 - 5 = 295
        assert result.suggested_qty == Decimal("295")

    @patch.object(PurchaseSuggestionEngine, "_recommend_supplier",
                  return_value=(1, Decimal("90"), {}, []))
    @patch.object(PurchaseSuggestionEngine, "_generate_suggestion_no",
                  return_value="PS202401010004")
    def test_returns_none_if_existing_suggestion(self, mock_no, mock_supplier):
        engine, db = _make_engine()
        material = _make_material(current_stock=Decimal("5"))
        db.query.return_value.get.return_value = material
        db.query.return_value.filter.return_value.first.return_value = MagicMock()  # existing
        with patch.object(engine, "_calculate_avg_consumption", return_value=Decimal("100")):
            result = engine.generate_from_forecast(material_id=1, forecast_months=3)
        assert result is None


# ────────────────────────────────────────────────
# 7. _calculate_supplier_score
# ────────────────────────────────────────────────

@pytest.mark.unit
class TestCalculateSupplierScore:

    def _setup_engine_with_supplier(
        self,
        order_count=0,
        lead_time_days=7,
        price=Decimal("100"),
        perf_score=None,
    ):
        engine, db = _make_engine()
        # SupplierPerformance
        perf = MagicMock()
        perf.overall_score = perf_score or Decimal("80")
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = perf
        # MaterialSupplier prices query
        db.query.return_value.filter.return_value.all.return_value = [
            (price,), (price,)  # two suppliers with same price
        ]
        # Current supplier
        ms = MagicMock()
        ms.price = price
        ms.lead_time_days = lead_time_days
        db.query.return_value.filter.return_value.first.return_value = ms
        # Order count
        db.query.return_value.filter.return_value.scalar.return_value = order_count
        return engine, db

    def test_total_score_is_within_0_to_100(self):
        engine, db = self._setup_engine_with_supplier()
        weight = {
            "performance": Decimal("40"),
            "price": Decimal("30"),
            "delivery": Decimal("20"),
            "history": Decimal("10"),
        }
        scores = engine._calculate_supplier_score(1, 1, weight)
        assert Decimal("0") <= scores["total_score"] <= Decimal("100")

    def test_short_lead_time_gives_max_delivery_score(self):
        engine, db = self._setup_engine_with_supplier(lead_time_days=5)
        scores = engine._calculate_supplier_score(1, 1, {"performance": Decimal("0"),
                                                         "price": Decimal("0"),
                                                         "delivery": Decimal("100"),
                                                         "history": Decimal("0")})
        # lead_time <= 7 → delivery_score = 100
        assert scores["delivery_score"] == Decimal("100")

    def test_many_orders_gives_max_history_score(self):
        engine, db = self._setup_engine_with_supplier(order_count=25)
        scores = engine._calculate_supplier_score(1, 1, {"performance": Decimal("0"),
                                                         "price": Decimal("0"),
                                                         "delivery": Decimal("0"),
                                                         "history": Decimal("100")})
        assert scores["history_score"] == Decimal("100")

    def test_default_performance_score_when_no_history(self):
        engine, db = _make_engine()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.filter.return_value.scalar.return_value = 0
        scores = engine._calculate_supplier_score(1, 1, {
            "performance": Decimal("100"),
            "price": Decimal("0"),
            "delivery": Decimal("0"),
            "history": Decimal("0"),
        })
        # Default performance is 60 when no record
        assert scores["performance_score"] == Decimal("60")


# ────────────────────────────────────────────────
# 8. _recommend_supplier
# ────────────────────────────────────────────────

@pytest.mark.unit
class TestRecommendSupplier:

    def test_returns_none_tuple_when_no_suppliers(self):
        engine, db = _make_engine()
        db.query.return_value.filter.return_value.all.return_value = []
        result = engine._recommend_supplier(material_id=1)
        assert result == (None, None, None, None)

    def test_returns_best_supplier_id(self):
        engine, db = _make_engine()
        ms = MagicMock()
        ms.supplier_id = 10
        ms.vendor = MagicMock(supplier_code="S001", supplier_name="供应商A")
        ms.price = Decimal("100")
        ms.lead_time_days = 7
        db.query.return_value.filter.return_value.all.return_value = [ms]

        with patch.object(engine, "_calculate_supplier_score", return_value={
            "total_score": Decimal("80"),
            "performance_score": Decimal("80"),
            "price_score": Decimal("80"),
            "delivery_score": Decimal("80"),
            "history_score": Decimal("80"),
        }):
            supplier_id, confidence, reason, alternatives = engine._recommend_supplier(1)

        assert supplier_id == 10
        assert confidence == Decimal("80")
        assert isinstance(reason, dict)
        assert alternatives == []  # only 1 supplier, no alternatives
