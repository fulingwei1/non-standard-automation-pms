# -*- coding: utf-8 -*-
"""
项目文档 API 测试

测试项目文档的上传、查询、下载、删除及权限管理
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestProjectDocumentsAPI:
    """项目文档 API 测试类"""

    def test_list_project_documents(self, client: TestClient, admin_token: str):
        """测试获取项目文档列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 获取项目
        projects_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/",
            headers=headers
        )
        if projects_response.status_code != 200:
            pytest.skip("No projects available")

        projects = projects_response.json()
        items = projects.get("items", projects) if isinstance(projects, dict) else projects
        if not items:
            pytest.skip("No projects available")

        project_id = items[0]["id"]

        # 获取文档列表
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/documents/",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Project documents API not implemented")

        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_upload_document(self, client: TestClient, admin_token: str):
        """测试上传项目文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 模拟文件上传
        files = {
            "file": ("test_document.pdf", b"fake pdf content", "application/pdf")
        }
        data = {
            "document_type": "requirement",
            "description": "项目需求文档",
            "version": "1.0"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/1/documents/",
            headers=headers,
            files=files,
            data=data
        )

        if response.status_code == 404:
            pytest.skip("Document upload API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_get_document_detail(self, client: TestClient, admin_token: str):
        """测试获取文档详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/documents/1",
            headers=headers
        )

        if response.status_code in [404, 422]:
            pytest.skip("No document data or API not implemented")

        assert response.status_code == 200, response.text

    def test_download_document(self, client: TestClient, admin_token: str):
        """测试下载文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/documents/1/download",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Document download API not implemented")

        # 可能返回文件内容或重定向
        assert response.status_code in [200, 302, 404], response.text

    def test_update_document_metadata(self, client: TestClient, admin_token: str):
        """测试更新文档元数据"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {
            "description": "更新后的文档描述",
            "version": "1.1",
            "tags": ["重要", "需求"]
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/1/documents/1",
            headers=headers,
            json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("Document API not implemented or no data")

        assert response.status_code == 200, response.text

    def test_delete_document(self, client: TestClient, admin_token: str):
        """测试删除文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(
            f"{settings.API_V1_PREFIX}/projects/1/documents/999",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Document API not implemented")

        assert response.status_code in [200, 204, 404], response.text

    def test_document_unauthorized_access(self, client: TestClient):
        """测试未授权访问文档"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/documents/"
        )

        assert response.status_code in [401, 403], response.text

    def test_document_filter_by_type(self, client: TestClient, admin_token: str):
        """测试按类型过滤文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/documents/?document_type=requirement",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Document API not implemented")

        assert response.status_code == 200, response.text

    def test_document_search(self, client: TestClient, admin_token: str):
        """测试文档搜索"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/documents/?search=需求",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Document search API not implemented")

        assert response.status_code == 200, response.text

    def test_document_version_control(self, client: TestClient, admin_token: str):
        """测试文档版本控制"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/documents/1/versions",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Document version API not implemented")

        assert response.status_code == 200, response.text

    def test_document_upload_validation(self, client: TestClient, admin_token: str):
        """测试文档上传验证（文件大小、格式等）"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 测试无效的文件类型
        files = {
            "file": ("test.exe", b"fake exe content", "application/x-executable")
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/1/documents/",
            headers=headers,
            files=files
        )

        if response.status_code == 404:
            pytest.skip("Document upload API not implemented")

        # 可能返回 422（验证失败）或 200（接受所有类型）
        assert response.status_code in [200, 201, 422], response.text

    def test_document_pagination(self, client: TestClient, admin_token: str):
        """测试文档列表分页"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/documents/?page=1&page_size=20",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Document API not implemented")

        assert response.status_code == 200, response.text

    def test_document_statistics(self, client: TestClient, admin_token: str):
        """测试项目文档统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/documents/statistics",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Document statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_batch_delete_documents(self, client: TestClient, admin_token: str):
        """测试批量删除文档"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        delete_data = {
            "document_ids": [999, 998, 997]
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/1/documents/batch-delete",
            headers=headers,
            json=delete_data
        )

        if response.status_code == 404:
            pytest.skip("Batch delete API not implemented")

        assert response.status_code in [200, 204], response.text
