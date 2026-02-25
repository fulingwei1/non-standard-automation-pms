# -*- coding: utf-8 -*-
"""
项目复盘报告生成器单元测试

目标:
1. 只mock外部依赖(db, ai_client)
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, date
import json

from app.services.project_review_ai.report_generator import ProjectReviewReportGenerator


class TestProjectReviewReportGenerator(unittest.TestCase):
    """测试报告生成器主类"""

    def setUp(self):
        """每个测试前的准备"""
        self.mock_db = MagicMock()
        self.generator = ProjectReviewReportGenerator(self.mock_db)
        
    # ========== generate_report() 主入口测试 ==========
    
    @patch.object(ProjectReviewReportGenerator, '_extract_project_data')
    @patch.object(ProjectReviewReportGenerator, '_build_review_prompt')
    @patch.object(ProjectReviewReportGenerator, '_parse_ai_response')
    def test_generate_report_success(self, mock_parse, mock_build_prompt, mock_extract):
        """测试成功生成报告"""
        # 准备mock数据
        mock_project_data = self._create_mock_project_data()
        mock_extract.return_value = mock_project_data
        mock_build_prompt.return_value = "test prompt"
        
        mock_ai_response = {
            'content': '{"summary": "项目总结"}',
            'token_usage': 1000
        }
        self.generator.ai_client.generate_solution = MagicMock(return_value=mock_ai_response)
        
        mock_parsed_data = {'project_id': 1, 'summary': '项目总结'}
        mock_parse.return_value = mock_parsed_data
        
        # 执行
        result = self.generator.generate_report(project_id=1)
        
        # 验证
        self.assertIn('ai_metadata', result)
        self.assertEqual(result['ai_metadata']['model'], 'glm-5')
        self.assertIn('processing_time_ms', result['ai_metadata'])
        self.assertEqual(result['ai_metadata']['token_usage'], 1000)
        
        # 验证调用
        mock_extract.assert_called_once_with(1)
        mock_build_prompt.assert_called_once_with(mock_project_data, 'POST_MORTEM', None)
        self.generator.ai_client.generate_solution.assert_called_once_with(
            prompt="test prompt",
            model="glm-5",
            temperature=0.7,
            max_tokens=3000
        )
    
    @patch.object(ProjectReviewReportGenerator, '_extract_project_data')
    def test_generate_report_project_not_found(self, mock_extract):
        """测试项目不存在"""
        mock_extract.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.generator.generate_report(project_id=999)
        
        self.assertIn("项目 999 不存在", str(context.exception))
    
    @patch.object(ProjectReviewReportGenerator, '_extract_project_data')
    @patch.object(ProjectReviewReportGenerator, '_build_review_prompt')
    def test_generate_report_with_additional_context(self, mock_build_prompt, mock_extract):
        """测试带额外上下文的报告生成"""
        mock_extract.return_value = self._create_mock_project_data()
        mock_build_prompt.return_value = "prompt"
        
        self.generator.ai_client.generate_solution = MagicMock(return_value={
            'content': '{}',
            'token_usage': 500
        })
        
        self.generator.generate_report(
            project_id=1,
            review_type="MID_TERM",
            additional_context="重点关注技术债务"
        )
        
        # 验证额外上下文被传递
        mock_build_prompt.assert_called_once()
        call_args = mock_build_prompt.call_args
        self.assertEqual(call_args[0][1], "MID_TERM")
        self.assertEqual(call_args[0][2], "重点关注技术债务")
    
    # ========== _extract_project_data() 测试 ==========
    
    def test_extract_project_data_success(self):
        """测试成功提取项目数据"""
        # 创建mock项目
        mock_project = self._create_mock_project()
        
        # 配置db查询
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # 执行
        result = self.generator._extract_project_data(1)
        
        # 验证
        self.assertIsNotNone(result)
        self.assertIn('project', result)
        self.assertIn('statistics', result)
        self.assertIn('team_members', result)
        self.assertIn('changes', result)
        
        self.assertEqual(result['project']['id'], 1)
        self.assertEqual(result['project']['code'], 'PRJ001')
        self.assertEqual(result['project']['name'], '测试项目')
    
    def test_extract_project_data_project_not_found(self):
        """测试项目不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.generator._extract_project_data(999)
        
        self.assertIsNone(result)
    
    def test_extract_project_data_with_timesheets(self):
        """测试包含工时数据"""
        mock_project = self._create_mock_project()
        
        # 创建工时记录
        mock_timesheets = [
            self._create_mock_timesheet(work_hours=8, user_id=1),
            self._create_mock_timesheet(work_hours=6, user_id=1),
            self._create_mock_timesheet(work_hours=10, user_id=2),
        ]
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = mock_project
            elif model.__name__ == 'Timesheet':
                mock_query.filter.return_value.all.return_value = mock_timesheets
            else:
                mock_query.filter.return_value.all.return_value = []
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.generator._extract_project_data(1)
        
        # 验证工时统计
        self.assertEqual(result['statistics']['total_hours'], 24)  # 8+6+10
    
    def test_extract_project_data_with_costs(self):
        """测试包含成本数据"""
        mock_project = self._create_mock_project(budget_amount=10000)
        
        mock_costs = [
            self._create_mock_cost(amount=3000),
            self._create_mock_cost(amount=2500),
        ]
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = mock_project
            elif model.__name__ == 'ProjectCost':
                mock_query.filter.return_value.all.return_value = mock_costs
            else:
                mock_query.filter.return_value.all.return_value = []
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.generator._extract_project_data(1)
        
        # 验证成本统计
        self.assertEqual(result['statistics']['total_cost'], 5500)
        self.assertEqual(result['statistics']['cost_variance'], -4500)  # 5500 - 10000
    
    def test_extract_project_data_with_changes(self):
        """测试包含变更数据"""
        mock_project = self._create_mock_project()
        
        mock_changes = [
            self._create_mock_change(title='需求变更1', change_type='SCOPE'),
            self._create_mock_change(title='需求变更2', change_type='SCHEDULE'),
        ]
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = mock_project
            elif model.__name__ == 'ChangeRequest':
                mock_query.filter.return_value.all.return_value = mock_changes
            else:
                mock_query.filter.return_value.all.return_value = []
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.generator._extract_project_data(1)
        
        # 验证变更统计
        self.assertEqual(result['statistics']['change_count'], 2)
        self.assertEqual(len(result['changes']), 2)
        self.assertEqual(result['changes'][0]['title'], '需求变更1')
    
    def test_extract_project_data_schedule_variance(self):
        """测试工期偏差计算"""
        planned_start = date(2024, 1, 1)
        planned_end = date(2024, 1, 31)  # 30天
        actual_start = date(2024, 1, 1)
        actual_end = date(2024, 2, 10)  # 40天
        
        mock_project = self._create_mock_project(
            planned_start_date=planned_start,
            planned_end_date=planned_end,
            actual_start_date=actual_start,
            actual_end_date=actual_end
        )
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.generator._extract_project_data(1)
        
        # 验证工期计算
        self.assertEqual(result['statistics']['plan_duration'], 30)
        self.assertEqual(result['statistics']['actual_duration'], 40)
        self.assertEqual(result['statistics']['schedule_variance'], 10)  # 延期10天
    
    def test_extract_project_data_with_team_members(self):
        """测试包含团队成员"""
        mock_user1 = MagicMock()
        mock_user1.username = '张三'
        mock_user2 = MagicMock()
        mock_user2.username = '李四'
        
        mock_member1 = MagicMock()
        mock_member1.user = mock_user1
        mock_member1.role = 'PM'
        mock_member1.user_id = 1
        
        mock_member2 = MagicMock()
        mock_member2.user = mock_user2
        mock_member2.role = 'DEV'
        mock_member2.user_id = 2
        
        mock_project = self._create_mock_project()
        mock_project.members = [mock_member1, mock_member2]
        
        mock_timesheets = [
            self._create_mock_timesheet(work_hours=20, user_id=1),
            self._create_mock_timesheet(work_hours=40, user_id=2),
        ]
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = mock_project
            elif model.__name__ == 'Timesheet':
                mock_query.filter.return_value.all.return_value = mock_timesheets
            else:
                mock_query.filter.return_value.all.return_value = []
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.generator._extract_project_data(1)
        
        # 验证团队成员
        self.assertEqual(len(result['team_members']), 2)
        self.assertEqual(result['team_members'][0]['name'], '张三')
        self.assertEqual(result['team_members'][0]['hours'], 20)
        self.assertEqual(result['team_members'][1]['name'], '李四')
        self.assertEqual(result['team_members'][1]['hours'], 40)
    
    # ========== _build_review_prompt() 测试 ==========
    
    def test_build_review_prompt_basic(self):
        """测试基本提示词构建"""
        project_data = self._create_mock_project_data()
        
        prompt = self.generator._build_review_prompt(
            project_data,
            'POST_MORTEM',
            None
        )
        
        # 验证包含关键信息
        self.assertIn('测试项目', prompt)
        self.assertIn('PRJ001', prompt)
        self.assertIn('测试客户', prompt)
        self.assertIn('进度偏差', prompt)  # 源代码使用的是"进度偏差"
        self.assertIn('成本偏差', prompt)
        self.assertIn('总工时', prompt)
        self.assertIn('变更次数', prompt)
    
    def test_build_review_prompt_with_additional_context(self):
        """测试带额外上下文的提示词"""
        project_data = self._create_mock_project_data()
        
        prompt = self.generator._build_review_prompt(
            project_data,
            'MID_TERM',
            '重点关注技术债务和团队协作'
        )
        
        # 验证额外上下文被包含
        self.assertIn('补充信息', prompt)
        self.assertIn('重点关注技术债务和团队协作', prompt)
    
    def test_build_review_prompt_delay_detection(self):
        """测试延期检测"""
        project_data = self._create_mock_project_data()
        project_data['statistics']['schedule_variance'] = 10  # 延期
        
        prompt = self.generator._build_review_prompt(project_data, 'POST_MORTEM', None)
        
        self.assertIn('延期', prompt)
    
    def test_build_review_prompt_early_detection(self):
        """测试提前完成检测"""
        project_data = self._create_mock_project_data()
        project_data['statistics']['schedule_variance'] = -5  # 提前
        
        prompt = self.generator._build_review_prompt(project_data, 'POST_MORTEM', None)
        
        self.assertIn('提前', prompt)
    
    def test_build_review_prompt_budget_overrun(self):
        """测试预算超支检测"""
        project_data = self._create_mock_project_data()
        project_data['statistics']['cost_variance'] = 5000  # 超支
        
        prompt = self.generator._build_review_prompt(project_data, 'POST_MORTEM', None)
        
        self.assertIn('超支', prompt)
    
    def test_build_review_prompt_budget_surplus(self):
        """测试预算结余检测"""
        project_data = self._create_mock_project_data()
        project_data['statistics']['cost_variance'] = -3000  # 结余
        
        prompt = self.generator._build_review_prompt(project_data, 'POST_MORTEM', None)
        
        self.assertIn('结余', prompt)
    
    # ========== _format_changes() 测试 ==========
    
    def test_format_changes_empty(self):
        """测试空变更列表"""
        result = self.generator._format_changes([])
        
        self.assertEqual(result, "无变更记录")
    
    def test_format_changes_single(self):
        """测试单条变更"""
        changes = [
            {'title': '需求变更1', 'type': 'SCOPE', 'impact': 'HIGH', 'status': 'APPROVED'}
        ]
        
        result = self.generator._format_changes(changes)
        
        self.assertIn('1. 需求变更1', result)
        self.assertIn('类型：SCOPE', result)
        self.assertIn('影响：HIGH', result)
    
    def test_format_changes_multiple(self):
        """测试多条变更"""
        changes = [
            {'title': f'变更{i}', 'type': 'SCOPE', 'impact': 'MEDIUM', 'status': 'DONE'}
            for i in range(3)
        ]
        
        result = self.generator._format_changes(changes)
        
        self.assertIn('1. 变更0', result)
        self.assertIn('2. 变更1', result)
        self.assertIn('3. 变更2', result)
    
    def test_format_changes_more_than_five(self):
        """测试超过5条变更"""
        changes = [
            {'title': f'变更{i}', 'type': 'SCOPE', 'impact': 'LOW', 'status': 'PENDING'}
            for i in range(10)
        ]
        
        result = self.generator._format_changes(changes)
        
        # 只显示前5条
        self.assertIn('1. 变更0', result)
        self.assertIn('5. 变更4', result)
        # 显示总数
        self.assertIn('共10条变更', result)
        # 不包含第6条
        self.assertNotIn('6. 变更5', result)
    
    # ========== _parse_ai_response() 测试 ==========
    
    def test_parse_ai_response_valid_json(self):
        """测试有效JSON响应"""
        ai_response = {
            'content': json.dumps({
                'summary': '项目按时完成',
                'success_factors': ['团队协作良好', '技术选型合理'],
                'problems': ['需求变更频繁'],
                'improvements': ['加强需求管理'],
                'best_practices': ['每日站会'],
                'conclusion': '总体成功',
                'insights': {'risk_level': 'LOW'}
            })
        }
        
        project_data = self._create_mock_project_data()
        
        result = self.generator._parse_ai_response(ai_response, project_data)
        
        # 验证基本字段
        self.assertEqual(result['project_id'], 1)
        self.assertEqual(result['project_code'], 'PRJ001')
        
        # 验证AI生成内容
        self.assertEqual(result['ai_summary'], '项目按时完成')
        self.assertIn('团队协作良好', result['success_factors'])
        self.assertIn('需求变更频繁', result['problems'])
        self.assertEqual(result['ai_insights'], {'risk_level': 'LOW'})
        
        # 验证AI标记
        self.assertTrue(result['ai_generated'])
        self.assertIsNotNone(result['ai_generated_at'])
    
    def test_parse_ai_response_with_json_code_block(self):
        """测试带```json代码块的响应"""
        ai_response = {
            'content': '''这是一些说明文字
```json
{
    "summary": "测试总结",
    "success_factors": ["因素1"],
    "problems": [],
    "improvements": [],
    "best_practices": [],
    "conclusion": "结论"
}
```
更多说明'''
        }
        
        project_data = self._create_mock_project_data()
        
        result = self.generator._parse_ai_response(ai_response, project_data)
        
        self.assertEqual(result['ai_summary'], '测试总结')
        self.assertIn('因素1', result['success_factors'])
    
    def test_parse_ai_response_with_generic_code_block(self):
        """测试通用代码块"""
        ai_response = {
            'content': '''```
{
    "summary": "无json标记",
    "success_factors": [],
    "problems": [],
    "improvements": [],
    "best_practices": [],
    "conclusion": "OK"
}
```'''
        }
        
        project_data = self._create_mock_project_data()
        
        result = self.generator._parse_ai_response(ai_response, project_data)
        
        self.assertEqual(result['ai_summary'], '无json标记')
    
    def test_parse_ai_response_invalid_json(self):
        """测试无效JSON响应"""
        ai_response = {
            'content': '这不是有效的JSON格式内容，AI可能直接返回了文本'
        }
        
        project_data = self._create_mock_project_data()
        
        result = self.generator._parse_ai_response(ai_response, project_data)
        
        # 应该使用原始文本作为摘要
        self.assertIn('这不是有效的JSON', result['ai_summary'])
        # 其他字段应该是空的
        self.assertEqual(result['success_factors'], '')
        self.assertEqual(result['problems'], '')
    
    def test_parse_ai_response_data_mapping(self):
        """测试数据映射完整性"""
        ai_response = {'content': '{}'}
        
        project_data = self._create_mock_project_data()
        project_data['statistics']['plan_duration'] = 30
        project_data['statistics']['actual_duration'] = 35
        project_data['statistics']['schedule_variance'] = 5
        project_data['statistics']['total_cost'] = 12000
        project_data['statistics']['cost_variance'] = 2000
        project_data['statistics']['change_count'] = 3
        project_data['project']['budget'] = 10000
        
        result = self.generator._parse_ai_response(ai_response, project_data)
        
        # 验证周期数据
        self.assertEqual(result['plan_duration'], 30)
        self.assertEqual(result['actual_duration'], 35)
        self.assertEqual(result['schedule_variance'], 5)
        
        # 验证成本数据
        self.assertEqual(result['budget_amount'], 10000)
        self.assertEqual(result['actual_cost'], 12000)
        self.assertEqual(result['cost_variance'], 2000)
        
        # 验证质量指标
        self.assertEqual(result['change_count'], 3)
        self.assertEqual(result['quality_issues'], 0)
        self.assertIsNone(result['customer_satisfaction'])
    
    # ========== 辅助方法 ==========
    
    def _create_mock_project(
        self,
        project_id=1,
        code='PRJ001',
        name='测试项目',
        budget_amount=10000,
        planned_start_date=None,
        planned_end_date=None,
        actual_start_date=None,
        actual_end_date=None
    ):
        """创建mock项目对象"""
        mock_project = MagicMock()
        mock_project.id = project_id
        mock_project.code = code
        mock_project.name = name
        mock_project.description = '这是一个测试项目'
        mock_project.status = 'DONE'
        mock_project.project_type = 'INTERNAL'
        mock_project.budget_amount = budget_amount
        
        # 客户
        mock_customer = MagicMock()
        mock_customer.name = '测试客户'
        mock_project.customer = mock_customer
        
        # 日期
        mock_project.planned_start_date = planned_start_date or date(2024, 1, 1)
        mock_project.planned_end_date = planned_end_date or date(2024, 1, 31)
        mock_project.actual_start_date = actual_start_date or date(2024, 1, 1)
        mock_project.actual_end_date = actual_end_date or date(2024, 1, 31)
        
        # 默认无团队成员
        mock_project.members = []
        
        return mock_project
    
    def _create_mock_timesheet(self, work_hours=8, user_id=1):
        """创建mock工时记录"""
        mock_timesheet = MagicMock()
        mock_timesheet.work_hours = work_hours
        mock_timesheet.user_id = user_id
        return mock_timesheet
    
    def _create_mock_cost(self, amount=1000):
        """创建mock成本记录"""
        mock_cost = MagicMock()
        mock_cost.amount = amount
        return mock_cost
    
    def _create_mock_change(
        self,
        title='测试变更',
        change_type='SCOPE',
        impact_level='MEDIUM',
        status='APPROVED'
    ):
        """创建mock变更记录"""
        mock_change = MagicMock()
        mock_change.title = title
        mock_change.change_type = change_type
        mock_change.impact_level = impact_level
        mock_change.status = status
        return mock_change
    
    def _create_mock_project_data(self):
        """创建完整的mock项目数据"""
        return {
            'project': {
                'id': 1,
                'code': 'PRJ001',
                'name': '测试项目',
                'description': '测试描述',
                'customer_name': '测试客户',
                'status': 'DONE',
                'type': 'INTERNAL',
                'planned_start': '2024-01-01',
                'planned_end': '2024-01-31',
                'actual_start': '2024-01-01',
                'actual_end': '2024-01-31',
                'budget': 10000,
            },
            'statistics': {
                'total_hours': 160,
                'total_cost': 8000,
                'change_count': 2,
                'plan_duration': 30,
                'actual_duration': 30,
                'schedule_variance': 0,
                'cost_variance': -2000,
            },
            'team_members': [
                {'name': '张三', 'role': 'PM', 'hours': 80},
                {'name': '李四', 'role': 'DEV', 'hours': 80},
            ],
            'changes': [
                {'title': '需求变更1', 'type': 'SCOPE', 'impact': 'MEDIUM', 'status': 'APPROVED'},
                {'title': '进度调整', 'type': 'SCHEDULE', 'impact': 'LOW', 'status': 'DONE'},
            ]
        }


class TestProjectReviewReportGeneratorEdgeCases(unittest.TestCase):
    """边界情况测试"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        self.generator = ProjectReviewReportGenerator(self.mock_db)
    
    def test_extract_project_data_no_dates(self):
        """测试缺少日期的项目"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.code = 'PRJ001'
        mock_project.name = '测试项目'
        mock_project.description = '描述'
        mock_project.status = 'PLANNING'
        mock_project.project_type = 'INTERNAL'
        mock_project.budget_amount = 10000
        mock_project.customer = MagicMock()
        mock_project.customer.name = '客户'
        mock_project.members = []
        
        # 所有日期都是None
        mock_project.planned_start_date = None
        mock_project.planned_end_date = None
        mock_project.actual_start_date = None
        mock_project.actual_end_date = None
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.generator._extract_project_data(1)
        
        self.assertEqual(result['statistics']['plan_duration'], 0)
        self.assertEqual(result['statistics']['actual_duration'], 0)
        self.assertIsNone(result['project']['planned_start'])
    
    def test_extract_project_data_no_customer(self):
        """测试没有客户的项目"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.code = 'PRJ001'
        mock_project.name = '内部项目'
        mock_project.description = '描述'
        mock_project.status = 'ACTIVE'
        mock_project.project_type = 'INTERNAL'
        mock_project.budget_amount = 5000
        mock_project.planned_start_date = date(2024, 1, 1)
        mock_project.planned_end_date = date(2024, 1, 31)
        mock_project.actual_start_date = None
        mock_project.actual_end_date = None
        mock_project.members = []
        
        # 删除customer属性
        delattr(mock_project, 'customer')
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.generator._extract_project_data(1)
        
        self.assertIsNone(result['project']['customer_name'])
    
    def test_timesheets_with_none_hours(self):
        """测试工时为None的记录"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.code = 'PRJ001'
        mock_project.name = '项目'
        mock_project.description = ''
        mock_project.status = 'ACTIVE'
        mock_project.project_type = 'INTERNAL'
        mock_project.budget_amount = 0
        mock_project.customer = MagicMock()
        mock_project.customer.name = '客户'
        mock_project.planned_start_date = date(2024, 1, 1)
        mock_project.planned_end_date = date(2024, 1, 31)
        mock_project.actual_start_date = None
        mock_project.actual_end_date = None
        mock_project.members = []
        
        # 工时记录中有None值
        mock_timesheets = [
            MagicMock(work_hours=8, user_id=1),
            MagicMock(work_hours=None, user_id=1),  # None
            MagicMock(work_hours=10, user_id=2),
        ]
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = mock_project
            elif model.__name__ == 'Timesheet':
                mock_query.filter.return_value.all.return_value = mock_timesheets
            else:
                mock_query.filter.return_value.all.return_value = []
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.generator._extract_project_data(1)
        
        # None被当作0处理
        self.assertEqual(result['statistics']['total_hours'], 18)  # 8 + 0 + 10
    
    def test_costs_with_none_amount(self):
        """测试金额为None的成本记录"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.code = 'PRJ001'
        mock_project.name = '项目'
        mock_project.description = ''
        mock_project.status = 'ACTIVE'
        mock_project.project_type = 'INTERNAL'
        mock_project.budget_amount = None  # 预算也是None
        mock_project.customer = MagicMock()
        mock_project.customer.name = '客户'
        mock_project.planned_start_date = date(2024, 1, 1)
        mock_project.planned_end_date = date(2024, 1, 31)
        mock_project.actual_start_date = None
        mock_project.actual_end_date = None
        mock_project.members = []
        
        mock_costs = [
            MagicMock(amount=1000),
            MagicMock(amount=None),  # None
            MagicMock(amount=2000),
        ]
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Project':
                mock_query.filter.return_value.first.return_value = mock_project
            elif model.__name__ == 'ProjectCost':
                mock_query.filter.return_value.all.return_value = mock_costs
            else:
                mock_query.filter.return_value.all.return_value = []
            return mock_query
        
        self.mock_db.query.side_effect = query_side_effect
        
        result = self.generator._extract_project_data(1)
        
        self.assertEqual(result['statistics']['total_cost'], 3000)
        self.assertEqual(result['project']['budget'], 0)


if __name__ == '__main__':
    unittest.main()
