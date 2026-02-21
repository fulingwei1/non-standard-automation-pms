# -*- coding: utf-8 -*-
"""
AI WBS分解器增强测试
覆盖所有核心方法和边界条件
"""

import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.ai_planning.wbs_decomposer import AIWbsDecomposer
from app.models import Project, TaskUnified
from app.models.ai_planning import AIWbsSuggestion, AIProjectPlanTemplate


class TestAIWbsDecomposerInit:
    """测试初始化"""
    
    def test_init_with_glm_service(self):
        """测试使用提供的GLM服务初始化"""
        mock_db = MagicMock(spec=Session)
        mock_glm = MagicMock()
        
        decomposer = AIWbsDecomposer(db=mock_db, glm_service=mock_glm)
        
        assert decomposer.db == mock_db
        assert decomposer.glm_service == mock_glm
    
    @patch('app.services.ai_planning.wbs_decomposer.GLMService')
    def test_init_without_glm_service(self, mock_glm_class):
        """测试不提供GLM服务时自动创建"""
        mock_db = MagicMock(spec=Session)
        mock_glm_instance = MagicMock()
        mock_glm_class.return_value = mock_glm_instance
        
        decomposer = AIWbsDecomposer(db=mock_db)
        
        assert decomposer.db == mock_db
        mock_glm_class.assert_called_once_with()
        assert decomposer.glm_service == mock_glm_instance


class TestGenerateLevel1Tasks:
    """测试一级任务生成"""
    
    def test_generate_from_template(self):
        """测试从模板生成一级任务"""
        mock_db = MagicMock()
        mock_glm = MagicMock()
        decomposer = AIWbsDecomposer(db=mock_db, glm_service=mock_glm)
        
        project = Project(id=1, project_type="SOFTWARE")
        template = AIProjectPlanTemplate(
            id=10,
            ai_model_version="glm-4",
            phases=json.dumps([
                {"name": "启动阶段", "duration_days": 10, "deliverables": ["项目章程"]},
                {"name": "规划阶段", "duration_days": 15, "deliverables": ["项目计划"]}
            ])
        )
        
        tasks = decomposer._generate_level_1_tasks(project, template)
        
        assert len(tasks) == 2
        assert tasks[0].task_name == "启动阶段"
        assert tasks[0].estimated_duration_days == 10
        assert tasks[0].wbs_level == 1
        assert tasks[0].wbs_code == "1"
        assert tasks[0].template_id == 10
        assert tasks[0].confidence_score == 90.0
        
        assert tasks[1].task_name == "规划阶段"
        assert tasks[1].wbs_code == "2"
        assert tasks[1].sequence == 2
    
    def test_generate_without_template(self):
        """测试无模板时使用默认阶段"""
        mock_db = MagicMock()
        decomposer = AIWbsDecomposer(db=mock_db)
        
        project = Project(id=2)
        
        tasks = decomposer._generate_level_1_tasks(project, None)
        
        assert len(tasks) == 4
        assert tasks[0].task_name == "需求分析"
        assert tasks[1].task_name == "设计阶段"
        assert tasks[2].task_name == "开发实施"
        assert tasks[3].task_name == "测试验收"
        assert all(t.confidence_score == 75.0 for t in tasks)
    
    def test_task_properties(self):
        """测试任务属性正确性"""
        mock_db = MagicMock()
        decomposer = AIWbsDecomposer(db=mock_db)
        
        project = Project(id=3)
        tasks = decomposer._generate_level_1_tasks(project, None)
        
        for i, task in enumerate(tasks, 1):
            assert task.project_id == 3
            assert task.wbs_level == 1
            assert task.parent_wbs_id is None
            assert task.sequence == i
            assert task.task_type == "PHASE"
            assert task.complexity == "MEDIUM"
            assert task.status == "SUGGESTED"
            assert task.suggestion_code == f"WBS_3_L1_{i:02d}"


class TestFindReferenceTasks:
    """测试查找参考任务"""
    
    def test_find_reference_tasks(self):
        """测试查找参考任务"""
        mock_db = MagicMock()
        decomposer = AIWbsDecomposer(db=mock_db)
        
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_limit = MagicMock()
        
        mock_tasks = [
            TaskUnified(id=1, title="参考任务1", task_type="DESIGN"),
            TaskUnified(id=2, title="参考任务2", task_type="DESIGN")
        ]
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.limit.return_value = mock_limit
        mock_limit.all.return_value = mock_tasks
        
        result = decomposer._find_reference_tasks("设计", "DESIGN", "SOFTWARE", limit=5)
        
        assert result == mock_tasks
        mock_db.query.assert_called_once_with(TaskUnified)
        mock_limit.all.assert_called_once()
    
    def test_find_reference_tasks_with_custom_limit(self):
        """测试自定义限制数量"""
        mock_db = MagicMock()
        decomposer = AIWbsDecomposer(db=mock_db)
        
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_limit = MagicMock()
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.limit.return_value = mock_limit
        mock_limit.all.return_value = []
        
        decomposer._find_reference_tasks("测试", "TEST", "WEB", limit=10)
        
        mock_filter.limit.assert_called_once_with(10)


class TestTaskToDict:
    """测试任务转字典"""
    
    def test_task_to_dict_with_hours(self):
        """测试带工时的任务转换"""
        decomposer = AIWbsDecomposer(db=MagicMock())
        
        task = TaskUnified(
            id=100,
            title="测试任务",
            task_type="DEVELOP",
            actual_hours=40.5
        )
        
        result = decomposer._task_to_dict(task)
        
        assert result == {
            'id': 100,
            'name': "测试任务",
            'type': "DEVELOP",
            'effort_hours': 40.5
        }
    
    def test_task_to_dict_without_hours(self):
        """测试无工时的任务转换"""
        decomposer = AIWbsDecomposer(db=MagicMock())
        
        task = TaskUnified(
            id=101,
            title="无工时任务",
            task_type="REVIEW",
            actual_hours=None
        )
        
        result = decomposer._task_to_dict(task)
        
        assert result['id'] == 101
        assert result['effort_hours'] is None


class TestGenerateFallbackSubtasks:
    """测试备用子任务生成"""
    
    def test_requirement_task_fallback(self):
        """测试需求类任务的备用分解"""
        decomposer = AIWbsDecomposer(db=MagicMock())
        
        parent_task = AIWbsSuggestion(
            id=1,
            task_name="需求分析阶段",
            task_type="ANALYSIS",
            estimated_duration_days=15
        )
        
        result = decomposer._generate_fallback_subtasks(parent_task)
        
        assert len(result) == 3
        assert result[0]['task_name'] == "需求调研"
        assert result[0]['task_type'] == "ANALYSIS"
        assert result[0]['complexity'] == "MEDIUM"
        
        assert result[1]['task_name'] == "需求分析"
        assert result[1]['risk_level'] == "MEDIUM"
        
        assert result[2]['task_name'] == "需求评审"
        assert result[2]['task_type'] == "REVIEW"
    
    def test_design_task_fallback(self):
        """测试设计类任务的备用分解"""
        decomposer = AIWbsDecomposer(db=MagicMock())
        
        parent_task = AIWbsSuggestion(
            task_name="系统设计",
            task_type="DESIGN"
        )
        
        result = decomposer._generate_fallback_subtasks(parent_task)
        
        assert len(result) == 3
        assert result[0]['task_name'] == "概要设计"
        assert result[0]['complexity'] == "COMPLEX"
        assert result[1]['task_name'] == "详细设计"
        assert result[2]['task_name'] == "设计评审"
    
    def test_generic_task_fallback(self):
        """测试通用任务的备用分解"""
        decomposer = AIWbsDecomposer(db=MagicMock())
        
        parent_task = AIWbsSuggestion(
            task_name="测试任务",
            task_type="TEST",
            estimated_duration_days=10
        )
        
        result = decomposer._generate_fallback_subtasks(parent_task)
        
        assert len(result) == 3
        assert result[0]['task_name'] == "测试任务 - 准备"
        assert result[0]['estimated_duration_days'] == 2  # 10 * 0.2
        assert result[1]['task_name'] == "测试任务 - 执行"
        assert result[1]['estimated_duration_days'] == 6  # 10 * 0.6
        assert result[2]['task_name'] == "测试任务 - 验收"
        assert result[2]['estimated_duration_days'] == 2  # 10 * 0.2
    
    def test_fallback_with_null_duration(self):
        """测试无工期时的备用分解"""
        decomposer = AIWbsDecomposer(db=MagicMock())
        
        parent_task = AIWbsSuggestion(
            task_name="未知工期任务",
            estimated_duration_days=None
        )
        
        result = decomposer._generate_fallback_subtasks(parent_task)
        
        # 使用默认10天
        assert len(result) == 3


class TestCreateSuggestionFromData:
    """测试从数据创建建议"""
    
    def test_create_suggestion_basic(self):
        """测试基本建议创建"""
        mock_db = MagicMock()
        mock_glm = MagicMock()
        mock_glm.is_available.return_value = True
        mock_glm.model = "glm-4-flash"
        
        decomposer = AIWbsDecomposer(db=mock_db, glm_service=mock_glm)
        
        project = Project(id=5)
        parent_task = AIWbsSuggestion(
            id=10,
            wbs_code="1.2",
            template_id=20
        )
        
        data = {
            'task_name': "子任务1",
            'task_description': "描述",
            'task_type': "DEVELOP",
            'estimated_duration_days': 5,
            'estimated_effort_hours': 40,
            'complexity': "COMPLEX",
            'confidence_score': 85.5
        }
        
        result = decomposer._create_suggestion_from_data(
            data, project, parent_task, level=2, sequence=3
        )
        
        assert result.suggestion_code == "WBS_5_L2_10_03"
        assert result.project_id == 5
        assert result.template_id == 20
        assert result.ai_model_version == "glm-4-flash"
        assert result.wbs_level == 2
        assert result.parent_wbs_id == 10
        assert result.wbs_code == "1.2.3"
        assert result.sequence == 3
        assert result.task_name == "子任务1"
        assert result.task_type == "DEVELOP"
        assert result.complexity == "COMPLEX"
        assert result.confidence_score == 85.5
    
    def test_create_suggestion_with_defaults(self):
        """测试使用默认值创建建议"""
        mock_glm = MagicMock()
        mock_glm.is_available.return_value = False
        
        decomposer = AIWbsDecomposer(db=MagicMock(), glm_service=mock_glm)
        
        project = Project(id=6)
        parent_task = AIWbsSuggestion(id=11, wbs_code="2")
        
        data = {'task_name': "最小任务"}
        
        result = decomposer._create_suggestion_from_data(
            data, project, parent_task, level=3, sequence=1
        )
        
        assert result.ai_model_version == "RULE_ENGINE"
        assert result.task_type == "GENERAL"
        assert result.complexity == "MEDIUM"
        assert result.confidence_score == 80.0


class TestIdentifyDependencies:
    """测试依赖识别"""
    
    def test_identify_dependencies_same_level(self):
        """测试同层级任务依赖"""
        decomposer = AIWbsDecomposer(db=MagicMock())
        
        suggestions = [
            AIWbsSuggestion(id=1, wbs_level=1, parent_wbs_id=None, sequence=1),
            AIWbsSuggestion(id=2, wbs_level=1, parent_wbs_id=None, sequence=2),
            AIWbsSuggestion(id=3, wbs_level=1, parent_wbs_id=None, sequence=3),
        ]
        
        decomposer._identify_dependencies(suggestions)
        
        # 第一个任务无依赖
        assert suggestions[0].dependencies is None or suggestions[0].dependencies == "[]"
        
        # 第二个任务依赖第一个
        deps_2 = json.loads(suggestions[1].dependencies)
        assert len(deps_2) == 1
        assert deps_2[0]['task_id'] == 1
        assert deps_2[0]['type'] == "FS"
        assert suggestions[1].dependency_type == "FS"
        
        # 第三个任务依赖第二个
        deps_3 = json.loads(suggestions[2].dependencies)
        assert deps_3[0]['task_id'] == 2
    
    def test_identify_dependencies_different_parents(self):
        """测试不同父任务的依赖"""
        decomposer = AIWbsDecomposer(db=MagicMock())
        
        suggestions = [
            AIWbsSuggestion(id=10, wbs_level=2, parent_wbs_id=1, sequence=1),
            AIWbsSuggestion(id=11, wbs_level=2, parent_wbs_id=1, sequence=2),
            AIWbsSuggestion(id=20, wbs_level=2, parent_wbs_id=2, sequence=1),
        ]
        
        decomposer._identify_dependencies(suggestions)
        
        # 同一父任务下的任务有依赖
        deps_11 = json.loads(suggestions[1].dependencies)
        assert deps_11[0]['task_id'] == 10
        
        # 不同父任务的任务无依赖
        # suggestions[2] (id=20) 不应依赖 suggestions[1] (id=11)
        deps_20 = suggestions[2].dependencies
        assert deps_20 is None or deps_20 == "[]" or json.loads(deps_20) == []
    
    def test_identify_dependencies_multiple_levels(self):
        """测试多层级依赖"""
        decomposer = AIWbsDecomposer(db=MagicMock())
        
        suggestions = [
            AIWbsSuggestion(id=1, wbs_level=1, parent_wbs_id=None, sequence=1),
            AIWbsSuggestion(id=2, wbs_level=2, parent_wbs_id=1, sequence=1),
            AIWbsSuggestion(id=3, wbs_level=2, parent_wbs_id=1, sequence=2),
            AIWbsSuggestion(id=4, wbs_level=3, parent_wbs_id=2, sequence=1),
        ]
        
        decomposer._identify_dependencies(suggestions)
        
        # 验证每层级内的依赖关系
        assert suggestions[2].dependencies  # id=3 依赖 id=2


class TestCalculateCriticalPath:
    """测试关键路径计算"""
    
    def test_calculate_critical_path_simple(self):
        """测试简单关键路径"""
        decomposer = AIWbsDecomposer(db=MagicMock())
        
        suggestions = [
            AIWbsSuggestion(id=1, wbs_level=1, parent_wbs_id=None, estimated_duration_days=10),
            AIWbsSuggestion(id=2, wbs_level=2, parent_wbs_id=1, estimated_duration_days=5),
            AIWbsSuggestion(id=3, wbs_level=2, parent_wbs_id=1, estimated_duration_days=8),
        ]
        
        decomposer._calculate_critical_path(suggestions)
        
        # 应该有任务被标记为关键路径
        critical_count = sum(1 for s in suggestions if s.is_critical_path)
        assert critical_count > 0
    
    def test_calculate_task_duration_leaf(self):
        """测试叶子任务工期计算"""
        decomposer = AIWbsDecomposer(db=MagicMock())
        
        task = AIWbsSuggestion(id=1, estimated_duration_days=15)
        
        duration = decomposer._calculate_task_duration(task, [])
        
        assert duration == 15
    
    def test_calculate_task_duration_with_subtasks(self):
        """测试带子任务的工期计算"""
        decomposer = AIWbsDecomposer(db=MagicMock())
        
        parent = AIWbsSuggestion(id=1, estimated_duration_days=100)
        child1 = AIWbsSuggestion(id=2, parent_wbs_id=1, estimated_duration_days=20)
        child2 = AIWbsSuggestion(id=3, parent_wbs_id=1, estimated_duration_days=30)
        
        all_tasks = [parent, child1, child2]
        
        duration = decomposer._calculate_task_duration(parent, all_tasks)
        
        # 应该返回子任务的总和
        assert duration == 50
    
    def test_get_task_chain(self):
        """测试获取任务链"""
        decomposer = AIWbsDecomposer(db=MagicMock())
        
        parent = AIWbsSuggestion(id=1)
        child1 = AIWbsSuggestion(id=2, parent_wbs_id=1)
        child2 = AIWbsSuggestion(id=3, parent_wbs_id=1)
        grandchild = AIWbsSuggestion(id=4, parent_wbs_id=2)
        
        all_tasks = [parent, child1, child2, grandchild]
        
        chain = decomposer._get_task_chain(parent, all_tasks)
        
        assert len(chain) == 4
        assert parent in chain
        assert child1 in chain
        assert child2 in chain
        assert grandchild in chain


class TestDecomposeTask:
    """测试任务分解（异步）"""
    
    @pytest.mark.asyncio
    async def test_decompose_task_max_level_reached(self):
        """测试达到最大层级时停止分解"""
        mock_db = MagicMock()
        decomposer = AIWbsDecomposer(db=mock_db)
        
        parent_task = AIWbsSuggestion(id=1, task_name="测试")
        project = Project(id=1)
        
        result = await decomposer._decompose_task(
            parent_task, project, level=5, max_level=3
        )
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_decompose_task_with_ai(self):
        """测试使用AI分解任务"""
        mock_db = MagicMock()
        mock_glm = MagicMock()
        
        ai_result = [
            {
                'task_name': "AI子任务1",
                'task_type': "DEVELOP",
                'estimated_duration_days': 5,
                'complexity': "MEDIUM"
            }
        ]
        mock_glm.decompose_wbs.return_value = ai_result
        
        decomposer = AIWbsDecomposer(db=mock_db, glm_service=mock_glm)
        
        parent_task = AIWbsSuggestion(
            id=10,
            task_name="父任务",
            task_description="描述",
            task_type="GENERAL",
            estimated_duration_days=10,
            wbs_code="1"
        )
        project = Project(id=2, project_type="WEB")
        
        # Mock数据库操作
        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()
        
        result = await decomposer._decompose_task(
            parent_task, project, level=2, max_level=2
        )
        
        assert len(result) == 1
        assert result[0].task_name == "AI子任务1"
        mock_glm.decompose_wbs.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_decompose_task_fallback(self):
        """测试AI失败时使用备用分解"""
        mock_db = MagicMock()
        mock_glm = MagicMock()
        mock_glm.decompose_wbs.return_value = None  # AI失败
        
        decomposer = AIWbsDecomposer(db=mock_db, glm_service=mock_glm)
        
        parent_task = AIWbsSuggestion(
            id=20,
            task_name="需求分析",
            task_type="ANALYSIS",
            wbs_code="1"
        )
        project = Project(id=3)
        
        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()
        
        result = await decomposer._decompose_task(
            parent_task, project, level=2, max_level=2
        )
        
        # 应该生成备用子任务
        assert len(result) == 3
        assert "需求调研" in [t.task_name for t in result]
    
    @pytest.mark.asyncio
    async def test_decompose_task_recursive(self):
        """测试递归分解"""
        mock_db = MagicMock()
        mock_glm = MagicMock()
        
        # 第一次分解返回一个复杂任务
        first_result = [{
            'task_name': "复杂子任务",
            'complexity': "COMPLEX",
            'task_type': "DEVELOP",
            'estimated_duration_days': 10
        }]
        
        # 第二次分解返回简单任务
        second_result = [{
            'task_name': "简单孙任务",
            'complexity': "SIMPLE",
            'task_type': "CODE",
            'estimated_duration_days': 3
        }]
        
        mock_glm.decompose_wbs.side_effect = [first_result, second_result]
        
        decomposer = AIWbsDecomposer(db=mock_db, glm_service=mock_glm)
        
        parent_task = AIWbsSuggestion(
            id=30,
            task_name="顶级任务",
            wbs_code="1",
            complexity="COMPLEX"
        )
        project = Project(id=4)
        
        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()
        
        result = await decomposer._decompose_task(
            parent_task, project, level=2, max_level=3
        )
        
        # 应该包含子任务和孙任务
        assert len(result) == 2
        assert result[0].task_name == "复杂子任务"
        assert result[1].task_name == "简单孙任务"


class TestDecomposeProject:
    """测试项目分解（异步）"""
    
    @pytest.mark.asyncio
    async def test_decompose_project_not_found(self):
        """测试项目不存在"""
        mock_db = MagicMock()
        mock_db.query.return_value.get.return_value = None
        
        decomposer = AIWbsDecomposer(db=mock_db)
        
        result = await decomposer.decompose_project(project_id=999)
        
        assert result == []
    
    @pytest.mark.asyncio
    @patch('app.services.ai_planning.wbs_decomposer.AIWbsDecomposer._decompose_task')
    async def test_decompose_project_basic(self, mock_decompose):
        """测试基本项目分解"""
        # Mock _decompose_task返回空列表
        mock_decompose.return_value = []
        
        mock_db = MagicMock()
        project = Project(id=100, project_type="SOFTWARE")
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.get.return_value = project
        
        mock_glm = MagicMock()
        
        decomposer = AIWbsDecomposer(db=mock_db, glm_service=mock_glm)
        mock_db.add = MagicMock()
        
        # Mock flush to assign IDs
        id_counter = [1000]
        def mock_flush():
            for obj in mock_db.add.call_args_list:
                if obj[0]:
                    task = obj[0][0]
                    if isinstance(task, AIWbsSuggestion) and task.id is None:
                        task.id = id_counter[0]
                        id_counter[0] += 1
        
        mock_db.flush = mock_flush
        
        result = await decomposer.decompose_project(
            project_id=100,
            max_level=2
        )
        
        # 应该生成一级任务
        assert len(result) == 4
        level_1 = [r for r in result if r.wbs_level == 1]
        assert len(level_1) == 4
    
    @pytest.mark.asyncio
    @patch('app.services.ai_planning.wbs_decomposer.AIWbsDecomposer._decompose_task')
    async def test_decompose_project_with_template(self, mock_decompose):
        """测试使用模板分解项目"""
        # Mock _decompose_task返回空列表
        mock_decompose.return_value = []
        
        mock_db = MagicMock()
        
        project = Project(id=101)
        template = AIProjectPlanTemplate(
            id=50,
            ai_model_version="glm-4",
            phases=json.dumps([
                {"name": "阶段1", "duration_days": 10, "deliverables": []},
                {"name": "阶段2", "duration_days": 20, "deliverables": []}
            ])
        )
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == Project:
                mock_query.get.return_value = project
            elif model == AIProjectPlanTemplate:
                mock_query.get.return_value = template
            return mock_query
        
        mock_db.query.side_effect = query_side_effect
        
        mock_glm = MagicMock()
        
        decomposer = AIWbsDecomposer(db=mock_db, glm_service=mock_glm)
        
        mock_db.add = MagicMock()
        
        # Mock flush to assign IDs
        id_counter = [2000]
        def mock_flush():
            for obj in mock_db.add.call_args_list:
                if obj[0]:
                    task = obj[0][0]
                    if isinstance(task, AIWbsSuggestion) and task.id is None:
                        task.id = id_counter[0]
                        id_counter[0] += 1
        
        mock_db.flush = mock_flush
        
        result = await decomposer.decompose_project(
            project_id=101,
            template_id=50,
            max_level=1
        )
        
        # 应该生成模板定义的阶段
        assert len(result) == 2
        assert result[0].task_name == "阶段1"
        assert result[1].task_name == "阶段2"
    
    @pytest.mark.asyncio
    @patch('app.services.ai_planning.wbs_decomposer.AIWbsDecomposer._decompose_task')
    async def test_decompose_project_max_level(self, mock_decompose):
        """测试最大层级限制"""
        # Mock _decompose_task返回空列表
        mock_decompose.return_value = []
        
        mock_db = MagicMock()
        
        project = Project(id=102)
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.get.return_value = project
        
        mock_glm = MagicMock()
        
        decomposer = AIWbsDecomposer(db=mock_db, glm_service=mock_glm)
        
        mock_db.add = MagicMock()
        
        # Mock flush to assign IDs
        id_counter = [3000]
        def mock_flush():
            for obj in mock_db.add.call_args_list:
                if obj[0]:
                    task = obj[0][0]
                    if isinstance(task, AIWbsSuggestion) and task.id is None:
                        task.id = id_counter[0]
                        id_counter[0] += 1
        
        mock_db.flush = mock_flush
        
        result = await decomposer.decompose_project(
            project_id=102,
            max_level=1
        )
        
        # 应该只有一级任务
        assert all(r.wbs_level == 1 for r in result)
        assert len(result) == 4


class TestEdgeCases:
    """边界条件测试"""
    
    def test_empty_suggestions_list(self):
        """测试空建议列表"""
        decomposer = AIWbsDecomposer(db=MagicMock())
        
        decomposer._identify_dependencies([])
        decomposer._calculate_critical_path([])
        
        # 不应抛出异常
    
    def test_null_duration_handling(self):
        """测试空工期处理"""
        decomposer = AIWbsDecomposer(db=MagicMock())
        
        task = AIWbsSuggestion(id=1, estimated_duration_days=None)
        
        duration = decomposer._calculate_task_duration(task, [])
        
        assert duration == 0
    
    def test_complex_wbs_code_generation(self):
        """测试复杂WBS编码生成"""
        decomposer = AIWbsDecomposer(db=MagicMock(), glm_service=MagicMock())
        
        project = Project(id=999)
        parent = AIWbsSuggestion(id=1, wbs_code="1.2.3", template_id=None)
        
        data = {'task_name': "深层任务"}
        
        result = decomposer._create_suggestion_from_data(
            data, project, parent, level=4, sequence=7
        )
        
        assert result.wbs_code == "1.2.3.7"
    
    def test_json_serialization(self):
        """测试JSON序列化"""
        decomposer = AIWbsDecomposer(db=MagicMock(), glm_service=MagicMock())
        
        project = Project(id=1)
        parent = AIWbsSuggestion(id=1, wbs_code="1")
        
        data = {
            'task_name': "任务",
            'dependencies': [{'task_id': 10, 'type': 'FS'}],
            'required_skills': [{'skill': 'Python', 'level': 'Senior'}],
            'deliverables': [{'name': '文档', 'type': 'DOC'}]
        }
        
        result = decomposer._create_suggestion_from_data(
            data, project, parent, level=2, sequence=1
        )
        
        # 验证JSON字段可以序列化
        assert result.dependencies
        assert result.required_skills
        assert result.deliverables
        
        # 验证可以反序列化
        deps = json.loads(result.dependencies)
        assert deps[0]['task_id'] == 10
