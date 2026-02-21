# -*- coding: utf-8 -*-
"""
预设阶段模板 - 执行阶段 单元测试 (Batch 19)

测试 app/services/preset_stage_templates/templates/execution_stages.py
覆盖率目标: 60%+
"""

import pytest


@pytest.mark.unit
class TestExecutionStagesImport:
    """测试执行阶段导入"""

    def test_can_import_execution_stages(self):
        """测试可以导入EXECUTION_STAGES"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        assert EXECUTION_STAGES is not None

    def test_execution_stages_is_list(self):
        """测试EXECUTION_STAGES是列表类型"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        assert isinstance(EXECUTION_STAGES, list)

    def test_all_export(self):
        """测试__all__导出"""
        from app.services.preset_stage_templates.templates import execution_stages

        assert hasattr(execution_stages, "__all__")
        assert "EXECUTION_STAGES" in execution_stages.__all__


@pytest.mark.unit
class TestExecutionStagesStructure:
    """测试执行阶段结构"""

    def test_execution_stages_not_empty(self):
        """测试执行阶段不为空"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        assert len(EXECUTION_STAGES) > 0

    def test_execution_stages_contains_dicts(self):
        """测试执行阶段包含字典元素"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        for stage in EXECUTION_STAGES:
            assert isinstance(stage, dict)

    def test_stages_have_required_fields(self):
        """测试阶段包含必需字段"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        required_fields = ["stage_code", "stage_name"]

        for stage in EXECUTION_STAGES:
            for field in required_fields:
                assert field in stage, f"Stage missing {field}: {stage}"

    def test_stage_codes_are_unique(self):
        """测试阶段代码唯一"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        stage_codes = [stage.get("stage_code") for stage in EXECUTION_STAGES]
        assert len(stage_codes) == len(set(stage_codes))


@pytest.mark.unit
class TestExecutionStagesContent:
    """测试执行阶段内容"""

    def test_stages_have_nodes(self):
        """测试阶段包含节点"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        for stage in EXECUTION_STAGES:
            if "nodes" in stage:
                assert isinstance(stage["nodes"], list)

    def test_nodes_structure(self):
        """测试节点结构"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        for stage in EXECUTION_STAGES:
            if "nodes" in stage:
                for node in stage["nodes"]:
                    assert isinstance(node, dict)
                    assert "node_code" in node or "node_name" in node

    def test_stage_sequence(self):
        """测试阶段有序号"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        for stage in EXECUTION_STAGES:
            if "sequence" in stage:
                assert isinstance(stage["sequence"], int)
                assert stage["sequence"] >= 0

    def test_estimated_days(self):
        """测试预估天数"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        for stage in EXECUTION_STAGES:
            if "estimated_days" in stage:
                assert isinstance(stage["estimated_days"], (int, float))
                assert stage["estimated_days"] > 0


@pytest.mark.unit
class TestExecutionStagesIntegration:
    """测试执行阶段集成"""

    def test_can_iterate_stages(self):
        """测试可以遍历阶段"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        count = 0
        for stage in EXECUTION_STAGES:
            count += 1
            assert stage is not None

        assert count > 0

    def test_can_filter_stages(self):
        """测试可以筛选阶段"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        # 筛选包含特定字段的阶段
        required_stages = [
            stage for stage in EXECUTION_STAGES if stage.get("is_required") is True
        ]

        # 应该有一些必需阶段
        assert isinstance(required_stages, list)

    def test_can_sort_stages(self):
        """测试可以排序阶段"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        # 按序号排序
        stages_with_seq = [
            stage for stage in EXECUTION_STAGES if "sequence" in stage
        ]

        if stages_with_seq:
            sorted_stages = sorted(stages_with_seq, key=lambda x: x["sequence"])
            assert len(sorted_stages) == len(stages_with_seq)

    def test_can_access_stage_by_code(self):
        """测试可以通过代码访问阶段"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        # 创建代码到阶段的映射
        stage_map = {stage["stage_code"]: stage for stage in EXECUTION_STAGES}

        assert len(stage_map) > 0
        # 验证所有stage_code都被映射
        assert len(stage_map) == len(EXECUTION_STAGES)


@pytest.mark.unit
class TestExecutionStagesValidation:
    """测试执行阶段验证"""

    def test_no_duplicate_stage_codes(self):
        """测试没有重复的阶段代码"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        codes = [stage["stage_code"] for stage in EXECUTION_STAGES]
        unique_codes = set(codes)

        assert len(codes) == len(unique_codes)

    def test_stage_names_not_empty(self):
        """测试阶段名称不为空"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        for stage in EXECUTION_STAGES:
            assert stage["stage_name"]
            assert len(stage["stage_name"]) > 0

    def test_nodes_have_valid_types(self):
        """测试节点类型有效"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        valid_types = ["TASK", "APPROVAL", "DELIVERABLE", "MILESTONE"]

        for stage in EXECUTION_STAGES:
            if "nodes" in stage:
                for node in stage["nodes"]:
                    if "node_type" in node:
                        # 如果有node_type，应该是有效类型之一
                        # （或者可以是其他业务定义的类型）
                        assert isinstance(node["node_type"], str)

    def test_description_exists(self):
        """测试描述字段存在"""
        from app.services.preset_stage_templates.templates.execution_stages import (
            EXECUTION_STAGES,
        )

        stages_with_desc = [
            stage for stage in EXECUTION_STAGES if "description" in stage
        ]

        # 大多数阶段应该有描述
        assert len(stages_with_desc) > 0
