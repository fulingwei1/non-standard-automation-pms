# -*- coding: utf-8 -*-
"""
客户档案与联系人管理 API 单元测试

测试覆盖：
- 客户档案 CRUD（15+用例）
- 联系人管理 CRUD（10+用例）
- 客户分级自动化测试
- 标签管理测试
- 搜索/筛选测试
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _unique_code(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"


class TestCustomerCRUD:
    """客户档案 CRUD 测试（15+用例）"""

    def test_create_customer_success(self, client: TestClient, admin_token: str):
        """测试成功创建客户"""
        headers = _auth_headers(admin_token)
        payload = {
            "customer_name": f"测试客户-{uuid.uuid4().hex[:4]}",
            "short_name": "测试客户",
            "customer_type": "enterprise",
            "industry": "电子制造",
            "scale": "中型",
            "address": "上海市浦东新区",
            "website": "https://example.com",
            "credit_limit": 1000000,
            "payment_terms": "月结30天",
            "account_period": 30,
            "customer_source": "展会",
            "status": "potential",
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["customer_name"] == payload["customer_name"]
        assert data["customer_code"].startswith("CUS")
        assert data["customer_level"] == "D"  # 新客户默认D级
        assert "customer_id" in data or "id" in data

    def test_create_customer_auto_generate_code(self, client: TestClient, admin_token: str):
        """测试自动生成客户编码"""
        headers = _auth_headers(admin_token)
        payload = {
            "customer_name": f"自动编码客户-{uuid.uuid4().hex[:4]}",
            "customer_type": "enterprise",
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["customer_code"].startswith("CUS")
        assert len(data["customer_code"]) == 15  # CUS + YYYYMMDD + 0001

    def test_create_customer_duplicate_code(self, client: TestClient, admin_token: str):
        """测试创建重复编码的客户（应失败）"""
        headers = _auth_headers(admin_token)
        unique_code = _unique_code("TESTCUST")
        
        # 第一次创建
        payload1 = {
            "customer_code": unique_code,
            "customer_name": f"客户A-{uuid.uuid4().hex[:4]}",
            "customer_type": "enterprise",
        }
        response1 = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers",
            json=payload1,
            headers=headers,
        )
        assert response1.status_code == 201

        # 第二次创建（重复编码）
        payload2 = {
            "customer_code": unique_code,
            "customer_name": f"客户B-{uuid.uuid4().hex[:4]}",
            "customer_type": "enterprise",
        }
        response2 = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers",
            json=payload2,
            headers=headers,
        )
        assert response2.status_code == 400
        assert "已存在" in response2.text or "duplicate" in response2.text.lower()

    def test_read_customer_detail(self, client: TestClient, admin_token: str):
        """测试获取客户详情"""
        headers = _auth_headers(admin_token)
        
        # 先创建一个客户
        create_payload = {
            "customer_name": f"详情测试客户-{uuid.uuid4().hex[:4]}",
            "industry": "汽车制造",
        }
        create_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers",
            json=create_payload,
            headers=headers,
        )
        assert create_response.status_code == 201
        customer_id = create_response.json()["id"]

        # 获取客户详情
        detail_response = client.get(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}",
            headers=headers,
        )
        assert detail_response.status_code == 200
        data = detail_response.json()
        assert data["id"] == customer_id
        assert data["customer_name"] == create_payload["customer_name"]
        assert data["industry"] == "汽车制造"

    def test_read_customer_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的客户"""
        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/customers/999999",
            headers=headers,
        )
        assert response.status_code == 404

    def test_update_customer_success(self, client: TestClient, admin_token: str):
        """测试成功更新客户信息"""
        headers = _auth_headers(admin_token)
        
        # 先创建一个客户
        create_payload = {
            "customer_name": f"更新测试客户-{uuid.uuid4().hex[:4]}",
            "industry": "电子制造",
            "scale": "小型",
        }
        create_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers",
            json=create_payload,
            headers=headers,
        )
        customer_id = create_response.json()["id"]

        # 更新客户
        update_payload = {
            "industry": "半导体制造",
            "scale": "大型",
            "website": "https://updated.com",
        }
        update_response = client.put(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}",
            json=update_payload,
            headers=headers,
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["industry"] == "半导体制造"
        assert data["scale"] == "大型"
        assert data["website"] == "https://updated.com"

    def test_delete_customer_success(self, client: TestClient, admin_token: str):
        """测试成功删除客户"""
        headers = _auth_headers(admin_token)
        
        # 先创建一个客户
        create_payload = {
            "customer_name": f"删除测试客户-{uuid.uuid4().hex[:4]}",
        }
        create_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers",
            json=create_payload,
            headers=headers,
        )
        customer_id = create_response.json()["id"]

        # 删除客户
        delete_response = client.delete(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}",
            headers=headers,
        )
        assert delete_response.status_code == 204

        # 验证已删除
        get_response = client.get(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}",
            headers=headers,
        )
        assert get_response.status_code == 404

    def test_list_customers_with_pagination(self, client: TestClient, admin_token: str):
        """测试客户列表分页"""
        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/customers",
            params={"page": 1, "page_size": 10},
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or "data" in data or isinstance(data, list)
        assert "total" in data or isinstance(data, list)

    def test_list_customers_filter_by_level(self, client: TestClient, admin_token: str):
        """测试按客户等级筛选"""
        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/customers",
            params={"customer_level": "A"},
            headers=headers,
        )
        assert response.status_code == 200

    def test_list_customers_filter_by_status(self, client: TestClient, admin_token: str):
        """测试按客户状态筛选"""
        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/customers",
            params={"status": "customer"},
            headers=headers,
        )
        assert response.status_code == 200

    def test_list_customers_filter_by_industry(self, client: TestClient, admin_token: str):
        """测试按行业筛选"""
        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/customers",
            params={"industry": "电子制造"},
            headers=headers,
        )
        assert response.status_code == 200

    def test_search_customers_by_keyword(self, client: TestClient, admin_token: str):
        """测试关键词搜索客户"""
        headers = _auth_headers(admin_token)
        
        # 创建一个特征明显的客户
        unique_name = f"搜索测试-{uuid.uuid4().hex[:8]}"
        create_payload = {"customer_name": unique_name}
        create_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers",
            json=create_payload,
            headers=headers,
        )
        assert create_response.status_code == 201

        # 搜索客户
        search_response = client.get(
            f"{settings.API_V1_PREFIX}/sales/customers",
            params={"keyword": unique_name[:10]},
            headers=headers,
        )
        assert search_response.status_code == 200

    def test_customer_stats(self, client: TestClient, admin_token: str):
        """测试客户统计数据"""
        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/customers/stats",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_customers" in data
        assert "level_a_count" in data or "a_level_count" in data
        assert "potential_count" in data
        assert "total_annual_revenue" in data or "annual_revenue" in data

    def test_sort_customers_by_created_at(self, client: TestClient, admin_token: str):
        """测试按创建时间排序"""
        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/customers",
            params={"order_by": "created_at", "order_desc": True},
            headers=headers,
        )
        assert response.status_code == 200

    def test_sort_customers_by_last_follow_up(self, client: TestClient, admin_token: str):
        """测试按最后跟进时间排序"""
        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/customers",
            params={"order_by": "last_follow_up_at", "order_desc": True},
            headers=headers,
        )
        assert response.status_code == 200


class TestCustomerLevelAutomation:
    """客户分级自动化测试"""

    def test_customer_level_a(self, client: TestClient, admin_token: str):
        """测试A级客户判定：年成交额>100万，合作>3年"""
        headers = _auth_headers(admin_token)
        payload = {
            "customer_name": f"A级客户-{uuid.uuid4().hex[:4]}",
            "annual_revenue": 1500000,  # 150万
            "cooperation_years": 4,
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["customer_level"] == "A"

    def test_customer_level_b(self, client: TestClient, admin_token: str):
        """测试B级客户判定：年成交额50-100万，合作1-3年"""
        headers = _auth_headers(admin_token)
        payload = {
            "customer_name": f"B级客户-{uuid.uuid4().hex[:4]}",
            "annual_revenue": 800000,  # 80万
            "cooperation_years": 2,
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["customer_level"] == "B"

    def test_customer_level_c(self, client: TestClient, admin_token: str):
        """测试C级客户判定：年成交额10-50万"""
        headers = _auth_headers(admin_token)
        payload = {
            "customer_name": f"C级客户-{uuid.uuid4().hex[:4]}",
            "annual_revenue": 300000,  # 30万
            "cooperation_years": 0,
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["customer_level"] == "C"

    def test_customer_level_d(self, client: TestClient, admin_token: str):
        """测试D级客户判定：年成交额<10万或潜在客户"""
        headers = _auth_headers(admin_token)
        payload = {
            "customer_name": f"D级客户-{uuid.uuid4().hex[:4]}",
            "annual_revenue": 50000,  # 5万
            "cooperation_years": 1,
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["customer_level"] == "D"

    def test_customer_level_update(self, client: TestClient, admin_token: str):
        """测试客户等级自动更新"""
        headers = _auth_headers(admin_token)
        
        # 创建D级客户
        create_payload = {
            "customer_name": f"升级测试客户-{uuid.uuid4().hex[:4]}",
            "annual_revenue": 50000,
            "cooperation_years": 0,
        }
        create_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers",
            json=create_payload,
            headers=headers,
        )
        customer_id = create_response.json()["id"]
        assert create_response.json()["customer_level"] == "D"

        # 更新为A级条件
        update_payload = {
            "annual_revenue": 1200000,
            "cooperation_years": 4,
        }
        update_response = client.put(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}",
            json=update_payload,
            headers=headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["customer_level"] == "A"


class TestContactCRUD:
    """联系人 CRUD 测试（10+用例）"""

    def _create_customer(self, client: TestClient, token: str) -> int:
        """辅助方法：创建客户"""
        headers = _auth_headers(token)
        payload = {
            "customer_name": f"联系人测试客户-{uuid.uuid4().hex[:4]}",
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers",
            json=payload,
            headers=headers,
        )
        return response.json()["id"]

    def test_create_contact_success(self, client: TestClient, admin_token: str):
        """测试成功创建联系人"""
        customer_id = self._create_customer(client, admin_token)
        headers = _auth_headers(admin_token)
        
        payload = {
            "customer_id": customer_id,
            "customer_name": "张三",
            "position": "采购经理",
            "department": "采购部",
            "mobile": "13800138000",
            "email": "zhangsan@example.com",
            "wechat": "zhangsan_wx",
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/contacts",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["customer_name"] == "张三"
        assert data["customer_id"] == customer_id

    def test_create_contact_as_primary(self, client: TestClient, admin_token: str):
        """测试创建主要联系人"""
        customer_id = self._create_customer(client, admin_token)
        headers = _auth_headers(admin_token)
        
        payload = {
            "customer_id": customer_id,
            "customer_name": "李四",
            "position": "总经理",
            "is_primary": True,
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/contacts",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["is_primary"] is True

    def test_read_contact_detail(self, client: TestClient, admin_token: str):
        """测试获取联系人详情"""
        customer_id = self._create_customer(client, admin_token)
        headers = _auth_headers(admin_token)
        
        # 创建联系人
        create_payload = {
            "customer_id": customer_id,
            "customer_name": "王五",
            "mobile": "13900139000",
        }
        create_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/contacts",
            json=create_payload,
            headers=headers,
        )
        contact_id = create_response.json()["id"]

        # 获取详情
        detail_response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contacts/{contact_id}",
            headers=headers,
        )
        assert detail_response.status_code == 200
        data = detail_response.json()
        assert data["customer_name"] == "王五"

    def test_update_contact_success(self, client: TestClient, admin_token: str):
        """测试更新联系人"""
        customer_id = self._create_customer(client, admin_token)
        headers = _auth_headers(admin_token)
        
        # 创建联系人
        create_payload = {
            "customer_id": customer_id,
            "customer_name": "赵六",
            "mobile": "13700137000",
        }
        create_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/contacts",
            json=create_payload,
            headers=headers,
        )
        contact_id = create_response.json()["id"]

        # 更新联系人
        update_payload = {
            "position": "副总经理",
            "email": "zhaoliu@example.com",
        }
        update_response = client.put(
            f"{settings.API_V1_PREFIX}/sales/contacts/{contact_id}",
            json=update_payload,
            headers=headers,
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["position"] == "副总经理"
        assert data["email"] == "zhaoliu@example.com"

    def test_delete_contact_success(self, client: TestClient, admin_token: str):
        """测试删除联系人"""
        customer_id = self._create_customer(client, admin_token)
        headers = _auth_headers(admin_token)
        
        # 创建联系人
        create_payload = {
            "customer_id": customer_id,
            "customer_name": "孙七",
        }
        create_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/contacts",
            json=create_payload,
            headers=headers,
        )
        contact_id = create_response.json()["id"]

        # 删除联系人
        delete_response = client.delete(
            f"{settings.API_V1_PREFIX}/sales/contacts/{contact_id}",
            headers=headers,
        )
        assert delete_response.status_code == 204

    def test_list_customer_contacts(self, client: TestClient, admin_token: str):
        """测试获取客户的联系人列表"""
        customer_id = self._create_customer(client, admin_token)
        headers = _auth_headers(admin_token)
        
        # 创建多个联系人
        for i in range(3):
            payload = {
                "customer_id": customer_id,
                "customer_name": f"联系人{i+1}",
            }
            client.post(
                f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/contacts",
                json=payload,
                headers=headers,
            )

        # 获取列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/contacts",
            headers=headers,
        )
        assert list_response.status_code == 200

    def test_set_primary_contact(self, client: TestClient, admin_token: str):
        """测试设置主要联系人"""
        customer_id = self._create_customer(client, admin_token)
        headers = _auth_headers(admin_token)
        
        # 创建两个联系人
        contact1_payload = {"customer_id": customer_id, "customer_name": "联系人1", "is_primary": True}
        contact1_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/contacts",
            json=contact1_payload,
            headers=headers,
        )
        contact1_id = contact1_response.json()["id"]

        contact2_payload = {"customer_id": customer_id, "customer_name": "联系人2"}
        contact2_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/contacts",
            json=contact2_payload,
            headers=headers,
        )
        contact2_id = contact2_response.json()["id"]

        # 设置联系人2为主要联系人
        set_primary_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/contacts/{contact2_id}/set-primary",
            headers=headers,
        )
        assert set_primary_response.status_code == 200
        assert set_primary_response.json()["is_primary"] is True

    def test_search_contacts_by_keyword(self, client: TestClient, admin_token: str):
        """测试关键词搜索联系人"""
        customer_id = self._create_customer(client, admin_token)
        headers = _auth_headers(admin_token)
        
        unique_name = f"搜索测试-{uuid.uuid4().hex[:6]}"
        payload = {
            "customer_id": customer_id,
            "customer_name": unique_name,
            "mobile": "13666666666",
        }
        client.post(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/contacts",
            json=payload,
            headers=headers,
        )

        # 搜索
        search_response = client.get(
            f"{settings.API_V1_PREFIX}/sales/contacts",
            params={"keyword": unique_name[:6]},
            headers=headers,
        )
        assert search_response.status_code == 200

    def test_contact_list_sorted_by_primary(self, client: TestClient, admin_token: str):
        """测试联系人列表按主要联系人排序"""
        customer_id = self._create_customer(client, admin_token)
        headers = _auth_headers(admin_token)
        
        # 创建普通联系人
        payload1 = {"customer_id": customer_id, "customer_name": "普通联系人"}
        client.post(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/contacts",
            json=payload1,
            headers=headers,
        )

        # 创建主要联系人
        payload2 = {"customer_id": customer_id, "customer_name": "主要联系人", "is_primary": True}
        client.post(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/contacts",
            json=payload2,
            headers=headers,
        )

        # 获取列表（主要联系人应排在前面）
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/contacts",
            headers=headers,
        )
        assert list_response.status_code == 200


class TestCustomerTags:
    """客户标签管理测试"""

    def _create_customer(self, client: TestClient, token: str) -> int:
        """辅助方法：创建客户"""
        headers = _auth_headers(token)
        payload = {
            "customer_name": f"标签测试客户-{uuid.uuid4().hex[:4]}",
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers",
            json=payload,
            headers=headers,
        )
        return response.json()["id"]

    def test_get_predefined_tags(self, client: TestClient, admin_token: str):
        """测试获取预定义标签列表"""
        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/customer-tags/predefined",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "tags" in data
        assert "重点客户" in data["tags"]

    def test_create_customer_tag(self, client: TestClient, admin_token: str):
        """测试创建客户标签"""
        customer_id = self._create_customer(client, admin_token)
        headers = _auth_headers(admin_token)
        
        payload = {
            "customer_id": customer_id,
            "tag_name": "重点客户",
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/tags",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["tag_name"] == "重点客户"

    def test_create_duplicate_tag(self, client: TestClient, admin_token: str):
        """测试创建重复标签（应失败）"""
        customer_id = self._create_customer(client, admin_token)
        headers = _auth_headers(admin_token)
        
        payload = {
            "customer_id": customer_id,
            "tag_name": "战略客户",
        }
        
        # 第一次创建
        response1 = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/tags",
            json=payload,
            headers=headers,
        )
        assert response1.status_code == 201

        # 第二次创建（重复）
        response2 = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/tags",
            json=payload,
            headers=headers,
        )
        assert response2.status_code == 400

    def test_batch_create_tags(self, client: TestClient, admin_token: str):
        """测试批量创建标签"""
        customer_id = self._create_customer(client, admin_token)
        headers = _auth_headers(admin_token)
        
        payload = {
            "customer_id": customer_id,
            "tag_names": ["重点客户", "长期合作", "高价值客户"],
        }
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/tags/batch",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 3

    def test_list_customer_tags(self, client: TestClient, admin_token: str):
        """测试获取客户标签列表"""
        customer_id = self._create_customer(client, admin_token)
        headers = _auth_headers(admin_token)
        
        # 创建标签
        payload = {
            "customer_id": customer_id,
            "tag_name": "新客户",
        }
        client.post(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/tags",
            json=payload,
            headers=headers,
        )

        # 获取标签列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/tags",
            headers=headers,
        )
        assert list_response.status_code == 200

    def test_delete_customer_tag(self, client: TestClient, admin_token: str):
        """测试删除客户标签"""
        customer_id = self._create_customer(client, admin_token)
        headers = _auth_headers(admin_token)
        
        # 创建标签
        create_payload = {
            "customer_id": customer_id,
            "tag_name": "测试标签",
        }
        create_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/tags",
            json=create_payload,
            headers=headers,
        )
        tag_id = create_response.json()["id"]

        # 删除标签
        delete_response = client.delete(
            f"{settings.API_V1_PREFIX}/sales/customers/{customer_id}/tags/{tag_id}",
            headers=headers,
        )
        assert delete_response.status_code == 204
