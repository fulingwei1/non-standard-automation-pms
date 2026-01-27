# -*- coding: utf-8 -*-
"""
Tests for data_sync_service
"""

import pytest
from datetime import date
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.sales import Contract


class TestDataSyncService:
    """Test suite for DataSyncService class."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    def test_init_service(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)

        assert service.db == db_session

    def test_sync_contract_to_project_contract_not_found(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        db_session.query = Mock(
        return_value=Mock(
        filter=Mock(return_value=Mock(first=Mock(return_value=None)))
        )
        )

        result = service.sync_contract_to_project(999)

        assert result["success"] is False

    def test_sync_contract_to_project_not_linked_to_project(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.project_id = None

        mock_query = Mock()
        mock_query.filter = Mock(
        return_value=Mock(first=Mock(return_value=mock_contract))
        )
        db_session.query = Mock(return_value=mock_query)

        result = service.sync_contract_to_project(1)

        assert result["success"] is False
        assert "未关联项目" in result["message"]

    def test_sync_contract_to_project_project_not_found(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.project_id = 100

        def mock_query_side_effect(model):
            if model == Contract:
                return Mock(
                filter=Mock(
                return_value=Mock(first=Mock(return_value=mock_contract))
                )
                )
        else:
            return Mock(
            filter=Mock(return_value=Mock(first=Mock(return_value=None)))
            )

            db_session.query = Mock(side_effect=mock_query_side_effect)

            result = service.sync_contract_to_project(1)

            assert result["success"] is False
            assert "项目不存在" in result["message"]

    def test_sync_contract_to_project_sync_contract_amount(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.project_id = 100
        mock_contract.contract_amount = 150000.0

        mock_project = Mock(spec=Project)
        mock_project.id = 100
        mock_project.contract_amount = 100000.0

        def mock_query_side_effect(model):
            if model == Contract:
                return Mock(
                filter=Mock(
                return_value=Mock(first=Mock(return_value=mock_contract))
                )
                )
        else:
            return Mock(
            filter=Mock(
            return_value=Mock(first=Mock(return_value=mock_project))
            )
            )

            db_session.query = Mock(side_effect=mock_query_side_effect)

            result = service.sync_contract_to_project(1)

            assert result["success"] is True
            assert "已同步字段：contract_amount" in result["message"]
            assert mock_project.contract_amount == 150000.0

    def test_sync_contract_to_project_sync_contract_date(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.project_id = 100
        mock_contract.contract_amount = None
        mock_contract.signed_date = date(2025, 6, 15)

        mock_project = Mock(spec=Project)
        mock_project.id = 100
        mock_project.contract_amount = 100000.0
        mock_project.contract_date = date(2025, 1, 1)

        def mock_query_side_effect(model):
            if model == Contract:
                return Mock(
                filter=Mock(
                return_value=Mock(first=Mock(return_value=mock_contract))
                )
                )
        else:
            return Mock(
            filter=Mock(
            return_value=Mock(first=Mock(return_value=mock_project))
            )
            )

            db_session.query = Mock(side_effect=mock_query_side_effect)

            result = service.sync_contract_to_project(1)

            assert result["success"] is True
            assert "已同步字段：contract_date" in result["message"]
            assert mock_project.contract_date == date(2025, 6, 15)

    def test_sync_contract_to_project_no_changes(self, db_session):
        from app.services.data_sync_service import DataSyncService

        service = DataSyncService(db_session)
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 1
        mock_contract.project_id = 100
        mock_contract.contract_amount = 100000.0
        mock_contract.signed_date = date(2025, 6, 15)
        mock_contract.delivery_deadline = date(2025, 12, 31)

        mock_project = Mock(spec=Project)
        mock_project.id = 100
        mock_project.contract_amount = 100000.0
        mock_project.contract_date = date(2025, 6, 15)
        mock_project.planned_end_date = date(2025, 12, 31)

        def mock_query_side_effect(model):
            if model == Contract:
                return Mock(
                filter=Mock(
                return_value=Mock(first=Mock(return_value=mock_contract))
                )
                )
        else:
            return Mock(
            filter=Mock(
            return_value=Mock(first=Mock(return_value=mock_project))
            )
            )

            db_session.query = Mock(side_effect=mock_query_side_effect)

            result = service.sync_contract_to_project(1)

            assert result["success"] is True
            assert "没有需要同步的字段" in result.get("message", "")
