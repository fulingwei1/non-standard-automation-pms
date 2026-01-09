# -*- coding: utf-8 -*-
"""
项目管理模块 - 健康度计算单元测试

Sprint 6.3: 健康度计算单元测试
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta
from app.core.config import settings
from app.models.project import Project, ProjectMilestone
from app.models.issue import Issue
from app.models.alert import AlertRecord, AlertRule
from app.models.enums import ProjectHealthEnum, IssueStatusEnum, IssueTypeEnum, AlertLevelEnum


class TestHealthCalculator:
    """健康度计算测试"""
    
    def test_health_h4_closed_project(self, client: TestClient, admin_token: str, db_session):
        """测试H4场景 - 已完结项目（ST30）"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        project_data = {
            "project_code": "PJ250101H01",
            "project_name": "健康度测试-已结项",
            "customer_id": 1,
            "status": "ST30",  # 已结项
            "health": "H1",  # 初始健康度
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json=project_data,
            headers=headers
        )
        
        if response.status_code == 201:
            project_id = response.json()["id"]
            
            # 手动触发健康度计算
            calc_response = client.post(
                f"{settings.API_V1_PREFIX}/projects/{project_id}/health/calculate",
                headers=headers
            )
            
            assert calc_response.status_code == 200
            calc_data = calc_response.json()
            # 已结项项目应该是H4
            assert calc_data.get("new_health") == ProjectHealthEnum.H4.value
    
    def test_health_h4_cancelled_project(self, client: TestClient, admin_token: str, db_session):
        """测试H4场景 - 已取消项目（ST99）"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        project_data = {
            "project_code": "PJ250101H02",
            "project_name": "健康度测试-已取消",
            "customer_id": 1,
            "status": "ST99",  # 项目取消
            "health": "H1",
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json=project_data,
            headers=headers
        )
        
        if response.status_code == 201:
            project_id = response.json()["id"]
            
            # 手动触发健康度计算
            calc_response = client.post(
                f"{settings.API_V1_PREFIX}/projects/{project_id}/health/calculate",
                headers=headers
            )
            
            assert calc_response.status_code == 200
            calc_data = calc_response.json()
            # 已取消项目应该是H4
            assert calc_data.get("new_health") == ProjectHealthEnum.H4.value
    
    def test_health_h3_blocked_status(self, client: TestClient, admin_token: str, db_session):
        """测试H3场景 - 阻塞状态（ST14缺料阻塞）"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        project_data = {
            "project_code": "PJ250101H03",
            "project_name": "健康度测试-缺料阻塞",
            "customer_id": 1,
            "status": "ST14",  # 缺料阻塞
            "health": "H1",
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json=project_data,
            headers=headers
        )
        
        if response.status_code == 201:
            project_id = response.json()["id"]
            
            # 手动触发健康度计算
            calc_response = client.post(
                f"{settings.API_V1_PREFIX}/projects/{project_id}/health/calculate",
                headers=headers
            )
            
            assert calc_response.status_code == 200
            calc_data = calc_response.json()
            # 阻塞状态应该是H3
            assert calc_data.get("new_health") == ProjectHealthEnum.H3.value
    
    def test_health_h3_technical_blocked(self, client: TestClient, admin_token: str, db_session):
        """测试H3场景 - 技术阻塞（ST19）"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        project_data = {
            "project_code": "PJ250101H04",
            "project_name": "健康度测试-技术阻塞",
            "customer_id": 1,
            "status": "ST19",  # 技术阻塞
            "health": "H1",
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json=project_data,
            headers=headers
        )
        
        if response.status_code == 201:
            project_id = response.json()["id"]
            
            # 手动触发健康度计算
            calc_response = client.post(
                f"{settings.API_V1_PREFIX}/projects/{project_id}/health/calculate",
                headers=headers
            )
            
            assert calc_response.status_code == 200
            calc_data = calc_response.json()
            # 技术阻塞应该是H3
            assert calc_data.get("new_health") == ProjectHealthEnum.H3.value
    
    def test_health_h2_rectification_status(self, client: TestClient, admin_token: str, db_session):
        """测试H2场景 - 整改中状态（ST22 FAT整改中）"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        project_data = {
            "project_code": "PJ250101H05",
            "project_name": "健康度测试-FAT整改中",
            "customer_id": 1,
            "status": "ST22",  # FAT整改中
            "health": "H1",
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json=project_data,
            headers=headers
        )
        
        if response.status_code == 201:
            project_id = response.json()["id"]
            
            # 手动触发健康度计算
            calc_response = client.post(
                f"{settings.API_V1_PREFIX}/projects/{project_id}/health/calculate",
                headers=headers
            )
            
            assert calc_response.status_code == 200
            calc_data = calc_response.json()
            # 整改中应该是H2
            assert calc_data.get("new_health") == ProjectHealthEnum.H2.value
    
    def test_health_h2_deadline_approaching(self, client: TestClient, admin_token: str, db_session):
        """测试H2场景 - 交期临近（7天内）"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 交期在7天内
        deadline = date.today() + timedelta(days=5)
        
        project_data = {
            "project_code": "PJ250101H06",
            "project_name": "健康度测试-交期临近",
            "customer_id": 1,
            "status": "ST01",
            "health": "H1",
            "planned_end_date": deadline.isoformat(),
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json=project_data,
            headers=headers
        )
        
        if response.status_code == 201:
            project_id = response.json()["id"]
            
            # 手动触发健康度计算
            calc_response = client.post(
                f"{settings.API_V1_PREFIX}/projects/{project_id}/health/calculate",
                headers=headers
            )
            
            assert calc_response.status_code == 200
            calc_data = calc_response.json()
            # 交期临近应该是H2
            assert calc_data.get("new_health") == ProjectHealthEnum.H2.value
    
    def test_health_h1_normal(self, client: TestClient, admin_token: str, db_session):
        """测试H1场景 - 正常项目"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 交期在30天后，状态正常
        deadline = date.today() + timedelta(days=30)
        
        project_data = {
            "project_code": "PJ250101H07",
            "project_name": "健康度测试-正常",
            "customer_id": 1,
            "status": "ST01",
            "health": "H2",  # 初始为H2
            "planned_end_date": deadline.isoformat(),
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json=project_data,
            headers=headers
        )
        
        if response.status_code == 201:
            project_id = response.json()["id"]
            
            # 手动触发健康度计算
            calc_response = client.post(
                f"{settings.API_V1_PREFIX}/projects/{project_id}/health/calculate",
                headers=headers
            )
            
            assert calc_response.status_code == 200
            calc_data = calc_response.json()
            # 正常项目应该是H1
            assert calc_data.get("new_health") == ProjectHealthEnum.H1.value
    
    def test_health_details_diagnosis(self, client: TestClient, admin_token: str, db_session):
        """测试健康度详情诊断"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        project_data = {
            "project_code": "PJ250101H08",
            "project_name": "健康度详情测试",
            "customer_id": 1,
            "status": "ST01",
            "health": "H1",
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json=project_data,
            headers=headers
        )
        
        if response.status_code == 201:
            project_id = response.json()["id"]
            
            # 获取健康度详情
            details_response = client.get(
                f"{settings.API_V1_PREFIX}/projects/{project_id}/health/details",
                headers=headers
            )
            
            assert details_response.status_code == 200
            details_data = details_response.json()
            assert "health" in details_data
            assert "diagnosis" in details_data
            assert "factors" in details_data
            assert "recommendations" in details_data
    
    def test_batch_health_calculation(self, client: TestClient, admin_token: str, db_session):
        """测试批量健康度计算"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 创建多个项目
        project_ids = []
        for i in range(3):
            project_data = {
                "project_code": f"PJ250101H09{i}",
                "project_name": f"批量计算测试-{i}",
                "customer_id": 1,
                "status": "ST01",
                "health": "H1",
            }
            
            response = client.post(
                f"{settings.API_V1_PREFIX}/projects/",
                json=project_data,
                headers=headers
            )
            
            if response.status_code == 201:
                project_ids.append(response.json()["id"])
        
        if len(project_ids) > 0:
            # 批量计算健康度
            batch_response = client.post(
                f"{settings.API_V1_PREFIX}/projects/health/batch-calculate",
                json={"project_ids": project_ids},
                headers=headers
            )
            
            assert batch_response.status_code == 200
            batch_data = batch_response.json()
            assert "total" in batch_data
            assert "updated" in batch_data
            assert "unchanged" in batch_data
            assert batch_data["total"] == len(project_ids)
    
    def test_health_calculation_priority(self, client: TestClient, admin_token: str, db_session):
        """测试健康度计算优先级（H4 > H3 > H2 > H1）"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 创建同时满足H2和H3条件的项目（应该返回H3）
        project_data = {
            "project_code": "PJ250101H10",
            "project_name": "健康度优先级测试",
            "customer_id": 1,
            "status": "ST14",  # 缺料阻塞（H3）
            "health": "H1",
            "planned_end_date": (date.today() + timedelta(days=5)).isoformat(),  # 交期临近（H2）
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json=project_data,
            headers=headers
        )
        
        if response.status_code == 201:
            project_id = response.json()["id"]
            
            # 手动触发健康度计算
            calc_response = client.post(
                f"{settings.API_V1_PREFIX}/projects/{project_id}/health/calculate",
                headers=headers
            )
            
            assert calc_response.status_code == 200
            calc_data = calc_response.json()
            # H3优先级高于H2，应该返回H3
            assert calc_data.get("new_health") == ProjectHealthEnum.H3.value
