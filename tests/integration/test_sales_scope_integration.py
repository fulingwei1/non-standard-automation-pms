# -*- coding: utf-8 -*-
"""
销售数据范围可见性集成测试

使用 SQLite 内存数据库 + 真实模型，调用 sales_permissions / sales_scope 服务层函数，
验证 OWN / DEPARTMENT / FINANCE / ALL 各级别的列表过滤与实体访问判断。

覆盖场景：
  1. OWN 范围：只能看到自己的线索/商机
  2. DEPT 范围：能看到同部门成员的数据
  3. 财务角色特权：FINANCE_ONLY 对普通销售数据不可见，但发票/收款可见
  4. 导出/analytics 复用 scope 过滤：模拟列表查询后验证过滤结果
  5. sales_scope.py 的 apply_owner_scope / can_access 函数
"""

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import Column, Integer, Table, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


def _create_test_engine():
    import app.models  # noqa: F401

    for stub in ["production_work_orders", "suppliers"]:
        if stub not in Base.metadata.tables:
            Table(stub, Base.metadata, Column("id", Integer, primary_key=True))

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    for table in Base.metadata.sorted_tables:
        try:
            table.create(bind=engine, checkfirst=True)
        except Exception:
            pass
    return engine


@pytest.fixture(scope="function")
def db():
    engine = _create_test_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(db, username, real_name="测试用户", department="销售部", is_superuser=False):
    from app.models.user import User

    user = User(
        username=username,
        password_hash="hashed_pw",
        real_name=real_name,
        department=department,
        is_active=True,
        is_superuser=is_superuser,
    )
    db.add(user)
    db.flush()
    return user


def _make_department(db, dept_name):
    from app.models.organization import Department

    dept = Department(
        dept_code=f"D-{uuid.uuid4().hex[:6]}",
        dept_name=dept_name,
        is_active=True,
    )
    db.add(dept)
    db.flush()
    return dept


def _make_customer(db, name="测试客户"):
    from app.models.project import Customer

    cust = Customer(
        customer_code=f"C-{uuid.uuid4().hex[:6]}",
        customer_name=name,
        status="ACTIVE",
    )
    db.add(cust)
    db.flush()
    return cust


def _make_lead(db, owner_id, name="测试线索"):
    from app.models.sales import Lead

    lead = Lead(
        lead_code=f"LD-{uuid.uuid4().hex[:8]}",
        customer_name=name,
        source="WEBSITE",
        status="NEW",
        owner_id=owner_id,
    )
    db.add(lead)
    db.flush()
    return lead


def _make_opportunity(db, owner_id, customer_id, opp_name="测试商机"):
    from app.models.sales import Opportunity

    opp = Opportunity(
        opp_code=f"OP-{uuid.uuid4().hex[:8]}",
        opp_name=opp_name,
        customer_id=customer_id,
        stage="INITIAL",
        probability=30,
        est_amount=Decimal("100000.00"),
        expected_close_date=date.today() + timedelta(days=60),
        owner_id=owner_id,
    )
    db.add(opp)
    db.flush()
    return opp


# ===========================================================================
# Tests — OWN 范围
# ===========================================================================


@pytest.mark.integration
@pytest.mark.permission
class TestOwnScopeFiltering:
    """TC-SS-1x: OWN 范围过滤"""

    def test_own_scope_only_sees_own_leads(self, db):
        """TC-SS-11: OWN 范围用户只能看到自己负责的线索。"""
        from app.models.sales import Lead
        from app.core.sales_permissions import filter_sales_data_by_scope

        user_a = _make_user(db, "sales_a", "销售A")
        user_b = _make_user(db, "sales_b", "销售B")

        lead_a = _make_lead(db, user_a.id, "A的线索")
        lead_b = _make_lead(db, user_b.id, "B的线索")
        db.commit()

        query = db.query(Lead)
        with patch("app.core.sales_permissions.get_sales_data_scope", return_value="OWN"):
            filtered = filter_sales_data_by_scope(query, user_a, db, Lead, "owner_id")

        results = filtered.all()
        result_ids = {r.id for r in results}

        assert lead_a.id in result_ids
        assert lead_b.id not in result_ids

    def test_own_scope_entity_check_denied(self, db):
        """TC-SS-12: OWN 范围用户不能访问他人的单条实体。"""
        from app.core.sales_permissions import check_sales_data_permission

        user_a = _make_user(db, "sales_own_a", "销售A")
        user_b = _make_user(db, "sales_own_b", "销售B")
        lead_b = _make_lead(db, user_b.id, "B的线索")
        db.commit()

        with patch("app.core.sales_permissions.get_sales_data_scope", return_value="OWN"):
            assert check_sales_data_permission(lead_b, user_a, db, "owner_id") is False

    def test_own_scope_can_access_own_entity(self, db):
        """TC-SS-13: OWN 范围用户可以访问自己的实体。"""
        from app.core.sales_permissions import check_sales_data_permission

        user_a = _make_user(db, "sales_own_self", "销售A")
        lead_a = _make_lead(db, user_a.id, "A的线索")
        db.commit()

        with patch("app.core.sales_permissions.get_sales_data_scope", return_value="OWN"):
            assert check_sales_data_permission(lead_a, user_a, db, "owner_id") is True


# ===========================================================================
# Tests — DEPT 范围
# ===========================================================================


@pytest.mark.integration
@pytest.mark.permission
class TestDeptScopeFiltering:
    """TC-SS-2x: DEPT 范围过滤"""

    def test_dept_scope_sees_same_department(self, db):
        """TC-SS-21: DEPT 范围用户可以看到同部门成员的数据。"""
        from app.models.sales import Lead
        from app.core.sales_permissions import filter_sales_data_by_scope

        _make_department(db, "销售一部")
        _make_department(db, "销售二部")

        user_a = _make_user(db, "dept_a", "部门A", department="销售一部")
        user_b = _make_user(db, "dept_b", "部门B", department="销售一部")
        user_c = _make_user(db, "dept_c", "部门C", department="销售二部")

        lead_a = _make_lead(db, user_a.id, "A的线索")
        lead_b = _make_lead(db, user_b.id, "B的线索（同部门）")
        lead_c = _make_lead(db, user_c.id, "C的线索（他部门）")
        db.commit()

        query = db.query(Lead)
        with patch("app.core.sales_permissions.get_sales_data_scope", return_value="DEPT"):
            filtered = filter_sales_data_by_scope(query, user_a, db, Lead, "owner_id")

        results = filtered.all()
        result_ids = {r.id for r in results}

        assert lead_a.id in result_ids
        assert lead_b.id in result_ids
        assert lead_c.id not in result_ids

    def test_dept_scope_entity_check_cross_dept_denied(self, db):
        """TC-SS-22: DEPT 范围不能访问其他部门的单条记录。"""
        from app.core.sales_permissions import check_sales_data_permission

        _make_department(db, "部门X")
        _make_department(db, "部门Y")

        user_x = _make_user(db, "dept_x", "用户X", department="部门X")
        user_y = _make_user(db, "dept_y", "用户Y", department="部门Y")
        lead_y = _make_lead(db, user_y.id, "Y的线索")
        db.commit()

        with patch("app.core.sales_permissions.get_sales_data_scope", return_value="DEPT"):
            assert check_sales_data_permission(lead_y, user_x, db, "owner_id") is False


# ===========================================================================
# Tests — 财务角色特权
# ===========================================================================


@pytest.mark.integration
@pytest.mark.permission
class TestFinanceRolePrivilege:
    """TC-SS-3x: 财务角色特权"""

    def test_finance_role_blocks_normal_sales_data(self, db):
        """TC-SS-31: FINANCE_ONLY 范围对普通商机不可见。"""
        from app.models.sales import Lead
        from app.core.sales_permissions import filter_sales_data_by_scope

        finance_user = _make_user(db, "finance01", "财务人员", department="财务部")
        sales_user = _make_user(db, "sales01", "销售人员")

        _make_lead(db, sales_user.id, "销售的线索")
        db.commit()

        query = db.query(Lead)
        with patch("app.core.sales_permissions.get_sales_data_scope", return_value="FINANCE_ONLY"):
            filtered = filter_sales_data_by_scope(query, finance_user, db, Lead, "owner_id")

        results = filtered.all()
        assert len(results) == 0

    def test_finance_role_can_see_invoice_data(self, db):
        """TC-SS-32: FINANCE_ONLY 对发票/收款数据可见（filter_sales_finance_data_by_scope 不过滤）。"""
        from app.models.sales import Lead
        from app.core.sales_permissions import filter_sales_finance_data_by_scope

        finance_user = _make_user(db, "finance02", "财务人员2", department="财务部")
        sales_user = _make_user(db, "sales02", "销售人员2")

        _make_lead(db, sales_user.id, "模拟发票数据")
        db.commit()

        query = db.query(Lead)
        with patch("app.core.sales_permissions.get_sales_data_scope", return_value="FINANCE_ONLY"):
            filtered = filter_sales_finance_data_by_scope(
                query, finance_user, db, Lead, "owner_id"
            )

        results = filtered.all()
        assert len(results) > 0

    def test_finance_entity_check_denied_for_non_finance_scope(self, db):
        """TC-SS-33: FINANCE_ONLY scope 下 check_sales_data_permission 返回 False。"""
        from app.core.sales_permissions import check_sales_data_permission

        user = _make_user(db, "random_user", "普通用户")
        sales_user = _make_user(db, "sales03", "销售")
        lead = _make_lead(db, sales_user.id, "销售的线索")
        db.commit()

        with patch("app.core.sales_permissions.get_sales_data_scope", return_value="FINANCE_ONLY"):
            assert check_sales_data_permission(lead, user, db, "owner_id") is False


# ===========================================================================
# Tests — 导出/Analytics scope 过滤
# ===========================================================================


@pytest.mark.integration
@pytest.mark.permission
class TestExportAnalyticsScopeFiltering:
    """TC-SS-4x: 导出/Analytics 使用相同 scope 过滤逻辑"""

    def test_export_query_respects_own_scope(self, db):
        """TC-SS-41: 模拟导出场景 — OWN 用户只能导出自己的数据。"""
        from app.models.sales import Lead
        from app.core.sales_permissions import filter_sales_data_by_scope

        user_a = _make_user(db, "export_a", "导出用户A")
        user_b = _make_user(db, "export_b", "导出用户B")

        lead_a = _make_lead(db, user_a.id, "A的线索")
        lead_b = _make_lead(db, user_b.id, "B的线索")
        db.commit()

        export_query = db.query(Lead)
        with patch("app.core.sales_permissions.get_sales_data_scope", return_value="OWN"):
            filtered = filter_sales_data_by_scope(export_query, user_a, db, Lead, "owner_id")

        results = filtered.all()
        result_ids = {r.id for r in results}

        assert lead_a.id in result_ids
        assert lead_b.id not in result_ids

    def test_analytics_query_all_scope_sees_everything(self, db):
        """TC-SS-42: ALL 范围用户在 analytics 查询中能看到所有数据。"""
        from app.models.sales import Lead
        from app.core.sales_permissions import filter_sales_data_by_scope

        boss = _make_user(db, "boss", "总经理")
        user_a = _make_user(db, "analytics_a", "销售A")
        user_b = _make_user(db, "analytics_b", "销售B")

        lead_a = _make_lead(db, user_a.id, "线索A")
        lead_b = _make_lead(db, user_b.id, "线索B")
        db.commit()

        query = db.query(Lead)
        with patch("app.core.sales_permissions.get_sales_data_scope", return_value="ALL"):
            filtered = filter_sales_data_by_scope(query, boss, db, Lead, "owner_id")

        results = filtered.all()
        result_ids = {r.id for r in results}

        assert lead_a.id in result_ids
        assert lead_b.id in result_ids

    def test_export_dept_scope_filters_correctly(self, db):
        """TC-SS-43: DEPT 范围导出只包含同部门数据。"""
        from app.models.sales import Lead
        from app.core.sales_permissions import filter_sales_data_by_scope

        _make_department(db, "出口部")
        _make_department(db, "内销部")

        user_a = _make_user(db, "exp_dept_a", "出口A", department="出口部")
        user_b = _make_user(db, "exp_dept_b", "出口B", department="出口部")
        user_c = _make_user(db, "exp_dept_c", "内销C", department="内销部")

        lead_a = _make_lead(db, user_a.id, "出口线索A")
        lead_b = _make_lead(db, user_b.id, "出口线索B")
        lead_c = _make_lead(db, user_c.id, "内销线索C")
        db.commit()

        query = db.query(Lead)
        with patch("app.core.sales_permissions.get_sales_data_scope", return_value="DEPT"):
            filtered = filter_sales_data_by_scope(query, user_a, db, Lead, "owner_id")

        results = filtered.all()
        result_ids = {r.id for r in results}

        assert lead_a.id in result_ids
        assert lead_b.id in result_ids
        assert lead_c.id not in result_ids

    def test_export_with_real_opportunity_model(self, db):
        """TC-SS-44: 用真实 Opportunity 模型验证 OWN 过滤（含 customer FK）。"""
        from app.models.sales import Opportunity
        from app.core.sales_permissions import filter_sales_data_by_scope

        cust = _make_customer(db)
        user_a = _make_user(db, "opp_export_a", "销售A")
        user_b = _make_user(db, "opp_export_b", "销售B")

        opp_a = _make_opportunity(db, user_a.id, cust.id, "A的商机")
        opp_b = _make_opportunity(db, user_b.id, cust.id, "B的商机")
        db.commit()

        query = db.query(Opportunity)
        with patch("app.core.sales_permissions.get_sales_data_scope", return_value="OWN"):
            filtered = filter_sales_data_by_scope(query, user_a, db, Opportunity, "owner_id")

        result_ids = {r.id for r in filtered.all()}
        assert opp_a.id in result_ids
        assert opp_b.id not in result_ids


# ===========================================================================
# Tests — sales_scope.py 服务层
# ===========================================================================


@pytest.mark.integration
@pytest.mark.permission
class TestSalesScopeService:
    """TC-SS-5x: sales_scope.py 的 apply_owner_scope + can_access 函数"""

    def test_apply_owner_scope_own(self, db):
        """TC-SS-51: apply_owner_scope(OWN) 只返回 owner 为自己的记录。"""
        from app.models.sales import Lead
        from app.services.sales.sales_scope import (
            SalesScopeContext,
            apply_owner_scope,
        )
        from app.models.permission import ScopeType

        user_a = _make_user(db, "scope_own_a", "用户A")
        user_b = _make_user(db, "scope_own_b", "用户B")
        lead_a = _make_lead(db, user_a.id, "A的")
        lead_b = _make_lead(db, user_b.id, "B的")
        db.commit()

        ctx = SalesScopeContext(
            scope_type=ScopeType.OWN.value,
            user_id=user_a.id,
        )
        query = db.query(Lead)
        filtered = apply_owner_scope(query, ctx, Lead.owner_id)

        result_ids = {r.id for r in filtered.all()}
        assert lead_a.id in result_ids
        assert lead_b.id not in result_ids

    def test_apply_owner_scope_team(self, db):
        """TC-SS-52: apply_owner_scope(TEAM) 包含自己和下属的记录。"""
        from app.models.sales import Lead
        from app.services.sales.sales_scope import (
            SalesScopeContext,
            apply_owner_scope,
        )
        from app.models.permission import ScopeType

        manager = _make_user(db, "mgr01", "经理")
        subordinate = _make_user(db, "sub01", "下属")
        outsider = _make_user(db, "out01", "外人")

        lead_mgr = _make_lead(db, manager.id, "经理的线索")
        lead_sub = _make_lead(db, subordinate.id, "下属的线索")
        lead_out = _make_lead(db, outsider.id, "外人的线索")
        db.commit()

        ctx = SalesScopeContext(
            scope_type=ScopeType.TEAM.value,
            user_id=manager.id,
            accessible_user_ids={manager.id, subordinate.id},
        )
        query = db.query(Lead)
        filtered = apply_owner_scope(query, ctx, Lead.owner_id)

        result_ids = {r.id for r in filtered.all()}
        assert lead_mgr.id in result_ids
        assert lead_sub.id in result_ids
        assert lead_out.id not in result_ids

    def test_can_access_sales_entity_own_denied(self, db):
        """TC-SS-53: can_access_sales_entity(OWN) 对他人的实体返回 False。"""
        from app.services.sales.sales_scope import (
            SalesScopeContext,
            can_access_sales_entity,
        )
        from app.models.permission import ScopeType

        ctx = SalesScopeContext(
            scope_type=ScopeType.OWN.value,
            user_id=100,
        )
        assert can_access_sales_entity(ctx, owner_id=200) is False

    def test_can_access_finance_entity_finance_role(self, db):
        """TC-SS-54: 财务角色可以访问财务实体。"""
        from app.services.sales.sales_scope import (
            SalesScopeContext,
            can_access_finance_entity,
        )
        from app.models.permission import ScopeType

        ctx = SalesScopeContext(
            scope_type=ScopeType.OWN.value,
            user_id=100,
            is_finance_role=True,
        )
        assert can_access_finance_entity(ctx, owner_id=200) is True

    def test_apply_finance_scope_non_finance_blocked(self, db):
        """TC-SS-55: 非财务、非 ALL 用户对无 owner_column 的数据不可见。"""
        from app.models.sales import Lead
        from app.services.sales.sales_scope import (
            SalesScopeContext,
            apply_finance_scope,
        )
        from app.models.permission import ScopeType

        user = _make_user(db, "no_fin", "普通用户")
        _make_lead(db, user.id, "一些数据")
        db.commit()

        ctx = SalesScopeContext(
            scope_type=ScopeType.OWN.value,
            user_id=user.id,
            is_finance_role=False,
        )
        query = db.query(Lead)
        filtered = apply_finance_scope(query, ctx, owner_column=None)
        assert len(filtered.all()) == 0
