# -*- coding: utf-8 -*-
"""
完整测试: project_workspace_service
覆盖: app/services/project_workspace_service.py
目标覆盖率: 60%+
测试数量: 25个
覆盖功能: 项目工作空间、文档管理、协作、共享
"""

import pytest
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime, date
from decimal import Decimal

from app.services.project_workspace_service import (
    build_project_basic_info,
    build_team_info,
    build_task_info,
    build_bonus_info,
    build_meeting_info,
    build_issue_info,
    build_solution_info,
    build_document_info,
)


class TestBuildProjectBasicInfo:
    """测试 build_project_basic_info 函数"""

    def test_normal_project_info(self):
        """测试正常项目信息构建"""
        # 创建 mock 项目对象
        project = Mock()
        project.id = 1
        project.project_code = 'PRJ001'
        project.project_name = '智能制造系统'
        project.stage = 'execution'
        project.status = 'active'
        project.health = 'green'
        project.progress_pct = Decimal('65.5')
        project.contract_amount = Decimal('1500000.00')
        project.pm_name = '张三'

        result = build_project_basic_info(project)

        assert result['id'] == 1
        assert result['project_code'] == 'PRJ001'
        assert result['project_name'] == '智能制造系统'
        assert result['stage'] == 'execution'
        assert result['status'] == 'active'
        assert result['health'] == 'green'
        assert result['progress_pct'] == 65.5
        assert result['contract_amount'] == 1500000.0
        assert result['pm_name'] == '张三'

    def test_project_with_none_values(self):
        """测试包含 None 值的项目"""
        project = Mock()
        project.id = 2
        project.project_code = 'PRJ002'
        project.project_name = '测试项目'
        project.stage = 'planning'
        project.status = 'pending'
        project.health = 'yellow'
        project.progress_pct = None
        project.contract_amount = None
        project.pm_name = '李四'

        result = build_project_basic_info(project)

        assert result['id'] == 2
        assert result['progress_pct'] == 0.0
        assert result['contract_amount'] == 0.0
        assert result['pm_name'] == '李四'

    def test_decimal_to_float_conversion(self):
        """测试 Decimal 到 float 的转换"""
        project = Mock()
        project.id = 3
        project.project_code = 'PRJ003'
        project.project_name = '转换测试'
        project.stage = 'execution'
        project.status = 'active'
        project.health = 'green'
        project.progress_pct = Decimal('99.99')
        project.contract_amount = Decimal('9999999.99')
        project.pm_name = '王五'

        result = build_project_basic_info(project)

        assert isinstance(result['progress_pct'], float)
        assert isinstance(result['contract_amount'], float)
        assert result['progress_pct'] == 99.99
        assert result['contract_amount'] == 9999999.99


class TestBuildTeamInfo:
    """测试 build_team_info 函数"""

    def test_normal_team_members(self):
        """测试正常团队成员列表"""
        db = Mock()
        project_id = 1

        # 创建 mock 成员
        member1 = Mock()
        member1.user_id = 10
        member1.user = Mock()
        member1.user.real_name = '张三'
        member1.user.username = 'zhangsan'
        member1.role_code = 'PM'
        member1.allocation_pct = Decimal('100')
        member1.start_date = date(2024, 1, 1)
        member1.end_date = date(2024, 12, 31)

        member2 = Mock()
        member2.user_id = 11
        member2.user = Mock()
        member2.user.real_name = '李四'
        member2.user.username = 'lisi'
        member2.role_code = 'DEV'
        member2.allocation_pct = Decimal('50')
        member2.start_date = date(2024, 2, 1)
        member2.end_date = None

        mock_query = Mock()
        db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [member1, member2]

        result = build_team_info(db, project_id)

        assert len(result) == 2
        assert result[0]['user_id'] == 10
        assert result[0]['user_name'] == '张三'
        assert result[0]['role_code'] == 'PM'
        assert result[0]['allocation_pct'] == 100.0
        assert result[0]['start_date'] == '2024-01-01'
        assert result[0]['end_date'] == '2024-12-31'
        
        assert result[1]['user_id'] == 11
        assert result[1]['user_name'] == '李四'
        assert result[1]['allocation_pct'] == 50.0
        assert result[1]['end_date'] is None

    def test_empty_team(self):
        """测试空团队"""
        db = Mock()
        project_id = 1

        mock_query = Mock()
        db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = build_team_info(db, project_id)

        assert result == []

    def test_member_without_user(self):
        """测试成员缺少用户信息"""
        db = Mock()
        project_id = 1

        member = Mock()
        member.user_id = 12
        member.user = None
        member.role_code = 'QA'
        member.allocation_pct = Decimal('100')
        member.start_date = None
        member.end_date = None

        mock_query = Mock()
        db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [member]

        result = build_team_info(db, project_id)

        assert len(result) == 1
        assert result[0]['user_id'] == 12
        assert result[0]['user_name'] == 'user_12'
        assert result[0]['start_date'] is None


class TestBuildTaskInfo:
    """测试 build_task_info 函数"""

    def test_normal_task_list(self):
        """测试正常任务列表"""
        db = Mock()
        project_id = 1

        task1 = Mock()
        task1.id = 101
        task1.title = '需求分析'
        task1.status = 'completed'
        task1.assignee_name = '张三'
        task1.plan_end_date = date(2024, 1, 15)
        task1.progress = Decimal('100')

        task2 = Mock()
        task2.id = 102
        task2.title = '系统设计'
        task2.status = 'in_progress'
        task2.assignee_name = '李四'
        task2.plan_end_date = date(2024, 2, 28)
        task2.progress = Decimal('60.5')

        mock_query = Mock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [task1, task2]

        result = build_task_info(db, project_id)

        assert len(result) == 2
        assert result[0]['id'] == 101
        assert result[0]['title'] == '需求分析'
        assert result[0]['status'] == 'completed'
        assert result[0]['progress'] == 100.0
        assert result[0]['plan_end_date'] == '2024-01-15'

    def test_empty_task_list(self):
        """测试空任务列表"""
        db = Mock()
        project_id = 1

        mock_query = Mock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = build_task_info(db, project_id)

        assert result == []

    def test_task_limit(self):
        """测试任务数量限制"""
        db = Mock()
        project_id = 1
        limit = 10

        mock_query = Mock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        build_task_info(db, project_id, limit=limit)

        mock_query.limit.assert_called_once_with(limit)


class TestBuildBonusInfo:
    """测试 build_bonus_info 函数"""

    @patch('app.services.project_workspace_service.ProjectBonusService')
    def test_normal_bonus_info(self, mock_bonus_service_class):
        """测试正常奖金信息"""
        db = Mock()
        project_id = 1

        # Mock 规则
        rule = Mock()
        rule.id = 1
        rule.rule_name = '项目奖金'
        rule.bonus_type = 'project'
        rule.coefficient = Decimal('0.15')

        # Mock 计算记录
        calc = Mock()
        calc.id = 10
        calc.calculation_code = 'CALC001'
        calc.user = Mock()
        calc.user.real_name = '张三'
        calc.calculated_amount = Decimal('5000')
        calc.status = 'approved'
        calc.calculated_at = datetime(2024, 1, 15, 10, 0, 0)

        # Mock 分配记录
        dist = Mock()
        dist.id = 20
        dist.user = Mock()
        dist.user.real_name = '张三'
        dist.distributed_amount = Decimal('5000')
        dist.status = 'distributed'
        dist.distributed_at = datetime(2024, 1, 20, 10, 0, 0)

        mock_service = Mock()
        mock_service.get_project_bonus_rules.return_value = [rule]
        mock_service.get_project_bonus_calculations.return_value = [calc]
        mock_service.get_project_bonus_distributions.return_value = [dist]
        mock_service.get_project_bonus_statistics.return_value = {'total': 5000}
        mock_service.get_project_member_bonus_summary.return_value = []
        mock_bonus_service_class.return_value = mock_service

        result = build_bonus_info(db, project_id)

        assert len(result['rules']) == 1
        assert result['rules'][0]['id'] == 1
        assert result['rules'][0]['coefficient'] == 0.15
        
        assert len(result['calculations']) == 1
        assert result['calculations'][0]['user_name'] == '张三'
        assert result['calculations'][0]['calculated_amount'] == 5000.0
        
        assert len(result['distributions']) == 1
        assert result['statistics'] == {'total': 5000}

    @patch('app.services.project_workspace_service.ProjectBonusService')
    def test_bonus_service_exception(self, mock_bonus_service_class):
        """测试奖金服务异常"""
        db = Mock()
        project_id = 1

        mock_bonus_service_class.side_effect = Exception('Service error')

        result = build_bonus_info(db, project_id)

        assert result['rules'] == []
        assert result['calculations'] == []
        assert result['distributions'] == []
        assert result['statistics'] == {}
        assert result['member_summary'] == []

    @patch('app.services.project_workspace_service.ProjectBonusService')
    def test_bonus_empty_data(self, mock_bonus_service_class):
        """测试空奖金数据"""
        db = Mock()
        project_id = 1

        mock_service = Mock()
        mock_service.get_project_bonus_rules.return_value = []
        mock_service.get_project_bonus_calculations.return_value = []
        mock_service.get_project_bonus_distributions.return_value = []
        mock_service.get_project_bonus_statistics.return_value = {}
        mock_service.get_project_member_bonus_summary.return_value = []
        mock_bonus_service_class.return_value = mock_service

        result = build_bonus_info(db, project_id)

        assert result['rules'] == []
        assert result['calculations'] == []

    @patch('app.services.project_workspace_service.ProjectBonusService')
    def test_bonus_missing_user_attribute(self, mock_bonus_service_class):
        """测试缺少用户属性的奖金记录"""
        db = Mock()
        project_id = 1

        calc = Mock()
        calc.id = 10
        calc.calculation_code = 'CALC001'
        calc.user = None  # 缺少用户
        calc.calculated_amount = Decimal('5000')
        calc.status = 'approved'

        mock_service = Mock()
        mock_service.get_project_bonus_rules.return_value = []
        mock_service.get_project_bonus_calculations.return_value = [calc]
        mock_service.get_project_bonus_distributions.return_value = []
        mock_service.get_project_bonus_statistics.return_value = {}
        mock_service.get_project_member_bonus_summary.return_value = []
        mock_bonus_service_class.return_value = mock_service

        result = build_bonus_info(db, project_id)

        assert len(result['calculations']) == 1
        assert result['calculations'][0]['user_name'] == 'Unknown'


class TestBuildMeetingInfo:
    """测试 build_meeting_info 函数"""

    @patch('app.services.project_workspace_service.ProjectMeetingService')
    def test_normal_meeting_info(self, mock_meeting_service_class):
        """测试正常会议信息"""
        db = Mock()
        project_id = 1

        meeting = Mock()
        meeting.id = 1
        meeting.meeting_name = '项目启动会'
        meeting.meeting_date = datetime(2024, 1, 10, 14, 0, 0)
        meeting.rhythm_level = 'weekly'
        meeting.status = 'completed'
        meeting.organizer_name = '张三'
        meeting.minutes = '会议纪要内容'

        mock_service = Mock()
        mock_service.get_project_meetings.return_value = [meeting]
        mock_service.get_project_meeting_statistics.return_value = {'total': 10}
        mock_meeting_service_class.return_value = mock_service

        result = build_meeting_info(db, project_id)

        assert len(result['meetings']) == 1
        assert result['meetings'][0]['id'] == 1
        assert result['meetings'][0]['meeting_name'] == '项目启动会'
        assert result['meetings'][0]['has_minutes'] is True
        assert result['statistics'] == {'total': 10}

    @patch('app.services.project_workspace_service.ProjectMeetingService')
    def test_meeting_service_exception(self, mock_meeting_service_class):
        """测试会议服务异常"""
        db = Mock()
        project_id = 1

        mock_meeting_service_class.side_effect = Exception('Service error')

        result = build_meeting_info(db, project_id)

        assert result['meetings'] == []
        assert result['statistics'] == {}

    @patch('app.services.project_workspace_service.ProjectMeetingService')
    def test_meeting_empty_data(self, mock_meeting_service_class):
        """测试空会议数据"""
        db = Mock()
        project_id = 1

        mock_service = Mock()
        mock_service.get_project_meetings.return_value = []
        mock_service.get_project_meeting_statistics.return_value = {}
        mock_meeting_service_class.return_value = mock_service

        result = build_meeting_info(db, project_id)

        assert result['meetings'] == []
        assert result['statistics'] == {}


class TestBuildIssueInfo:
    """测试 build_issue_info 函数"""

    def test_normal_issue_list(self):
        """测试正常问题列表"""
        db = Mock()
        project_id = 1

        issue1 = Mock()
        issue1.id = 1
        issue1.issue_no = 'ISS001'
        issue1.title = '系统无法登录'
        issue1.status = 'resolved'
        issue1.severity = 'high'
        issue1.priority = 'urgent'
        issue1.solution = '重置密码'
        issue1.assignee_name = '张三'
        issue1.report_date = datetime(2024, 1, 10)

        issue2 = Mock()
        issue2.id = 2
        issue2.issue_no = 'ISS002'
        issue2.title = '性能问题'
        issue2.status = 'open'
        issue2.severity = 'medium'
        issue2.priority = 'normal'
        issue2.solution = None
        issue2.assignee_name = '李四'
        issue2.report_date = datetime(2024, 1, 15)

        mock_query = Mock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [issue1, issue2]

        result = build_issue_info(db, project_id)

        assert len(result['issues']) == 2
        assert result['issues'][0]['id'] == 1
        assert result['issues'][0]['has_solution'] is True
        assert result['issues'][1]['has_solution'] is False

    def test_empty_issue_list(self):
        """测试空问题列表"""
        db = Mock()
        project_id = 1

        mock_query = Mock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = build_issue_info(db, project_id)

        assert result['issues'] == []

    def test_issue_limit(self):
        """测试问题数量限制"""
        db = Mock()
        project_id = 1
        limit = 20

        mock_query = Mock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        build_issue_info(db, project_id, limit=limit)

        mock_query.limit.assert_called_once_with(limit)


class TestBuildSolutionInfo:
    """测试 build_solution_info 函数"""

    @patch('app.services.project_workspace_service.ProjectSolutionService')
    def test_normal_solution_info(self, mock_solution_service_class):
        """测试正常解决方案信息"""
        db = Mock()
        project_id = 1

        solutions = [
            {'id': 1, 'title': '技术方案A'},
            {'id': 2, 'title': '技术方案B'}
        ]

        mock_service = Mock()
        mock_service.get_project_solutions.return_value = solutions
        mock_service.get_project_solution_statistics.return_value = {'total': 2}
        mock_solution_service_class.return_value = mock_service

        result = build_solution_info(db, project_id)

        assert len(result['solutions']) == 2
        assert result['statistics'] == {'total': 2}

    @patch('app.services.project_workspace_service.ProjectSolutionService')
    def test_solution_service_exception(self, mock_solution_service_class):
        """测试解决方案服务异常"""
        db = Mock()
        project_id = 1

        mock_solution_service_class.side_effect = Exception('Service error')

        result = build_solution_info(db, project_id)

        assert result['solutions'] == []
        assert result['statistics'] == {}

    @patch('app.services.project_workspace_service.ProjectSolutionService')
    def test_solution_empty_data(self, mock_solution_service_class):
        """测试空解决方案数据"""
        db = Mock()
        project_id = 1

        mock_service = Mock()
        mock_service.get_project_solutions.return_value = []
        mock_service.get_project_solution_statistics.return_value = {}
        mock_solution_service_class.return_value = mock_service

        result = build_solution_info(db, project_id)

        assert result['solutions'] == []


class TestBuildDocumentInfo:
    """测试 build_document_info 函数"""

    def test_normal_document_list(self):
        """测试正常文档列表"""
        db = Mock()
        project_id = 1

        doc1 = Mock()
        doc1.id = 1
        doc1.doc_name = '需求文档'
        doc1.doc_type = 'requirement'
        doc1.version = 'v1.0'
        doc1.status = 'approved'
        doc1.created_at = datetime(2024, 1, 10, 10, 0, 0)

        doc2 = Mock()
        doc2.id = 2
        doc2.doc_name = '设计文档'
        doc2.doc_type = 'design'
        doc2.version = 'v2.1'
        doc2.status = 'draft'
        doc2.created_at = datetime(2024, 1, 15, 10, 0, 0)

        mock_query = Mock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [doc1, doc2]

        result = build_document_info(db, project_id)

        assert len(result) == 2
        assert result[0]['id'] == 1
        assert result[0]['doc_name'] == '需求文档'
        assert result[0]['version'] == 'v1.0'
        assert result[0]['created_at'] == '2024-01-10T10:00:00'

    def test_empty_document_list(self):
        """测试空文档列表"""
        db = Mock()
        project_id = 1

        mock_query = Mock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = build_document_info(db, project_id)

        assert result == []

    def test_document_limit(self):
        """测试文档数量限制"""
        db = Mock()
        project_id = 1
        limit = 10

        mock_query = Mock()
        db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        build_document_info(db, project_id, limit=limit)

        mock_query.limit.assert_called_once_with(limit)
