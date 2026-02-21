# -*- coding: utf-8 -*-
"""
WBS分解器单元测试

目标：
1. 只mock外部依赖（db.query, db.add, db.commit, glm_service等）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import MagicMock, Mock, patch, call
from datetime import datetime
import json
import asyncio

from app.services.ai_planning.wbs_decomposer import AIWbsDecomposer


class TestAIWbsDecomposer(unittest.TestCase):
    """测试WBS分解器核心功能"""

    def setUp(self):
        """测试前准备"""
        # Mock数据库会话
        self.mock_db = MagicMock()
        
        # Mock GLM服务
        self.mock_glm = MagicMock()
        self.mock_glm.is_available.return_value = True
        self.mock_glm.model = "glm-4"
        
        # 创建分解器实例
        self.decomposer = AIWbsDecomposer(
            db=self.mock_db,
            glm_service=self.mock_glm
        )

    # ========== __init__() 初始化测试 ==========
    
    def test_init_with_glm_service(self):
        """测试使用自定义GLM服务初始化"""
        decomposer = AIWbsDecomposer(
            db=self.mock_db,
            glm_service=self.mock_glm
        )
        self.assertEqual(decomposer.db, self.mock_db)
        self.assertEqual(decomposer.glm_service, self.mock_glm)

    def test_init_without_glm_service(self):
        """测试不提供GLM服务时自动创建"""
        with patch('app.services.ai_planning.wbs_decomposer.GLMService') as MockGLM:
            mock_instance = MagicMock()
            MockGLM.return_value = mock_instance
            
            decomposer = AIWbsDecomposer(db=self.mock_db)
            
            MockGLM.assert_called_once()
            self.assertEqual(decomposer.glm_service, mock_instance)

    # ========== _generate_level_1_tasks() 测试 ==========
    
    def test_generate_level_1_tasks_with_template(self):
        """测试使用模板生成一级任务"""
        # Mock项目
        mock_project = MagicMock()
        mock_project.id = 100
        
        # Mock模板
        mock_template = MagicMock()
        mock_template.id = 10
        mock_template.ai_model_version = "glm-4"
        mock_template.phases = json.dumps([
            {"name": "需求阶段", "duration_days": 10, "deliverables": ["需求文档"]},
            {"name": "开发阶段", "duration_days": 30, "deliverables": ["代码"]},
        ])
        
        # 执行
        tasks = self.decomposer._generate_level_1_tasks(mock_project, mock_template)
        
        # 验证
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].task_name, "需求阶段")
        self.assertEqual(tasks[0].estimated_duration_days, 10)
        self.assertEqual(tasks[0].wbs_level, 1)
        self.assertEqual(tasks[0].wbs_code, "1")
        self.assertEqual(tasks[0].project_id, 100)
        self.assertEqual(tasks[0].template_id, 10)
        self.assertEqual(tasks[0].confidence_score, 90.0)
        
        self.assertEqual(tasks[1].task_name, "开发阶段")
        self.assertEqual(tasks[1].wbs_code, "2")
        self.assertEqual(tasks[1].sequence, 2)

    def test_generate_level_1_tasks_without_template(self):
        """测试无模板时使用默认阶段"""
        mock_project = MagicMock()
        mock_project.id = 200
        
        tasks = self.decomposer._generate_level_1_tasks(mock_project, None)
        
        # 验证默认生成4个阶段
        self.assertEqual(len(tasks), 4)
        
        # 验证阶段名称
        phase_names = [t.task_name for t in tasks]
        self.assertIn("需求分析", phase_names)
        self.assertIn("设计阶段", phase_names)
        self.assertIn("开发实施", phase_names)
        self.assertIn("测试验收", phase_names)
        
        # 验证基本属性
        self.assertEqual(tasks[0].project_id, 200)
        self.assertEqual(tasks[0].confidence_score, 75.0)
        self.assertEqual(tasks[0].task_type, "PHASE")
        self.assertIsNone(tasks[0].template_id)

    def test_generate_level_1_tasks_deliverables_format(self):
        """测试交付物格式正确"""
        mock_project = MagicMock()
        mock_project.id = 300
        
        mock_template = MagicMock()
        mock_template.phases = json.dumps([
            {"name": "阶段A", "duration_days": 5, "deliverables": ["文档A", "文档B"]},
        ])
        
        tasks = self.decomposer._generate_level_1_tasks(mock_project, mock_template)
        
        # 验证deliverables是JSON格式
        deliverables = json.loads(tasks[0].deliverables)
        self.assertEqual(deliverables, ["文档A", "文档B"])

    # ========== _find_reference_tasks() 测试 ==========
    
    def test_find_reference_tasks(self):
        """测试查找参考任务"""
        # Mock查询链
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_limit = MagicMock()
        
        mock_task1 = MagicMock()
        mock_task1.id = 1
        mock_task1.title = "需求分析"
        
        mock_task2 = MagicMock()
        mock_task2.id = 2
        mock_task2.title = "需求设计"
        
        mock_limit.all.return_value = [mock_task1, mock_task2]
        mock_filter.limit.return_value = mock_limit
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query
        
        # 执行
        result = self.decomposer._find_reference_tasks(
            task_name="需求分析",
            task_type="ANALYSIS",
            project_type="SOFTWARE"
        )
        
        # 验证
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[1].id, 2)

    def test_find_reference_tasks_with_limit(self):
        """测试限制返回数量"""
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_limit = MagicMock()
        
        mock_limit.all.return_value = []
        mock_filter.limit.return_value = mock_limit
        mock_query.filter.return_value = mock_filter
        self.mock_db.query.return_value = mock_query
        
        self.decomposer._find_reference_tasks(
            task_name="测试",
            task_type="TEST",
            project_type="SOFTWARE",
            limit=3
        )
        
        # 验证调用了limit
        mock_filter.limit.assert_called_once_with(3)

    # ========== _task_to_dict() 测试 ==========
    
    def test_task_to_dict(self):
        """测试任务对象转字典"""
        mock_task = MagicMock()
        mock_task.id = 123
        mock_task.title = "编码任务"
        mock_task.task_type = "DEVELOPMENT"
        mock_task.actual_hours = 40.5
        
        result = self.decomposer._task_to_dict(mock_task)
        
        self.assertEqual(result['id'], 123)
        self.assertEqual(result['name'], "编码任务")
        self.assertEqual(result['type'], "DEVELOPMENT")
        self.assertEqual(result['effort_hours'], 40.5)

    def test_task_to_dict_with_none_hours(self):
        """测试无工时的任务"""
        mock_task = MagicMock()
        mock_task.id = 456
        mock_task.title = "设计任务"
        mock_task.task_type = "DESIGN"
        mock_task.actual_hours = None
        
        result = self.decomposer._task_to_dict(mock_task)
        
        self.assertIsNone(result['effort_hours'])

    # ========== _generate_fallback_subtasks() 测试 ==========
    
    def test_generate_fallback_subtasks_requirement(self):
        """测试需求类任务的备用分解"""
        mock_parent = MagicMock()
        mock_parent.task_name = "需求分析阶段"
        mock_parent.task_type = "ANALYSIS"
        
        result = self.decomposer._generate_fallback_subtasks(mock_parent)
        
        # 验证返回3个子任务
        self.assertEqual(len(result), 3)
        
        task_names = [t['task_name'] for t in result]
        self.assertIn("需求调研", task_names)
        self.assertIn("需求分析", task_names)
        self.assertIn("需求评审", task_names)
        
        # 验证字段完整性
        self.assertIn('task_description', result[0])
        self.assertIn('estimated_duration_days', result[0])
        self.assertIn('complexity', result[0])

    def test_generate_fallback_subtasks_design(self):
        """测试设计类任务的备用分解"""
        mock_parent = MagicMock()
        mock_parent.task_name = "系统设计"
        mock_parent.task_type = "DESIGN"
        
        result = self.decomposer._generate_fallback_subtasks(mock_parent)
        
        self.assertEqual(len(result), 3)
        
        task_names = [t['task_name'] for t in result]
        self.assertIn("概要设计", task_names)
        self.assertIn("详细设计", task_names)
        self.assertIn("设计评审", task_names)

    def test_generate_fallback_subtasks_generic(self):
        """测试通用任务的备用分解"""
        mock_parent = MagicMock()
        mock_parent.task_name = "开发功能模块"
        mock_parent.task_type = "DEVELOPMENT"
        mock_parent.estimated_duration_days = 10
        
        result = self.decomposer._generate_fallback_subtasks(mock_parent)
        
        # 验证通用3阶段：准备-执行-验收
        self.assertEqual(len(result), 3)
        
        # 验证名称格式
        self.assertTrue(result[0]['task_name'].endswith("准备"))
        self.assertTrue(result[1]['task_name'].endswith("执行"))
        self.assertTrue(result[2]['task_name'].endswith("验收"))
        
        # 验证工期分配（20%-60%-20%）
        self.assertEqual(result[0]['estimated_duration_days'], 2)
        self.assertEqual(result[1]['estimated_duration_days'], 6)
        self.assertEqual(result[2]['estimated_duration_days'], 2)

    def test_generate_fallback_subtasks_case_insensitive(self):
        """测试关键词匹配不区分大小写"""
        mock_parent = MagicMock()
        mock_parent.task_name = "REQUIREMENT Analysis"
        mock_parent.task_type = "ANALYSIS"
        
        result = self.decomposer._generate_fallback_subtasks(mock_parent)
        
        # 应该识别为需求任务
        task_names = [t['task_name'] for t in result]
        self.assertIn("需求调研", task_names)

    # ========== _create_suggestion_from_data() 测试 ==========
    
    def test_create_suggestion_from_data(self):
        """测试从数据创建建议对象"""
        mock_project = MagicMock()
        mock_project.id = 999
        
        mock_parent = MagicMock()
        mock_parent.id = 10
        mock_parent.wbs_code = "1.2"
        mock_parent.template_id = 5
        
        data = {
            'task_name': "子任务A",
            'task_description': "描述A",
            'task_type': "CODING",
            'estimated_duration_days': 5,
            'estimated_effort_hours': 40,
            'complexity': "HIGH",
            'dependencies': [{"task_id": 9, "type": "FS"}],
            'required_skills': [{"skill": "Python", "level": "Senior"}],
            'deliverables': [{"name": "代码", "type": "CODE"}],
            'risk_level': "HIGH",
        }
        
        self.mock_glm.is_available.return_value = True
        self.mock_glm.model = "glm-4"
        
        result = self.decomposer._create_suggestion_from_data(
            data=data,
            project=mock_project,
            parent_task=mock_parent,
            level=3,
            sequence=2
        )
        
        # 验证基本属性
        self.assertEqual(result.project_id, 999)
        self.assertEqual(result.template_id, 5)
        self.assertEqual(result.wbs_level, 3)
        self.assertEqual(result.parent_wbs_id, 10)
        self.assertEqual(result.wbs_code, "1.2.2")
        self.assertEqual(result.sequence, 2)
        self.assertEqual(result.task_name, "子任务A")
        self.assertEqual(result.task_type, "CODING")
        self.assertEqual(result.complexity, "HIGH")
        self.assertEqual(result.ai_model_version, "glm-4")

    def test_create_suggestion_from_data_with_defaults(self):
        """测试使用默认值创建建议"""
        mock_project = MagicMock()
        mock_project.id = 888
        
        mock_parent = MagicMock()
        mock_parent.id = 20
        mock_parent.wbs_code = "2"
        mock_parent.template_id = None
        
        # 最小数据集
        data = {
            'task_name': "简单任务",
        }
        
        self.mock_glm.is_available.return_value = False
        
        result = self.decomposer._create_suggestion_from_data(
            data=data,
            project=mock_project,
            parent_task=mock_parent,
            level=2,
            sequence=1
        )
        
        # 验证默认值
        self.assertEqual(result.task_name, "简单任务")
        self.assertIsNone(result.task_description)
        self.assertEqual(result.task_type, "GENERAL")
        self.assertEqual(result.complexity, "MEDIUM")
        self.assertEqual(result.ai_model_version, "RULE_ENGINE")

    # ========== _identify_dependencies() 测试 ==========
    
    def test_identify_dependencies(self):
        """测试识别依赖关系"""
        # 创建模拟任务列表
        task1 = MagicMock()
        task1.id = 1
        task1.wbs_level = 1
        task1.parent_wbs_id = None
        task1.sequence = 1
        
        task2 = MagicMock()
        task2.id = 2
        task2.wbs_level = 1
        task2.parent_wbs_id = None
        task2.sequence = 2
        
        task3 = MagicMock()
        task3.id = 3
        task3.wbs_level = 2
        task3.parent_wbs_id = 1
        task3.sequence = 1
        
        task4 = MagicMock()
        task4.id = 4
        task4.wbs_level = 2
        task4.parent_wbs_id = 1
        task4.sequence = 2
        
        suggestions = [task1, task2, task3, task4]
        
        # 执行
        self.decomposer._identify_dependencies(suggestions)
        
        # 验证：同层级且同父任务的任务设置了FS依赖
        # task2应该依赖task1（同层级、同父任务None）
        self.assertEqual(task2.dependencies, json.dumps([{"task_id": 1, "type": "FS"}]))
        self.assertEqual(task2.dependency_type, "FS")
        
        # task4应该依赖task3（同层级、同父任务1）
        self.assertEqual(task4.dependencies, json.dumps([{"task_id": 3, "type": "FS"}]))

    def test_identify_dependencies_different_parents(self):
        """测试不同父任务的子任务不设置依赖"""
        task1 = MagicMock()
        task1.id = 1
        task1.wbs_level = 2
        task1.parent_wbs_id = 10
        task1.sequence = 1
        task1.dependencies = None  # 初始化
        
        task2 = MagicMock()
        task2.id = 2
        task2.wbs_level = 2
        task2.parent_wbs_id = 20  # 不同父任务
        task2.sequence = 1
        task2.dependencies = None  # 初始化
        
        suggestions = [task1, task2]
        
        self.decomposer._identify_dependencies(suggestions)
        
        # task1和task2都不应该设置依赖（父任务不同）
        # 由于它们父任务不同，不在同一序列中
        # task1没有前置任务（sequence=1）
        self.assertIsNone(task1.dependencies)
        # task2也没有前置任务（不同父任务，序列重新开始）
        self.assertIsNone(task2.dependencies)

    def test_identify_dependencies_empty_list(self):
        """测试空任务列表"""
        # 不应该抛出异常
        self.decomposer._identify_dependencies([])

    # ========== _calculate_task_duration() 测试 ==========
    
    def test_calculate_task_duration_leaf_task(self):
        """测试叶子任务的工期计算"""
        task = MagicMock()
        task.id = 1
        task.estimated_duration_days = 10
        
        all_tasks = [task]
        
        result = self.decomposer._calculate_task_duration(task, all_tasks)
        
        self.assertEqual(result, 10)

    def test_calculate_task_duration_with_subtasks(self):
        """测试有子任务时的工期计算"""
        parent = MagicMock()
        parent.id = 1
        parent.estimated_duration_days = 30
        
        child1 = MagicMock()
        child1.id = 2
        child1.parent_wbs_id = 1
        child1.estimated_duration_days = 10
        
        child2 = MagicMock()
        child2.id = 3
        child2.parent_wbs_id = 1
        child2.estimated_duration_days = 15
        
        all_tasks = [parent, child1, child2]
        
        result = self.decomposer._calculate_task_duration(parent, all_tasks)
        
        # 应该返回子任务之和
        self.assertEqual(result, 25)

    def test_calculate_task_duration_none_duration(self):
        """测试工期为None的情况"""
        task = MagicMock()
        task.id = 1
        task.estimated_duration_days = None
        
        result = self.decomposer._calculate_task_duration(task, [task])
        
        self.assertEqual(result, 0)

    # ========== _get_task_chain() 测试 ==========
    
    def test_get_task_chain_single_task(self):
        """测试单个任务的链"""
        task = MagicMock()
        task.id = 1
        
        result = self.decomposer._get_task_chain(task, [task])
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)

    def test_get_task_chain_with_children(self):
        """测试包含子任务的链"""
        parent = MagicMock()
        parent.id = 1
        
        child1 = MagicMock()
        child1.id = 2
        child1.parent_wbs_id = 1
        
        child2 = MagicMock()
        child2.id = 3
        child2.parent_wbs_id = 1
        
        grandchild = MagicMock()
        grandchild.id = 4
        grandchild.parent_wbs_id = 2
        
        all_tasks = [parent, child1, child2, grandchild]
        
        result = self.decomposer._get_task_chain(parent, all_tasks)
        
        # 应该包含所有后代任务
        task_ids = [t.id for t in result]
        self.assertIn(1, task_ids)  # parent
        self.assertIn(2, task_ids)  # child1
        self.assertIn(3, task_ids)  # child2
        self.assertIn(4, task_ids)  # grandchild

    # ========== _calculate_critical_path() 测试 ==========
    
    def test_calculate_critical_path(self):
        """测试计算关键路径"""
        # 创建一级任务
        task1 = MagicMock()
        task1.id = 1
        task1.wbs_level = 1
        task1.estimated_duration_days = 10
        
        task2 = MagicMock()
        task2.id = 2
        task2.wbs_level = 1
        task2.estimated_duration_days = 20
        
        # task2的子任务
        subtask1 = MagicMock()
        subtask1.id = 3
        subtask1.parent_wbs_id = 2
        subtask1.wbs_level = 2
        subtask1.estimated_duration_days = 15
        
        subtask2 = MagicMock()
        subtask2.id = 4
        subtask2.parent_wbs_id = 2
        subtask2.wbs_level = 2
        subtask2.estimated_duration_days = 5
        
        suggestions = [task1, task2, subtask1, subtask2]
        
        # 执行
        self.decomposer._calculate_critical_path(suggestions)
        
        # task2及其子任务应该被标记为关键路径（总工期20天）
        self.assertTrue(task2.is_critical_path)

    # ========== decompose_project() 异步测试 ==========
    
    def test_decompose_project_not_found(self):
        """测试项目不存在的情况"""
        # Mock数据库返回None
        self.mock_db.query.return_value.get.return_value = None
        
        # 运行异步测试
        async def run_test():
            result = await self.decomposer.decompose_project(project_id=999)
            self.assertEqual(result, [])
        
        asyncio.run(run_test())

    def test_decompose_project_basic(self):
        """测试基本项目分解"""
        # Mock项目
        mock_project = MagicMock()
        mock_project.id = 100
        mock_project.project_type = "SOFTWARE"
        
        # Mock数据库查询
        mock_query = MagicMock()
        mock_query.get.return_value = mock_project
        self.mock_db.query.return_value = mock_query
        
        # Mock flush操作 - 为每个任务分配ID
        task_id_counter = [100]  # 使用列表避免闭包问题
        def mock_flush():
            for call_args in self.mock_db.add.call_args_list:
                task = call_args[0][0]
                if not hasattr(task, 'id') or task.id is None:
                    task.id = task_id_counter[0]
                    task_id_counter[0] += 1
        
        self.mock_db.flush.side_effect = mock_flush
        
        async def run_test():
            result = await self.decomposer.decompose_project(
                project_id=100,
                max_level=1  # 只生成1级避免复杂度
            )
            
            # 应该返回默认4个一级任务
            self.assertEqual(len(result), 4)
            
            # 验证调用了db.add
            self.assertEqual(self.mock_db.add.call_count, 4)
            
            # 验证调用了db.flush
            self.assertTrue(self.mock_db.flush.called)
        
        asyncio.run(run_test())

    def test_decompose_project_with_template(self):
        """测试使用模板分解项目"""
        # Mock项目
        mock_project = MagicMock()
        mock_project.id = 200
        
        # Mock模板
        mock_template = MagicMock()
        mock_template.id = 10
        mock_template.phases = json.dumps([
            {"name": "阶段1", "duration_days": 10, "deliverables": []},
        ])
        
        def get_side_effect(entity_id):
            if entity_id == 200:
                return mock_project
            elif entity_id == 10:
                return mock_template
            return None
        
        mock_query = MagicMock()
        mock_query.get.side_effect = get_side_effect
        self.mock_db.query.return_value = mock_query
        
        # Mock flush操作 - 为任务分配ID
        task_id_counter = [200]
        def mock_flush():
            for call_args in self.mock_db.add.call_args_list:
                task = call_args[0][0]
                if not hasattr(task, 'id') or task.id is None:
                    task.id = task_id_counter[0]
                    task_id_counter[0] += 1
        
        self.mock_db.flush.side_effect = mock_flush
        
        async def run_test():
            result = await self.decomposer.decompose_project(
                project_id=200,
                template_id=10,
                max_level=1
            )
            
            # 应该生成1个任务（模板中只有1个阶段）
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].task_name, "阶段1")
        
        asyncio.run(run_test())

    # ========== _decompose_task() 异步测试 ==========
    
    def test_decompose_task_exceeds_max_level(self):
        """测试超过最大层级时不分解"""
        mock_parent = MagicMock()
        mock_project = MagicMock()
        
        async def run_test():
            result = await self.decomposer._decompose_task(
                parent_task=mock_parent,
                project=mock_project,
                level=4,
                max_level=3
            )
            
            # 超过最大层级，返回空列表
            self.assertEqual(result, [])
        
        asyncio.run(run_test())

    def test_decompose_task_with_ai(self):
        """测试使用AI分解任务"""
        mock_parent = MagicMock()
        mock_parent.id = 10
        mock_parent.task_name = "开发模块"
        mock_parent.task_description = "开发核心模块"
        mock_parent.task_type = "DEVELOPMENT"
        mock_parent.estimated_duration_days = 20
        mock_parent.wbs_code = "1"
        mock_parent.template_id = None
        mock_parent.complexity = "MEDIUM"
        
        mock_project = MagicMock()
        mock_project.id = 100
        mock_project.project_type = "SOFTWARE"
        
        # Mock GLM返回的子任务
        ai_subtasks = [
            {
                'task_name': "编码",
                'task_type': "CODING",
                'estimated_duration_days': 15,
                'complexity': 'MEDIUM',
            },
            {
                'task_name': "单元测试",
                'task_type': "TEST",
                'estimated_duration_days': 5,
                'complexity': 'SIMPLE',
            }
        ]
        self.mock_glm.decompose_wbs.return_value = ai_subtasks
        
        # Mock数据库查询（查找参考任务）
        mock_query_result = MagicMock()
        mock_query_result.limit.return_value.all.return_value = []
        self.mock_db.query.return_value.filter.return_value = mock_query_result
        
        async def run_test():
            result = await self.decomposer._decompose_task(
                parent_task=mock_parent,
                project=mock_project,
                level=2,
                max_level=2
            )
            
            # 应该生成2个子任务
            self.assertEqual(len(result), 2)
            
            # 验证调用了AI服务
            self.mock_glm.decompose_wbs.assert_called_once()
            
            # 验证子任务属性
            self.assertEqual(result[0].task_name, "编码")
            self.assertEqual(result[1].task_name, "单元测试")
        
        asyncio.run(run_test())

    def test_decompose_task_fallback_to_rules(self):
        """测试AI失败时使用规则引擎"""
        mock_parent = MagicMock()
        mock_parent.id = 20
        mock_parent.task_name = "需求分析"
        mock_parent.task_description = ""
        mock_parent.task_type = "ANALYSIS"
        mock_parent.estimated_duration_days = 15
        mock_parent.wbs_code = "1"
        mock_parent.template_id = None
        mock_parent.complexity = "MEDIUM"
        
        mock_project = MagicMock()
        mock_project.id = 200
        mock_project.project_type = "SOFTWARE"
        
        # Mock GLM返回空（模拟AI失败）
        self.mock_glm.decompose_wbs.return_value = None
        
        # Mock数据库查询
        mock_query_result = MagicMock()
        mock_query_result.limit.return_value.all.return_value = []
        self.mock_db.query.return_value.filter.return_value = mock_query_result
        
        async def run_test():
            result = await self.decomposer._decompose_task(
                parent_task=mock_parent,
                project=mock_project,
                level=2,
                max_level=2
            )
            
            # 应该使用规则引擎生成3个子任务
            self.assertEqual(len(result), 3)
            
            # 验证是需求类任务的标准分解
            task_names = [t.task_name for t in result]
            self.assertIn("需求调研", task_names)
        
        asyncio.run(run_test())

    def test_decompose_task_recursive(self):
        """测试递归分解复杂任务"""
        mock_parent = MagicMock()
        mock_parent.id = 30
        mock_parent.task_name = "复杂功能"
        mock_parent.task_description = "复杂功能开发"
        mock_parent.task_type = "DEVELOPMENT"
        mock_parent.estimated_duration_days = 30
        mock_parent.wbs_code = "1"
        mock_parent.template_id = None
        
        mock_project = MagicMock()
        mock_project.id = 300
        
        # 第一次AI调用返回1个复杂子任务
        level2_subtasks = [
            {
                'task_name': "核心模块",
                'task_type': "DEVELOPMENT",
                'estimated_duration_days': 20,
                'complexity': 'COMPLEX',  # 复杂任务，会继续分解
            }
        ]
        
        # 第二次AI调用返回简单子任务
        level3_subtasks = [
            {
                'task_name': "具体功能A",
                'task_type': "CODING",
                'estimated_duration_days': 10,
                'complexity': 'SIMPLE',
            }
        ]
        
        # Mock GLM的两次调用
        self.mock_glm.decompose_wbs.side_effect = [level2_subtasks, level3_subtasks]
        
        # Mock数据库
        mock_query_result = MagicMock()
        mock_query_result.limit.return_value.all.return_value = []
        self.mock_db.query.return_value.filter.return_value = mock_query_result
        
        async def run_test():
            result = await self.decomposer._decompose_task(
                parent_task=mock_parent,
                project=mock_project,
                level=2,
                max_level=3
            )
            
            # 应该返回2个任务（1个level2 + 1个level3）
            self.assertEqual(len(result), 2)
            
            # 验证递归调用
            self.assertEqual(self.mock_glm.decompose_wbs.call_count, 2)
        
        asyncio.run(run_test())


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_glm = MagicMock()
        self.decomposer = AIWbsDecomposer(self.mock_db, self.mock_glm)
    
    def test_empty_template_phases(self):
        """测试模板阶段为空的情况"""
        mock_project = MagicMock()
        mock_project.id = 1
        
        mock_template = MagicMock()
        mock_template.phases = json.dumps([])  # 空列表
        
        tasks = self.decomposer._generate_level_1_tasks(mock_project, mock_template)
        
        # 空模板应该返回空任务列表
        self.assertEqual(len(tasks), 0)
    
    def test_invalid_json_in_template(self):
        """测试模板JSON格式错误"""
        mock_project = MagicMock()
        mock_template = MagicMock()
        mock_template.phases = "invalid json"
        
        # 应该抛出JSON解析异常
        with self.assertRaises(json.JSONDecodeError):
            self.decomposer._generate_level_1_tasks(mock_project, mock_template)
    
    def test_wbs_code_format(self):
        """测试WBS编码格式正确性"""
        mock_project = MagicMock()
        mock_project.id = 1
        
        mock_parent = MagicMock()
        mock_parent.id = 10
        mock_parent.wbs_code = "1.2.3"
        mock_parent.template_id = None
        
        data = {'task_name': "测试任务"}
        
        self.mock_glm.is_available.return_value = False
        
        result = self.decomposer._create_suggestion_from_data(
            data, mock_project, mock_parent, level=4, sequence=5
        )
        
        # 验证WBS编码格式: parent.sequence
        self.assertEqual(result.wbs_code, "1.2.3.5")
    
    def test_suggestion_code_uniqueness(self):
        """测试建议代码的唯一性"""
        mock_project = MagicMock()
        mock_project.id = 100
        
        mock_parent = MagicMock()
        mock_parent.id = 10
        mock_parent.wbs_code = "1"
        mock_parent.template_id = None
        
        data = {'task_name': "任务"}
        
        self.mock_glm.is_available.return_value = False
        
        # 生成两个不同序号的建议
        result1 = self.decomposer._create_suggestion_from_data(
            data, mock_project, mock_parent, level=2, sequence=1
        )
        result2 = self.decomposer._create_suggestion_from_data(
            data, mock_project, mock_parent, level=2, sequence=2
        )
        
        # suggestion_code应该不同
        self.assertNotEqual(result1.suggestion_code, result2.suggestion_code)


if __name__ == "__main__":
    unittest.main()
