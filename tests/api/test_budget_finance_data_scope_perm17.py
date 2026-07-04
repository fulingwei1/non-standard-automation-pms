# -*- coding: utf-8 -*-
"""
PERM-17 预算/成本/财务报表域数据权限过滤测试

覆盖新挂载的 DataScopeService.filter_by_scope：
- app.api.v1.endpoints.budget.budgets.list_budgets
- app.api.v1.endpoints.budget.items.get_budget_items
- app.api.v1.endpoints.finance_reports.get_project_profitability

对每个改动端点验证：
(a) ALL 范围 / 超级管理员可看到全部记录
(b) OWN 范围仅能看到自己创建/管理的记录
"""

import uuid
from datetime import date
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.budget import ProjectBudget
from app.models.project import Project
from app.models.user import User

SCOPE_PATCH_TARGET = "app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope"


def _make_user(db: Session, *, is_superuser: bool = False) -> User:
    unique = uuid.uuid4().hex[:10]
    user = User(
        username=f"perm17_budget_{unique}",
        password_hash=get_password_hash("Test1234!"),
        real_name=f"用户{unique}",
        is_active=True,
        is_superuser=is_superuser,
    )
    db.add(user)
    db.flush()
    return user


def _make_project(db: Session, *, created_by=None, pm_id=None) -> Project:
    unique = uuid.uuid4().hex[:10]
    project = Project(
        project_code=f"PRJ{unique}",
        project_name=f"项目{unique}",
        created_by=created_by,
        pm_id=pm_id,
        is_active=True,
        contract_amount=1_000_000,
        actual_cost=500_000,
    )
    db.add(project)
    db.flush()
    return project


def _make_budget(db: Session, *, project: Project, created_by=None) -> ProjectBudget:
    unique = uuid.uuid4().hex[:10]
    budget = ProjectBudget(
        budget_no=f"BUD-{unique}",
        project_id=project.id,
        budget_name=f"预算{unique}",
        total_amount=100_000,
        status="DRAFT",
        created_by=created_by,
    )
    db.add(budget)
    db.flush()
    return budget


class TestListBudgetsDataScope:
    """app/api/v1/endpoints/budget/budgets.py::list_budgets"""

    def test_all_scope_sees_every_users_budgets(self, db_session: Session):
        from app.api.v1.endpoints.budget.budgets import list_budgets
        from app.common.pagination import PaginationParams

        user_a = _make_user(db_session, is_superuser=True)
        user_b = _make_user(db_session)
        project = _make_project(db_session, created_by=user_a.id)
        _make_budget(db_session, project=project, created_by=user_a.id)
        _make_budget(db_session, project=project, created_by=user_b.id)
        db_session.commit()

        result = list_budgets(
            db=db_session,
            pagination=PaginationParams(page=1, page_size=50, offset=0, limit=50),
            project_id=None,
            budget_status=None,
            budget_type=None,
            current_user=user_a,
        )

        seen_creators = {item.created_by for item in result["items"]}
        assert user_a.id in seen_creators
        assert user_b.id in seen_creators

    def test_own_scope_sees_only_self_created_budgets(self, db_session: Session):
        from app.api.v1.endpoints.budget.budgets import list_budgets
        from app.common.pagination import PaginationParams

        user_a = _make_user(db_session)
        user_b = _make_user(db_session)
        project = _make_project(db_session, created_by=user_a.id)
        _make_budget(db_session, project=project, created_by=user_a.id)
        _make_budget(db_session, project=project, created_by=user_b.id)
        db_session.commit()

        with patch(SCOPE_PATCH_TARGET, return_value="OWN"):
            result = list_budgets(
                db=db_session,
                pagination=PaginationParams(page=1, page_size=50, offset=0, limit=50),
                project_id=None,
                budget_status=None,
                budget_type=None,
                current_user=user_a,
            )

        seen_creators = {item.created_by for item in result["items"]}
        assert seen_creators == {user_a.id}


class TestBudgetItemsDataScope:
    """app/api/v1/endpoints/budget/items.py::get_budget_items"""

    def test_all_scope_sees_items_of_any_budget(self, db_session: Session):
        from app.api.v1.endpoints.budget.items import get_budget_items

        user_a = _make_user(db_session, is_superuser=True)
        user_b = _make_user(db_session)
        project = _make_project(db_session, created_by=user_b.id)
        budget = _make_budget(db_session, project=project, created_by=user_b.id)
        db_session.commit()

        items = get_budget_items(db=db_session, budget_id=budget.id, current_user=user_a)
        assert items == []  # no items yet, but no 404 raised -> access granted

    def test_own_scope_cannot_access_others_budget_items(self, db_session: Session):
        from app.api.v1.endpoints.budget.items import get_budget_items

        user_a = _make_user(db_session)
        user_b = _make_user(db_session)
        project = _make_project(db_session, created_by=user_b.id)
        budget = _make_budget(db_session, project=project, created_by=user_b.id)
        db_session.commit()

        with patch(SCOPE_PATCH_TARGET, return_value="OWN"):
            with pytest.raises(HTTPException) as exc_info:
                get_budget_items(db=db_session, budget_id=budget.id, current_user=user_a)

        assert exc_info.value.status_code == 404

    def test_own_scope_can_access_own_budget_items(self, db_session: Session):
        from app.api.v1.endpoints.budget.items import get_budget_items

        user_a = _make_user(db_session)
        project = _make_project(db_session, created_by=user_a.id)
        budget = _make_budget(db_session, project=project, created_by=user_a.id)
        db_session.commit()

        with patch(SCOPE_PATCH_TARGET, return_value="OWN"):
            items = get_budget_items(db=db_session, budget_id=budget.id, current_user=user_a)

        assert items == []


class TestProjectProfitabilityDataScope:
    """app/api/v1/endpoints/finance_reports.py::get_project_profitability"""

    def test_all_scope_sees_every_project(self, db_session: Session):
        from app.api.v1.endpoints.finance_reports import get_project_profitability

        user_a = _make_user(db_session, is_superuser=True)
        user_b = _make_user(db_session)
        _make_project(db_session, created_by=user_a.id)
        _make_project(db_session, created_by=user_b.id)
        db_session.commit()

        rows = get_project_profitability(limit=100, db=db_session, current_user=user_a)

        assert len(rows) >= 2

    def test_own_scope_sees_only_own_projects(self, db_session: Session):
        from app.api.v1.endpoints.finance_reports import get_project_profitability

        user_a = _make_user(db_session)
        user_b = _make_user(db_session)
        project_a = _make_project(db_session, created_by=user_a.id)
        project_b = _make_project(db_session, created_by=user_b.id)
        db_session.commit()

        with patch(SCOPE_PATCH_TARGET, return_value="OWN"):
            rows = get_project_profitability(limit=100, db=db_session, current_user=user_a)

        seen_names = {row["project"] for row in rows}
        # 只应看到自己创建的项目，看不到 project_b
        assert (project_a.short_name or project_a.project_name or project_a.project_code) in seen_names
        assert (
            project_b.short_name or project_b.project_name or project_b.project_code
        ) not in seen_names
