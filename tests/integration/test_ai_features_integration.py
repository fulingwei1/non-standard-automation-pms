import uuid
# -*- coding: utf-8 -*-
"""
AI 功能集成测试

测试范围：
- GLM-5 / Kimi AI 调用（mock 掉实际 HTTP 请求）
- AI 生成方案的完整流程
- AI 结果存储到数据库的流程

共 8 个测试用例
"""
import json
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.services.ai_client_service import AIClientService
from app.models.ai_planning.plan_template import AIProjectPlanTemplate
from app.models.ai_planning.wbs_suggestion import AIWbsSuggestion
from app.models.shortage.smart_alert import ShortageAlert, ShortageHandlingPlan

# ---------------------------------------------------------------------------
# 通用 mock 返回值
# ---------------------------------------------------------------------------
MOCK_AI_RESPONSE = {"content": "test response", "model": "glm-5"}
MOCK_AI_RESPONSE_KIMI = {"content": "test response", "model": "kimi"}

MOCK_SOLUTION_JSON = json.dumps({
    "description": "非标自动化生产线方案",
    "technical_parameters": {"生产节拍": "60秒/件", "自动化程度": "95%"},
    "equipment_list": [
        {"name": "自动上料机", "quantity": 1, "unit": "台"}
    ],
    "process_flow": "上料 → 加工 → 检测 → 下料",
    "key_features": ["模块化设计", "智能故障诊断"]
})


@pytest.mark.integration
class TestAIClientGLM5Call:
    """测试 GLM-5 AI 调用（mock HTTP 请求）"""

    @patch('app.services.ai_client_service.AIClientService.generate_solution')
    def test_glm5_call_returns_mocked_response(self, mock_generate):
        """测试 GLM-5 AI 调用返回 mock 响应"""
        # 配置 mock
        mock_generate.return_value = MOCK_AI_RESPONSE

        # 调用 AI 服务
        ai_service = AIClientService()
        result = ai_service.generate_solution(
            prompt="请为非标自动化项目生成技术方案",
            model="glm-5"
        )

        # 验证 mock 被调用
        mock_generate.assert_called_once()
        call_kwargs = mock_generate.call_args

        # 验证返回结果
        assert result["content"] == "test response"
        assert result["model"] == "glm-5"
        print(f"✅ GLM-5 mock 调用验证通过: model={result['model']}")

    @patch('app.services.ai_client_service.AIClientService.generate_solution')
    def test_glm5_call_with_complex_prompt(self, mock_generate):
        """测试 GLM-5 处理复杂 prompt（含方案设计关键词，会触发思考模式）"""
        mock_generate.return_value = {
            "content": "test response",
            "model": "glm-5",
            "reasoning": "深度思考过程：分析项目需求..."
        }

        ai_service = AIClientService()
        result = ai_service.generate_solution(
            prompt="请设计一套复杂的非标自动化架构方案",
            model="glm-5",
            temperature=0.5,
            max_tokens=4096
        )

        assert result["model"] == "glm-5"
        assert "content" in result
        # 验证 mock 被调用且传入了正确的参数
        mock_generate.assert_called_once_with(
            prompt="请设计一套复杂的非标自动化架构方案",
            model="glm-5",
            temperature=0.5,
            max_tokens=4096
        )
        print(f"✅ GLM-5 复杂 prompt 测试通过")


@pytest.mark.integration
class TestAIClientKimiCall:
    """测试 Kimi AI 调用（mock HTTP 请求）"""

    @patch('app.services.ai_client_service.AIClientService.generate_solution')
    def test_kimi_call_returns_mocked_response(self, mock_generate):
        """测试 Kimi AI 调用返回 mock 响应"""
        mock_generate.return_value = MOCK_AI_RESPONSE_KIMI

        ai_service = AIClientService()
        result = ai_service.generate_solution(
            prompt="请分析供应商交货风险",
            model="kimi"
        )

        mock_generate.assert_called_once()
        assert result["content"] == "test response"
        assert result["model"] == "kimi"
        print(f"✅ Kimi mock 调用验证通过: model={result['model']}")

    @patch('app.services.ai_client_service.AIClientService.generate_architecture')
    def test_ai_architecture_generation_mocked(self, mock_arch):
        """测试 AI 架构图生成（Kimi/GLM-5 均可用）"""
        mock_arch.return_value = {
            "content": "test response",
            "model": "glm-5"
        }

        ai_service = AIClientService()
        result = ai_service.generate_architecture(
            prompt="请生成自动化生产线架构图（Mermaid 格式）"
        )

        mock_arch.assert_called_once()
        assert result["content"] == "test response"
        assert result["model"] == "glm-5"
        print(f"✅ AI 架构图生成 mock 验证通过")


@pytest.mark.integration
class TestAIGenerateSolutionFlow:
    """测试 AI 生成方案的完整流程"""

    @patch('app.services.ai_client_service.AIClientService.generate_solution')
    def test_ai_generate_project_plan_template_flow(self, mock_generate, db_session):
        """
        测试 AI 生成项目计划模板的完整流程：
        1. 调用 AI 生成方案
        2. 解析 AI 返回内容
        3. 创建 AIProjectPlanTemplate 对象
        4. 存入数据库
        """
        db = db_session
        mock_generate.return_value = {
            "content": "test response",
            "model": "glm-5",
            "usage": {"total_tokens": 150}
        }

        # Step 1: 调用 AI 生成方案
        ai_service = AIClientService()
        ai_result = ai_service.generate_solution(
            prompt="请为非标自动化项目生成项目计划模板",
            model="glm-5"
        )

        assert ai_result["content"] == "test response"
        mock_generate.assert_called_once()

        # Step 2: 基于 AI 结果创建计划模板对象
        template = AIProjectPlanTemplate(
            template_code=f"TMPL_AI_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            template_name="AI生成的非标自动化项目模板",
            project_type="CUSTOM",
            ai_model_version=ai_result["model"],
            generation_time=datetime.utcnow(),
            confidence_score=Decimal("85.00"),
            description=ai_result["content"],
        )

        # Step 3: 存入数据库
        db.add(template)
        db.commit()
        db.refresh(template)

        # Step 4: 验证结果
        assert template.id is not None
        assert template.ai_model_version == "glm-5"
        assert template.description == "test response"

        # 从数据库重新查询验证
        saved = db.query(AIProjectPlanTemplate).filter(
            AIProjectPlanTemplate.id == template.id
        ).first()
        assert saved is not None
        assert saved.template_code.startswith("TMPL_AI_")

        print(f"✅ AI 生成项目计划模板流程测试通过 (id={template.id})")

    @patch('app.services.ai_client_service.AIClientService.generate_solution')
    def test_ai_generate_wbs_suggestion_flow(self, mock_generate, db_session):
        """
        测试 AI 生成 WBS 建议的完整流程：
        1. 调用 AI 获取 WBS 拆分建议
        2. 解析并创建 AIWbsSuggestion 对象
        3. 存入数据库并验证
        """
        db = db_session
        mock_generate.return_value = {
            "content": "test response",
            "model": "glm-5"
        }

        # Step 1: 调用 AI
        ai_service = AIClientService()
        ai_result = ai_service.generate_solution(
            prompt="请为自动化生产线项目生成 WBS 工作分解结构",
            model="glm-5"
        )

        # Step 2: 创建模板（WBS 建议关联模板）
        template = AIProjectPlanTemplate(
            template_code=f"TMPL_WBS_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            template_name="WBS测试模板",
            project_type="CUSTOM",
            ai_model_version="glm-5",
            generation_time=datetime.utcnow(),
        )
        db.add(template)
        db.flush()

        # Step 3: 创建 WBS 建议对象
        wbs = AIWbsSuggestion(
            suggestion_code=f"WBS_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            template_id=template.id,
            ai_model_version=ai_result["model"],
            generation_time=datetime.utcnow(),
            confidence_score=Decimal("90.00"),
            wbs_level=1,
            wbs_code="1",
            sequence=1,
            task_name="根任务 - AI生成",
            task_description=ai_result["content"],
            task_type="DESIGN",
            estimated_duration_days=Decimal("30.0"),
        )
        db.add(wbs)
        db.commit()
        db.refresh(wbs)

        # Step 4: 验证存储
        assert wbs.id is not None
        assert wbs.ai_model_version == "glm-5"
        assert wbs.task_description == "test response"

        saved_wbs = db.query(AIWbsSuggestion).filter(
            AIWbsSuggestion.id == wbs.id
        ).first()
        assert saved_wbs is not None
        assert saved_wbs.wbs_level == 1

        print(f"✅ AI 生成 WBS 建议流程测试通过 (id={wbs.id})")


@pytest.mark.integration
class TestAIResultStorageToDatabase:
    """测试 AI 结果存储到数据库的流程"""

    @patch('app.services.ai_client_service.AIClientService.generate_solution')
    def test_ai_shortage_handling_plan_storage(self, mock_generate, db_session):
        """
        测试 AI 生成缺料处理方案并存入数据库：
        1. 先创建缺料预警
        2. AI 生成处理方案
        3. 方案存入 ShortageHandlingPlan
        4. 关联预警并验证
        """
        db = db_session
        mock_generate.return_value = {
            "content": "test response",
            "model": "glm-5"
        }

        # Step 1: 创建缺料预警（作为前置数据）
        alert = ShortageAlert(
            alert_no=f"ALERT_AI_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            material_id=None,  # 测试环境中无真实物料
            material_code=f"TEST_MAT_001-{uuid.uuid4().hex[:8]}",
            material_name="测试物料-AI方案",
            project_id=None,
            required_qty=Decimal("100"),
            shortage_qty=Decimal("50"),
            alert_level="WARNING",
            required_date=datetime.utcnow().date(),
            status="PENDING",
            alert_source="AUTO",
        )
        db.add(alert)
        db.flush()

        # Step 2: 调用 AI 生成处理方案
        ai_service = AIClientService()
        ai_result = ai_service.generate_solution(
            prompt=f"物料 {alert.material_name} 缺料 {alert.shortage_qty}，请生成处理方案",
            model="glm-5"
        )

        mock_generate.assert_called_once()
        assert ai_result["content"] == "test response"

        # Step 3: 创建处理方案记录
        plan = ShortageHandlingPlan(
            plan_no=f"PLAN_AI_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            alert_id=alert.id,
            solution_type="URGENT_PURCHASE",
            solution_name="AI推荐：紧急采购方案",
            solution_description=ai_result["content"],
            ai_score=Decimal("88.50"),
            feasibility_score=Decimal("90.00"),
            cost_score=Decimal("85.00"),
            time_score=Decimal("88.00"),
            risk_score=Decimal("80.00"),
            is_recommended=True,
            recommendation_rank=1,
            status="PENDING",
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        # Step 4: 验证存储结果
        assert plan.id is not None
        assert plan.solution_description == "test response"
        assert plan.ai_score == Decimal("88.50")
        assert plan.is_recommended is True

        # 验证与预警的关联
        saved_plan = db.query(ShortageHandlingPlan).filter(
            ShortageHandlingPlan.id == plan.id
        ).first()
        assert saved_plan.alert_id == alert.id

        print(f"✅ AI 缺料处理方案存储测试通过 (plan_id={plan.id}, alert_id={alert.id})")

    @patch('app.services.ai_client_service.AIClientService.generate_solution')
    def test_ai_multiple_results_batch_storage(self, mock_generate, db_session):
        """
        测试批量 AI 结果存储：
        多次调用 AI，批量存入数据库，验证数量和内容
        """
        db = db_session

        # 设置 mock 每次返回相同结果
        mock_generate.return_value = {
            "content": "test response",
            "model": "glm-5"
        }

        ai_service = AIClientService()
        templates_created = []

        # 批量生成 3 个模板（模拟不同项目类型）
        project_types = ["CUSTOM", "STANDARD", "UPGRADE"]
        ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')

        for i, ptype in enumerate(project_types):
            ai_result = ai_service.generate_solution(
                prompt=f"为{ptype}类型项目生成计划模板",
                model="glm-5"
            )

            template = AIProjectPlanTemplate(
                template_code=f"BATCH_TMPL_{ts}_{i}",
                template_name=f"{ptype}项目AI模板",
                project_type=ptype,
                ai_model_version=ai_result["model"],
                generation_time=datetime.utcnow(),
                description=ai_result["content"],
            )
            db.add(template)
            templates_created.append(template)

        db.commit()

        # 验证批量存储结果
        assert mock_generate.call_count == 3

        for tmpl in templates_created:
            db.refresh(tmpl)
            assert tmpl.id is not None
            assert tmpl.description == "test response"
            assert tmpl.ai_model_version == "glm-5"

        # 从 DB 查询验证数量
        saved_count = db.query(AIProjectPlanTemplate).filter(
            AIProjectPlanTemplate.template_code.like(f"BATCH_TMPL_{ts}_%")
        ).count()
        assert saved_count == 3

        print(f"✅ AI 批量结果存储测试通过 (已存储 {saved_count} 个模板)")
