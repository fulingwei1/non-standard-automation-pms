# -*- coding: utf-8 -*-
"""
AssemblyKitService 综合单元测试

测试覆盖:
- validate_analysis_inputs: 验证齐套分析输入参数
- initialize_stage_results: 初始化阶段统计结果
- analyze_bom_item: 分析单个BOM物料项
- get_expected_arrival_date: 获取预计到货日期
- calculate_stage_kit_rates: 计算各阶段齐套率
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestValidateAnalysisInputs:
    """测试 validate_analysis_inputs 函数"""

    def test_raises_exception_when_project_not_found(self):
        """测试项目不存在时抛出异常"""
        from app.services.assembly_kit_service import validate_analysis_inputs

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(Exception) as exc_info:
            validate_analysis_inputs(mock_db, project_id=999, bom_id=1)

        assert "项目不存在" in str(exc_info.value.detail)

    def test_raises_exception_when_bom_not_found(self):
        """测试BOM不存在时抛出异常"""
        from app.services.assembly_kit_service import validate_analysis_inputs

        mock_db = MagicMock()
        mock_project = MagicMock()

        # 第一次查询返回项目，第二次返回None（BOM不存在）
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_project,
            None,
        ]

        with pytest.raises(Exception) as exc_info:
            validate_analysis_inputs(mock_db, project_id=1, bom_id=999)

        assert "BOM不存在" in str(exc_info.value.detail)

    def test_raises_exception_when_machine_not_found(self):
        """测试机台不存在时抛出异常"""
        from app.services.assembly_kit_service import validate_analysis_inputs

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_bom = MagicMock()

        # 按顺序返回项目、BOM、机台(None)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_project,
            mock_bom,
            None,
        ]

        with pytest.raises(Exception) as exc_info:
            validate_analysis_inputs(
                mock_db, project_id=1, bom_id=1, machine_id=999
            )

        assert "机台不存在" in str(exc_info.value.detail)

    def test_returns_project_bom_machine_when_all_exist(self):
        """测试所有参数有效时返回正确对象"""
        from app.services.assembly_kit_service import validate_analysis_inputs

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_bom = MagicMock()
        mock_machine = MagicMock()

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_project,
            mock_bom,
            mock_machine,
        ]

        result = validate_analysis_inputs(
            mock_db, project_id=1, bom_id=1, machine_id=1
        )

        assert result == (mock_project, mock_bom, mock_machine)

    def test_returns_none_machine_when_machine_id_not_provided(self):
        """测试不提供机台ID时返回None"""
        from app.services.assembly_kit_service import validate_analysis_inputs

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_bom = MagicMock()

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_project,
            mock_bom,
        ]

        project, bom, machine = validate_analysis_inputs(
            mock_db, project_id=1, bom_id=1
        )

        assert project == mock_project
        assert bom == mock_bom
        assert machine is None


class TestInitializeStageResults:
    """测试 initialize_stage_results 函数"""

    def test_returns_empty_dict_when_no_stages(self):
        """测试无阶段时返回空字典"""
        from app.services.assembly_kit_service import initialize_stage_results

        result = initialize_stage_results([])

        assert result == {}

    def test_initializes_stage_results_correctly(self):
        """测试正确初始化阶段统计结果"""
        from app.services.assembly_kit_service import initialize_stage_results

        mock_stage1 = MagicMock()
        mock_stage1.stage_code = "MECH"

        mock_stage2 = MagicMock()
        mock_stage2.stage_code = "ELEC"

        stages = [mock_stage1, mock_stage2]

        result = initialize_stage_results(stages)

        assert "MECH" in result
        assert "ELEC" in result
        assert result["MECH"]["total"] == 0
        assert result["MECH"]["fulfilled"] == 0
        assert result["MECH"]["blocking_total"] == 0
        assert result["MECH"]["blocking_fulfilled"] == 0
        assert result["MECH"]["stage"] == mock_stage1

    def test_preserves_stage_object_reference(self):
        """测试保留阶段对象引用"""
        from app.services.assembly_kit_service import initialize_stage_results

        mock_stage = MagicMock()
        mock_stage.stage_code = "TEST"

        result = initialize_stage_results([mock_stage])

        assert result["TEST"]["stage"] is mock_stage


class TestAnalyzeBomItem:
    """测试 analyze_bom_item 函数"""

    def test_returns_none_when_material_not_found(self):
        """测试物料不存在时返回None"""
        from app.services.assembly_kit_service import analyze_bom_item

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_bom_item = MagicMock()
        mock_bom_item.material_id = 999

        result = analyze_bom_item(
            mock_db,
            mock_bom_item,
            date.today(),
            {},
            {},
            lambda *args: (Decimal(0), Decimal(0), Decimal(0), Decimal(0)),
        )

        assert result is None

    def test_uses_default_stage_when_no_attr(self):
        """测试无装配属性时使用默认阶段"""
        from app.services.assembly_kit_service import analyze_bom_item

        mock_db = MagicMock()
        mock_material = MagicMock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"

        # 物料查询返回material，装配属性查询返回None
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_material,
            None,  # No assembly attrs
        ]

        mock_bom_item = MagicMock()
        mock_bom_item.id = 1
        mock_bom_item.material_id = 1
        mock_bom_item.quantity = Decimal("10")
        mock_bom_item.required_date = None

        stage_results = {"MECH": {"total": 0, "fulfilled": 0, "blocking_total": 0, "blocking_fulfilled": 0}}

        def calc_available(db, material_id, check_date):
            return (Decimal("20"), Decimal("0"), Decimal("0"), Decimal("20"))

        result = analyze_bom_item(
            mock_db,
            mock_bom_item,
            date.today(),
            {},
            stage_results,
            calc_available,
        )

        # 应该没有缺料（因为可用数量足够）
        assert result is None
        assert stage_results["MECH"]["total"] == 1
        assert stage_results["MECH"]["fulfilled"] == 1

    def test_returns_shortage_details_when_insufficient(self):
        """测试物料不足时返回缺料明细"""
        from app.services.assembly_kit_service import analyze_bom_item

        mock_db = MagicMock()
        mock_material = MagicMock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"

        mock_attr = MagicMock()
        mock_attr.assembly_stage = "ELEC"
        mock_attr.is_blocking = True

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_material,
            mock_attr,
        ]

        mock_bom_item = MagicMock()
        mock_bom_item.id = 1
        mock_bom_item.material_id = 1
        mock_bom_item.quantity = Decimal("10")
        mock_bom_item.required_date = date.today() + timedelta(days=7)

        stage_results = {"ELEC": {"total": 0, "fulfilled": 0, "blocking_total": 0, "blocking_fulfilled": 0}}

        def calc_available(db, material_id, check_date):
            return (Decimal("5"), Decimal("0"), Decimal("0"), Decimal("5"))

        with patch("app.services.assembly_kit_service.get_expected_arrival_date", return_value=None):
            with patch("app.api.v1.endpoints.assembly_kit.kit_analysis.utils.determine_alert_level", return_value="WARNING"):
                result = analyze_bom_item(
                    mock_db,
                    mock_bom_item,
                    date.today(),
                    {},
                    stage_results,
                    calc_available,
                )

        assert result is not None
        assert result["shortage_qty"] == Decimal("5")
        assert result["is_blocking"] is True
        assert result["assembly_stage"] == "ELEC"

    def test_updates_stage_stats_correctly(self):
        """测试正确更新阶段统计"""
        from app.services.assembly_kit_service import analyze_bom_item

        mock_db = MagicMock()
        mock_material = MagicMock()
        mock_material.id = 1
        mock_material.material_code = "MAT001"
        mock_material.material_name = "测试物料"

        mock_attr = MagicMock()
        mock_attr.assembly_stage = "MECH"
        mock_attr.is_blocking = True

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_material,
            mock_attr,
        ]

        mock_bom_item = MagicMock()
        mock_bom_item.id = 1
        mock_bom_item.material_id = 1
        mock_bom_item.quantity = Decimal("10")
        mock_bom_item.required_date = None

        stage_results = {"MECH": {"total": 5, "fulfilled": 3, "blocking_total": 2, "blocking_fulfilled": 1}}

        def calc_available(db, material_id, check_date):
            return (Decimal("20"), Decimal("0"), Decimal("0"), Decimal("20"))

        result = analyze_bom_item(
            mock_db,
            mock_bom_item,
            date.today(),
            {},
            stage_results,
            calc_available,
        )

        assert stage_results["MECH"]["total"] == 6
        assert stage_results["MECH"]["fulfilled"] == 4
        assert stage_results["MECH"]["blocking_total"] == 3
        assert stage_results["MECH"]["blocking_fulfilled"] == 2


class TestGetExpectedArrivalDate:
    """测试 get_expected_arrival_date 函数"""

    def test_returns_none_when_no_po(self):
        """测试无采购订单时返回None"""
        from app.services.assembly_kit_service import get_expected_arrival_date

        mock_db = MagicMock()
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = get_expected_arrival_date(mock_db, material_id=1)

        assert result is None

    def test_returns_promised_date_from_po(self):
        """测试返回采购订单的承诺日期"""
        from app.services.assembly_kit_service import get_expected_arrival_date

        mock_db = MagicMock()
        expected_date = date.today() + timedelta(days=10)

        mock_po_item = MagicMock()
        mock_po_item.order = MagicMock()
        mock_po_item.order.promised_date = expected_date

        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.first.return_value = mock_po_item

        result = get_expected_arrival_date(mock_db, material_id=1)

        assert result == expected_date

    def test_handles_exception_gracefully(self):
        """测试异常处理"""
        from app.services.assembly_kit_service import get_expected_arrival_date

        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("DB error")

        result = get_expected_arrival_date(mock_db, material_id=1)

        assert result is None


class TestCalculateStageKitRates:
    """测试 calculate_stage_kit_rates 函数"""

    def test_returns_empty_when_no_stages(self):
        """测试无阶段时返回空结果"""
        from app.services.assembly_kit_service import calculate_stage_kit_rates

        result = calculate_stage_kit_rates([], {}, [])

        stage_rates, can_proceed, first_blocked, workable, stats, blocking_items = result

        assert stage_rates == []
        assert can_proceed is True
        assert first_blocked is None
        assert workable is None

    def test_calculates_kit_rates_correctly(self):
        """测试正确计算齐套率"""
        from app.services.assembly_kit_service import calculate_stage_kit_rates

        mock_stage = MagicMock()
        mock_stage.stage_code = "MECH"
        mock_stage.stage_name = "机械模组"
        mock_stage.stage_order = 1
        mock_stage.color_code = "#FF0000"

        stages = [mock_stage]
        stage_results = {
            "MECH": {
                "total": 10,
                "fulfilled": 8,
                "blocking_total": 5,
                "blocking_fulfilled": 5,
            }
        }

        result = calculate_stage_kit_rates(stages, stage_results, [])

        stage_rates, can_proceed, first_blocked, workable, stats, blocking_items = result

        assert len(stage_rates) == 1
        assert stage_rates[0]["kit_rate"] == Decimal("80")
        assert stage_rates[0]["blocking_rate"] == Decimal("100")
        assert stage_rates[0]["can_start"] is True
        assert can_proceed is True
        assert workable == "MECH"

    def test_identifies_blocked_stage(self):
        """测试识别阻塞阶段"""
        from app.services.assembly_kit_service import calculate_stage_kit_rates

        mock_stage1 = MagicMock()
        mock_stage1.stage_code = "MECH"
        mock_stage1.stage_name = "机械模组"
        mock_stage1.stage_order = 1
        mock_stage1.color_code = "#FF0000"

        mock_stage2 = MagicMock()
        mock_stage2.stage_code = "ELEC"
        mock_stage2.stage_name = "电气模组"
        mock_stage2.stage_order = 2
        mock_stage2.color_code = "#00FF00"

        stages = [mock_stage1, mock_stage2]
        stage_results = {
            "MECH": {
                "total": 10,
                "fulfilled": 10,
                "blocking_total": 5,
                "blocking_fulfilled": 5,  # 100% blocking rate
            },
            "ELEC": {
                "total": 10,
                "fulfilled": 5,
                "blocking_total": 5,
                "blocking_fulfilled": 3,  # 60% blocking rate
            },
        }

        shortage_details = [
            {"assembly_stage": "ELEC", "is_blocking": True, "material_code": "E001"}
        ]

        result = calculate_stage_kit_rates(stages, stage_results, shortage_details)

        stage_rates, can_proceed, first_blocked, workable, stats, blocking_items = result

        assert first_blocked == "ELEC"
        assert workable == "MECH"
        assert len(blocking_items) == 1

    def test_calculates_overall_stats(self):
        """测试计算总体统计"""
        from app.services.assembly_kit_service import calculate_stage_kit_rates

        mock_stage1 = MagicMock()
        mock_stage1.stage_code = "MECH"
        mock_stage1.stage_name = "机械模组"
        mock_stage1.stage_order = 1
        mock_stage1.color_code = "#FF0000"

        mock_stage2 = MagicMock()
        mock_stage2.stage_code = "ELEC"
        mock_stage2.stage_name = "电气模组"
        mock_stage2.stage_order = 2
        mock_stage2.color_code = "#00FF00"

        stages = [mock_stage1, mock_stage2]
        stage_results = {
            "MECH": {
                "total": 10,
                "fulfilled": 8,
                "blocking_total": 5,
                "blocking_fulfilled": 5,
            },
            "ELEC": {
                "total": 15,
                "fulfilled": 12,
                "blocking_total": 8,
                "blocking_fulfilled": 8,
            },
        }

        result = calculate_stage_kit_rates(stages, stage_results, [])

        stage_rates, can_proceed, first_blocked, workable, stats, blocking_items = result

        assert stats["total"] == 25
        assert stats["fulfilled"] == 20
        assert stats["blocking_total"] == 13
        assert stats["blocking_fulfilled"] == 13

    def test_handles_zero_totals(self):
        """测试处理零总数"""
        from app.services.assembly_kit_service import calculate_stage_kit_rates

        mock_stage = MagicMock()
        mock_stage.stage_code = "MECH"
        mock_stage.stage_name = "机械模组"
        mock_stage.stage_order = 1
        mock_stage.color_code = "#FF0000"

        stages = [mock_stage]
        stage_results = {
            "MECH": {
                "total": 0,
                "fulfilled": 0,
                "blocking_total": 0,
                "blocking_fulfilled": 0,
            }
        }

        result = calculate_stage_kit_rates(stages, stage_results, [])

        stage_rates, can_proceed, first_blocked, workable, stats, blocking_items = result

        assert stage_rates[0]["kit_rate"] == Decimal("100")
        assert stage_rates[0]["blocking_rate"] == Decimal("100")
        assert stage_rates[0]["can_start"] is True

    def test_stage_without_results_uses_defaults(self):
        """测试阶段无结果时使用默认值"""
        from app.services.assembly_kit_service import calculate_stage_kit_rates

        mock_stage = MagicMock()
        mock_stage.stage_code = "UNKNOWN"
        mock_stage.stage_name = "未知阶段"
        mock_stage.stage_order = 1
        mock_stage.color_code = "#CCCCCC"

        stages = [mock_stage]
        stage_results = {}  # No results for this stage

        result = calculate_stage_kit_rates(stages, stage_results, [])

        stage_rates, can_proceed, first_blocked, workable, stats, blocking_items = result

        assert stage_rates[0]["total_items"] == 0
        assert stage_rates[0]["kit_rate"] == Decimal("100")
