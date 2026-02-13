# -*- coding: utf-8 -*-
"""资源冲突检测单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date
from app.services.resource_allocation_service.conflicts import detect_resource_conflicts


class TestDetectResourceConflicts:
    def setup_method(self):
        self.db = MagicMock()

    def test_no_machine_id(self):
        result = detect_resource_conflicts(self.db, 1, None, date(2024, 1, 1), date(2024, 3, 1))
        assert result == []

    def test_machine_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = detect_resource_conflicts(self.db, 1, 10, date(2024, 1, 1), date(2024, 3, 1))
        assert result == []

    def test_no_conflicts(self):
        machine = MagicMock()
        machine.machine_code = "MC001"
        self.db.query.return_value.filter.return_value.first.return_value = machine
        self.db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        result = detect_resource_conflicts(self.db, 1, 10, date(2024, 1, 1), date(2024, 3, 1))
        assert result == []

    def test_with_conflicts(self):
        machine = MagicMock()
        machine.machine_code = "MC001"
        self.db.query.return_value.filter.return_value.first.return_value = machine
        conflict_project = MagicMock()
        conflict_project.id = 2
        conflict_project.project_name = "冲突项目"
        conflict_project.planned_start_date = date(2024, 2, 1)
        conflict_project.planned_end_date = date(2024, 4, 1)
        self.db.query.return_value.join.return_value.filter.return_value.all.return_value = [conflict_project]
        result = detect_resource_conflicts(self.db, 1, 10, date(2024, 1, 1), date(2024, 3, 1))
        assert len(result) == 1
        assert result[0]['type'] == 'MACHINE'
        assert result[0]['severity'] == 'HIGH'
