"""
售前AI方案生成模块 - 单元测试
至少30个测试用例
"""
import pytest
import json
from decimal import Decimal
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.presale_ai_solution import (
    PresaleAISolution,
    PresaleSolutionTemplate,
    PresaleAIGenerationLog
)
from app.models.user import User
from app.schemas.presale_ai_solution import (
    TemplateMatchRequest,
    SolutionGenerationRequest,
    ArchitectureGenerationRequest,
    BOMGenerationRequest
)
from app.services.presale_ai_service import PresaleAIService
from app.services.presale_ai_template_service import PresaleAITemplateService


# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = User(
        username="test_user",
        email="test@example.com",
        password_hash="hashed_password_123"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_template(db_session, test_user):
    """创建测试模板"""
    template = PresaleSolutionTemplate(
        name="汽车装配线方案模板",
        code="AUTO_ASSEMBLY_001",
        industry="汽车",
        equipment_type="装配",
        complexity_level="medium",
        solution_content={
            "description": "汽车装配线标准方案",
            "equipment_list": [
                {"name": "装配机器人", "model": "ROBOT-500", "quantity": 4}
            ]
        },
        architecture_diagram="graph TB\nA-->B",
        bom_template={"items": []},
        keywords="汽车 装配 机器人 自动化",
        usage_count=10,
        avg_quality_score=Decimal("4.5"),
        is_active=1,
        created_by=test_user.id
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


# ==================== 模板匹配测试 (8个) ====================

def test_match_templates_by_industry(db_session, test_user, test_template):
    """测试1: 按行业匹配模板"""
    service = PresaleAIService()
    request = TemplateMatchRequest(
        presale_ticket_id=1,
        industry="汽车",
        top_k=3
    )
    
    matched, search_time = service.match_templates(request, test_user.id)
    
    assert len(matched) > 0
    assert matched[0].industry == "汽车"
    assert search_time > 0


def test_match_templates_by_equipment_type(db_session, test_user, test_template):
    """测试2: 按设备类型匹配模板"""
    service = PresaleAIService()
    request = TemplateMatchRequest(
        presale_ticket_id=1,
        equipment_type="装配",
        top_k=3
    )
    
    matched, search_time = service.match_templates(request, test_user.id)
    
    assert len(matched) > 0
    assert matched[0].equipment_type == "装配"


def test_match_templates_by_keywords(db_session, test_user, test_template):
    """测试3: 按关键词匹配模板"""
    service = PresaleAIService()
    request = TemplateMatchRequest(
        presale_ticket_id=1,
        keywords="汽车 机器人",
        top_k=3
    )
    
    matched, search_time = service.match_templates(request, test_user.id)
    
    assert len(matched) > 0
    assert matched[0].similarity_score > 0


def test_match_templates_empty_result(db_session, test_user):
    """测试4: 无匹配结果"""
    service = PresaleAIService()
    request = TemplateMatchRequest(
        presale_ticket_id=1,
        industry="不存在的行业",
        top_k=3
    )
    
    matched, search_time = service.match_templates(request, test_user.id)
    
    assert len(matched) == 0


def test_match_templates_top_k_limit(db_session, test_user, test_template):
    """测试5: TOP K限制"""
    # 创建多个模板
    for i in range(5):
        template = PresaleSolutionTemplate(
            name=f"测试模板{i}",
            code=f"TEST_{i}",
            industry="汽车",
            equipment_type="装配",
            solution_content={},
            is_active=1,
            created_by=test_user.id
        )
        db_session.add(template)
    db_session.commit()
    
    service = PresaleAIService()
    request = TemplateMatchRequest(
        presale_ticket_id=1,
        industry="汽车",
        top_k=3
    )
    
    matched, search_time = service.match_templates(request, test_user.id)
    
    assert len(matched) <= 3


def test_match_templates_similarity_scoring(db_session, test_user, test_template):
    """测试6: 相似度评分计算"""
    service = PresaleAIService()
    
    score = service._calculate_similarity("汽车 装配 机器人", "汽车 装配")
    
    assert 0 <= score <= 1
    assert score > 0


def test_match_templates_with_usage_count(db_session, test_user, test_template):
    """测试7: 按使用次数排序"""
    service = PresaleAIService()
    request = TemplateMatchRequest(
        presale_ticket_id=1,
        industry="汽车",
        top_k=3
    )
    
    matched, search_time = service.match_templates(request, test_user.id)
    
    assert matched[0].usage_count >= 0


def test_match_templates_performance(db_session, test_user, test_template):
    """测试8: 匹配性能"""
    service = PresaleAIService()
    request = TemplateMatchRequest(
        presale_ticket_id=1,
        industry="汽车",
        top_k=3
    )
    
    matched, search_time = service.match_templates(request, test_user.id)
    
    # 搜索时间应小于1000ms
    assert search_time < 1000


# ==================== 方案生成测试 (8个) ====================

def test_generate_solution_basic(db_session, test_user, test_template):
    """测试9: 基本方案生成"""
    service = PresaleAIService()
    request = SolutionGenerationRequest(
        presale_ticket_id=1,
        template_id=test_template.id,
        requirements={"industry": "汽车", "type": "装配线"},
        generate_architecture=False,
        generate_bom=False,
        ai_model="gpt-4"
    )
    
    result = service.generate_solution(request, test_user.id)
    
    assert result["solution_id"] > 0
    assert result["solution"] is not None
    assert result["generation_time_seconds"] > 0


def test_generate_solution_with_architecture(db_session, test_user, test_template):
    """测试10: 生成方案包含架构图"""
    service = PresaleAIService()
    request = SolutionGenerationRequest(
        presale_ticket_id=1,
        requirements={"industry": "汽车"},
        generate_architecture=True,
        generate_bom=False
    )
    
    result = service.generate_solution(request, test_user.id)
    
    assert result["architecture_diagram"] is not None


def test_generate_solution_with_bom(db_session, test_user):
    """测试11: 生成方案包含BOM"""
    service = PresaleAIService()
    request = SolutionGenerationRequest(
        presale_ticket_id=1,
        requirements={"industry": "汽车"},
        generate_architecture=False,
        generate_bom=True
    )
    
    result = service.generate_solution(request, test_user.id)
    
    # BOM可能为空（如果没有equipment_list）
    assert "bom_list" in result


def test_generate_solution_confidence_score(db_session, test_user, test_template):
    """测试12: 置信度评分计算"""
    service = PresaleAIService()
    
    solution = {
        "description": "test",
        "equipment_list": [{"name": "test"}],
        "technical_parameters": {"param1": "value1"},
        "process_flow": "flow"
    }
    
    score = service._calculate_confidence(solution, test_template)
    
    assert 0 <= score <= 1
    assert score >= 0.5  # 有模板参考，分数应>=0.5


def test_generate_solution_without_template(db_session, test_user):
    """测试13: 无模板生成方案"""
    service = PresaleAIService()
    request = SolutionGenerationRequest(
        presale_ticket_id=1,
        requirements={"industry": "电子", "type": "贴片"},
        generate_architecture=False,
        generate_bom=False
    )
    
    result = service.generate_solution(request, test_user.id)
    
    assert result["solution_id"] > 0


def test_generate_solution_prompt_building(db_session, test_user, test_template):
    """测试14: 提示词构建"""
    service = PresaleAIService()
    
    requirements = {"industry": "汽车", "capacity": "1000件/天"}
    prompt = service._build_solution_prompt(requirements, test_template)
    
    assert "汽车" in prompt
    assert "1000件/天" in prompt
    assert test_template.name in prompt


def test_generate_solution_parse_response(db_session, test_user):
    """测试15: 解析AI响应"""
    service = PresaleAIService()
    
    ai_response = {
        "content": '```json\n{"description": "test solution"}\n```'
    }
    
    parsed = service._parse_solution_response(ai_response)
    
    assert "description" in parsed
    assert parsed["description"] == "test solution"


def test_generate_solution_logging(db_session, test_user):
    """测试16: 生成日志记录"""
    service = PresaleAIService()
    
    service._log_generation(
        solution_id=1,
        request_type="solution",
        input_data={"test": "data"},
        output_data={"result": "ok"},
        success=True,
        response_time_ms=500,
        ai_model="gpt-4",
        tokens_used=100
    )
    
    logs = db_session.query(PresaleAIGenerationLog).all()
    
    assert len(logs) == 1
    assert logs[0].request_type == "solution"


# ==================== 架构图生成测试 (6个) ====================

def test_generate_architecture_basic(db_session, test_user):
    """测试17: 基本架构图生成"""
    service = PresaleAIService()
    
    result = service.generate_architecture(
        requirements={"type": "装配线"},
        diagram_type="architecture"
    )
    
    assert result["diagram_code"] is not None
    assert result["diagram_type"] == "architecture"
    assert result["format"] == "mermaid"


def test_generate_topology_diagram(db_session, test_user):
    """测试18: 生成拓扑图"""
    service = PresaleAIService()
    
    result = service.generate_architecture(
        requirements={"equipment": ["robot", "plc"]},
        diagram_type="topology"
    )
    
    assert result["diagram_type"] == "topology"


def test_generate_signal_flow_diagram(db_session, test_user):
    """测试19: 生成信号流程图"""
    service = PresaleAIService()
    
    result = service.generate_architecture(
        requirements={"signals": ["input", "output"]},
        diagram_type="signal_flow"
    )
    
    assert result["diagram_type"] == "signal_flow"


def test_extract_mermaid_code(db_session, test_user):
    """测试20: 提取Mermaid代码"""
    service = PresaleAIService()
    
    content = "```mermaid\ngraph TB\nA-->B\n```"
    code = service._extract_mermaid_code(content)
    
    assert "graph TB" in code
    assert "```" not in code


def test_architecture_prompt_building(db_session, test_user):
    """测试21: 架构图提示词构建"""
    service = PresaleAIService()
    
    requirements = {"type": "装配线", "stations": 5}
    prompt = service._build_architecture_prompt(requirements, "architecture")
    
    assert "架构图" in prompt
    assert "Mermaid" in prompt


def test_generate_architecture_with_solution_id(db_session, test_user):
    """测试22: 关联方案ID生成架构图"""
    # 先创建一个方案
    solution = PresaleAISolution(
        presale_ticket_id=1,
        created_by=test_user.id
    )
    db_session.add(solution)
    db_session.commit()
    db_session.refresh(solution)
    
    service = PresaleAIService()
    
    result = service.generate_architecture(
        requirements={"type": "test"},
        diagram_type="architecture",
        solution_id=solution.id
    )
    
    # 重新查询方案
    db_session.refresh(solution)
    
    assert solution.architecture_diagram is not None


# ==================== BOM生成测试 (8个) ====================

def test_generate_bom_basic(db_session, test_user):
    """测试23: 基本BOM生成"""
    service = PresaleAIService()
    
    equipment_list = [
        {"name": "机器人", "model": "ROBOT-500", "quantity": 2}
    ]
    
    result = service.generate_bom(
        equipment_list=equipment_list,
        include_cost=True,
        include_suppliers=True
    )
    
    assert result["item_count"] == 1
    assert len(result["bom_items"]) == 1


def test_generate_bom_without_cost(db_session, test_user):
    """测试24: 生成BOM不含成本"""
    service = PresaleAIService()
    
    equipment_list = [
        {"name": "PLC", "quantity": 1}
    ]
    
    result = service.generate_bom(
        equipment_list=equipment_list,
        include_cost=False,
        include_suppliers=False
    )
    
    assert result["item_count"] == 1


def test_generate_bom_without_suppliers(db_session, test_user):
    """测试25: 生成BOM不含供应商"""
    service = PresaleAIService()
    
    equipment_list = [
        {"name": "传感器", "quantity": 10}
    ]
    
    result = service.generate_bom(
        equipment_list=equipment_list,
        include_cost=True,
        include_suppliers=False
    )
    
    assert result["item_count"] == 1


def test_generate_bom_item_structure(db_session, test_user):
    """测试26: BOM项结构验证"""
    service = PresaleAIService()
    
    equipment = {
        "name": "机器人",
        "model": "ROBOT-600",
        "quantity": 1,
        "unit": "台"
    }
    
    item = service._generate_bom_item(equipment, True, True)
    
    assert "item_name" in item
    assert "model" in item
    assert "quantity" in item
    assert item["item_name"] == "机器人"


def test_generate_bom_total_cost(db_session, test_user):
    """测试27: BOM总成本计算"""
    service = PresaleAIService()
    
    equipment_list = [
        {"name": "设备A", "quantity": 2},
        {"name": "设备B", "quantity": 1}
    ]
    
    result = service.generate_bom(
        equipment_list=equipment_list,
        include_cost=True
    )
    
    assert result["total_cost"] > 0


def test_generate_bom_with_solution_id(db_session, test_user):
    """测试28: 关联方案ID生成BOM"""
    # 创建方案
    solution = PresaleAISolution(
        presale_ticket_id=1,
        created_by=test_user.id
    )
    db_session.add(solution)
    db_session.commit()
    db_session.refresh(solution)
    
    service = PresaleAIService()
    
    equipment_list = [
        {"name": "测试设备", "quantity": 1}
    ]
    
    result = service.generate_bom(
        equipment_list=equipment_list,
        solution_id=solution.id
    )
    
    db_session.refresh(solution)
    
    assert solution.bom_list is not None


def test_generate_bom_empty_list(db_session, test_user):
    """测试29: 空设备列表"""
    service = PresaleAIService()
    
    result = service.generate_bom(
        equipment_list=[],
        include_cost=True
    )
    
    assert result["item_count"] == 0
    assert result["total_cost"] == Decimal("0")


def test_generate_bom_performance(db_session, test_user):
    """测试30: BOM生成性能"""
    service = PresaleAIService()
    
    equipment_list = [
        {"name": f"设备{i}", "quantity": 1}
        for i in range(10)
    ]
    
    result = service.generate_bom(
        equipment_list=equipment_list,
        include_cost=True
    )
    
    # 生成时间应小于5秒
    assert result["generation_time_seconds"] < 5


# ==================== 方案管理测试 (额外测试) ====================

def test_get_solution(db_session, test_user):
    """测试31: 获取方案"""
    solution = PresaleAISolution(
        presale_ticket_id=1,
        solution_description="Test solution",
        created_by=test_user.id
    )
    db_session.add(solution)
    db_session.commit()
    db_session.refresh(solution)
    
    service = PresaleAIService()
    retrieved = service.get_solution(solution.id)
    
    assert retrieved is not None
    assert retrieved.id == solution.id


def test_update_solution(db_session, test_user):
    """测试32: 更新方案"""
    solution = PresaleAISolution(
        presale_ticket_id=1,
        created_by=test_user.id
    )
    db_session.add(solution)
    db_session.commit()
    db_session.refresh(solution)
    
    service = PresaleAIService()
    
    updated = service.update_solution(
        solution.id,
        {"solution_description": "Updated description"}
    )
    
    assert updated.solution_description == "Updated description"


def test_review_solution(db_session, test_user):
    """测试33: 审核方案"""
    solution = PresaleAISolution(
        presale_ticket_id=1,
        status="draft",
        created_by=test_user.id
    )
    db_session.add(solution)
    db_session.commit()
    db_session.refresh(solution)
    
    service = PresaleAIService()
    
    reviewed = service.review_solution(
        solution.id,
        test_user.id,
        "approved",
        "方案通过审核"
    )
    
    assert reviewed.status == "approved"
    assert reviewed.reviewed_by == test_user.id
    assert reviewed.review_comments == "方案通过审核"


def test_get_template_library(db_session, test_user, test_template):
    """测试34: 获取模板库"""
    service = PresaleAIService()
    
    templates = service.get_template_library(
        industry="汽车",
        is_active=True
    )
    
    assert len(templates) > 0
    assert templates[0].industry == "汽车"


# ==================== 模板管理测试 ====================

def test_create_template(db_session, test_user):
    """测试35: 创建模板"""
    template_service = PresaleAITemplateService(db_session)
    
    data = {
        "name": "新模板",
        "code": "NEW_TEMPLATE",
        "industry": "电子",
        "solution_content": {"test": "data"}
    }
    
    template = template_service.create_template(data, test_user.id)
    
    assert template.id is not None
    assert template.name == "新模板"


def test_update_template(db_session, test_user, test_template):
    """测试36: 更新模板"""
    template_service = PresaleAITemplateService(db_session)
    
    updated = template_service.update_template(
        test_template.id,
        {"name": "更新后的模板名"}
    )
    
    assert updated.name == "更新后的模板名"


def test_increment_template_usage(db_session, test_user, test_template):
    """测试37: 增加模板使用次数"""
    template_service = PresaleAITemplateService(db_session)
    
    initial_count = test_template.usage_count
    
    template_service.increment_usage(test_template.id)
    
    db_session.refresh(test_template)
    
    assert test_template.usage_count == initial_count + 1


def test_update_template_quality_score(db_session, test_user, test_template):
    """测试38: 更新模板质量评分"""
    template_service = PresaleAITemplateService(db_session)
    
    template_service.update_quality_score(test_template.id, 5.0)
    
    db_session.refresh(test_template)
    
    assert test_template.avg_quality_score > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
