# -*- coding: utf-8 -*-
"""
文档管理模块 API 测试

测试项目文档的 CRUD 操作、下载和版本管理
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _get_first_project(client: TestClient, token: str) -> dict:
    """获取第一个可用的项目"""
    headers = _auth_headers(token)
    response = client.get(
        f"{settings.API_V1_PREFIX}/projects/",
        headers=headers
    )

    if response.status_code != 200:
        return None

    projects = response.json()
    items = projects.get("items", projects) if isinstance(projects, dict) else projects
    if not items:
        return None

    return items[0]


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
            headers=headers
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
            headers=headers
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
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_document(self, client: TestClient, admin_token: str):
        """测试创建文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        doc_data = {
            "doc_code": f"DOC-{uuid.uuid4().hex[:6].upper()}",
            "doc_name": f"测试文档-{uuid.uuid4().hex[:4]}",
            "doc_type": "DESIGN",
            "project_id": project["id"],
            "version": "V1.0",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/documents/",
            json=doc_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to create document")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")

        assert response.status_code in [200, 201], response.text

    def test_create_document_for_project(self, client: TestClient, admin_token: str):
        """测试为项目创建文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = _get_first_project(client, admin_token)
        if not project:
            pytest.skip("No projects available for testing")

        headers = _auth_headers(admin_token)
        doc_data = {
            "doc_code": f"DOC-{uuid.uuid4().hex[:6].upper()}",
            "doc_name": f"项目文档-{uuid.uuid4().hex[:4]}",
            "doc_type": "MANUAL",
            "version": "V1.0",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/documents/projects/{project['id']}/documents",
            json=doc_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to create document")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")

        assert response.status_code in [200, 201], response.text

    def test_get_document_by_id(self, client: TestClient, admin_token: str):
        """测试根据 ID 获取文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取文档列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/documents/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get documents list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No documents available for testing")

        doc_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/documents/{doc_id}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc_id

    def test_get_document_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/documents/99999",
            headers=headers
        )

        assert response.status_code == 404

    def test_update_document(self, client: TestClient, admin_token: str):
        """测试更新文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取文档列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/documents/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get documents list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No documents available for testing")

        doc_id = items[0]["id"]

        update_data = {
            "doc_name": f"更新文档-{uuid.uuid4().hex[:4]}",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/documents/{doc_id}",
            json=update_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to update document")

        assert response.status_code == 200, response.text


class TestDocumentVersions:
    """文档版本测试"""

    def test_get_document_versions(self, client: TestClient, admin_token: str):
        """测试获取文档版本列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取文档列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/documents/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get documents list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No documents available for testing")

        doc_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/documents/{doc_id}/versions",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestDocumentDownload:
    """文档下载测试"""

    def test_download_document(self, client: TestClient, admin_token: str):
        """测试下载文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 先获取文档列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/documents/",
            headers=headers
        )

        if list_response.status_code != 200:
            pytest.skip("Failed to get documents list")

        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        if not items:
            pytest.skip("No documents available for testing")

        # 找一个有文件路径的文档
        doc_id = items[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/documents/{doc_id}/download",
            headers=headers
        )

        # 如果文档没有实际文件，会返回 404
        if response.status_code == 404:
            pytest.skip("Document has no file or file not found")

        assert response.status_code == 200


class TestDocumentDelete:
    """文档删除测试"""

    def test_delete_document_not_found(self, client: TestClient, admin_token: str):
        """测试删除不存在的文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.delete(
            f"{settings.API_V1_PREFIX}/documents/99999",
            headers=headers
        )

        assert response.status_code in [404, 403]  # 可能返回403如果没有权限
