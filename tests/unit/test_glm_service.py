# -*- coding: utf-8 -*-
"""
GLM服务单元测试

测试策略：
1. 只mock外部依赖（ZhipuAI客户端、环境变量、time.sleep）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率70%+
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import json
import os
from app.services.ai_planning.glm_service import GLMService


class TestGLMServiceInit(unittest.TestCase):
    """测试GLMService初始化"""

    @patch.dict(os.environ, {'GLM_API_KEY': 'test-api-key'})
    @patch('app.services.ai_planning.glm_service.ZhipuAI')
    def test_init_with_env_api_key(self, mock_zhipuai):
        """测试使用环境变量的API key初始化"""
        service = GLMService()
        
        self.assertEqual(service.api_key, 'test-api-key')
        mock_zhipuai.assert_called_once_with(api_key='test-api-key')
        self.assertIsNotNone(service.client)
        self.assertEqual(service.model, 'glm-4')
        self.assertEqual(service.max_retries, 3)
        self.assertEqual(service.timeout, 30)

    @patch('app.services.ai_planning.glm_service.ZhipuAI')
    def test_init_with_explicit_api_key(self, mock_zhipuai):
        """测试使用显式API key初始化"""
        service = GLMService(api_key='explicit-key')
        
        self.assertEqual(service.api_key, 'explicit-key')
        mock_zhipuai.assert_called_once_with(api_key='explicit-key')
        self.assertIsNotNone(service.client)

    @patch.dict(os.environ, {}, clear=True)
    @patch('app.services.ai_planning.glm_service.ZhipuAI')
    def test_init_without_api_key(self, mock_zhipuai):
        """测试无API key初始化（应该警告）"""
        service = GLMService()
        
        self.assertIsNone(service.api_key)
        self.assertIsNone(service.client)
        mock_zhipuai.assert_not_called()

    @patch.dict(os.environ, {'GLM_API_KEY': 'test-key'})
    @patch('app.services.ai_planning.glm_service.ZhipuAI', None)
    def test_init_without_zhipuai_package(self):
        """测试zhipuai包未安装的情况"""
        service = GLMService()
        
        self.assertEqual(service.api_key, 'test-key')
        self.assertIsNone(service.client)


class TestGLMServiceAvailability(unittest.TestCase):
    """测试GLMService可用性检查"""

    @patch('app.services.ai_planning.glm_service.ZhipuAI')
    def test_is_available_with_client(self, mock_zhipuai):
        """测试有客户端时返回True"""
        service = GLMService(api_key='test-key')
        self.assertTrue(service.is_available())

    @patch('app.services.ai_planning.glm_service.ZhipuAI', None)
    def test_is_available_without_client(self):
        """测试无客户端时返回False"""
        service = GLMService()
        self.assertFalse(service.is_available())


class TestGLMServiceChat(unittest.TestCase):
    """测试GLMService对话功能"""

    def setUp(self):
        self.mock_client = MagicMock()
        with patch('app.services.ai_planning.glm_service.ZhipuAI', return_value=self.mock_client):
            self.service = GLMService(api_key='test-key')

    def test_chat_success(self):
        """测试成功的对话"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "AI回复内容"
        
        self.mock_client.chat.completions.create.return_value = mock_response
        
        messages = [{"role": "user", "content": "测试问题"}]
        result = self.service.chat(messages, temperature=0.7, max_tokens=2000)
        
        self.assertEqual(result, "AI回复内容")
        self.mock_client.chat.completions.create.assert_called_once_with(
            model='glm-4',
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )

    def test_chat_with_custom_params(self):
        """测试带自定义参数的对话"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "回复"
        
        self.mock_client.chat.completions.create.return_value = mock_response
        
        messages = [{"role": "user", "content": "测试"}]
        result = self.service.chat(
            messages, 
            temperature=0.5, 
            max_tokens=1000,
            top_p=0.9
        )
        
        self.assertEqual(result, "回复")
        self.mock_client.chat.completions.create.assert_called_once_with(
            model='glm-4',
            messages=messages,
            temperature=0.5,
            max_tokens=1000,
            top_p=0.9
        )

    def test_chat_empty_response(self):
        """测试空响应"""
        mock_response = MagicMock()
        mock_response.choices = []
        
        self.mock_client.chat.completions.create.return_value = mock_response
        
        messages = [{"role": "user", "content": "测试"}]
        result = self.service.chat(messages)
        
        self.assertIsNone(result)

    @patch('time.sleep')
    def test_chat_retry_on_error(self, mock_sleep):
        """测试错误重试机制"""
        self.mock_client.chat.completions.create.side_effect = [
            Exception("网络错误"),
            Exception("超时错误"),
            MagicMock(choices=[MagicMock(message=MagicMock(content="成功"))])
        ]
        
        messages = [{"role": "user", "content": "测试"}]
        result = self.service.chat(messages)
        
        self.assertEqual(result, "成功")
        self.assertEqual(self.mock_client.chat.completions.create.call_count, 3)
        # 检查指数退避
        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_any_call(1)  # 2^0
        mock_sleep.assert_any_call(2)  # 2^1

    @patch('time.sleep')
    def test_chat_max_retries_exceeded(self, mock_sleep):
        """测试超过最大重试次数"""
        self.mock_client.chat.completions.create.side_effect = Exception("持续失败")
        
        messages = [{"role": "user", "content": "测试"}]
        result = self.service.chat(messages)
        
        self.assertIsNone(result)
        self.assertEqual(self.mock_client.chat.completions.create.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    def test_chat_service_unavailable(self):
        """测试服务不可用"""
        service = GLMService()  # 无API key
        
        messages = [{"role": "user", "content": "测试"}]
        result = service.chat(messages)
        
        self.assertIsNone(result)


class TestGLMServiceProjectPlanning(unittest.TestCase):
    """测试项目计划生成功能"""

    def setUp(self):
        self.mock_client = MagicMock()
        with patch('app.services.ai_planning.glm_service.ZhipuAI', return_value=self.mock_client):
            self.service = GLMService(api_key='test-key')

    def test_generate_project_plan_success(self):
        """测试成功生成项目计划"""
        plan_json = {
            "project_name": "测试项目",
            "estimated_duration_days": 30,
            "estimated_effort_hours": 200,
            "phases": [
                {"name": "需求分析", "duration_days": 5}
            ]
        }
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(plan_json)
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result = self.service.generate_project_plan(
            project_name="测试项目",
            project_type="软件开发",
            requirements="需要开发一个项目管理系统",
            industry="IT",
            complexity="中等"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['project_name'], "测试项目")
        self.assertEqual(result['estimated_duration_days'], 30)

    def test_generate_project_plan_with_references(self):
        """测试带参考项目的计划生成"""
        plan_json = {"project_name": "新项目"}
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(plan_json)
        self.mock_client.chat.completions.create.return_value = mock_response
        
        reference_projects = [
            {"name": "参考项目1", "type": "开发", "duration_days": 20},
            {"name": "参考项目2", "type": "测试", "duration_days": 10}
        ]
        
        result = self.service.generate_project_plan(
            project_name="新项目",
            project_type="综合",
            requirements="需求描述",
            reference_projects=reference_projects
        )
        
        self.assertIsNotNone(result)
        # 验证调用参数包含参考项目
        call_args = self.mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        user_message = messages[1]['content']
        self.assertIn("参考项目1", user_message)

    def test_generate_project_plan_parse_error(self):
        """测试解析失败"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "无效的JSON内容"
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result = self.service.generate_project_plan(
            project_name="测试",
            project_type="开发",
            requirements="需求"
        )
        
        # 解析失败应该返回raw_response
        self.assertIsNotNone(result)
        self.assertIn("raw_response", result)

    def test_generate_project_plan_chat_failure(self):
        """测试对话失败"""
        self.mock_client.chat.completions.create.side_effect = Exception("API错误")
        
        result = self.service.generate_project_plan(
            project_name="测试",
            project_type="开发",
            requirements="需求"
        )
        
        self.assertIsNone(result)


class TestGLMServiceWBS(unittest.TestCase):
    """测试WBS分解功能"""

    def setUp(self):
        self.mock_client = MagicMock()
        with patch('app.services.ai_planning.glm_service.ZhipuAI', return_value=self.mock_client):
            self.service = GLMService(api_key='test-key')

    def test_decompose_wbs_success(self):
        """测试成功分解WBS"""
        wbs_json = [
            {
                "task_name": "子任务1",
                "task_type": "开发",
                "estimated_duration_days": 3
            },
            {
                "task_name": "子任务2",
                "task_type": "测试",
                "estimated_duration_days": 2
            }
        ]
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(wbs_json)
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result = self.service.decompose_wbs(
            task_name="开发用户模块",
            task_description="实现用户注册、登录、权限管理",
            task_type="开发",
            estimated_duration=5
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['task_name'], "子任务1")

    def test_decompose_wbs_with_references(self):
        """测试带参考任务的WBS分解"""
        wbs_json = [{"task_name": "新任务"}]
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(wbs_json)
        self.mock_client.chat.completions.create.return_value = mock_response
        
        reference_tasks = [
            {"name": "参考任务1", "effort_hours": 16},
            {"name": "参考任务2", "effort_hours": 24}
        ]
        
        result = self.service.decompose_wbs(
            task_name="主任务",
            task_description="描述",
            task_type="开发",
            reference_tasks=reference_tasks
        )
        
        self.assertIsNotNone(result)
        # 验证参考任务被包含在提示词中
        call_args = self.mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        user_message = messages[1]['content']
        self.assertIn("参考任务1", user_message)

    def test_decompose_wbs_parse_error(self):
        """测试解析失败返回空列表"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "不是JSON数组"
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result = self.service.decompose_wbs(
            task_name="任务",
            task_description="描述",
            task_type="开发"
        )
        
        self.assertEqual(result, [])

    def test_decompose_wbs_chat_failure(self):
        """测试对话失败"""
        self.mock_client.chat.completions.create.side_effect = Exception("错误")
        
        result = self.service.decompose_wbs(
            task_name="任务",
            task_description="描述",
            task_type="开发"
        )
        
        self.assertIsNone(result)


class TestGLMServiceResourceRecommendation(unittest.TestCase):
    """测试资源推荐功能"""

    def setUp(self):
        self.mock_client = MagicMock()
        with patch('app.services.ai_planning.glm_service.ZhipuAI', return_value=self.mock_client):
            self.service = GLMService(api_key='test-key')

    def test_recommend_resources_success(self):
        """测试成功推荐资源"""
        recommendation_json = [
            {
                "user_id": 1,
                "allocation_type": "PRIMARY",
                "match_score": 95
            },
            {
                "user_id": 2,
                "allocation_type": "SECONDARY",
                "match_score": 80
            }
        ]
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(recommendation_json)
        self.mock_client.chat.completions.create.return_value = mock_response
        
        task_info = {
            "name": "开发任务",
            "type": "开发",
            "effort_hours": 40,
            "required_skills": [{"skill": "Python"}]
        }
        
        available_users = [
            {"id": 1, "name": "张三", "role": "开发", "skills": ["Python", "Django"], "workload": 50},
            {"id": 2, "name": "李四", "role": "测试", "skills": ["测试"], "workload": 30}
        ]
        
        result = self.service.recommend_resources(task_info, available_users)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['user_id'], 1)
        self.assertEqual(result[0]['match_score'], 95)

    def test_recommend_resources_with_constraints(self):
        """测试带约束条件的资源推荐"""
        recommendation_json = [{"user_id": 1, "match_score": 90}]
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(recommendation_json)
        self.mock_client.chat.completions.create.return_value = mock_response
        
        task_info = {"name": "任务", "type": "开发", "required_skills": []}
        available_users = [{"id": 1, "name": "用户1"}]
        constraints = {"max_workload": 80, "must_have_skill": "Python"}
        
        result = self.service.recommend_resources(
            task_info,
            available_users,
            constraints
        )
        
        self.assertIsNotNone(result)
        # 验证约束条件被包含
        call_args = self.mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        user_message = messages[1]['content']
        self.assertIn("max_workload", user_message)

    def test_recommend_resources_parse_error(self):
        """测试解析失败"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "无效JSON"
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result = self.service.recommend_resources(
            {"name": "任务"},
            [{"id": 1}]
        )
        
        self.assertEqual(result, [])

    def test_recommend_resources_chat_failure(self):
        """测试对话失败"""
        self.mock_client.chat.completions.create.side_effect = Exception("错误")
        
        result = self.service.recommend_resources(
            {"name": "任务"},
            [{"id": 1}]
        )
        
        self.assertIsNone(result)


class TestGLMServicePromptBuilding(unittest.TestCase):
    """测试提示词构建方法"""

    def setUp(self):
        with patch('app.services.ai_planning.glm_service.ZhipuAI'):
            self.service = GLMService(api_key='test-key')

    def test_build_plan_generation_prompt_basic(self):
        """测试基本项目计划提示词构建"""
        prompt = self.service._build_plan_generation_prompt(
            project_name="测试项目",
            project_type="软件开发",
            requirements="需求描述",
            industry=None,
            complexity=None,
            reference_projects=None
        )
        
        self.assertIn("测试项目", prompt)
        self.assertIn("软件开发", prompt)
        self.assertIn("需求描述", prompt)
        self.assertIn("通用", prompt)  # 默认行业
        self.assertIn("中等", prompt)  # 默认复杂度
        self.assertIn("JSON", prompt)

    def test_build_plan_generation_prompt_with_all_params(self):
        """测试完整参数的提示词构建"""
        reference_projects = [
            {"name": "项目A", "type": "开发", "duration_days": 30},
            {"name": "项目B", "type": "测试", "duration_days": 10}
        ]
        
        prompt = self.service._build_plan_generation_prompt(
            project_name="新项目",
            project_type="综合",
            requirements="详细需求",
            industry="金融",
            complexity="高",
            reference_projects=reference_projects
        )
        
        self.assertIn("新项目", prompt)
        self.assertIn("金融", prompt)
        self.assertIn("高", prompt)
        self.assertIn("参考项目", prompt)
        self.assertIn("项目A", prompt)

    def test_build_plan_generation_prompt_limits_references(self):
        """测试参考项目数量限制（最多3个）"""
        reference_projects = [
            {"name": f"项目{i}"} for i in range(5)
        ]
        
        prompt = self.service._build_plan_generation_prompt(
            project_name="项目",
            project_type="类型",
            requirements="需求",
            industry=None,
            complexity=None,
            reference_projects=reference_projects
        )
        
        # 应该只包含前3个
        self.assertIn("项目0", prompt)
        self.assertIn("项目1", prompt)
        self.assertIn("项目2", prompt)
        self.assertNotIn("项目3", prompt)

    def test_build_wbs_decomposition_prompt_basic(self):
        """测试基本WBS分解提示词"""
        prompt = self.service._build_wbs_decomposition_prompt(
            task_name="开发模块",
            task_description="实现用户管理功能",
            task_type="开发",
            estimated_duration=None,
            reference_tasks=None
        )
        
        self.assertIn("开发模块", prompt)
        self.assertIn("实现用户管理功能", prompt)
        self.assertIn("开发", prompt)
        self.assertIn("待估算", prompt)

    def test_build_wbs_decomposition_prompt_with_references(self):
        """测试带参考任务的WBS提示词"""
        reference_tasks = [
            {"name": "任务1", "effort_hours": 16},
            {"name": "任务2", "effort_hours": 24}
        ]
        
        prompt = self.service._build_wbs_decomposition_prompt(
            task_name="主任务",
            task_description="描述",
            task_type="开发",
            estimated_duration=5,
            reference_tasks=reference_tasks
        )
        
        self.assertIn("5天", prompt)
        self.assertIn("参考任务", prompt)
        self.assertIn("任务1", prompt)

    def test_build_resource_recommendation_prompt_basic(self):
        """测试基本资源推荐提示词"""
        task_info = {
            "name": "开发任务",
            "type": "开发",
            "effort_hours": 40,
            "required_skills": [{"skill": "Python"}]
        }
        
        available_users = [
            {"name": "张三", "role": "开发", "skills": ["Python"], "workload": 50}
        ]
        
        prompt = self.service._build_resource_recommendation_prompt(
            task_info,
            available_users,
            None
        )
        
        self.assertIn("开发任务", prompt)
        self.assertIn("40小时", prompt)
        self.assertIn("Python", prompt)
        self.assertIn("张三", prompt)

    def test_build_resource_recommendation_prompt_limits_users(self):
        """测试用户列表限制（最多10个）"""
        available_users = [
            {"name": f"用户{i}", "skills": []} for i in range(15)
        ]
        
        task_info = {"name": "任务", "required_skills": []}
        
        prompt = self.service._build_resource_recommendation_prompt(
            task_info,
            available_users,
            None
        )
        
        # 应该只包含前10个
        self.assertIn("用户0", prompt)
        self.assertIn("用户9", prompt)
        self.assertNotIn("用户10", prompt)

    def test_build_resource_recommendation_prompt_with_constraints(self):
        """测试带约束的资源推荐提示词"""
        task_info = {"name": "任务", "required_skills": []}
        available_users = [{"name": "用户"}]
        constraints = {"max_workload": 70}
        
        prompt = self.service._build_resource_recommendation_prompt(
            task_info,
            available_users,
            constraints
        )
        
        self.assertIn("约束条件", prompt)


class TestGLMServiceResponseParsing(unittest.TestCase):
    """测试响应解析方法"""

    def setUp(self):
        with patch('app.services.ai_planning.glm_service.ZhipuAI'):
            self.service = GLMService(api_key='test-key')

    def test_parse_plan_response_valid_json(self):
        """测试解析有效的JSON计划"""
        response = '{"project_name": "测试", "phases": []}'
        result = self.service._parse_plan_response(response)
        
        self.assertEqual(result['project_name'], "测试")
        self.assertEqual(result['phases'], [])

    def test_parse_plan_response_json_in_text(self):
        """测试从文本中提取JSON"""
        response = '这是一些前导文本\n{"project_name": "测试", "value": 100}\n后续内容'
        result = self.service._parse_plan_response(response)
        
        self.assertEqual(result['project_name'], "测试")
        self.assertEqual(result['value'], 100)

    def test_parse_plan_response_no_json(self):
        """测试无JSON的响应"""
        response = '这是纯文本响应，没有JSON'
        result = self.service._parse_plan_response(response)
        
        self.assertIn('raw_response', result)
        self.assertEqual(result['raw_response'], response)

    def test_parse_wbs_response_valid_json(self):
        """测试解析有效的WBS JSON数组"""
        response = '[{"task_name": "任务1"}, {"task_name": "任务2"}]'
        result = self.service._parse_wbs_response(response)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['task_name'], "任务1")

    def test_parse_wbs_response_json_in_text(self):
        """测试从文本中提取WBS数组"""
        response = '前导文本\n[{"task_name": "任务"}]\n尾部'
        result = self.service._parse_wbs_response(response)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['task_name'], "任务")

    def test_parse_wbs_response_no_json(self):
        """测试无JSON数组的响应"""
        response = '纯文本响应'
        result = self.service._parse_wbs_response(response)
        
        self.assertEqual(result, [])

    def test_parse_resource_response_valid_json(self):
        """测试解析有效的资源推荐JSON"""
        response = '[{"user_id": 1, "match_score": 95}]'
        result = self.service._parse_resource_response(response)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['user_id'], 1)

    def test_parse_resource_response_no_json(self):
        """测试无JSON的资源推荐响应"""
        response = '无效响应'
        result = self.service._parse_resource_response(response)
        
        self.assertEqual(result, [])

    def test_parse_response_nested_json(self):
        """测试嵌套JSON解析"""
        response = '''
        这是一段说明文字
        {
          "project_name": "复杂项目",
          "phases": [
            {"name": "阶段1", "tasks": ["任务1", "任务2"]},
            {"name": "阶段2", "tasks": []}
          ],
          "nested": {"key": "value"}
        }
        后续内容
        '''
        result = self.service._parse_plan_response(response)
        
        self.assertEqual(result['project_name'], "复杂项目")
        self.assertEqual(len(result['phases']), 2)
        self.assertEqual(result['nested']['key'], "value")


class TestGLMServiceEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        self.mock_client = MagicMock()
        with patch('app.services.ai_planning.glm_service.ZhipuAI', return_value=self.mock_client):
            self.service = GLMService(api_key='test-key')

    def test_chat_with_none_choices(self):
        """测试响应choices为None"""
        mock_response = MagicMock()
        mock_response.choices = None
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result = self.service.chat([{"role": "user", "content": "测试"}])
        self.assertIsNone(result)

    def test_generate_project_plan_minimal_params(self):
        """测试最小参数生成计划"""
        plan_json = {"project_name": "最小项目"}
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(plan_json)
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result = self.service.generate_project_plan(
            project_name="最小项目",
            project_type="类型",
            requirements="需求"
        )
        
        self.assertIsNotNone(result)

    def test_decompose_wbs_empty_task_description(self):
        """测试空任务描述"""
        wbs_json = []
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(wbs_json)
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result = self.service.decompose_wbs(
            task_name="任务",
            task_description="",
            task_type="开发"
        )
        
        # 应该能正常处理
        self.assertIsNotNone(result)

    def test_recommend_resources_empty_users(self):
        """测试空用户列表"""
        recommendation_json = []
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(recommendation_json)
        self.mock_client.chat.completions.create.return_value = mock_response
        
        result = self.service.recommend_resources(
            {"name": "任务"},
            []
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()
