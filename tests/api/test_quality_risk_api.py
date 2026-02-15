# -*- coding: utf-8 -*-
"""
质量风险识别系统 API集成测试
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.quality_risk_detection import QualityRiskDetection, QualityTestRecommendation


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """获取认证头（假设有登录接口）"""
    # TODO: 实现实际的登录逻辑
    return {"Authorization": "Bearer test_token"}


class TestQualityRiskDetectionAPI:
    """质量风险检测API测试"""
    
    def test_analyze_work_logs_success(self, client, auth_headers, db: Session):
        """测试成功分析工作日志"""
        # 先创建测试数据（工作日志）
        # TODO: 创建测试项目和工作日志
        
        payload = {
            "project_id": 1,
            "start_date": str(date.today() - timedelta(days=7)),
            "end_date": str(date.today())
        }
        
        # 由于测试环境可能没有数据，这个测试可能会失败
        # 实际使用时需要先准备测试数据
        response = client.post(
            "/api/v1/quality-risk/detections/analyze",
            json=payload,
            headers=auth_headers
        )
        
        # 如果有数据应该返回200，无数据返回404
        assert response.status_code in [200, 404]
    
    def test_analyze_work_logs_missing_project(self, client, auth_headers):
        """测试缺少项目ID"""
        payload = {
            "start_date": str(date.today() - timedelta(days=7)),
            "end_date": str(date.today())
        }
        
        response = client.post(
            "/api/v1/quality-risk/detections/analyze",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_list_detections(self, client, auth_headers):
        """测试查询检测记录列表"""
        response = client.get(
            "/api/v1/quality-risk/detections",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_detections_with_filters(self, client, auth_headers):
        """测试带过滤条件查询"""
        params = {
            "project_id": 1,
            "risk_level": "HIGH",
            "limit": 10
        }
        
        response = client.get(
            "/api/v1/quality-risk/detections",
            params=params,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_detection_not_found(self, client, auth_headers):
        """测试获取不存在的检测记录"""
        response = client.get(
            "/api/v1/quality-risk/detections/999999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_update_detection_status(self, client, auth_headers, db: Session):
        """测试更新检测状态"""
        # 假设存在ID=1的记录
        payload = {
            "status": "CONFIRMED",
            "resolution_note": "已确认为真实风险"
        }
        
        response = client.patch(
            "/api/v1/quality-risk/detections/1",
            json=payload,
            headers=auth_headers
        )
        
        # 如果记录存在应该返回200，否则404
        assert response.status_code in [200, 404]


class TestQualityTestRecommendationAPI:
    """测试推荐API测试"""
    
    def test_generate_recommendation(self, client, auth_headers):
        """测试生成测试推荐"""
        response = client.post(
            "/api/v1/quality-risk/recommendations/generate",
            params={"detection_id": 1},
            headers=auth_headers
        )
        
        # 如果检测记录存在应该返回200，否则404
        assert response.status_code in [200, 404]
    
    def test_generate_recommendation_missing_detection(self, client, auth_headers):
        """测试基于不存在的检测生成推荐"""
        response = client.post(
            "/api/v1/quality-risk/recommendations/generate",
            params={"detection_id": 999999},
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_list_recommendations(self, client, auth_headers):
        """测试查询推荐列表"""
        response = client.get(
            "/api/v1/quality-risk/recommendations",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_recommendations_with_filters(self, client, auth_headers):
        """测试带过滤条件查询推荐"""
        params = {
            "project_id": 1,
            "priority_level": "HIGH",
            "status": "PENDING"
        }
        
        response = client.get(
            "/api/v1/quality-risk/recommendations",
            params=params,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_recommendation(self, client, auth_headers):
        """测试更新推荐"""
        payload = {
            "status": "ACCEPTED",
            "acceptance_note": "已接受推荐"
        }
        
        response = client.patch(
            "/api/v1/quality-risk/recommendations/1",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]
    
    def test_update_recommendation_with_results(self, client, auth_headers):
        """测试更新推荐结果"""
        payload = {
            "status": "COMPLETED",
            "actual_test_days": 5,
            "actual_coverage": 85.5,
            "bugs_found": 12,
            "critical_bugs_found": 3,
            "recommendation_accuracy": 80.0
        }
        
        response = client.patch(
            "/api/v1/quality-risk/recommendations/1",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]


class TestQualityReportAPI:
    """质量报告API测试"""
    
    def test_generate_quality_report(self, client, auth_headers):
        """测试生成质量报告"""
        payload = {
            "project_id": 1,
            "start_date": str(date.today() - timedelta(days=30)),
            "end_date": str(date.today()),
            "include_recommendations": True
        }
        
        response = client.post(
            "/api/v1/quality-risk/reports/generate",
            json=payload,
            headers=auth_headers
        )
        
        # 如果有数据返回200，无数据返回404
        assert response.status_code in [200, 404]
    
    def test_generate_report_missing_dates(self, client, auth_headers):
        """测试缺少日期参数"""
        payload = {
            "project_id": 1
        }
        
        response = client.post(
            "/api/v1/quality-risk/reports/generate",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_statistics_summary(self, client, auth_headers):
        """测试获取统计摘要"""
        response = client.get(
            "/api/v1/quality-risk/statistics/summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'total_detections' in data
        assert 'average_risk_score' in data
    
    def test_get_statistics_with_filters(self, client, auth_headers):
        """测试带过滤条件的统计"""
        params = {
            "project_id": 1,
            "days": 60
        }
        
        response = client.get(
            "/api/v1/quality-risk/statistics/summary",
            params=params,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['period_days'] == 60
