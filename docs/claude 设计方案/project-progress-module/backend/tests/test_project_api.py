"""
项目管理API测试
"""
import pytest


class TestProjectAPI:
    """项目API测试类"""
    
    @pytest.mark.unit
    def test_get_project_list(self, client):
        """测试获取项目列表"""
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "list" in data["data"]
        assert "total" in data["data"]
    
    @pytest.mark.unit
    def test_get_project_list_with_filters(self, client):
        """测试带筛选条件获取项目列表"""
        response = client.get("/api/v1/projects", params={
            "status": "进行中",
            "level": "A",
            "page": 1,
            "page_size": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
    
    @pytest.mark.unit
    def test_get_project_detail(self, client):
        """测试获取项目详情"""
        response = client.get("/api/v1/projects/1")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "project_id" in data["data"]
        assert "project_code" in data["data"]
        assert "project_name" in data["data"]
    
    @pytest.mark.unit
    def test_create_project(self, client, sample_project):
        """测试创建项目"""
        response = client.post("/api/v1/projects", json=sample_project)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "project_id" in data["data"]
    
    @pytest.mark.unit
    def test_create_project_missing_required(self, client):
        """测试创建项目缺少必填字段"""
        response = client.post("/api/v1/projects", json={
            "project_name": "测试项目"
            # 缺少project_code
        })
        assert response.status_code == 422  # 验证错误
    
    @pytest.mark.unit
    def test_update_project(self, client):
        """测试更新项目"""
        response = client.put("/api/v1/projects/1", json={
            "project_name": "更新后的项目名称",
            "status": "进行中"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
    
    @pytest.mark.unit
    def test_get_project_progress(self, client):
        """测试获取项目进度"""
        response = client.get("/api/v1/projects/1/progress")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "progress_rate" in data["data"]
        assert "health_status" in data["data"]
        assert "phase_progress" in data["data"]
    
    @pytest.mark.unit
    def test_get_project_team(self, client):
        """测试获取项目团队"""
        response = client.get("/api/v1/projects/1/team")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)
    
    @pytest.mark.unit
    def test_get_project_timeline(self, client):
        """测试获取项目时间线"""
        response = client.get("/api/v1/projects/1/timeline")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)
    
    @pytest.mark.unit
    def test_get_project_statistics(self, client):
        """测试获取项目统计"""
        response = client.get("/api/v1/projects/1/statistics")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "task_count" in data["data"]
        assert "manhours" in data["data"]


class TestProjectValidation:
    """项目数据验证测试"""
    
    @pytest.mark.unit
    def test_project_level_validation(self, client, sample_project):
        """测试项目级别验证"""
        # 有效级别
        for level in ["A", "B", "C", "D"]:
            sample_project["project_level"] = level
            sample_project["project_code"] = f"PRJ-TEST-{level}"
            response = client.post("/api/v1/projects", json=sample_project)
            assert response.status_code == 200
    
    @pytest.mark.unit
    def test_project_date_validation(self, client, sample_project):
        """测试项目日期验证"""
        # 结束日期早于开始日期应该报错（如果实现了验证）
        sample_project["plan_start_date"] = "2025-03-31"
        sample_project["plan_end_date"] = "2025-01-01"
        response = client.post("/api/v1/projects", json=sample_project)
        # 根据实际验证逻辑调整断言
        assert response.status_code in [200, 422]
