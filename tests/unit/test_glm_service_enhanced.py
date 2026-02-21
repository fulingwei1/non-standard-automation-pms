# -*- coding: utf-8 -*-
"""
GLM Service 增强单元测试
测试覆盖所有核心方法和边界条件
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import json
import os
from typing import Dict, List


class TestGLMServiceInit(unittest.TestCase):
    """测试 GLMService 初始化"""
    
    @patch('app.services.ai_planning.glm_service.ZhipuAI')
    def test_init_with_api_key(self, mock_zhipuai):
        """测试使用API密钥初始化"""
        from app.services.ai_planning.glm_service import GLMService
        
        service = GLMService(api_key="test-api-key")
        
        self.assertEqual(service.api_key, "test-api-key")
        mock_zhipuai.assert_called_once_with(api_key="test-api-key")
        self.assertIsNotNone(service.client)
    
    @patch.dict(os.environ, {'GLM_API_KEY': 'env-api-key'})
    @patch('app.services.ai_planning.glm_service.ZhipuAI')
    def test_init_with_env_api_key(self, mock_zhipuai):
        """测试从环境变量获取API密钥"""
        from app.services.ai_planning.glm_service import GLMService
        
        service = GLMService()
        
        self.assertEqual(service.api_key, "env-api-key")
        mock_zhipuai.assert_called_once_with(api_key="env-api-key")
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('app.services.ai_planning.glm_service.logger')
    def test_init_without_api_key(self, mock_logger):
        """测试没有API密钥时的初始化"""
        from app.services.ai_planning.glm_service import GLMService
        
        service = GLMService()
        
        self.assertIsNone(service.client)
        mock_logger.warning.assert_called_once()
    
    @patch('app.services.ai_planning.glm_service.ZhipuAI', None)
    @patch('app.services.ai_planning.glm_service.logger')
    def test_init_without_zhipuai_package(self, mock_logger):
        """测试zhipuai包未安装时的初始化"""
        from app.services.ai_planning.glm_service import GLMService
        
        service = GLMService(api_key="test-key")
        
        self.assertIsNone(service.client)
        mock_logger.error.assert_called_once()
    
    @patch('app.services.ai_planning.glm_service.ZhipuAI')
    def test_init_sets_default_parameters(self, mock_zhipuai):
        """测试初始化设置默认参数"""
        from app.services.ai_planning.glm_service import GLMService
        
        service = GLMService(api_key="test-key")
        
        self.assertEqual(service.model, "glm-4")
        self.assertEqual(service.max_retries, 3)
        self.assertEqual(service.timeout, 30)


class TestGLMServiceAvailability(unittest.TestCase):
    """测试服务可用性检查"""
    
    @patch('app.services.ai_planning.glm_service.ZhipuAI')
    def test_is_available_true(self, mock_zhipuai):
        """测试服务可用"""
        from app.services.ai_planning.glm_service import GLMService
        
        service = GLMService(api_key="test-key")
        
        self.assertTrue(service.is_available())
    
    @patch.dict(os.environ, {}, clear=True)
    def test_is_available_false(self):
        """测试服务不可用"""
        from app.services.ai_planning.glm_service import GLMService
        
        service = GLMService()
        
        self.assertFalse(service.is_available())


class TestGLMServiceChat(unittest.TestCase):
    """测试 chat 方法"""
    
    def setUp(self):
        """测试前准备"""
        self.patcher = patch('app.services.ai_planning.glm_service.ZhipuAI')
        self.mock_zhipuai = self.patcher.start()
        
    def tearDown(self):
        """测试后清理"""
        self.patcher.stop()
    
    def test_chat_success(self):
        """测试成功对话"""
        from app.services.ai_planning.glm_service import GLMService
        
        # Mock响应
        mock_choice = MagicMock()
        mock_choice.message.content = "AI响应内容"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        self.mock_zhipuai.return_value = mock_client
        
        service = GLMService(api_key="test-key")
        messages = [{"role": "user", "content": "测试消息"}]
        
        result = service.chat(messages)
        
        self.assertEqual(result, "AI响应内容")
        mock_client.chat.completions.create.assert_called_once()
    
    def test_chat_with_custom_parameters(self):
        """测试使用自定义参数对话"""
        from app.services.ai_planning.glm_service import GLMService
        
        mock_choice = MagicMock()
        mock_choice.message.content = "响应"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        self.mock_zhipuai.return_value = mock_client
        
        service = GLMService(api_key="test-key")
        messages = [{"role": "user", "content": "测试"}]
        
        result = service.chat(messages, temperature=0.5, max_tokens=1000)
        
        self.assertEqual(result, "响应")
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_kwargs['temperature'], 0.5)
        self.assertEqual(call_kwargs['max_tokens'], 1000)
    
    def test_chat_empty_response(self):
        """测试空响应"""
        from app.services.ai_planning.glm_service import GLMService
        
        mock_response = MagicMock()
        mock_response.choices = []
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        self.mock_zhipuai.return_value = mock_client
        
        service = GLMService(api_key="test-key")
        messages = [{"role": "user", "content": "测试"}]
        
        result = service.chat(messages)
        
        self.assertIsNone(result)
    
    @patch('app.services.ai_planning.glm_service.time.sleep')
    def test_chat_retry_on_exception(self, mock_sleep):
        """测试异常时重试"""
        from app.services.ai_planning.glm_service import GLMService
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API错误")
        self.mock_zhipuai.return_value = mock_client
        
        service = GLMService(api_key="test-key")
        messages = [{"role": "user", "content": "测试"}]
        
        result = service.chat(messages)
        
        self.assertIsNone(result)
        self.assertEqual(mock_client.chat.completions.create.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)  # 指数退避
    
    @patch('app.services.ai_planning.glm_service.time.sleep')
    def test_chat_success_after_retry(self, mock_sleep):
        """测试重试后成功"""
        from app.services.ai_planning.glm_service import GLMService
        
        mock_choice = MagicMock()
        mock_choice.message.content = "成功响应"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        mock_client = MagicMock()
        # 第一次失败，第二次成功
        mock_client.chat.completions.create.side_effect = [
            Exception("临时错误"),
            mock_response
        ]
        self.mock_zhipuai.return_value = mock_client
        
        service = GLMService(api_key="test-key")
        messages = [{"role": "user", "content": "测试"}]
        
        result = service.chat(messages)
        
        self.assertEqual(result, "成功响应")
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)
    
    def test_chat_service_unavailable(self):
        """测试服务不可用时对话"""
        from app.services.ai_planning.glm_service import GLMService
        
        service = GLMService()  # 无API密钥
        messages = [{"role": "user", "content": "测试"}]
        
        result = service.chat(messages)
        
        self.assertIsNone(result)


class TestGLMServiceGenerateProjectPlan(unittest.TestCase):
    """测试项目计划生成"""
    
    def setUp(self):
        """测试前准备"""
        self.patcher = patch('app.services.ai_planning.glm_service.ZhipuAI')
        self.mock_zhipuai = self.patcher.start()
        
    def tearDown(self):
        """测试后清理"""
        self.patcher.stop()
    
    def _setup_mock_response(self, content):
        """设置模拟响应"""
        mock_choice = MagicMock()
        mock_choice.message.content = content
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        self.mock_zhipuai.return_value = mock_client
        
        return mock_client
    
    def test_generate_project_plan_success(self):
        """测试成功生成项目计划"""
        from app.services.ai_planning.glm_service import GLMService
        
        plan_json = json.dumps({
            "project_name": "测试项目",
            "estimated_duration_days": 30,
            "phases": []
        })
        self._setup_mock_response(plan_json)
        
        service = GLMService(api_key="test-key")
        result = service.generate_project_plan(
            "测试项目", "软件开发", "需求描述"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result["project_name"], "测试项目")
        self.assertEqual(result["estimated_duration_days"], 30)
    
    def test_generate_project_plan_with_optional_params(self):
        """测试带可选参数生成计划"""
        from app.services.ai_planning.glm_service import GLMService
        
        plan_json = json.dumps({"project_name": "项目"})
        self._setup_mock_response(plan_json)
        
        service = GLMService(api_key="test-key")
        reference_projects = [{"name": "参考项目", "duration_days": 20}]
        
        result = service.generate_project_plan(
            "测试项目", "开发", "需求",
            industry="金融",
            complexity="高",
            reference_projects=reference_projects
        )
        
        self.assertIsNotNone(result)
    
    def test_generate_project_plan_json_in_text(self):
        """测试从文本中提取JSON"""
        from app.services.ai_planning.glm_service import GLMService
        
        response_text = """这是一些说明文字
        {
            "project_name": "提取的项目",
            "estimated_duration_days": 45
        }
        更多说明"""
        self._setup_mock_response(response_text)
        
        service = GLMService(api_key="test-key")
        result = service.generate_project_plan("项目", "类型", "需求")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["project_name"], "提取的项目")
    
    def test_generate_project_plan_no_json(self):
        """测试无法提取JSON时返回原始文本"""
        from app.services.ai_planning.glm_service import GLMService
        
        response_text = "这是纯文本响应，没有JSON"
        self._setup_mock_response(response_text)
        
        service = GLMService(api_key="test-key")
        result = service.generate_project_plan("项目", "类型", "需求")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["raw_response"], response_text)
    
    def test_generate_project_plan_invalid_json(self):
        """测试解析无效JSON"""
        from app.services.ai_planning.glm_service import GLMService
        
        response_text = "{invalid json}"
        self._setup_mock_response(response_text)
        
        service = GLMService(api_key="test-key")
        result = service.generate_project_plan("项目", "类型", "需求")
        
        self.assertIsNone(result)
    
    def test_generate_project_plan_api_failure(self):
        """测试API调用失败"""
        from app.services.ai_planning.glm_service import GLMService
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API错误")
        self.mock_zhipuai.return_value = mock_client
        
        service = GLMService(api_key="test-key")
        result = service.generate_project_plan("项目", "类型", "需求")
        
        self.assertIsNone(result)


class TestGLMServiceDecomposeWBS(unittest.TestCase):
    """测试WBS任务分解"""
    
    def setUp(self):
        """测试前准备"""
        self.patcher = patch('app.services.ai_planning.glm_service.ZhipuAI')
        self.mock_zhipuai = self.patcher.start()
        
    def tearDown(self):
        """测试后清理"""
        self.patcher.stop()
    
    def _setup_mock_response(self, content):
        """设置模拟响应"""
        mock_choice = MagicMock()
        mock_choice.message.content = content
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        self.mock_zhipuai.return_value = mock_client
        
        return mock_client
    
    def test_decompose_wbs_success(self):
        """测试成功分解WBS"""
        from app.services.ai_planning.glm_service import GLMService
        
        tasks_json = json.dumps([
            {"task_name": "子任务1", "estimated_duration_days": 3},
            {"task_name": "子任务2", "estimated_duration_days": 5}
        ])
        self._setup_mock_response(tasks_json)
        
        service = GLMService(api_key="test-key")
        result = service.decompose_wbs(
            "主任务", "任务描述", "开发"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["task_name"], "子任务1")
    
    def test_decompose_wbs_with_optional_params(self):
        """测试带可选参数分解WBS"""
        from app.services.ai_planning.glm_service import GLMService
        
        tasks_json = json.dumps([{"task_name": "任务"}])
        self._setup_mock_response(tasks_json)
        
        service = GLMService(api_key="test-key")
        reference_tasks = [{"name": "参考任务", "effort_hours": 16}]
        
        result = service.decompose_wbs(
            "主任务", "描述", "开发",
            estimated_duration=10,
            reference_tasks=reference_tasks
        )
        
        self.assertIsNotNone(result)
    
    def test_decompose_wbs_array_in_text(self):
        """测试从文本中提取JSON数组"""
        from app.services.ai_planning.glm_service import GLMService
        
        response_text = """任务分解如下：
        [
            {"task_name": "提取的任务", "estimated_duration_days": 2}
        ]
        以上是分解结果"""
        self._setup_mock_response(response_text)
        
        service = GLMService(api_key="test-key")
        result = service.decompose_wbs("任务", "描述", "类型")
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["task_name"], "提取的任务")
    
    def test_decompose_wbs_no_array(self):
        """测试无法提取数组时返回空列表"""
        from app.services.ai_planning.glm_service import GLMService
        
        response_text = "没有JSON数组的纯文本"
        self._setup_mock_response(response_text)
        
        service = GLMService(api_key="test-key")
        result = service.decompose_wbs("任务", "描述", "类型")
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 0)
    
    def test_decompose_wbs_invalid_json(self):
        """测试解析无效JSON数组"""
        from app.services.ai_planning.glm_service import GLMService
        
        # 使用能匹配正则但JSON无效的字符串
        response_text = "[{invalid}]"
        self._setup_mock_response(response_text)
        
        service = GLMService(api_key="test-key")
        result = service.decompose_wbs("任务", "描述", "类型")
        
        self.assertIsNone(result)
    
    def test_decompose_wbs_api_failure(self):
        """测试API调用失败"""
        from app.services.ai_planning.glm_service import GLMService
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API错误")
        self.mock_zhipuai.return_value = mock_client
        
        service = GLMService(api_key="test-key")
        result = service.decompose_wbs("任务", "描述", "类型")
        
        self.assertIsNone(result)


class TestGLMServiceRecommendResources(unittest.TestCase):
    """测试资源推荐"""
    
    def setUp(self):
        """测试前准备"""
        self.patcher = patch('app.services.ai_planning.glm_service.ZhipuAI')
        self.mock_zhipuai = self.patcher.start()
        
    def tearDown(self):
        """测试后清理"""
        self.patcher.stop()
    
    def _setup_mock_response(self, content):
        """设置模拟响应"""
        mock_choice = MagicMock()
        mock_choice.message.content = content
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        self.mock_zhipuai.return_value = mock_client
        
        return mock_client
    
    def test_recommend_resources_success(self):
        """测试成功推荐资源"""
        from app.services.ai_planning.glm_service import GLMService
        
        recommendations_json = json.dumps([
            {"user_id": 1, "match_score": 95, "allocation_type": "PRIMARY"},
            {"user_id": 2, "match_score": 85, "allocation_type": "SECONDARY"}
        ])
        self._setup_mock_response(recommendations_json)
        
        service = GLMService(api_key="test-key")
        task_info = {
            "name": "开发任务",
            "type": "coding",
            "effort_hours": 20,
            "required_skills": [{"skill": "Python"}]
        }
        available_users = [
            {"name": "张三", "role": "开发", "skills": ["Python"], "workload": 50}
        ]
        
        result = service.recommend_resources(task_info, available_users)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["user_id"], 1)
        self.assertEqual(result[0]["match_score"], 95)
    
    def test_recommend_resources_with_constraints(self):
        """测试带约束条件推荐资源"""
        from app.services.ai_planning.glm_service import GLMService
        
        recommendations_json = json.dumps([{"user_id": 1, "match_score": 90}])
        self._setup_mock_response(recommendations_json)
        
        service = GLMService(api_key="test-key")
        task_info = {"name": "任务", "type": "开发", "required_skills": []}
        available_users = [{"name": "李四", "skills": []}]
        constraints = {"max_workload": 80, "preferred_team": "A组"}
        
        result = service.recommend_resources(task_info, available_users, constraints)
        
        self.assertIsNotNone(result)
    
    def test_recommend_resources_array_in_text(self):
        """测试从文本中提取推荐数组"""
        from app.services.ai_planning.glm_service import GLMService
        
        response_text = """推荐结果：
        [
            {"user_id": 3, "match_score": 92, "allocation_type": "PRIMARY"}
        ]
        以上是推荐人员"""
        self._setup_mock_response(response_text)
        
        service = GLMService(api_key="test-key")
        task_info = {"name": "任务", "required_skills": []}
        available_users = [{"name": "王五"}]
        
        result = service.recommend_resources(task_info, available_users)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["user_id"], 3)
    
    def test_recommend_resources_no_array(self):
        """测试无法提取数组时返回空列表"""
        from app.services.ai_planning.glm_service import GLMService
        
        response_text = "无法推荐合适人员"
        self._setup_mock_response(response_text)
        
        service = GLMService(api_key="test-key")
        task_info = {"name": "任务", "required_skills": []}
        available_users = []
        
        result = service.recommend_resources(task_info, available_users)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 0)
    
    def test_recommend_resources_invalid_json(self):
        """测试解析无效JSON"""
        from app.services.ai_planning.glm_service import GLMService
        
        response_text = "[{invalid}]"
        self._setup_mock_response(response_text)
        
        service = GLMService(api_key="test-key")
        task_info = {"name": "任务", "required_skills": []}
        available_users = []
        
        result = service.recommend_resources(task_info, available_users)
        
        self.assertIsNone(result)
    
    def test_recommend_resources_api_failure(self):
        """测试API调用失败"""
        from app.services.ai_planning.glm_service import GLMService
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API错误")
        self.mock_zhipuai.return_value = mock_client
        
        service = GLMService(api_key="test-key")
        task_info = {"name": "任务", "required_skills": []}
        available_users = []
        
        result = service.recommend_resources(task_info, available_users)
        
        self.assertIsNone(result)


class TestGLMServicePromptBuilders(unittest.TestCase):
    """测试提示词构建方法"""
    
    @patch('app.services.ai_planning.glm_service.ZhipuAI')
    def setUp(self, mock_zhipuai):
        """测试前准备"""
        from app.services.ai_planning.glm_service import GLMService
        self.service = GLMService(api_key="test-key")
    
    def test_build_plan_generation_prompt_basic(self):
        """测试基本计划生成提示词"""
        prompt = self.service._build_plan_generation_prompt(
            "测试项目", "软件开发", "需求描述", None, None, None
        )
        
        self.assertIn("测试项目", prompt)
        self.assertIn("软件开发", prompt)
        self.assertIn("需求描述", prompt)
        self.assertIn("通用", prompt)  # 默认行业
        self.assertIn("中等", prompt)  # 默认复杂度
    
    def test_build_plan_generation_prompt_with_references(self):
        """测试带参考项目的提示词"""
        reference_projects = [
            {"name": "参考1", "type": "开发", "duration_days": 30},
            {"name": "参考2", "type": "测试", "duration_days": 15}
        ]
        
        prompt = self.service._build_plan_generation_prompt(
            "项目", "类型", "需求", "金融", "高", reference_projects
        )
        
        self.assertIn("参考1", prompt)
        self.assertIn("金融", prompt)
        self.assertIn("高", prompt)
    
    def test_build_wbs_decomposition_prompt_basic(self):
        """测试基本WBS分解提示词"""
        prompt = self.service._build_wbs_decomposition_prompt(
            "任务名", "任务描述", "开发", None, None
        )
        
        self.assertIn("任务名", prompt)
        self.assertIn("任务描述", prompt)
        self.assertIn("开发", prompt)
        self.assertIn("待估算", prompt)
    
    def test_build_wbs_decomposition_prompt_with_references(self):
        """测试带参考任务的WBS提示词"""
        reference_tasks = [
            {"name": "参考任务1", "effort_hours": 16},
            {"name": "参考任务2", "effort_hours": 24}
        ]
        
        prompt = self.service._build_wbs_decomposition_prompt(
            "任务", "描述", "类型", 10, reference_tasks
        )
        
        self.assertIn("参考任务1", prompt)
        self.assertIn("10", prompt)
    
    def test_build_resource_recommendation_prompt_basic(self):
        """测试基本资源推荐提示词"""
        task_info = {
            "name": "开发任务",
            "type": "coding",
            "effort_hours": 20,
            "required_skills": [{"skill": "Python"}, {"skill": "Django"}]
        }
        available_users = [
            {"name": "张三", "role": "开发", "skills": ["Python", "Java"], "workload": 50},
            {"name": "李四", "role": "测试", "skills": ["Selenium"], "workload": 30}
        ]
        
        prompt = self.service._build_resource_recommendation_prompt(
            task_info, available_users, None
        )
        
        self.assertIn("开发任务", prompt)
        self.assertIn("20", prompt)
        self.assertIn("Python", prompt)
        self.assertIn("张三", prompt)
        self.assertIn("李四", prompt)
    
    def test_build_resource_recommendation_prompt_with_constraints(self):
        """测试带约束的资源推荐提示词"""
        task_info = {"name": "任务", "required_skills": []}
        available_users = [{"name": "用户", "skills": [], "workload": 0}]
        constraints = {"max_workload": 80}
        
        prompt = self.service._build_resource_recommendation_prompt(
            task_info, available_users, constraints
        )
        
        self.assertIn("max_workload", prompt)
        self.assertIn("80", prompt)


if __name__ == '__main__':
    unittest.main()
