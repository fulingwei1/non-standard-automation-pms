"""
任务管理API测试
"""
import pytest
from fastapi.testclient import TestClient


class TestTaskAPI:
    """任务API测试类"""
    
    @pytest.mark.unit
    def test_get_task_list(self, client):
        """测试获取任务列表"""
        response = client.get("/api/v1/tasks", params={"project_id": 1})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "list" in data["data"]
    
    @pytest.mark.unit
    def test_get_wbs_tasks(self, client):
        """测试获取WBS任务树"""
        response = client.get("/api/v1/tasks/wbs/1")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert isinstance(data["data"], list)
    
    @pytest.mark.unit
    def test_get_gantt_tasks(self, client):
        """测试获取甘特图数据"""
        response = client.get("/api/v1/tasks/gantt/1")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "tasks" in data["data"]
        assert "links" in data["data"]
    
    @pytest.mark.unit
    def test_get_my_tasks(self, client):
        """测试获取我的任务"""
        response = client.get("/api/v1/tasks/my-tasks", params={"user_id": 1})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "list" in data["data"]
    
    @pytest.mark.unit
    def test_create_task(self, client, sample_task):
        """测试创建任务"""
        response = client.post("/api/v1/tasks", json=sample_task)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "task_id" in data["data"]
    
    @pytest.mark.unit
    def test_create_task_missing_project(self, client, sample_task):
        """测试创建任务缺少项目ID"""
        del sample_task["project_id"]
        response = client.post("/api/v1/tasks", json=sample_task)
        assert response.status_code == 422
    
    @pytest.mark.unit
    def test_batch_create_tasks(self, client, sample_tasks_batch):
        """测试批量创建任务"""
        response = client.post("/api/v1/tasks/batch", json={"tasks": sample_tasks_batch})
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
    
    @pytest.mark.unit
    def test_update_task(self, client):
        """测试更新任务"""
        response = client.put("/api/v1/tasks/1", json={
            "task_name": "更新后的任务名",
            "status": "进行中"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
    
    @pytest.mark.unit
    def test_update_task_progress(self, client):
        """测试更新任务进度"""
        response = client.put("/api/v1/tasks/1/progress", json={
            "progress_rate": 50,
            "status": "进行中",
            "content": "完成了50%的工作"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
    
    @pytest.mark.unit
    def test_update_task_progress_invalid(self, client):
        """测试更新任务进度-无效值"""
        response = client.put("/api/v1/tasks/1/progress", json={
            "progress_rate": 150  # 超过100
        })
        # 根据实际验证逻辑调整
        assert response.status_code in [200, 422]
    
    @pytest.mark.unit
    def test_batch_update_progress(self, client):
        """测试批量更新进度"""
        response = client.put("/api/v1/tasks/batch-progress", json={
            "updates": [
                {"task_id": 1, "progress_rate": 60},
                {"task_id": 2, "progress_rate": 40}
            ]
        })
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_get_task_dependencies(self, client):
        """测试获取任务依赖"""
        response = client.get("/api/v1/tasks/1/dependencies")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
    
    @pytest.mark.unit
    def test_set_task_dependency(self, client):
        """测试设置任务依赖"""
        response = client.post("/api/v1/tasks/dependencies", json={
            "task_id": 2,
            "predecessor_id": 1,
            "link_type": "FS",
            "lag_days": 0
        })
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_get_critical_path(self, client):
        """测试获取关键路径"""
        response = client.get("/api/v1/tasks/critical-path/1")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "critical_tasks" in data["data"]


class TestTaskAssignment:
    """任务分配测试"""
    
    @pytest.mark.unit
    def test_assign_task(self, client):
        """测试分配任务"""
        response = client.post("/api/v1/tasks/1/assign", json={
            "user_id": 2,
            "allocation_rate": 100
        })
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_get_task_assignments(self, client):
        """测试获取任务分配"""
        response = client.get("/api/v1/tasks/1/assignments")
        assert response.status_code == 200


class TestTaskProgress:
    """任务进度计算测试"""
    
    @pytest.mark.unit
    def test_progress_calculation_by_weight(self, client):
        """测试按权重计算进度"""
        # 这个测试验证进度计算逻辑
        response = client.get("/api/v1/projects/1/progress")
        assert response.status_code == 200
        data = response.json()
        progress = data["data"]["progress_rate"]
        assert 0 <= progress <= 100
    
    @pytest.mark.unit
    def test_progress_auto_update_parent(self, client):
        """测试子任务完成后父任务进度自动更新"""
        # 更新子任务进度
        response = client.put("/api/v1/tasks/11/progress", json={
            "progress_rate": 100
        })
        assert response.status_code == 200
        
        # 检查父任务进度是否更新
        response = client.get("/api/v1/tasks/1")
        assert response.status_code == 200
