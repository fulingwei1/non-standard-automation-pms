"""
负荷管理和预警API测试
"""
import pytest


class TestWorkloadAPI:
    """负荷管理API测试"""
    
    @pytest.mark.unit
    def test_get_user_workload(self, client):
        """测试获取用户负荷"""
        response = client.get("/api/v1/workload/user/1", params={
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "summary" in data["data"]
        assert "by_project" in data["data"]
    
    @pytest.mark.unit
    def test_get_team_workload(self, client):
        """测试获取团队负荷"""
        response = client.get("/api/v1/workload/team", params={
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)
    
    @pytest.mark.unit
    def test_team_workload_by_dept(self, client):
        """测试按部门获取团队负荷"""
        response = client.get("/api/v1/workload/team", params={
            "dept_id": 1
        })
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_get_workload_heatmap(self, client):
        """测试获取负荷热力图"""
        response = client.get("/api/v1/workload/heatmap", params={
            "start_date": "2025-01-01",
            "weeks": 4
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "users" in data["data"]
        assert "weeks" in data["data"]
        assert "data" in data["data"]
    
    @pytest.mark.unit
    def test_get_available_resources(self, client):
        """测试获取可用资源"""
        response = client.get("/api/v1/workload/available", params={
            "start_date": "2025-01-15",
            "end_date": "2025-01-31",
            "min_hours": 8
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)
    
    @pytest.mark.unit
    def test_available_resources_by_skill(self, client):
        """测试按技能筛选可用资源"""
        response = client.get("/api/v1/workload/available", params={
            "skill": "电气设计",
            "min_hours": 16
        })
        assert response.status_code == 200


class TestWorkloadCalculation:
    """负荷计算测试"""
    
    @pytest.mark.unit
    def test_allocation_rate_calculation(self, client):
        """测试负荷率计算"""
        response = client.get("/api/v1/workload/user/1", params={
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        })
        assert response.status_code == 200
        data = response.json()
        summary = data["data"]["summary"]
        
        # 验证负荷率计算公式
        assigned = summary.get("total_assigned_hours", 0)
        standard = summary.get("standard_hours", 176)
        expected_rate = round(assigned / standard * 100, 1) if standard > 0 else 0
        actual_rate = summary.get("allocation_rate", 0)
        
        assert abs(expected_rate - actual_rate) < 1  # 允许1%误差


class TestAlertAPI:
    """预警API测试"""
    
    @pytest.mark.unit
    def test_get_alert_list(self, client):
        """测试获取预警列表"""
        response = client.get("/api/v1/alerts", params={
            "status": "待处理"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "list" in data["data"]
    
    @pytest.mark.unit
    def test_get_alert_list_by_level(self, client):
        """测试按级别获取预警"""
        response = client.get("/api/v1/alerts", params={
            "alert_level": "红"
        })
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_get_alert_list_by_type(self, client):
        """测试按类型获取预警"""
        response = client.get("/api/v1/alerts", params={
            "alert_type": "任务逾期"
        })
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_get_alert_detail(self, client):
        """测试获取预警详情"""
        response = client.get("/api/v1/alerts/1")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "alert_id" in data["data"]
        assert "alert_type" in data["data"]
        assert "alert_level" in data["data"]
    
    @pytest.mark.unit
    def test_handle_alert(self, client):
        """测试处理预警"""
        response = client.put("/api/v1/alerts/1/handle", json={
            "action": "处理中",
            "comment": "正在跟进处理"
        })
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_resolve_alert(self, client):
        """测试解决预警"""
        response = client.put("/api/v1/alerts/1/handle", json={
            "action": "已解决",
            "comment": "问题已解决"
        })
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_ignore_alert(self, client):
        """测试忽略预警"""
        response = client.put("/api/v1/alerts/1/handle", json={
            "action": "忽略",
            "comment": "非关键问题，暂时忽略"
        })
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_get_alert_statistics(self, client):
        """测试获取预警统计"""
        response = client.get("/api/v1/alerts/statistics", params={
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "summary" in data["data"]
        assert "by_level" in data["data"]
        assert "by_type" in data["data"]
    
    @pytest.mark.unit
    def test_trigger_alert_check(self, client):
        """测试触发预警检查"""
        response = client.post("/api/v1/alerts/check")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200


class TestAlertRules:
    """预警规则测试"""
    
    @pytest.mark.unit
    def test_overdue_task_alert(self, client):
        """测试任务逾期预警生成"""
        # 先触发预警检查
        response = client.post("/api/v1/alerts/check")
        assert response.status_code == 200
        
        # 检查是否生成了逾期预警
        response = client.get("/api/v1/alerts", params={
            "alert_type": "任务逾期"
        })
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_progress_delay_alert(self, client):
        """测试进度滞后预警"""
        response = client.get("/api/v1/alerts", params={
            "alert_type": "进度滞后"
        })
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_overload_alert(self, client):
        """测试负荷过高预警"""
        response = client.get("/api/v1/alerts", params={
            "alert_type": "负荷过高"
        })
        assert response.status_code == 200
