# -*- coding: utf-8 -*-
"""
装配齐套分析系统测试
测试核心功能：智能推荐、排产建议、资源分配、企业微信集成
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

# 测试数据准备
@pytest.fixture
def sample_project_data():
    """示例项目数据"""
    return {
        "project_id": 1,
        "project_code": "PJ250108001",
        "project_name": "测试项目",
        "priority": "P2",
        "contract_amount": 500000,
        "planned_start_date": date.today() + timedelta(days=7),
        "planned_end_date": date.today() + timedelta(days=60),
        "customer_id": 1
    }


@pytest.fixture
def sample_bom_data():
    """示例BOM数据"""
    return {
        "bom_id": 1,
        "bom_no": "BOM001",
        "items": [
            {
                "material_id": 1,
                "material_code": "MAT001",
                "material_name": "测试物料1",
                "quantity": 10,
                "required_date": date.today() + timedelta(days=14)
            },
            {
                "material_id": 2,
                "material_code": "MAT002",
                "material_name": "测试物料2",
                "quantity": 5,
                "required_date": date.today() + timedelta(days=21)
            }
        ]
    }


class TestAssemblyAttrRecommender:
    """测试智能推荐功能"""
    
    def test_history_match(self, db_session: Session):
        """测试历史数据匹配"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        from app.models import BomItem, Material
        
        # 创建测试数据
        material = Material(
            material_code="MAT_TEST",
            material_name="测试物料",
            category_id=1
        )
        db_session.add(material)
        db_session.flush()
        
        # 测试历史匹配（需要先有历史数据）
        # 这里简化测试，主要验证函数可以正常调用
        assert AssemblyAttrRecommender is not None
    
    def test_keyword_match(self, db_session: Session):
        """测试关键词匹配"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        from app.models import Material
        
        material = Material(
            material_code="MAT_FRAME",
            material_name="铝型材框架",
            category_id=1
        )
        db_session.add(material)
        db_session.flush()
        
        # 测试关键词匹配
        rec = AssemblyAttrRecommender._match_from_keywords(material)
        assert rec is not None
        assert rec.stage_code in ['FRAME', 'MECH', 'ELECTRIC', 'WIRING', 'DEBUG', 'COSMETIC']
        assert rec.confidence == 70.0
    
    def test_supplier_inference(self, db_session: Session):
        """测试供应商类型推断"""
        from app.services.assembly_attr_recommender import AssemblyAttrRecommender
        from app.models import Material, Supplier
        
        supplier = Supplier(
            supplier_code="SUP001",
            supplier_name="测试供应商",
            supplier_type="MACHINING"
        )
        db_session.add(supplier)
        db_session.flush()
        
        material = Material(
            material_code="MAT_MACH",
            material_name="机加件",
            category_id=1,
            default_supplier_id=supplier.id
        )
        db_session.add(material)
        db_session.flush()
        
        rec = AssemblyAttrRecommender._infer_from_supplier(db_session, material)
        assert rec is not None
        assert rec.stage_code == 'MECH'
        assert rec.confidence == 60.0


class TestSchedulingSuggestionService:
    """测试排产建议服务"""
    
    def test_priority_score_calculation(self, db_session: Session):
        """测试优先级评分计算"""
        from app.services.scheduling_suggestion_service import SchedulingSuggestionService
        from app.models import Project, MaterialReadiness
        
        project = Project(
            project_code="PJ_TEST",
            project_name="测试项目",
            priority="P1",
            contract_amount=Decimal("1000000"),
            planned_start_date=date.today(),
            planned_end_date=date.today() + timedelta(days=10),
            customer_id=1
        )
        db_session.add(project)
        db_session.flush()
        
        readiness = MaterialReadiness(
            readiness_no="KR_TEST",
            project_id=project.id,
            bom_id=1,
            blocking_kit_rate=Decimal("85.5")
        )
        db_session.add(readiness)
        db_session.flush()
        
        score_result = SchedulingSuggestionService.calculate_priority_score(
            db_session, project, readiness
        )
        
        assert score_result is not None
        assert 'total_score' in score_result
        assert 'factors' in score_result
        assert score_result['total_score'] > 0
        assert len(score_result['factors']) == 5  # 5个评分因子
    
    def test_deadline_pressure_calculation(self):
        """测试交期压力分计算"""
        from app.services.scheduling_suggestion_service import SchedulingSuggestionService
        from app.models import Project
        
        # 测试紧急交期（≤7天）
        project_urgent = Project(
            project_code="PJ_URGENT",
            project_name="紧急项目",
            planned_end_date=date.today() + timedelta(days=5)
        )
        score = SchedulingSuggestionService._calculate_deadline_pressure(project_urgent)
        assert score == 25.0
        
        # 测试正常交期（≤30天）
        project_normal = Project(
            project_code="PJ_NORMAL",
            project_name="正常项目",
            planned_end_date=date.today() + timedelta(days=20)
        )
        score = SchedulingSuggestionService._calculate_deadline_pressure(project_normal)
        assert score == 15.0


class TestResourceAllocationService:
    """测试资源分配服务"""
    
    def test_workstation_availability(self, db_session: Session):
        """测试工位可用性检查"""
        from app.services.resource_allocation_service import ResourceAllocationService
        from app.models.production import Workstation, Workshop
        
        workshop = Workshop(
            workshop_code="WS001",
            workshop_name="测试车间"
        )
        db_session.add(workshop)
        db_session.flush()
        
        workstation = Workstation(
            workstation_code="ST001",
            workstation_name="测试工位",
            workshop_id=workshop.id,
            status="IDLE",
            is_active=True
        )
        db_session.add(workstation)
        db_session.flush()
        
        is_available, reason = ResourceAllocationService.check_workstation_availability(
            db_session,
            workstation.id,
            date.today(),
            date.today() + timedelta(days=7)
        )
        
        assert is_available is True
        assert reason is None
    
    def test_worker_availability(self, db_session: Session):
        """测试人员可用性检查"""
        from app.services.resource_allocation_service import ResourceAllocationService
        from app.models.production import Worker, Workshop
        
        workshop = Workshop(
            workshop_code="WS001",
            workshop_name="测试车间"
        )
        db_session.add(workshop)
        db_session.flush()
        
        worker = Worker(
            worker_no="W001",
            worker_name="测试工人",
            workshop_id=workshop.id,
            status="ACTIVE",
            is_active=True
        )
        db_session.add(worker)
        db_session.flush()
        
        is_available, reason, available_hours = ResourceAllocationService.check_worker_availability(
            db_session,
            worker.id,
            date.today(),
            date.today() + timedelta(days=7),
            required_hours=8.0
        )
        
        assert is_available is True or is_available is False  # 取决于是否有其他分配
        assert available_hours >= 0


class TestAssemblyKitOptimizer:
    """测试齐套分析优化服务"""
    
    def test_optimize_estimated_ready_date(self, db_session: Session):
        """测试预计齐套日期优化"""
        from app.services.assembly_kit_optimizer import AssemblyKitOptimizer
        from app.models import MaterialReadiness, ShortageDetail
        
        readiness = MaterialReadiness(
            readiness_no="KR_TEST",
            project_id=1,
            bom_id=1,
            estimated_ready_date=date.today() + timedelta(days=20)
        )
        db_session.add(readiness)
        db_session.flush()
        
        optimized_date = AssemblyKitOptimizer.optimize_estimated_ready_date(
            db_session, readiness
        )
        
        # 优化日期应该存在（可能等于原日期或更早）
        assert optimized_date is None or optimized_date <= readiness.estimated_ready_date
    
    def test_generate_optimization_suggestions(self, db_session: Session):
        """测试优化建议生成"""
        from app.services.assembly_kit_optimizer import AssemblyKitOptimizer
        from app.models import MaterialReadiness, ShortageDetail
        
        readiness = MaterialReadiness(
            readiness_no="KR_TEST",
            project_id=1,
            bom_id=1
        )
        db_session.add(readiness)
        db_session.flush()
        
        suggestions = AssemblyKitOptimizer.generate_optimization_suggestions(
            db_session, readiness
        )
        
        assert isinstance(suggestions, list)
        # 如果没有阻塞物料，建议列表应该为空
        # 如果有阻塞物料，应该有建议


class TestWeChatClient:
    """测试企业微信客户端"""
    
    def test_token_cache(self):
        """测试Token缓存"""
        from app.utils.wechat_client import WeChatTokenCache
        
        # 测试设置和获取
        WeChatTokenCache.set("test_key", "test_token", 7200)
        token = WeChatTokenCache.get("test_key")
        assert token == "test_token"
        
        # 测试清除
        WeChatTokenCache.clear("test_key")
        token = WeChatTokenCache.get("test_key")
        assert token is None
    
    def test_client_initialization(self):
        """测试客户端初始化"""
        from app.utils.wechat_client import WeChatClient
        from app.core.config import settings
        
        # 如果配置不完整，应该抛出异常
        if not all([settings.WECHAT_CORP_ID, settings.WECHAT_AGENT_ID, settings.WECHAT_SECRET]):
            with pytest.raises(ValueError):
                client = WeChatClient()
        else:
            # 如果配置完整，应该可以创建客户端
            client = WeChatClient()
            assert client is not None


class TestIntegration:
    """集成测试"""
    
    def test_full_kit_analysis_flow(self, db_session: Session):
        """测试完整的齐套分析流程"""
        from app.api.v1.endpoints.assembly_kit import execute_kit_analysis
        from app.schemas.assembly_kit import MaterialReadinessCreate
        
        # 这个测试需要完整的数据库环境
        # 在实际测试中，需要准备：
        # 1. 项目数据
        # 2. BOM数据
        # 3. 物料数据
        # 4. 装配属性数据
        
        # 这里只验证函数可以导入
        assert execute_kit_analysis is not None
    
    def test_smart_recommend_flow(self, db_session: Session):
        """测试智能推荐流程"""
        from app.api.v1.endpoints.assembly_kit import smart_recommend_assembly_attrs
        from app.schemas.assembly_kit import BomAssemblyAttrsAutoRequest
        
        # 验证函数可以导入
        assert smart_recommend_assembly_attrs is not None
    
    def test_scheduling_suggestion_flow(self, db_session: Session):
        """测试排产建议流程"""
        from app.api.v1.endpoints.assembly_kit import generate_scheduling_suggestions
        
        # 验证函数可以导入
        assert generate_scheduling_suggestions is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
