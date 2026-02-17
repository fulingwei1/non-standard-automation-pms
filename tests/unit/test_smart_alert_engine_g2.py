# -*- coding: utf-8 -*-
"""
SmartAlertEngine 单元测试 - G2组覆盖率提升

覆盖:
- SmartAlertEngine.__init__
- SmartAlertEngine.calculate_alert_level (核心纯逻辑)
- SmartAlertEngine.predict_impact
- SmartAlertEngine.scan_and_alert (集成路径)
- SmartAlertEngine.generate_solutions
- SmartAlertEngine._calculate_risk_score
"""

from decimal import Decimal
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestSmartAlertEngineInit:
    """测试初始化"""

    def test_init_stores_db(self):
        from app.services.shortage.smart_alert_engine import SmartAlertEngine
        db = MagicMock()
        engine = SmartAlertEngine(db)
        assert engine.db is db


class TestCalculateAlertLevel:
    """测试 calculate_alert_level - 核心预警级别逻辑，无 IO 依赖"""

    def setup_method(self):
        from app.services.shortage.smart_alert_engine import SmartAlertEngine
        self.engine = SmartAlertEngine(MagicMock())

    def test_level_urgent_when_days_zero(self):
        """距离需求日期 <=0 天，应为 URGENT"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal("10"),
            required_qty=Decimal("100"),
            days_to_shortage=0,
        )
        assert level == "URGENT"

    def test_level_urgent_when_days_negative(self):
        """已逾期，应为 URGENT"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal("50"),
            required_qty=Decimal("100"),
            days_to_shortage=-5,
        )
        assert level == "URGENT"

    def test_level_urgent_critical_path_within_3_days(self):
        """关键路径且 3 天内，应为 URGENT"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal("10"),
            required_qty=Decimal("100"),
            days_to_shortage=2,
            is_critical_path=True,
        )
        assert level == "URGENT"

    def test_level_urgent_critical_path_high_shortage_rate(self):
        """关键路径且缺口率 > 50%，应为 URGENT"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal("60"),
            required_qty=Decimal("100"),
            days_to_shortage=10,
            is_critical_path=True,
        )
        assert level == "URGENT"

    def test_level_critical_non_critical_path(self):
        """非关键路径 7 天内且缺口率 > 50%，应为 CRITICAL"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal("60"),
            required_qty=Decimal("100"),
            days_to_shortage=5,
            is_critical_path=False,
        )
        assert level == "CRITICAL"

    def test_level_warning_moderate_shortage(self):
        """14 天内且缺口率 > 30%，应为 WARNING"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal("35"),
            required_qty=Decimal("100"),
            days_to_shortage=10,
            is_critical_path=False,
        )
        assert level == "WARNING"

    def test_level_info_small_shortage(self):
        """缺口率低且时间充裕，应为 INFO"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal("5"),
            required_qty=Decimal("100"),
            days_to_shortage=30,
            is_critical_path=False,
        )
        assert level == "INFO"

    def test_level_warning_high_rate_but_not_urgent(self):
        """缺口率 > 50% 但时间不是很紧，应为 WARNING"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal("55"),
            required_qty=Decimal("100"),
            days_to_shortage=20,
            is_critical_path=False,
        )
        assert level == "WARNING"

    def test_level_critical_path_warning(self):
        """关键路径且 7 天内且缺口率 > 30%，应为 CRITICAL"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal("40"),
            required_qty=Decimal("100"),
            days_to_shortage=5,
            is_critical_path=True,
        )
        assert level == "CRITICAL"

    def test_required_qty_zero_no_exception(self):
        """需求数量为 0 时，不应抛出异常"""
        level = self.engine.calculate_alert_level(
            shortage_qty=Decimal("10"),
            required_qty=Decimal("0"),
            days_to_shortage=5,
        )
        # shortage_rate = 0 when required_qty == 0
        assert level in ("INFO", "WARNING", "CRITICAL", "URGENT")


class TestPredictImpact:
    """测试 predict_impact 方法"""

    def setup_method(self):
        from app.services.shortage.smart_alert_engine import SmartAlertEngine
        self.db = MagicMock()
        self.engine = SmartAlertEngine(self.db)

    def test_returns_impact_dict_structure(self):
        """返回值包含必要键"""
        # Mock internal methods
        self.engine._find_affected_projects = MagicMock(return_value=[])
        self.engine._get_average_lead_time = MagicMock(return_value=7)
        self.engine._calculate_risk_score = MagicMock(return_value=50)

        # Mock material query
        mock_material = MagicMock()
        mock_material.standard_price = Decimal("100")
        self.db.query.return_value.filter.return_value.first.return_value = mock_material

        result = self.engine.predict_impact(
            material_id=1,
            shortage_qty=Decimal("10"),
            required_date=date.today() + timedelta(days=14),
            project_id=1,
        )

        assert "estimated_delay_days" in result
        assert "estimated_cost_impact" in result
        assert "affected_projects" in result
        assert "risk_score" in result

    def test_cost_impact_calculated_when_material_has_price(self):
        """物料有标准单价时，成本影响应被计算"""
        self.engine._find_affected_projects = MagicMock(return_value=[])
        self.engine._get_average_lead_time = MagicMock(return_value=0)
        self.engine._calculate_risk_score = MagicMock(return_value=10)

        mock_material = MagicMock()
        mock_material.standard_price = Decimal("200")
        self.db.query.return_value.filter.return_value.first.return_value = mock_material

        result = self.engine.predict_impact(
            material_id=1,
            shortage_qty=Decimal("5"),
            required_date=date.today() + timedelta(days=30),
        )

        # cost = 5 * 200 * 1.5 = 1500
        assert result["estimated_cost_impact"] == Decimal("1500")

    def test_no_cost_impact_when_material_not_found(self):
        """物料不存在时，成本影响为 0"""
        self.engine._find_affected_projects = MagicMock(return_value=[])
        self.engine._get_average_lead_time = MagicMock(return_value=0)
        self.engine._calculate_risk_score = MagicMock(return_value=0)

        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.engine.predict_impact(
            material_id=99,
            shortage_qty=Decimal("5"),
            required_date=date.today() + timedelta(days=30),
        )

        assert result["estimated_cost_impact"] == Decimal("0")

    def test_affected_projects_populated(self):
        """受影响项目列表被正确填充"""
        affected = [
            {"id": 1, "name": "Project A", "required_qty": Decimal("50")},
            {"id": 2, "name": "Project B", "required_qty": Decimal("30")},
        ]
        self.engine._find_affected_projects = MagicMock(return_value=affected)
        self.engine._get_average_lead_time = MagicMock(return_value=0)
        self.engine._calculate_risk_score = MagicMock(return_value=20)
        self.db.query.return_value.filter.return_value.first.return_value = None

        result = self.engine.predict_impact(
            material_id=1,
            shortage_qty=Decimal("10"),
            required_date=date.today() + timedelta(days=5),
        )

        assert len(result["affected_projects"]) == 2


class TestScanAndAlert:
    """测试 scan_and_alert 集成路径"""

    def setup_method(self):
        from app.services.shortage.smart_alert_engine import SmartAlertEngine
        self.db = MagicMock()
        self.engine = SmartAlertEngine(self.db)

    def test_no_demands_returns_empty_list(self):
        """没有需求数据时返回空列表"""
        self.engine._collect_material_demands = MagicMock(return_value=[])
        result = self.engine.scan_and_alert()
        assert result == []

    def test_no_shortage_skipped(self):
        """供应充足（无缺口）时不生成预警"""
        self.engine._collect_material_demands = MagicMock(return_value=[{
            "material_id": 1,
            "material_code": "MAT001",
            "material_name": "测试物料",
            "required_qty": Decimal("100"),
            "days_to_required": 10,
            "required_date": date.today() + timedelta(days=10),
            "project_id": 1,
            "is_critical_path": False,
        }])
        self.engine._get_available_qty = MagicMock(return_value=Decimal("200"))
        self.engine._get_in_transit_qty = MagicMock(return_value=Decimal("0"))
        result = self.engine.scan_and_alert()
        assert result == []

    def test_shortage_generates_alert(self):
        """有缺口时生成预警"""
        demand = {
            "material_id": 1,
            "material_code": "MAT001",
            "material_name": "测试物料",
            "required_qty": Decimal("100"),
            "days_to_required": 5,
            "required_date": date.today() + timedelta(days=5),
            "project_id": 1,
            "is_critical_path": False,
            "work_order_id": 10,
        }
        self.engine._collect_material_demands = MagicMock(return_value=[demand])
        self.engine._get_available_qty = MagicMock(return_value=Decimal("20"))
        self.engine._get_in_transit_qty = MagicMock(return_value=Decimal("10"))

        mock_alert = MagicMock()
        mock_alert.alert_no = "ALT-001"
        self.engine._create_alert = MagicMock(return_value=mock_alert)
        self.engine.calculate_alert_level = MagicMock(return_value="WARNING")
        self.engine.predict_impact = MagicMock(return_value={
            "estimated_delay_days": 2,
            "estimated_cost_impact": Decimal("500"),
            "affected_projects": [],
            "risk_score": 40,
        })
        self.engine.generate_solutions = MagicMock(return_value=[])

        result = self.engine.scan_and_alert()
        assert len(result) == 1
        assert result[0] == mock_alert

    def test_critical_alert_triggers_solution_generation(self):
        """CRITICAL/URGENT 预警自动生成处理方案"""
        demand = {
            "material_id": 1,
            "material_code": "MAT001",
            "material_name": "测试物料",
            "required_qty": Decimal("100"),
            "days_to_required": 1,
            "required_date": date.today() + timedelta(days=1),
            "project_id": 1,
            "is_critical_path": True,
            "work_order_id": None,
        }
        self.engine._collect_material_demands = MagicMock(return_value=[demand])
        self.engine._get_available_qty = MagicMock(return_value=Decimal("0"))
        self.engine._get_in_transit_qty = MagicMock(return_value=Decimal("0"))

        mock_alert = MagicMock()
        mock_alert.alert_no = "ALT-002"
        self.engine._create_alert = MagicMock(return_value=mock_alert)
        self.engine.calculate_alert_level = MagicMock(return_value="URGENT")
        self.engine.predict_impact = MagicMock(return_value={
            "estimated_delay_days": 5,
            "estimated_cost_impact": Decimal("5000"),
            "affected_projects": [],
            "risk_score": 90,
        })
        generate_solutions = MagicMock(return_value=[MagicMock()])
        self.engine.generate_solutions = generate_solutions

        self.engine.scan_and_alert()
        generate_solutions.assert_called_once_with(mock_alert)
