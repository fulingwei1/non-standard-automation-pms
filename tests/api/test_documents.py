# -*- coding: utf-8 -*-
"""
文档管理模块 API 测试

测试项目文档的 CRUD 操作、下载和版本管理
"""

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _unwrap_data(payload):
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


def _unwrap_items(payload):
    payload = _unwrap_data(payload)
    if isinstance(payload, dict) and "items" in payload:
        return payload["items"]
    return payload if isinstance(payload, list) else []


def _get_first_project(client: TestClient, token: str) -> dict:
    """获取第一个可用的项目"""
    headers = _auth_headers(token)
    response = client.get(f"{settings.API_V1_PREFIX}/projects/", headers=headers)

    if response.status_code != 200:
        return None

    items = _unwrap_items(response.json())
    if not items:
        return None

    return items[0]


def _build_document_payload(project_id: int | None = None, **overrides) -> dict:
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "doc_type": "DESIGN",
        "doc_category": "API_TEST",
        "doc_name": f"测试文档-{suffix}",
        "doc_no": f"DOC-{suffix.upper()}",
        "version": "1.0",
        "file_path": f"api-tests/{suffix}.txt",
        "file_name": f"document-{suffix}.txt",
        "description": "API 自动化测试文档",
    }
    if project_id is not None:
        payload["project_id"] = project_id
    payload.update(overrides)
    return payload


def _create_document(client: TestClient, token: str, project_id: int, **overrides) -> dict:
    headers = _auth_headers(token)
    payload = _build_document_payload(project_id=project_id, **overrides)
    response = client.post(f"{settings.API_V1_PREFIX}/documents/", json=payload, headers=headers)
    assert response.status_code in [200, 201], response.text
    return _unwrap_data(response.json())


def _write_document_file(relative_path: str, content: str = "test document") -> Path:
    file_path = Path(settings.UPLOAD_DIR) / "documents" / relative_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return file_path


class TestDocumentCRUD:
    """文档 CRUD 测试"""

    def test_list_documents(self, client: TestClient, admin_token: str):
        """测试获取文档列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/documents/",
            params={"page": 1, "page_size": 10},
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_list_documents_with_project_filter(self, client: TestClient, admin_token: str):
        """测试按项目筛选文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/documents/",
            params={"project_id": project["id"]},
            headers=headers,
        )

        assert response.status_code == 200

    def test_list_documents_by_project(self, client: TestClient, admin_token: str):
        """测试获取项目的文档列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/documents/projects/{project['id']}/documents",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
        if isinstance(data, dict):
            assert "items" in data or "data" in data

    def test_create_document(self, client: TestClient, admin_token: str):
        """测试创建文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        doc_data = _build_document_payload(project_id=project["id"])

        response = client.post(
            f"{settings.API_V1_PREFIX}/documents/", json=doc_data, headers=headers
        )

        assert response.status_code in [200, 201], response.text
        data = _unwrap_data(response.json())
        assert data["project_id"] == project["id"]
        assert data["doc_name"] == doc_data["doc_name"]
        assert data["doc_no"] == doc_data["doc_no"]

    def test_create_document_for_project(self, client: TestClient, admin_token: str):
        """测试为项目创建文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        doc_data = _build_document_payload(doc_type="MANUAL")

        response = client.post(
            f"{settings.API_V1_PREFIX}/documents/projects/{project['id']}/documents",
            json=doc_data,
            headers=headers,
        )

        assert response.status_code in [200, 201], response.text
        data = _unwrap_data(response.json())
        assert data["project_id"] == project["id"]
        assert data["doc_type"] == "MANUAL"

    def test_get_document_by_id(self, client: TestClient, admin_token: str):
        """测试根据 ID 获取文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        created = _create_document(client, admin_token, project["id"])

        response = client.get(f"{settings.API_V1_PREFIX}/documents/{created['id']}", headers=headers)

        assert response.status_code == 200
        data = _unwrap_data(response.json())
        assert data["id"] == created["id"]
        assert data["doc_name"] == created["doc_name"]

    def test_get_document_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(f"{settings.API_V1_PREFIX}/documents/99999", headers=headers)

        assert response.status_code == 404

    def test_update_document(self, client: TestClient, admin_token: str):
        """测试更新文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        created = _create_document(client, admin_token, project["id"])

        update_data = {
            "doc_name": f"更新文档-{uuid.uuid4().hex[:4]}",
            "version": "2.0",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/documents/{created['id']}", json=update_data, headers=headers
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["id"] == created["id"]
        assert data["doc_name"] == update_data["doc_name"]
        assert data["version"] == "2.0"


class TestDocumentVersions:
    """文档版本测试"""

    def test_get_document_versions(self, client: TestClient, admin_token: str):
        """测试获取文档版本列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        doc_no = f"DOC-{uuid.uuid4().hex[:8].upper()}"
        first = _create_document(client, admin_token, project["id"], doc_no=doc_no, version="1.0")
        _create_document(client, admin_token, project["id"], doc_no=doc_no, version="2.0")

        response = client.get(
            f"{settings.API_V1_PREFIX}/documents/{first['id']}/versions", headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        assert {item["version"] for item in data} >= {"1.0", "2.0"}


class TestDocumentDownload:
    """文档下载测试"""

    def test_download_document(self, client: TestClient, admin_token: str):
        """测试下载文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        relative_path = f"api-tests/{uuid.uuid4().hex[:8]}.txt"
        expected_content = "downloadable test document"
        _write_document_file(relative_path, expected_content)
        created = _create_document(
            client,
            admin_token,
            project["id"],
            file_path=relative_path,
            file_name="download-test.txt",
        )

        response = client.get(
            f"{settings.API_V1_PREFIX}/documents/{created['id']}/download", headers=headers
        )

        assert response.status_code == 200, response.text
        assert response.content.decode("utf-8") == expected_content


class TestDocumentDelete:
    """文档删除测试"""

    def test_delete_document_not_found(self, client: TestClient, admin_token: str):
        """测试删除不存在的文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.delete(f"{settings.API_V1_PREFIX}/documents/99999", headers=headers)

        assert response.status_code in [404, 403]  # 可能返回403如果没有权限
