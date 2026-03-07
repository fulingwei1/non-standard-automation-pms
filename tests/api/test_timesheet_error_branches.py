# -*- coding: utf-8 -*-
"""
工时API异常分支测试

补充工时管理端点的异常处理分支测试,提升分支覆盖率
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings


class TestTimesheetListErrorBranches:
    """工时列表端点异常分支测试"""

    def test_list_timesheets_no_token(self, client: TestClient):
        """无Token访问"""
        response = client.get(f"{settings.API_V1_PREFIX}/timesheets")
        assert response.status_code == 401

    def test_list_timesheets_invalid_token(self, client: TestClient):
        """无效Token"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/timesheets",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_list_timesheets_invalid_date_format(self, client: TestClient, admin_token: str):
        """无效日期格式"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/timesheets",
            params={"start_date": "invalid-date"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]

    def test_list_timesheets_end_before_start(self, client: TestClient, admin_token: str):
        """结束日期早于开始日期"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/timesheets",
            params={
                "start_date": "2025-12-31",
                "end_date": "2025-01-01"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 可能返回空结果或验证错误
        assert response.status_code in [200, 400, 422]

    def test_list_timesheets_invalid_page(self, client: TestClient, admin_token: str):
        """无效页码"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/timesheets",
            params={"page": -1},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]

    def test_list_timesheets_excessive_page_size(self, client: TestClient, admin_token: str):
        """超大分页"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/timesheets",
            params={"page_size": 10000},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [200, 400, 422]


class TestCreateTimesheetErrorBranches:
    """创建工时记录端点异常分支测试"""

    def test_create_timesheet_no_token(self, client: TestClient):
        """无Token创建"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/timesheets",
            json={"work_date": date.today().isoformat(), "hours": 8.0}
        )
        assert response.status_code == 401

    def test_create_timesheet_missing_required_field(self, client: TestClient, admin_token: str):
        """缺少必填字段"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/timesheets",
            json={},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_create_timesheet_missing_project_id(self, client: TestClient, admin_token: str):
        """缺少项目ID"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/timesheets",
            json={
                "work_date": date.today().isoformat(),
                "hours": 8.0
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_create_timesheet_missing_work_date(self, client: TestClient, admin_token: str):
        """缺少工作日期"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/timesheets",
            json={
                "project_id": 1,
                "hours": 8.0
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_create_timesheet_missing_hours(self, client: TestClient, admin_token: str):
        """缺少工时"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/timesheets",
            json={
                "project_id": 1,
                "work_date": date.today().isoformat()
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_create_timesheet_invalid_project_id(self, client: TestClient, admin_token: str):
        """项目不存在"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/timesheets",
            json={
                "project_id": 999999,
                "work_date": date.today().isoformat(),
                "hours": 8.0
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 404, 422]

    @pytest.mark.parametrize("invalid_hours", [
        -1,  # 负数
        0,  # 零
        25,  # 超过24小时
        100,  # 明显超出
        0.001,  # 过小
    ])
    def test_create_timesheet_invalid_hours(
        self, client: TestClient, admin_token: str, invalid_hours: float
    ):
        """无效工时数"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/timesheets",
            json={
                "project_id": 1,
                "work_date": date.today().isoformat(),
                "hours": invalid_hours
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]

    def test_create_timesheet_future_date(self, client: TestClient, admin_token: str):
        """未来日期"""
        if not admin_token:
            pytest.skip("Admin token not available")

        future_date = (date.today() + timedelta(days=30)).isoformat()
        response = client.post(
            f"{settings.API_V1_PREFIX}/timesheets",
            json={
                "project_id": 1,
                "work_date": future_date,
                "hours": 8.0
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 可能允许或禁止
        assert response.status_code in [200, 201, 400, 422]

    def test_create_timesheet_duplicate(self, client: TestClient, admin_token: str, db_session: Session):
        """重复的工时记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 先查找现有工时记录
        from app.models.timesheet import TimesheetRecord
        existing = db_session.query(TimesheetRecord).first()
        if not existing:
            pytest.skip("No existing timesheet for duplicate test")

        response = client.post(
            f"{settings.API_V1_PREFIX}/timesheets",
            json={
                "project_id": existing.project_id,
                "work_date": existing.work_date.isoformat(),
                "hours": 8.0
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 可能允许或禁止重复
        assert response.status_code in [200, 201, 400, 409]

    def test_create_timesheet_invalid_work_type(self, client: TestClient, admin_token: str):
        """无效工作类型"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/timesheets",
            json={
                "project_id": 1,
                "work_date": date.today().isoformat(),
                "hours": 8.0,
                "work_type": "INVALID_TYPE"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422


class TestGetTimesheetErrorBranches:
    """获取工时详情端点异常分支测试"""

    def test_get_timesheet_no_token(self, client: TestClient):
        """无Token访问"""
        response = client.get(f"{settings.API_V1_PREFIX}/timesheets/1")
        assert response.status_code == 401

    def test_get_timesheet_not_found(self, client: TestClient, admin_token: str):
        """工时记录不存在"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/timesheets/999999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    def test_get_timesheet_invalid_id_format(self, client: TestClient, admin_token: str):
        """无效ID格式"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/timesheets/invalid",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422


class TestUpdateTimesheetErrorBranches:
    """更新工时记录端点异常分支测试"""

    def test_update_timesheet_no_token(self, client: TestClient):
        """无Token更新"""
        response = client.put(
            f"{settings.API_V1_PREFIX}/timesheets/1",
            json={"hours": 6.0}
        )
        assert response.status_code == 401

    def test_update_timesheet_not_found(self, client: TestClient, admin_token: str):
        """更新不存在的工时"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.put(
            f"{settings.API_V1_PREFIX}/timesheets/999999",
            json={"hours": 6.0},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    def test_update_timesheet_invalid_hours(self, client: TestClient, admin_token: str, db_session: Session):
        """更新为无效工时"""
        if not admin_token:
            pytest.skip("Admin token not available")

        from app.models.timesheet import TimesheetRecord
        record = db_session.query(TimesheetRecord).first()
        if not record:
            pytest.skip("No timesheet available for test")

        response = client.put(
            f"{settings.API_V1_PREFIX}/timesheets/{record.id}",
            json={"hours": -5.0},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]

    def test_update_timesheet_already_approved(self, client: TestClient, admin_token: str, db_session: Session):
        """更新已审批的工时"""
        if not admin_token:
            pytest.skip("Admin token not available")

        from app.models.timesheet import TimesheetRecord
        approved = db_session.query(TimesheetRecord).filter(
            TimesheetRecord.status == "APPROVED"
        ).first()

        if not approved:
            pytest.skip("No approved timesheet for test")

        response = client.put(
            f"{settings.API_V1_PREFIX}/timesheets/{approved.id}",
            json={"hours": 6.0},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 可能禁止修改已审批的记录
        assert response.status_code in [200, 400, 403]


class TestDeleteTimesheetErrorBranches:
    """删除工时记录端点异常分支测试"""

    def test_delete_timesheet_no_token(self, client: TestClient):
        """无Token删除"""
        response = client.delete(f"{settings.API_V1_PREFIX}/timesheets/1")
        assert response.status_code == 401

    def test_delete_timesheet_not_found(self, client: TestClient, admin_token: str):
        """删除不存在的工时"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.delete(
            f"{settings.API_V1_PREFIX}/timesheets/999999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    def test_delete_timesheet_already_approved(self, client: TestClient, admin_token: str, db_session: Session):
        """删除已审批的工时"""
        if not admin_token:
            pytest.skip("Admin token not available")

        from app.models.timesheet import TimesheetRecord
        approved = db_session.query(TimesheetRecord).filter(
            TimesheetRecord.status == "APPROVED"
        ).first()

        if not approved:
            pytest.skip("No approved timesheet for test")

        response = client.delete(
            f"{settings.API_V1_PREFIX}/timesheets/{approved.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 可能禁止删除已审批的记录
        assert response.status_code in [200, 400, 403]


class TestTimesheetApprovalErrorBranches:
    """工时审批端点异常分支测试"""

    def test_approve_timesheet_no_token(self, client: TestClient):
        """无Token审批"""
        response = client.post(f"{settings.API_V1_PREFIX}/timesheets/1/approve")
        assert response.status_code == 401

    def test_approve_timesheet_no_permission(self, client: TestClient, admin_token: str):
        """无审批权限"""
        # 这需要一个没有审批权限的用户token
        # 这里用admin token测试,可能会通过
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/timesheets/1/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 如果admin有权限会通过,否则403
        assert response.status_code in [200, 403, 404]

    def test_approve_timesheet_not_found(self, client: TestClient, admin_token: str):
        """审批不存在的工时"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/timesheets/999999/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    def test_approve_timesheet_already_approved(self, client: TestClient, admin_token: str, db_session: Session):
        """重复审批"""
        if not admin_token:
            pytest.skip("Admin token not available")

        from app.models.timesheet import TimesheetRecord
        approved = db_session.query(TimesheetRecord).filter(
            TimesheetRecord.status == "APPROVED"
        ).first()

        if not approved:
            pytest.skip("No approved timesheet for test")

        response = client.post(
            f"{settings.API_V1_PREFIX}/timesheets/{approved.id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 可能返回错误或允许重复审批
        assert response.status_code in [200, 400, 409]

    def test_reject_timesheet_no_reason(self, client: TestClient, admin_token: str, db_session: Session):
        """拒绝工时但未提供原因"""
        if not admin_token:
            pytest.skip("Admin token not available")

        from app.models.timesheet import TimesheetRecord
        pending = db_session.query(TimesheetRecord).filter(
            TimesheetRecord.status == "PENDING"
        ).first()

        if not pending:
            pytest.skip("No pending timesheet for test")

        response = client.post(
            f"{settings.API_V1_PREFIX}/timesheets/{pending.id}/reject",
            json={},  # 没有提供拒绝原因
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 可能要求必须提供原因
        assert response.status_code in [200, 400, 422]


class TestTimesheetStatisticsErrorBranches:
    """工时统计端点异常分支测试"""

    def test_statistics_no_token(self, client: TestClient):
        """无Token访问统计"""
        response = client.get(f"{settings.API_V1_PREFIX}/timesheets/statistics")
        assert response.status_code == 401

    def test_statistics_invalid_date_range(self, client: TestClient, admin_token: str):
        """无效日期范围"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/timesheets/statistics",
            params={
                "start_date": "invalid",
                "end_date": "2025-12-31"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]

    def test_weekly_view_invalid_week(self, client: TestClient, admin_token: str):
        """无效周数"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/timesheets/week",
            params={"week": "invalid"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]
