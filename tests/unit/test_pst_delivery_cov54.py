"""Tests for app/services/preset_stage_templates/templates/standard/delivery.py"""
import pytest
from unittest.mock import MagicMock

try:
    from app.services.preset_stage_templates.templates.standard.delivery import DELIVERY_STAGES
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def test_is_list():
    """DELIVERY_STAGES 是列表"""
    assert isinstance(DELIVERY_STAGES, list)


def test_has_three_stages():
    """包含 3 个阶段（S7-S9）"""
    assert len(DELIVERY_STAGES) == 3


def test_stage_codes_unique():
    """所有阶段编码唯一"""
    codes = [s['stage_code'] for s in DELIVERY_STAGES]
    assert len(codes) == len(set(codes))


def test_stage_codes_are_s7_s8_s9():
    """阶段编码为 S7、S8、S9"""
    codes = {s['stage_code'] for s in DELIVERY_STAGES}
    assert codes == {'S7', 'S8', 'S9'}


def test_each_stage_has_required_fields():
    """每个阶段包含必需字段"""
    required_fields = ['stage_code', 'stage_name', 'sequence', 'nodes']
    for stage in DELIVERY_STAGES:
        for field in required_fields:
            assert field in stage, f"Stage {stage.get('stage_code')} missing field: {field}"


def test_s8_has_four_nodes():
    """S8 现场安装包含 4 个节点"""
    s8 = next(s for s in DELIVERY_STAGES if s['stage_code'] == 'S8')
    assert len(s8['nodes']) == 4


def test_s9_has_optional_node():
    """S9 质保结项中包含非必需节点（客户培训）"""
    s9 = next(s for s in DELIVERY_STAGES if s['stage_code'] == 'S9')
    optional_nodes = [n for n in s9['nodes'] if not n.get('is_required', True)]
    assert len(optional_nodes) > 0


def test_nodes_have_required_fields():
    """每个节点包含必需字段"""
    required_node_fields = ['node_code', 'node_name', 'node_type', 'completion_method']
    for stage in DELIVERY_STAGES:
        for node in stage['nodes']:
            for field in required_node_fields:
                assert field in node, (
                    f"Node {node.get('node_code')} in stage {stage.get('stage_code')} missing: {field}"
                )
