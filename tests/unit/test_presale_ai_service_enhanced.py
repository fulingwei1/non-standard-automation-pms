"""
售前AI方案生成服务增强测试
Enhanced Unit Tests for Presale AI Service
"""
import unittest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime
from decimal import Decimal
import json

from app.services.presale_ai_service import PresaleAIService
from app.models.presale_ai_solution import (
    PresaleAISolution,
    PresaleSolutionTemplate,
    PresaleAIGenerationLog
)
from app.schemas.presale_ai_solution import (
    TemplateMatchRequest,
    SolutionGenerationRequest,
    ArchitectureGenerationRequest,
    BOMGenerationRequest
)


class TestPresaleAIServiceInit(unittest.TestCase):
    """测试初始化"""
    
    def test_init_success(self):
        """测试正常初始化"""
        mock_db = MagicMock()
        with patch('app.services.presale_ai_service.AIClientService'):
            service = PresaleAIService(db=mock_db)
            self.assertEqual(service.db, mock_db)
            self.assertIsNotNone(service.ai_client)


class TestTemplateMatching(unittest.TestCase):
    """测试模板匹配功能"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.presale_ai_service.AIClientService'):
            self.service = PresaleAIService(db=self.mock_db)
    
    def test_match_templates_with_industry_filter(self):
        """测试按行业过滤模板"""
        # 准备模拟数据
        mock_template = MagicMock(spec=PresaleSolutionTemplate)
        mock_template.id = 1
        mock_template.name = "智能仓储模板"
        mock_template.industry = "物流"
        mock_template.equipment_type = "仓储"
        mock_template.keywords = "仓储 自动化 AGV"
        mock_template.usage_count = 10
        mock_template.avg_quality_score = Decimal("4.5")
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_template]
        self.mock_db.query.return_value = mock_query
        
        # 执行测试
        request = TemplateMatchRequest(
            presale_ticket_id=1,
            industry="物流",
            keywords="仓储 AGV",
            top_k=5
        )
        results, search_time = self.service.match_templates(request, user_id=1)
        
        # 验证
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].template_id, 1)
        self.assertEqual(results[0].industry, "物流")
        self.assertGreaterEqual(search_time, 0)
    
    def test_match_templates_with_equipment_type_filter(self):
        """测试按设备类型过滤"""
        mock_template = MagicMock(spec=PresaleSolutionTemplate)
        mock_template.id = 2
        mock_template.name = "装配线模板"
        mock_template.industry = "制造"
        mock_template.equipment_type = "装配"
        mock_template.keywords = "装配 自动化"
        mock_template.usage_count = 5
        mock_template.avg_quality_score = None
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_template]
        self.mock_db.query.return_value = mock_query
        
        request = TemplateMatchRequest(
            presale_ticket_id=1,
            equipment_type="装配",
            top_k=3
        )
        results, _ = self.service.match_templates(request, user_id=1)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].equipment_type, "装配")
        self.assertIsNone(results[0].avg_quality_score)
    
    def test_match_templates_with_keywords_similarity(self):
        """测试关键词相似度匹配"""
        templates = [
            self._create_mock_template(1, "模板A", "仓储 AGV 物流", 5),
            self._create_mock_template(2, "模板B", "装配 机器人", 3),
            self._create_mock_template(3, "模板C", "仓储 自动化 AGV", 8),
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = templates
        self.mock_db.query.return_value = mock_query
        
        request = TemplateMatchRequest(
            presale_ticket_id=1,
            keywords="仓储 AGV",
            top_k=2
        )
        results, _ = self.service.match_templates(request, user_id=1)
        
        # 应返回相似度最高的2个模板
        self.assertEqual(len(results), 2)
        # 第一个应该是包含"仓储 AGV"的模板
        self.assertGreater(results[0].similarity_score, 0)
    
    def test_match_templates_no_keywords_sort_by_usage(self):
        """测试无关键词时按使用次数排序"""
        templates = [
            self._create_mock_template(1, "模板A", "关键词A", 5),
            self._create_mock_template(2, "模板B", "关键词B", 15),
            self._create_mock_template(3, "模板C", "关键词C", 10),
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = templates
        self.mock_db.query.return_value = mock_query
        
        request = TemplateMatchRequest(presale_ticket_id=1, top_k=3)
        results, _ = self.service.match_templates(request, user_id=1)
        
        # 应按usage_count降序排列
        self.assertEqual(results[0].template_id, 2)  # usage_count=15
        self.assertEqual(results[1].template_id, 3)  # usage_count=10
        self.assertEqual(results[2].template_id, 1)  # usage_count=5
    
    def test_match_templates_empty_result(self):
        """测试无匹配结果"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        self.mock_db.query.return_value = mock_query
        
        request = TemplateMatchRequest(presale_ticket_id=1, industry="未知行业", top_k=5)
        results, _ = self.service.match_templates(request, user_id=1)
        
        self.assertEqual(len(results), 0)
    
    def test_calculate_similarity_jaccard(self):
        """测试Jaccard相似度计算"""
        score1 = self.service._calculate_similarity("仓储 AGV 自动化", "仓储 AGV")
        self.assertGreater(score1, 0)
        
        score2 = self.service._calculate_similarity("仓储 AGV", "仓储 AGV")
        self.assertEqual(score2, 1.0)
        
        score3 = self.service._calculate_similarity("完全不同", "totally different")
        self.assertEqual(score3, 0.0)
    
    def test_calculate_similarity_empty_input(self):
        """测试空输入的相似度计算"""
        score1 = self.service._calculate_similarity("", "仓储 AGV")
        self.assertEqual(score1, 0.0)
        
        score2 = self.service._calculate_similarity("仓储", "")
        self.assertEqual(score2, 0.0)
        
        score3 = self.service._calculate_similarity("", "")
        self.assertEqual(score3, 0.0)
    
    def _create_mock_template(self, id, name, keywords, usage_count):
        """辅助方法：创建模拟模板"""
        template = MagicMock(spec=PresaleSolutionTemplate)
        template.id = id
        template.name = name
        template.industry = "制造"
        template.equipment_type = "通用"
        template.keywords = keywords
        template.usage_count = usage_count
        template.avg_quality_score = Decimal("4.0")
        return template


class TestSolutionGeneration(unittest.TestCase):
    """测试方案生成功能"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.presale_ai_service.AIClientService') as MockAI:
            self.mock_ai_client = MockAI.return_value
            self.service = PresaleAIService(db=self.mock_db)
            self.service.ai_client = self.mock_ai_client
    
    @patch('app.services.presale_ai_service.save_obj')
    def test_generate_solution_basic(self, mock_save):
        """测试基础方案生成"""
        # 模拟数据库查询
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        # 模拟AI响应
        self.mock_ai_client.generate_solution.return_value = {
            "content": json.dumps({
                "description": "智能仓储系统方案",
                "technical_parameters": {"capacity": "1000件/天"},
                "equipment_list": [{"name": "AGV小车", "quantity": 5}],
                "process_flow": "入库-存储-出库",
                "key_features": ["智能调度"],
                "technical_advantages": ["高效率"]
            }),
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 200,
                "total_tokens": 300
            }
        }
        
        # 执行测试
        request = SolutionGenerationRequest(
            presale_ticket_id=1,
            requirements={"industry": "物流", "capacity": 1000},
            ai_model="gpt-4",
            generate_architecture=False,
            generate_bom=False
        )
        
        result = self.service.generate_solution(request, user_id=1)
        
        # 验证
        self.assertIn("solution_id", result)
        self.assertIn("solution", result)
        self.assertEqual(result["solution"]["description"], "智能仓储系统方案")
        self.assertGreater(result["confidence_score"], 0)
        self.assertEqual(result["ai_model_used"], "gpt-4")
        mock_save.assert_called_once()
    
    @patch('app.services.presale_ai_service.save_obj')
    def test_generate_solution_with_template(self, mock_save):
        """测试使用模板生成方案"""
        # 模拟模板
        mock_template = MagicMock(spec=PresaleSolutionTemplate)
        mock_template.id = 1
        mock_template.name = "仓储模板"
        mock_template.industry = "物流"
        mock_template.equipment_type = "仓储"
        mock_template.solution_content = {"sample": "content"}
        
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = mock_template
        self.mock_db.query.return_value = mock_query
        
        # 模拟AI响应
        self.mock_ai_client.generate_solution.return_value = {
            "content": '{"description": "基于模板的方案"}',
            "usage": {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150}
        }
        
        # 模拟 save_obj 以设置 ID
        def set_id(db, obj):
            obj.id = 2
            return obj
        mock_save.side_effect = set_id
        
        request = SolutionGenerationRequest(
            presale_ticket_id=1,
            template_id=1,
            requirements={"capacity": 500},
            ai_model="gpt-3.5-turbo"
        )
        
        result = self.service.generate_solution(request, user_id=1)
        
        self.assertIsNotNone(result["solution_id"])
        # 置信度应该因为有模板而更高
        self.assertGreaterEqual(result["confidence_score"], 0.5)
    
    def test_build_solution_prompt_without_template(self):
        """测试无模板的提示词构建"""
        requirements = {"industry": "物流", "capacity": 1000}
        prompt = self.service._build_solution_prompt(requirements, None)
        
        self.assertIn("需求信息", prompt)
        self.assertIn("物流", prompt)
        self.assertNotIn("参考模板", prompt)
    
    def test_build_solution_prompt_with_template(self):
        """测试有模板的提示词构建"""
        mock_template = MagicMock(spec=PresaleSolutionTemplate)
        mock_template.name = "测试模板"
        mock_template.industry = "制造"
        mock_template.equipment_type = "装配"
        mock_template.solution_content = {"key": "value"}
        
        requirements = {"capacity": 500}
        prompt = self.service._build_solution_prompt(requirements, mock_template)
        
        self.assertIn("参考模板", prompt)
        self.assertIn("测试模板", prompt)
        self.assertIn("制造", prompt)
    
    def test_parse_solution_response_json_code_block(self):
        """测试解析JSON代码块响应"""
        ai_response = {
            "content": """这是方案：
```json
{
    "description": "测试方案",
    "technical_parameters": {"param1": "value1"}
}
```
"""
        }
        
        result = self.service._parse_solution_response(ai_response)
        
        self.assertEqual(result["description"], "测试方案")
        self.assertEqual(result["technical_parameters"]["param1"], "value1")
    
    def test_parse_solution_response_plain_code_block(self):
        """测试解析普通代码块响应"""
        ai_response = {
            "content": """```
{"description": "普通代码块", "equipment_list": []}
```"""
        }
        
        result = self.service._parse_solution_response(ai_response)
        
        self.assertEqual(result["description"], "普通代码块")
    
    def test_parse_solution_response_direct_json(self):
        """测试解析直接JSON响应"""
        ai_response = {
            "content": '{"description": "直接JSON", "process_flow": "流程"}'
        }
        
        result = self.service._parse_solution_response(ai_response)
        
        self.assertEqual(result["description"], "直接JSON")
        self.assertEqual(result["process_flow"], "流程")
    
    def test_parse_solution_response_invalid_json(self):
        """测试解析无效JSON"""
        ai_response = {
            "content": "这不是有效的JSON"
        }
        
        result = self.service._parse_solution_response(ai_response)
        
        # 应返回默认结构
        self.assertIn("description", result)
        self.assertIn("technical_parameters", result)
        self.assertIn("equipment_list", result)
        self.assertEqual(result["description"], "这不是有效的JSON")
    
    def test_calculate_confidence_base_score(self):
        """测试基础置信度"""
        solution = {}
        score = self.service._calculate_confidence(solution, None)
        self.assertEqual(score, 0.5)
    
    def test_calculate_confidence_with_template(self):
        """测试有模板的置信度"""
        solution = {}
        mock_template = MagicMock()
        score = self.service._calculate_confidence(solution, mock_template)
        self.assertEqual(score, 0.7)  # 0.5 + 0.2
    
    def test_calculate_confidence_full_score(self):
        """测试完整方案的置信度"""
        solution = {
            "equipment_list": [{"name": "设备1"}],
            "technical_parameters": {"param1": "value1"},
            "process_flow": "完整流程"
        }
        mock_template = MagicMock()
        score = self.service._calculate_confidence(solution, mock_template)
        self.assertEqual(score, 1.0)  # 0.5 + 0.2 + 0.15 + 0.1 + 0.05


class TestArchitectureGeneration(unittest.TestCase):
    """测试架构图生成"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.presale_ai_service.AIClientService') as MockAI:
            self.mock_ai_client = MockAI.return_value
            self.service = PresaleAIService(db=self.mock_db)
            self.service.ai_client = self.mock_ai_client
    
    def test_generate_architecture_basic(self):
        """测试基础架构图生成"""
        self.mock_ai_client.generate_architecture.return_value = {
            "content": """```mermaid
graph TD
    A[控制系统] --> B[执行单元]
```"""
        }
        
        requirements = {"system_type": "控制系统"}
        result = self.service.generate_architecture(requirements)
        
        self.assertIn("diagram_code", result)
        self.assertIn("graph TD", result["diagram_code"])
        self.assertEqual(result["diagram_type"], "architecture")
        self.assertEqual(result["format"], "mermaid")
    
    def test_generate_architecture_with_solution_id(self):
        """测试关联方案ID生成架构图"""
        mock_solution = MagicMock(spec=PresaleAISolution)
        mock_solution.id = 1
        mock_solution.architecture_diagram = None
        
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = mock_solution
        self.mock_db.query.return_value = mock_query
        
        self.mock_ai_client.generate_architecture.return_value = {
            "content": "```mermaid\ngraph LR\n```"
        }
        
        result = self.service.generate_architecture(
            requirements={},
            solution_id=1
        )
        
        # 验证方案被更新
        self.assertIsNotNone(mock_solution.architecture_diagram)
        self.mock_db.commit.assert_called()
    
    def test_generate_architecture_topology_type(self):
        """测试拓扑图类型"""
        mock_solution = MagicMock(spec=PresaleAISolution)
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = mock_solution
        self.mock_db.query.return_value = mock_query
        
        self.mock_ai_client.generate_architecture.return_value = {
            "content": "```mermaid\ngraph\n```"
        }
        
        result = self.service.generate_architecture(
            requirements={},
            diagram_type="topology",
            solution_id=1
        )
        
        self.assertEqual(result["diagram_type"], "topology")
        self.assertIsNotNone(mock_solution.topology_diagram)
    
    def test_build_architecture_prompt_types(self):
        """测试不同类型架构图提示词"""
        requirements = {"system": "test"}
        
        prompt_arch = self.service._build_architecture_prompt(requirements, "architecture")
        self.assertIn("系统架构图", prompt_arch)
        
        prompt_topo = self.service._build_architecture_prompt(requirements, "topology")
        self.assertIn("设备拓扑图", prompt_topo)
        
        prompt_signal = self.service._build_architecture_prompt(requirements, "signal_flow")
        self.assertIn("信号流程图", prompt_signal)
    
    def test_extract_mermaid_code_with_mermaid_tag(self):
        """测试提取mermaid标记的代码"""
        content = """说明文字
```mermaid
graph TD
    A --> B
```
其他内容"""
        
        code = self.service._extract_mermaid_code(content)
        self.assertEqual(code.strip(), "graph TD\n    A --> B")
    
    def test_extract_mermaid_code_with_generic_tag(self):
        """测试提取普通代码块"""
        content = """```
graph LR
    X --> Y
```"""
        
        code = self.service._extract_mermaid_code(content)
        self.assertIn("graph LR", code)
    
    def test_extract_mermaid_code_plain_text(self):
        """测试提取纯文本"""
        content = "graph TD\n    A --> B"
        code = self.service._extract_mermaid_code(content)
        self.assertEqual(code, content.strip())


class TestBOMGeneration(unittest.TestCase):
    """测试BOM清单生成"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.presale_ai_service.AIClientService'):
            self.service = PresaleAIService(db=self.mock_db)
    
    def test_generate_bom_basic(self):
        """测试基础BOM生成"""
        equipment_list = [
            {"name": "AGV小车", "model": "AGV-100", "quantity": 5, "unit": "台"},
            {"name": "传感器", "model": "SEN-200", "quantity": 10, "unit": "个"}
        ]
        
        result = self.service.generate_bom(equipment_list, include_cost=True)
        
        self.assertEqual(result["item_count"], 2)
        self.assertGreater(result["total_cost"], 0)
        self.assertEqual(len(result["bom_items"]), 2)
    
    def test_generate_bom_without_cost(self):
        """测试不含成本的BOM"""
        equipment_list = [{"name": "设备A", "quantity": 1}]
        
        result = self.service.generate_bom(equipment_list, include_cost=False)
        
        self.assertNotIn("unit_price", result["bom_items"][0])
    
    def test_generate_bom_with_solution_id(self):
        """测试关联方案ID生成BOM"""
        mock_solution = MagicMock(spec=PresaleAISolution)
        mock_solution.id = 1
        
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = mock_solution
        self.mock_db.query.return_value = mock_query
        
        equipment_list = [{"name": "设备", "quantity": 2}]
        
        result = self.service.generate_bom(equipment_list, solution_id=1)
        
        self.assertIsNotNone(mock_solution.bom_list)
        self.assertIsNotNone(mock_solution.estimated_cost)
        self.mock_db.commit.assert_called()
    
    def test_generate_bom_item_with_cost(self):
        """测试生成单个BOM项（含成本）"""
        equipment = {
            "name": "机器人",
            "model": "ROBOT-X",
            "quantity": 3,
            "unit": "台",
            "notes": "高精度机器人"
        }
        
        item = self.service._generate_bom_item(equipment, include_cost=True, include_suppliers=False)
        
        self.assertEqual(item["item_name"], "机器人")
        self.assertEqual(item["model"], "ROBOT-X")
        self.assertEqual(item["quantity"], 3)
        self.assertIn("unit_price", item)
        self.assertIn("total_price", item)
    
    def test_generate_bom_item_with_suppliers(self):
        """测试生成BOM项（含供应商）"""
        equipment = {"name": "传感器", "quantity": 5}
        
        item = self.service._generate_bom_item(
            equipment,
            include_cost=False,
            include_suppliers=True
        )
        
        self.assertIn("supplier", item)
        self.assertIn("lead_time_days", item)
    
    def test_generate_bom_empty_list(self):
        """测试空设备列表"""
        result = self.service.generate_bom([], include_cost=True)
        
        self.assertEqual(result["item_count"], 0)
        self.assertEqual(result["total_cost"], Decimal("0"))
        self.assertEqual(len(result["bom_items"]), 0)


class TestLoggingAndQueries(unittest.TestCase):
    """测试日志记录和查询功能"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.presale_ai_service.AIClientService'):
            self.service = PresaleAIService(db=self.mock_db)
    
    def test_log_generation(self):
        """测试生成日志记录"""
        self.service._log_generation(
            solution_id=1,
            request_type="solution",
            input_data={"req": "data"},
            output_data={"result": "data"},
            success=True,
            response_time_ms=1500,
            ai_model="gpt-4",
            tokens_used=500
        )
        
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        
        # 验证日志对象
        log_call = self.mock_db.add.call_args[0][0]
        self.assertIsInstance(log_call, PresaleAIGenerationLog)
        self.assertEqual(log_call.solution_id, 1)
        self.assertEqual(log_call.success, 1)
    
    def test_get_solution_exists(self):
        """测试获取存在的方案"""
        mock_solution = MagicMock(spec=PresaleAISolution)
        mock_solution.id = 1
        
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = mock_solution
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_solution(1)
        
        self.assertEqual(result.id, 1)
    
    def test_get_solution_not_found(self):
        """测试获取不存在的方案"""
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_solution(999)
        
        self.assertIsNone(result)
    
    def test_update_solution_success(self):
        """测试更新方案成功"""
        mock_solution = MagicMock(spec=PresaleAISolution)
        mock_solution.id = 1
        
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = mock_solution
        self.mock_db.query.return_value = mock_query
        
        update_data = {
            "status": "approved",
            "confidence_score": Decimal("0.95")
        }
        
        result = self.service.update_solution(1, update_data)
        
        self.assertEqual(mock_solution.status, "approved")
        self.mock_db.commit.assert_called()
        self.mock_db.refresh.assert_called_with(mock_solution)
    
    def test_update_solution_not_found(self):
        """测试更新不存在的方案"""
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        with self.assertRaises(ValueError) as context:
            self.service.update_solution(999, {"status": "approved"})
        
        self.assertIn("not found", str(context.exception))
    
    def test_review_solution_approve(self):
        """测试审核通过方案"""
        mock_solution = MagicMock(spec=PresaleAISolution)
        mock_solution.id = 1
        
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = mock_solution
        self.mock_db.query.return_value = mock_query
        
        result = self.service.review_solution(
            solution_id=1,
            reviewer_id=2,
            status="approved",
            comments="方案优秀"
        )
        
        self.assertEqual(mock_solution.status, "approved")
        self.assertEqual(mock_solution.reviewed_by, 2)
        self.assertEqual(mock_solution.review_comments, "方案优秀")
        self.assertIsNotNone(mock_solution.reviewed_at)
    
    def test_review_solution_reject(self):
        """测试审核拒绝方案"""
        mock_solution = MagicMock(spec=PresaleAISolution)
        
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = mock_solution
        self.mock_db.query.return_value = mock_query
        
        result = self.service.review_solution(
            solution_id=1,
            reviewer_id=3,
            status="rejected",
            comments="需要改进"
        )
        
        self.assertEqual(mock_solution.status, "rejected")
        self.assertEqual(mock_solution.review_comments, "需要改进")
    
    def test_review_solution_not_found(self):
        """测试审核不存在的方案"""
        mock_query = MagicMock()
        mock_query.filter_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        with self.assertRaises(ValueError):
            self.service.review_solution(999, 1, "approved")


class TestTemplateLibrary(unittest.TestCase):
    """测试模板库管理"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        with patch('app.services.presale_ai_service.AIClientService'):
            self.service = PresaleAIService(db=self.mock_db)
    
    def test_get_template_library_all_active(self):
        """测试获取所有活跃模板"""
        templates = [
            self._create_template(1, "模板A", 10),
            self._create_template(2, "模板B", 5),
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = templates
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_template_library()
        
        self.assertEqual(len(result), 2)
    
    def test_get_template_library_filter_by_industry(self):
        """测试按行业过滤模板库"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_template_library(industry="物流")
        
        # 验证过滤被调用
        self.assertIsNotNone(result)
    
    def test_get_template_library_filter_by_equipment_type(self):
        """测试按设备类型过滤"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_template_library(equipment_type="装配")
        
        self.assertIsNotNone(result)
    
    def test_get_template_library_include_inactive(self):
        """测试包含非活跃模板"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query
        
        result = self.service.get_template_library(is_active=False)
        
        self.assertIsNotNone(result)
    
    def _create_template(self, id, name, usage_count):
        """辅助方法：创建模板"""
        template = MagicMock(spec=PresaleSolutionTemplate)
        template.id = id
        template.name = name
        template.usage_count = usage_count
        return template


if __name__ == '__main__':
    unittest.main()
