# -*- coding: utf-8 -*-
"""RD project route aliases should not redirect the browser across origins."""

from fastapi.testclient import TestClient

from app.core.config import settings


def test_rd_project_list_without_trailing_slash_does_not_redirect(
    client: TestClient, admin_token: str
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/rd-projects",
        headers={"Authorization": f"Bearer {admin_token}"},
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
