# -*- coding: utf-8 -*-
"""
项目经验教训提取器单元测试

测试策略:
1. 只mock外部依赖（db.query, db.add, db.commit, AIClientService）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, date
import json

try:
    from app.services.project_review_ai.lesson_extractor import ProjectLessonExtractor
    from app.models.project_review import ProjectReview, ProjectLesson
except ImportError as e:
    import pytest
    pytest.skip(f"project_review_ai dependencies not available: {e}", allow_module_level=True)


class TestProjectLessonExtractor(unittest.TestCase):
    """测试 ProjectLessonExtractor 类"""

    def setUp(self):
        """测试前的准备工作"""
        # Mock数据库会话
        self.mock_db = MagicMock()
        
        # 创建提取器实例（会mock掉AIClientService）
        with patch('app.services.project_review_ai.lesson_extractor.AIClientService'):
            self.extractor = ProjectLessonExtractor(self.mock_db)
            self.extractor.ai_client = MagicMock()

    # ========== extract_lessons() 主方法测试 ==========

    def test_extract_lessons_success(self):
        """测试成功提取经验教训"""
        # Mock复盘报告数据
        mock_review = MagicMock(spec=ProjectReview)
        mock_review.id = 1
        mock_review.project_id = 100
        mock_review.project_code = "PRJ-2024-001"
        mock_review.review_type = "POST_MORTEM"
        mock_review.schedule_variance = 5
        mock_review.cost_variance = 10000
        mock_review.change_count = 3
        mock_review.customer_satisfaction = 4
        mock_review.success_factors = "团队协作良好"
        mock_review.problems = "进度延误"
        mock_review.improvements = "加强风险管理"
        mock_review.best_practices = "每日站会"
        
        # Mock数据库查询
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_review
        
        # Mock AI响应
        ai_response = {
            'content': '''```json
[
    {
        "lesson_type": "SUCCESS",
        "title": "团队每日站会提升协作效率",
        "description": "通过每日15分钟站会，团队成员及时同步进度，快速解决问题，避免了信息孤岛。",
        "root_cause": "建立了高效的沟通机制，信息透明度高",
        "impact": "整体项目进度提升20%，问题响应时间缩短50%",
        "improvement_action": null,
        "category": "沟通",
        "tags": ["站会", "沟通", "协作"],
        "priority": "HIGH",
        "confidence": 0.9
    },
    {
        "lesson_type": "FAILURE",
        "title": "需求变更管理不足导致进度延误",
        "description": "项目中期客户多次提出需求变更，但缺乏有效的变更管理流程，导致开发返工严重。",
        "root_cause": "未建立正式的变更控制流程，缺少影响评估",
        "impact": "进度延误5天，额外成本增加10000元",
        "improvement_action": "引入正式的变更管理流程，要求所有变更必须经过影响评估和审批",
        "category": "管理",
        "tags": ["需求变更", "流程", "进度"],
        "priority": "HIGH",
        "confidence": 0.85
    },
    {
        "lesson_type": "SUCCESS",
        "title": "代码审查机制保障质量",
        "description": "强制要求所有代码必须经过同行评审，有效降低了bug率。",
        "root_cause": "建立了严格的质量把控机制",
        "impact": "测试阶段bug数量减少40%",
        "improvement_action": null,
        "category": "质量",
        "tags": ["代码审查", "质量", "最佳实践"],
        "priority": "MEDIUM",
        "confidence": 0.8
    }
]
```'''
        }
        self.extractor.ai_client.generate_solution.return_value = ai_response
        
        # 执行提取
        lessons = self.extractor.extract_lessons(review_id=1, min_confidence=0.6)
        
        # 验证结果
        self.assertEqual(len(lessons), 3)
        
        # 验证第一条
        self.assertEqual(lessons[0]['lesson_type'], 'SUCCESS')
        self.assertEqual(lessons[0]['title'], '团队每日站会提升协作效率')
        self.assertEqual(lessons[0]['category'], '沟通')
        self.assertEqual(lessons[0]['priority'], 'HIGH')
        self.assertEqual(lessons[0]['ai_confidence'], 0.9)
        self.assertEqual(lessons[0]['review_id'], 1)
        self.assertEqual(lessons[0]['project_id'], 100)
        
        # 验证第二条（FAILURE类型）
        self.assertEqual(lessons[1]['lesson_type'], 'FAILURE')
        self.assertIsNotNone(lessons[1]['improvement_action'])
        
        # 验证数据库查询被调用
        self.mock_db.query.assert_called_once_with(ProjectReview)
        
        # 验证AI客户端被调用
        self.extractor.ai_client.generate_solution.assert_called_once()
        call_args = self.extractor.ai_client.generate_solution.call_args
        self.assertIn('prompt', call_args.kwargs)
        self.assertEqual(call_args.kwargs['model'], 'glm-5')
        self.assertEqual(call_args.kwargs['temperature'], 0.5)

    def test_extract_lessons_with_min_confidence_filter(self):
        """测试最小置信度过滤"""
        # Mock复盘报告
        mock_review = self._create_mock_review()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_review
        
        # Mock AI响应（包含低置信度项）
        ai_response = {
            'content': '''```json
[
    {
        "lesson_type": "SUCCESS",
        "title": "高置信度经验",
        "description": "这是高置信度的经验",
        "root_cause": "原因分析",
        "impact": "影响范围",
        "category": "技术",
        "tags": ["测试"],
        "priority": "HIGH",
        "confidence": 0.9
    },
    {
        "lesson_type": "FAILURE",
        "title": "低置信度教训",
        "description": "这是低置信度的教训",
        "root_cause": "原因分析",
        "impact": "影响范围",
        "improvement_action": "改进措施",
        "category": "管理",
        "tags": ["测试"],
        "priority": "LOW",
        "confidence": 0.4
    }
]
```'''
        }
        self.extractor.ai_client.generate_solution.return_value = ai_response
        
        # 执行提取，设置最小置信度为0.6
        lessons = self.extractor.extract_lessons(review_id=1, min_confidence=0.6)
        
        # 验证只返回高置信度的项
        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]['title'], '高置信度经验')
        self.assertEqual(lessons[0]['ai_confidence'], 0.9)

    def test_extract_lessons_review_not_found(self):
        """测试复盘报告不存在的情况"""
        # Mock数据库返回None
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 验证抛出异常
        with self.assertRaises(ValueError) as context:
            self.extractor.extract_lessons(review_id=999)
        
        self.assertIn('复盘报告 999 不存在', str(context.exception))

    # ========== _build_extraction_prompt() 测试 ==========

    def test_build_extraction_prompt(self):
        """测试提示词构建"""
        mock_review = self._create_mock_review()
        
        prompt = self.extractor._build_extraction_prompt(mock_review)
        
        # 验证提示词包含必要信息
        self.assertIn('项目经验教训提取任务', prompt)
        self.assertIn('PRJ-2024-001', prompt)
        self.assertIn('POST_MORTEM', prompt)
        self.assertIn('团队协作良好', prompt)
        self.assertIn('进度延误', prompt)
        self.assertIn('加强风险管理', prompt)
        self.assertIn('每日站会', prompt)
        
        # 验证提示词包含任务要求
        self.assertIn('SUCCESS', prompt)
        self.assertIn('FAILURE', prompt)
        self.assertIn('进度管理', prompt)
        self.assertIn('成本控制', prompt)
        self.assertIn('JSON数组格式', prompt)

    def test_build_extraction_prompt_with_null_fields(self):
        """测试复盘报告字段为空的情况"""
        mock_review = MagicMock(spec=ProjectReview)
        mock_review.project_code = "PRJ-2024-002"
        mock_review.review_type = "MID_TERM"
        mock_review.schedule_variance = 0
        mock_review.cost_variance = 0
        mock_review.change_count = 0
        mock_review.customer_satisfaction = 5
        mock_review.success_factors = None
        mock_review.problems = None
        mock_review.improvements = None
        mock_review.best_practices = None
        
        prompt = self.extractor._build_extraction_prompt(mock_review)
        
        # 验证空字段被处理为"无"
        self.assertIn('无', prompt)
        self.assertIn('PRJ-2024-002', prompt)

    # ========== _parse_lessons() 测试 ==========

    def test_parse_lessons_with_json_code_block(self):
        """测试解析带```json标记的AI响应"""
        mock_review = self._create_mock_review()
        
        ai_response = {
            'content': '''这是一些说明文字
```json
[
    {
        "lesson_type": "SUCCESS",
        "title": "测试经验",
        "description": "经验描述",
        "root_cause": "根本原因",
        "impact": "影响范围",
        "category": "技术",
        "tags": ["测试"],
        "priority": "MEDIUM",
        "confidence": 0.75
    }
]
```
这是一些结束语'''
        }
        
        lessons = self.extractor._parse_lessons(ai_response, mock_review)
        
        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]['title'], '测试经验')
        self.assertEqual(lessons[0]['review_id'], 1)
        self.assertEqual(lessons[0]['project_id'], 100)

    def test_parse_lessons_with_plain_code_block(self):
        """测试解析普通```标记的AI响应"""
        mock_review = self._create_mock_review()
        
        ai_response = {
            'content': '''```
[
    {
        "lesson_type": "FAILURE",
        "title": "失败教训",
        "description": "教训描述",
        "root_cause": "根本原因",
        "impact": "影响范围",
        "improvement_action": "改进措施",
        "category": "管理",
        "tags": ["教训"],
        "priority": "HIGH",
        "confidence": 0.8
    }
]
```'''
        }
        
        lessons = self.extractor._parse_lessons(ai_response, mock_review)
        
        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]['lesson_type'], 'FAILURE')
        self.assertEqual(lessons[0]['improvement_action'], '改进措施')

    def test_parse_lessons_pure_json(self):
        """测试解析纯JSON格式的AI响应"""
        mock_review = self._create_mock_review()
        
        ai_response = {
            'content': '''[
    {
        "lesson_type": "SUCCESS",
        "title": "纯JSON经验",
        "description": "经验描述",
        "category": "质量",
        "tags": ["质量"],
        "priority": "LOW",
        "confidence": 0.7
    }
]'''
        }
        
        lessons = self.extractor._parse_lessons(ai_response, mock_review)
        
        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]['title'], '纯JSON经验')

    def test_parse_lessons_single_object(self):
        """测试解析单个对象（非数组）"""
        mock_review = self._create_mock_review()
        
        ai_response = {
            'content': '''{
        "lesson_type": "SUCCESS",
        "title": "单个对象",
        "description": "描述",
        "category": "沟通",
        "tags": ["沟通"],
        "priority": "MEDIUM",
        "confidence": 0.65
    }'''
        }
        
        lessons = self.extractor._parse_lessons(ai_response, mock_review)
        
        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]['title'], '单个对象')

    def test_parse_lessons_invalid_json(self):
        """测试解析无效JSON"""
        mock_review = self._create_mock_review()
        
        ai_response = {
            'content': 'This is not valid JSON at all!'
        }
        
        lessons = self.extractor._parse_lessons(ai_response, mock_review)
        
        # 无效JSON应返回空列表
        self.assertEqual(lessons, [])

    def test_parse_lessons_with_defaults(self):
        """测试字段缺失时的默认值"""
        mock_review = self._create_mock_review()
        
        ai_response = {
            'content': '''[
    {
        "title": "最小化数据",
        "description": "只有必填字段"
    }
]'''
        }
        
        lessons = self.extractor._parse_lessons(ai_response, mock_review)
        
        self.assertEqual(len(lessons), 1)
        # 验证默认值
        self.assertEqual(lessons[0]['lesson_type'], 'SUCCESS')
        self.assertEqual(lessons[0]['category'], '管理')
        self.assertEqual(lessons[0]['priority'], 'MEDIUM')
        self.assertEqual(lessons[0]['ai_confidence'], 0.7)
        self.assertEqual(lessons[0]['ai_extracted'], True)
        self.assertEqual(lessons[0]['status'], 'OPEN')
        self.assertEqual(lessons[0]['tags'], [])

    def test_parse_lessons_title_truncation(self):
        """测试标题过长时的截断"""
        mock_review = self._create_mock_review()
        
        long_title = "这是一个非常长的标题" * 50  # 超过200字符
        
        ai_response = {
            'content': f'''[
    {{
        "title": "{long_title}",
        "description": "描述",
        "confidence": 0.8
    }}
]'''
        }
        
        lessons = self.extractor._parse_lessons(ai_response, mock_review)
        
        # 验证标题被截断到200字符
        self.assertEqual(len(lessons[0]['title']), 200)

    # ========== categorize_lessons() 测试 ==========

    def test_categorize_lessons(self):
        """测试按类别分组"""
        lessons = [
            {'category': '进度', 'title': '进度管理经验1'},
            {'category': '成本', 'title': '成本控制经验1'},
            {'category': '进度', 'title': '进度管理经验2'},
            {'category': '质量', 'title': '质量保证经验1'},
            {'category': '沟通', 'title': '沟通协作经验1'},
            {'category': '技术', 'title': '技术实现经验1'},
            {'category': '管理', 'title': '风险管理经验1'},
        ]
        
        categorized = self.extractor.categorize_lessons(lessons)
        
        # 验证分类结果
        self.assertEqual(len(categorized), 6)
        self.assertEqual(len(categorized['进度']), 2)
        self.assertEqual(len(categorized['成本']), 1)
        self.assertEqual(len(categorized['质量']), 1)
        self.assertEqual(len(categorized['沟通']), 1)
        self.assertEqual(len(categorized['技术']), 1)
        self.assertEqual(len(categorized['管理']), 1)

    def test_categorize_lessons_empty(self):
        """测试空列表分类"""
        categorized = self.extractor.categorize_lessons([])
        
        # 验证返回空的分类字典
        self.assertEqual(len(categorized), 6)
        for category in categorized.values():
            self.assertEqual(len(category), 0)

    def test_categorize_lessons_unknown_category(self):
        """测试未知类别的处理"""
        lessons = [
            {'category': '未知类别', 'title': '测试'},
            {'category': '进度', 'title': '进度管理'},
        ]
        
        categorized = self.extractor.categorize_lessons(lessons)
        
        # 未知类别的项不应出现在任何分类中
        total_count = sum(len(items) for items in categorized.values())
        self.assertEqual(total_count, 1)  # 只有"进度"分类的那一条

    # ========== rank_lessons_by_priority() 测试 ==========

    def test_rank_lessons_by_priority(self):
        """测试按优先级排序"""
        lessons = [
            {'title': '低优先级', 'priority': 'LOW', 'ai_confidence': 0.7},
            {'title': '高优先级1', 'priority': 'HIGH', 'ai_confidence': 0.9},
            {'title': '中等优先级', 'priority': 'MEDIUM', 'ai_confidence': 0.8},
            {'title': '高优先级2', 'priority': 'HIGH', 'ai_confidence': 0.95},
        ]
        
        ranked = self.extractor.rank_lessons_by_priority(lessons)
        
        # 验证排序结果
        self.assertEqual(ranked[0]['title'], '高优先级2')  # HIGH + 0.95
        self.assertEqual(ranked[1]['title'], '高优先级1')  # HIGH + 0.9
        self.assertEqual(ranked[2]['title'], '中等优先级')  # MEDIUM + 0.8
        self.assertEqual(ranked[3]['title'], '低优先级')   # LOW + 0.7

    def test_rank_lessons_with_same_priority(self):
        """测试相同优先级按置信度排序"""
        lessons = [
            {'title': '高优先级A', 'priority': 'HIGH', 'ai_confidence': 0.8},
            {'title': '高优先级B', 'priority': 'HIGH', 'ai_confidence': 0.9},
            {'title': '高优先级C', 'priority': 'HIGH', 'ai_confidence': 0.85},
        ]
        
        ranked = self.extractor.rank_lessons_by_priority(lessons)
        
        # 相同优先级按置信度降序
        self.assertEqual(ranked[0]['ai_confidence'], 0.9)
        self.assertEqual(ranked[1]['ai_confidence'], 0.85)
        self.assertEqual(ranked[2]['ai_confidence'], 0.8)

    def test_rank_lessons_empty(self):
        """测试空列表排序"""
        ranked = self.extractor.rank_lessons_by_priority([])
        self.assertEqual(ranked, [])

    def test_rank_lessons_with_missing_fields(self):
        """测试缺少优先级或置信度字段"""
        lessons = [
            {'title': '完整数据', 'priority': 'HIGH', 'ai_confidence': 0.9},
            {'title': '缺少优先级'},  # 缺少priority和ai_confidence
        ]
        
        ranked = self.extractor.rank_lessons_by_priority(lessons)
        
        # 验证不会报错，缺失字段使用默认值
        self.assertEqual(len(ranked), 2)

    # ========== find_similar_lessons() 测试 ==========

    def test_find_similar_lessons_success(self):
        """测试查找相似经验"""
        # Mock当前经验
        mock_lesson = MagicMock(spec=ProjectLesson)
        mock_lesson.id = 1
        mock_lesson.category = '技术'
        mock_lesson.tags = ['自动化', '测试']
        
        # Mock相似经验
        similar_lesson_1 = MagicMock(spec=ProjectLesson)
        similar_lesson_1.id = 2
        similar_lesson_1.title = '相似经验1'
        similar_lesson_1.description = '描述1'
        similar_lesson_1.category = '技术'
        similar_lesson_1.tags = ['自动化', '部署']
        similar_lesson_1.ai_confidence = 0.85
        similar_lesson_1.review = MagicMock()
        similar_lesson_1.review.project_code = 'PRJ-2024-002'
        
        similar_lesson_2 = MagicMock(spec=ProjectLesson)
        similar_lesson_2.id = 3
        similar_lesson_2.title = '相似经验2'
        similar_lesson_2.description = '描述2'
        similar_lesson_2.category = '技术'
        similar_lesson_2.tags = ['CI/CD']
        similar_lesson_2.ai_confidence = 0.75
        similar_lesson_2.review = MagicMock()
        similar_lesson_2.review.project_code = 'PRJ-2024-003'
        
        # Mock数据库查询
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_lesson
        mock_query.limit.return_value.all.return_value = [similar_lesson_1, similar_lesson_2]
        
        # 执行查找
        results = self.extractor.find_similar_lessons(lesson_id=1, limit=5)
        
        # 验证结果
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], 2)
        self.assertEqual(results[0]['title'], '相似经验1')
        self.assertEqual(results[0]['category'], '技术')
        self.assertEqual(results[0]['confidence'], 0.85)
        self.assertEqual(results[0]['project_code'], 'PRJ-2024-002')

    def test_find_similar_lessons_not_found(self):
        """测试经验不存在"""
        # Mock数据库返回None
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        results = self.extractor.find_similar_lessons(lesson_id=999)
        
        # 验证返回空列表
        self.assertEqual(results, [])

    def test_find_similar_lessons_no_review(self):
        """测试相似经验没有关联复盘报告"""
        # Mock当前经验
        mock_lesson = MagicMock(spec=ProjectLesson)
        mock_lesson.id = 1
        mock_lesson.category = '管理'
        
        # Mock相似经验（没有review）
        similar_lesson = MagicMock(spec=ProjectLesson)
        similar_lesson.id = 2
        similar_lesson.title = '相似经验'
        similar_lesson.description = '描述'
        similar_lesson.category = '管理'
        similar_lesson.tags = ['管理']
        similar_lesson.ai_confidence = None
        similar_lesson.review = None  # 没有关联复盘报告
        
        # Mock数据库
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_lesson
        mock_query.limit.return_value.all.return_value = [similar_lesson]
        
        # 执行查找
        results = self.extractor.find_similar_lessons(lesson_id=1)
        
        # 验证结果
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['confidence'], 0.0)  # ai_confidence为None时转换为0
        self.assertIsNone(results[0]['project_code'])

    # ========== 辅助方法 ==========

    def _create_mock_review(self):
        """创建Mock复盘报告对象"""
        mock_review = MagicMock(spec=ProjectReview)
        mock_review.id = 1
        mock_review.project_id = 100
        mock_review.project_code = "PRJ-2024-001"
        mock_review.review_type = "POST_MORTEM"
        mock_review.schedule_variance = 5
        mock_review.cost_variance = 10000
        mock_review.change_count = 3
        mock_review.customer_satisfaction = 4
        mock_review.success_factors = "团队协作良好"
        mock_review.problems = "进度延误"
        mock_review.improvements = "加强风险管理"
        mock_review.best_practices = "每日站会"
        return mock_review


if __name__ == "__main__":
    unittest.main()
