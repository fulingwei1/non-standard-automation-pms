# -*- coding: utf-8 -*-
"""
O1组 API层单元测试 - sales/opportunity_crud.py
使用 Method A: 直接调用端点函数 + MagicMock

覆盖：
  - read_opportunities
  - create_opportunity
  - read_opportunity
  - update_opportunity
"""
import sys
from unittest.mock import MagicMock, patch

redis_mock = MagicMock()
sys.modules.setdefault("redis", redis_mock)
sys.modules.setdefault("redis.exceptions", MagicMock())

import os
os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("ENABLE_SCHEDULER", "false")

import pytest
from fastapi import HTTPException


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _make_db():
    db = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db


def _make_user():
    user = MagicMock()
    user.id = 1
    user.username = "admin"
    user.real_name = "管理员"
    user.is_superuser = True
    return user


def _make_opp(opp_id=1):
    opp = MagicMock()
    opp.id = opp_id
    opp.opp_code = f"OPP{opp_id:04d}"
    opp.opp_name = "比亚迪ADAS商机"
    opp.customer_id = 1
    opp.owner_id = 1
    opp.stage = "LEAD"
    opp.priority_score = 80
    opp.updated_by = 1
    opp.requirements = []
    opp.customer = MagicMock(customer_name="比亚迪")
    opp.owner = MagicMock(real_name="张三")
    opp.updater = MagicMock(real_name="管理员")
    opp.__table__ = MagicMock()
    opp.__table__.columns = []
    return opp


def _make_pagination():
    pag = MagicMock()
    pag.offset = 0
    pag.limit = 20
    pag.page = 1
    pag.page_size = 20
    pag.to_response = MagicMock(return_value={"items": [], "total": 0})
    return pag


# ──────────────────────────────────────────────
# Tests: read_opportunities
# ──────────────────────────────────────────────

class TestReadOpportunities:

    def test_list_opportunities_empty(self):
        """空列表请求"""
        from app.api.v1.endpoints.sales.opportunity_crud import read_opportunities

        db = _make_db()
        current_user = _make_user()
        pagination = _make_pagination()

        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        db.query.return_value = mock_query

        with patch("app.api.v1.endpoints.sales.opportunity_crud.security") as mock_sec:
            mock_sec.filter_sales_data_by_scope.return_value = mock_query
            with patch("app.api.v1.endpoints.sales.opportunity_crud.apply_keyword_filter", return_value=mock_query):

                result = read_opportunities(
                    db=db,
                    pagination=pagination,
                    keyword=None,
                    stage=None,
                    customer_id=None,
                    owner_id=None,
                    current_user=current_user,
                )

        pagination.to_response.assert_called_once()

    def test_list_opportunities_with_filters(self):
        """带过滤条件的商机列表"""
        from app.api.v1.endpoints.sales.opportunity_crud import read_opportunities

        db = _make_db()
        current_user = _make_user()
        pagination = _make_pagination()

        mock_query = MagicMock()
        mock_query.count.return_value = 1
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        db.query.return_value = mock_query

        with patch("app.api.v1.endpoints.sales.opportunity_crud.security") as mock_sec:
            mock_sec.filter_sales_data_by_scope.return_value = mock_query
            with patch("app.api.v1.endpoints.sales.opportunity_crud.apply_keyword_filter", return_value=mock_query):

                result = read_opportunities(
                    db=db,
                    pagination=pagination,
                    keyword="比亚迪",
                    stage="LEAD",
                    customer_id=1,
                    owner_id=1,
                    current_user=current_user,
                )

        assert result is not None


# ──────────────────────────────────────────────
# Tests: create_opportunity
# ──────────────────────────────────────────────

class TestCreateOpportunity:

    def test_create_opportunity_success(self):
        """正常创建商机"""
        from app.api.v1.endpoints.sales.opportunity_crud import create_opportunity

        db = _make_db()
        current_user = _make_user()

        opp_in = MagicMock()
        opp_in.requirement = None
        opp_in.model_dump.return_value = {
            "opp_name": "比亚迪ADAS商机",
            "customer_id": 1,
            "owner_id": 1,
            "opp_code": "",  # empty -> auto-generate
        }

        customer_mock = MagicMock(customer_name="比亚迪")
        opp_instance = _make_opp()
        opp_instance.__table__.columns = []

        db.query.return_value.filter.return_value.first.return_value = None  # no duplicate

        with patch("app.api.v1.endpoints.sales.opportunity_crud.generate_opportunity_code", return_value="OPP0001"), \
             patch("app.api.v1.endpoints.sales.opportunity_crud.Customer") as MockCustomer, \
             patch("app.api.v1.endpoints.sales.opportunity_crud.Opportunity") as MockOpp, \
             patch("app.api.v1.endpoints.sales.opportunity_crud.OpportunityRequirementResponse"):

            # customer lookup
            db.query.return_value.filter.return_value.first.side_effect = [
                None,           # duplicate code check
                customer_mock,  # customer lookup
                None,           # requirement lookup at end
            ]

            MockOpp.return_value = opp_instance

            result = create_opportunity(db=db, opp_in=opp_in, current_user=current_user)

        assert db.flush.called
        assert db.commit.called

    def test_create_opportunity_customer_not_found(self):
        """客户不存在时抛出404"""
        from app.api.v1.endpoints.sales.opportunity_crud import create_opportunity

        db = _make_db()
        current_user = _make_user()

        opp_in = MagicMock()
        opp_in.requirement = None
        opp_in.model_dump.return_value = {
            "opp_name": "比亚迪商机",
            "customer_id": 999,
            "owner_id": 1,
            "opp_code": "OPP9999",
        }

        # First call: code check -> None (not duplicate), then customer -> None
        db.query.return_value.filter.return_value.first.side_effect = [None, None]

        with patch("app.api.v1.endpoints.sales.opportunity_crud.generate_opportunity_code", return_value="OPP0001"):
            with pytest.raises(HTTPException) as exc_info:
                create_opportunity(db=db, opp_in=opp_in, current_user=current_user)

        assert exc_info.value.status_code == 404

    def test_create_opportunity_duplicate_code(self):
        """重复商机编码应抛出400"""
        from app.api.v1.endpoints.sales.opportunity_crud import create_opportunity

        db = _make_db()
        current_user = _make_user()

        opp_in = MagicMock()
        opp_in.requirement = None
        opp_in.model_dump.return_value = {
            "opp_code": "EXISTING001",
            "customer_id": 1,
        }

        # existing opportunity found for code check
        db.query.return_value.filter.return_value.first.return_value = _make_opp()

        with pytest.raises(HTTPException) as exc_info:
            create_opportunity(db=db, opp_in=opp_in, current_user=current_user)

        assert exc_info.value.status_code == 400


# ──────────────────────────────────────────────
# Tests: read_opportunity
# ──────────────────────────────────────────────

class TestReadOpportunity:

    def test_read_opportunity_success(self):
        """正常读取商机详情"""
        from app.api.v1.endpoints.sales.opportunity_crud import read_opportunity

        db = _make_db()
        current_user = _make_user()
        opp = _make_opp()
        opp.__table__.columns = []

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = opp
        db.query.return_value = mock_query

        with patch("app.api.v1.endpoints.sales.opportunity_crud.OpportunityRequirementResponse"), \
             patch("app.api.v1.endpoints.sales.opportunity_crud.OpportunityResponse") as MockResp:
            MockResp.return_value = MagicMock()

            result = read_opportunity(db=db, opp_id=1, current_user=current_user)

        assert result is not None

    def test_read_opportunity_not_found(self):
        """商机不存在时抛出404"""
        from app.api.v1.endpoints.sales.opportunity_crud import read_opportunity

        db = _make_db()
        current_user = _make_user()

        mock_query = MagicMock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        db.query.return_value = mock_query

        with pytest.raises(HTTPException) as exc_info:
            read_opportunity(db=db, opp_id=999, current_user=current_user)

        assert exc_info.value.status_code == 404


# ──────────────────────────────────────────────
# Tests: update_opportunity
# ──────────────────────────────────────────────

class TestUpdateOpportunity:

    def test_update_opportunity_success(self):
        """有权限时正常更新"""
        from app.api.v1.endpoints.sales.opportunity_crud import update_opportunity

        db = _make_db()
        current_user = _make_user()
        opp = _make_opp()
        opp.__table__.columns = []

        opp_in = MagicMock()
        opp_in.requirement = None
        opp_in.model_dump.return_value = {"opp_name": "更新后的商机名"}

        with patch("app.api.v1.endpoints.sales.opportunity_crud.get_or_404", return_value=opp), \
             patch("app.api.v1.endpoints.sales.opportunity_crud.security") as mock_sec, \
             patch("app.api.v1.endpoints.sales.opportunity_crud.get_entity_creator_id", return_value=1), \
             patch("app.api.v1.endpoints.sales.opportunity_crud.OpportunityRequirementResponse"), \
             patch("app.api.v1.endpoints.sales.opportunity_crud.OpportunityResponse") as MockResp:
            mock_sec.check_sales_edit_permission.return_value = True
            MockResp.return_value = MagicMock()
            db.query.return_value.filter.return_value.first.return_value = None  # no requirement

            result = update_opportunity(db=db, opp_id=1, opp_in=opp_in, current_user=current_user)

        assert db.commit.called

    def test_update_opportunity_no_permission(self):
        """无编辑权限时抛出403"""
        from app.api.v1.endpoints.sales.opportunity_crud import update_opportunity

        db = _make_db()
        current_user = _make_user(
        )
        current_user.is_superuser = False
        opp = _make_opp()

        opp_in = MagicMock()
        opp_in.requirement = None
        opp_in.model_dump.return_value = {}

        with patch("app.api.v1.endpoints.sales.opportunity_crud.get_or_404", return_value=opp), \
             patch("app.api.v1.endpoints.sales.opportunity_crud.security") as mock_sec, \
             patch("app.api.v1.endpoints.sales.opportunity_crud.get_entity_creator_id", return_value=2):
            mock_sec.check_sales_edit_permission.return_value = False

            with pytest.raises(HTTPException) as exc_info:
                update_opportunity(db=db, opp_id=1, opp_in=opp_in, current_user=current_user)

        assert exc_info.value.status_code == 403
