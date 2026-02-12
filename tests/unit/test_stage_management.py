# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from app.services.stage_template.stage_management import StageManagementMixin


class FakeService(StageManagementMixin):
    def __init__(self, db):
        self.db = db


class TestStageManagementMixin:
    def setup_method(self):
        self.db = MagicMock()
        self.service = FakeService(self.db)

    def test_add_stage_template_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            self.service.add_stage(template_id=1, stage_code="S1", stage_name="阶段1")

    def test_add_stage_duplicate_code(self):
        template_mock = MagicMock()
        existing_mock = MagicMock()
        self.db.query.return_value.filter.return_value.first.side_effect = [template_mock, existing_mock]
        with pytest.raises(ValueError, match="已存在"):
            self.service.add_stage(template_id=1, stage_code="S1", stage_name="阶段1")

    def test_add_stage_success(self):
        template_mock = MagicMock()
        self.db.query.return_value.filter.return_value.first.side_effect = [template_mock, None]
        result = self.service.add_stage(template_id=1, stage_code="S1", stage_name="阶段1", sequence=0)
        self.db.add.assert_called_once()
        self.db.flush.assert_called_once()

    def test_update_stage_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.service.update_stage(stage_id=1, stage_name="new")
        assert result is None

    def test_update_stage_success(self):
        stage = MagicMock()
        stage.id = 1
        stage.template_id = 1
        stage.created_at = "2024-01-01"
        self.db.query.return_value.filter.return_value.first.return_value = stage
        result = self.service.update_stage(stage_id=1, stage_name="new")
        assert result == stage

    def test_delete_stage_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        assert self.service.delete_stage(999) is False

    def test_delete_stage_success(self):
        stage = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = stage
        assert self.service.delete_stage(1) is True
        self.db.delete.assert_called_once_with(stage)

    def test_reorder_stages(self):
        result = self.service.reorder_stages(template_id=1, stage_ids=[3, 1, 2])
        self.db.flush.assert_called_once()
        assert result is True
