import importlib
import importlib.util
import sys
from datetime import date, datetime
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Generic, TypeVar

import pytest
from fastapi import HTTPException
from pydantic import BaseModel


def _load_module_from_path(module_name, relative_path):
    root = Path(__file__).resolve().parents[2]
    module_path = root / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_serialize_project_status_log_returns_full_payload(monkeypatch):
    project_mod = ModuleType("app.models.project")
    project_mod.ProjectStatusLog = object
    monkeypatch.setitem(sys.modules, "app.models.project", project_mod)

    module = _load_module_from_path(
        "app.api.v1.endpoints.projects.serialization",
        "app/api/v1/endpoints/projects/serialization.py",
    )

    log = SimpleNamespace(
        id=1,
        project_id=2,
        old_stage="设计",
        new_stage="生产",
        old_status="OPEN",
        new_status="DONE",
        old_health="YELLOW",
        new_health="GREEN",
        change_type="manual",
        change_reason="推进",
        changed_by=9,
        changed_at=datetime(2026, 4, 14, 7, 0, 0),
        created_at=None,
    )

    result = module._serialize_project_status_log(log)

    assert result["id"] == 1
    assert result["changed_at"] == "2026-04-14T07:00:00"
    assert result["created_at"] is None


def test_paginated_result_pages_returns_zero_for_non_positive_page_size():
    module = _load_module_from_path("app.common.crud.types", "app/common/crud/types.py")
    result = module.PaginatedResult.model_construct(items=[], total=10, page=1, page_size=0)

    assert result.pages == 0


def test_project_machine_ensure_project_exists_raises_not_found(monkeypatch):
    deps_mod = ModuleType("app.api.deps")
    deps_mod.get_db = lambda: None
    monkeypatch.setitem(sys.modules, "app.api.deps", deps_mod)

    crud_mod = ModuleType("app.common.crud")
    crud_mod.QueryParams = object
    monkeypatch.setitem(sys.modules, "app.common.crud", crud_mod)

    core_mod = ModuleType("app.core")
    core_mod.security = SimpleNamespace(require_permission=lambda _perm: (lambda: None))
    monkeypatch.setitem(sys.modules, "app.core", core_mod)

    class _Field:
        def __eq__(self, other):
            return ("eq", other)

    project_mod = ModuleType("app.models.project")
    project_mod.Project = SimpleNamespace(id=_Field())
    monkeypatch.setitem(sys.modules, "app.models.project", project_mod)

    user_mod = ModuleType("app.models.user")
    user_mod.User = object
    monkeypatch.setitem(sys.modules, "app.models.user", user_mod)

    common_schema_mod = ModuleType("app.schemas.common")
    T = TypeVar("T")

    class _PaginatedResponse(BaseModel, Generic[T]):
        items: list = []
        total: int = 0
        page: int = 1
        page_size: int = 20
        pages: int = 0

    common_schema_mod.PaginatedResponse = _PaginatedResponse
    monkeypatch.setitem(sys.modules, "app.schemas.common", common_schema_mod)

    project_schema_mod = ModuleType("app.schemas.project")

    class MachineCreate(BaseModel):
        name: str = "demo"

    class MachineResponse(BaseModel):
        id: int = 1

    class MachineUpdate(BaseModel):
        name: str = "demo"

    project_schema_mod.MachineCreate = MachineCreate
    project_schema_mod.MachineResponse = MachineResponse
    project_schema_mod.MachineUpdate = MachineUpdate
    monkeypatch.setitem(sys.modules, "app.schemas.project", project_schema_mod)

    service_mod = ModuleType("app.services.project")

    class ProjectMachineService:
        def __init__(self, db=None, project_id=None):
            self.db = db
            self.project_id = project_id

    service_mod.ProjectMachineService = ProjectMachineService
    monkeypatch.setitem(sys.modules, "app.services.project", service_mod)

    perm_mod = ModuleType("app.utils.permission_helpers")
    perm_mod.check_project_access_or_raise = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, "app.utils.permission_helpers", perm_mod)

    module = _load_module_from_path(
        "app.api.v1.endpoints.projects.machines.crud",
        "app/api/v1/endpoints/projects/machines/crud.py",
    )

    class FakeQuery:
        def filter(self, *args):
            return self

        def first(self):
            return None

    class FakeDB:
        def query(self, _model):
            return FakeQuery()

    with pytest.raises(HTTPException) as exc:
        module._ensure_project_exists(FakeDB(), 1)

    assert exc.value.detail == "项目不存在"


def test_project_work_logs_builds_items_from_logs(monkeypatch):
    deps_mod = ModuleType("app.api.deps")
    deps_mod.get_db = lambda: None
    monkeypatch.setitem(sys.modules, "app.api.deps", deps_mod)

    pagination_mod = ModuleType("app.common.pagination")

    class PaginationParams:
        offset = 0
        limit = 20

    pagination_mod.PaginationParams = PaginationParams
    pagination_mod.get_pagination_query = lambda: PaginationParams()
    monkeypatch.setitem(sys.modules, "app.common.pagination", pagination_mod)

    core_mod = ModuleType("app.core")
    core_mod.security = SimpleNamespace(require_permission=lambda _perm: (lambda: None))
    monkeypatch.setitem(sys.modules, "app.core", core_mod)

    user_mod = ModuleType("app.models.user")
    user_mod.User = object
    monkeypatch.setitem(sys.modules, "app.models.user", user_mod)

    class _Field:
        def __eq__(self, other):
            return ("eq", other)

        def __ge__(self, other):
            return ("ge", other)

        def __le__(self, other):
            return ("le", other)

    work_log_mod = ModuleType("app.models.work_log")
    work_log_mod.WorkLog = SimpleNamespace(id=_Field(), work_date=_Field(), created_at=_Field())
    work_log_mod.WorkLogMention = SimpleNamespace(work_log_id=_Field(), mention_type=_Field(), mention_id=_Field())
    monkeypatch.setitem(sys.modules, "app.models.work_log", work_log_mod)

    common_schema_mod = ModuleType("app.schemas.common")
    common_schema_mod.ResponseModel = lambda **kwargs: kwargs
    monkeypatch.setitem(sys.modules, "app.schemas.common", common_schema_mod)

    service_mod = ModuleType("app.services.project_statistics_service")
    service_mod.WorkLogStatisticsService = object
    monkeypatch.setitem(sys.modules, "app.services.project_statistics_service", service_mod)

    perm_mod = ModuleType("app.utils.permission_helpers")
    perm_mod.check_project_access_or_raise = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, "app.utils.permission_helpers", perm_mod)

    module = _load_module_from_path(
        "app.api.v1.endpoints.projects.work_logs.crud",
        "app/api/v1/endpoints/projects/work_logs/crud.py",
    )
    module.desc = lambda value: value

    log = SimpleNamespace(
        id=1,
        user_id=2,
        user_name="测试员",
        work_date=date(2026, 4, 14),
        content="完成联调",
        status="DONE",
        created_at=datetime(2026, 4, 14, 7, 0, 0),
    )

    class FakeQuery:
        def join(self, *args):
            return self

        def filter(self, *args):
            return self

        def count(self):
            return 1

        def order_by(self, *args):
            return self

        def offset(self, _value):
            return self

        def limit(self, _value):
            return self

        def all(self):
            return [log]

    class FakeDB:
        def query(self, _model):
            return FakeQuery()

    result = module.list_project_work_logs(
        project_id=1,
        db=FakeDB(),
        start_date=None,
        end_date=None,
        pagination=PaginationParams(),
        current_user=object(),
    )

    assert result["data"]["items"][0]["content"] == "完成联调"
    assert result["data"]["total"] == 1
