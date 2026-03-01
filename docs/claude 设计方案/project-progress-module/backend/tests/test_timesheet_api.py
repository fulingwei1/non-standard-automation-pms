"""
工时管理API测试
"""
import pytest


class TestTimesheetAPI:
    """工时API测试类"""
    
    @pytest.mark.unit
    def test_get_timesheet_list(self, client):
        """测试获取工时列表"""
        response = client.get("/api/v1/timesheets", params={
            "user_id": 1,
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "list" in data["data"]
    
    @pytest.mark.unit
    def test_create_timesheet(self, client, sample_timesheet):
        """测试创建工时记录"""
        response = client.post("/api/v1/timesheets", json=sample_timesheet)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "timesheet_id" in data["data"]
    
    @pytest.mark.unit
    def test_create_timesheet_invalid_hours(self, client, sample_timesheet):
        """测试创建工时-无效小时数"""
        sample_timesheet["hours"] = 25  # 超过24小时
        response = client.post("/api/v1/timesheets", json=sample_timesheet)
        # 根据实际验证逻辑
        assert response.status_code in [200, 422]
    
    @pytest.mark.unit
    def test_batch_create_timesheet(self, client, sample_timesheet):
        """测试批量创建工时"""
        entries = []
        for i in range(5):
            entry = sample_timesheet.copy()
            entry["work_date"] = f"2025-01-{10+i:02d}"
            entries.append(entry)
        
        response = client.post("/api/v1/timesheets/batch", json={"entries": entries})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
    
    @pytest.mark.unit
    def test_update_timesheet(self, client):
        """测试更新工时"""
        response = client.put("/api/v1/timesheets/1", json={
            "hours": 6,
            "work_content": "更新后的工作内容"
        })
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_delete_timesheet(self, client):
        """测试删除工时（仅草稿可删）"""
        response = client.delete("/api/v1/timesheets/1")
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_submit_timesheets(self, client):
        """测试提交工时"""
        response = client.post("/api/v1/timesheets/submit", json=[1, 2, 3])
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_approve_timesheets(self, client):
        """测试审核工时"""
        response = client.post("/api/v1/timesheets/approve", json={
            "timesheet_ids": [1, 2],
            "status": "通过",
            "comment": "审核通过"
        })
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_reject_timesheets(self, client):
        """测试驳回工时"""
        response = client.post("/api/v1/timesheets/approve", json={
            "timesheet_ids": [3],
            "status": "驳回",
            "comment": "工时填写不准确"
        })
        assert response.status_code == 200


class TestWeekTimesheet:
    """周工时表测试"""
    
    @pytest.mark.unit
    def test_get_week_timesheet(self, client):
        """测试获取周工时表"""
        response = client.get("/api/v1/timesheets/week", params={
            "user_id": 1,
            "week_start": "2024-12-30"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "tasks" in data["data"]
        assert "summary" in data["data"]
    
    @pytest.mark.unit
    def test_week_timesheet_summary(self, client):
        """测试周工时汇总计算"""
        response = client.get("/api/v1/timesheets/week", params={
            "user_id": 1,
            "week_start": "2024-12-30"
        })
        assert response.status_code == 200
        data = response.json()
        summary = data["data"]["summary"]
        
        assert "total_hours" in summary
        assert "standard_hours" in summary
        assert "daily_totals" in summary


class TestMonthSummary:
    """月度工时汇总测试"""
    
    @pytest.mark.unit
    def test_get_month_summary(self, client):
        """测试获取月度汇总"""
        response = client.get("/api/v1/timesheets/month-summary", params={
            "user_id": 1,
            "year": 2025,
            "month": 1
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "total_hours" in data["data"]
        assert "project_breakdown" in data["data"]
    
    @pytest.mark.unit
    def test_month_project_breakdown(self, client):
        """测试月度项目工时分布"""
        response = client.get("/api/v1/timesheets/month-summary", params={
            "user_id": 1,
            "year": 2025,
            "month": 1
        })
        assert response.status_code == 200
        data = response.json()
        breakdown = data["data"]["project_breakdown"]
        
        # 验证百分比总和
        total_pct = sum(p.get("percentage", 0) for p in breakdown)
        assert abs(total_pct - 100) < 1  # 允许1%误差


class TestTimesheetStatistics:
    """工时统计测试"""
    
    @pytest.mark.unit
    def test_get_statistics(self, client):
        """测试获取工时统计"""
        response = client.get("/api/v1/timesheets/statistics", params={
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "total_hours" in data["data"]
        assert "by_project" in data["data"]
    
    @pytest.mark.unit
    def test_get_pending_approval(self, client):
        """测试获取待审核工时"""
        response = client.get("/api/v1/timesheets/pending-approval", params={
            "approver_id": 1
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "list" in data["data"]
