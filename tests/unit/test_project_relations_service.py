# -*- coding: utf-8 -*-
"""
项目关联关系服务单元测试
覆盖物料转移关联、统计、发现函数等
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.project_relations_service import (
    calculate_relation_statistics,
    discover_same_customer_relations,
    discover_same_pm_relations,
    discover_time_overlap_relations,
)


def make_project(id=1, project_code="P001", project_name="项目A",
                 customer_id=None, pm_id=None, pm_name=None, customer_name=None,
                 planned_start_date=None, planned_end_date=None, is_active=True):
    p = MagicMock()
    p.id = id
    p.project_code = project_code
    p.project_name = project_name
    p.customer_id = customer_id
    p.customer_name = customer_name
    p.pm_id = pm_id
    p.pm_name = pm_name
    p.planned_start_date = planned_start_date
    p.planned_end_date = planned_end_date
    p.is_active = is_active
    return p


class TestCalculateRelationStatistics:
    def test_empty_relations(self):
        stats = calculate_relation_statistics([])
        assert stats["total_relations"] == 0
        assert stats["by_type"] == {}
        assert stats["by_strength"] == {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

    def test_counts_by_type(self):
        relations = [
            {"type": "MATERIAL_TRANSFER_OUT", "strength": "MEDIUM"},
            {"type": "MATERIAL_TRANSFER_OUT", "strength": "HIGH"},
            {"type": "SHARED_CUSTOMER", "strength": "LOW"},
        ]
        stats = calculate_relation_statistics(relations)
        assert stats["total_relations"] == 3
        assert stats["by_type"]["MATERIAL_TRANSFER_OUT"] == 2
        assert stats["by_type"]["SHARED_CUSTOMER"] == 1

    def test_counts_by_strength(self):
        relations = [
            {"type": "T1", "strength": "HIGH"},
            {"type": "T2", "strength": "HIGH"},
            {"type": "T3", "strength": "LOW"},
        ]
        stats = calculate_relation_statistics(relations)
        assert stats["by_strength"]["HIGH"] == 2
        assert stats["by_strength"]["LOW"] == 1
        assert stats["by_strength"]["MEDIUM"] == 0


class TestDiscoverSameCustomerRelations:
    def test_no_customer_id_returns_empty(self):
        db = MagicMock()
        project = make_project(customer_id=None)
        result = discover_same_customer_relations(db, project, project_id=1)
        assert result == []

    def test_returns_customer_relations(self):
        related = make_project(id=2, project_code="P002", project_name="项目B")
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [related]
        project = make_project(customer_id=10, customer_name="Acme")
        result = discover_same_customer_relations(db, project, project_id=1)
        assert len(result) == 1
        assert result[0]["relation_type"] == "SAME_CUSTOMER"
        assert result[0]["confidence"] == 0.8
        assert result[0]["related_project_id"] == 2

    def test_excludes_self_project(self):
        """DB 过滤 Project.id != project_id 已在查询层实现，此处验证逻辑正确调用"""
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        project = make_project(customer_id=10)
        result = discover_same_customer_relations(db, project, project_id=1)
        assert result == []


class TestDiscoverSamePmRelations:
    def test_no_pm_id_returns_empty(self):
        db = MagicMock()
        project = make_project(pm_id=None)
        result = discover_same_pm_relations(db, project, project_id=1)
        assert result == []

    def test_returns_pm_relations(self):
        related = make_project(id=3, project_code="P003", project_name="项目C")
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [related]
        project = make_project(pm_id=5, pm_name="张三")
        result = discover_same_pm_relations(db, project, project_id=1)
        assert len(result) == 1
        assert result[0]["relation_type"] == "SAME_PM"
        assert result[0]["confidence"] == 0.7


class TestDiscoverTimeOverlapRelations:
    def test_no_dates_returns_empty(self):
        db = MagicMock()
        project = make_project(planned_start_date=None, planned_end_date=None)
        result = discover_time_overlap_relations(db, project, project_id=1)
        assert result == []

    def test_returns_overlap_relations(self):
        from datetime import date
        related = make_project(id=4, project_code="P004", project_name="项目D")
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [related]
        project = make_project(
            planned_start_date=date(2025, 1, 1),
            planned_end_date=date(2025, 6, 30),
        )
        result = discover_time_overlap_relations(db, project, project_id=1)
        assert len(result) == 1
        assert result[0]["relation_type"] == "TIME_OVERLAP"
        assert result[0]["confidence"] == 0.6
