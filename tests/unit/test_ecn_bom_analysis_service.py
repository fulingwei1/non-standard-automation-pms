# -*- coding: utf-8 -*-
"""
ecn_bom_analysis_service 单元测试

测试ECN BOM影响分析服务：
- BOM影响分析
- 级联影响分析
- 成本/交期影响计算
- 呆滞料风险识别
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.ecn_bom_analysis_service import EcnBomAnalysisService


def create_mock_db_session():
    """创建模拟的数据库会话"""
    return MagicMock()


def create_mock_ecn(
    ecn_id=1,
    ecn_no="ECN250712001",
    machine_id=1,
    project_id=1,
    status="PENDING"
):
    """创建模拟的ECN"""
    mock = MagicMock()
    mock.id = ecn_id
    mock.ecn_no = ecn_no
    mock.machine_id = machine_id
    mock.project_id = project_id
    mock.status = status
    return mock


def create_mock_machine(machine_id=1, machine_no="PN001", machine_name="测试设备"):
    """创建模拟的设备"""
    mock = MagicMock()
    mock.id = machine_id
    mock.machine_no = machine_no
    mock.machine_name = machine_name
    return mock


def create_mock_bom_header(
    bom_id=1,
    bom_no="BOM250712001",
    bom_name="测试BOM",
    machine_id=1,
    status="RELEASED",
    is_latest=True
):
    """创建模拟的BOM头"""
    mock = MagicMock()
    mock.id = bom_id
    mock.bom_no = bom_no
    mock.bom_name = bom_name
    mock.machine_id = machine_id
    mock.status = status
    mock.is_latest = is_latest
    return mock


def create_mock_bom_item(
    item_id=1,
    bom_id=1,
    material_id=1,
    material_code="M001",
    material_name="测试物料",
    quantity=10,
    amount=1000,
    parent_item_id=None
):
    """创建模拟的BOM项"""
    mock = MagicMock()
    mock.id = item_id
    mock.bom_id = bom_id
    mock.material_id = material_id
    mock.material_code = material_code
    mock.material_name = material_name
    mock.quantity = quantity
    mock.amount = amount
    mock.parent_item_id = parent_item_id
    return mock


def create_mock_affected_material(
    mat_id=1,
    ecn_id=1,
    material_id=1,
    material_code="M001",
    change_type="UPDATE",
    cost_impact=None,
    old_quantity=None,
    new_quantity=None,
    old_specification=None,
    new_specification=None
):
    """创建模拟的受影响物料"""
    mock = MagicMock()
    mock.id = mat_id
    mock.ecn_id = ecn_id
    mock.material_id = material_id
    mock.material_code = material_code
    mock.change_type = change_type
    mock.cost_impact = cost_impact
    mock.old_quantity = old_quantity
    mock.new_quantity = new_quantity
    mock.old_specification = old_specification
    mock.new_specification = new_specification
    return mock


def create_mock_material(
    material_id=1,
    material_code="M001",
    material_name="测试物料",
    current_stock=100,
    standard_price=50.0,
    last_price=55.0,
    lead_time_days=14
):
    """创建模拟的物料"""
    mock = MagicMock()
    mock.id = material_id
    mock.material_code = material_code
    mock.material_name = material_name
    mock.current_stock = current_stock
    mock.standard_price = standard_price
    mock.last_price = last_price
    mock.lead_time_days = lead_time_days
    return mock


def create_mock_po_item(
    item_id=1,
    material_id=1,
    quantity=50,
    received_qty=20
):
    """创建模拟的采购订单项"""
    mock = MagicMock()
    mock.id = item_id
    mock.material_id = material_id
    mock.quantity = quantity
    mock.received_qty = received_qty
    return mock


@pytest.mark.unit
class TestAnalyzeBomImpact:
    """测试 analyze_bom_impact 方法"""

    def test_raises_error_for_nonexistent_ecn(self):
        """测试ECN不存在时抛出异常"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.first.return_value = None

        service = EcnBomAnalysisService(db)

        with pytest.raises(ValueError, match="ECN 1 不存在"):
            service.analyze_bom_impact(ecn_id=1)

    def test_raises_error_without_machine_id(self):
        """测试无设备ID时抛出异常"""
        db = create_mock_db_session()
        ecn = create_mock_ecn(machine_id=None)
        db.query.return_value.filter.return_value.first.return_value = ecn

        service = EcnBomAnalysisService(db)

        with pytest.raises(ValueError, match="需要指定设备ID或ECN必须关联设备"):
            service.analyze_bom_impact(ecn_id=1)

    def test_returns_no_impact_when_no_affected_materials(self):
        """测试无受影响物料时返回无影响"""
        db = create_mock_db_session()
        ecn = create_mock_ecn()

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            mock_filter = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:  # ECN query
            mock_filter.first.return_value = ecn
        elif call_count[0] == 2:  # Affected materials
        mock_filter.all.return_value = []
        return mock_filter

        db.query.return_value.filter.side_effect = filter_side_effect

        service = EcnBomAnalysisService(db)
        result = service.analyze_bom_impact(ecn_id=1)

        assert result["has_impact"] is False
        assert result["message"] == "没有受影响的物料"

    def test_raises_error_for_nonexistent_machine(self):
        """测试设备不存在时抛出异常"""
        db = create_mock_db_session()
        ecn = create_mock_ecn()
        affected_mat = create_mock_affected_material()

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            mock_filter = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:  # ECN query
            mock_filter.first.return_value = ecn
        elif call_count[0] == 2:  # Affected materials
        mock_filter.all.return_value = [affected_mat]
        elif call_count[0] == 3:  # Machine query
        mock_filter.first.return_value = None
        return mock_filter

        db.query.return_value.filter.side_effect = filter_side_effect

        service = EcnBomAnalysisService(db)

        with pytest.raises(ValueError, match="设备 1 不存在"):
            service.analyze_bom_impact(ecn_id=1)

    def test_returns_no_impact_when_no_released_bom(self):
        """测试无已发布BOM时返回无影响"""
        db = create_mock_db_session()
        ecn = create_mock_ecn()
        affected_mat = create_mock_affected_material()
        machine = create_mock_machine()

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            mock_filter = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:  # ECN query
            mock_filter.first.return_value = ecn
        elif call_count[0] == 2:  # Affected materials
        mock_filter.all.return_value = [affected_mat]
        elif call_count[0] == 3:  # Machine query
        mock_filter.first.return_value = machine
        elif call_count[0] == 4:  # BOM headers
        mock_filter.all.return_value = []
        return mock_filter

        db.query.return_value.filter.side_effect = filter_side_effect

        service = EcnBomAnalysisService(db)
        result = service.analyze_bom_impact(ecn_id=1)

        assert result["has_impact"] is False
        assert result["message"] == "设备没有已发布的BOM"


@pytest.mark.unit
class TestGetImpactDescription:
    """测试 _get_impact_description 方法"""

    def test_maps_add_change_type(self):
        """测试新增变更类型映射"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)
        affected_mat = create_mock_affected_material(change_type="ADD")

        result = service._get_impact_description(affected_mat)

        assert "新增" in result

    def test_maps_delete_change_type(self):
        """测试删除变更类型映射"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)
        affected_mat = create_mock_affected_material(change_type="DELETE")

        result = service._get_impact_description(affected_mat)

        assert "删除" in result

    def test_maps_update_change_type(self):
        """测试修改变更类型映射"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)
        affected_mat = create_mock_affected_material(change_type="UPDATE")

        result = service._get_impact_description(affected_mat)

        assert "修改" in result

    def test_maps_replace_change_type(self):
        """测试替换变更类型映射"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)
        affected_mat = create_mock_affected_material(change_type="REPLACE")

        result = service._get_impact_description(affected_mat)

        assert "替换" in result

    def test_includes_quantity_change(self):
        """测试包含数量变更信息"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)
        affected_mat = create_mock_affected_material(
        change_type="UPDATE",
        old_quantity=10,
        new_quantity=20
        )

        result = service._get_impact_description(affected_mat)

        assert "数量" in result
        assert "10" in result
        assert "20" in result

    def test_includes_specification_change(self):
        """测试包含规格变更信息"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)
        affected_mat = create_mock_affected_material(
        change_type="UPDATE",
        old_specification="规格A",
        new_specification="规格B"
        )

        result = service._get_impact_description(affected_mat)

        assert "规格变更" in result


@pytest.mark.unit
class TestCalculateObsoleteRiskLevel:
    """测试 _calculate_obsolete_risk_level 方法"""

    def test_returns_critical_for_high_cost(self):
        """测试高成本返回CRITICAL"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)

        result = service._calculate_obsolete_risk_level(
        obsolete_qty=Decimal(1000),
        obsolete_cost=Decimal(150000)
        )

        assert result == "CRITICAL"

    def test_returns_high_for_medium_high_cost(self):
        """测试中高成本返回HIGH"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)

        result = service._calculate_obsolete_risk_level(
        obsolete_qty=Decimal(500),
        obsolete_cost=Decimal(75000)
        )

        assert result == "HIGH"

    def test_returns_medium_for_medium_cost(self):
        """测试中等成本返回MEDIUM"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)

        result = service._calculate_obsolete_risk_level(
        obsolete_qty=Decimal(200),
        obsolete_cost=Decimal(25000)
        )

        assert result == "MEDIUM"

    def test_returns_low_for_low_cost(self):
        """测试低成本返回LOW"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)

        result = service._calculate_obsolete_risk_level(
        obsolete_qty=Decimal(50),
        obsolete_cost=Decimal(5000)
        )

        assert result == "LOW"

    def test_boundary_at_100000(self):
        """测试10万边界值"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)

        result = service._calculate_obsolete_risk_level(
        obsolete_qty=Decimal(100),
        obsolete_cost=Decimal(100000)
        )

        assert result == "CRITICAL"

    def test_boundary_at_50000(self):
        """测试5万边界值"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)

        result = service._calculate_obsolete_risk_level(
        obsolete_qty=Decimal(100),
        obsolete_cost=Decimal(50000)
        )

        assert result == "HIGH"

    def test_boundary_at_10000(self):
        """测试1万边界值"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)

        result = service._calculate_obsolete_risk_level(
        obsolete_qty=Decimal(100),
        obsolete_cost=Decimal(10000)
        )

        assert result == "MEDIUM"


@pytest.mark.unit
class TestCheckObsoleteMaterialRisk:
    """测试 check_obsolete_material_risk 方法"""

    def test_raises_error_for_nonexistent_ecn(self):
        """测试ECN不存在时抛出异常"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.first.return_value = None

        service = EcnBomAnalysisService(db)

        with pytest.raises(ValueError, match="ECN 1 不存在"):
            service.check_obsolete_material_risk(ecn_id=1)

    def test_returns_no_risk_when_no_delete_or_replace(self):
        """测试无删除/替换物料时返回无风险"""
        db = create_mock_db_session()
        ecn = create_mock_ecn()

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            mock_filter = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:  # ECN query
            mock_filter.first.return_value = ecn
        else:  # Affected materials with DELETE/REPLACE
        mock_filter.in_.return_value = mock_filter
        mock_filter.all.return_value = []
        return mock_filter

        db.query.return_value.filter.side_effect = filter_side_effect

        service = EcnBomAnalysisService(db)
        result = service.check_obsolete_material_risk(ecn_id=1)

        assert result["has_obsolete_risk"] is False
        assert result["message"] == "没有删除或替换的物料"

    def test_skips_affected_material_without_material_id(self):
        """测试跳过无物料ID的受影响物料"""
        db = create_mock_db_session()
        ecn = create_mock_ecn()
        affected_mat = create_mock_affected_material(material_id=None)

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            mock_filter = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:  # ECN query
            mock_filter.first.return_value = ecn
        else:
            mock_filter.in_.return_value = mock_filter
            mock_filter.all.return_value = [affected_mat]
            return mock_filter

            db.query.return_value.filter.side_effect = filter_side_effect

            service = EcnBomAnalysisService(db)
            result = service.check_obsolete_material_risk(ecn_id=1)

            assert result["has_obsolete_risk"] is False


@pytest.mark.unit
class TestAnalyzeCascadeImpact:
    """测试 _analyze_cascade_impact 方法"""

    def test_returns_empty_for_no_parent_child_relations(self):
        """测试无父子关系时返回空"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)

        bom_items = [
        create_mock_bom_item(item_id=1, parent_item_id=None),
        create_mock_bom_item(item_id=2, parent_item_id=None)
        ]
        affected_item_ids = {1}

        result = service._analyze_cascade_impact(bom_items, affected_item_ids)

        assert len(result) == 0

    def test_finds_upward_cascade(self):
        """测试向上级联影响"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)

        parent_item = create_mock_bom_item(item_id=1, material_code="PARENT")
        child_item = create_mock_bom_item(item_id=2, material_code="CHILD", parent_item_id=1)
        bom_items = [parent_item, child_item]
        affected_item_ids = {2}  # 子物料受影响

        result = service._analyze_cascade_impact(bom_items, affected_item_ids)

        # 应该找到父物料也受级联影响
        assert len(result) == 1
        assert result[0]["cascade_type"] == "UPWARD"
        assert result[0]["material_code"] == "PARENT"

    def test_finds_downward_cascade(self):
        """测试向下级联影响"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)

        parent_item = create_mock_bom_item(item_id=1, material_code="PARENT")
        child_item = create_mock_bom_item(item_id=2, material_code="CHILD", parent_item_id=1)
        bom_items = [parent_item, child_item]
        affected_item_ids = {1}  # 父物料受影响

        result = service._analyze_cascade_impact(bom_items, affected_item_ids)

        # 应该找到子物料也受级联影响
        assert len(result) == 1
        assert result[0]["cascade_type"] == "DOWNWARD"
        assert result[0]["material_code"] == "CHILD"


@pytest.mark.unit
class TestCalculateCostImpact:
    """测试 _calculate_cost_impact 方法"""

    def test_returns_zero_for_no_cost_impact(self):
        """测试无成本影响时返回0"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)

        affected_materials = [create_mock_affected_material(cost_impact=None)]
        bom_items = [create_mock_bom_item(amount=None)]
        affected_item_ids = set()

        result = service._calculate_cost_impact(affected_materials, bom_items, affected_item_ids)

        assert result == Decimal(0)

    def test_sums_cost_impact_from_affected_materials(self):
        """测试汇总受影响物料的成本影响"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)

        affected_materials = [
        create_mock_affected_material(cost_impact=1000),
        create_mock_affected_material(cost_impact=2000)
        ]
        bom_items = []
        affected_item_ids = set()

        result = service._calculate_cost_impact(affected_materials, bom_items, affected_item_ids)

        assert result == Decimal(3000)

    def test_subtracts_cost_for_delete_change(self):
        """测试删除物料时减去成本"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)

        affected_materials = [
        create_mock_affected_material(
        material_code="M001",
        change_type="DELETE",
        cost_impact=None
        )
        ]
        bom_items = [create_mock_bom_item(item_id=1, material_code="M001", amount=5000)]
        affected_item_ids = {1}

        result = service._calculate_cost_impact(affected_materials, bom_items, affected_item_ids)

        assert result == Decimal(-5000)


@pytest.mark.unit
class TestCalculateScheduleImpact:
    """测试 _calculate_schedule_impact 方法"""

    def test_returns_zero_for_no_affected_items(self):
        """测试无受影响项时返回0"""
        db = create_mock_db_session()
        service = EcnBomAnalysisService(db)

        result = service._calculate_schedule_impact([], [], set())

        assert result == 0

    def test_returns_max_lead_time_for_update_change(self):
        """测试更新变更返回最大交期"""
        db = create_mock_db_session()

        material = create_mock_material(material_id=1, lead_time_days=21)

        # 设置查询返回
        db.query.return_value.filter.return_value.first.return_value = material

        service = EcnBomAnalysisService(db)

        affected_materials = [
        create_mock_affected_material(
        material_code="M001",
        change_type="UPDATE"
        )
        ]
        bom_items = [create_mock_bom_item(item_id=1, material_code="M001", material_id=1)]
        affected_item_ids = {1}

        result = service._calculate_schedule_impact(affected_materials, bom_items, affected_item_ids)

        assert result == 21

    def test_returns_max_of_multiple_lead_times(self):
        """测试多个物料返回最大交期"""
        db = create_mock_db_session()

        materials = [
        create_mock_material(material_id=1, lead_time_days=14),
        create_mock_material(material_id=2, lead_time_days=28)
        ]

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            mock_filter = MagicMock()
            result = materials[call_count[0]] if call_count[0] < len(materials) else None
            mock_filter.first.return_value = result
            call_count[0] += 1
            return mock_filter

            db.query.return_value.filter.side_effect = filter_side_effect

            service = EcnBomAnalysisService(db)

            affected_materials = [
            create_mock_affected_material(material_code="M001", change_type="UPDATE"),
            create_mock_affected_material(material_code="M002", change_type="ADD")
            ]
            bom_items = [
            create_mock_bom_item(item_id=1, material_code="M001", material_id=1),
            create_mock_bom_item(item_id=2, material_code="M002", material_id=2)
            ]
            affected_item_ids = {1, 2}

            result = service._calculate_schedule_impact(affected_materials, bom_items, affected_item_ids)

            assert result == 28


@pytest.mark.unit
class TestSaveBomImpact:
    """测试 _save_bom_impact 方法"""

    def test_creates_new_record_when_not_exists(self):
        """测试不存在时创建新记录"""
        db = create_mock_db_session()
        db.query.return_value.filter.return_value.first.return_value = None

        service = EcnBomAnalysisService(db)

        service._save_bom_impact(
        ecn_id=1,
        bom_version_id=1,
        machine_id=1,
        project_id=1,
        affected_item_count=5,
        total_cost_impact=Decimal(10000),
        schedule_impact_days=14,
        impact_analysis={"test": "data"}
        )

        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_updates_existing_record(self):
        """测试已存在时更新记录"""
        db = create_mock_db_session()
        existing = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing

        service = EcnBomAnalysisService(db)

        service._save_bom_impact(
        ecn_id=1,
        bom_version_id=1,
        machine_id=1,
        project_id=1,
        affected_item_count=10,
        total_cost_impact=Decimal(20000),
        schedule_impact_days=21,
        impact_analysis={"updated": "data"}
        )

        assert existing.affected_item_count == 10
        assert existing.total_cost_impact == Decimal(20000)
        assert existing.schedule_impact_days == 21
        assert existing.analysis_status == "COMPLETED"
        db.add.assert_not_called()
        db.commit.assert_called_once()
