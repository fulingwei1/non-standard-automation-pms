# -*- coding: utf-8 -*-
"""
Unit tests for SalesTeamService and SalesRegionService (第三十批)
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.sales_team_service import SalesTeamService, SalesRegionService


@pytest.fixture
def mock_db():
    return MagicMock()


# ---------------------------------------------------------------------------
# SalesTeamService
# ---------------------------------------------------------------------------

class TestSalesTeamServiceCreate:
    @patch("app.services.sales_team_service.save_obj")
    def test_create_team_success(self, mock_save, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        team_data = MagicMock()
        team_data.team_code = "TEAM001"
        team_data.model_dump.return_value = {"team_code": "TEAM001", "team_name": "销售一组"}

        result = SalesTeamService.create_team(mock_db, team_data, created_by=1)
        mock_save.assert_called_once()

    def test_create_team_duplicate_code_raises(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
        team_data = MagicMock()
        team_data.team_code = "TEAM001"

        with pytest.raises(HTTPException) as exc:
            SalesTeamService.create_team(mock_db, team_data, created_by=1)
        assert exc.value.status_code == 400


class TestSalesTeamServiceGet:
    def test_get_team_returns_team(self, mock_db):
        team = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = team

        result = SalesTeamService.get_team(mock_db, team_id=1)
        assert result is team

    def test_get_team_returns_none_when_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = SalesTeamService.get_team(mock_db, team_id=999)
        assert result is None

    def test_get_teams_with_filters(self, mock_db):
        teams = [MagicMock(), MagicMock()]
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = teams

        result = SalesTeamService.get_teams(mock_db, team_type="SALES", is_active=True)
        assert result is not None


class TestSalesTeamServiceUpdate:
    def test_update_team_success(self, mock_db):
        team = MagicMock()
        with patch("app.services.sales_team_service.get_or_404", return_value=team):
            team_data = MagicMock()
            team_data.model_dump.return_value = {"team_name": "新名称"}

            result = SalesTeamService.update_team(mock_db, team_id=1, team_data=team_data)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(team)


class TestSalesTeamServiceDelete:
    def test_delete_team_success(self, mock_db):
        team = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        with patch("app.services.sales_team_service.get_or_404", return_value=team):
            with patch("app.services.sales_team_service.delete_obj") as mock_del:
                result = SalesTeamService.delete_team(mock_db, team_id=1)
                assert result is True
                mock_del.assert_called_once()

    def test_delete_team_with_sub_teams_raises(self, mock_db):
        team = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 2

        with patch("app.services.sales_team_service.get_or_404", return_value=team):
            with pytest.raises(HTTPException) as exc:
                SalesTeamService.delete_team(mock_db, team_id=1)
            assert exc.value.status_code == 400


class TestSalesTeamServiceMembers:
    @patch("app.services.sales_team_service.save_obj")
    def test_add_member_success(self, mock_save, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        member_data = MagicMock()
        member_data.team_id = 1
        member_data.user_id = 10
        member_data.model_dump.return_value = {"team_id": 1, "user_id": 10}

        result = SalesTeamService.add_member(mock_db, member_data)
        mock_save.assert_called_once()

    def test_add_member_duplicate_raises(self, mock_db):
        existing = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing
        member_data = MagicMock()
        member_data.team_id = 1
        member_data.user_id = 10

        with pytest.raises(HTTPException) as exc:
            SalesTeamService.add_member(mock_db, member_data)
        assert exc.value.status_code == 400

    def test_remove_member_success(self, mock_db):
        member = MagicMock()
        member.is_active = True
        mock_db.query.return_value.filter.return_value.first.return_value = member

        result = SalesTeamService.remove_member(mock_db, team_id=1, user_id=10)
        assert result is True
        assert member.is_active is False

    def test_remove_member_not_found_raises(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc:
            SalesTeamService.remove_member(mock_db, team_id=1, user_id=999)
        assert exc.value.status_code == 404


class TestSalesTeamTree:
    def test_get_team_tree_builds_hierarchy(self, mock_db):
        parent = MagicMock()
        parent.id = 1
        parent.team_code = "T01"
        parent.team_name = "父团队"
        parent.team_type = "SALES"
        parent.leader_id = 1
        parent.parent_team_id = None

        child = MagicMock()
        child.id = 2
        child.team_code = "T02"
        child.team_name = "子团队"
        child.team_type = "SALES"
        child.leader_id = 2
        child.parent_team_id = 1

        mock_db.query.return_value.filter.return_value.all.return_value = [parent, child]

        result = SalesTeamService.get_team_tree(mock_db)
        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["team_code"] == "T01"


# ---------------------------------------------------------------------------
# SalesRegionService
# ---------------------------------------------------------------------------

class TestSalesRegionService:
    @patch("app.services.sales_team_service.save_obj")
    def test_create_region_success(self, mock_save, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        region_data = MagicMock()
        region_data.region_code = "R001"
        region_data.model_dump.return_value = {"region_code": "R001", "region_name": "华东"}

        result = SalesRegionService.create_region(mock_db, region_data, created_by=1)
        mock_save.assert_called_once()

    def test_create_region_duplicate_raises(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
        region_data = MagicMock()
        region_data.region_code = "R001"

        with pytest.raises(HTTPException) as exc:
            SalesRegionService.create_region(mock_db, region_data, created_by=1)
        assert exc.value.status_code == 400

    def test_assign_team_updates_region(self, mock_db):
        region = MagicMock()
        team = MagicMock()

        with patch("app.services.sales_team_service.get_or_404") as mock_404:
            mock_404.side_effect = [region, team]
            result = SalesRegionService.assign_team(mock_db, region_id=1, team_id=2, leader_id=5)

        assert region.team_id == 2
        assert region.leader_id == 5
        mock_db.commit.assert_called_once()
