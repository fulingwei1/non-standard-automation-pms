"""API端点测试 - 额外测试"""
import pytest
from fastapi.testclient import TestClient


class TestAPIEndpoints:
    """API端点测试"""

    def test_root_endpoint(self, client):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AI智能话术推荐引擎"
        assert data["version"] == "1.0.0"

    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_get_script_library_endpoint(self, client):
        """测试获取话术库API"""
        response = client.get("/api/v1/presale/ai/script-library")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "scripts" in data

    def test_add_script_template_endpoint(self, client):
        """测试添加话术模板API"""
        payload = {
            "scenario": "first_contact",
            "script_content": "测试话术内容",
            "customer_type": "technical",
            "tags": ["测试"],
            "success_rate": 85.5
        }
        response = client.post("/api/v1/presale/ai/add-script-template", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["script_content"] == "测试话术内容"

    def test_script_feedback_endpoint(self, client):
        """测试话术反馈API"""
        payload = {
            "script_id": 1,
            "is_effective": True,
            "feedback_notes": "效果很好"
        }
        response = client.post("/api/v1/presale/ai/script-feedback", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True

    def test_get_sales_scripts_by_scenario(self, client):
        """测试按场景获取话术"""
        response = client.get("/api/v1/presale/ai/sales-scripts/first_contact?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
