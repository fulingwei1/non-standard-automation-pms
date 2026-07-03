# -*- coding: utf-8 -*-
"""Role template workflow contracts used by Role Management."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import ApiPermission, Role, RoleApiPermission, RoleTemplate, UserRole


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _unwrap_data(response) -> dict | list:
    body = response.json()
    return body.get("data", body)


def _ensure_permission(db: Session, code: str, name: str) -> tuple[ApiPermission, bool]:
    permission = db.query(ApiPermission).filter(ApiPermission.perm_code == code).first()
    if permission:
        return permission, False

    permission = ApiPermission(
        perm_code=code,
        perm_name=name,
        module=code.split(":", 1)[0],
        action=code.split(":", 1)[1] if ":" in code else "read",
        is_system=True,
        is_active=True,
    )
    db.add(permission)
    db.flush()
    return permission, True


def _cleanup(
    db: Session,
    *,
    role_codes: list[str],
    template_codes: list[str],
    permission_id: int | None = None,
) -> None:
    role_ids = [row[0] for row in db.query(Role.id).filter(Role.role_code.in_(role_codes)).all()]
    template_ids = [
        row[0]
        for row in db.query(RoleTemplate.id).filter(RoleTemplate.template_code.in_(template_codes)).all()
    ]

    if role_ids:
        db.query(RoleApiPermission).filter(RoleApiPermission.role_id.in_(role_ids)).delete(
            synchronize_session=False
        )
        db.query(UserRole).filter(UserRole.role_id.in_(role_ids)).delete(synchronize_session=False)
        db.query(Role).filter(Role.id.in_(role_ids)).delete(synchronize_session=False)
    if template_ids:
        db.query(RoleTemplate).filter(RoleTemplate.id.in_(template_ids)).delete(
            synchronize_session=False
        )
    if permission_id is not None:
        db.query(RoleApiPermission).filter(RoleApiPermission.permission_id == permission_id).delete(
            synchronize_session=False
        )
        db.query(ApiPermission).filter(ApiPermission.id == permission_id).delete(
            synchronize_session=False
        )
    db.commit()


def test_role_template_crud_round_trip(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    template_code = f"QA_TPL_{suffix}"
    headers = _auth_headers(admin_token)

    _cleanup(db_session, role_codes=[], template_codes=[template_code])
    permission, created_permission = _ensure_permission(
        db_session,
        f"qa:template:{suffix}",
        "角色模板测试权限",
    )
    db_session.commit()

    try:
        create_response = client.post(
            f"{settings.API_V1_PREFIX}/roles/templates/",
            json={
                "template_code": template_code,
                "template_name": "QA角色模板",
                "description": "template workflow contract",
                "data_scope": "PROJECT",
                "permission_codes": [permission.perm_code],
            },
            headers=headers,
        )
        assert create_response.status_code == 201, create_response.text
        created = _unwrap_data(create_response)
        assert created["template_code"] == template_code
        assert created["permission_codes"] == [permission.perm_code]
        assert created["version"] == 1

        list_response = client.get(f"{settings.API_V1_PREFIX}/roles/templates", headers=headers)
        assert list_response.status_code == 200, list_response.text
        listed = _unwrap_data(list_response)
        matched = next(item for item in listed if item["template_code"] == template_code)
        assert matched["permission_codes"] == [permission.perm_code]

        detail_response = client.get(
            f"{settings.API_V1_PREFIX}/roles/templates/{created['id']}",
            headers=headers,
        )
        assert detail_response.status_code == 200, detail_response.text
        detail = _unwrap_data(detail_response)
        assert detail["template_code"] == template_code
        assert detail["permission_codes"] == [permission.perm_code]

        update_response = client.put(
            f"{settings.API_V1_PREFIX}/roles/templates/{created['id']}",
            json={
                "template_name": "QA角色模板-更新",
                "description": "updated",
                "permission_codes": [],
                "version_note": "contract update",
            },
            headers=headers,
        )
        assert update_response.status_code == 200, update_response.text
        updated = _unwrap_data(update_response)
        assert updated["template_name"] == "QA角色模板-更新"
        assert updated["permission_codes"] == []
        assert updated["version"] == 2

        delete_response = client.delete(
            f"{settings.API_V1_PREFIX}/roles/templates/{created['id']}",
            headers=headers,
        )
        assert delete_response.status_code == 200, delete_response.text

        missing_response = client.get(
            f"{settings.API_V1_PREFIX}/roles/templates/{created['id']}",
            headers=headers,
        )
        assert missing_response.status_code == 404
    finally:
        _cleanup(
            db_session,
            role_codes=[],
            template_codes=[template_code],
            permission_id=permission.id if created_permission else None,
        )


def test_role_can_be_saved_as_template_and_recreated_from_template(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    source_role_code = f"QA_TPL_SRC_{suffix}"
    created_role_code = f"QA_TPL_ROLE_{suffix}"
    template_code = f"QA_TPL_SAVE_{suffix}"
    headers = _auth_headers(admin_token)

    _cleanup(
        db_session,
        role_codes=[source_role_code, created_role_code],
        template_codes=[template_code],
    )
    permission, created_permission = _ensure_permission(db_session, "user:read", "查看用户")
    db_session.commit()

    try:
        role_response = client.post(
            f"{settings.API_V1_PREFIX}/roles/",
            json={
                "role_code": source_role_code,
                "role_name": "QA模板来源角色",
                "description": "source role",
                "data_scope": "PROJECT",
                "permission_ids": [permission.id],
            },
            headers=headers,
        )
        assert role_response.status_code == 201, role_response.text
        source_role = _unwrap_data(role_response)

        save_response = client.post(
            f"{settings.API_V1_PREFIX}/roles/{source_role['id']}/save-as-template",
            json={
                "template_code": template_code,
                "template_name": "QA另存模板",
                "description": "saved from source role",
            },
            headers=headers,
        )
        assert save_response.status_code == 201, save_response.text
        template = _unwrap_data(save_response)
        assert template["template_code"] == template_code
        assert template["permission_codes"] == ["user:read"]
        assert template["source_role_id"] == source_role["id"]

        create_role_response = client.post(
            f"{settings.API_V1_PREFIX}/roles/templates/{template['id']}/create-role",
            json={
                "role_code": created_role_code,
                "role_name": "QA模板创建角色",
                "description": "created from template",
            },
            headers=headers,
        )
        assert create_role_response.status_code == 201, create_role_response.text
        created_role = _unwrap_data(create_role_response)
        assert created_role["role_code"] == created_role_code
        assert created_role["source_template_id"] == template["id"]

        permissions_response = client.get(
            f"{settings.API_V1_PREFIX}/permissions/roles/{created_role['id']}",
            headers=headers,
        )
        assert permissions_response.status_code == 200, permissions_response.text
        permissions = _unwrap_data(permissions_response)["permissions"]
        assert [item["permission_code"] for item in permissions] == ["user:read"]

        delete_created_role_response = client.delete(
            f"{settings.API_V1_PREFIX}/roles/{created_role['id']}",
            headers=headers,
        )
        assert delete_created_role_response.status_code == 200, delete_created_role_response.text

        delete_source_role_response = client.delete(
            f"{settings.API_V1_PREFIX}/roles/{source_role['id']}",
            headers=headers,
        )
        assert delete_source_role_response.status_code == 200, delete_source_role_response.text

        delete_template_response = client.delete(
            f"{settings.API_V1_PREFIX}/roles/templates/{template['id']}",
            headers=headers,
        )
        assert delete_template_response.status_code == 200, delete_template_response.text
    finally:
        _cleanup(
            db_session,
            role_codes=[source_role_code, created_role_code],
            template_codes=[template_code],
            permission_id=permission.id if created_permission else None,
        )
