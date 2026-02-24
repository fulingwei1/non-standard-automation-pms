"""
负载测试
使用Locust进行负载测试
"""
import pytest

try:
    from locust import HttpUser, task, between
except ImportError:
    pytest.skip("locust not available", allow_module_level=True)
import time


class ProjectUser(HttpUser):
    """项目用户负载测试"""
    wait_time = between(1, 3)
    
    def on_start(self):
        """登录获取token"""
        response = self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        if response.status_code == 200:
            self.token = response.json().get('access_token')
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def list_projects(self):
        """列表查询 - 高频"""
        self.client.get("/api/projects", headers=self.headers)
    
    @task(2)
    def search_projects(self):
        """搜索 - 中频"""
        self.client.get("/api/projects/search?q=test", headers=self.headers)
    
    @task(1)
    def create_project(self):
        """创建 - 低频"""
        self.client.post(
            "/api/projects",
            json={"name": f"Load Test {time.time()}", "code": f"LT{int(time.time())}"},
            headers=self.headers
        )


class TestLoadTesting:
    """负载测试类"""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_can_import_locust(self):
        """测试Locust可用性"""
        try:
            from locust import HttpUser, task
            assert True
        except ImportError:
            pytest.skip("Locust未安装")
