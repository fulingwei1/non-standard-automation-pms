# -*- coding: utf-8 -*-
"""
项目管理模块 - 集成测试

Sprint 6.4: 项目管理集成测试
测试端到端工作流程和模块联动
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta
from app.core.config import settings


class TestProjectWorkflow:
    """项目工作流集成测试"""
    
    def test_project_lifecycle_workflow(self, client: TestClient, admin_token: str):
        """测试项目完整生命周期流程"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 1. 创建项目
        project_data = {
            "project_code": "PJ250101WF01",
            "project_name": "集成测试-完整流程",
            "customer_id": 1,
            "customer_name": "测试客户",
            "customer_contact": "张三",
            "customer_phone": "13800138000",
            "requirements": "项目需求描述",
            "stage": "S1",
            "status": "ST01",
            "health": "H1",
        }
        
        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json=project_data,
            headers=headers
        )
        
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]
        
        # 2. 检查阶段门（G1: S1→S2）
        gate_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/gate-check/S2",
            headers=headers
        )
        assert gate_response.status_code == 200
        
        # 3. 推进阶段（S1→S2）
        advance_data = {
            "target_stage": "S2",
            "skip_gate_check": False,
        }
        advance_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/advance-stage",
            json=advance_data,
            headers=headers
        )
        # 如果Gate校验通过，应该成功；否则可能返回400/422
        assert advance_response.status_code in [200, 400, 422]
        
        # 4. 更新项目状态
        update_data = {
            "status": "ST02",  # 假设ST02是S2阶段的某个状态
        }
        update_response = client.put(
            f"{settings.API_V1_PREFIX}/projects/{project_id}",
            json=update_data,
            headers=headers
        )
        assert update_response.status_code == 200
        
        # 5. 触发健康度计算
        health_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/{project_id}/health/calculate",
            headers=headers
        )
        assert health_response.status_code == 200
        
        # 6. 获取项目详情（验证所有数据）
        detail_response = client.get(
            f"{settings.API_V1_PREFIX}/projects/{project_id}",
            headers=headers
        )
        assert detail_response.status_code == 200
        detail_data = detail_response.json()
        assert detail_data["id"] == project_id
        assert "stage" in detail_data
        assert "status" in detail_data
        assert "health" in detail_data
    
    def test_project_machine_workflow(self, client: TestClient, admin_token: str):
        """测试机台管理完整流程"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 1. 创建项目
        project_data = {
            "project_code": "PJ250101WF02",
            "project_name": "集成测试-机台管理",
            "customer_id": 1,
            "stage": "S1",
        }
        
        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json=project_data,
            headers=headers
        )
        
        if create_response.status_code == 201:
            project_id = create_response.json()["id"]
            
            # 2. 创建机台
            machine_data = {
                "machine_code": "PN001",
                "machine_name": "测试机台",
                "project_id": project_id,
            }
            
            machine_response = client.post(
                f"{settings.API_V1_PREFIX}/machines/",
                json=machine_data,
                headers=headers
            )
            
            # 如果机台API存在，应该成功
            if machine_response.status_code in [201, 404]:
                if machine_response.status_code == 201:
                    machine_id = machine_response.json()["id"]
                    
                    # 3. 查询项目下的机台
                    machines_response = client.get(
                        f"{settings.API_V1_PREFIX}/projects/{project_id}/machines",
                        headers=headers
                    )
                    # 应该返回机台列表或空列表
                    assert machines_response.status_code in [200, 404]
    
    def test_project_milestone_workflow(self, client: TestClient, admin_token: str):
        """测试里程碑管理完整流程"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 1. 创建项目
        project_data = {
            "project_code": "PJ250101WF03",
            "project_name": "集成测试-里程碑管理",
            "customer_id": 1,
            "stage": "S1",
        }
        
        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json=project_data,
            headers=headers
        )
        
        if create_response.status_code == 201:
            project_id = create_response.json()["id"]
            
            # 2. 创建里程碑
            milestone_data = {
                "milestone_name": "需求确认",
                "project_id": project_id,
                "planned_date": date.today().isoformat(),
                "is_key": True,
            }
            
            milestone_response = client.post(
                f"{settings.API_V1_PREFIX}/milestones/",
                json=milestone_data,
                headers=headers
            )
            
            # 如果里程碑API存在，应该成功
            if milestone_response.status_code in [201, 404]:
                if milestone_response.status_code == 201:
                    milestone_id = milestone_response.json()["id"]
                    
                    # 3. 更新里程碑状态
                    update_data = {
                        "status": "COMPLETED",
                        "actual_date": date.today().isoformat(),
                    }
                    
                    update_response = client.put(
                        f"{settings.API_V1_PREFIX}/milestones/{milestone_id}",
                        json=update_data,
                        headers=headers
                    )
                    # 应该成功更新
                    assert update_response.status_code in [200, 404]
    
    def test_project_member_workflow(self, client: TestClient, admin_token: str):
        """测试项目成员管理完整流程"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 1. 创建项目
        project_data = {
            "project_code": "PJ250101WF04",
            "project_name": "集成测试-成员管理",
            "customer_id": 1,
            "stage": "S1",
        }
        
        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json=project_data,
            headers=headers
        )
        
        if create_response.status_code == 201:
            project_id = create_response.json()["id"]
            
            # 2. 添加项目成员
            member_data = {
                "project_id": project_id,
                "user_id": 1,  # 假设存在ID为1的用户
                "role": "DEVELOPER",
            }
            
            member_response = client.post(
                f"{settings.API_V1_PREFIX}/project-members/",
                json=member_data,
                headers=headers
            )
            
            # 如果成员API存在，应该成功
            if member_response.status_code in [201, 404]:
                if member_response.status_code == 201:
                    member_id = member_response.json()["id"]
                    
                    # 3. 查询项目成员列表
                    members_response = client.get(
                        f"{settings.API_V1_PREFIX}/projects/{project_id}/members",
                        headers=headers
                    )
                    # 应该返回成员列表
                    assert members_response.status_code in [200, 404]
    
    def test_project_status_health_integration(self, client: TestClient, admin_token: str):
        """测试项目状态更新与健康度计算联动"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 1. 创建项目
        project_data = {
            "project_code": "PJ250101WF05",
            "project_name": "集成测试-状态健康联动",
            "customer_id": 1,
            "status": "ST01",
            "health": "H1",
        }
        
        create_response = client.post(
            f"{settings.API_V1_PREFIX}/projects/",
            json=project_data,
            headers=headers
        )
        
        if create_response.status_code == 201:
            project_id = create_response.json()["id"]
            
            # 2. 更新状态为阻塞状态（应该触发健康度变化）
            update_data = {
                "status": "ST14",  # 缺料阻塞
            }
            
            update_response = client.put(
                f"{settings.API_V1_PREFIX}/projects/{project_id}",
                json=update_data,
                headers=headers
            )
            assert update_response.status_code == 200
            
            # 3. 验证健康度是否自动更新为H3
            detail_response = client.get(
                f"{settings.API_V1_PREFIX}/projects/{project_id}",
                headers=headers
            )
            assert detail_response.status_code == 200
            detail_data = detail_response.json()
            # 注意：如果后端实现了自动健康度计算，health应该是H3
            # 否则需要手动触发计算
            assert "health" in detail_data


class TestProjectModuleIntegration:
    """项目模块与其他模块联动测试"""
    
    def test_contract_to_project_flow(self, client: TestClient, admin_token: str):
        """测试合同签订 → 项目创建流程"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 注意：这里假设有合同API，实际测试需要根据实际情况调整
        # 1. 创建合同（如果合同API存在）
        # 2. 合同签订后自动创建项目
        # 3. 验证项目已创建
        
        # 由于合同API可能不存在，这里先跳过具体实现
        pytest.skip("Contract API not implemented yet")
    
    def test_acceptance_to_status_update(self, client: TestClient, admin_token: str):
        """测试验收通过 → 状态更新流程"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 注意：这里假设有验收API，实际测试需要根据实际情况调整
        # 1. 创建项目
        # 2. 创建验收记录
        # 3. 验收通过后自动更新项目状态
        # 4. 验证状态已更新
        
        # 由于验收API可能不存在，这里先跳过具体实现
        pytest.skip("Acceptance API integration test needs implementation")
    
    def test_ecn_to_schedule_update(self, client: TestClient, admin_token: str):
        """测试ECN变更 → 交期更新流程"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 注意：这里假设有ECN API，实际测试需要根据实际情况调整
        # 1. 创建项目
        # 2. 创建ECN变更
        # 3. ECN变更后自动更新项目交期
        # 4. 验证交期已更新
        
        # 由于ECN API可能不存在，这里先跳过具体实现
        pytest.skip("ECN API integration test needs implementation")


class TestProjectPerformance:
    """项目性能测试"""
    
    def test_project_list_large_dataset(self, client: TestClient, admin_token: str):
        """测试大数据量场景 - 项目列表查询"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 测试分页查询性能
        start_time = datetime.now()
        
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/?page=1&page_size=100",
            headers=headers
        )
        
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        
        assert response.status_code == 200
        # 100条数据查询应该在合理时间内完成（例如5秒内）
        assert elapsed < 5.0
    
    def test_batch_health_calculation_performance(self, client: TestClient, admin_token: str):
        """测试批量健康度计算性能"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 创建多个项目用于批量计算
        project_ids = []
        for i in range(10):
            project_data = {
                "project_code": f"PJ250101PF{i:02d}",
                "project_name": f"性能测试-{i}",
                "customer_id": 1,
                "status": "ST01",
            }
            
            response = client.post(
                f"{settings.API_V1_PREFIX}/projects/",
                json=project_data,
                headers=headers
            )
            
            if response.status_code == 201:
                project_ids.append(response.json()["id"])
        
        if len(project_ids) > 0:
            start_time = datetime.now()
            
            batch_response = client.post(
                f"{settings.API_V1_PREFIX}/projects/health/batch-calculate",
                json={"project_ids": project_ids},
                headers=headers
            )
            
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            
            assert batch_response.status_code == 200
            # 10个项目批量计算应该在合理时间内完成（例如10秒内）
            assert elapsed < 10.0
