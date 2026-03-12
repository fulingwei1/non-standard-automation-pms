# -*- coding: utf-8 -*-
"""
销售模块 API 集成测试 - 共享 Fixtures

提供认证、测试数据等共享资源
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture(scope="module")
def auth_headers(client: TestClient, admin_token: str) -> dict:
    """获取认证请求头"""
    if not admin_token:
        pytest.skip("无法获取管理员 token")
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def test_customer(client: TestClient, auth_headers: dict) -> dict:
    """创建测试客户，供商机测试使用"""
    from app.models.base import SessionLocal
    from app.models.project import Customer

    db = SessionLocal()
    try:
        # 检查是否已有测试客户
        existing = db.query(Customer).filter(Customer.customer_name == "集成测试客户").first()
        if existing:
            return {"id": existing.id, "customer_name": existing.customer_name}

        # 创建测试客户
        customer = Customer(
            customer_code="TEST-CUST-001",
            customer_name="集成测试客户",
            customer_type="企业",
            industry="制造业",
            contact_person="测试联系人",
            contact_phone="13800138000",
            status="ACTIVE",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return {"id": customer.id, "customer_name": customer.customer_name}
    finally:
        db.close()


@pytest.fixture(scope="module")
def test_opportunity_data(test_customer: dict) -> dict:
    """商机测试数据"""
    return {
        "customer_id": test_customer["id"],
        "opp_name": "集成测试商机-自动化设备项目",
        "project_type": "NPI",
        "equipment_type": "FCT测试",
        "stage": "DISCOVERY",
        "probability": 30,
        "est_amount": "1500000.00",
        "est_margin": "35.00",
    }


@pytest.fixture(scope="module")
def created_opportunity(
    client: TestClient, auth_headers: dict, test_opportunity_data: dict
) -> dict:
    """创建一个商机用于后续测试"""
    response = client.post(
        "/api/v1/sales/opportunities",
        json=test_opportunity_data,
        headers=auth_headers,
    )
    if response.status_code == 201:
        return response.json()
    elif response.status_code == 400 and "已存在" in response.text:
        # 商机已存在，尝试获取
        list_resp = client.get(
            "/api/v1/sales/opportunities",
            params={"keyword": test_opportunity_data["opp_name"]},
            headers=auth_headers,
        )
        if list_resp.status_code == 200:
            items = list_resp.json().get("items", [])
            if items:
                return items[0]
    pytest.skip(f"无法创建测试商机: {response.status_code} - {response.text}")
