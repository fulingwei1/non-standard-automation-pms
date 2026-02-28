# -*- coding: utf-8 -*-
"""
O1组 API层单元测试 - projects/project_crud.py
使用 Method A: 直接调用端点函数 + MagicMock

覆盖：
  - create_project
  - read_project
  - update_project
  - delete_project
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

import uuid

_P0001 = f"P0001-{uuid.uuid4().hex[:8]}"
_P0002 = f"P0002-{uuid.uuid4().hex[:8]}"



# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _make_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db


def _make_user(is_superuser=True):
    user = MagicMock()
    user.id = 1
    user.username = "admin"
    user.real_name = "管理员"
    user.is_superuser = is_superuser
    return user


def _make_project(project_id=1):
    p = MagicMock()
    p.id = project_id
    p.project_code = f"P{project_id:04d}"
    p.project_name = "比亚迪ADAS ICT测试系统"
    p.customer_id = 1
    p.pm_id = 1
    p.budget_amount = 320000.0
    p.actual_cost = 100000.0
    p.is_active = True
    p.customer = None
    p.manager = None
    p.customer_name = "比亚迪"
    p.pm_name = "张三"
    p.salesperson_id = 2
    p.stage = "S1"
    p.status = "ST01"
    p.health = "H1"
    p.project_type = "ICT"
    p.progress_pct = 30.0
    p.created_at = None
    return p


# ──────────────────────────────────────────────
# Tests: create_project
# ──────────────────────────────────────────────

class TestCreateProject:

    @patch("app.utils.project_utils.init_project_stages")
    @patch("app.utils.db_helpers.save_obj")
    def test_create_project_success(self, mock_save, mock_init_stages):
        """正常创建项目"""
        from app.api.v1.endpoints.projects.project_crud import create_project

        db = _make_db()
        current_user = _make_user()

        db.query.return_value.filter.return_value.first.return_value = None
        customer_mock = MagicMock(
            customer_name="比亚迪",
            contact_person="李四",
            contact_phone="13800000000"
        )
        pm_mock = MagicMock(real_name="张三", username="zhangsan")
        db.query.return_value.get.side_effect = [customer_mock, pm_mock]

        project_in = MagicMock()
        project_in.project_code = _P0001
        project_in.model_dump.return_value = {
            "project_code": _P0001,
            "project_name": "比亚迪ADAS ICT测试系统",
            "customer_id": 1,
            "pm_id": 1,
        }

        with patch("app.api.v1.endpoints.projects.project_crud.Project") as MockProject:
            mock_proj_instance = _make_project()
            MockProject.return_value = mock_proj_instance

            result = create_project(db=db, project_in=project_in, current_user=current_user)

        mock_save.assert_called_once()
        mock_init_stages.assert_called_once()

    @patch("app.utils.project_utils.init_project_stages")
    @patch("app.utils.db_helpers.save_obj")
    def test_create_project_duplicate_code_raises(self, mock_save, mock_init_stages):
        """重复项目编码应抛出400"""
        from app.api.v1.endpoints.projects.project_crud import create_project

        db = _make_db()
        current_user = _make_user()

        db.query.return_value.filter.return_value.first.return_value = _make_project()

        project_in = MagicMock()
        project_in.project_code = _P0001
        project_in.model_dump.return_value = {"project_code": _P0001}

        with pytest.raises(HTTPException) as exc_info:
            create_project(db=db, project_in=project_in, current_user=current_user)

        assert exc_info.value.status_code == 400

    @patch("app.utils.project_utils.init_project_stages")
    @patch("app.utils.db_helpers.save_obj")
    def test_create_project_no_customer(self, mock_save, mock_init_stages):
        """无customer_id时也能正常创建"""
        from app.api.v1.endpoints.projects.project_crud import create_project

        db = _make_db()
        current_user = _make_user()

        db.query.return_value.filter.return_value.first.return_value = None
        db.query.return_value.get.return_value = None

        project_in = MagicMock()
        project_in.project_code = _P0002
        project_in.model_dump.return_value = {
            "project_code": _P0002,
            "project_name": "无客户项目",
            "customer_id": None,
            "pm_id": None,
        }

        with patch("app.api.v1.endpoints.projects.project_crud.Project") as MockProject:
            mock_proj_instance = _make_project(2)
            mock_proj_instance.customer_id = None
            mock_proj_instance.pm_id = None
            MockProject.return_value = mock_proj_instance

            result = create_project(db=db, project_in=project_in, current_user=current_user)

        mock_save.assert_called_once()


# ──────────────────────────────────────────────
# Tests: update_project
# ──────────────────────────────────────────────

class TestUpdateProject:

    def test_update_project_success(self):
        """正常更新项目字段"""
        from app.api.v1.endpoints.projects.project_crud import update_project

        db = _make_db()
        current_user = _make_user()
        project = _make_project()

        with patch("app.utils.permission_helpers.check_project_access_or_raise", return_value=project), \
             patch("app.services.cache_service.CacheService", MagicMock()):
            project_in = MagicMock()
            project_in.model_dump.return_value = {"project_name": "更新后的名称"}

            result = update_project(
                db=db,
                project_id=1,
                project_in=project_in,
                current_user=current_user,
            )

        assert db.add.called
        assert db.commit.called

    def test_update_project_not_found(self):
        """项目不存在时抛出404"""
        from app.api.v1.endpoints.projects.project_crud import update_project

        db = _make_db()
        current_user = _make_user()

        with patch(
            "app.utils.permission_helpers.check_project_access_or_raise",
            side_effect=HTTPException(status_code=404, detail="项目不存在")
        ):
            project_in = MagicMock()
            project_in.model_dump.return_value = {}

            with pytest.raises(HTTPException) as exc_info:
                update_project(db=db, project_id=999, project_in=project_in, current_user=current_user)

        assert exc_info.value.status_code == 404

    def test_update_project_with_customer_update(self):
        """更新 customer_id 时同步冗余字段"""
        from app.api.v1.endpoints.projects.project_crud import update_project

        db = _make_db()
        current_user = _make_user()
        project = _make_project()
        project.customer_id = 2

        customer_mock = MagicMock(
            customer_name="新客户",
            contact_person="王五",
            contact_phone="13900000000"
        )
        db.query.return_value.get.return_value = customer_mock

        with patch("app.utils.permission_helpers.check_project_access_or_raise", return_value=project), \
             patch("app.services.cache_service.CacheService", MagicMock()):
            project_in = MagicMock()
            project_in.model_dump.return_value = {"customer_id": 2}

            result = update_project(db=db, project_id=1, project_in=project_in, current_user=current_user)

        assert db.commit.called


# ──────────────────────────────────────────────
# Tests: delete_project
# ──────────────────────────────────────────────

class TestDeleteProject:

    def test_delete_project_success(self):
        """正常软删除项目"""
        from app.api.v1.endpoints.projects.project_crud import delete_project

        db = _make_db()
        current_user = _make_user()
        project = _make_project()

        with patch("app.utils.permission_helpers.check_project_access_or_raise", return_value=project), \
             patch("app.services.cache_service.CacheService", MagicMock()):
            result = delete_project(db=db, project_id=1, current_user=current_user)

        assert project.is_active is False
        assert db.commit.called
        assert result.code == 200

    def test_delete_project_no_permission(self):
        """无权限时应抛出403"""
        from app.api.v1.endpoints.projects.project_crud import delete_project

        db = _make_db()
        current_user = _make_user(is_superuser=False)

        with patch(
            "app.utils.permission_helpers.check_project_access_or_raise",
            side_effect=HTTPException(status_code=403, detail="您没有权限删除该项目")
        ):
            with pytest.raises(HTTPException) as exc_info:
                delete_project(db=db, project_id=1, current_user=current_user)

        assert exc_info.value.status_code == 403

    def test_delete_project_sets_inactive(self):
        """确认软删除将 is_active 置为 False"""
        from app.api.v1.endpoints.projects.project_crud import delete_project

        db = _make_db()
        current_user = _make_user()
        project = _make_project()
        project.is_active = True

        with patch("app.utils.permission_helpers.check_project_access_or_raise", return_value=project), \
             patch("app.services.cache_service.CacheService", MagicMock()):
            delete_project(db=db, project_id=1, current_user=current_user)

        assert project.is_active is False


# ──────────────────────────────────────────────
# Tests: read_project
# ──────────────────────────────────────────────

class TestReadProject:

    def test_read_project_not_found(self):
        """项目不存在时抛出404"""
        from app.api.v1.endpoints.projects.project_crud import read_project

        db = _make_db()
        current_user = _make_user()

        with patch("app.utils.permission_helpers.check_project_access_or_raise", return_value=None):
            db.query.return_value.options.return_value.filter.return_value.first.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                read_project(db=db, project_id=999, use_cache=False, current_user=current_user)

        assert exc_info.value.status_code == 404

    def test_read_project_success(self):
        """正常读取项目详情"""
        from app.api.v1.endpoints.projects.project_crud import read_project

        db = _make_db()
        current_user = _make_user()
        project = _make_project()
        project.machines = MagicMock()
        project.machines.all = MagicMock(return_value=[])
        project.milestones = MagicMock()
        project.milestones.all = MagicMock(return_value=[])

        db.query.return_value.options.return_value.filter.return_value.all.return_value = []
        db.query.return_value.options.return_value.filter.return_value.first.return_value = project

        with patch("app.utils.permission_helpers.check_project_access_or_raise", return_value=None), \
             patch("app.api.v1.endpoints.projects.project_crud.ProjectResponse") as MockPR, \
             patch("app.api.v1.endpoints.projects.project_crud.ProjectDetailResponse") as MockPD:
            mock_pr = MagicMock()
            mock_pr.model_dump.return_value = {"id": 1}
            MockPR.model_validate.return_value = mock_pr
            MockPD.return_value = MagicMock()

            result = read_project(db=db, project_id=1, use_cache=False, current_user=current_user)

        assert result is not None
