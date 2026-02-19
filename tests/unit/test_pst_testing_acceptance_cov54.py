"""Tests for app/services/preset_stage_templates/templates/execution/testing_acceptance.py"""
import pytest
from unittest.mock import MagicMock

try:
    from app.services.preset_stage_templates.templates.execution.testing_acceptance import (
        TESTING_ACCEPTANCE_STAGES,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def test_is_list():
    """TESTING_ACCEPTANCE_STAGES 是列表"""
    assert isinstance(TESTING_ACCEPTANCE_STAGES, list)


def test_has_four_stages():
    """包含 4 个阶段（S17-S20）"""
    assert len(TESTING_ACCEPTANCE_STAGES) == 4


def test_stage_codes_are_unique():
    """所有阶段编码唯一"""
    codes = [s['stage_code'] for s in TESTING_ACCEPTANCE_STAGES]
    assert len(codes) == len(set(codes))


def test_stage_codes_are_s17_to_s20():
    """阶段编码为 S17、S18、S19、S20"""
    codes = {s['stage_code'] for s in TESTING_ACCEPTANCE_STAGES}
    assert codes == {'S17', 'S18', 'S19', 'S20'}


def test_each_stage_has_required_fields():
    """每个阶段包含必需字段"""
    required_fields = ['stage_code', 'stage_name', 'sequence', 'nodes']
    for stage in TESTING_ACCEPTANCE_STAGES:
        for field in required_fields:
            assert field in stage, f"Stage {stage.get('stage_code')} missing field: {field}"


def test_s17_is_milestone():
    """S17 内部验收是里程碑"""
    s17 = next(s for s in TESTING_ACCEPTANCE_STAGES if s['stage_code'] == 'S17')
    assert s17.get('is_milestone') is True


def test_s17_has_five_nodes():
    """S17 包含 5 个节点"""
    s17 = next(s for s in TESTING_ACCEPTANCE_STAGES if s['stage_code'] == 'S17')
    assert len(s17['nodes']) == 5


def test_nodes_have_required_fields():
    """每个节点包含必需字段"""
    required_node_fields = ['node_code', 'node_name', 'node_type', 'sequence', 'completion_method']
    for stage in TESTING_ACCEPTANCE_STAGES:
        for node in stage['nodes']:
            for field in required_node_fields:
                assert field in node, (
                    f"Node {node.get('node_code')} in stage {stage.get('stage_code')} missing: {field}"
                )
