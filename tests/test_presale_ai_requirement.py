"""
AI需求理解模块单元测试
覆盖所有核心功能，至少25个测试用例
"""
import pytest
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.presale_ai_requirement_analysis import PresaleAIRequirementAnalysis
from app.models.user import User
from app.schemas.presale_ai_requirement import (
    RequirementAnalysisRequest,
    RequirementRefinementRequest,
    RequirementUpdateRequest,
    StructuredRequirement,
    EquipmentItem,
    ProcessStep,
    TechnicalParameter,
    ClarificationQuestion
)
from app.services.presale_ai_requirement_service import (
    AIRequirementAnalyzer,
    PresaleAIRequirementService
)


# ========== 测试数据库设置 ==========

@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    # 创建测试用户
    test_user = User(
        id=1,
        username="test_user",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    db.add(test_user)
    db.commit()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_requirement_text():
    """示例需求文本"""
    return """
    我们需要一条自动化生产线，用于手机外壳的组装和检测。
    产能要求：每小时200件
    工艺流程：上料 -> 视觉检测 -> 自动组装 -> 质量检测 -> 下料
    设备要求：工业机器人、视觉检测系统、自动组装设备、质检设备
    精度要求：±0.05mm
    环境要求：洁净车间，温度20-25℃
    """


@pytest.fixture
def mock_openai_response():
    """模拟OpenAI API响应"""
    return {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "structured_requirement": {
                        "project_type": "手机外壳组装自动化",
                        "industry": "消费电子",
                        "core_objectives": ["提升产能", "保证质量", "降低人工成本"],
                        "functional_requirements": ["自动上料", "视觉检测", "自动组装", "质量检测", "自动下料"],
                        "non_functional_requirements": ["产能≥200件/小时", "精度±0.05mm", "洁净车间"],
                        "constraints": ["温度20-25℃"],
                        "assumptions": ["手机外壳标准化"]
                    },
                    "equipment_list": [
                        {"name": "六轴工业机器人", "type": "机器人", "quantity": 2, "priority": "high"},
                        {"name": "3D视觉检测系统", "type": "检测设备", "quantity": 2, "priority": "high"},
                        {"name": "自动组装工作站", "type": "组装设备", "quantity": 1, "priority": "high"}
                    ],
                    "process_flow": [
                        {"step_number": 1, "name": "上料", "description": "自动上料系统", "equipment_required": ["上料机"]},
                        {"step_number": 2, "name": "视觉检测", "description": "外观检测", "equipment_required": ["视觉系统"]},
                        {"step_number": 3, "name": "组装", "description": "自动组装", "equipment_required": ["机器人"]}
                    ],
                    "technical_parameters": [
                        {"parameter_name": "产能", "value": "200件/小时", "unit": "件/小时", "is_critical": True},
                        {"parameter_name": "精度", "value": "±0.05mm", "unit": "mm", "tolerance": "±0.01mm", "is_critical": True}
                    ],
                    "acceptance_criteria": ["产能达标", "精度合格", "稳定运行24小时"]
                }, ensure_ascii=False)
            }
        }]
    }


# ========== 需求解析测试 (8个) ==========

class TestRequirementAnalysis:
    """需求解析测试"""
    
    @pytest.mark.asyncio
    async def test_analyze_simple_requirement(self, sample_requirement_text):
        """测试1: 分析简单需求"""
        analyzer = AIRequirementAnalyzer(api_key="test_key")
        
        with patch.object(analyzer, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = '{"structured_requirement": {"project_type": "自动化"}, "equipment_list": []}'
            
            result = await analyzer.analyze_requirement(sample_requirement_text)
            
            assert 'structured_requirement' in result
            assert 'confidence_score' in result
            mock_api.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_with_deep_mode(self, sample_requirement_text):
        """测试2: 深度分析模式"""
        analyzer = AIRequirementAnalyzer(api_key="test_key")
        
        with patch.object(analyzer, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = '{"structured_requirement": {}}'
            
            result = await analyzer.analyze_requirement(sample_requirement_text, "deep")
            
            assert result is not None
            # 验证deep模式调用了正确的prompt
            call_args = mock_api.call_args[0]
            assert "深度分析" in call_args[0]
    
    @pytest.mark.asyncio
    async def test_analyze_extracts_equipment(self, mock_openai_response):
        """测试3: 设备识别"""
        analyzer = AIRequirementAnalyzer(api_key="test_key")
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = mock_openai_response
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response
            
            result = await analyzer.analyze_requirement("需要机器人和视觉系统")
            
            assert 'equipment_list' in result
            assert len(result['equipment_list']) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_extracts_technical_parameters(self, mock_openai_response):
        """测试4: 技术参数提取"""
        analyzer = AIRequirementAnalyzer(api_key="test_key")
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = mock_openai_response
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response
            
            result = await analyzer.analyze_requirement("精度±0.05mm，产能200件/小时")
            
            assert 'technical_parameters' in result
            assert len(result['technical_parameters']) > 0
    
    @pytest.mark.asyncio
    async def test_confidence_score_calculation(self, sample_requirement_text):
        """测试5: 置信度计算"""
        analyzer = AIRequirementAnalyzer(api_key="test_key")
        
        parsed_result = {
            'structured_requirement': {
                'project_type': '自动化',
                'core_objectives': ['目标1', '目标2'],
                'functional_requirements': ['需求1']
            },
            'equipment_list': [{'name': '设备1'}],
            'technical_parameters': [{'name': '参数1'}],
            'process_flow': [{'step': 1}]
        }
        
        score = analyzer._calculate_confidence_score(sample_requirement_text, parsed_result)
        
        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)
    
    @pytest.mark.asyncio
    async def test_fallback_on_api_failure(self, sample_requirement_text):
        """测试6: API失败时的降级处理"""
        analyzer = AIRequirementAnalyzer(api_key="test_key")
        
        with patch.object(analyzer, '_call_openai_api', side_effect=Exception("API Error")):
            result = await analyzer.analyze_requirement(sample_requirement_text)
            
            # 应该返回降级的规则分析结果
            assert result is not None
            assert 'structured_requirement' in result
            assert result.get('confidence_score', 0) < 0.5  # 降级结果置信度较低
    
    @pytest.mark.asyncio
    async def test_extract_json_from_code_block(self):
        """测试7: 从代码块提取JSON"""
        analyzer = AIRequirementAnalyzer(api_key="test_key")
        
        response = """
        这是一些说明文字
        ```json
        {"key": "value", "number": 42}
        ```
        后续文字
        """
        
        result = analyzer._extract_json_from_response(response)
        
        assert result == {"key": "value", "number": 42}
    
    @pytest.mark.asyncio
    async def test_parse_complex_requirement(self):
        """测试8: 解析复杂需求"""
        analyzer = AIRequirementAnalyzer(api_key="test_key")
        
        complex_req = """
        项目需求：智能仓储系统
        包含：AGV小车、自动货架、WMS系统
        技术指标：存储容量1000托盘，出入库效率50托盘/小时
        环境：常温仓库，需要防尘防潮
        预算：500万以内
        工期：6个月
        """
        
        with patch.object(analyzer, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = '{"structured_requirement": {"project_type": "智能仓储"}}'
            
            result = await analyzer.analyze_requirement(complex_req)
            
            assert result is not None
            assert result.get('confidence_score', 0) > 0


# ========== 问题生成测试 (6个) ==========

class TestQuestionGeneration:
    """问题生成测试"""
    
    @pytest.mark.asyncio
    async def test_generate_clarification_questions(self, sample_requirement_text):
        """测试9: 生成澄清问题"""
        analyzer = AIRequirementAnalyzer(api_key="test_key")
        
        with patch.object(analyzer, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = json.dumps([
                {"question_id": 1, "category": "技术参数", "question": "精度要求？", "importance": "critical"},
                {"question_id": 2, "category": "功能需求", "question": "需要哪些功能？", "importance": "high"}
            ])
            
            questions = await analyzer.generate_clarification_questions(sample_requirement_text)
            
            assert len(questions) > 0
            assert all(isinstance(q, ClarificationQuestion) for q in questions)
    
    @pytest.mark.asyncio
    async def test_questions_have_categories(self, sample_requirement_text):
        """测试10: 问题包含分类"""
        analyzer = AIRequirementAnalyzer(api_key="test_key")
        
        with patch.object(analyzer, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = json.dumps([
                {"question_id": 1, "category": "技术参数", "question": "Q1", "importance": "high"}
            ])
            
            questions = await analyzer.generate_clarification_questions(sample_requirement_text)
            
            assert questions[0].category in ["技术参数", "功能需求", "约束条件", "验收标准", "资源预算"]
    
    @pytest.mark.asyncio
    async def test_questions_have_importance(self, sample_requirement_text):
        """测试11: 问题包含重要性"""
        analyzer = AIRequirementAnalyzer(api_key="test_key")
        
        with patch.object(analyzer, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = json.dumps([
                {"question_id": 1, "category": "技术", "question": "Q1", "importance": "critical"}
            ])
            
            questions = await analyzer.generate_clarification_questions(sample_requirement_text)
            
            assert questions[0].importance in ["critical", "high", "medium", "low"]
    
    @pytest.mark.asyncio
    async def test_generate_5_to_10_questions(self, sample_requirement_text):
        """测试12: 生成5-10个问题"""
        analyzer = AIRequirementAnalyzer(api_key="test_key")
        
        with patch.object(analyzer, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            # 模拟生成8个问题
            mock_questions = [
                {"question_id": i, "category": "技术", "question": f"Q{i}", "importance": "medium"}
                for i in range(1, 9)
            ]
            mock_api.return_value = json.dumps(mock_questions)
            
            questions = await analyzer.generate_clarification_questions(sample_requirement_text)
            
            assert 5 <= len(questions) <= 10
    
    @pytest.mark.asyncio
    async def test_fallback_question_generation(self, sample_requirement_text):
        """测试13: 问题生成失败时的降级"""
        analyzer = AIRequirementAnalyzer(api_key="test_key")
        
        with patch.object(analyzer, '_call_openai_api', side_effect=Exception("API Error")):
            questions = await analyzer.generate_clarification_questions(sample_requirement_text)
            
            # 应该返回默认问题
            assert len(questions) >= 5
            assert all(isinstance(q, ClarificationQuestion) for q in questions)
    
    @pytest.mark.asyncio
    async def test_questions_with_structured_data(self, sample_requirement_text):
        """测试14: 基于结构化数据生成问题"""
        analyzer = AIRequirementAnalyzer(api_key="test_key")
        
        structured_data = {
            "equipment_list": [{"name": "机器人", "type": "六轴"}],
            "technical_parameters": []
        }
        
        with patch.object(analyzer, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = json.dumps([
                {"question_id": 1, "category": "技术参数", "question": "机器人负载？", "importance": "high"}
            ])
            
            questions = await analyzer.generate_clarification_questions(
                sample_requirement_text, 
                structured_data
            )
            
            assert len(questions) > 0


# ========== 结构化输出测试 (6个) ==========

class TestStructuredOutput:
    """结构化输出测试"""
    
    def test_structured_requirement_schema(self):
        """测试15: 结构化需求Schema验证"""
        data = {
            "project_type": "自动化",
            "industry": "汽车",
            "core_objectives": ["目标1"],
            "functional_requirements": ["功能1"],
            "non_functional_requirements": ["性能1"]
        }
        
        sr = StructuredRequirement(**data)
        
        assert sr.project_type == "自动化"
        assert len(sr.core_objectives) == 1
    
    def test_equipment_item_schema(self):
        """测试16: 设备项Schema验证"""
        data = {
            "name": "工业机器人",
            "type": "六轴机器人",
            "quantity": 2,
            "priority": "high"
        }
        
        eq = EquipmentItem(**data)
        
        assert eq.name == "工业机器人"
        assert eq.quantity == 2
    
    def test_process_step_schema(self):
        """测试17: 工艺步骤Schema验证"""
        data = {
            "step_number": 1,
            "name": "上料",
            "description": "自动上料"
        }
        
        step = ProcessStep(**data)
        
        assert step.step_number == 1
        assert step.name == "上料"
    
    def test_technical_parameter_schema(self):
        """测试18: 技术参数Schema验证"""
        data = {
            "parameter_name": "精度",
            "value": "±0.05mm",
            "unit": "mm",
            "is_critical": True
        }
        
        param = TechnicalParameter(**data)
        
        assert param.is_critical is True
        assert param.unit == "mm"
    
    def test_equipment_quantity_validation(self):
        """测试19: 设备数量验证"""
        with pytest.raises(ValueError):
            EquipmentItem(
                name="机器人",
                type="六轴",
                quantity=0  # 数量必须≥1
            )
    
    def test_process_step_number_validation(self):
        """测试20: 步骤序号验证"""
        with pytest.raises(ValueError):
            ProcessStep(
                step_number=0,  # 步骤序号必须≥1
                name="步骤",
                description="描述"
            )


# ========== API集成测试 (5个) ==========

class TestAPIIntegration:
    """API集成测试"""
    
    @pytest.mark.asyncio
    async def test_service_analyze_requirement(self, test_db, sample_requirement_text):
        """测试21: 服务层需求分析"""
        service = PresaleAIRequirementService(test_db)
        
        request = RequirementAnalysisRequest(
            presale_ticket_id=1,
            raw_requirement=sample_requirement_text,
            ai_model="gpt-4"
        )
        
        with patch.object(service.analyzer, 'analyze_requirement', new_callable=AsyncMock) as mock_analyze:
            with patch.object(service.analyzer, 'generate_clarification_questions', new_callable=AsyncMock) as mock_questions:
                with patch.object(service.analyzer, 'perform_feasibility_analysis', new_callable=AsyncMock) as mock_feasibility:
                    # 模拟返回
                    mock_analyze.return_value = {
                        'structured_requirement': {},
                        'equipment_list': [],
                        'confidence_score': 0.75
                    }
                    mock_questions.return_value = []
                    mock_feasibility.return_value = Mock(dict=lambda: {})
                    
                    result = await service.analyze_requirement(request, user_id=1)
                    
                    assert result.id is not None
                    assert result.presale_ticket_id == 1
                    assert result.confidence_score == 0.75
    
    def test_service_get_analysis(self, test_db):
        """测试22: 获取分析结果"""
        service = PresaleAIRequirementService(test_db)
        
        # 创建测试记录
        analysis = PresaleAIRequirementAnalysis(
            presale_ticket_id=1,
            raw_requirement="测试需求",
            confidence_score=0.8,
            created_by=1
        )
        test_db.add(analysis)
        test_db.commit()
        
        result = service.get_analysis(analysis.id)
        
        assert result is not None
        assert result.id == analysis.id
    
    @pytest.mark.asyncio
    async def test_service_refine_requirement(self, test_db):
        """测试23: 精炼需求"""
        service = PresaleAIRequirementService(test_db)
        
        # 创建初始分析
        analysis = PresaleAIRequirementAnalysis(
            presale_ticket_id=1,
            raw_requirement="初始需求",
            confidence_score=0.6,
            created_by=1
        )
        test_db.add(analysis)
        test_db.commit()
        
        request = RequirementRefinementRequest(
            analysis_id=analysis.id,
            additional_context="补充信息"
        )
        
        with patch.object(service.analyzer, 'analyze_requirement', new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                'structured_requirement': {},
                'confidence_score': 0.85
            }
            
            result = await service.refine_requirement(request, user_id=1)
            
            assert result.is_refined is True
            assert result.refinement_count == 1
            assert result.confidence_score == 0.85
    
    def test_service_get_clarification_questions(self, test_db):
        """测试24: 获取澄清问题"""
        service = PresaleAIRequirementService(test_db)
        
        # 创建带问题的分析
        questions_data = [
            {"question_id": 1, "category": "技术", "question": "Q1", "importance": "high"},
            {"question_id": 2, "category": "功能", "question": "Q2", "importance": "medium"}
        ]
        
        analysis = PresaleAIRequirementAnalysis(
            presale_ticket_id=1,
            raw_requirement="测试",
            clarification_questions=questions_data,
            created_by=1
        )
        test_db.add(analysis)
        test_db.commit()
        
        questions, analysis_id = service.get_clarification_questions(1)
        
        assert len(questions) == 2
        assert analysis_id == analysis.id
        assert all(isinstance(q, ClarificationQuestion) for q in questions)
    
    def test_service_get_confidence(self, test_db):
        """测试25: 获取置信度评分"""
        service = PresaleAIRequirementService(test_db)
        
        # 创建高置信度分析
        analysis = PresaleAIRequirementAnalysis(
            presale_ticket_id=1,
            raw_requirement="测试",
            confidence_score=0.90,
            created_by=1
        )
        test_db.add(analysis)
        test_db.commit()
        
        result = service.get_requirement_confidence(1)
        
        assert result['confidence_score'] == 0.90
        assert result['assessment'] == 'high_confidence'
        assert len(result['recommendations']) > 0


# ========== 额外测试 (验收标准相关) ==========

class TestAcceptanceCriteria:
    """验收标准测试"""
    
    @pytest.mark.asyncio
    async def test_response_time_under_3_seconds(self, sample_requirement_text):
        """测试26: 响应时间<3秒"""
        import time
        
        analyzer = AIRequirementAnalyzer(api_key="test_key")
        
        with patch.object(analyzer, '_call_openai_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = '{"structured_requirement": {}}'
            
            start_time = time.time()
            await analyzer.analyze_requirement(sample_requirement_text)
            elapsed_time = time.time() - start_time
            
            # 在模拟环境下应该非常快
            assert elapsed_time < 3.0
    
    def test_requirement_update(self, test_db):
        """测试27: 更新结构化需求"""
        service = PresaleAIRequirementService(test_db)
        
        # 创建初始分析
        analysis = PresaleAIRequirementAnalysis(
            presale_ticket_id=1,
            raw_requirement="测试",
            created_by=1
        )
        test_db.add(analysis)
        test_db.commit()
        
        # 更新请求
        equipment = [EquipmentItem(name="机器人", type="六轴", quantity=1)]
        request = RequirementUpdateRequest(
            analysis_id=analysis.id,
            equipment_list=equipment
        )
        
        result = service.update_structured_requirement(request, user_id=1)
        
        assert result.equipment_list is not None
        assert len(result.equipment_list) == 1
        assert result.status == "reviewed"
    
    def test_confidence_score_breakdown(self, test_db):
        """测试28: 置信度分数分解"""
        service = PresaleAIRequirementService(test_db)
        
        analysis = PresaleAIRequirementAnalysis(
            presale_ticket_id=1,
            raw_requirement="测试",
            confidence_score=0.80,
            created_by=1
        )
        test_db.add(analysis)
        test_db.commit()
        
        result = service.get_requirement_confidence(1)
        
        assert 'score_breakdown' in result
        breakdown = result['score_breakdown']
        assert '需求完整性' in breakdown
        assert '技术清晰度' in breakdown
        assert '参数明确性' in breakdown
        assert '可执行性' in breakdown
