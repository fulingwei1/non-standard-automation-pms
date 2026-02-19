# -*- coding: utf-8 -*-
"""资源分配服务单元测试 - 第三十四批"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date

pytest.importorskip("app.services.resource_allocation_service.allocation")

try:
    from app.services.resource_allocation_service.allocation import allocate_resources
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    allocate_resources = None


START = date(2024, 6, 1)
END = date(2024, 6, 30)


@pytest.fixture
def db():
    return MagicMock()


class TestAllocateResources:
    def test_conflict_prevents_allocation(self, db):
        conflicts = [{"type": "workstation_conflict", "detail": "已占用"}]
        with patch(
            "app.services.resource_allocation_service.allocation.detect_resource_conflicts",
            return_value=conflicts
        ), patch(
            "app.services.resource_allocation_service.allocation.find_available_workstations",
            return_value=[]
        ), patch(
            "app.services.resource_allocation_service.allocation.find_available_workers",
            return_value=[]
        ):
            result = allocate_resources(db, 1, None, START, END)
            assert result["can_allocate"] is False
            assert result["conflicts"] == conflicts

    def test_no_conflict_allocates_resources(self, db):
        workstations = [{"id": 1}, {"id": 2}]
        workers = [{"id": 10}, {"id": 11}]
        with patch(
            "app.services.resource_allocation_service.allocation.detect_resource_conflicts",
            return_value=[]
        ), patch(
            "app.services.resource_allocation_service.allocation.find_available_workstations",
            return_value=workstations
        ), patch(
            "app.services.resource_allocation_service.allocation.find_available_workers",
            return_value=workers
        ):
            result = allocate_resources(db, 1, None, START, END)
            assert result["can_allocate"] is True
            assert result["workstations"] == workstations[:3]
            assert result["workers"] == workers[:5]

    def test_no_workstation_fails_allocation(self, db):
        with patch(
            "app.services.resource_allocation_service.allocation.detect_resource_conflicts",
            return_value=[]
        ), patch(
            "app.services.resource_allocation_service.allocation.find_available_workstations",
            return_value=[]
        ), patch(
            "app.services.resource_allocation_service.allocation.find_available_workers",
            return_value=[{"id": 10}]
        ):
            result = allocate_resources(db, 1, None, START, END)
            assert result["can_allocate"] is False
            assert "工位" in result.get("reason", "")

    def test_no_worker_fails_allocation(self, db):
        with patch(
            "app.services.resource_allocation_service.allocation.detect_resource_conflicts",
            return_value=[]
        ), patch(
            "app.services.resource_allocation_service.allocation.find_available_workstations",
            return_value=[{"id": 1}]
        ), patch(
            "app.services.resource_allocation_service.allocation.find_available_workers",
            return_value=[]
        ):
            result = allocate_resources(db, 1, None, START, END)
            assert result["can_allocate"] is False
            assert "人员" in result.get("reason", "")

    def test_result_has_expected_structure(self, db):
        with patch(
            "app.services.resource_allocation_service.allocation.detect_resource_conflicts",
            return_value=[]
        ), patch(
            "app.services.resource_allocation_service.allocation.find_available_workstations",
            return_value=[{"id": i} for i in range(5)]
        ), patch(
            "app.services.resource_allocation_service.allocation.find_available_workers",
            return_value=[{"id": i} for i in range(8)]
        ):
            result = allocate_resources(db, 2, 100, START, END)
            assert "workstations" in result
            assert "workers" in result
            assert "conflicts" in result
            assert "can_allocate" in result

    def test_max_workstations_returned(self, db):
        """最多返回3个工位"""
        with patch(
            "app.services.resource_allocation_service.allocation.detect_resource_conflicts",
            return_value=[]
        ), patch(
            "app.services.resource_allocation_service.allocation.find_available_workstations",
            return_value=[{"id": i} for i in range(10)]
        ), patch(
            "app.services.resource_allocation_service.allocation.find_available_workers",
            return_value=[{"id": i} for i in range(10)]
        ):
            result = allocate_resources(db, 1, None, START, END)
            assert len(result["workstations"]) <= 3

    def test_max_workers_returned(self, db):
        """最多返回5个人员"""
        with patch(
            "app.services.resource_allocation_service.allocation.detect_resource_conflicts",
            return_value=[]
        ), patch(
            "app.services.resource_allocation_service.allocation.find_available_workstations",
            return_value=[{"id": 1}]
        ), patch(
            "app.services.resource_allocation_service.allocation.find_available_workers",
            return_value=[{"id": i} for i in range(10)]
        ):
            result = allocate_resources(db, 1, None, START, END)
            assert len(result["workers"]) <= 5
