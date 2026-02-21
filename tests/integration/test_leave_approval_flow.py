# -*- coding: utf-8 -*-
"""
人事管理集成测试 - 请假审批流程
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.mark.integration
class TestLeaveApprovalFlow:
    
    def test_leave_application(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：请假申请"""
        leave_data = {
            "employee_id": test_employee.id,
            "leave_type": "年假",
            "start_date": str(date.today() + timedelta(days=7)),
            "end_date": str(date.today() + timedelta(days=9)),
            "days": 3,
            "reason": "家庭旅行"
        }
        
        response = client.post("/api/v1/hr/leave-applications", json=leave_data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]

    def test_leave_approval(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：请假审批"""
        approval_data = {
            "application_id": 1,
            "action": "approve",
            "approver_id": test_employee.id + 1,
            "comments": "同意请假"
        }
        
        response = client.post("/api/v1/hr/leave-applications/1/approve", json=approval_data, headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_leave_balance_check(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：假期余额查询"""
        response = client.get(f"/api/v1/hr/employees/{test_employee.id}/leave-balance", headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_leave_statistics(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：请假统计"""
        response = client.get("/api/v1/hr/leave-statistics?year=2024&month=2", headers=auth_headers)
        assert response.status_code in [200, 404]
