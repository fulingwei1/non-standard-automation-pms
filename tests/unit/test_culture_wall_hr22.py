# -*- coding: utf-8 -*-
"""HR-22: culture wall publishing must go through review."""

from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.endpoints.culture_wall import contents as content_endpoints
from app.api.v1.endpoints.culture_wall import router as culture_wall_router
from app.common.pagination import PaginationParams
from app.models.culture_wall import CultureWallContent, CultureWallReadRecord
from app.models.culture_wall_config import CultureWallConfig
from app.schemas.culture_wall import (
    CultureWallContentCreate,
    CultureWallContentReview,
    CultureWallContentUpdate,
)


ROOT = Path(__file__).resolve().parents[2]


class _User:
    id = 902
    real_name = "审核人"
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


def test_content_cannot_self_publish_and_requires_review_endpoint():
    db = _make_session()
    user = _User()

    created = content_endpoints.create_culture_wall_content(
        CultureWallContentCreate(
            content_type="NOTICE",
            title="待审公告",
            content="创建人即使勾选发布也不能直接上墙",
            is_published=True,
        ),
        db=db,
        current_user=user,
    )
    updated = content_endpoints.update_culture_wall_content(
        created.id,
        CultureWallContentUpdate(is_published=True, title="仍需审核"),
        db=db,
        current_user=user,
    )

    assert created.is_published is False
    assert created.published_by is None
    assert updated.is_published is False
    assert updated.published_by is None

    reviewed = content_endpoints.review_culture_wall_content(
        created.id,
        CultureWallContentReview(approved=True, review_note="同意发布"),
        db=db,
        current_user=user,
    )

    assert reviewed.is_published is True
    assert reviewed.published_by == user.id
    assert reviewed.published_by_name == user.real_name
    assert reviewed.publish_date is not None


def test_content_list_uses_real_read_records_instead_of_false_constant():
    db = _make_session()
    user = _User()
    content = CultureWallContent(
        content_type="NOTICE",
        title="已读公告",
        content="content",
        is_published=True,
        created_by=user.id,
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    db.add(
        CultureWallReadRecord(
            content_id=content.id,
            user_id=user.id,
            read_at=datetime.now(),
        )
    )
    db.commit()

    result = content_endpoints.read_culture_wall_contents(
        db=db,
        pagination=PaginationParams(page=1, page_size=20, offset=0, limit=20),
        content_type=None,
        is_published=None,
        keyword=None,
        current_user=user,
    )

    assert result.items[0].id == content.id
    assert result.items[0].is_read is True


def test_review_route_and_frontend_contract_are_registered():
    route_contracts = _route_methods_and_paths(culture_wall_router)
    admin_api = (ROOT / "frontend/src/services/api/admin.js").read_text(encoding="utf-8")

    assert ("POST", "/contents/{content_id}/review") in route_contracts
    assert 'api.post(`/culture-wall/contents/${id}/review`, data)' in admin_api
