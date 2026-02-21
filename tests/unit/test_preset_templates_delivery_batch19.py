# -*- coding: utf-8 -*-
"""
预设阶段模板 - 交付和结项阶段 单元测试 (Batch 19)

测试 app/services/preset_stage_templates/templates/standard/delivery.py
覆盖率目标: 60%+
"""

import pytest


@pytest.mark.unit
class TestDeliveryStagesImport:
    """测试交付阶段导入"""

    def test_can_import_delivery_stages(self):
        """测试可以导入DELIVERY_STAGES"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        assert DELIVERY_STAGES is not None

    def test_delivery_stages_is_list(self):
        """测试DELIVERY_STAGES是列表"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        assert isinstance(DELIVERY_STAGES, list)


@pytest.mark.unit
class TestDeliveryStagesStructure:
    """测试交付阶段结构"""

    def test_delivery_stages_not_empty(self):
        """测试交付阶段不为空"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        assert len(DELIVERY_STAGES) > 0

    def test_delivery_stages_count(self):
        """测试交付阶段数量（S7-S9共3个）"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        # 根据注释，应该有3个阶段：S7, S8, S9
        assert len(DELIVERY_STAGES) == 3

    def test_stages_have_required_fields(self):
        """测试阶段包含必需字段"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        required_fields = ["stage_code", "stage_name", "sequence"]

        for stage in DELIVERY_STAGES:
            for field in required_fields:
                assert field in stage, f"Stage missing {field}: {stage}"

    def test_stage_codes_correct(self):
        """测试阶段代码正确（S7, S8, S9）"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        expected_codes = {"S7", "S8", "S9"}
        actual_codes = {stage["stage_code"] for stage in DELIVERY_STAGES}

        assert actual_codes == expected_codes


@pytest.mark.unit
class TestDeliveryStagesContent:
    """测试交付阶段内容"""

    def test_s7_packaging_stage(self):
        """测试S7包装发运阶段"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        s7 = next(s for s in DELIVERY_STAGES if s["stage_code"] == "S7")

        assert s7["stage_name"] == "包装发运"
        assert s7["sequence"] == 6
        assert s7["estimated_days"] == 3
        assert s7["is_required"] is True

    def test_s7_has_nodes(self):
        """测试S7包含节点"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        s7 = next(s for s in DELIVERY_STAGES if s["stage_code"] == "S7")

        assert "nodes" in s7
        assert len(s7["nodes"]) >= 3  # 至少3个节点

    def test_s8_installation_stage(self):
        """测试S8现场安装阶段"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        s8 = next(s for s in DELIVERY_STAGES if s["stage_code"] == "S8")

        assert s8["stage_name"] == "现场安装"
        assert s8["sequence"] == 7
        assert s8["estimated_days"] == 7
        assert s8["is_required"] is True

    def test_s8_has_sat_approval(self):
        """测试S8包含SAT验收节点"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        s8 = next(s for s in DELIVERY_STAGES if s["stage_code"] == "S8")
        nodes = s8["nodes"]

        # 查找SAT验收节点
        sat_node = next(
            (n for n in nodes if "SAT" in n.get("node_name", "")),
            None,
        )

        assert sat_node is not None
        assert sat_node["node_type"] == "APPROVAL"

    def test_s9_warranty_stage(self):
        """测试S9质保结项阶段"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        s9 = next(s for s in DELIVERY_STAGES if s["stage_code"] == "S9")

        assert s9["stage_name"] == "质保结项"
        assert s9["sequence"] == 8
        assert s9["estimated_days"] == 7
        assert s9["is_required"] is True

    def test_s9_has_archiving(self):
        """测试S9包含文档归档节点"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        s9 = next(s for s in DELIVERY_STAGES if s["stage_code"] == "S9")
        nodes = s9["nodes"]

        # 查找文档归档节点
        archive_node = next(
            (n for n in nodes if "归档" in n.get("node_name", "")),
            None,
        )

        assert archive_node is not None


@pytest.mark.unit
class TestDeliveryNodesStructure:
    """测试交付阶段节点结构"""

    def test_all_nodes_have_codes(self):
        """测试所有节点都有代码"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        for stage in DELIVERY_STAGES:
            for node in stage.get("nodes", []):
                assert "node_code" in node
                assert node["node_code"]

    def test_all_nodes_have_names(self):
        """测试所有节点都有名称"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        for stage in DELIVERY_STAGES:
            for node in stage.get("nodes", []):
                assert "node_name" in node
                assert node["node_name"]

    def test_all_nodes_have_types(self):
        """测试所有节点都有类型"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        valid_types = {"TASK", "APPROVAL", "DELIVERABLE"}

        for stage in DELIVERY_STAGES:
            for node in stage.get("nodes", []):
                assert "node_type" in node
                assert node["node_type"] in valid_types

    def test_nodes_have_sequences(self):
        """测试节点有序号"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        for stage in DELIVERY_STAGES:
            for node in stage.get("nodes", []):
                assert "sequence" in node
                assert isinstance(node["sequence"], int)
                assert node["sequence"] >= 0

    def test_nodes_have_estimated_days(self):
        """测试节点有预估天数"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        for stage in DELIVERY_STAGES:
            for node in stage.get("nodes", []):
                assert "estimated_days" in node
                assert isinstance(node["estimated_days"], (int, float))
                assert node["estimated_days"] > 0


@pytest.mark.unit
class TestDeliveryNodesRoles:
    """测试节点角色配置"""

    def test_nodes_have_owner_roles(self):
        """测试节点有负责人角色"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        for stage in DELIVERY_STAGES:
            for node in stage.get("nodes", []):
                assert "owner_role_code" in node
                assert node["owner_role_code"]

    def test_nodes_have_participant_roles(self):
        """测试节点有参与者角色列表"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        for stage in DELIVERY_STAGES:
            for node in stage.get("nodes", []):
                assert "participant_role_codes" in node
                assert isinstance(node["participant_role_codes"], list)

    def test_common_roles_exist(self):
        """测试常见角色存在"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        all_roles = set()
        for stage in DELIVERY_STAGES:
            for node in stage.get("nodes", []):
                all_roles.add(node.get("owner_role_code"))
                all_roles.update(node.get("participant_role_codes", []))

        # 常见角色应该出现
        expected_roles = {"PM", "QA", "SALES"}
        assert expected_roles.issubset(all_roles)


@pytest.mark.unit
class TestDeliveryNodesDependencies:
    """测试节点依赖关系"""

    def test_some_nodes_have_dependencies(self):
        """测试部分节点有依赖"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        has_dependency = False
        for stage in DELIVERY_STAGES:
            for node in stage.get("nodes", []):
                if node.get("dependency_node_codes"):
                    has_dependency = True
                    break

        assert has_dependency

    def test_dependencies_are_lists(self):
        """测试依赖是列表类型"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        for stage in DELIVERY_STAGES:
            for node in stage.get("nodes", []):
                if "dependency_node_codes" in node:
                    assert isinstance(node["dependency_node_codes"], list)


@pytest.mark.unit
class TestDeliveryNodesDeliverables:
    """测试节点交付物"""

    def test_nodes_have_deliverables(self):
        """测试节点有交付物列表"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        for stage in DELIVERY_STAGES:
            for node in stage.get("nodes", []):
                assert "deliverables" in node
                assert isinstance(node["deliverables"], list)

    def test_deliverables_not_empty(self):
        """测试交付物列表不为空"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        total_deliverables = 0
        for stage in DELIVERY_STAGES:
            for node in stage.get("nodes", []):
                total_deliverables += len(node.get("deliverables", []))

        assert total_deliverables > 0

    def test_key_deliverables_exist(self):
        """测试关键交付物存在"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        all_deliverables = []
        for stage in DELIVERY_STAGES:
            for node in stage.get("nodes", []):
                all_deliverables.extend(node.get("deliverables", []))

        # 关键交付物
        key_deliverables = ["SAT验收报告", "质保交接单"]
        for key_del in key_deliverables:
            assert any(key_del in d for d in all_deliverables)


@pytest.mark.unit
class TestDeliveryStagesValidation:
    """测试交付阶段验证"""

    def test_stage_codes_unique(self):
        """测试阶段代码唯一"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        codes = [s["stage_code"] for s in DELIVERY_STAGES]
        assert len(codes) == len(set(codes))

    def test_node_codes_unique_within_stage(self):
        """测试阶段内节点代码唯一"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        for stage in DELIVERY_STAGES:
            node_codes = [n["node_code"] for n in stage.get("nodes", [])]
            assert len(node_codes) == len(set(node_codes))

    def test_stages_ordered_by_sequence(self):
        """测试阶段按序号排序"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        sequences = [s["sequence"] for s in DELIVERY_STAGES]
        assert sequences == sorted(sequences)

    def test_nodes_ordered_by_sequence(self):
        """测试节点按序号排序"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        for stage in DELIVERY_STAGES:
            node_sequences = [n["sequence"] for n in stage.get("nodes", [])]
            assert node_sequences == sorted(node_sequences)

    def test_estimated_days_reasonable(self):
        """测试预估天数合理"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        for stage in DELIVERY_STAGES:
            # 阶段预估天数应该在1-30天之间（合理范围）
            assert 1 <= stage["estimated_days"] <= 30

            for node in stage.get("nodes", []):
                # 节点预估天数应该不超过阶段天数
                assert node["estimated_days"] <= stage["estimated_days"]


@pytest.mark.unit
class TestDeliveryStagesUsage:
    """测试交付阶段使用"""

    def test_can_iterate_stages(self):
        """测试可以遍历阶段"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        count = 0
        for stage in DELIVERY_STAGES:
            count += 1
            assert stage is not None

        assert count == 3

    def test_can_filter_required_stages(self):
        """测试可以筛选必需阶段"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        required_stages = [s for s in DELIVERY_STAGES if s.get("is_required")]

        # 所有交付阶段都是必需的
        assert len(required_stages) == 3

    def test_can_calculate_total_days(self):
        """测试可以计算总天数"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        total_days = sum(s["estimated_days"] for s in DELIVERY_STAGES)

        # 3 + 7 + 7 = 17天
        assert total_days == 17

    def test_can_extract_all_nodes(self):
        """测试可以提取所有节点"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        all_nodes = []
        for stage in DELIVERY_STAGES:
            all_nodes.extend(stage.get("nodes", []))

        assert len(all_nodes) > 0

    def test_can_build_stage_map(self):
        """测试可以构建阶段映射"""
        from app.services.preset_stage_templates.templates.standard.delivery import (
            DELIVERY_STAGES,
        )

        stage_map = {s["stage_code"]: s for s in DELIVERY_STAGES}

        assert "S7" in stage_map
        assert "S8" in stage_map
        assert "S9" in stage_map
        assert len(stage_map) == 3
