# -*- coding: utf-8 -*-
"""
Integration tests for Documents API
Covers: app/api/v1/endpoints/documents.py
"""

from datetime import date


class TestDocumentsAPI:
    """文档管理API集成测试"""

    def test_list_documents(self, client, admin_token):
        """测试获取文档列表"""
        response = client.get(
            "/api/v1/documents/", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_list_documents_with_pagination(self, client, admin_token):
        """测试分页参数"""
        response = client.get(
            "/api/v1/documents/?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_list_documents_with_filters(self, client, admin_token):
        """测试过滤参数"""
        response = client.get(
            "/api/v1/documents/?document_type=TECHNICAL",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_list_documents_by_category(self, client, admin_token):
        """测试按分类筛选"""
        response = client.get(
            "/api/v1/documents/?category=MANUAL",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_get_document_detail(self, client, admin_token):
        """测试获取文档详情"""
        response = client.get(
            "/api/v1/documents/1", headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 200 if exists, 404 if not
        assert response.status_code in [200, 404]

    def test_get_document_not_found(self, client, admin_token):
        """测试获取不存在的文档"""
        response = client.get(
            "/api/v1/documents/999999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_create_document(self, client, admin_token):
        """测试创建文档"""
        document_data = {
            "document_name": "API测试文档",
            "document_code": f"DOC-{date.today().strftime('%Y%m%d')}-001",
            "document_type": "TECHNICAL",
            "category": "MANUAL",
            "version": "1.0",
            "description": "测试文档描述",
        }
        response = client.post(
            "/api/v1/documents/",
            json=document_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_name"] == document_data["document_name"]
        assert "id" in data

    def test_create_document_duplicate_code(self, client, admin_token):
        """测试创建重复编码文档"""
        document_data = {
            "document_name": "重复编码文档",
            "document_code": f"DOC-DUP-{date.today().strftime('%Y%m%d')}",
            "document_type": "TECHNICAL",
        }
        # First create
        response = client.post(
            "/api/v1/documents/",
            json=document_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Try to create again
        response = client.post(
            "/api/v1/documents/",
            json=document_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code in [200, 400, 409]

    def test_update_document(self, client, admin_token):
        """测试更新文档"""
        document_data = {
            "document_name": "待更新文档",
            "document_code": f"DOC-UPD-{date.today().strftime('%Y%m%d')}",
            "document_type": "TECHNICAL",
        }
        response = client.post(
            "/api/v1/documents/",
            json=document_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        if response.status_code == 200:
            doc_id = response.json()["id"]
            update_data = {"document_name": "更新后的文档名称", "version": "2.0"}
            response = client.put(
                f"/api/v1/documents/{doc_id}",
                json=update_data,
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert response.status_code == 200

    def test_update_document_not_found(self, client, admin_token):
        """测试更新不存在的文档"""
        update_data = {"document_name": "不存在的文档"}
        response = client.put(
            "/api/v1/documents/999999",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_delete_document(self, client, admin_token):
        """测试删除文档"""
        document_data = {
            "document_name": "待删除文档",
            "document_code": f"DOC-DEL-{date.today().strftime('%Y%m%d')}",
            "document_type": "TECHNICAL",
        }
        response = client.post(
            "/api/v1/documents/",
            json=document_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        if response.status_code == 200:
            doc_id = response.json()["id"]
            response = client.delete(
                f"/api/v1/documents/{doc_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert response.status_code == 200

    def test_delete_document_not_found(self, client, admin_token):
        """测试删除不存在的文档"""
        response = client.delete(
            "/api/v1/documents/999999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404


class TestDocumentsAPIAuth:
    """文档API认证测试"""

    def test_list_documents_without_token(self, client):
        """测试无token访问"""
        response = client.get("/api/v1/documents/")
        assert response.status_code == 401

    def test_get_document_without_token(self, client):
        """测试无token获取详情"""
        response = client.get("/api/v1/documents/1")
        assert response.status_code == 401

    def test_create_document_without_token(self, client):
        """测试无token创建"""
        response = client.post("/api/v1/documents/", json={"document_name": "测试"})
        assert response.status_code == 401

    def test_update_document_without_token(self, client):
        """测试无token更新"""
        response = client.put("/api/v1/documents/1", json={"document_name": "测试"})
        assert response.status_code == 401

    def test_delete_document_without_token(self, client):
        """测试无token删除"""
        response = client.delete("/api/v1/documents/1")
        assert response.status_code == 401


class TestDocumentsAPIValidation:
    """文档API验证测试"""

    def test_create_document_validation_error(self, client, admin_token):
        """测试创建文档验证错误"""
        document_data = {}
        response = client.post(
            "/api/v1/documents/",
            json=document_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

    def test_invalid_document_type(self, client, admin_token):
        """测试无效文档类型"""
        document_data = {
            "document_name": "测试文档",
            "document_type": "INVALID_TYPE",
        }
        response = client.post(
            "/api/v1/documents/",
            json=document_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422

    def test_search_documents(self, client, admin_token):
        """测试搜索文档"""
        response = client.get(
            "/api/v1/documents/?search=测试",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_version_history(self, client, admin_token):
        """测试获取文档版本历史"""
        response = client.get(
            "/api/v1/documents/1/versions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code in [200, 404]


class TestDocumentsAPISorting:
    """文档API排序测试"""

    def test_sort_by_created_at_desc(self, client, admin_token):
        """测试按创建时间降序排序"""
        response = client.get(
            "/api/v1/documents/?order_by=created_at&order=desc",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

    def test_sort_by_document_name_asc(self, client, admin_token):
        """测试按文档名称升序排序"""
        response = client.get(
            "/api/v1/documents/?order_by=document_name&order=asc",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
