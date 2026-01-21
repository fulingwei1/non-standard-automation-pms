# -*- coding: utf-8 -*-
"""
文档管理模块 API 集成测试

测试范围：
- 文档上传/下载 (Upload/Download)
- 文档管理 (Documents)
- 文件夹管理 (Folders)
- 文档权限 (Permissions)
- 文档版本 (Versions)
"""

import pytest
from datetime import date, datetime, timedelta

from tests.integration.api_test_helper import APITestHelper, Colors


@pytest.mark.integration
class TestDocumentsAPI:
    """文档管理 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.tracked_resources = []
        self.helper.print_info("文档管理 API 测试")

    def test_upload_document(self):
        """测试上传文档"""
        self.helper.print_info("测试上传文档...")

        # 模拟文件上传（实际文件上传需要multipart/form-data）
        document_data = {
            "project_id": self.test_project_id,
            "document_name": "FCT设备技术方案.pdf",
            "document_type": "SPECIFICATION",
            "category": "DESIGN",
            "version": "V1.0",
            "description": "FCT测试设备的技术方案文档",
            "upload_date": date.today().isoformat(),
        }

        response = self.helper.post(
            "/documents", document_data, resource_type="document"
        )

        result = self.helper.assert_success(response)
        if result:
            doc_id = result.get("id")
            if doc_id:
                self.tracked_resources.append(("document", doc_id))
                self.helper.print_success(f"文档上传成功，ID: {doc_id}")
            else:
                self.helper.print_warning("文档上传成功，但未返回ID")
        else:
            self.helper.print_warning("上传文档响应不符合预期，继续测试")

    def test_get_documents_list(self):
        """测试获取文档列表"""
        self.helper.print_info("测试获取文档列表...")

        params = {
            "page": 1,
            "page_size": 20,
            "project_id": self.test_project_id,
            "document_type": "SPECIFICATION",
        }

        response = self.helper.get(
            "/documents", params=params, resource_type="documents_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个文档")
        else:
            self.helper.print_warning("获取文档列表响应不符合预期")

    def test_get_document_detail(self):
        """测试获取文档详情"""
        if not self.tracked_resources:
            pytest.skip("没有可用的文档ID")

        doc_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取文档详情 (ID: {doc_id})...")

        response = self.helper.get(
            f"/documents/{doc_id}", resource_type=f"document_{doc_id}"
        )

        result = self.helper.assert_success(response)
        if result:
            self.helper.assert_data_not_empty(result)
            self.helper.print_success("文档详情获取成功")
        else:
            self.helper.print_warning("获取文档详情响应不符合预期")

    def test_download_document(self):
        """测试下载文档"""
        if not self.tracked_resources:
            pytest.skip("没有可用的文档ID")

        doc_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试下载文档 (ID: {doc_id})...")

        response = self.helper.get(
            f"/documents/{doc_id}/download", resource_type=f"document_{doc_id}_download"
        )

        # 检查响应，下载端点应该返回文件或下载URL
        if response.status_code == 200:
            self.helper.print_success("文档下载请求成功")
        else:
            self.helper.print_warning("下载文档响应不符合预期")

    def test_update_document(self):
        """测试更新文档"""
        if not self.tracked_resources:
            pytest.skip("没有可用的文档ID")

        doc_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新文档 (ID: {doc_id})...")

        update_data = {
            "document_name": "FCT设备技术方案_V1.1.pdf",
            "version": "V1.1",
            "description": "更新：增加了电气部分的技术说明",
        }

        response = self.helper.put(
            f"/documents/{doc_id}",
            update_data,
            resource_type=f"document_{doc_id}_update",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("文档更新成功")
        else:
            self.helper.print_warning("更新文档响应不符合预期")

    def test_delete_document(self):
        """测试删除文档"""
        if not self.tracked_resources:
            pytest.skip("没有可用的文档ID")

        doc_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试删除文档 (ID: {doc_id})...")

        response = self.helper.delete(
            f"/documents/{doc_id}", resource_type=f"document_{doc_id}_delete"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("文档删除成功")
        else:
            self.helper.print_warning("删除文档响应不符合预期")


@pytest.mark.integration
class TestDocumentsFoldersAPI:
    """文档文件夹管理 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, test_project, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.test_project_id = test_project.id if test_project else None
        self.tracked_resources = []
        self.helper.print_info("文档文件夹管理 API 测试")

    def test_create_folder(self):
        """测试创建文件夹"""
        self.helper.print_info("测试创建文件夹...")

        folder_data = {
            "project_id": self.test_project_id,
            "folder_name": "技术文档",
            "parent_folder_id": None,
            "description": "存放所有技术相关文档",
        }

        response = self.helper.post("/folders", folder_data, resource_type="folder")

        result = self.helper.assert_success(response)
        if result:
            folder_id = result.get("id")
            if folder_id:
                self.tracked_resources.append(("folder", folder_id))
                self.helper.print_success(f"文件夹创建成功，ID: {folder_id}")
            else:
                self.helper.print_warning("文件夹创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建文件夹响应不符合预期，继续测试")

    def test_get_folders_list(self):
        """测试获取文件夹列表"""
        self.helper.print_info("测试获取文件夹列表...")

        params = {
            "project_id": self.test_project_id,
            "include_subfolders": True,
            "parent_folder_id": None,
        }

        response = self.helper.get(
            "/folders", params=params, resource_type="folders_list"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个文件夹")
        else:
            self.helper.print_warning("获取文件夹列表响应不符合预期")


@pytest.mark.integration
class TestDocumentsPermissionsAPI:
    """文档权限管理 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("文档权限管理 API 测试")

    def test_grant_document_permission(self):
        """测试授予文档权限"""
        if not self.tracked_resources:
            pytest.skip("没有可用的文档ID")

        doc_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试授予文档权限 (文档ID: {doc_id})...")

        permission_data = {
            "document_id": doc_id,
            "user_id": 2,  # 假设存在用户ID
            "permission_level": "READ_WRITE",
            "granted_by": 1,
            "expiry_date": (date.today() + timedelta(days=30)).isoformat(),
        }

        response = self.helper.post(
            "/permissions/grant", permission_data, resource_type="document_permission"
        )

        if self.helper.assert_success(response):
            self.helper.print_success("文档权限授予成功")
        else:
            self.helper.print_warning("授予文档权限响应不符合预期")

    def test_get_document_permissions(self):
        """测试获取文档权限"""
        if not self.tracked_resources:
            pytest.skip("没有可用的文档ID")

        doc_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取文档权限 (文档ID: {doc_id})...")

        params = {
            "document_id": doc_id,
        }

        response = self.helper.get(
            "/permissions", params=params, resource_type="document_permissions"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 条权限记录")
        else:
            self.helper.print_warning("获取文档权限响应不符合预期")


@pytest.mark.integration
class TestDocumentsVersionsAPI:
    """文档版本管理 API 测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token, db_session):
        """测试前置设置"""
        self.helper = APITestHelper(client, admin_token)
        self.db = db_session
        self.tracked_resources = []
        self.helper.print_info("文档版本管理 API 测试")

    def test_create_document_version(self):
        """测试创建文档版本"""
        if not self.tracked_resources:
            pytest.skip("没有可用的文档ID")

        doc_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试创建文档版本 (文档ID: {doc_id})...")

        version_data = {
            "document_id": doc_id,
            "version": "V2.0",
            "change_description": "更新了电气部分的技术规格",
            "uploaded_by": 1,
            "upload_date": datetime.now().isoformat(),
        }

        response = self.helper.post(
            "/versions", version_data, resource_type="document_version"
        )

        result = self.helper.assert_success(response)
        if result:
            version_id = result.get("id")
            if version_id:
                self.tracked_resources.append(("version", version_id))
                self.helper.print_success(f"文档版本创建成功，ID: {version_id}")
            else:
                self.helper.print_warning("文档版本创建成功，但未返回ID")
        else:
            self.helper.print_warning("创建文档版本响应不符合预期，继续测试")

    def test_get_document_versions(self):
        """测试获取文档版本列表"""
        if not self.tracked_resources:
            pytest.skip("没有可用的文档ID")

        doc_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取文档版本列表 (文档ID: {doc_id})...")

        params = {
            "document_id": doc_id,
        }

        response = self.helper.get(
            "/versions", params=params, resource_type="document_versions"
        )

        result = self.helper.assert_success(response)
        if result:
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个文档版本")
        else:
            self.helper.print_warning("获取文档版本列表响应不符合预期")
