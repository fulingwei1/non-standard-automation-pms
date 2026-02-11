# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

from app.services.status_handlers.material_handler import MaterialStatusHandler


class TestMaterialStatusHandler:
    def setup_method(self):
        self.db = MagicMock()
        self.handler = MaterialStatusHandler(self.db)

    def test_handle_bom_published_no_project(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        assert self.handler.handle_bom_published(1) is False

    def test_handle_bom_published_wrong_stage(self):
        project = MagicMock(stage="S3")
        self.db.query.return_value.filter.return_value.first.return_value = project
        assert self.handler.handle_bom_published(1) is False

    def test_handle_bom_published_success(self):
        project = MagicMock(stage="S4", status="ST10")
        self.db.query.return_value.filter.return_value.first.return_value = project
        result = self.handler.handle_bom_published(1)
        assert result is True
        assert project.stage == "S5"
        assert project.status == "ST12"
        self.db.commit.assert_called()

    def test_handle_material_shortage_no_project(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        assert self.handler.handle_material_shortage(1) is False

    def test_handle_material_shortage_not_critical(self):
        project = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = project
        assert self.handler.handle_material_shortage(1, is_critical=False) is False

    def test_handle_material_shortage_success(self):
        project = MagicMock(stage="S5", status="ST12", health="H1")
        self.db.query.return_value.filter.return_value.first.return_value = project
        result = self.handler.handle_material_shortage(1, is_critical=True)
        assert result is True
        assert project.status == "ST14"
        assert project.health == "H3"

    def test_handle_material_ready_no_project(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        assert self.handler.handle_material_ready(1) is False

    def test_handle_material_ready_wrong_stage(self):
        project = MagicMock(stage="S4")
        self.db.query.return_value.filter.return_value.first.return_value = project
        assert self.handler.handle_material_ready(1) is False

    def test_handle_material_ready_success(self):
        project = MagicMock(stage="S5", status="ST14", health="H3")
        self.db.query.return_value.filter.return_value.first.return_value = project
        result = self.handler.handle_material_ready(1)
        assert result is True
        assert project.status == "ST16"
        assert project.health == "H1"

    def test_log_status_change_with_callback(self):
        callback = MagicMock()
        self.handler._log_status_change(1, old_stage="S4", new_stage="S5", log_status_change=callback)
        callback.assert_called_once()

    def test_log_status_change_creates_log(self):
        self.handler._log_status_change(1, old_stage="S4", new_stage="S5")
        self.db.add.assert_called_once()
