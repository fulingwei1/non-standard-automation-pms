# -*- coding: utf-8 -*-
"""项目关联关系服务测试"""
from unittest.mock import MagicMock

import pytest

from app.services.project_relations_service import (
    get_material_transfer_relations, get_shared_customer_relations,
    calculate_relation_statistics, discover_same_customer_relations,
    discover_same_pm_relations, discover_time_overlap_relations,
    discover_material_transfer_relations, deduplicate_and_filter_relations,
    calculate_discovery_relation_statistics,
)


@pytest.fixture
def db():
    return MagicMock()


class TestGetMaterialTransferRelations:
    def test_wrong_type(self, db):
        result = get_material_transfer_relations(db, 1, 'SHARED_RESOURCE')
        assert result == []

    def test_no_transfers(self, db):
        db.query.return_value.filter.return_value.all.return_value = []
        result = get_material_transfer_relations(db, 1, None)
        assert result == []

    def test_outbound_transfer(self, db):
        transfer = MagicMock(
            to_project_id=2, transfer_no='T001',
            material_code='M001', material_name='Material', transfer_qty=10
        )
        project = MagicMock(project_code='P002', project_name='Project 2')
        db.query.return_value.filter.return_value.all.side_effect = [[transfer], []]
        db.query.return_value.filter.return_value.first.return_value = project
        result = get_material_transfer_relations(db, 1, None)
        assert len(result) == 1
        assert result[0]['type'] == 'MATERIAL_TRANSFER_OUT'


class TestGetSharedCustomerRelations:
    def test_no_customer(self, db):
        project = MagicMock(customer_id=None)
        result = get_shared_customer_relations(db, project, 1, None)
        assert result == []

    def test_with_shared_customer(self, db):
        project = MagicMock(customer_id=1, customer_name='Test Customer')
        related = MagicMock(id=2, project_code='P002', project_name='P2')
        db.query.return_value.filter.return_value.all.return_value = [related]
        result = get_shared_customer_relations(db, project, 1, None)
        assert len(result) == 1


class TestCalculateRelationStatistics:
    def test_empty(self):
        result = calculate_relation_statistics([])
        assert result['total_relations'] == 0

    def test_with_relations(self):
        relations = [
            {'type': 'MATERIAL_TRANSFER_OUT', 'strength': 'MEDIUM'},
            {'type': 'SHARED_CUSTOMER', 'strength': 'LOW'},
        ]
        result = calculate_relation_statistics(relations)
        assert result['total_relations'] == 2
        assert result['by_strength']['MEDIUM'] == 1


class TestDiscoverSameCustomer:
    def test_no_customer(self, db):
        project = MagicMock(customer_id=None)
        assert discover_same_customer_relations(db, project, 1) == []

    def test_found(self, db):
        project = MagicMock(customer_id=1, customer_name='Test')
        related = MagicMock(id=2, project_code='P002', project_name='P2')
        db.query.return_value.filter.return_value.all.return_value = [related]
        result = discover_same_customer_relations(db, project, 1)
        assert len(result) == 1
        assert result[0]['relation_type'] == 'SAME_CUSTOMER'


class TestDiscoverSamePm:
    def test_no_pm(self, db):
        project = MagicMock(pm_id=None)
        assert discover_same_pm_relations(db, project, 1) == []


class TestDiscoverTimeOverlap:
    def test_no_dates(self, db):
        project = MagicMock(planned_start_date=None, planned_end_date=None)
        assert discover_time_overlap_relations(db, project, 1) == []


class TestDiscoverMaterialTransfer:
    def test_no_transfers(self, db):
        db.query.return_value.filter.return_value.all.return_value = []
        assert discover_material_transfer_relations(db, 1) == []


class TestDeduplicateAndFilter:
    def test_filter_by_confidence(self):
        relations = [
            {'related_project_id': 1, 'confidence': 0.9, 'relation_type': 'A'},
            {'related_project_id': 2, 'confidence': 0.3, 'relation_type': 'B'},
        ]
        result = deduplicate_and_filter_relations(relations, min_confidence=0.5)
        assert len(result) == 1

    def test_deduplicate(self):
        relations = [
            {'related_project_id': 1, 'confidence': 0.7, 'relation_type': 'A'},
            {'related_project_id': 1, 'confidence': 0.9, 'relation_type': 'B'},
        ]
        result = deduplicate_and_filter_relations(relations, min_confidence=0.5)
        assert len(result) == 1
        assert result[0]['confidence'] == 0.9


class TestDiscoveryStatistics:
    def test_empty(self):
        result = calculate_discovery_relation_statistics([])
        assert result['by_type'] == {}

    def test_with_data(self):
        relations = [
            {'relation_type': 'A', 'confidence': 0.9},
            {'relation_type': 'A', 'confidence': 0.6},
            {'relation_type': 'B', 'confidence': 0.3},
        ]
        result = calculate_discovery_relation_statistics(relations)
        assert result['by_type']['A'] == 2
        assert result['by_confidence_range']['high'] == 1
