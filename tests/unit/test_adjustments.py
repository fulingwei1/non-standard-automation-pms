# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock
from app.services.stage_instance.adjustments import AdjustmentsMixin


class FakeService(AdjustmentsMixin):
    def __init__(self, db):
        self.db = db


class TestAdjustmentsMixin:
    def setup_method(self):
        self.db = MagicMock()
        self.service = FakeService(self.db)

    def test_add_custom_node_stage_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            self.service.add_custom_node(stage_instance_id=999, node_code="N1", node_name="节点1")

    def test_add_custom_node_at_end(self):
        stage = MagicMock()
        stage.project_id = 1
        self.db.query.return_value.filter.return_value.first.return_value = stage
        self.db.query.return_value.filter.return_value.count.return_value = 3
        result = self.service.add_custom_node(
            stage_instance_id=1, node_code="N1", node_name="节点1"
        )
        self.db.add.assert_called_once()
        self.db.flush.assert_called_once()

    def test_update_node_planned_date_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            from datetime import date
            self.service.update_node_planned_date(999, date(2024, 6, 1))

    def test_update_node_planned_date_success(self):
        from datetime import date
        node = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = node
        result = self.service.update_node_planned_date(1, date(2024, 6, 1))
        assert result == node
        assert node.planned_date == date(2024, 6, 1)
