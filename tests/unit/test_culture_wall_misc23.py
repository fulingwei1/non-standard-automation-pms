# -*- coding: utf-8 -*-
"""MISC-23: culture wall config/goals/content CRUD contracts."""

from pathlib import Path

from app.api.v1.endpoints.culture_wall import router as culture_wall_router
from app.api.v1.endpoints.culture_wall import contents as content_endpoints
from app.api.v1.endpoints import culture_wall_config
from app.models.culture_wall import CultureWallContent, CultureWallReadRecord
from app.models.culture_wall_config import CultureWallConfig
from app.schemas.culture_wall import CultureWallContentCreate, CultureWallContentUpdate
from app.schemas.culture_wall_config import CultureWallConfigCreate, CultureWallConfigUpdate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


ROOT = Path(__file__).resolve().parents[2]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


class _User:
    id = 901
    real_name = "测试用户"
    role_codes = ["admin"]


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    for table in (
        CultureWallConfig.__table__,
        CultureWallContent.__table__,
        CultureWallReadRecord.__table__,
    ):
        table.create(bind=engine)
    return sessionmaker(bind=engine)()


def _route_methods_and_paths(router):
    return {
        (method, route.path)
        for route in router.routes
        for method in getattr(route, "methods", set())
    }


def test_culture_wall_config_route_is_real_crud_not_placeholder():
    source = read_text("app/api/v1/endpoints/culture_wall_config.py")
    route_contracts = _route_methods_and_paths(culture_wall_config.router)

    assert "module placeholder" not in source
    assert ("GET", "/") in route_contracts
    assert ("POST", "/") in route_contracts
    assert ("PUT", "/{config_id}") in route_contracts
    assert ("DELETE", "/{config_id}") in route_contracts


def test_culture_wall_content_update_delete_and_prefixed_goal_routes_are_mounted():
    route_contracts = _route_methods_and_paths(culture_wall_router)

    assert ("GET", "/contents") in route_contracts
    assert ("POST", "/contents") in route_contracts
    assert ("PUT", "/contents/{content_id}") in route_contracts
    assert ("DELETE", "/contents/{content_id}") in route_contracts
    assert ("GET", "/personal-goals") in route_contracts
    assert ("POST", "/personal-goals") in route_contracts
    assert ("PUT", "/personal-goals/{goal_id}") in route_contracts


def test_frontend_culture_wall_api_uses_registered_backend_paths():
    source = read_text("frontend/src/services/api/admin.js")
    workstation_sources = [
        read_text("frontend/src/pages/ChairmanWorkstation.jsx"),
        read_text("frontend/src/pages/gm-workstation/GeneralManagerWorkstation.jsx"),
    ]

    assert 'api.get("/culture-wall/summary")' in source
    assert 'api.put(`/culture-wall/contents/${id}`, data)' in source
    assert 'api.post(`/culture-wall/contents/${id}/review`, data)' in source
    assert 'api.delete(`/culture-wall/contents/${id}`)' in source
    assert 'api.get("/culture-wall/personal-goals"' in source
    assert 'api.post("/culture-wall/personal-goals"' in source
    assert 'api.put(`/culture-wall/personal-goals/${id}`, data)' in source
    assert 'api.get("/personal-goals"' not in source
    assert 'api.post("/personal-goals"' not in source
    assert 'api.put(`/personal-goals/${id}`' not in source
    assert all('"/personal-goals"' not in item for item in workstation_sources)
    assert all("'/personal-goals'" not in item for item in workstation_sources)


def test_culture_wall_content_update_delete_flow_persists_to_db():
    db = _make_session()
    user = _User()

    created = content_endpoints.create_culture_wall_content(
        CultureWallContentCreate(
            content_type="NOTICE",
            title="原始标题",
            content="原始内容",
            is_published=False,
        ),
        db=db,
        current_user=user,
    )
    updated = content_endpoints.update_culture_wall_content(
        created.id,
        CultureWallContentUpdate(title="更新标题"),
        db=db,
        current_user=user,
    )

    assert updated.title == "更新标题"
    assert updated.is_published is False
    assert db.query(CultureWallContent).filter_by(id=created.id).one().title == "更新标题"

    db.add(CultureWallReadRecord(content_id=created.id, user_id=user.id, read_at=updated.updated_at))
    db.commit()
    content_endpoints.delete_culture_wall_content(
        created.id,
        db=db,
        current_user=user,
    )

    assert db.query(CultureWallContent).filter_by(id=created.id).first() is None
    assert db.query(CultureWallReadRecord).filter_by(content_id=created.id).count() == 0


def test_culture_wall_config_crud_flow_persists_defaults_and_updates():
    db = _make_session()
    user = _User()

    first = culture_wall_config.create_culture_wall_config(
        CultureWallConfigCreate(config_name="默认配置A", is_default=True),
        db=db,
        current_user=user,
    )
    second = culture_wall_config.create_culture_wall_config(
        CultureWallConfigCreate(config_name="默认配置B", is_default=True),
        db=db,
        current_user=user,
    )
    updated = culture_wall_config.update_culture_wall_config(
        second.id,
        CultureWallConfigUpdate(description="给文化墙轮播使用", visible_roles=["admin"]),
        db=db,
        current_user=user,
    )

    assert db.query(CultureWallConfig).filter_by(id=first.id).one().is_default is False
    assert db.query(CultureWallConfig).filter_by(id=second.id).one().is_default is True
    assert updated.description == "给文化墙轮播使用"
    assert updated.visible_roles == ["admin"]

    culture_wall_config.delete_culture_wall_config(
        second.id,
        db=db,
        current_user=user,
    )
    assert db.query(CultureWallConfig).filter_by(id=second.id).first() is None
