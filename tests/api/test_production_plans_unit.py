# -*- coding: utf-8 -*-
"""
O1组 API层单元测试 - production/plans.py
使用 Method A: 直接调用端点函数 + MagicMock

覆盖：
  - read_production_plans
  - create_production_plan
  - read_production_plan
  - update_production_plan
  - submit_production_plan
  - approve_production_plan
  - publish_production_plan
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

# 服务层的 patch 前缀
SVC = "app.services.production.plan_service"


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _make_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db


def _make_user():
    user = MagicMock()
    user.id = 1
    user.username = "admin"
    user.is_superuser = True
    return user


def _make_plan(plan_id=1, status="DRAFT"):
    from datetime import date
    plan = MagicMock()
    plan.id = plan_id
    plan.plan_no = f"PP{plan_id:06d}"
    plan.payment_name = "2026年Q1生产计划"
    plan.plan_type = "MASTER"
    plan.project_id = 1
    plan.workshop_id = 1
    plan.plan_start_date = date(2026, 1, 1)
    plan.plan_end_date = date(2026, 3, 31)
    plan.status = status
    plan.progress = 0
    plan.description = "测试计划"
    plan.created_by = 1
    plan.approved_by = None
    plan.approved_at = None
    plan.remark = None
    plan.created_at = None
    plan.updated_at = None
    return plan


def _make_pagination():
    pag = MagicMock()
    pag.offset = 0
    pag.limit = 20
    pag.page = 1
    pag.page_size = 20
    pag.to_response = MagicMock(return_value={"items": [], "total": 0, "page": 1, "page_size": 20})
    return pag


# ──────────────────────────────────────────────
# Tests: read_production_plans
# ──────────────────────────────────────────────

class TestReadProductionPlans:

    def test_list_plans_empty(self):
        """空数据库列表请求应返回空列表"""
        from app.api.v1.endpoints.production.plans import read_production_plans

        db = _make_db()
        current_user = _make_user()
        pagination = _make_pagination()

        db.query.return_value.filter.return_value = db.query.return_value
        db.query.return_value.count.return_value = 0
        db.query.return_value.order_by.return_value = db.query.return_value
        db.query.return_value.all.return_value = []

        with patch(f"{SVC}.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = []

            result = read_production_plans(
                db=db,
                pagination=pagination,
                plan_type=None,
                project_id=None,
                workshop_id=None,
                status=None,
                current_user=current_user,
            )

        pagination.to_response.assert_called_once()

    def test_list_plans_with_filter(self):
        """按plan_type过滤应传递正确条件"""
        from app.api.v1.endpoints.production.plans import read_production_plans

        db = _make_db()
        current_user = _make_user()
        pagination = _make_pagination()
        plan = _make_plan()

        db.query.return_value.filter.return_value = db.query.return_value
        db.query.return_value.count.return_value = 1

        with patch(f"{SVC}.apply_pagination") as mock_pag:
            mock_pag.return_value.all.return_value = [plan]
            db.query.return_value.filter.return_value.first.return_value = None  # project/workshop lookups

            result = read_production_plans(
                db=db,
                pagination=pagination,
                plan_type="MASTER",
                project_id=None,
                workshop_id=None,
                status=None,
                current_user=current_user,
            )

        assert db.query.called


# ──────────────────────────────────────────────
# Tests: create_production_plan
# ──────────────────────────────────────────────

class TestCreateProductionPlan:

    def test_create_plan_success(self):
        """正常创建生产计划"""
        from app.api.v1.endpoints.production.plans import create_production_plan

        db = _make_db()
        current_user = _make_user()

        plan_in = MagicMock()
        plan_in.project_id = 1
        plan_in.workshop_id = 1
        plan_in.model_dump.return_value = {
            "plan_name": "2026年Q1生产计划",
            "plan_type": "MASTER",
            "project_id": 1,
            "workshop_id": 1,
        }

        project_mock = MagicMock(project_name="比亚迪项目")
        workshop_mock = MagicMock(workshop_name="一号车间")

        db.query.return_value.filter.return_value.first.side_effect = [
            project_mock, workshop_mock, project_mock, workshop_mock
        ]

        plan_instance = _make_plan()

        with patch(f"{SVC}.ProductionPlan") as MockPlan, \
             patch("app.api.v1.endpoints.production.utils.generate_plan_no", return_value="PP000001"), \
             patch(f"{SVC}.save_obj"):
            MockPlan.return_value = plan_instance

            result = create_production_plan(db=db, plan_in=plan_in, current_user=current_user)

        assert result is not None
        assert result.id == 1

    def test_create_plan_project_not_found(self):
        """项目不存在时抛出404"""
        from app.api.v1.endpoints.production.plans import create_production_plan

        db = _make_db()
        current_user = _make_user()

        plan_in = MagicMock()
        plan_in.project_id = 999
        plan_in.workshop_id = None
        plan_in.model_dump.return_value = {"project_id": 999}

        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            create_production_plan(db=db, plan_in=plan_in, current_user=current_user)

        assert exc_info.value.status_code == 404

    def test_create_plan_workshop_not_found(self):
        """车间不存在时抛出404"""
        from app.api.v1.endpoints.production.plans import create_production_plan

        db = _make_db()
        current_user = _make_user()

        plan_in = MagicMock()
        plan_in.project_id = None
        plan_in.workshop_id = 999
        plan_in.model_dump.return_value = {"workshop_id": 999}

        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            create_production_plan(db=db, plan_in=plan_in, current_user=current_user)

        assert exc_info.value.status_code == 404


# ──────────────────────────────────────────────
# Tests: read_production_plan
# ──────────────────────────────────────────────

class TestReadProductionPlan:

    def test_read_plan_success(self):
        """正常读取生产计划详情"""
        from app.api.v1.endpoints.production.plans import read_production_plan

        db = _make_db()
        current_user = _make_user()
        plan = _make_plan()

        with patch(f"{SVC}.get_or_404", return_value=plan):
            db.query.return_value.filter.return_value.first.return_value = None
            result = read_production_plan(plan_id=1, db=db, current_user=current_user)

        assert result.id == 1
        assert result.plan_no == "PP000001"

    def test_read_plan_not_found(self):
        """计划不存在时抛出404"""
        from app.api.v1.endpoints.production.plans import read_production_plan

        db = _make_db()
        current_user = _make_user()

        with patch(
            f"{SVC}.get_or_404",
            side_effect=HTTPException(status_code=404, detail="生产计划不存在")
        ):
            with pytest.raises(HTTPException) as exc_info:
                read_production_plan(plan_id=999, db=db, current_user=current_user)

        assert exc_info.value.status_code == 404


# ──────────────────────────────────────────────
# Tests: update_production_plan
# ──────────────────────────────────────────────

class TestUpdateProductionPlan:

    def test_update_plan_draft_success(self):
        """草稿状态计划可正常更新"""
        from app.api.v1.endpoints.production.plans import update_production_plan

        db = _make_db()
        current_user = _make_user()
        plan = _make_plan(status="DRAFT")

        plan_in = MagicMock()
        plan_in.model_dump.return_value = {"plan_name": "更新计划名"}

        with patch(f"{SVC}.get_or_404", return_value=plan), \
             patch(f"{SVC}.save_obj"):
            db.query.return_value.filter.return_value.first.return_value = None
            result = update_production_plan(db=db, plan_id=1, plan_in=plan_in, current_user=current_user)

        assert result is not None

    def test_update_plan_non_draft_raises(self):
        """非草稿状态计划不可更新"""
        from app.api.v1.endpoints.production.plans import update_production_plan

        db = _make_db()
        current_user = _make_user()
        plan = _make_plan(status="SUBMITTED")

        plan_in = MagicMock()
        plan_in.model_dump.return_value = {}

        with patch(f"{SVC}.get_or_404", return_value=plan):
            with pytest.raises(HTTPException) as exc_info:
                update_production_plan(db=db, plan_id=1, plan_in=plan_in, current_user=current_user)

        assert exc_info.value.status_code == 400


# ──────────────────────────────────────────────
# Tests: submit / approve / publish
# ──────────────────────────────────────────────

class TestPlanWorkflow:

    def test_submit_draft_plan(self):
        """草稿计划可以提交"""
        from app.api.v1.endpoints.production.plans import submit_production_plan

        db = _make_db()
        current_user = _make_user()
        plan = _make_plan(status="DRAFT")

        with patch(f"{SVC}.get_or_404", return_value=plan):
            result = submit_production_plan(db=db, plan_id=1, current_user=current_user)

        assert plan.status == "SUBMITTED"
        assert db.commit.called
        assert result["code"] == 200

    def test_submit_non_draft_raises(self):
        """非草稿计划不可提交"""
        from app.api.v1.endpoints.production.plans import submit_production_plan

        db = _make_db()
        current_user = _make_user()
        plan = _make_plan(status="SUBMITTED")

        with patch(f"{SVC}.get_or_404", return_value=plan):
            with pytest.raises(HTTPException) as exc_info:
                submit_production_plan(db=db, plan_id=1, current_user=current_user)

        assert exc_info.value.status_code == 400

    def test_approve_plan_success(self):
        """审批通过已提交的计划"""
        from app.api.v1.endpoints.production.plans import approve_production_plan

        db = _make_db()
        current_user = _make_user()
        plan = _make_plan(status="SUBMITTED")

        with patch(f"{SVC}.get_or_404", return_value=plan):
            result = approve_production_plan(
                db=db, plan_id=1, approved=True, approval_note="通过", current_user=current_user
            )

        assert plan.status == "APPROVED"
        assert plan.approved_by == current_user.id
        assert result["code"] == 200

    def test_reject_plan(self):
        """驳回计划回到草稿状态"""
        from app.api.v1.endpoints.production.plans import approve_production_plan

        db = _make_db()
        current_user = _make_user()
        plan = _make_plan(status="SUBMITTED")

        with patch(f"{SVC}.get_or_404", return_value=plan):
            result = approve_production_plan(
                db=db, plan_id=1, approved=False, approval_note=None, current_user=current_user
            )

        assert plan.status == "DRAFT"

    def test_publish_approved_plan(self):
        """已审批计划可以发布"""
        from app.api.v1.endpoints.production.plans import publish_production_plan

        db = _make_db()
        current_user = _make_user()
        plan = _make_plan(status="APPROVED")

        with patch(f"{SVC}.get_or_404", return_value=plan):
            result = publish_production_plan(db=db, plan_id=1, current_user=current_user)

        assert plan.status == "PUBLISHED"
        assert result["code"] == 200

    def test_publish_unapproved_raises(self):
        """未审批计划不可发布"""
        from app.api.v1.endpoints.production.plans import publish_production_plan

        db = _make_db()
        current_user = _make_user()
        plan = _make_plan(status="DRAFT")

        with patch(f"{SVC}.get_or_404", return_value=plan):
            with pytest.raises(HTTPException) as exc_info:
                publish_production_plan(db=db, plan_id=1, current_user=current_user)

        assert exc_info.value.status_code == 400
