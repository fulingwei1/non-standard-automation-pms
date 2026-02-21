# -*- coding: utf-8 -*-
"""
Schemas 测试的 Fixtures
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal


@pytest.fixture
def sample_project_data():
    """示例项目数据"""
    return {
        "project_code": "PRJ001",
        "project_name": "测试项目",
        "customer_id": 1,
        "pm_id": 1,
        "contract_amount": 100000.00,
        "planned_start_date": date.today(),
        "planned_end_date": date.today() + timedelta(days=90)
    }


@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "real_name": "测试用户"
    }


@pytest.fixture
def sample_customer_data():
    """示例客户数据"""
    return {
        "customer_name": "测试客户",
        "customer_code": "CUST001",
        "customer_type": "企业",
        "contact_person": "张三",
        "contact_phone": "13800138000"
    }
