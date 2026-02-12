# -*- coding: utf-8 -*-
"""模板导入导出 单元测试"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.stage_template.import_export import ImportExportMixin


def _make_mixin():
    m = ImportExportMixin()
    m.db = MagicMock()
    m.get_template = MagicMock()
    m.create_template = MagicMock()
    m.add_stage = MagicMock()
    m.add_node = MagicMock()
    m._get_dependency_codes = MagicMock(return_value=[])
    return m


class TestExportTemplate:
    def test_not_found(self):
        m = _make_mixin()
        m.get_template.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            m.export_template(999)

    def test_basic_export(self):
        m = _make_mixin()
        template = MagicMock()
        template.template_code = "T001"
        template.template_name = "模板1"
        template.description = "描述"
        template.project_type = "CUSTOM"
        template.stages = []
        m.get_template.return_value = template

        result = m.export_template(1)
        assert result["template_code"] == "T001"
        assert result["stages"] == []

    def test_export_with_stages_and_nodes(self):
        m = _make_mixin()
        node = MagicMock()
        node.node_code = "N01"
        node.node_name = "节点1"
        node.node_type = "TASK"
        node.sequence = 0
        node.estimated_days = 3
        node.completion_method = "MANUAL"
        node.is_required = True
        node.required_attachments = False
        node.approval_role_ids = None
        node.auto_condition = None
        node.description = "desc"
        node.owner_role_code = "PM"
        node.participant_role_codes = []
        node.deliverables = []

        stage = MagicMock()
        stage.stage_code = "S01"
        stage.stage_name = "阶段1"
        stage.sequence = 0
        stage.estimated_days = 10
        stage.description = "desc"
        stage.is_required = True
        stage.nodes = [node]

        template = MagicMock()
        template.template_code = "T001"
        template.template_name = "模板1"
        template.description = "描述"
        template.project_type = "CUSTOM"
        template.stages = [stage]
        m.get_template.return_value = template

        result = m.export_template(1)
        assert len(result["stages"]) == 1
        assert len(result["stages"][0]["nodes"]) == 1


class TestImportTemplate:
    def test_basic_import(self):
        m = _make_mixin()
        template = MagicMock()
        template.id = 1
        m.create_template.return_value = template
        stage = MagicMock()
        stage.id = 10
        m.add_stage.return_value = stage
        node = MagicMock()
        node.id = 100
        m.add_node.return_value = node

        data = {
            "template_code": "T001",
            "template_name": "模板1",
            "stages": [{
                "stage_code": "S01",
                "stage_name": "阶段1",
                "nodes": [{
                    "node_code": "N01",
                    "node_name": "节点1",
                }]
            }]
        }

        result = m.import_template(data, created_by=1)
        m.create_template.assert_called_once()
        m.add_stage.assert_called_once()
        m.add_node.assert_called_once()

    def test_import_with_dependencies(self):
        m = _make_mixin()
        template = MagicMock()
        template.id = 1
        m.create_template.return_value = template
        stage = MagicMock()
        stage.id = 10
        m.add_stage.return_value = stage
        node1 = MagicMock()
        node1.id = 100
        node2 = MagicMock()
        node2.id = 101
        m.add_node.side_effect = [node1, node2]

        data = {
            "template_code": "T001",
            "template_name": "模板1",
            "stages": [{
                "stage_code": "S01",
                "stage_name": "阶段1",
                "nodes": [
                    {"node_code": "N01", "node_name": "节点1"},
                    {"node_code": "N02", "node_name": "节点2", "dependency_node_codes": ["N01"]},
                ]
            }]
        }

        m.import_template(data)
        # Should update dependency
        m.db.query.return_value.filter.return_value.update.assert_called()
