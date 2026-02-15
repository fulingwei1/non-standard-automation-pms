# -*- coding: utf-8 -*-
"""
异常处理增强 API 测试
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.models.production import (
    ProductionException,
    ExceptionHandlingFlow,
    ExceptionKnowledge,
    ExceptionPDCA,
    FlowStatus,
    EscalationLevel,
    PDCAStage,
)
from app.models.user import User


class TestExceptionEscalation:
    """异常升级测试"""
    
    def test_escalate_exception_success(self, client: TestClient, db_session, auth_headers):
        """测试异常升级成功"""
        # 创建测试异常
        exception = ProductionException(
            exception_no="EXC-TEST-001",
            exception_type="EQUIPMENT",
            exception_level="MAJOR",
            title="设备故障",
            description="设备突然停机",
            reporter_id=1,
            status="REPORTED",
        )
        db_session.add(exception)
        db_session.commit()
        
        # 升级异常
        response = client.post(
            "/api/v1/production/exception/escalate",
            json={
                "exception_id": exception.id,
                "reason": "超过2小时未处理",
                "escalation_level": "LEVEL_1",
                "escalated_to_id": 2,
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["exception_id"] == exception.id
        assert data["escalation_level"] == "LEVEL_1"
        assert data["escalation_reason"] == "超过2小时未处理"
    
    def test_escalate_exception_not_found(self, client: TestClient, auth_headers):
        """测试升级不存在的异常"""
        response = client.post(
            "/api/v1/production/exception/escalate",
            json={
                "exception_id": 99999,
                "reason": "测试",
                "escalation_level": "LEVEL_1",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 404
    
    def test_escalate_multiple_levels(self, client: TestClient, db_session, auth_headers):
        """测试多级升级"""
        exception = ProductionException(
            exception_no="EXC-TEST-002",
            exception_type="QUALITY",
            exception_level="CRITICAL",
            title="严重质量问题",
            reporter_id=1,
            status="REPORTED",
        )
        db_session.add(exception)
        db_session.commit()
        
        # 一级升级
        response = client.post(
            "/api/v1/production/exception/escalate",
            json={
                "exception_id": exception.id,
                "reason": "严重异常",
                "escalation_level": "LEVEL_1",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        
        # 二级升级
        response = client.post(
            "/api/v1/production/exception/escalate",
            json={
                "exception_id": exception.id,
                "reason": "需要更高级别处理",
                "escalation_level": "LEVEL_2",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["escalation_level"] == "LEVEL_2"


class TestFlowTracking:
    """流程跟踪测试"""
    
    def test_get_flow_tracking(self, client: TestClient, db_session, auth_headers):
        """测试获取流程跟踪"""
        # 创建异常和流程
        exception = ProductionException(
            exception_no="EXC-TEST-003",
            exception_type="MATERIAL",
            exception_level="MINOR",
            title="物料短缺",
            reporter_id=1,
            status="PROCESSING",
        )
        db_session.add(exception)
        db_session.commit()
        
        flow = ExceptionHandlingFlow(
            exception_id=exception.id,
            status=FlowStatus.PROCESSING,
            escalation_level=EscalationLevel.NONE,
            pending_at=datetime.now() - timedelta(hours=1),
            processing_at=datetime.now(),
        )
        db_session.add(flow)
        db_session.commit()
        
        # 查询流程
        response = client.get(
            f"/api/v1/production/exception/{exception.id}/flow",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["exception_id"] == exception.id
        assert data["status"] == "PROCESSING"
        assert data["pending_duration_minutes"] is not None
    
    def test_get_flow_not_found(self, client: TestClient, auth_headers):
        """测试查询不存在的流程"""
        response = client.get(
            "/api/v1/production/exception/99999/flow",
            headers=auth_headers,
        )
        
        assert response.status_code == 404


class TestKnowledge:
    """知识库测试"""
    
    def test_create_knowledge(self, client: TestClient, auth_headers):
        """测试创建知识库条目"""
        response = client.post(
            "/api/v1/production/exception/knowledge",
            json={
                "title": "设备故障处理指南",
                "exception_type": "EQUIPMENT",
                "exception_level": "MAJOR",
                "symptom_description": "设备异响、温度过高",
                "solution": "1. 停机检查 2. 更换零件 3. 重新启动",
                "keywords": "设备,故障,异响,温度",
                "prevention_measures": "定期保养，监控温度",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "设备故障处理指南"
        assert data["exception_type"] == "EQUIPMENT"
        assert data["reference_count"] == 0
    
    def test_search_knowledge_by_keyword(self, client: TestClient, db_session, auth_headers):
        """测试按关键词搜索知识库"""
        # 创建测试知识
        knowledge = ExceptionKnowledge(
            title="质量问题处理",
            exception_type="QUALITY",
            exception_level="MAJOR",
            symptom_description="产品尺寸超差",
            solution="调整工艺参数",
            keywords="质量,尺寸,超差",
            creator_id=1,
        )
        db_session.add(knowledge)
        db_session.commit()
        
        # 搜索
        response = client.get(
            "/api/v1/production/exception/knowledge/search?keyword=质量",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(k["title"] == "质量问题处理" for k in data["items"])
    
    def test_search_knowledge_by_type(self, client: TestClient, db_session, auth_headers):
        """测试按类型搜索知识库"""
        response = client.get(
            "/api/v1/production/exception/knowledge/search?exception_type=EQUIPMENT",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        # 验证返回的都是EQUIPMENT类型
        for item in data["items"]:
            assert item["exception_type"] == "EQUIPMENT"
    
    def test_search_knowledge_pagination(self, client: TestClient, db_session, auth_headers):
        """测试知识库分页"""
        # 创建多条测试数据
        for i in range(25):
            knowledge = ExceptionKnowledge(
                title=f"测试知识{i}",
                exception_type="OTHER",
                exception_level="MINOR",
                symptom_description=f"测试描述{i}",
                solution=f"测试解决方案{i}",
                creator_id=1,
            )
            db_session.add(knowledge)
        db_session.commit()
        
        # 第1页
        response = client.get(
            "/api/v1/production/exception/knowledge/search?page=1&page_size=20",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 20
        assert data["page"] == 1
        
        # 第2页
        response = client.get(
            "/api/v1/production/exception/knowledge/search?page=2&page_size=20",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 5


class TestStatistics:
    """统计分析测试"""
    
    def test_get_statistics(self, client: TestClient, db_session, auth_headers):
        """测试获取统计数据"""
        # 创建测试异常
        for i in range(10):
            exception = ProductionException(
                exception_no=f"EXC-STAT-{i:03d}",
                exception_type="EQUIPMENT" if i % 2 == 0 else "QUALITY",
                exception_level="MAJOR" if i % 3 == 0 else "MINOR",
                title=f"测试异常{i}",
                reporter_id=1,
                status="REPORTED",
                report_time=datetime.now() - timedelta(days=i),
            )
            db_session.add(exception)
        db_session.commit()
        
        # 查询统计
        response = client.get(
            "/api/v1/production/exception/statistics",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 10
        assert "by_type" in data
        assert "by_level" in data
        assert "by_status" in data
        assert "top_exceptions" in data
    
    def test_get_statistics_with_date_range(self, client: TestClient, db_session, auth_headers):
        """测试按日期范围统计"""
        start_date = (datetime.now() - timedelta(days=7)).isoformat()
        end_date = datetime.now().isoformat()
        
        response = client.get(
            f"/api/v1/production/exception/statistics?start_date={start_date}&end_date={end_date}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_count" in data


class TestPDCA:
    """PDCA管理测试"""
    
    def test_create_pdca(self, client: TestClient, db_session, auth_headers):
        """测试创建PDCA记录"""
        # 创建测试异常
        exception = ProductionException(
            exception_no="EXC-PDCA-001",
            exception_type="QUALITY",
            exception_level="MAJOR",
            title="质量问题",
            reporter_id=1,
            status="RESOLVED",
        )
        db_session.add(exception)
        db_session.commit()
        
        # 创建PDCA
        response = client.post(
            "/api/v1/production/exception/pdca",
            json={
                "exception_id": exception.id,
                "plan_description": "产品尺寸超差",
                "plan_root_cause": "设备精度不足",
                "plan_target": "提高产品合格率至99%",
                "plan_owner_id": 1,
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["exception_id"] == exception.id
        assert data["current_stage"] == "PLAN"
        assert data["plan_description"] == "产品尺寸超差"
    
    def test_advance_pdca_to_do(self, client: TestClient, db_session, auth_headers):
        """测试推进PDCA到Do阶段"""
        # 创建异常和PDCA
        exception = ProductionException(
            exception_no="EXC-PDCA-002",
            exception_type="EQUIPMENT",
            exception_level="MAJOR",
            title="设备故障",
            reporter_id=1,
            status="RESOLVED",
        )
        db_session.add(exception)
        db_session.commit()
        
        pdca = ExceptionPDCA(
            exception_id=exception.id,
            pdca_no=f"PDCA-TEST-{exception.id}",
            current_stage=PDCAStage.PLAN,
            plan_description="设备老化",
            plan_root_cause="缺乏维护",
            plan_target="恢复设备正常运行",
            plan_owner_id=1,
        )
        db_session.add(pdca)
        db_session.commit()
        
        # 推进到Do
        response = client.put(
            f"/api/v1/production/exception/pdca/{pdca.id}/advance",
            json={
                "stage": "DO",
                "do_action_taken": "更换老化部件",
                "do_resources_used": "新部件，技术人员",
                "do_owner_id": 1,
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_stage"] == "DO"
        assert data["do_action_taken"] == "更换老化部件"
    
    def test_pdca_stage_validation(self, client: TestClient, db_session, auth_headers):
        """测试PDCA阶段状态机验证"""
        # 创建处于PLAN阶段的PDCA
        exception = ProductionException(
            exception_no="EXC-PDCA-003",
            exception_type="OTHER",
            exception_level="MINOR",
            title="其他问题",
            reporter_id=1,
            status="RESOLVED",
        )
        db_session.add(exception)
        db_session.commit()
        
        pdca = ExceptionPDCA(
            exception_id=exception.id,
            pdca_no=f"PDCA-TEST-{exception.id}",
            current_stage=PDCAStage.PLAN,
            plan_description="测试",
            plan_root_cause="测试",
            plan_target="测试",
            plan_owner_id=1,
        )
        db_session.add(pdca)
        db_session.commit()
        
        # 尝试直接跳到CHECK（应该失败）
        response = client.put(
            f"/api/v1/production/exception/pdca/{pdca.id}/advance",
            json={
                "stage": "CHECK",
                "check_result": "测试",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 400
    
    def test_pdca_full_cycle(self, client: TestClient, db_session, auth_headers):
        """测试PDCA完整周期"""
        # 创建异常
        exception = ProductionException(
            exception_no="EXC-PDCA-004",
            exception_type="QUALITY",
            exception_level="MAJOR",
            title="完整测试",
            reporter_id=1,
            status="RESOLVED",
        )
        db_session.add(exception)
        db_session.commit()
        
        # 创建PDCA
        response = client.post(
            "/api/v1/production/exception/pdca",
            json={
                "exception_id": exception.id,
                "plan_description": "问题",
                "plan_root_cause": "根因",
                "plan_target": "目标",
                "plan_owner_id": 1,
            },
            headers=auth_headers,
        )
        pdca_id = response.json()["id"]
        
        # Do
        response = client.put(
            f"/api/v1/production/exception/pdca/{pdca_id}/advance",
            json={"stage": "DO", "do_action_taken": "执行", "do_owner_id": 1},
            headers=auth_headers,
        )
        assert response.status_code == 200
        
        # Check
        response = client.put(
            f"/api/v1/production/exception/pdca/{pdca_id}/advance",
            json={"stage": "CHECK", "check_result": "检查", "check_effectiveness": "EFFECTIVE", "check_owner_id": 1},
            headers=auth_headers,
        )
        assert response.status_code == 200
        
        # Act
        response = client.put(
            f"/api/v1/production/exception/pdca/{pdca_id}/advance",
            json={"stage": "ACT", "act_standardization": "标准化", "act_owner_id": 1},
            headers=auth_headers,
        )
        assert response.status_code == 200
        
        # Complete
        response = client.put(
            f"/api/v1/production/exception/pdca/{pdca_id}/advance",
            json={"stage": "COMPLETED", "summary": "总结", "lessons_learned": "经验"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_completed"] is True


class TestRecurrenceAnalysis:
    """重复异常分析测试"""
    
    def test_analyze_recurrence(self, client: TestClient, db_session, auth_headers):
        """测试重复异常分析"""
        # 创建重复异常
        for i in range(5):
            exception = ProductionException(
                exception_no=f"EXC-REC-{i:03d}",
                exception_type="EQUIPMENT",
                exception_level="MAJOR",
                title="设备故障" if i < 3 else "其他问题",
                reporter_id=1,
                status="RESOLVED",
                report_time=datetime.now() - timedelta(days=i),
            )
            db_session.add(exception)
        db_session.commit()
        
        # 分析
        response = client.get(
            "/api/v1/production/exception/recurrence?days=30",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "exception_type" in data[0]
        assert "total_occurrences" in data[0]
        assert "similar_exceptions" in data[0]
        assert "time_trend" in data[0]
    
    def test_analyze_recurrence_by_type(self, client: TestClient, auth_headers):
        """测试按类型分析重复异常"""
        response = client.get(
            "/api/v1/production/exception/recurrence?exception_type=EQUIPMENT&days=7",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        # 验证只返回EQUIPMENT类型
        for item in data:
            assert item["exception_type"] == "EQUIPMENT"
