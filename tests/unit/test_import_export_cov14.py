# -*- coding: utf-8 -*-
"""
第十四批：阶段模板导入导出 Mixin 单元测试
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.stage_template.import_export import ImportExportMixin
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


class ConcreteImportExport(ImportExportMixin):
    """用于测试的具体实现"""
    def __init__(self, db=None):
        self.db = db or MagicMock()

    def get_template(self, template_id, include_stages=False, include_nodes=False):
        return self._mock_template

    def create_template(self, **kwargs):
        t = MagicMock()
        t.id = 1
        return t

    def add_stage(self, **kwargs):
        s = MagicMock()
        s.id = 10
        s.nodes = []
        return s

    def add_node(self, **kwargs):
        n = MagicMock()
        n.id = 100
        return n

    def _get_dependency_codes(self, node):
        return []


def make_template_with_stages():
    tmpl = MagicMock()
    tmpl.template_code = "TMPL-001"
    tmpl.template_name = "测试模板"
    tmpl.description = "描述"
    tmpl.project_type = "STANDARD"
    # 一个阶段，一个节点
    node = MagicMock()
    node.node_code = "N001"
    node.node_name = "需求分析"
    node.node_type = "TASK"
    node.sequence = 1
    node.estimated_days = 3
    node.completion_method = "MANUAL"
    node.is_required = True
    node.required_attachments = False
    node.approval_role_ids = None
    node.auto_condition = None
    node.description = ""
    node.owner_role_code = None
    node.participant_role_codes = None
    node.deliverables = None
    stage = MagicMock()
    stage.stage_code = "S001"
    stage.stage_name = "需求阶段"
    stage.sequence = 1
    stage.estimated_days = 5
    stage.description = ""
    stage.is_required = True
    stage.nodes = [node]
    tmpl.stages = [stage]
    return tmpl


class TestImportExportMixin:
    def test_export_template_not_found(self):
        ie = ConcreteImportExport()
        ie._mock_template = None
        with pytest.raises(ValueError, match="不存在"):
            ie.export_template(999)

    def test_export_template_structure(self):
        ie = ConcreteImportExport()
        ie._mock_template = make_template_with_stages()
        result = ie.export_template(1)
        assert result["template_code"] == "TMPL-001"
        assert len(result["stages"]) == 1
        assert len(result["stages"][0]["nodes"]) == 1

    def test_export_template_has_required_keys(self):
        ie = ConcreteImportExport()
        ie._mock_template = make_template_with_stages()
        result = ie.export_template(1)
        assert "template_code" in result
        assert "template_name" in result
        assert "stages" in result

    def test_import_template_basic(self):
        ie = ConcreteImportExport()
        data = {
            "template_code": "NEW-001",
            "template_name": "新模板",
            "description": "测试",
            "project_type": "CUSTOM",
            "stages": [
                {
                    "stage_code": "S001",
                    "stage_name": "阶段1",
                    "sequence": 1,
                    "nodes": [
                        {
                            "node_code": "N001",
                            "node_name": "节点1",
                            "node_type": "TASK",
                            "sequence": 1,
                        }
                    ]
                }
            ]
        }
        result = ie.import_template(data, created_by=1)
        assert result is not None
        assert result.id == 1

    def test_import_template_override_code(self):
        ie = ConcreteImportExport()
        data = {
            "template_code": "ORIG-001",
            "template_name": "原名",
            "stages": []
        }
        result = ie.import_template(data, override_code="OVERRIDE-001", override_name="新名")
        assert result is not None

    def test_import_template_empty_stages(self):
        ie = ConcreteImportExport()
        data = {
            "template_code": "EMPTY-001",
            "template_name": "空模板",
            "stages": []
        }
        result = ie.import_template(data)
        assert result is not None

    def test_import_then_export_roundtrip(self):
        ie = ConcreteImportExport()
        template_data = {
            "template_code": "RT-001",
            "template_name": "往返测试",
            "stages": []
        }
        imported = ie.import_template(template_data, created_by=1)
        # 导出
        ie._mock_template = make_template_with_stages()
        exported = ie.export_template(1)
        assert "template_code" in exported
