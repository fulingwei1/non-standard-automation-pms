# -*- coding: utf-8 -*-
"""第二十四批 - presale_ai_export_service 单元测试"""

import os
import pytest
from unittest.mock import MagicMock, patch, mock_open

pytest.importorskip("app.services.presale_ai_export_service")

from app.services.presale_ai_export_service import PresaleAIExportService


@pytest.fixture
def export_service(tmp_path):
    db = MagicMock()
    export_dir = str(tmp_path / "exports")
    os.makedirs(export_dir, exist_ok=True)
    with patch("app.services.presale_ai_export_service.os.makedirs"):
        svc = PresaleAIExportService(db=db)
        svc.export_dir = export_dir
    return svc, db


class TestExportToPdf:
    def test_raises_when_solution_not_found(self, export_service):
        svc, db = export_service
        db.query.return_value.filter_by.return_value.first.return_value = None
        with pytest.raises(ValueError, match="not found"):
            svc.export_to_pdf(solution_id=999)

    def test_creates_file_on_success(self, export_service):
        svc, db = export_service
        solution = MagicMock()
        solution.solution_description = "测试方案描述"
        solution.architecture_diagram = None
        solution.bom_list = None
        db.query.return_value.filter_by.return_value.first.return_value = solution

        filepath = svc.export_to_pdf(solution_id=1)
        assert os.path.exists(filepath)

    def test_file_contains_solution_id(self, export_service):
        svc, db = export_service
        solution = MagicMock()
        solution.solution_description = "项目描述内容"
        solution.architecture_diagram = None
        solution.bom_list = None
        db.query.return_value.filter_by.return_value.first.return_value = solution

        filepath = svc.export_to_pdf(solution_id=42)
        with open(filepath, "r") as f:
            content = f.read()
        assert "42" in content

    def test_includes_architecture_when_flag_true(self, export_service):
        svc, db = export_service
        solution = MagicMock()
        solution.solution_description = "描述"
        solution.architecture_diagram = "系统架构图内容"
        solution.bom_list = None
        db.query.return_value.filter_by.return_value.first.return_value = solution

        filepath = svc.export_to_pdf(solution_id=5, include_diagrams=True)
        with open(filepath, "r") as f:
            content = f.read()
        assert "系统架构图" in content

    def test_includes_bom_when_flag_true(self, export_service):
        svc, db = export_service
        solution = MagicMock()
        solution.solution_description = "描述"
        solution.architecture_diagram = None
        solution.bom_list = [{"item": "气缸", "qty": 2}]
        db.query.return_value.filter_by.return_value.first.return_value = solution

        filepath = svc.export_to_pdf(solution_id=6, include_bom=True)
        with open(filepath, "r") as f:
            content = f.read()
        assert "BOM" in content

    def test_export_to_word_returns_none(self, export_service):
        svc, db = export_service
        # export_to_word is TODO/pass, should return None
        result = svc.export_to_word(solution_id=1)
        assert result is None

    def test_export_to_excel_returns_none(self, export_service):
        svc, db = export_service
        result = svc.export_to_excel(solution_id=1)
        assert result is None
