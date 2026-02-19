# -*- coding: utf-8 -*-
"""
第四十五批覆盖：stage_template/stage_management.py
"""

import pytest
from unittest.mock import MagicMock

pytest.importorskip("app.services.stage_template.stage_management")

from app.services.stage_template.stage_management import StageManagementMixin


class ConcreteStageManagement(StageManagementMixin):
    def __init__(self, db):
        self.db = db


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def manager(mock_db):
    return ConcreteStageManagement(mock_db)


class TestAddStage:
    def test_template_not_found_raises(self, manager, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="模板.*不存在"):
            manager.add_stage(999, "S1", "阶段一")

    def test_duplicate_stage_code_raises(self, manager, mock_db):
        template = MagicMock(id=1)
        existing = MagicMock(id=10)
        mock_db.query.return_value.filter.return_value.first.side_effect = [template, existing]
        with pytest.raises(ValueError, match="阶段编码.*已存在"):
            manager.add_stage(1, "S1", "阶段一")

    def test_add_stage_success(self, manager, mock_db):
        template = MagicMock(id=1)
        mock_db.query.return_value.filter.return_value.first.side_effect = [template, None]

        result = manager.add_stage(1, "S1", "阶段一", sequence=1, estimated_days=5)
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called()

    def test_add_stage_with_description(self, manager, mock_db):
        template = MagicMock(id=1)
        mock_db.query.return_value.filter.return_value.first.side_effect = [template, None]

        manager.add_stage(1, "S2", "阶段二", description="描述内容", is_required=False)
        mock_db.add.assert_called_once()


class TestUpdateStage:
    def test_update_stage_not_found_returns_none(self, manager, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = manager.update_stage(999, stage_name="新名称")
        assert result is None

    def test_update_stage_attributes(self, manager, mock_db):
        stage = MagicMock()
        stage.id = 1
        stage.stage_name = "旧名称"
        mock_db.query.return_value.filter.return_value.first.return_value = stage

        result = manager.update_stage(1, stage_name="新名称")
        assert stage.stage_name == "新名称"
        mock_db.flush.assert_called()

    def test_update_cannot_change_id(self, manager, mock_db):
        stage = MagicMock()
        stage.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = stage

        manager.update_stage(1, id=999)
        # id should not have changed since it's protected
        assert stage.id == 1


class TestDeleteStage:
    def test_delete_not_found_returns_false(self, manager, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = manager.delete_stage(999)
        assert result is False

    def test_delete_success_returns_true(self, manager, mock_db):
        stage = MagicMock(id=1)
        mock_db.query.return_value.filter.return_value.first.return_value = stage
        result = manager.delete_stage(1)
        assert result is True
        mock_db.delete.assert_called_once_with(stage)


class TestReorderStages:
    def test_reorder_updates_sequence(self, manager, mock_db):
        mock_db.query.return_value.filter.return_value.update.return_value = 1
        result = manager.reorder_stages(1, [3, 1, 2])
        assert result is True
        assert mock_db.query.return_value.filter.return_value.update.call_count == 3

    def test_reorder_empty_list(self, manager, mock_db):
        result = manager.reorder_stages(1, [])
        assert result is True
