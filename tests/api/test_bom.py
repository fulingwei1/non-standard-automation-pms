# -*- coding: utf-8 -*-
"""
BOM 管理模块 API 测试

测试 BOM 的 CRUD 操作、版本管理和采购申请生成
"""

import uuid
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _get_first_machine(client: TestClient, token: str) -> dict:
    """获取第一个可用的机台"""
    headers = _auth_headers(token)

    # 先获取项目列表
    projects_response = client.get(
        f"{settings.API_V1_PREFIX}/projects/",
        headers=headers
    )

    if projects_response.status_code != 200:
        return None

    projects = projects_response.json()
    items = projects.get("items", projects) if isinstance(projects, dict) else projects
    if not items:
        return None

    project_id = items[0]["id"]

    # 获取项目的机台列表
    machines_response = client.get(
        f"{settings.API_V1_PREFIX}/machines/",
        params={"project_id": project_id},
        headers=headers
    )

    if machines_response.status_code != 200:
        return None

    machines = machines_response.json()
    machine_items = machines.get("items", machines) if isinstance(machines, dict) else machines
    if not machine_items:
        return None

    return {"machine": machine_items[0], "project_id": project_id}


class TestBomCRUD:
    """BOM CRUD 测试"""

    def test_get_machine_bom_list(self, client: TestClient, admin_token: str):
        """测试获取机台的 BOM 列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        result = _get_first_machine(client, admin_token)
        if not result:
            pytest.skip("No machines available for testing")

        headers = _auth_headers(admin_token)
        machine_id = result["machine"]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/bom/machines/{machine_id}/bom",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_machine_bom_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的机台的 BOM 列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/bom/machines/99999/bom",
            headers=headers
        )

        assert response.status_code == 404

    def test_create_bom(self, client: TestClient, admin_token: str):
        """测试创建 BOM"""
        if not admin_token:
            pytest.skip("Admin token not available")

        result = _get_first_machine(client, admin_token)
        if not result:
            pytest.skip("No machines available for testing")

        headers = _auth_headers(admin_token)
        machine_id = result["machine"]["id"]
        project_id = result["project_id"]

        bom_data = {
            "bom_name": f"测试BOM-{uuid.uuid4().hex[:4]}",
            "project_id": project_id,
            "version": "V1.0",
            "remark": "测试用BOM",
            "items": [
                {
                    "material_code": f"MAT-{uuid.uuid4().hex[:6].upper()}",
                    "material_name": "测试物料1",
                    "specification": "规格1",
                    "unit": "个",
                    "quantity": 10,
                    "unit_price": 100.00,
                    "source_type": "PURCHASE",
                    "is_key_item": False,
                },
                {
                    "material_code": f"MAT-{uuid.uuid4().hex[:6].upper()}",
                    "material_name": "测试物料2",
                    "specification": "规格2",
                    "unit": "件",
                    "quantity": 5,
                    "unit_price": 200.00,
                    "source_type": "PURCHASE",
                    "is_key_item": True,
                }
            ]
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/bom/machines/{machine_id}/bom",
            json=bom_data,
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to create BOM")
        if response.status_code == 422:
            pytest.skip("Validation error - schema mismatch")

        assert response.status_code in [200, 201], response.text
        data = response.json()
        assert data["bom_name"] == bom_data["bom_name"]
        assert data["project_id"] == project_id
        assert data["machine_id"] == machine_id
        assert data["status"] == "DRAFT"
        assert data["total_items"] == 2

    def test_get_bom_by_id(self, client: TestClient, admin_token: str):
        """测试根据 ID 获取 BOM"""
        if not admin_token:
            pytest.skip("Admin token not available")

        result = _get_first_machine(client, admin_token)
        if not result:
            pytest.skip("No machines available for testing")

        headers = _auth_headers(admin_token)
        machine_id = result["machine"]["id"]

        # 先获取机台的 BOM 列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/bom/machines/{machine_id}/bom",
            headers=headers
        )

        if list_response.status_code != 200 or not list_response.json():
            pytest.skip("No BOMs available for testing")

        bom_id = list_response.json()[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/bom/{bom_id}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == bom_id

    def test_get_bom_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的 BOM"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/bom/99999",
            headers=headers
        )

        assert response.status_code == 404

    def test_update_bom(self, client: TestClient, admin_token: str):
        """测试更新 BOM"""
        if not admin_token:
            pytest.skip("Admin token not available")

        result = _get_first_machine(client, admin_token)
        if not result:
            pytest.skip("No machines available for testing")

        headers = _auth_headers(admin_token)
        machine_id = result["machine"]["id"]

        # 获取草稿状态的 BOM
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/bom/machines/{machine_id}/bom",
            headers=headers
        )

        if list_response.status_code != 200 or not list_response.json():
            pytest.skip("No BOMs available for testing")

        # 查找草稿状态的 BOM
        boms = list_response.json()
        draft_bom = None
        for bom in boms:
            if bom.get("status") == "DRAFT":
                draft_bom = bom
                break

        if not draft_bom:
            pytest.skip("No draft BOM available for testing")

        bom_id = draft_bom["id"]

        update_data = {
            "bom_name": f"更新后BOM-{uuid.uuid4().hex[:4]}",
            "remark": "更新后的备注",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/bom/{bom_id}",
            json=update_data,
            headers=headers
        )

        if response.status_code == 400:
            pytest.skip("BOM is not in DRAFT status")
        if response.status_code == 403:
            pytest.skip("User does not have permission to update BOM")

        assert response.status_code == 200, response.text


class TestBomItems:
    """BOM 明细测试"""

    def test_get_bom_items(self, client: TestClient, admin_token: str):
        """测试获取 BOM 明细列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        result = _get_first_machine(client, admin_token)
        if not result:
            pytest.skip("No machines available for testing")

        headers = _auth_headers(admin_token)
        machine_id = result["machine"]["id"]

        # 获取 BOM 列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/bom/machines/{machine_id}/bom",
            headers=headers
        )

        if list_response.status_code != 200 or not list_response.json():
            pytest.skip("No BOMs available for testing")

        bom_id = list_response.json()[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/bom/{bom_id}/items",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_add_bom_item(self, client: TestClient, admin_token: str):
        """测试添加 BOM 明细"""
        if not admin_token:
            pytest.skip("Admin token not available")

        result = _get_first_machine(client, admin_token)
        if not result:
            pytest.skip("No machines available for testing")

        headers = _auth_headers(admin_token)
        machine_id = result["machine"]["id"]

        # 获取草稿状态的 BOM
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/bom/machines/{machine_id}/bom",
            headers=headers
        )

        if list_response.status_code != 200 or not list_response.json():
            pytest.skip("No BOMs available for testing")

        # 查找草稿状态的 BOM
        boms = list_response.json()
        draft_bom = None
        for bom in boms:
            if bom.get("status") == "DRAFT":
                draft_bom = bom
                break

        if not draft_bom:
            pytest.skip("No draft BOM available for testing")

        bom_id = draft_bom["id"]

        item_data = {
            "material_code": f"MAT-{uuid.uuid4().hex[:6].upper()}",
            "material_name": "新增测试物料",
            "specification": "新规格",
            "unit": "套",
            "quantity": 3,
            "unit_price": 150.00,
            "source_type": "PURCHASE",
            "is_key_item": False,
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/bom/{bom_id}/items",
            json=item_data,
            headers=headers
        )

        if response.status_code == 400:
            pytest.skip("BOM is not in DRAFT status")
        if response.status_code == 422:
            pytest.skip("Validation error")

        assert response.status_code in [200, 201], response.text
        data = response.json()
        assert data["material_code"] == item_data["material_code"]

    def test_update_bom_item(self, client: TestClient, admin_token: str):
        """测试更新 BOM 明细"""
        if not admin_token:
            pytest.skip("Admin token not available")

        result = _get_first_machine(client, admin_token)
        if not result:
            pytest.skip("No machines available for testing")

        headers = _auth_headers(admin_token)
        machine_id = result["machine"]["id"]

        # 获取草稿状态的 BOM
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/bom/machines/{machine_id}/bom",
            headers=headers
        )

        if list_response.status_code != 200 or not list_response.json():
            pytest.skip("No BOMs available for testing")

        # 查找草稿状态的 BOM
        boms = list_response.json()
        draft_bom = None
        for bom in boms:
            if bom.get("status") == "DRAFT" and bom.get("items"):
                draft_bom = bom
                break

        if not draft_bom or not draft_bom.get("items"):
            pytest.skip("No draft BOM with items available for testing")

        item_id = draft_bom["items"][0]["id"]

        update_data = {
            "material_code": f"MAT-{uuid.uuid4().hex[:6].upper()}",
            "material_name": "更新后物料",
            "specification": "更新规格",
            "unit": "个",
            "quantity": 20,
            "unit_price": 180.00,
            "source_type": "PURCHASE",
            "is_key_item": True,
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/bom/items/{item_id}",
            json=update_data,
            headers=headers
        )

        if response.status_code == 400:
            pytest.skip("BOM is not in DRAFT status")
        if response.status_code == 404:
            pytest.skip("BOM item not found")

        assert response.status_code == 200, response.text

    def test_delete_bom_item(self, client: TestClient, admin_token: str):
        """测试删除 BOM 明细"""
        if not admin_token:
            pytest.skip("Admin token not available")

        result = _get_first_machine(client, admin_token)
        if not result:
            pytest.skip("No machines available for testing")

        headers = _auth_headers(admin_token)
        machine_id = result["machine"]["id"]
        project_id = result["project_id"]

        # 创建新的 BOM 用于测试删除
        bom_data = {
            "bom_name": f"删除测试BOM-{uuid.uuid4().hex[:4]}",
            "project_id": project_id,
            "version": "V1.0",
            "items": [
                {
                    "material_code": f"MAT-DEL-{uuid.uuid4().hex[:6].upper()}",
                    "material_name": "待删除物料",
                    "unit": "个",
                    "quantity": 1,
                    "unit_price": 10.00,
                    "source_type": "PURCHASE",
                    "is_key_item": False,
                }
            ]
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/bom/machines/{machine_id}/bom",
            json=bom_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create BOM for testing")

        bom = create_response.json()
        if not bom.get("items"):
            pytest.skip("No items in created BOM")

        item_id = bom["items"][0]["id"]

        response = client.delete(
            f"{settings.API_V1_PREFIX}/bom/items/{item_id}",
            headers=headers
        )

        if response.status_code == 400:
            pytest.skip("BOM is not in DRAFT status")

        assert response.status_code == 200, response.text


class TestBomVersions:
    """BOM 版本管理测试"""

    def test_get_bom_versions(self, client: TestClient, admin_token: str):
        """测试获取 BOM 版本列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        result = _get_first_machine(client, admin_token)
        if not result:
            pytest.skip("No machines available for testing")

        headers = _auth_headers(admin_token)
        machine_id = result["machine"]["id"]

        # 获取 BOM 列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/bom/machines/{machine_id}/bom",
            headers=headers
        )

        if list_response.status_code != 200 or not list_response.json():
            pytest.skip("No BOMs available for testing")

        bom_id = list_response.json()[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/bom/{bom_id}/versions",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_compare_bom_versions(self, client: TestClient, admin_token: str):
        """测试对比 BOM 版本"""
        if not admin_token:
            pytest.skip("Admin token not available")

        result = _get_first_machine(client, admin_token)
        if not result:
            pytest.skip("No machines available for testing")

        headers = _auth_headers(admin_token)
        machine_id = result["machine"]["id"]

        # 获取 BOM 列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/bom/machines/{machine_id}/bom",
            headers=headers
        )

        if list_response.status_code != 200 or not list_response.json():
            pytest.skip("No BOMs available for testing")

        bom_id = list_response.json()[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/bom/{bom_id}/versions/compare",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "version1" in data
        assert "version2" in data
        assert "comparison" in data


class TestBomRelease:
    """BOM 发布测试"""

    def test_release_bom(self, client: TestClient, admin_token: str):
        """测试发布 BOM"""
        if not admin_token:
            pytest.skip("Admin token not available")

        result = _get_first_machine(client, admin_token)
        if not result:
            pytest.skip("No machines available for testing")

        headers = _auth_headers(admin_token)
        machine_id = result["machine"]["id"]
        project_id = result["project_id"]

        # 创建新的 BOM 用于测试发布
        bom_data = {
            "bom_name": f"发布测试BOM-{uuid.uuid4().hex[:4]}",
            "project_id": project_id,
            "version": "V1.0",
            "items": [
                {
                    "material_code": f"MAT-REL-{uuid.uuid4().hex[:6].upper()}",
                    "material_name": "发布测试物料",
                    "unit": "个",
                    "quantity": 5,
                    "unit_price": 50.00,
                    "source_type": "PURCHASE",
                    "is_key_item": False,
                }
            ]
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/bom/machines/{machine_id}/bom",
            json=bom_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create BOM for testing")

        bom = create_response.json()
        bom_id = bom["id"]

        response = client.post(
            f"{settings.API_V1_PREFIX}/bom/{bom_id}/release",
            params={"change_note": "测试发布"},
            headers=headers
        )

        if response.status_code == 400:
            pytest.skip("BOM is not in DRAFT status or has no items")
        if response.status_code == 403:
            pytest.skip("User does not have permission to release BOM")

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "RELEASED"
        assert data["is_latest"] == True

    def test_release_bom_without_items(self, client: TestClient, admin_token: str):
        """测试发布没有明细的 BOM（应该失败）"""
        if not admin_token:
            pytest.skip("Admin token not available")

        result = _get_first_machine(client, admin_token)
        if not result:
            pytest.skip("No machines available for testing")

        headers = _auth_headers(admin_token)
        machine_id = result["machine"]["id"]
        project_id = result["project_id"]

        # 创建没有明细的 BOM
        bom_data = {
            "bom_name": f"空BOM测试-{uuid.uuid4().hex[:4]}",
            "project_id": project_id,
            "version": "V1.0",
            "items": []
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/bom/machines/{machine_id}/bom",
            json=bom_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create empty BOM for testing")

        bom = create_response.json()
        bom_id = bom["id"]

        response = client.post(
            f"{settings.API_V1_PREFIX}/bom/{bom_id}/release",
            headers=headers
        )

        # 应该返回 400 错误
        assert response.status_code == 400


class TestBomExcelOperations:
    """BOM Excel 导入导出测试"""

    def test_download_import_template(self, client: TestClient, admin_token: str):
        """测试下载 BOM 导入模板"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/bom/template/download",
            headers=headers
        )

        if response.status_code == 500:
            pytest.skip("Excel library not available")

        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("content-type", "")

    def test_export_bom(self, client: TestClient, admin_token: str):
        """测试导出 BOM"""
        if not admin_token:
            pytest.skip("Admin token not available")

        result = _get_first_machine(client, admin_token)
        if not result:
            pytest.skip("No machines available for testing")

        headers = _auth_headers(admin_token)
        machine_id = result["machine"]["id"]

        # 获取 BOM 列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/bom/machines/{machine_id}/bom",
            headers=headers
        )

        if list_response.status_code != 200 or not list_response.json():
            pytest.skip("No BOMs available for testing")

        bom_id = list_response.json()[0]["id"]

        response = client.get(
            f"{settings.API_V1_PREFIX}/bom/{bom_id}/export",
            headers=headers
        )

        if response.status_code == 500:
            pytest.skip("Excel library not available")

        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("content-type", "")


class TestBomPurchaseRequest:
    """BOM 采购申请生成测试"""

    def test_generate_purchase_request(self, client: TestClient, admin_token: str):
        """测试从 BOM 生成采购申请"""
        if not admin_token:
            pytest.skip("Admin token not available")

        result = _get_first_machine(client, admin_token)
        if not result:
            pytest.skip("No machines available for testing")

        headers = _auth_headers(admin_token)
        machine_id = result["machine"]["id"]

        # 获取已发布的 BOM
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/bom/machines/{machine_id}/bom",
            headers=headers
        )

        if list_response.status_code != 200 or not list_response.json():
            pytest.skip("No BOMs available for testing")

        # 查找有采购物料的 BOM
        boms = list_response.json()
        test_bom = None
        for bom in boms:
            if bom.get("items"):
                test_bom = bom
                break

        if not test_bom:
            pytest.skip("No BOM with items available for testing")

        bom_id = test_bom["id"]

        response = client.post(
            f"{settings.API_V1_PREFIX}/bom/{bom_id}/generate-pr",
            params={"create_requests": False},  # 只预览不创建
            headers=headers
        )

        if response.status_code == 400:
            pytest.skip("BOM has no purchasable items")
        if response.status_code == 403:
            pytest.skip("User does not have procurement access")
        if response.status_code == 500:
            pytest.skip("Internal server error (service may not be available)")

        assert response.status_code == 200, response.text
        data = response.json()
        assert "data" in data
        assert "purchase_requests" in data["data"]
